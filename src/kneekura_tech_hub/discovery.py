from __future__ import annotations

import json
from collections import Counter, defaultdict, deque
from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator

from .repository import Record, RecordRepository
from .service import CurationEngine
from .validator import validate_record


DiscoveryBatch = dict[str, Any]
_ALLOWED_TYPES = {"source", "source_snapshot", "evidence", "staged_observation"}
_BLOCKED_CANONICAL_TYPES = {
    "knowledge_entity",
    "claim",
    "review_decision",
    "curation_event",
}


class DiscoveryIntakeError(ValueError):
    """Raised when an untrusted discovery batch cannot enter the staging boundary safely."""


def load_discovery_intake_schema(schema_path: Path | None = None) -> dict[str, Any]:
    if schema_path is None:
        schema_path = (
            Path(__file__).resolve().parents[2]
            / "schemas"
            / "v1"
            / "discovery-intake.schema.json"
        )
    return json.loads(schema_path.read_text(encoding="utf-8"))


def _parse_time(value: Any, *, field: str) -> datetime:
    if not isinstance(value, str) or not value:
        raise DiscoveryIntakeError(f"{field} must be a timezone-aware ISO timestamp")
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise DiscoveryIntakeError(f"{field} must be a timezone-aware ISO timestamp") from exc
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise DiscoveryIntakeError(f"{field} must include a timezone")
    return parsed.astimezone(timezone.utc)


def _github_repository_name(source: Record) -> str:
    if source.get("record_type") != "source":
        raise DiscoveryIntakeError(f"expected source, got {source.get('record_type')!r}")
    if source.get("kind") != "repository":
        raise DiscoveryIntakeError(f"discovery v1 only accepts repository Sources: {source.get('id')}")
    origin = source.get("origin") or {}
    if origin.get("provider") != "github":
        raise DiscoveryIntakeError(f"discovery v1 only accepts GitHub Sources: {source.get('id')}")
    repository = origin.get("repository")
    if not isinstance(repository, str):
        raise DiscoveryIntakeError(f"GitHub Source requires origin.repository: {source.get('id')}")
    parts = repository.strip().split("/")
    if len(parts) != 2 or not all(parts):
        raise DiscoveryIntakeError(
            f"GitHub origin.repository must be owner/name: {source.get('id')}"
        )
    return f"{parts[0].lower()}/{parts[1].lower()}"


def github_source_id(repository: str) -> str:
    parts = repository.strip().split("/")
    if len(parts) != 2 or not all(parts):
        raise DiscoveryIntakeError("GitHub repository must be owner/name")
    return f"src:github:{parts[0].lower()}:{parts[1].lower()}"


def _validate_source_identity(source: Record) -> str:
    repository = _github_repository_name(source)
    expected = github_source_id(repository)
    if source.get("id") != expected:
        raise DiscoveryIntakeError(
            f"GitHub Source ID must be deterministic: expected {expected}, got {source.get('id')}"
        )
    return repository


def _snapshot_prefix_for_source(source_id: str) -> str:
    return "ss:" + source_id.removeprefix("src:") + ":"


def _dependencies(record: Record) -> set[str]:
    record_type = record.get("record_type")
    if record_type == "source":
        return set()
    if record_type == "source_snapshot":
        return {record["source_id"]}
    if record_type == "evidence":
        return {record["source_id"], record["source_snapshot_id"]}
    if record_type == "staged_observation":
        return {record["source_id"], *record.get("evidence_candidate_ids", [])}
    raise DiscoveryIntakeError(f"blocked discovery record_type: {record_type!r}")


def _get_record(
    record_id: str,
    *,
    by_id: dict[str, Record],
    repository: RecordRepository | None,
    expected_type: str,
) -> Record:
    record = by_id.get(record_id)
    if record is None and repository is not None:
        record = repository.get(record_id)
    if record is None:
        raise DiscoveryIntakeError(f"missing dependency: {record_id}")
    if record.get("record_type") != expected_type:
        raise DiscoveryIntakeError(
            f"expected {expected_type} for {record_id}, got {record.get('record_type')!r}"
        )
    return record


def _validate_existing_github_source_uniqueness(
    source: Record,
    repository: RecordRepository | None,
) -> None:
    if repository is None:
        return
    logical_name = _github_repository_name(source)
    expected = github_source_id(logical_name)
    for existing in repository.list("source"):
        try:
            existing_name = _github_repository_name(existing)
        except DiscoveryIntakeError:
            continue
        if existing_name == logical_name and existing["id"] != expected:
            raise DiscoveryIntakeError(
                f"GitHub repository already exists under non-deterministic Source ID: "
                f"{existing['id']}"
            )


