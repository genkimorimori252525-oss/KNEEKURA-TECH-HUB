from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timezone
from hashlib import sha256
import os
from pathlib import Path
import stat
from typing import Any
from uuid import uuid4

from .authorization import authorization_effectiveness
from .execution import (
    AcquisitionExecutionError,
    acquisition_execution_history,
    execution_manifest_sha256,
    git_blob_sha,
    record_fingerprint_sha256,
)
from .repository import Record, RecordRepository
from .validator import validate_record


class VerifiedAcquisitionCommitError(ValueError):
    """Raised when fetched bytes cannot be promoted into canonical Source state."""


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _record(repository: RecordRepository, record_id: str, expected_type: str) -> Record:
    record = repository.get(record_id)
    if record is None:
        raise VerifiedAcquisitionCommitError(f"missing {expected_type}: {record_id}")
    if record.get("record_type") != expected_type:
        raise VerifiedAcquisitionCommitError(
            f"expected {expected_type} for {record_id}, got {record.get('record_type')!r}"
        )
    return record


def _safe_store_directory(storage_root: Path, storage_key: str) -> Path:
    root = Path(storage_root)
    if not root.exists() or not root.is_dir():
        raise VerifiedAcquisitionCommitError("acquisition storage root does not exist or is not a directory")
    if root.is_symlink():
        raise VerifiedAcquisitionCommitError("acquisition storage root must not be a symlink")
    if not storage_key.startswith("ax-") or len(storage_key) != 67:
        raise VerifiedAcquisitionCommitError("execution storage_key is not a valid v1 store key")
    directory = root / storage_key
    if not directory.exists() or not directory.is_dir():
        raise VerifiedAcquisitionCommitError("execution storage directory is missing")
    if directory.is_symlink():
        raise VerifiedAcquisitionCommitError("execution storage directory must not be a symlink")
    return directory


def _expected_directories(paths: list[str]) -> set[str]:
    directories: set[str] = set()
    for raw in paths:
        parts = raw.split("/")[:-1]
        for index in range(1, len(parts) + 1):
            directories.add("/".join(parts[:index]))
    return directories


def _inventory_store(directory: Path) -> tuple[set[str], set[str]]:
    files: set[str] = set()
    directories: set[str] = set()
    for root, dirnames, filenames in os.walk(directory, topdown=True, followlinks=False):
        root_path = Path(root)
        for name in list(dirnames):
            item = root_path / name
            mode = item.lstat().st_mode
            relative = item.relative_to(directory).as_posix()
            if stat.S_ISLNK(mode):
                raise VerifiedAcquisitionCommitError(f"symlink found in execution store: {relative}")
            if not stat.S_ISDIR(mode):
                raise VerifiedAcquisitionCommitError(
                    f"non-directory entry found where directory expected: {relative}"
                )
            directories.add(relative)
        for name in filenames:
            item = root_path / name
            mode = item.lstat().st_mode
            relative = item.relative_to(directory).as_posix()
            if stat.S_ISLNK(mode):
                raise VerifiedAcquisitionCommitError(f"symlink found in execution store: {relative}")
            if not stat.S_ISREG(mode):
                raise VerifiedAcquisitionCommitError(f"non-regular file in execution store: {relative}")
            files.add(relative)
    return files, directories


