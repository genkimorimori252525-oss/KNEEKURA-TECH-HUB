from __future__ import annotations

from contextlib import contextmanager
from copy import deepcopy
from datetime import datetime, timezone
import json
from pathlib import Path
from typing import Any
from uuid import uuid4

from jsonschema import Draft202012Validator

from .claim_support import (
    ClaimSupportError,
    _claim,
    _evidence_snapshot,
    claim_support_history,
)
from .comparison import compare_claim
from .repository import Record, RecordRepository
from .review import review_claim
from .service import CurationEngine, CurationError


class ClaimResupportError(ValueError):
    """Raised when CHALLENGED -> SUPPORTED re-review violates governance."""


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def load_claim_resupport_decision_schema(schema_path: Path | None = None) -> dict[str, Any]:
    if schema_path is None:
        schema_path = (
            Path(__file__).resolve().parents[2]
            / "schemas"
            / "v1"
            / "claim-resupport-decision.schema.json"
        )
    return json.loads(schema_path.read_text(encoding="utf-8"))


def validate_claim_resupport_decision(
    record: Record,
    *,
    schema_path: Path | None = None,
) -> None:
    validator = Draft202012Validator(load_claim_resupport_decision_schema(schema_path))
    errors = sorted(validator.iter_errors(record), key=lambda error: list(error.path))
    if errors:
        raise ClaimResupportError("; ".join(error.message for error in errors))


def _resupport_repository(repository: RecordRepository) -> RecordRepository:
    connection = getattr(repository, "connection", None)
    lock = getattr(repository, "lock_claim_for_resupport", None)
    if connection is not None and not callable(lock):
        from .claim_resupport_postgres import ClaimResupportPostgresRepository

        return ClaimResupportPostgresRepository(connection)
    return repository


def _transactional_repository(repository: RecordRepository):
    connection = getattr(repository, "connection", None)
    lock = getattr(repository, "lock_claim_for_resupport", None)
    if connection is not None and callable(lock):
        return connection.transaction, lock

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

        def memory_lock(claim_id: str) -> None:
            record = repository.get(claim_id)
            if record is None or record.get("record_type") != "claim":
                raise ValueError(f"missing claim: {claim_id}")

        return memory_transaction, memory_lock

    raise ClaimResupportError(
        "claim resupport writes require PostgreSQL or MemoryRepository transaction support"
    )


def claim_resupport_history(
    repository: RecordRepository,
    *,
    claim_id: str | None = None,
) -> list[Record]:
    repository = _resupport_repository(repository)
    if claim_id is not None:
        _claim(repository, claim_id)
    records = repository.list("claim_resupport_decision")
    for record in records:
        validate_claim_resupport_decision(record)
        if repository.get(record["claim_id"]) is None:
            raise ClaimResupportError(
                f"claim resupport decision references missing Claim: {record['id']}"
            )
    if claim_id is not None:
        records = [record for record in records if record["claim_id"] == claim_id]
    return sorted(records, key=lambda record: (record["decided_at"], record["id"]))


def claim_resupport_context(repository: RecordRepository, claim_id: str) -> dict[str, Any]:
    repository = _resupport_repository(repository)
    claim = _claim(repository, claim_id)
    review = review_claim(repository, claim_id)
    comparison = compare_claim(repository, claim_id)
    competing_active_claim_ids = sorted(
        candidate_id
        for candidate_id in comparison["active_claim_ids"]
        if candidate_id != claim_id
    )
    return {
        "claim": deepcopy(claim),
        "review": deepcopy(review),
        "comparison": deepcopy(comparison),
        "competing_active_claim_ids": competing_active_claim_ids,
        "initial_support_decisions": claim_support_history(repository, claim_id=claim_id),
        "resupport_decisions": claim_resupport_history(repository, claim_id=claim_id),
    }


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
            support_decisions = claim_support_history(repository, claim_id=claim_id)
        except ClaimSupportError as exc:
            raise ClaimResupportError(str(exc)) from exc
        if len(support_decisions) != 1:
            raise ClaimResupportError(
                "CHALLENGED -> SUPPORTED requires exactly one initial Claim support decision"
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
            "record_type": "claim_resupport_decision",
            "id": decision_id or f"crsd:{uuid4()}",
            "claim_id": claim_id,
            "initial_support_decision_id": support_decisions[0]["id"],
            "from_maturity": "CHALLENGED",
            "to_maturity": "SUPPORTED",
            "reason": reason,
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

        validate_claim_resupport_decision(decision)
        repository.put(decision)

        arm = getattr(repository, "arm_support_review", None)
        if callable(arm):
            try:
                arm(claim_id, decision["decided_at"])
            except ValueError as exc:
                raise ClaimResupportError(str(exc)) from exc

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