def _require_acquired_source(source: Record, *, dependent_id: str) -> None:
    acquisition = (source.get("acquisition") or {}).get("level")
    if acquisition == "metadata-only":
        raise DiscoveryIntakeError(
            f"{dependent_id} cannot use metadata-only Source {source.get('id')}"
        )


def preflight_discovery_intake(
    batch: DiscoveryBatch,
    *,
    repository: RecordRepository | None = None,
    schema_path: Path | None = None,
) -> list[Record]:
    """Validate an untrusted discovery batch and return a dependency-safe write order.

    This function performs no writes. The only writable semantic surface is provenance and
    staging: Source, SourceSnapshot, Evidence, and NEW StagedObservation records.
    """

    envelope = Draft202012Validator(load_discovery_intake_schema(schema_path))
    envelope_errors = sorted(envelope.iter_errors(batch), key=lambda error: list(error.path))
    if envelope_errors:
        raise DiscoveryIntakeError("; ".join(error.message for error in envelope_errors))

    _parse_time(batch["discovered_at"], field="discovered_at")
    discovered_by = batch["discovered_by"]
    records: list[Record] = batch["records"]
    by_id: dict[str, Record] = {}
    errors: list[str] = []

    for index, record in enumerate(records):
        record_type = record.get("record_type")
        if record_type not in _ALLOWED_TYPES:
            blocked = "canonical" if record_type in _BLOCKED_CANONICAL_TYPES else "unsupported"
            errors.append(f"records[{index}]: {blocked} discovery record_type {record_type!r}")
            continue
        try:
            validate_record(record)
        except ValueError as exc:
            errors.append(f"records[{index}]: {exc}")
            continue

        record_id = record.get("id")
        if not isinstance(record_id, str) or not record_id:
            errors.append(f"records[{index}]: record id is required")
            continue
        if record_id in by_id:
            errors.append(f"duplicate discovery record id: {record_id}")
            continue
        if repository is not None and repository.get(record_id) is not None:
            errors.append(f"discovery attempts to redefine existing record: {record_id}")
            continue

        if record_type == "source":
            try:
                _validate_source_identity(record)
                _validate_existing_github_source_uniqueness(record, repository)
            except DiscoveryIntakeError as exc:
                errors.append(f"records[{index}]: {exc}")
                continue
        elif record_type == "staged_observation":
            if record.get("status") != "NEW":
                errors.append(
                    f"records[{index}]: discovery observations must enter with status NEW"
                )
                continue
            candidate_names = record.get("candidate_names") or []
            if not candidate_names:
                errors.append(
                    f"records[{index}]: discovery observations require candidate_names"
                )
                continue
            if record.get("created_by") != discovered_by:
                errors.append(
                    f"records[{index}]: observation created_by must match discovered_by"
                )
                continue

        by_id[record_id] = record

    if errors:
        raise DiscoveryIntakeError("; ".join(errors))

    existing_source_names: dict[str, str] = {}
    if repository is not None:
        for source in repository.list("source"):
            try:
                name = _github_repository_name(source)
            except DiscoveryIntakeError:
                continue
            previous = existing_source_names.get(name)
            if previous is not None and previous != source["id"]:
                raise DiscoveryIntakeError(
                    f"repository already contains duplicate GitHub Source identities: "
                    f"{previous}, {source['id']}"
                )
            existing_source_names[name] = source["id"]

    new_source_names: dict[str, str] = {}
    for record in by_id.values():
        if record["record_type"] != "source":
            continue
        name = _github_repository_name(record)
        duplicate = new_source_names.get(name)
        if duplicate is not None and duplicate != record["id"]:
            raise DiscoveryIntakeError(
                f"batch contains duplicate GitHub Source identity: {duplicate}, {record['id']}"
            )
        existing = existing_source_names.get(name)
        if existing is not None and existing != record["id"]:
            raise DiscoveryIntakeError(
                f"GitHub repository already exists as Source {existing}"
            )
        new_source_names[name] = record["id"]

    # Resolve and validate semantic dependencies before any write can happen.
    for record in by_id.values():
        record_type = record["record_type"]
        if record_type == "source":
            continue

        if record_type == "source_snapshot":
            source = _get_record(
                record["source_id"],
                by_id=by_id,
                repository=repository,
                expected_type="source",
            )
            _validate_source_identity(source)
            _require_acquired_source(source, dependent_id=record["id"])
            if not record["id"].startswith(_snapshot_prefix_for_source(source["id"])):
                raise DiscoveryIntakeError(
                    f"SourceSnapshot ID must be namespaced by its Source: {record['id']}"
                )
            continue

        if record_type == "evidence":
            source = _get_record(
                record["source_id"],
                by_id=by_id,
                repository=repository,
                expected_type="source",
            )
            snapshot = _get_record(
                record["source_snapshot_id"],
                by_id=by_id,
                repository=repository,
                expected_type="source_snapshot",
            )
            _validate_source_identity(source)
            _require_acquired_source(source, dependent_id=record["id"])
            if snapshot["source_id"] != source["id"]:
                raise DiscoveryIntakeError(
                    f"Evidence snapshot does not belong to Evidence Source: {record['id']}"
                )
            continue

        if record_type == "staged_observation":
            source = _get_record(
                record["source_id"],
                by_id=by_id,
                repository=repository,
                expected_type="source",
            )
            _validate_source_identity(source)
            evidence_ids = record.get("evidence_candidate_ids") or []
            snapshots: set[str] = set()
            for evidence_id in evidence_ids:
                evidence = _get_record(
                    evidence_id,
                    by_id=by_id,
                    repository=repository,
                    expected_type="evidence",
                )
                if evidence["source_id"] != source["id"]:
                    raise DiscoveryIntakeError(
                        f"Observation Evidence does not belong to Observation Source: {record['id']}"
                    )
                snapshots.add(evidence["source_snapshot_id"])
            if len(snapshots) != 1:
                raise DiscoveryIntakeError(
                    f"Discovery observation must resolve to exactly one SourceSnapshot: {record['id']}"
                )

    # Topological order permits intentionally scrambled crawler output.
    indegree: dict[str, int] = {record_id: 0 for record_id in by_id}
    outgoing: dict[str, set[str]] = defaultdict(set)
    for record_id, record in by_id.items():
        for dependency_id in _dependencies(record):
            if dependency_id in by_id:
                outgoing[dependency_id].add(record_id)
                indegree[record_id] += 1
                continue
            if repository is not None and repository.get(dependency_id) is not None:
                continue
            raise DiscoveryIntakeError(f"{record_id} references missing record: {dependency_id}")

    ready = deque(sorted(record_id for record_id, degree in indegree.items() if degree == 0))
    ordered_ids: list[str] = []
    while ready:
        record_id = ready.popleft()
        ordered_ids.append(record_id)
        for dependent in sorted(outgoing[record_id]):
            indegree[dependent] -= 1
            if indegree[dependent] == 0:
                ready.append(dependent)

    if len(ordered_ids) != len(by_id):
        cyclic = sorted(record_id for record_id, degree in indegree.items() if degree > 0)
        raise DiscoveryIntakeError(
            "discovery batch contains cyclic dependencies: " + ", ".join(cyclic)
        )

    return [by_id[record_id] for record_id in ordered_ids]


