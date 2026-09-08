from __future__ import annotations

from collections import Counter
from copy import deepcopy
from datetime import datetime, timezone
from uuid import uuid4

from .repository import Record, RecordRepository
from .validator import validate_record


class SourceSelectionError(ValueError):
    """Raised when a source review-selection decision is invalid or unsafe."""


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _decision_time(record: Record) -> datetime:
    raw = record.get("decided_at")
    if not isinstance(raw, str) or not raw:
        raise SourceSelectionError(
            f"source selection decision has invalid decided_at: {record.get('id')}"
        )
    try:
        parsed = datetime.fromisoformat(raw.replace("Z", "+00:00"))
    except ValueError as exc:
        raise SourceSelectionError(
            f"source selection decision has invalid decided_at: {record.get('id')}"
        ) from exc
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise SourceSelectionError(
            f"source selection decision decided_at must include timezone: {record.get('id')}"
        )
    return parsed.astimezone(timezone.utc)


def _source(repository: RecordRepository, source_id: str) -> Record:
    record = repository.get(source_id)
    if record is None:
        raise SourceSelectionError(f"missing source: {source_id}")
    if record.get("record_type") != "source":
        raise SourceSelectionError(
            f"expected source for {source_id}, got {record.get('record_type')!r}"
        )
    return record


def _decision(repository: RecordRepository, decision_id: str) -> Record:
    record = repository.get(decision_id)
    if record is None:
        raise SourceSelectionError(f"missing source selection decision: {decision_id}")
    if record.get("record_type") != "source_selection_decision":
        raise SourceSelectionError(
            f"expected source_selection_decision for {decision_id}, "
            f"got {record.get('record_type')!r}"
        )
    return record


def _validate_stored_decision(repository: RecordRepository, record: Record) -> None:
    if record.get("record_type") != "source_selection_decision":
        raise SourceSelectionError(
            f"expected source_selection_decision, got {record.get('record_type')!r}"
        )
    validate_record(record)
    _decision_time(record)
    _source(repository, record["source_id"])


def source_selection_history(
    repository: RecordRepository,
    *,
    source_id: str | None = None,
) -> list[Record]:
    if source_id is not None:
        _source(repository, source_id)

    records = repository.list("source_selection_decision")
    for record in records:
        _validate_stored_decision(repository, record)

    if source_id is not None:
        records = [record for record in records if record["source_id"] == source_id]
    return sorted(records, key=lambda item: (_decision_time(item), item["id"]))


def active_source_selection_decisions(
    repository: RecordRepository,
    *,
    source_id: str | None = None,
) -> list[Record]:
    history = source_selection_history(repository, source_id=source_id)
    all_records = source_selection_history(repository)
    superseded_ids = [
        record["supersedes_decision_id"]
        for record in all_records
        if record.get("supersedes_decision_id") is not None
    ]
    duplicates = [item for item, count in Counter(superseded_ids).items() if count > 1]
    if duplicates:
        raise SourceSelectionError(
            f"source selection decision has multiple successors: {sorted(duplicates)!r}"
        )
    superseded = set(superseded_ids)
    return [record for record in history if record["id"] not in superseded]


class SourceSelectionEngine:
    """Human-gated, append-only metadata review selection for Source records.

    This engine records whether a metadata-only Source should be reviewed more deeply. It never
    mutates Source.acquisition and never grants permission to create a SourceSnapshot or Evidence.
    """

    def __init__(self, repository: RecordRepository, *, policy_version: str = "1.0.0") -> None:
        self.repository = repository
        self.policy_version = policy_version

    def create(self, record: Record, *, actor: Record) -> Record:
        if record.get("record_type") != "source_selection_decision":
            raise SourceSelectionError(
                f"expected source_selection_decision, got {record.get('record_type')!r}"
            )
        if actor.get("actor_type") != "human":
            raise SourceSelectionError("source selection decisions require a human actor")
        if record.get("created_by") != actor:
            raise SourceSelectionError(
                "source selection decision created_by must match the acting identity"
            )
        if record.get("policy_version") != self.policy_version:
            raise SourceSelectionError(
                "source selection decision policy_version must match the active policy"
            )

        source = _source(self.repository, record["source_id"])
        if (source.get("acquisition") or {}).get("level") != "metadata-only":
            raise SourceSelectionError(
                "source selection decisions v1 apply only to metadata-only Sources"
            )

        supersedes = record.get("supersedes_decision_id")
        active = active_source_selection_decisions(
            self.repository,
            source_id=record["source_id"],
        )
        if supersedes is None:
            if active:
                raise SourceSelectionError(
                    "source already has an active selection decision; supersede it explicitly"
                )
        else:
            if supersedes == record["id"]:
                raise SourceSelectionError("source selection decision cannot supersede itself")
            previous = _decision(self.repository, supersedes)
            _validate_stored_decision(self.repository, previous)
            if previous["source_id"] != record["source_id"]:
                raise SourceSelectionError(
                    "superseding source selection decision must concern the same Source"
                )
            if not any(item["id"] == supersedes for item in active):
                raise SourceSelectionError(
                    "superseded source selection decision must be the active decision"
                )

        validate_record(record)
        _decision_time(record)
        self.repository.put(record)

        # Preservation invariant: a selection decision is not an acquisition-level mutation.
        after = _source(self.repository, record["source_id"])
        if after != source:
            raise SourceSelectionError(
                "source changed while recording selection decision; acquisition mutation is forbidden"
            )
        return deepcopy(record)

    def create_from_fields(
        self,
        *,
        source_id: str,
        decision: str,
        rationale: str,
        actor: Record,
        decision_id: str | None = None,
        supersedes_decision_id: str | None = None,
    ) -> Record:
        record: Record = {
            "record_type": "source_selection_decision",
            "id": decision_id or f"sd:{uuid4()}",
            "source_id": source_id,
            "decision": decision,
            "rationale": rationale,
            "created_by": actor,
            "policy_version": self.policy_version,
            "decided_at": _now(),
        }
        if supersedes_decision_id is not None:
            record["supersedes_decision_id"] = supersedes_decision_id
        return self.create(record, actor=actor)


def selected_for_review(repository: RecordRepository) -> list[Record]:
    """Read-only view of active human selections plus the unchanged Source records."""

    selected: list[Record] = []
    for decision in active_source_selection_decisions(repository):
        if decision["decision"] != "SELECT_FOR_REVIEW":
            continue
        source = _source(repository, decision["source_id"])
        selected.append(
            {
                "decision": deepcopy(decision),
                "source": deepcopy(source),
            }
        )
    return selected