def verify_execution_store(
    repository: RecordRepository,
    execution_id: str,
    *,
    storage_root: Path,
) -> dict[str, Any]:
    """Re-read and independently verify one successful execution without mutating canonical state."""

    execution = _record(repository, execution_id, "source_acquisition_execution")
    validate_record(execution)
    if execution.get("status") != "SUCCEEDED":
        raise VerifiedAcquisitionCommitError("verified commit requires a SUCCEEDED execution")
    if not execution.get("source_fingerprint_sha256") or not execution.get(
        "authorization_fingerprint_sha256"
    ):
        raise VerifiedAcquisitionCommitError(
            "execution predates required Source/Authorization provenance fingerprints"
        )

    try:
        history = acquisition_execution_history(
            repository,
            authorization_id=execution["authorization_id"],
        )
    except AcquisitionExecutionError as exc:
        raise VerifiedAcquisitionCommitError(str(exc)) from exc
    if not any(item["id"] == execution_id for item in history):
        raise VerifiedAcquisitionCommitError("execution is not present in validated execution history")

    source = _record(repository, execution["source_id"], "source")
    authorization = _record(
        repository,
        execution["authorization_id"],
        "source_acquisition_authorization",
    )
    if record_fingerprint_sha256(source) != execution["source_fingerprint_sha256"]:
        raise VerifiedAcquisitionCommitError("current Source fingerprint differs from execution provenance")
    if record_fingerprint_sha256(authorization) != execution[
        "authorization_fingerprint_sha256"
    ]:
        raise VerifiedAcquisitionCommitError(
            "current Authorization fingerprint differs from execution provenance"
        )

    effectiveness = authorization_effectiveness(repository, authorization["id"])
    if not effectiveness["effective"]:
        raise VerifiedAcquisitionCommitError(
            "Authorization is no longer effective: " + ",".join(effectiveness["blockers"])
        )
    source_level = (source.get("acquisition") or {}).get("level")
    if source_level not in {"metadata-only", "selected-files"}:
        raise VerifiedAcquisitionCommitError(
            "verified commit requires metadata-only intake or governed selected-files refresh"
        )
    if execution["revision"] != authorization["revision"]:
        raise VerifiedAcquisitionCommitError("execution revision differs from Authorization")
    if execution["requested_paths"] != authorization["allowed_paths"]:
        raise VerifiedAcquisitionCommitError("execution requested paths differ from Authorization")

    storage_key = execution.get("storage_key")
    if not isinstance(storage_key, str):
        raise VerifiedAcquisitionCommitError("successful execution has no storage_key")
    directory = _safe_store_directory(Path(storage_root), storage_key)
    actual_files, actual_directories = _inventory_store(directory)
    expected_files = set(execution["requested_paths"])
    if actual_files != expected_files:
        missing = sorted(expected_files - actual_files)
        extra = sorted(actual_files - expected_files)
        raise VerifiedAcquisitionCommitError(
            f"execution store file set differs: missing={missing!r} extra={extra!r}"
        )
    expected_directories = _expected_directories(execution["requested_paths"])
    unexpected_directories = sorted(actual_directories - expected_directories)
    if unexpected_directories:
        raise VerifiedAcquisitionCommitError(
            f"execution store contains unexpected directories: {unexpected_directories!r}"
        )

    by_path = {item["path"]: item for item in execution["file_results"]}
    verified_results: list[Record] = []
    for path in execution["requested_paths"]:
        expected = by_path.get(path)
        if expected is None or expected.get("status") != "FETCHED":
            raise VerifiedAcquisitionCommitError(f"missing FETCHED execution result for {path}")
        file_path = directory.joinpath(*path.split("/"))
        mode = file_path.lstat().st_mode
        if not stat.S_ISREG(mode) or stat.S_ISLNK(mode):
            raise VerifiedAcquisitionCommitError(f"authorized path is not a regular file: {path}")
        content = file_path.read_bytes()
        actual = {
            "path": path,
            "status": "FETCHED",
            "byte_count": len(content),
            "sha256": sha256(content).hexdigest(),
            "git_blob_sha": git_blob_sha(content),
            "error_code": None,
        }
        if actual != expected:
            raise VerifiedAcquisitionCommitError(f"execution store content mismatch for {path}")
        verified_results.append(actual)

    manifest = execution_manifest_sha256(authorization, verified_results)
    if manifest != execution.get("manifest_sha256"):
        raise VerifiedAcquisitionCommitError("execution manifest does not match re-verified store")

    return {
        "execution": deepcopy(execution),
        "source": deepcopy(source),
        "authorization": deepcopy(authorization),
        "verified_file_results": deepcopy(verified_results),
        "manifest_sha256": manifest,
        "storage_directory": directory,
    }


def _snapshot_id(source_id: str, revision: str, manifest_sha256: str) -> str:
    material = f"{source_id}\0{revision}\0{manifest_sha256}".encode("utf-8")
    return "ss:acq:" + sha256(material).hexdigest()


def _commit_id(execution_id: str, snapshot_id: str) -> str:
    material = f"{execution_id}\0{snapshot_id}".encode("utf-8")
    return "vc:" + sha256(material).hexdigest()