def ingest_discovery_intake(
    engine: CurationEngine,
    batch: DiscoveryBatch,
    *,
    actor: Record,
) -> Record:
    """Ingest only provenance/staging records through governed service methods.

    Callers that use PostgreSQL should wrap this function in one database transaction.
    """

    if actor != batch.get("discovered_by"):
        raise DiscoveryIntakeError("acting identity must exactly match batch discovered_by")

    ordered = preflight_discovery_intake(batch, repository=engine.repository)
    stored_ids: list[str] = []
    counts: Counter[str] = Counter()

    for record in ordered:
        record_type = record["record_type"]
        if record_type == "source":
            engine.register_source(record, actor=actor)
        elif record_type == "source_snapshot":
            engine.register_source_snapshot(record, actor=actor)
        elif record_type == "evidence":
            engine.register_evidence(record, actor=actor)
        elif record_type == "staged_observation":
            engine.stage_observation(record, actor=actor)
        else:  # defense in depth if the allowlist changes incorrectly later
            raise DiscoveryIntakeError(f"blocked discovery record_type: {record_type!r}")
        stored_ids.append(record["id"])
        counts[record_type] += 1

    return {
        "intake_version": batch["intake_version"],
        "batch_id": batch["batch_id"],
        "discovered_by": deepcopy(batch["discovered_by"]),
        "discovered_at": batch["discovered_at"],
        "stored_ids": stored_ids,
        "counts": dict(sorted(counts.items())),
        "canonical_knowledge_writes": 0,
        "allowed_record_types": sorted(_ALLOWED_TYPES),
    }
