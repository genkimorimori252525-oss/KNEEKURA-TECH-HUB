from __future__ import annotations

from collections import Counter
from copy import deepcopy
from datetime import datetime, timezone
from uuid import uuid4

from .comparison import claim_subject_key, compare_claim
from .repository import Record, RecordRepository
from .validator import validate_record


class DecisionError(ValueError):
    """Raised when a human review decision is invalid or cannot be read safely."""


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _claim(repository: RecordRepository, claim_id: str) -> Record:
    record = repository.get(claim_id)
    if record is None:
        raise DecisionError(f"missing claim: {claim_id}")
    if record.get("record_type") != "claim":
        raise DecisionError(f"expected claim for {claim_id}, got {record.get('record_type')!r}")
    return record


def _decision(repository: RecordRepository, decision_id: str) -> Record:
    record = repository.get(decision_id)
    if record is None:
        raise DecisionError(f"missing review decision: {decision_id}")
    if record.get("record_type") != "review_decision":
        raise DecisionError(
            f"expected review_decision for {decision_id}, got {record.get('record_type')!r}"
        )
    return record


def _pair(record: Record) -> frozenset[str]:
    return frozenset((record["source_claim_id"], record["target_claim_id"]))


def _validate_stored_decision(repository: RecordRepository, record: Record) -> None:
    if record.get("record_type") != "review_decision":
        raise DecisionError(f"expected review_decision, got {record.get('record_type')!r}")
    validate_record(record)
    source = _claim(repository, record["source_claim_id"])
    target = _claim(repository, record["target_claim_id"])
    if claim_subject_key(source) != claim_subject_key(target):
        raise DecisionError(f"review decision crosses Claim subjects: {record['id']}")


class HumanReviewDecisionEngine:
    """Human-gated append-only decisions about two Claims with the same exact subject."""

    def __init__(self, repository: RecordRepository, *, policy_version: str = "1.0.0") -> None:
        self.repository = repository
        self.policy_version = policy_version

    def create(
        self,
        record: Record,
        *,
        actor: Record,
    ) -> Record:
        if record.get("record_type") != "review_decision":
            raise DecisionError(f"expected review_decision, got {record.get('record_type')!r}")
        if actor.get("actor_type") != "human":
            raise DecisionError("review decisions require a human actor")
        if record.get("created_by") != actor:
            raise DecisionError("review decision created_by must match the acting identity")
        if record.get("policy_version") != self.policy_version:
            raise DecisionError("review decision policy_version must match the active policy")
        if record["source_claim_id"] == record["target_claim_id"]:
            raise DecisionError("review decision requires two distinct Claims")

        source = _claim(self.repository, record["source_claim_id"])
        target = _claim(self.repository, record["target_claim_id"])
        if claim_subject_key(source) != claim_subject_key(target):
            raise DecisionError("review decisions require Claims with the same exact subject")

        supersedes = record.get("supersedes_decision_id")
        if supersedes is not None:
            if supersedes == record["id"]:
                raise DecisionError("review decision cannot supersede itself")
            previous = _decision(self.repository, supersedes)
            _validate_stored_decision(self.repository, previous)
            if _pair(previous) != _pair(record):
                raise DecisionError("superseding decision must concern the same Claim pair")
            for existing in self.repository.list("review_decision"):
                if existing.get("supersedes_decision_id") == supersedes:
                    raise DecisionError("review decision already has a superseding successor")

        validate_record(record)
        self.repository.put(record)
        return deepcopy(record)

    def create_from_fields(
        self,
        *,
        source_claim_id: str,
        target_claim_id: str,
        decision: str,
        rationale: str,
        actor: Record,
        decision_id: str | None = None,
        supersedes_decision_id: str | None = None,
    ) -> Record:
        record: Record = {
            "record_type": "review_decision",
            "id": decision_id or f"rd:{uuid4()}",
            "source_claim_id": source_claim_id,
            "target_claim_id": target_claim_id,
            "decision": decision,
            "rationale": rationale,
            "created_by": actor,
            "policy_version": self.policy_version,
            "decided_at": _now(),
        }
        if supersedes_decision_id is not None:
            record["supersedes_decision_id"] = supersedes_decision_id
        return self.create(record, actor=actor)


def review_decision_history(
    repository: RecordRepository,
    *,
    claim_id: str | None = None,
) -> list[Record]:
    if claim_id is not None:
        _claim(repository, claim_id)

    records = repository.list("review_decision")
    for record in records:
        _validate_stored_decision(repository, record)

    if claim_id is not None:
        records = [
            record
            for record in records
            if claim_id in {record["source_claim_id"], record["target_claim_id"]}
        ]
    return sorted(records, key=lambda item: (item["decided_at"], item["id"]))


def active_review_decisions(
    repository: RecordRepository,
    *,
    claim_id: str | None = None,
) -> list[Record]:
    history = review_decision_history(repository, claim_id=claim_id)
    all_records = review_decision_history(repository)
    superseded_ids = [
        record["supersedes_decision_id"]
        for record in all_records
        if record.get("supersedes_decision_id") is not None
    ]
    duplicates = [item for item, count in Counter(superseded_ids).items() if count > 1]
    if duplicates:
        raise DecisionError(f"review decision has multiple successors: {sorted(duplicates)!r}")
    superseded = set(superseded_ids)
    return [record for record in history if record["id"] not in superseded]


def decision_context_for_claim(repository: RecordRepository, claim_id: str) -> Record:
    comparison = compare_claim(repository, claim_id)
    group_claim_ids = {item["claim"]["id"] for item in comparison["claims"]}
    history = [
        record
        for record in review_decision_history(repository)
        if record["source_claim_id"] in group_claim_ids
        and record["target_claim_id"] in group_claim_ids
    ]
    active_ids = {record["id"] for record in active_review_decisions(repository)}
    active = [record for record in history if record["id"] in active_ids]
    return {
        "comparison": comparison,
        "decision_count": len(history),
        "active_decision_count": len(active),
        "active_decisions": deepcopy(active),
        "decision_history": deepcopy(history),
    }
