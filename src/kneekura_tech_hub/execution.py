from __future__ import annotations

import base64
from copy import deepcopy
from datetime import datetime, timezone
from hashlib import sha1, sha256
import json
import os
from pathlib import Path
import shutil
import tempfile
from typing import Any, Callable
from urllib.error import HTTPError, URLError
from urllib.parse import quote, urlencode
from urllib.request import Request, urlopen
from uuid import uuid4

from .authorization import authorization_effectiveness
from .repository import Record, RecordRepository
from .validator import validate_record


MAX_FILE_BYTES = 1024 * 1024
MAX_TOTAL_BYTES = 8 * 1024 * 1024
MAX_API_RESPONSE_BYTES = 2 * 1024 * 1024


class AcquisitionExecutionError(ValueError):
    """Raised before or during an authorized acquisition execution."""


class FileFetchError(AcquisitionExecutionError):
    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code


FetchFile = Callable[[Record, str, str], dict[str, Any]]


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def git_blob_sha(content: bytes) -> str:
    """Return the canonical Git blob identity for exact file bytes."""
    header = f"blob {len(content)}\0".encode("ascii")
    return sha1(header + content).hexdigest()  # noqa: S324 - Git object identity, not security


def record_fingerprint_sha256(record: Record) -> str:
    """Fingerprint a full Hub record using deterministic canonical JSON."""
    encoded = json.dumps(
        record,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return sha256(encoded).hexdigest()


def _storage_key(execution_id: str) -> str:
    """Derive an opaque filesystem-safe key from the logical execution ID."""
    return "ax-" + sha256(execution_id.encode("utf-8")).hexdigest()


def _source(repository: RecordRepository, source_id: str) -> Record:
    record = repository.get(source_id)
    if record is None or record.get("record_type") != "source":
        raise AcquisitionExecutionError(f"missing Source for execution: {source_id}")
    return record


def _authorization(repository: RecordRepository, authorization_id: str) -> Record:
    record = repository.get(authorization_id)
    if record is None or record.get("record_type") != "source_acquisition_authorization":
        raise AcquisitionExecutionError(f"missing authorization: {authorization_id}")
    return record


def _execution_time(record: Record) -> datetime:
    raw = record.get("executed_at")
    if not isinstance(raw, str):
        raise AcquisitionExecutionError(f"invalid execution timestamp: {record.get('id')}")
    try:
        parsed = datetime.fromisoformat(raw.replace("Z", "+00:00"))
    except ValueError as exc:
        raise AcquisitionExecutionError(f"invalid execution timestamp: {record.get('id')}") from exc
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise AcquisitionExecutionError(
            f"execution timestamp must include timezone: {record.get('id')}"
        )
    return parsed.astimezone(timezone.utc)


def acquisition_execution_history(
    repository: RecordRepository,
    *,
    authorization_id: str | None = None,
    source_id: str | None = None,
) -> list[Record]:
    records = repository.list("source_acquisition_execution")
    result: list[Record] = []
    for record in records:
        validate_record(record)
        _execution_time(record)
        authorization = _authorization(repository, record["authorization_id"])
        source = _source(repository, record["source_id"])
        if authorization["source_id"] != source["id"]:
            raise AcquisitionExecutionError(
                f"execution authorization/source mismatch: {record['id']}"
            )
        if record["revision"] != authorization["revision"]:
            raise AcquisitionExecutionError(f"execution revision mismatch: {record['id']}")
        if record["requested_paths"] != authorization["allowed_paths"]:
            raise AcquisitionExecutionError(f"execution path scope mismatch: {record['id']}")
        if authorization_id is not None and record["authorization_id"] != authorization_id:
            continue
        if source_id is not None and record["source_id"] != source_id:
            continue
        result.append(record)
    return sorted(result, key=lambda item: (_execution_time(item), item["id"]))


def _already_succeeded(repository: RecordRepository, authorization_id: str) -> bool:
    return any(
        item["status"] == "SUCCEEDED"
        for item in acquisition_execution_history(repository, authorization_id=authorization_id)
    )


def _failure_record(
    *,
    execution_id: str,
    authorization: Record,
    file_results: list[Record],
    error_code: str,
    actor: Record,
    policy_version: str,
    authorization_effective_after: bool,
    source_fingerprint_sha256: str,
    authorization_fingerprint_sha256: str,
) -> Record:
    record: Record = {
        "record_type": "source_acquisition_execution",
        "id": execution_id,
        "authorization_id": authorization["id"],
        "source_id": authorization["source_id"],
        "revision": authorization["revision"],
        "requested_paths": deepcopy(authorization["allowed_paths"]),
        "status": "FAILED",
        "file_results": file_results,
        "manifest_sha256": None,
        "storage_key": None,
        "error_code": error_code,
        "executed_by": actor,
        "policy_version": policy_version,
        "executed_at": _now(),
        "authorization_effective_after": authorization_effective_after,
        "source_fingerprint_sha256": source_fingerprint_sha256,
        "authorization_fingerprint_sha256": authorization_fingerprint_sha256,
    }
    validate_record(record)
    return record


def execution_manifest_sha256(authorization: Record, file_results: list[Record]) -> str:
    """Return the deterministic integrity handle for one selected-files execution."""
    material = {
        "authorization_id": authorization["id"],
        "source_id": authorization["source_id"],
        "revision": authorization["revision"],
        "files": [
            {
                "path": item["path"],
                "byte_count": item["byte_count"],
                "sha256": item["sha256"],
                "git_blob_sha": item["git_blob_sha"],
            }
            for item in file_results
        ],
    }
    encoded = json.dumps(
        material,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return sha256(encoded).hexdigest()


def execute_authorized_acquisition(
    repository: RecordRepository,
    authorization_id: str,
    *,
    storage_root: Path,
    fetch_file: FetchFile,
    actor: Record,
    execution_id: str | None = None,
    policy_version: str = "1.0.0",
) -> Record:
    """Retrieve exactly one currently-effective authorization into a private local store.

    Successful retrieval is recorded separately from authorization and does not mutate the
    Source or create a SourceSnapshot. Any file failure, provenance race, or post-fetch
    authorization invalidation discards temporary content and records a FAILED execution.
    """

    if actor.get("actor_type") not in {"tool", "system"}:
        raise AcquisitionExecutionError("acquisition execution requires a tool or system actor")
    allowed_actor_fields = {"actor_type", "actor_id", "version"}
    if set(actor) - allowed_actor_fields:
        raise AcquisitionExecutionError("acquisition execution actor contains unsupported fields")

    status = authorization_effectiveness(repository, authorization_id)
    if not status["effective"]:
        raise AcquisitionExecutionError(
            "authorization is not currently effective: " + ",".join(status["blockers"])
        )
    authorization = status["authorization"]
    source = status["source"]
    source_fingerprint = record_fingerprint_sha256(source)
    authorization_fingerprint = record_fingerprint_sha256(authorization)

    if _already_succeeded(repository, authorization_id):
        raise AcquisitionExecutionError("authorization already has a successful execution")

    execution_id = execution_id or f"ax:{uuid4()}"
    storage_root = Path(storage_root)
    storage_root.mkdir(parents=True, exist_ok=True)
    temp_dir = Path(tempfile.mkdtemp(prefix=".ax-", dir=storage_root))
    file_results: list[Record] = []
    total_bytes = 0

    try:
        for index, path in enumerate(authorization["allowed_paths"]):
            try:
                fetched = fetch_file(source, authorization["revision"], path)
                content = fetched.get("content")
                provider_blob_sha = fetched.get("git_blob_sha")
                if not isinstance(content, bytes):
                    raise FileFetchError("INVALID_FETCH_PAYLOAD", "fetcher did not return bytes")
                if len(content) > MAX_FILE_BYTES:
                    raise FileFetchError("FILE_TOO_LARGE", f"file exceeds {MAX_FILE_BYTES} bytes")
                total_bytes += len(content)
                if total_bytes > MAX_TOTAL_BYTES:
                    raise FileFetchError("TOTAL_TOO_LARGE", "execution exceeds total byte limit")

                computed_blob_sha = git_blob_sha(content)
                if not isinstance(provider_blob_sha, str) or provider_blob_sha != computed_blob_sha:
                    raise FileFetchError(
                        "GIT_BLOB_MISMATCH",
                        f"provider blob identity mismatch for {path}",
                    )

                destination = temp_dir.joinpath(*path.split("/"))
                destination.parent.mkdir(parents=True, exist_ok=True)
                destination.write_bytes(content)
                file_results.append(
                    {
                        "path": path,
                        "status": "FETCHED",
                        "byte_count": len(content),
                        "sha256": sha256(content).hexdigest(),
                        "git_blob_sha": computed_blob_sha,
                        "error_code": None,
                    }
                )
            except FileFetchError as exc:
                file_results.append(
                    {
                        "path": path,
                        "status": "FAILED",
                        "byte_count": None,
                        "sha256": None,
                        "git_blob_sha": None,
                        "error_code": exc.code,
                    }
                )
                for remaining in authorization["allowed_paths"][index + 1 :]:
                    file_results.append(
                        {
                            "path": remaining,
                            "status": "FAILED",
                            "byte_count": None,
                            "sha256": None,
                            "git_blob_sha": None,
                            "error_code": "NOT_ATTEMPTED_AFTER_FAILURE",
                        }
                    )
                shutil.rmtree(temp_dir, ignore_errors=True)
                effective_after = authorization_effectiveness(repository, authorization_id)["effective"]
                record = _failure_record(
                    execution_id=execution_id,
                    authorization=authorization,
                    file_results=file_results,
                    error_code=exc.code,
                    actor=actor,
                    policy_version=policy_version,
                    authorization_effective_after=effective_after,
                    source_fingerprint_sha256=source_fingerprint,
                    authorization_fingerprint_sha256=authorization_fingerprint,
                )
                repository.put(record)
                return deepcopy(record)
            except Exception:  # convert untrusted fetcher failure into governed result
                file_results.append(
                    {
                        "path": path,
                        "status": "FAILED",
                        "byte_count": None,
                        "sha256": None,
                        "git_blob_sha": None,
                        "error_code": "FETCH_FAILED",
                    }
                )
                for remaining in authorization["allowed_paths"][index + 1 :]:
                    file_results.append(
                        {
                            "path": remaining,
                            "status": "FAILED",
                            "byte_count": None,
                            "sha256": None,
                            "git_blob_sha": None,
                            "error_code": "NOT_ATTEMPTED_AFTER_FAILURE",
                        }
                    )
                shutil.rmtree(temp_dir, ignore_errors=True)
                effective_after = authorization_effectiveness(repository, authorization_id)["effective"]
                record = _failure_record(
                    execution_id=execution_id,
                    authorization=authorization,
                    file_results=file_results,
                    error_code="FETCH_FAILED",
                    actor=actor,
                    policy_version=policy_version,
                    authorization_effective_after=effective_after,
                    source_fingerprint_sha256=source_fingerprint,
                    authorization_fingerprint_sha256=authorization_fingerprint,
                )
                repository.put(record)
                return deepcopy(record)

        postflight = authorization_effectiveness(repository, authorization_id)
        if not postflight["effective"]:
            shutil.rmtree(temp_dir, ignore_errors=True)
            record = _failure_record(
                execution_id=execution_id,
                authorization=authorization,
                file_results=file_results,
                error_code="AUTHORIZATION_BECAME_INEFFECTIVE",
                actor=actor,
                policy_version=policy_version,
                authorization_effective_after=False,
                source_fingerprint_sha256=source_fingerprint,
                authorization_fingerprint_sha256=authorization_fingerprint,
            )
            repository.put(record)
            return deepcopy(record)
        if postflight["authorization"] != authorization:
            shutil.rmtree(temp_dir, ignore_errors=True)
            record = _failure_record(
                execution_id=execution_id,
                authorization=authorization,
                file_results=file_results,
                error_code="AUTHORIZATION_CHANGED_DURING_EXECUTION",
                actor=actor,
                policy_version=policy_version,
                authorization_effective_after=postflight["effective"],
                source_fingerprint_sha256=source_fingerprint,
                authorization_fingerprint_sha256=authorization_fingerprint,
            )
            repository.put(record)
            return deepcopy(record)
        if postflight["source"] != source:
            shutil.rmtree(temp_dir, ignore_errors=True)
            record = _failure_record(
                execution_id=execution_id,
                authorization=authorization,
                file_results=file_results,
                error_code="SOURCE_CHANGED_DURING_EXECUTION",
                actor=actor,
                policy_version=policy_version,
                authorization_effective_after=postflight["effective"],
                source_fingerprint_sha256=source_fingerprint,
                authorization_fingerprint_sha256=authorization_fingerprint,
            )
            repository.put(record)
            return deepcopy(record)

        manifest_sha = execution_manifest_sha256(authorization, file_results)
        storage_key = _storage_key(execution_id)
        final_dir = storage_root / storage_key
        if final_dir.exists():
            raise AcquisitionExecutionError(f"storage destination already exists: {storage_key}")
        os.replace(temp_dir, final_dir)

        record: Record = {
            "record_type": "source_acquisition_execution",
            "id": execution_id,
            "authorization_id": authorization["id"],
            "source_id": authorization["source_id"],
            "revision": authorization["revision"],
            "requested_paths": deepcopy(authorization["allowed_paths"]),
            "status": "SUCCEEDED",
            "file_results": file_results,
            "manifest_sha256": manifest_sha,
            "storage_key": storage_key,
            "error_code": None,
            "executed_by": actor,
            "policy_version": policy_version,
            "executed_at": _now(),
            "authorization_effective_after": True,
            "source_fingerprint_sha256": source_fingerprint,
            "authorization_fingerprint_sha256": authorization_fingerprint,
        }
        validate_record(record)
        try:
            repository.put(record)
        except Exception:
            shutil.rmtree(final_dir, ignore_errors=True)
            raise
        return deepcopy(record)
    finally:
        if temp_dir.exists():
            shutil.rmtree(temp_dir, ignore_errors=True)


def fetch_github_file(
    source: Record,
    revision: str,
    path: str,
    *,
    token: str | None = None,
    timeout: float = 30.0,
) -> dict[str, Any]:
    """Fetch one file through GitHub's fixed Contents API at an exact commit revision."""

    origin = source.get("origin") or {}
    if origin.get("provider") != "github":
        raise FileFetchError("UNSUPPORTED_PROVIDER", "v1 executor supports GitHub Sources only")
    repository = origin.get("repository")
    if not isinstance(repository, str) or len(repository.split("/")) != 2:
        raise FileFetchError("INVALID_REPOSITORY", "GitHub Source requires owner/name repository")
    owner, name = repository.split("/", 1)
    if not owner or not name:
        raise FileFetchError("INVALID_REPOSITORY", "GitHub Source requires owner/name repository")

    encoded_path = quote(path, safe="/")
    url = (
        f"https://api.github.com/repos/{quote(owner, safe='')}/{quote(name, safe='')}/contents/"
        f"{encoded_path}?{urlencode({'ref': revision})}"
    )
    request = Request(
        url,
        headers={
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
            "User-Agent": "KNEEKURA-TECH-HUB/authorized-acquisition-execution-v1",
            **({"Authorization": f"Bearer {token}"} if token else {}),
        },
    )
    try:
        with urlopen(request, timeout=timeout) as response:  # noqa: S310 - fixed GitHub API host
            raw = response.read(MAX_API_RESPONSE_BYTES + 1)
    except HTTPError as exc:
        code = "PATH_NOT_FOUND" if exc.code == 404 else f"GITHUB_HTTP_{exc.code}"
        raise FileFetchError(code, f"GitHub Contents API returned HTTP {exc.code}") from exc
    except URLError as exc:
        raise FileFetchError("GITHUB_TRANSPORT_ERROR", str(exc.reason)) from exc

    if len(raw) > MAX_API_RESPONSE_BYTES:
        raise FileFetchError("API_RESPONSE_TOO_LARGE", "GitHub API response exceeds v1 limit")
    try:
        payload = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise FileFetchError("INVALID_GITHUB_RESPONSE", "GitHub returned invalid JSON") from exc
    if not isinstance(payload, dict) or payload.get("type") != "file":
        raise FileFetchError("NOT_A_FILE", "authorized path did not resolve to a file")
    if payload.get("encoding") != "base64" or not isinstance(payload.get("content"), str):
        raise FileFetchError("CONTENT_NOT_INLINE", "file content was not available inline")
    if payload.get("path") not in (None, path):
        raise FileFetchError("PATH_MISMATCH", "GitHub response path differs from authorized path")
    provider_sha = payload.get("sha")
    if not isinstance(provider_sha, str) or len(provider_sha) != 40:
        raise FileFetchError("INVALID_BLOB_SHA", "GitHub response lacks a full blob SHA")
    try:
        compact_base64 = "".join(payload["content"].split())
        content = base64.b64decode(compact_base64, validate=True)
    except (ValueError, TypeError) as exc:
        raise FileFetchError("INVALID_BASE64", "GitHub file content was not valid base64") from exc
    return {"content": content, "git_blob_sha": provider_sha}
