from __future__ import annotations

from contextlib import contextmanager
from copy import deepcopy
from datetime import datetime, timezone
import json
from pathlib import Path
from typing import Any
from uuid import uuid4

from jsonschema import Draft202012Validator

from .claim_support import _claim, _evidence_snapshot, claim_support_history
from .comparison import compare_claim
from .repository import Record, RecordRepository
from .review import review_claim
from .service import CurationEngine, CurationError


class ClaimValidationError(ValueError):
    """Raised when a Claim -> VALIDATED review violates governance."""


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def load_claim_validation_decision_schema(schema_path: Path | None = None) -> dict[str, Any]:
    if schema_path is None:
        schema_path = (
            Path(__file__).resolve().parents[2]
            / "schemas"
            / "v1"
            / "claim-validation-decision.schema.json"
        )
    return json.loads(schema_path.read_text(encoding="utf-8"))


def validate_claim_validation_decision(
    record: Record,
    *,
    schema_path: Path | None = None,
) -> None:
    validator = Draft202012Validator(load_claim_validation_decision_schema(schema_path))
    errors = sorted(validator.iter_errors(record), key=lambda error: list(error.path))
    if errors:
        raise ClaimValidationError("; ".join(error.message for error in errors))


def _validation_repository(repository: RecordRepository) -> RecordRepository:
    connection = getattr(repository, "connection", None)
    lock = getattr(repository, "lock_claim_for_validation", None)
    if connection is not None and not callable(lock):
        from .claim_validation_postgres import ClaimValidationPostgresRepository

        return ClaimValidationPostgresRepository(connection)
    return repository


def _transactional_repository(repository: RecordRepository):
    connection = getattr(repository, "connection", None)
    lock = getattr(repository, "lock_claim_for_validation", None)
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

    raise ClaimValidationError(
        "claim validation writes require PostgreSQL or MemoryRepository transaction support"
    )


def claim_validation_history(
    repository: RecordRepository,
    *,
    claim_id: str | None = None,
) -> list[Record]:
    repository = _validation_repository(repository)
    if claim_id is not None:
        _claim(repository, claim_id)
    records = repository.list("claim_validation_decision")
    for record in records:
        validate_claim_validation_decision(record)
        if repository.get(record["claim_id"]) is None:
            raise ClaimValidationError(
                f"claim validation decision references missing Claim: {record['id']}"
            )
        support = repository.get(record["support_decision_id"])
        if support is None or support.get("record_type") != "claim_support_decision":
            raise ClaimValidationError(
                f"claim validation decision references missing support decision: {record['id']}"
            )
        if support.get("claim_id") != record["claim_id"]:
            raise ClaimValidationError(
                f"claim validation decision support decision belongs to another Claim: {record['id']}"
            )
    if claim_id is not None:
        records = [record for record in records if record["claim_id"] == claim_id]
    return sorted(records, key=lambda record: (record["validated_at"], record["id"]))


def claim_validation_context(repository: RecordRepository, claim_id: str) -> dict[str, Any]:
    repository = _validation_repository(repository)
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
        "support_decisions": claim_support_history(repository, claim_id=claim_id),
        "validation_decisions": claim_validation_history(repository, claim_id=claim_id),
    }


