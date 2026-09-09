from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timezone
import json
from pathlib import Path
from typing import Any
from uuid import uuid4

from jsonschema import Draft202012Validator

from .comparison import compare_claim
from .repository import Record, RecordRepository
from .review import review_claim
from .service import CurationEngine, CurationError
from .validator import validate_record


class ClaimSupportError(ValueError):
    """Raised when a CANDIDATE -> SUPPORTED review violates governance."""


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def load_claim_support_decision_schema(schema_path: Path | None = None) -> dict[str, Any]:
    if schema_path is None:
        schema_path = (
            Path(__file__).resolve().parents[2]
            / "schemas"
            / "v1"
            / "claim-support-decision.schema.json"
        )
    return json.loads(schema_path.read_text(encoding="utf-8"))


def validate_claim_support_decision(
    record: Record,
    *,
    schema_path: Path | None = None,
) -> None:
    validator = Draft202012Validator(load_claim_support_decision_schema(schema_path))
    errors = sorted(validator.iter_errors(record), key=lambda error: list(error.path))
    if errors:
        raise ClaimSupportError("; ".join(error.message for error in errors))


def _claim(repository: RecordRepository, claim_id: str) -> Record:
    record = repository.get(claim_id)
    if record is None or record.get("record_type") != "claim":
        raise ClaimSupportError(f"missing claim: {claim_id}")
    validate_record(record)
    return record


def _transactional_repository(repository: RecordRepository):
    connection = getattr(repository, "connection", None)
    lock = getattr(repository, "lock_claim_for_support", None)
    if connection is None or not callable(lock):
        raise ClaimSupportError(
            "claim support writes require transactional PostgreSQL support repository"
        )
    return connection, lock


def claim_support_history(
    repository: RecordRepository,
    *,
    claim_id: str | None = None,
) -> list[Record]:
    if claim_id is not None:
        _claim(repository, claim_id)
    records = repository.list("claim_support_decision")
    for record in records:
        validate_claim_support_decision(record)
        if repository.get(record["claim_id"]) is None:
            raise ClaimSupportError(
                f"claim support decision references missing Claim: {record['id']}"
            )
    if claim_id is not None:
        records = [record for record in records if record["claim_id"] == claim_id]
    return sorted(records, key=lambda record: (record["decided_at"], record["id"]))


def claim_support_context(repository: RecordRepository, claim_id: str) -> dict[str, Any]:
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
    }


def _evidence_snapshot(
    repository: RecordRepository,
    claim: Record,
) -> dict[str, list[str]]:
    evidence_ids = sorted(set(claim.get("evidence_ids") or []))
    if not evidence_ids:
        raise ClaimSupportError("SUPPORTED promotion requires at least one Evidence record")

    supporting: list[str] = []
    refuting: list[str] = []
    qualifying: list[str] = []
    source_ids: set[str] = set()
    snapshot_ids: set[str] = set()

    for evidence_id in evidence_ids:
        evidence = repository.get(evidence_id)
        if evidence is None or evidence.get("record_type") != "evidence":
            raise ClaimSupportError(f"missing Evidence for claim support: {evidence_id}")
        validate_record(evidence)
        roles = set(evidence.get("roles") or [])
        if "SUPPORTS" in roles:
            supporting.append(evidence_id)
        if "REFUTES" in roles:
            refuting.append(evidence_id)
        if "QUALIFIES" in roles:
            qualifying.append(evidence_id)
        source_ids.add(evidence["source_id"])
        snapshot_ids.add(evidence["source_snapshot_id"])

    if not supporting:
        raise ClaimSupportError(
            "SUPPORTED promotion requires at least one Evidence record with SUPPORTS role"
        )

    return {
        "evidence_ids": evidence_ids,
        "supporting_evidence_ids": sorted(supporting),
        "refuting_evidence_ids": sorted(refuting),
        "qualifying_evidence_ids": sorted(qualifying),
        "distinct_source_ids": sorted(source_ids),
        "distinct_snapshot_ids": sorted(snapshot_ids),
    }


def promote_candidate_to_supported(
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
        raise ClaimSupportError("CANDIDATE -> SUPPORTED requires a human reviewer")
    if not isinstance(reason, str) or not reason.strip():
        raise ClaimSupportError("claim support review requires a non-empty reason")
    if independence_assessment not in {"NOT_ASSESSED", "HUMAN_REVIEWED"}:
        raise ClaimSupportError("invalid independence assessment")
    if independence_assessment == "HUMAN_REVIEWED" and not (
        isinstance(independence_note, str) and independence_note.strip()
    ):
        raise ClaimSupportError("HUMAN_REVIEWED independence requires independence_note")

    connection, lock = _transactional_repository(repository)
    with connection.transaction():
        try:
            lock(claim_id)
        except ValueError as exc:
            raise ClaimSupportError(str(exc)) from exc

        claim = _claim(repository, claim_id)
        if claim["maturity"] != "CANDIDATE":
            raise ClaimSupportError(
                f"claim support gate requires CANDIDATE maturity, got {claim['maturity']}"
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
            raise ClaimSupportError(
                "refuting Evidence requires an explicit counterevidence_note before support"
            )
        if evidence["qualifying_evidence_ids"] and not (
            isinstance(qualification_note, str) and qualification_note.strip()
        ):
            raise ClaimSupportError(
                "qualifying Evidence requires an explicit qualification_note before support"
            )
        if competing_active_claim_ids and not (
            isinstance(competition_note, str) and competition_note.strip()
        ):
            raise ClaimSupportError(
                "competing active Claims require an explicit competition_note before support"
            )

        decision: Record = {
            "record_type": "claim_support_decision",
            "id": decision_id or f"csd:{uuid4()}",
            "claim_id": claim_id,
            "from_maturity": "CANDIDATE",
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

        validate_claim_support_decision(decision)
        repository.put(decision)

        try:
            supported = CurationEngine(repository, policy_version=policy_version).transition_claim(
                claim_id,
                "SUPPORTED",
                actor=actor,
                reason=reason,
            )
        except CurationError as exc:
            raise ClaimSupportError(str(exc)) from exc

        stored_decision = repository.get(decision["id"])
        stored_claim = repository.get(claim_id)
        if stored_decision != decision:
            raise ClaimSupportError("claim support decision round-trip mismatch")
        if stored_claim != supported:
            raise ClaimSupportError("supported Claim round-trip mismatch")

        return {
            "claim": deepcopy(stored_claim),
            "decision": deepcopy(stored_decision),
            "review_before_support": deepcopy(review),
            "comparison_before_support": deepcopy(comparison),
        }
