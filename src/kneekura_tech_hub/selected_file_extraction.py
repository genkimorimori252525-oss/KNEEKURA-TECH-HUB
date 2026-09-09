from __future__ import annotations

from contextlib import nullcontext
from copy import deepcopy
from hashlib import sha256
import json
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator

from .execution import execution_manifest_sha256, git_blob_sha, record_fingerprint_sha256
from .repository import Record, RecordRepository
from .service import CurationEngine
from .validator import validate_record
from .verified_commit import _expected_directories, _inventory_store, _safe_store_directory


MAX_ANCHOR_LINES = 400
MAX_ANCHOR_BYTES = 256 * 1024


class SelectedFileExtractionError(ValueError):
    """Raised when a committed selected-file Snapshot cannot safely feed extraction."""


def load_selected_file_extraction_schema(schema_path: Path | None = None) -> dict[str, Any]:
    if schema_path is None:
        schema_path = (
            Path(__file__).resolve().parents[2]
            / "schemas"
            / "v1"
            / "selected-file-extraction-proposal.schema.json"
        )
    return json.loads(schema_path.read_text(encoding="utf-8"))


def _canonical_sha256(value: Any) -> str:
    encoded = json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return sha256(encoded).hexdigest()


def _record(repository: RecordRepository, record_id: str, expected_type: str) -> Record:
    record = repository.get(record_id)
    if record is None:
        raise SelectedFileExtractionError(f"missing {expected_type}: {record_id}")
    if record.get("record_type") != expected_type:
        raise SelectedFileExtractionError(
            f"expected {expected_type} for {record_id}, got {record.get('record_type')!r}"
        )
    validate_record(record)
    return record


def _commit_for_snapshot(repository: RecordRepository, snapshot_id: str) -> Record:
    matches = [
        record
        for record in repository.list("source_acquisition_commit")
        if record.get("snapshot_id") == snapshot_id
    ]
    if len(matches) != 1:
        raise SelectedFileExtractionError(
            f"selected-file Snapshot must have exactly one verified acquisition commit: {snapshot_id}"
        )
    validate_record(matches[0])
    return matches[0]