def validate_claim(
    repository: RecordRepository,
    claim_id: str,
    *,
    actor: Record,
    reason: str,
    validation_basis: str,
    validation_note: str,
    independence_assessment: str,
    independence_note: str | None = None,
    counterevidence_note: str | None = None,
    qualification_note: str | None = None,
    competition_note: str | None = None,
    decision_id: str | None = None,
    policy_version: str = "1.0.0",
) -> dict[str, Any]:
    if actor.get("actor_type") != "human":
        raise ClaimValidationError("VALIDATED promotion requires a human reviewer")
    if not isinstance(reason, str) or not reason.strip():
        raise ClaimValidationError("claim validation requires a non-empty reason")
    if validation_basis not in {"EVIDENCE_REVIEW", "REPRODUCTION", "EXPERIMENT", "OTHER"}:
        raise ClaimValidationError("invalid validation basis")
    if not isinstance(validation_note, str) or not validation_note.strip():
        raise ClaimValidationError("claim validation requires a non-empty validation_note")
    if independence_assessment not in {"NOT_ASSESSED", "HUMAN_REVIEWED"}:
        raise ClaimValidationError("invalid independence assessment")
    if independence_assessment == "HUMAN_REVIEWED" and not (
        isinstance(independence_note, str) and independence_note.strip()
    ):
        raise ClaimValidationError("HUMAN_REVIEWED independence requires independence_note")

    repository = _validation_repository(repository)
    transaction_factory, lock = _transactional_repository(repository)
    with transaction_factory():
        try:
            lock(claim_id)
        except ValueError as exc:
            raise ClaimValidationError(str(exc)) from exc

        claim = _claim(repository, claim_id)
        current = claim["maturity"]
        if current not in {"SUPPORTED", "CHALLENGED"}:
            raise ClaimValidationError(
                f"claim validation gate requires SUPPORTED or CHALLENGED maturity, got {current}"
            )

        support_decisions = claim_support_history(repository, claim_id=claim_id)
        if len(support_decisions) != 1:
            raise ClaimValidationError(
                "VALIDATED promotion requires exactly one prior Claim support decision"
            )

        evidence = _evidence_snapshot(repository, claim)
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
            raise ClaimValidationError(
                "refuting Evidence requires an explicit counterevidence_note before validation"
            )
        if evidence["qualifying_evidence_ids"] and not (
            isinstance(qualification_note, str) and qualification_note.strip()
        ):
            raise ClaimValidationError(
                "qualifying Evidence requires an explicit qualification_note before validation"
            )
        if competing_active_claim_ids and not (
            isinstance(competition_note, str) and competition_note.strip()
        ):
            raise ClaimValidationError(
                "competing active Claims require an explicit competition_note before validation"
            )

        validated_at = _now()
        decision: Record = {
            "record_type": "claim_validation_decision",
            "id": decision_id or f"cvd:{uuid4()}",
            "claim_id": claim_id,
            "support_decision_id": support_decisions[0]["id"],
            "from_maturity": current,
            "to_maturity": "VALIDATED",
            "reason": reason.strip(),
            "validated_by": deepcopy(actor),
            "validation_basis": validation_basis,
            "validation_note": validation_note.strip(),
            **evidence,
            "review_flags": sorted(set(review["flags"])),
            "competing_active_claim_ids": competing_active_claim_ids,
            "independence_assessment": independence_assessment,
            "policy_version": policy_version,
            "validated_at": validated_at,
        }
        for field, value in (
            ("independence_note", independence_note),
            ("counterevidence_note", counterevidence_note),
            ("qualification_note", qualification_note),
            ("competition_note", competition_note),
        ):
            if isinstance(value, str) and value.strip():
                decision[field] = value.strip()

        validate_claim_validation_decision(decision)
        repository.put(decision)

        try:
            validated = CurationEngine(repository, policy_version=policy_version).transition_claim(
                claim_id,
                "VALIDATED",
                actor=actor,
                reason=reason,
                _validation_gate_applied=True,
                _validation_timestamp=validated_at,
            )
        except CurationError as exc:
            raise ClaimValidationError(str(exc)) from exc

        stored_decision = repository.get(decision["id"])
        stored_claim = repository.get(claim_id)
        if stored_decision != decision:
            raise ClaimValidationError("claim validation decision round-trip mismatch")
        if stored_claim != validated:
            raise ClaimValidationError("validated Claim round-trip mismatch")
        if stored_claim.get("last_verified") != stored_decision["validated_at"]:
            raise ClaimValidationError("validated Claim timestamp does not match validation decision")

        return {
            "claim": deepcopy(stored_claim),
            "decision": deepcopy(stored_decision),
            "review_before_validation": deepcopy(review),
            "comparison_before_validation": deepcopy(comparison),
        }
