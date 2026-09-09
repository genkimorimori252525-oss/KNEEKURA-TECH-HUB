from __future__ import annotations

from contextlib import contextmanager
from copy import deepcopy
from datetime import datetime, timezone
import json
from pathlib import Path
from typing import Any
from uuid import uuid4

from jsonschema import Draft202012Validator

from .claim_support import _claim, _evidence_snapshot
from .comparison import claim_subject_key, compare_claim
from .repository import Record, RecordRepository
from .review import review_claim
from .service import CurationEngine, CurationError


class ClaimDispositionError(ValueError):
    """Raised when a protected terminal Claim transition violates governance."""


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def load_claim_disposition_decision_schema(schema_path: Path | None = None) -> dict[str, Any]:
    if schema_path is None:
        schema_path = (
            Path(__file__).resolve().parents[2]
            / "schemas"
            / "v1"
            / "claim-disposition-decision.schema.json"
        )
    return json.loads(schema_path.read_text(encoding="utf-8"))


def validate_claim_disposition_decision(
    record: Record,
    *,
    schema_path: Path | None = None,
) -> None:
    validator = Draft202012Validator(load_claim_disposition_decision_schema(schema_path))
    errors = sorted(validator.iter_errors(record), key=lambda error: list(error.path))
    if errors:
        raise ClaimDispositionError("; ".join(error.message for error in errors))


def _disposition_repository(repository: RecordRepository) -> RecordRepository:
    connection = getattr(repository, "connection", None)
    lock = getattr(repository, "lock_claim_for_disposition", None)
    if connection is not None and not callable(lock):
        from .claim_disposition_postgres import ClaimDispositionPostgresRepository

        return ClaimDispositionPostgresRepository(connection)
    return repository


def _transactional_repository(repository: RecordRepository):
    connection = getattr(repository, "connection", None)
    lock = getattr(repository, "lock_claim_for_disposition", None)
    if connection is not None and callable(lock):
        return connection.transaction, lock

    repository_transaction = getattr(repository, "transaction", None)
    if callable(repository_transaction):
        def memory_lock(claim_id: str) -> None:
            record = repository.get(claim_id)
            if record is None or record.get("record_type") != "claim":
                raise ValueError(f"missing claim: {claim_id}")

        return repository_transaction, memory_lock

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

    raise ClaimDispositionError(
        "claim disposition writes require PostgreSQL or MemoryRepository transaction support"
    )


def claim_disposition_history(
    repository: RecordRepository,
    *,
    claim_id: str | None = None,
) -> list[Record]:
    repository = _disposition_repository(repository)
    if claim_id is not None:
        _claim(repository, claim_id)
    records = repository.list("claim_disposition_decision")
    for record in records:
        validate_claim_disposition_decision(record)
        if repository.get(record["claim_id"]) is None:
            raise ClaimDispositionError(
                f"claim disposition decision references missing Claim: {record['id']}"
            )
        successor_id = record.get("successor_claim_id")
        if successor_id is not None and repository.get(successor_id) is None:
            raise ClaimDispositionError(
                f"claim disposition decision references missing successor Claim: {record['id']}"
            )
    if claim_id is not None:
        records = [record for record in records if record["claim_id"] == claim_id]
    return sorted(records, key=lambda record: (record["decided_at"], record["id"]))


def claim_disposition_context(repository: RecordRepository, claim_id: str) -> dict[str, Any]:
    repository = _disposition_repository(repository)
    claim = _claim(repository, claim_id)
    return {
        "claim": deepcopy(claim),
        "review": review_claim(repository, claim_id),
        "comparison": compare_claim(repository, claim_id),
        "decisions": claim_disposition_history(repository, claim_id=claim_id),
    }