def verify_committed_selected_file_snapshot(
    repository: RecordRepository,
    snapshot_id: str,
    *,
    storage_root: Path,
) -> dict[str, Any]:
    """Verify one canonical selected-file Snapshot and return its exact bytes.

    Current acquisition Authorization effectiveness is deliberately irrelevant here: the
    authorization was consumed by the earlier verified commit. Historical provenance and bytes,
    rather than continuing authority, govern extraction from an already committed Snapshot.
    """

    snapshot = _record(repository, snapshot_id, "source_snapshot")
    source = _record(repository, snapshot["source_id"], "source")
    commit = _commit_for_snapshot(repository, snapshot_id)
    execution = _record(
        repository,
        commit["execution_id"],
        "source_acquisition_execution",
    )
    authorization = _record(
        repository,
        commit["authorization_id"],
        "source_acquisition_authorization",
    )

    metadata = snapshot.get("metadata") or {}
    if metadata.get("acquisition_level") != "selected-files":
        raise SelectedFileExtractionError("Snapshot is not a selected-files acquisition Snapshot")
    if metadata.get("content_hash_kind") != "selected-files-manifest-sha256":
        raise SelectedFileExtractionError("Snapshot content hash kind is not selected-files manifest SHA-256")
    if (source.get("acquisition") or {}).get("level") not in {"selected-files", "full-source"}:
        raise SelectedFileExtractionError(
            "Source no longer represents at least the committed selected-files acquisition depth"
        )
    if execution.get("status") != "SUCCEEDED":
        raise SelectedFileExtractionError("committed Snapshot references a non-successful execution")

    expected_ids = {
        "source_id": source["id"],
        "snapshot_id": snapshot["id"],
        "execution_id": execution["id"],
        "authorization_id": authorization["id"],
    }
    if commit.get("source_id") != expected_ids["source_id"]:
        raise SelectedFileExtractionError("verified commit Source does not match Snapshot Source")
    if commit.get("snapshot_id") != expected_ids["snapshot_id"]:
        raise SelectedFileExtractionError("verified commit Snapshot ID mismatch")
    if commit.get("execution_id") != expected_ids["execution_id"]:
        raise SelectedFileExtractionError("verified commit Execution ID mismatch")
    if commit.get("authorization_id") != expected_ids["authorization_id"]:
        raise SelectedFileExtractionError("verified commit Authorization ID mismatch")
    if metadata.get("execution_id") != expected_ids["execution_id"]:
        raise SelectedFileExtractionError("Snapshot metadata Execution ID mismatch")
    if metadata.get("authorization_id") != expected_ids["authorization_id"]:
        raise SelectedFileExtractionError("Snapshot metadata Authorization ID mismatch")

    revision = snapshot.get("revision")
    if not isinstance(revision, str) or not revision:
        raise SelectedFileExtractionError("selected-file Snapshot requires an exact revision")
    if not (
        revision == commit.get("revision")
        == execution.get("revision")
        == authorization.get("revision")
    ):
        raise SelectedFileExtractionError("Snapshot/commit/execution/authorization revision mismatch")
    if execution.get("requested_paths") != authorization.get("allowed_paths"):
        raise SelectedFileExtractionError("Execution paths differ from historical Authorization")

    manifest = execution.get("manifest_sha256")
    if not isinstance(manifest, str) or len(manifest) != 64:
        raise SelectedFileExtractionError("committed execution lacks a valid manifest SHA-256")
    if not (
        snapshot.get("content_hash") == manifest
        and metadata.get("manifest_sha256") == manifest
        and commit.get("manifest_sha256") == manifest
    ):
        raise SelectedFileExtractionError("Snapshot manifest provenance is inconsistent")

    if not (
        execution.get("source_fingerprint_sha256")
        == commit.get("source_fingerprint_sha256")
        == metadata.get("source_fingerprint_sha256")
    ):
        raise SelectedFileExtractionError("Source provenance fingerprint chain is inconsistent")
    if not (
        execution.get("authorization_fingerprint_sha256")
        == commit.get("authorization_fingerprint_sha256")
        == metadata.get("authorization_fingerprint_sha256")
    ):
        raise SelectedFileExtractionError("Authorization provenance fingerprint chain is inconsistent")
    if record_fingerprint_sha256(authorization) != execution.get(
        "authorization_fingerprint_sha256"
    ):
        raise SelectedFileExtractionError("historical Authorization record changed after execution")

    expected_results = metadata.get("selected_files")
    if not isinstance(expected_results, list) or expected_results != execution.get("file_results"):
        raise SelectedFileExtractionError("Snapshot selected_files differ from committed execution results")
    if [item.get("path") for item in expected_results] != execution.get("requested_paths"):
        raise SelectedFileExtractionError("Snapshot selected_files do not preserve exact requested path order")
    if any(item.get("status") != "FETCHED" for item in expected_results):
        raise SelectedFileExtractionError("selected-file Snapshot contains a non-FETCHED file result")

    storage_key = metadata.get("storage_key")
    if storage_key != execution.get("storage_key") or not isinstance(storage_key, str):
        raise SelectedFileExtractionError("Snapshot storage key differs from committed execution")
    directory = _safe_store_directory(Path(storage_root), storage_key)
    actual_files, actual_directories = _inventory_store(directory)
    expected_paths = list(execution["requested_paths"])
    expected_file_set = set(expected_paths)
    if actual_files != expected_file_set:
        missing = sorted(expected_file_set - actual_files)
        extra = sorted(actual_files - expected_file_set)
        raise SelectedFileExtractionError(
            f"committed Snapshot store file set differs: missing={missing!r} extra={extra!r}"
        )
    unexpected_directories = sorted(
        actual_directories - _expected_directories(expected_paths)
    )
    if unexpected_directories:
        raise SelectedFileExtractionError(
            f"committed Snapshot store contains unexpected directories: {unexpected_directories!r}"
        )

    by_path = {item["path"]: item for item in expected_results}
    verified_results: list[Record] = []
    contents: dict[str, bytes] = {}
    for path in expected_paths:
        expected = by_path[path]
        content = directory.joinpath(*path.split("/")).read_bytes()
        actual: Record = {
            "path": path,
            "status": "FETCHED",
            "byte_count": len(content),
            "sha256": sha256(content).hexdigest(),
            "git_blob_sha": git_blob_sha(content),
            "error_code": None,
        }
        if actual != expected:
            raise SelectedFileExtractionError(f"committed Snapshot bytes differ for {path}")
        contents[path] = content
        verified_results.append(actual)

    recalculated_manifest = execution_manifest_sha256(authorization, verified_results)
    if recalculated_manifest != manifest:
        raise SelectedFileExtractionError("committed Snapshot manifest does not match re-verified bytes")

    return {
        "source": deepcopy(source),
        "snapshot": deepcopy(snapshot),
        "commit": deepcopy(commit),
        "execution": deepcopy(execution),
        "authorization": deepcopy(authorization),
        "manifest_sha256": manifest,
        "verified_file_results": deepcopy(verified_results),
        "contents": deepcopy(contents),
    }


