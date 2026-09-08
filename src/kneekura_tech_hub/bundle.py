from __future__ import annotations

import json
from collections import defaultdict, deque
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator

from .repository import RecordRepository
from .service import CurationEngine
from .validator import validate_record


Record = dict[str, Any]
Bundle = dict[str, Any]


class BundleValidationError(ValueError):
    pass


def load_bundle_schema(schema_path: Path | None = None) -> dict[str, Any]:
    if schema_path is None:
        schema_path = (
            Path(__file__).resolve().parents[2]
            / "schemas"
            / "v1"
            / "prototype-bundle.schema.json"
        )
    return json.loads(schema_path.read_text(encoding="utf-8"))


def _dependencies(record: Record) -> set[str]:
    record_type = record.get("record_type")
    dependencies: set[str] = set()

    if record_type == "source_snapshot":
        dependencies.add(record["source_id"])
    elif record_type == "evidence":
        dependencies.update([record["source_id"], record["source_snapshot_id"]])
    elif record_type == "claim":
        dependencies.add(record["entity_id"])
        dependencies.update(record.get("evidence_ids", []))
    elif record_type == "staged_observation":
        dependencies.add(record["source_id"])
        dependencies.update(record.get("evidence_candidate_ids", []))
    elif record_type == "knowledge_entity":
        dependencies.update(
            relation["target"] for relation in record.get("relations", [])
        )

    dependencies.discard(record.get("id"))
    return dependencies


def _creation_actor(record: Record, reviewer_actor: Record) -> Record:
    """Select the actor that actually created a record.

    Canonical identity/source acquisition is performed by the explicit bundle
    reviewer. Candidate claims and staged observations retain their own creator
    identity so AI-created discovery/claim records are not rewritten as human
    provenance.
    """

    if record.get("record_type") in {"claim", "staged_observation"}:
        creator = record.get("created_by")
        if not isinstance(creator, dict):
            raise BundleValidationError("created_by must be an actor object")
        if creator.get("actor_type") == "human" and creator != reviewer_actor:
            raise BundleValidationError(
                "human-created record actor must match the bundle reviewer"
            )
        return creator
    return reviewer_actor


def preflight_bundle(
    bundle: Bundle,
    *,
    repository: RecordRepository | None = None,
    bundle_schema_path: Path | None = None,
) -> list[Record]:
    """Validate a bundle and return a dependency-safe ingestion order.

    Preflight performs no writes. References may resolve either inside the bundle
    or through the supplied repository. Existing IDs may be referenced but may
    not be redefined by the bundle.
    """

    envelope_validator = Draft202012Validator(load_bundle_schema(bundle_schema_path))
    envelope_errors = sorted(
        envelope_validator.iter_errors(bundle), key=lambda error: list(error.path)
    )
    if envelope_errors:
        raise BundleValidationError(
            "; ".join(error.message for error in envelope_errors)
        )

    records: list[Record] = bundle["records"]
    by_id: dict[str, Record] = {}
    errors: list[str] = []

    for index, record in enumerate(records):
        try:
            validate_record(record)
        except ValueError as exc:
            errors.append(f"records[{index}]: {exc}")
            continue

        record_id = record.get("id")
        if not record_id:
            errors.append(f"records[{index}]: record id is required")
            continue
        if record_id in by_id:
            errors.append(f"duplicate bundle record id: {record_id}")
            continue
        if repository is not None and repository.get(record_id) is not None:
            errors.append(f"bundle attempts to redefine existing record: {record_id}")
            continue
        by_id[record_id] = record

    if errors:
        raise BundleValidationError("; ".join(errors))

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
            errors.append(f"{record_id} references missing record: {dependency_id}")

    if errors:
        raise BundleValidationError("; ".join(errors))

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
        raise BundleValidationError(
            "bundle contains cyclic record dependencies: " + ", ".join(cyclic)
        )

    return [by_id[record_id] for record_id in ordered_ids]


def ingest_bundle(
    engine: CurationEngine,
    bundle: Bundle,
    *,
    actor: Record,
) -> list[str]:
    """Preflight and ingest a curated bundle through the governed service layer.

    ``actor`` is the human reviewer/acquisition actor for canonical identities and
    source records. Candidate claims and staged observations retain their declared
    creator identity.
    """

    if actor.get("actor_type") != "human":
        raise BundleValidationError("prototype bundle reviewer must be a human actor")

    ordered = preflight_bundle(bundle, repository=engine.repository)
    stored: list[str] = []

    for record in ordered:
        record_type = record["record_type"]
        creation_actor = _creation_actor(record, actor)
        if record_type == "source":
            engine.register_source(record, actor=creation_actor)
        elif record_type == "source_snapshot":
            engine.register_source_snapshot(record, actor=creation_actor)
        elif record_type == "evidence":
            engine.register_evidence(record, actor=creation_actor)
        elif record_type == "knowledge_entity":
            engine.create_entity(
                record,
                actor=creation_actor,
                reason=f"bundle {bundle['bundle_id']}",
            )
        elif record_type == "claim":
            engine.create_claim(
                record,
                actor=creation_actor,
                reason=f"bundle {bundle['bundle_id']}",
            )
        elif record_type == "staged_observation":
            engine.stage_observation(record, actor=creation_actor)
        else:
            raise BundleValidationError(
                f"record_type cannot be ingested from prototype bundle: {record_type}"
            )
        stored.append(record["id"])

    return stored