def dispose_claim(
    repository: RecordRepository,
    claim_id: str,
    target_maturity: str,
    *,
    actor: Record,
    reason: str,
    successor_claim_id: str | None = None,
    competition_note: str | None = None,
    decision_id: str | None = None,
    policy_version: str = "1.0.0",
) -> dict[str, Any]:
    if actor.get("actor_type") != "human":
        raise ClaimDispositionError("protected Claim disposition requires a human reviewer")
    if not isinstance(reason, str) or not reason.strip():
        raise ClaimDispositionError("claim disposition requires a non-empty reason")
    if target_maturity not in {"REJECTED", "SUPERSEDED"}:
        raise ClaimDispositionError("claim disposition target must be REJECTED or SUPERSEDED")

    repository = _disposition_repository(repository)
    transaction_factory, lock = _transactional_repository(repository)
    with transaction_factory():
        try:
            lock(claim_id)
        except ValueError as exc:
            raise ClaimDispositionError(str(exc)) from exc

        claim = _claim(repository, claim_id)
        current = claim["maturity"]
        if target_maturity == "REJECTED":
            if current not in {"SUPPORTED", "CHALLENGED"}:
                raise ClaimDispositionError(
                    f"protected rejection requires SUPPORTED or CHALLENGED maturity, got {current}"
                )
            if successor_claim_id is not None:
                raise ClaimDispositionError("REJECTED disposition cannot name a successor Claim")
        else:
            if current not in {"VALIDATED", "CHALLENGED"}:
                raise ClaimDispositionError(
                    f"supersession requires VALIDATED or CHALLENGED maturity, got {current}"
                )
            if not successor_claim_id:
                raise ClaimDispositionError("SUPERSEDED disposition requires successor_claim_id")
            successor = _claim(repository, successor_claim_id)
            if successor["id"] == claim["id"]:
                raise ClaimDispositionError("a Claim cannot supersede itself")
            if claim_subject_key(successor) != claim_subject_key(claim):
                raise ClaimDispositionError("successor Claim must describe the same exact subject")
            if successor["maturity"] not in {"SUPPORTED", "VALIDATED"}:
                raise ClaimDispositionError("successor Claim must be at least SUPPORTED")

        evidence = _evidence_snapshot(repository, claim)
        review = review_claim(repository, claim_id)
        comparison = compare_claim(repository, claim_id)
        competing_active_claim_ids = sorted(
            candidate_id
            for candidate_id in comparison["active_claim_ids"]
            if candidate_id != claim_id
        )
        if competing_active_claim_ids and not (
            isinstance(competition_note, str) and competition_note.strip()
        ):
            raise ClaimDispositionError(
                "active competing Claims require an explicit competition_note before disposition"
            )

        decision: Record = {
            "record_type": "claim_disposition_decision",
            "id": decision_id or f"cdd:{uuid4()}",
            "claim_id": claim_id,
            "from_maturity": current,
            "to_maturity": target_maturity,
            "reason": reason.strip(),
            "decided_by": deepcopy(actor),
            **evidence,
            "review_flags": sorted(set(review["flags"])),
            "competing_active_claim_ids": competing_active_claim_ids,
            "policy_version": policy_version,
            "decided_at": _now(),
        }
        if successor_claim_id is not None:
            decision["successor_claim_id"] = successor_claim_id
        if isinstance(competition_note, str) and competition_note.strip():
            decision["competition_note"] = competition_note.strip()

        validate_claim_disposition_decision(decision)
        repository.put(decision)

        try:
            disposed = CurationEngine(repository, policy_version=policy_version).transition_claim(
                claim_id,
                target_maturity,
                actor=actor,
                reason=reason,
                superseded_by=successor_claim_id,
            )
        except CurationError as exc:
            raise ClaimDispositionError(str(exc)) from exc

        stored_decision = repository.get(decision["id"])
        stored_claim = repository.get(claim_id)
        if stored_decision != decision:
            raise ClaimDispositionError("claim disposition decision round-trip mismatch")
        if stored_claim != disposed:
            raise ClaimDispositionError("disposed Claim round-trip mismatch")

        return {
            "claim": deepcopy(stored_claim),
            "decision": deepcopy(stored_decision),
            "review_before_disposition": deepcopy(review),
            "comparison_before_disposition": deepcopy(comparison),
        }