def _proposal_errors(proposal: dict[str, Any], schema_path: Path | None) -> list[str]:
    validator = Draft202012Validator(load_selected_file_extraction_schema(schema_path))
    return [
        error.message
        for error in sorted(validator.iter_errors(proposal), key=lambda item: list(item.path))
    ]


def _actor_check(actor: Record) -> None:
    if actor.get("actor_type") not in {"human", "ai", "tool", "system"}:
        raise SelectedFileExtractionError("extraction actor_type is invalid")
    if set(actor) - {"actor_type", "actor_id", "version"}:
        raise SelectedFileExtractionError("extraction actor contains unsupported fields")


def _evidence_id(snapshot_id: str, locator: Record) -> str:
    return "ev:extract:" + _canonical_sha256(
        {
            "snapshot_id": snapshot_id,
            "path": locator["path"],
            "line_start": locator["line_start"],
            "line_end": locator["line_end"],
            "content_hash": locator["content_hash"],
        }
    )


def _observation_id(
    snapshot_id: str,
    evidence_ids: list[str],
    summary: str,
    candidate_names: list[str],
    actor: Record,
) -> str:
    return "obs:extract:" + _canonical_sha256(
        {
            "snapshot_id": snapshot_id,
            "evidence_ids": evidence_ids,
            "summary": summary,
            "candidate_names": candidate_names,
            "created_by": actor,
        }
    )