def commit_verified_acquisition(
    repository: Any,
    execution_id: str,
    *,
    storage_root: Path,
    actor: Record,
    commit_id: str | None = None,
    policy_version: str = "1.0.0",
) -> Record:
    """Canonicalize one independently re-verified successful acquisition atomically."""

    if actor.get("actor_type") not in {"tool", "system"}:
        raise VerifiedAcquisitionCommitError("verified acquisition commit requires tool/system actor")
    if set(actor) - {"actor_type", "actor_id", "version"}:
        raise VerifiedAcquisitionCommitError("verified acquisition commit actor has unsupported fields")
    atomic = getattr(repository, "commit_verified_acquisition_atomic", None)
    if not callable(atomic):
        raise VerifiedAcquisitionCommitError(
            "repository does not provide atomic verified acquisition commit support"
        )

    verified = verify_execution_store(repository, execution_id, storage_root=storage_root)
    execution: Record = verified["execution"]
    source: Record = verified["source"]
    authorization: Record = verified["authorization"]
    committed_at = _now()
    snapshot_id = _snapshot_id(source["id"], execution["revision"], execution["manifest_sha256"])
    commit_id = commit_id or _commit_id(execution["id"], snapshot_id)

    snapshot: Record = {
        "record_type": "source_snapshot",
        "id": snapshot_id,
        "source_id": source["id"],
        "revision": execution["revision"],
        "content_hash": execution["manifest_sha256"],
        "captured_at": committed_at,
        "metadata": {
            "acquisition_level": "selected-files",
            "content_hash_kind": "selected-files-manifest-sha256",
            "execution_id": execution["id"],
            "authorization_id": authorization["id"],
            "manifest_sha256": execution["manifest_sha256"],
            "storage_key": execution["storage_key"],
            "selected_files": deepcopy(verified["verified_file_results"]),
            "source_fingerprint_sha256": execution["source_fingerprint_sha256"],
            "authorization_fingerprint_sha256": execution[
                "authorization_fingerprint_sha256"
            ],
        },
    }
    validate_record(snapshot)

    source_after = deepcopy(source)
    source_after["acquisition"] = {"level": "selected-files"}
    validate_record(source_after)

    commit_record: Record = {
        "record_type": "source_acquisition_commit",
        "id": commit_id,
        "execution_id": execution["id"],
        "authorization_id": authorization["id"],
        "source_id": source["id"],
        "snapshot_id": snapshot_id,
        "revision": execution["revision"],
        "acquisition_level": "selected-files",
        "manifest_sha256": execution["manifest_sha256"],
        "source_fingerprint_sha256": execution["source_fingerprint_sha256"],
        "authorization_fingerprint_sha256": execution[
            "authorization_fingerprint_sha256"
        ],
        "committed_by": actor,
        "policy_version": policy_version,
        "committed_at": committed_at,
    }
    validate_record(commit_record)

    event: Record = {
        "record_type": "curation_event",
        "id": f"ce:{uuid4()}",
        "operation": "SOURCE_ACQUIRE",
        "actor": actor,
        "subject_ids": [source["id"], snapshot_id, execution["id"], commit_id],
        "reason": "verified selected-file acquisition committed from execution",
        "policy_version": policy_version,
        "occurred_at": committed_at,
        "reversible": False,
    }
    validate_record(event)

    def prewrite_check() -> None:
        latest = verify_execution_store(repository, execution_id, storage_root=storage_root)
        if latest["execution"] != execution:
            raise VerifiedAcquisitionCommitError("Execution changed during commit preparation")
        if latest["source"] != source:
            raise VerifiedAcquisitionCommitError("Source changed during commit preparation")
        if latest["authorization"] != authorization:
            raise VerifiedAcquisitionCommitError("Authorization changed during commit preparation")
        if latest["manifest_sha256"] != verified["manifest_sha256"]:
            raise VerifiedAcquisitionCommitError("execution store manifest changed during commit preparation")
        if latest["verified_file_results"] != verified["verified_file_results"]:
            raise VerifiedAcquisitionCommitError("execution store bytes changed during commit preparation")

    try:
        stored_commit, stored_snapshot, stored_source = atomic(
            expected_source=source,
            expected_authorization=authorization,
            expected_execution=execution,
            source_after=source_after,
            snapshot=snapshot,
            commit_record=commit_record,
            event=event,
            prewrite_check=prewrite_check,
        )
    except (ValueError, RuntimeError) as exc:
        raise VerifiedAcquisitionCommitError(str(exc)) from exc

    if stored_commit != commit_record:
        raise VerifiedAcquisitionCommitError("verified commit round-trip differs from planned record")
    if stored_snapshot != snapshot:
        raise VerifiedAcquisitionCommitError("SourceSnapshot round-trip differs from planned snapshot")
    if stored_source != source_after:
        raise VerifiedAcquisitionCommitError("Source round-trip differs after selected-files promotion")
    return deepcopy(stored_commit)
