from __future__ import annotations

from contextlib import contextmanager
from copy import deepcopy
from typing import Any, Protocol


Record = dict[str, Any]
DispositionTransition = tuple[str, str, str, str | None]


class RecordRepository(Protocol):
    def get(self, record_id: str) -> Record | None:
        ...

    def put(self, record: Record, *, replace: bool = False) -> None:
        ...

    def list(self, record_type: str | None = None) -> list[Record]:
        ...


class DuplicateRecordError(ValueError):
    pass


class MemoryRepository:
    """Small in-memory repository used by the curation domain layer and tests.

    Protected terminal Claim *transitions* preserve the same decision/state
    pairing as PostgreSQL. Prebuilt read fixtures may still contain historical
    terminal Claims without replaying their original decision transaction.

    A Claim's epistemic content is editable only while it remains CANDIDATE.
    Once human review starts, the reviewed payload is immutable and corrections
    must be represented by a new Claim.
    """

    _CLAIM_EPISTEMIC_FIELDS = (
        "entity_id",
        "relation",
        "claim_type",
        "statement",
        "scope",
        "applicability",
        "confidence",
        "reasoning_basis",
        "alternative_interpretations",
        "evidence_ids",
        "policy_version",
    )

    def __init__(self) -> None:
        self._records: dict[str, Record] = {}
        self._transaction_depth = 0
        self._transaction_snapshot: dict[str, Record] | None = None
        self._pending_disposition_transitions: list[DispositionTransition] = []

    def get(self, record_id: str) -> Record | None:
        record = self._records.get(record_id)
        return deepcopy(record) if record is not None else None

    @contextmanager
    def transaction(self):
        outermost = self._transaction_depth == 0
        if outermost:
            self._transaction_snapshot = deepcopy(self._records)
            self._pending_disposition_transitions = []
        self._transaction_depth += 1
        try:
            yield
            if outermost:
                for transition in self._pending_disposition_transitions:
                    self._validate_disposition_transition(transition)
                self._validate_disposition_decisions_applied()
        except Exception:
            if outermost and self._transaction_snapshot is not None:
                self._records.clear()
                self._records.update(self._transaction_snapshot)
            raise
        finally:
            self._transaction_depth -= 1
            if outermost:
                self._transaction_snapshot = None
                self._pending_disposition_transitions = []

    def put(self, record: Record, *, replace: bool = False) -> None:
        record_id = record["id"]
        current = self._records.get(record_id)

        if record.get("record_type") == "claim_disposition_decision":
            if current is not None:
                raise DuplicateRecordError(
                    f"claim disposition decisions are append-only: {record_id}"
                )
            self._validate_disposition_decision_insert(record)
            if any(
                existing.get("record_type") == "claim_disposition_decision"
                and existing.get("claim_id") == record.get("claim_id")
                for existing in self._records.values()
            ):
                raise DuplicateRecordError(
                    f"claim already has a disposition decision: {record.get('claim_id')}"
                )

        if current is not None and not replace:
            raise DuplicateRecordError(f"record already exists: {record_id}")

        self._guard_reviewed_claim_content_mutation(current, record)
        transition = self._protected_disposition_transition(current, record)
        before = deepcopy(current) if current is not None else None
        self._records[record_id] = deepcopy(record)

        if self._transaction_depth > 0:
            if transition is not None:
                self._pending_disposition_transitions.append(transition)
            return

        try:
            if transition is not None:
                self._validate_disposition_transition(transition)
            self._validate_disposition_decisions_applied()
        except Exception:
            if before is None:
                self._records.pop(record_id, None)
            else:
                self._records[record_id] = before
            raise

    def list(self, record_type: str | None = None) -> list[Record]:
        records = self._records.values()
        if record_type is not None:
            records = [record for record in records if record.get("record_type") == record_type]
        return [deepcopy(record) for record in records]

    @classmethod
    def _guard_reviewed_claim_content_mutation(
        cls,
        current: Record | None,
        updated: Record,
    ) -> None:
        if (
            current is None
            or current.get("record_type") != "claim"
            or updated.get("record_type") != "claim"
        ):
            return

        if current.get("created_by") != updated.get("created_by"):
            raise ValueError(f"claim created_by is immutable: {updated['id']}")

        changed = any(
            current.get(field) != updated.get(field)
            for field in cls._CLAIM_EPISTEMIC_FIELDS
        )
        if changed and not (
            current.get("maturity") == "CANDIDATE"
            and updated.get("maturity") == "CANDIDATE"
        ):
            raise ValueError(
                "reviewed Claim epistemic content is immutable; "
                f"create a new Claim for revisions: {updated['id']}"
            )

    @staticmethod
    def _protected_disposition_transition(
        current: Record | None,
        updated: Record,
    ) -> DispositionTransition | None:
        if (
            current is None
            or current.get("record_type") != "claim"
            or updated.get("record_type") != "claim"
        ):
            return None
        before = current.get("maturity")
        after = updated.get("maturity")
        protected = (
            before in {"SUPPORTED", "CHALLENGED"} and after == "REJECTED"
        ) or (
            before in {"VALIDATED", "CHALLENGED"} and after == "SUPERSEDED"
        )
        if not protected:
            return None
        return (updated["id"], before, after, updated.get("superseded_by"))

    def _validate_disposition_transition(self, transition: DispositionTransition) -> None:
        claim_id, from_maturity, to_maturity, successor_claim_id = transition
        matches = [
            record
            for record in self._records.values()
            if record.get("record_type") == "claim_disposition_decision"
            and record.get("claim_id") == claim_id
            and record.get("from_maturity") == from_maturity
            and record.get("to_maturity") == to_maturity
            and record.get("successor_claim_id") == successor_claim_id
        ]
        if len(matches) != 1:
            raise ValueError(
                f"claim {from_maturity} -> {to_maturity} requires matching human disposition decision: {claim_id}"
            )

    def _validate_disposition_decision_insert(self, decision: Record) -> None:
        from .claim_disposition import validate_claim_disposition_decision
        from .claim_support import _evidence_snapshot
        from .comparison import claim_subject_key, compare_claim

        validate_claim_disposition_decision(decision)
        claim = self.get(decision["claim_id"])
        if claim is None or claim.get("record_type") != "claim":
            raise ValueError(
                f"claim disposition decision references missing Claim: {decision['id']}"
            )
        if claim.get("maturity") != decision.get("from_maturity"):
            raise ValueError(
                "claim disposition decision from_maturity does not match current Claim state"
            )

        expected_evidence = _evidence_snapshot(self, claim)
        for field in (
            "evidence_ids",
            "supporting_evidence_ids",
            "refuting_evidence_ids",
            "qualifying_evidence_ids",
            "distinct_source_ids",
            "distinct_snapshot_ids",
        ):
            if decision.get(field) != expected_evidence.get(field):
                raise ValueError(
                    f"claim disposition decision {field} does not match Claim Evidence"
                )

        comparison = compare_claim(self, claim["id"])
        expected_competitors = sorted(
            candidate_id
            for candidate_id in comparison["active_claim_ids"]
            if candidate_id != claim["id"]
        )
        if decision.get("competing_active_claim_ids") != expected_competitors:
            raise ValueError(
                "claim disposition decision competing_active_claim_ids do not match active Claims"
            )
        if expected_competitors and not decision.get("competition_note"):
            raise ValueError(
                "claim disposition decision with active competing Claims requires competition_note"
            )

        successor_id = decision.get("successor_claim_id")
        if decision.get("to_maturity") == "SUPERSEDED":
            successor = self.get(successor_id) if successor_id else None
            if successor is None or successor.get("record_type") != "claim":
                raise ValueError("claim disposition decision requires an existing successor Claim")
            if successor["id"] == claim["id"]:
                raise ValueError("a Claim cannot supersede itself")
            if claim_subject_key(successor) != claim_subject_key(claim):
                raise ValueError("successor Claim must describe the same exact subject")
            if successor.get("maturity") not in {"SUPPORTED", "VALIDATED"}:
                raise ValueError("successor Claim must be at least SUPPORTED")

    def _validate_disposition_decisions_applied(self) -> None:
        seen_claim_ids: set[str] = set()
        for record in self._records.values():
            if record.get("record_type") != "claim_disposition_decision":
                continue
            claim_id = record["claim_id"]
            if claim_id in seen_claim_ids:
                raise ValueError(f"claim has multiple disposition decisions: {claim_id}")
            seen_claim_ids.add(claim_id)

            claim = self._records.get(claim_id)
            if claim is None or claim.get("record_type") != "claim":
                raise ValueError(
                    f"claim disposition decision references missing Claim: {record['id']}"
                )
            if claim.get("maturity") != record.get("to_maturity"):
                raise ValueError(
                    f"claim disposition decision requires matching terminal Claim state: {claim_id}"
                )
            if claim.get("superseded_by") != record.get("successor_claim_id"):
                raise ValueError(
                    f"claim disposition successor does not match terminal Claim state: {claim_id}"
                )