def prepare_selected_file_extraction(
    repository: RecordRepository,
    proposal: dict[str, Any],
    *,
    storage_root: Path,
    actor: Record,
    schema_path: Path | None = None,
) -> dict[str, Any]:
    """Validate untrusted extraction output and build governed records without writing."""

    _actor_check(actor)
    errors = _proposal_errors(proposal, schema_path)
    if errors:
        raise SelectedFileExtractionError("; ".join(errors))

    verified = verify_committed_selected_file_snapshot(
        repository,
        proposal["snapshot_id"],
        storage_root=storage_root,
    )
    snapshot = verified["snapshot"]
    source = verified["source"]
    contents: dict[str, bytes] = verified["contents"]
    file_results = {item["path"]: item for item in verified["verified_file_results"]}

    evidence_by_id: dict[str, Record] = {}
    observations: list[Record] = []
    seen_observation_ids: set[str] = set()

    for finding_index, finding in enumerate(proposal["findings"]):
        evidence_ids: list[str] = []
        for anchor_index, anchor in enumerate(finding["anchors"]):
            path = anchor["path"]
            if path not in contents:
                raise SelectedFileExtractionError(
                    f"findings[{finding_index}].anchors[{anchor_index}] path is not in committed Snapshot: {path}"
                )
            line_start = anchor["line_start"]
            line_end = anchor["line_end"]
            if line_end < line_start:
                raise SelectedFileExtractionError(
                    f"findings[{finding_index}].anchors[{anchor_index}] line_end precedes line_start"
                )
            if line_end - line_start + 1 > MAX_ANCHOR_LINES:
                raise SelectedFileExtractionError(
                    f"findings[{finding_index}].anchors[{anchor_index}] exceeds {MAX_ANCHOR_LINES} lines"
                )

            content = contents[path]
            try:
                content.decode("utf-8", errors="strict")
            except UnicodeDecodeError as exc:
                raise SelectedFileExtractionError(
                    f"finding anchor requires UTF-8 text but committed file is not UTF-8: {path}"
                ) from exc
            lines = content.splitlines(keepends=True)
            if line_start > len(lines) or line_end > len(lines):
                raise SelectedFileExtractionError(
                    f"finding anchor is outside committed file line range: {path}:{line_start}-{line_end}"
                )
            excerpt = b"".join(lines[line_start - 1 : line_end])
            if len(excerpt) > MAX_ANCHOR_BYTES:
                raise SelectedFileExtractionError(
                    f"finding anchor exceeds {MAX_ANCHOR_BYTES} bytes: {path}:{line_start}-{line_end}"
                )

            locator: Record = {
                "type": "source_lines",
                "path": path,
                "line_start": line_start,
                "line_end": line_end,
                "content_hash": "sha256:" + sha256(excerpt).hexdigest(),
                "file_sha256": file_results[path]["sha256"],
                "git_blob_sha": file_results[path]["git_blob_sha"],
                "snapshot_manifest_sha256": verified["manifest_sha256"],
            }
            evidence_id = _evidence_id(snapshot["id"], locator)
            evidence: Record = {
                "record_type": "evidence",
                "id": evidence_id,
                "source_id": source["id"],
                "source_snapshot_id": snapshot["id"],
                "locator": locator,
                "roles": ["SUPPORTS"],
            }
            validate_record(evidence)
            existing_candidate = evidence_by_id.get(evidence_id)
            if existing_candidate is not None and existing_candidate != evidence:
                raise SelectedFileExtractionError(f"generated conflicting Evidence identity: {evidence_id}")
            evidence_by_id[evidence_id] = evidence
            evidence_ids.append(evidence_id)

        normalized_evidence_ids = sorted(set(evidence_ids))
        candidate_names = list(finding.get("candidate_names", []))
        observation_id = _observation_id(
            snapshot["id"],
            normalized_evidence_ids,
            finding["summary"],
            candidate_names,
            actor,
        )
        if observation_id in seen_observation_ids:
            raise SelectedFileExtractionError(
                f"proposal contains a duplicate staged observation: {observation_id}"
            )
        seen_observation_ids.add(observation_id)
        observation: Record = {
            "record_type": "staged_observation",
            "id": observation_id,
            "source_id": source["id"],
            "evidence_candidate_ids": normalized_evidence_ids,
            "summary": finding["summary"],
            "candidate_names": candidate_names,
            "status": "NEW",
            "created_by": deepcopy(actor),
        }
        validate_record(observation)
        observations.append(observation)

    return {
        "proposal_version": proposal["proposal_version"],
        "snapshot_id": snapshot["id"],
        "source_id": source["id"],
        "manifest_sha256": verified["manifest_sha256"],
        "evidence": [evidence_by_id[key] for key in sorted(evidence_by_id)],
        "observations": observations,
    }


def _same_evidence(existing: Record, proposed: Record) -> bool:
    comparable = deepcopy(existing)
    comparable.pop("observed_at", None)
    return comparable == proposed


