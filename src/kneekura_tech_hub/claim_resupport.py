from __future__ import annotations

from contextlib import contextmanager
from copy import deepcopy
from typing import Any
from uuid import uuid4

from .claim_support import (
    ClaimSupportError,
    _claim,
    _evidence_snapshot,
    _now,
    claim_support_history,
    validate_claim_support_decision,
)
from .comparison import compare_claim
from .repository import Record, RecordRepository
from .review import review_claim
from .service import CurationEngine, CurationError


class ClaimResupportError(ValueError):
    """Raised when CHALLENGED -> SUPPORTED re-review violates governance."""


class _ResupportRepositoryView:
    """Compatibility view over unified claim_support_decision history.

    The service routing predates the unified support-lineage model and asks for a
    `claim_resupport_decision` list during the internal transition. This view
    exposes only CHALLENGED-origin support decisions under that legacy read name
    without creating a second canonical record type.
    """

    def __init__(self, base: RecordRepository) -> None:
        self.base = base

    def __getattr__(self, name: str) -> Any:
        return getattr(self.base, name)

    def get(self, record_id: str) -> Record | None:
        return self.base.get(record_id)

    def put(self, record: Record, *, replace: bool = False) -> None:
        self.base.put(record, replace=replace)

    def list(self, record_type: str | None = None) -> list[Record]:
        if record_type == "claim_resupport_decision":
            return [
                record
                for record in self.base.list("claim_support_decision")
                if record.get("from_maturity") == "CHALLENGED"
                and record.get("to_maturity") == "SUPPORTED"
            ]
        return self.base.list(record_type)

    def lock_claim_for_resupport(self, claim_id: str) -> None:
        lock = getattr(self.base, "lock_claim_for_support", None)
        if callable(lock):
            lock(claim_id)
            return
        record = self.base.get(claim_id)
        if record is None or record.get("record_type") != "claim":
            raise ValueError(f"missing claim: {claim_id}")


def _resupport_repository(repository: RecordRepository) -> RecordRepository:
    connection = getattr(repository, "connection", None)
    if connection is not None and not callable(getattr(repository, "lock_claim_for_support", None)):
        from .claim_support_postgres import ClaimSupportPostgresRepository

        repository = ClaimSupportPostgresRepository(connection)
    return _ResupportRepositoryView(repository)


def _transactional_repository(repository: RecordRepository):
    connection = getattr(repository, "connection", None)
    if connection is not None:
        return connection.transaction, repository.lock_claim_for_resupport

    records = getattr(repository, "_records", None)
    if isinstance(records, dict):
        @contextmanager
        def memory_transaction():
            before = deepcopy(records)
            try:
                yield
            except Exception:
                records.clear()
                records.update(before)
                raise

        return memory_transaction, repository.lock_claim_for_resupport

    raise ClaimResupportError(
        "claim resupport writes require PostgreSQL or MemoryRepository transaction support"
    )


def promote_challenged_to_supported(
    repository: RecordRepository,
    claim_id: str,
    *,
    actor: Record,
    reason: str,
    independence_assessment: str,
    independence_note: str | None = None,
    counterevidence_note: str | None = None,
    qualification_note: str | None = None,
    competition_note: str | None = None,
    decision_id: str | None = None,
    policy_version: str = "1.0.0",
) -> dict[str, Any]:
    if actor.get("actor_type") != "human":
        raise ClaimResupportError("CHALLENGED -> SUPPORTED requires a human reviewer")
    if not isinstance(reason, str) or not reason.strip():
        raise ClaimResupportError("claim resupport review requires a non-empty reason")
    if independence_assessment not in {"NOT_ASSESSED", "HUMAN_REVIEWED"}:
        raise ClaimResupportError("invalid independence assessment")
    if independence_assessment == "HUMAN_REVIEWED" and not (
        isinstance(independence_note, str) and independence_note.strip()
    ):
        raise ClaimResupportError("HUMAN_REVIEWED independence requires independence_note")

    repository = _resupport_repository(repository)
    transaction_factory, lock = _transactional_repository(repository)
    with transaction_factory():
        try:
            lock(claim_id)
        except ValueError as exc:
            raise ClaimResupportError(str(exc)) from exc

        claim = _claim(repository, claim_id)
        if claim["maturity"] != "CHALLENGED":
            raise ClaimResupportError(
                f"claim resupport gate requires CHALLENGED maturity, got {claim['maturity']}"
            )

        try:
            support_history = claim_support_history(repository, claim_id=claim_id)
        except ClaimSupportError as exc:
            raise ClaimResupportError(str(exc)) from exc
        if not support_history:
            raise ClaimResupportError(
                "CHALLENGED -> SUPPORTED requires prior Claim support history"
            )

        try:
            evidence = _evidence_snapshot(repository, claim)
        except ClaimSupportError as exc:
            raise ClaimResupportError(str(exc)) from exc
        review = review_claim(repository, claim_id)
        comparison = compare_claim(repository, claim_id)
        competing_active_claim_ids = sorted(
            candidate_id
            for candidate_id in comparison["active_claim_ids"]
            if candidate_id != claim_id
        )

        if evidence["refuting_evidence_ids"] and not (
            isinstance(counterevidence_note, str) and counterevidence_note.strip()
        ):
            raise ClaimResupportError(
                "refuting Evidence requires an explicit counterevidence_note before resupport"
            )
        if evidence["qualifying_evidence_ids"] and not (
            isinstance(qualification_note, str) and qualification_note.strip()
        ):
            raise ClaimResupportError(
                "qualifying Evidence requires an explicit qualification_note before resupport"
            )
        if competing_active_claim_ids and not (
            isinstance(competition_note, str) and competition_note.strip()
        ):
            raise ClaimResupportError(
                "competing active Claims require an explicit competition_note before resupport"
            )

        decision: Record = {
            "record_type": "claim_support_decision",
            "id": decision_id or f"csd:{uuid4()}",
            "claim_id": claim_id,
            "from_maturity": "CHALLENGED",
            "to_maturity": "SUPPORTED",
            "reason": reason.strip(),
            "reviewed_by": deepcopy(actor),
            **evidence,
            "review_flags": sorted(set(review["flags"])),
            "competing_active_claim_ids": competing_active_claim_ids,
            "independence_assessment": independence_assessment,
            "policy_version": policy_version,
            "decided_at": _now(),
        }
        for field, value in (
            ("independence_note", independence_note),
            ("counterevidence_note", counterevidence_note),
            ("qualification_note", qualification_note),
            ("competition_note", competition_note),
        ):
            if isinstance(value, str) and value.strip():
                decision[field] = value.strip()

        validate_claim_support_decision(decision)
        repository.put(decision)

        try:
            supported = CurationEngine(repository, policy_version=policy_version).transition_claim(
                claim_id,
                "SUPPORTED",
                actor=actor,
                reason=reason,
                _resupport_gate_applied=True,
                _resupport_timestamp=decision["decided_at"],
            )
        except CurationError as exc:
            raise ClaimResupportError(str(exc)) from exc

        stored_decision = repository.get(decision["id"])
        stored_claim = repository.get(claim_id)
        if stored_decision != decision:
            raise ClaimResupportError("claim resupport decision round-trip mismatch")
        if stored_claim != supported:
            raise ClaimResupportError("resupported Claim round-trip mismatch")

        return {
            "claim": deepcopy(stored_claim),
            "decision": deepcopy(stored_decision),
            "review_before_resupport": deepcopy(review),
            "comparison_before_resupport": deepcopy(comparison),
        }