def _preflight_existing_records(
    repository: RecordRepository,
    prepared: dict[str, Any],
) -> tuple[set[str], set[str]]:
    reused_evidence: set[str] = set()
    reused_observations: set[str] = set()
    for evidence in prepared["evidence"]:
        existing = repository.get(evidence["id"])
        if existing is None:
            continue
        if existing.get("record_type") != "evidence" or not _same_evidence(existing, evidence):
            raise SelectedFileExtractionError(
                f"existing record conflicts with deterministic Evidence identity: {evidence['id']}"
            )
        reused_evidence.add(evidence["id"])

    for observation in prepared["observations"]:
        existing = repository.get(observation["id"])
        if existing is None:
            continue
        if existing != observation:
            raise SelectedFileExtractionError(
                f"existing record conflicts with deterministic Observation identity: {observation['id']}"
            )
        reused_observations.add(observation["id"])
    return reused_evidence, reused_observations


def _lock_postgres_provenance(repository: Any, prepared: dict[str, Any]) -> None:
    connection = getattr(repository, "connection", None)
    if connection is None:
        return
    snapshot_id = prepared["snapshot_id"]
    snapshot = repository.get(snapshot_id)
    if snapshot is None:
        raise SelectedFileExtractionError(f"Snapshot disappeared before extraction ingest: {snapshot_id}")
    commit = _commit_for_snapshot(repository, snapshot_id)
    connection.execute("SELECT id FROM source_snapshot WHERE id=%s FOR SHARE", (snapshot_id,)).fetchone()
    connection.execute(
        "SELECT id FROM source_acquisition_commit WHERE id=%s FOR SHARE",
        (commit["id"],),
    ).fetchone()
    connection.execute(
        "SELECT id FROM source_acquisition_execution WHERE id=%s FOR SHARE",
        (commit["execution_id"],),
    ).fetchone()
    connection.execute(
        "SELECT id FROM source_acquisition_authorization WHERE id=%s FOR SHARE",
        (commit["authorization_id"],),
    ).fetchone()


def ingest_selected_file_extraction(
    engine: CurationEngine,
    proposal: dict[str, Any],
    *,
    storage_root: Path,
    actor: Record,
    schema_path: Path | None = None,
) -> dict[str, Any]:
    """Atomically ingest verified Evidence anchors and NEW StagedObservations only."""

    prepared = prepare_selected_file_extraction(
        engine.repository,
        proposal,
        storage_root=storage_root,
        actor=actor,
        schema_path=schema_path,
    )
    reused_evidence, reused_observations = _preflight_existing_records(
        engine.repository,
        prepared,
    )

    connection = getattr(engine.repository, "connection", None)
    transaction = connection.transaction() if connection is not None else nullcontext()
    with transaction:
        _lock_postgres_provenance(engine.repository, prepared)
        latest = prepare_selected_file_extraction(
            engine.repository,
            proposal,
            storage_root=storage_root,
            actor=actor,
            schema_path=schema_path,
        )
        if latest != prepared:
            raise SelectedFileExtractionError(
                "Snapshot bytes or extraction provenance changed during ingest preparation"
            )
        # Recheck IDs after locks so an interleaving writer cannot turn a preflight reuse into
        # a conflicting record before this transaction publishes the batch.
        locked_reused_evidence, locked_reused_observations = _preflight_existing_records(
            engine.repository,
            prepared,
        )
        reused_evidence |= locked_reused_evidence
        reused_observations |= locked_reused_observations

        for evidence in prepared["evidence"]:
            if evidence["id"] not in reused_evidence:
                engine.register_evidence(evidence, actor=actor)
        for observation in prepared["observations"]:
            if observation["id"] not in reused_observations:
                engine.stage_observation(observation, actor=actor)

    return {
        "snapshot_id": prepared["snapshot_id"],
        "source_id": prepared["source_id"],
        "manifest_sha256": prepared["manifest_sha256"],
        "evidence_ids": [item["id"] for item in prepared["evidence"]],
        "observation_ids": [item["id"] for item in prepared["observations"]],
        "new_evidence_count": len(prepared["evidence"]) - len(reused_evidence),
        "reused_evidence_count": len(reused_evidence),
        "new_observation_count": len(prepared["observations"]) - len(reused_observations),
        "reused_observation_count": len(reused_observations),
    }
