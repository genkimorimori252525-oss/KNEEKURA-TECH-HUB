from __future__ import annotations

import base64
from copy import deepcopy
from hashlib import sha1
import json
from pathlib import Path

import pytest

import kneekura_tech_hub.execution as execution_module
from kneekura_tech_hub.authorization import AcquisitionAuthorizationEngine
from kneekura_tech_hub.execution import (
    AcquisitionExecutionError,
    FileFetchError,
    acquisition_execution_history,
    execute_authorized_acquisition,
    fetch_github_file,
)
from kneekura_tech_hub.repository import MemoryRepository
from kneekura_tech_hub.selection import SourceSelectionEngine
from kneekura_tech_hub.validator import HubValidationError, validate_record


SHA = "0123456789abcdef0123456789abcdef01234567"
SOURCE_ID = "src:github:example:executor"
SELECTION_ID = "sd:executor"
AUTHORIZATION_ID = "aa:executor"
HUMAN = {"actor_type": "human", "actor_id": "reviewer"}
TOOL = {"actor_type": "tool", "actor_id": "authorized-fetcher", "version": "v1"}


def _blob_sha(content: bytes) -> str:
    header = f"blob {len(content)}\0".encode("ascii")
    return sha1(header + content).hexdigest()  # noqa: S324 - Git object identity


def _source() -> dict:
    return {
        "record_type": "source",
        "id": SOURCE_ID,
        "kind": "repository",
        "origin": {
            "provider": "github",
            "repository": "example/executor",
            "url": "https://github.com/example/executor",
        },
        "acquisition": {"level": "metadata-only"},
        "license": {
            "state": "KNOWN",
            "declared_expression": "MIT",
            "handling_policy": "REFERENCE_ONLY",
        },
    }


def _authorized_repo(paths: list[str] | None = None) -> tuple[MemoryRepository, dict, dict]:
    repository = MemoryRepository()
    repository.put(_source())
    selection = SourceSelectionEngine(repository).create_from_fields(
        source_id=SOURCE_ID,
        decision="SELECT_FOR_REVIEW",
        rationale="Manual review selected this Source for bounded investigation.",
        actor=HUMAN,
        decision_id=SELECTION_ID,
    )
    authorization = AcquisitionAuthorizationEngine(repository).authorize_from_fields(
        source_id=SOURCE_ID,
        selection_decision_id=selection["id"],
        revision=SHA,
        allowed_paths=paths or ["README.md", "src/lib.rs"],
        rationale="Only the exact pinned files are authorized.",
        actor=HUMAN,
        authorization_id=AUTHORIZATION_ID,
    )
    return repository, selection, authorization


def _offline_fetch(contents: dict[str, bytes]):
    def fetch(_source: dict, revision: str, path: str) -> dict:
        assert revision == SHA
        content = contents[path]
        return {"content": content, "git_blob_sha": _blob_sha(content)}

    return fetch


def _assert_no_published_or_temp_dirs(storage_root: Path) -> None:
    if not storage_root.exists():
        return
    assert list(storage_root.iterdir()) == []


def test_success_is_bounded_verified_and_does_not_create_snapshot(tmp_path: Path):
    repository, _selection, authorization = _authorized_repo()
    before_source = deepcopy(repository.get(SOURCE_ID))
    contents = {"README.md": b"hello\n", "src/lib.rs": b"pub fn x() {}\n"}

    record = execute_authorized_acquisition(
        repository,
        authorization["id"],
        storage_root=tmp_path,
        fetch_file=_offline_fetch(contents),
        actor=TOOL,
        execution_id="ax:success",
    )

    assert record["status"] == "SUCCEEDED"
    assert record["authorization_effective_after"] is True
    assert record["manifest_sha256"]
    assert record["storage_key"].startswith("ax-")
    assert "/" not in record["storage_key"] and "\\" not in record["storage_key"]
    assert [item["path"] for item in record["file_results"]] == authorization["allowed_paths"]
    assert all(item["status"] == "FETCHED" for item in record["file_results"])

    final_dir = tmp_path / record["storage_key"]
    assert (final_dir / "README.md").read_bytes() == contents["README.md"]
    assert (final_dir / "src" / "lib.rs").read_bytes() == contents["src/lib.rs"]
    assert repository.get(SOURCE_ID) == before_source
    assert repository.list("source_snapshot") == []
    assert acquisition_execution_history(repository) == [record]

    with pytest.raises(AcquisitionExecutionError, match="already has a successful execution"):
        execute_authorized_acquisition(
            repository,
            authorization["id"],
            storage_root=tmp_path,
            fetch_file=_offline_fetch(contents),
            actor=TOOL,
        )


def test_execution_id_cannot_escape_storage_root(tmp_path: Path):
    repository, _selection, authorization = _authorized_repo(["README.md"])
    outside = tmp_path.parent / "escape"
    if outside.exists():
        pytest.skip("test fixture path unexpectedly exists")

    record = execute_authorized_acquisition(
        repository,
        authorization["id"],
        storage_root=tmp_path,
        fetch_file=_offline_fetch({"README.md": b"safe"}),
        actor=TOOL,
        execution_id="ax:../../escape",
    )

    assert record["status"] == "SUCCEEDED"
    assert not outside.exists()
    assert (tmp_path / record["storage_key"] / "README.md").read_bytes() == b"safe"


def test_blob_mismatch_fails_closed_and_marks_remaining_paths_not_attempted(tmp_path: Path):
    repository, _selection, authorization = _authorized_repo(
        ["README.md", "src/lib.rs", "docs/design.md"]
    )

    def fetch(_source: dict, _revision: str, path: str) -> dict:
        if path == "README.md":
            return {"content": b"tampered", "git_blob_sha": "0" * 40}
        raise AssertionError("remaining paths must not be fetched after first failure")

    record = execute_authorized_acquisition(
        repository,
        authorization["id"],
        storage_root=tmp_path,
        fetch_file=fetch,
        actor=TOOL,
        execution_id="ax:blob-mismatch",
    )

    assert record["status"] == "FAILED"
    assert record["error_code"] == "GIT_BLOB_MISMATCH"
    assert record["manifest_sha256"] is None
    assert record["storage_key"] is None
    assert [item["path"] for item in record["file_results"]] == authorization["allowed_paths"]
    assert record["file_results"][0]["error_code"] == "GIT_BLOB_MISMATCH"
    assert [item["error_code"] for item in record["file_results"][1:]] == [
        "NOT_ATTEMPTED_AFTER_FAILURE",
        "NOT_ATTEMPTED_AFTER_FAILURE",
    ]
    _assert_no_published_or_temp_dirs(tmp_path)


def test_partial_fetch_failure_discards_already_downloaded_content(tmp_path: Path):
    repository, _selection, authorization = _authorized_repo(
        ["README.md", "src/lib.rs", "docs/design.md"]
    )
    calls: list[str] = []

    def fetch(_source: dict, _revision: str, path: str) -> dict:
        calls.append(path)
        if path == "README.md":
            content = b"first file"
            return {"content": content, "git_blob_sha": _blob_sha(content)}
        if path == "src/lib.rs":
            raise FileFetchError("PATH_NOT_FOUND", "missing exact authorized path")
        raise AssertionError("third path must not be attempted")

    record = execute_authorized_acquisition(
        repository,
        authorization["id"],
        storage_root=tmp_path,
        fetch_file=fetch,
        actor=TOOL,
        execution_id="ax:partial",
    )

    assert calls == ["README.md", "src/lib.rs"]
    assert record["status"] == "FAILED"
    assert record["file_results"][0]["status"] == "FETCHED"
    assert record["file_results"][1]["error_code"] == "PATH_NOT_FOUND"
    assert record["file_results"][2]["error_code"] == "NOT_ATTEMPTED_AFTER_FAILURE"
    _assert_no_published_or_temp_dirs(tmp_path)


def test_authorization_becoming_ineffective_midflight_discards_all_content(tmp_path: Path):
    repository, selection, authorization = _authorized_repo()
    contents = {"README.md": b"one", "src/lib.rs": b"two"}

    def fetch(_source: dict, _revision: str, path: str) -> dict:
        content = contents[path]
        if path == "src/lib.rs":
            SourceSelectionEngine(repository).create_from_fields(
                source_id=SOURCE_ID,
                decision="DEFER",
                rationale="A new concern pauses deeper acquisition immediately.",
                actor=HUMAN,
                decision_id="sd:defer-midflight",
                supersedes_decision_id=selection["id"],
            )
        return {"content": content, "git_blob_sha": _blob_sha(content)}

    record = execute_authorized_acquisition(
        repository,
        authorization["id"],
        storage_root=tmp_path,
        fetch_file=fetch,
        actor=TOOL,
        execution_id="ax:selection-race",
    )

    assert record["status"] == "FAILED"
    assert record["error_code"] == "AUTHORIZATION_BECAME_INEFFECTIVE"
    assert record["authorization_effective_after"] is False
    assert all(item["status"] == "FETCHED" for item in record["file_results"])
    _assert_no_published_or_temp_dirs(tmp_path)


def test_source_provenance_change_midflight_fails_even_if_authority_still_effective(tmp_path: Path):
    repository, _selection, authorization = _authorized_repo()
    contents = {"README.md": b"one", "src/lib.rs": b"two"}

    def fetch(_source: dict, _revision: str, path: str) -> dict:
        content = contents[path]
        if path == "src/lib.rs":
            changed = deepcopy(repository.get(SOURCE_ID))
            changed["origin"]["description"] = "updated during acquisition"
            repository.put(changed, replace=True)
        return {"content": content, "git_blob_sha": _blob_sha(content)}

    record = execute_authorized_acquisition(
        repository,
        authorization["id"],
        storage_root=tmp_path,
        fetch_file=fetch,
        actor=TOOL,
        execution_id="ax:source-race",
    )

    assert record["status"] == "FAILED"
    assert record["error_code"] == "SOURCE_CHANGED_DURING_EXECUTION"
    assert record["authorization_effective_after"] is False
    _assert_no_published_or_temp_dirs(tmp_path)


def test_authorization_record_change_midflight_fails_closed(tmp_path: Path):
    repository, _selection, authorization = _authorized_repo()
    contents = {"README.md": b"one", "src/lib.rs": b"two"}

    def fetch(_source: dict, _revision: str, path: str) -> dict:
        content = contents[path]
        if path == "src/lib.rs":
            changed = deepcopy(repository.get(authorization["id"]))
            changed["rationale"] = "tampered rationale during execution"
            repository.put(changed, replace=True)
        return {"content": content, "git_blob_sha": _blob_sha(content)}

    record = execute_authorized_acquisition(
        repository,
        authorization["id"],
        storage_root=tmp_path,
        fetch_file=fetch,
        actor=TOOL,
        execution_id="ax:authorization-race",
    )

    assert record["status"] == "FAILED"
    assert record["error_code"] == "AUTHORIZATION_CHANGED_DURING_EXECUTION"
    assert record["authorization_effective_after"] is False
    _assert_no_published_or_temp_dirs(tmp_path)


def test_repository_failure_rolls_back_published_files(tmp_path: Path):
    class FailingExecutionRepository(MemoryRepository):
        def put(self, record: dict, *, replace: bool = False) -> None:
            if record.get("record_type") == "source_acquisition_execution":
                raise RuntimeError("simulated persistence failure")
            super().put(record, replace=replace)

    repository = FailingExecutionRepository()
    repository.put(_source())
    selection = SourceSelectionEngine(repository).create_from_fields(
        source_id=SOURCE_ID,
        decision="SELECT_FOR_REVIEW",
        rationale="Select for bounded review.",
        actor=HUMAN,
        decision_id=SELECTION_ID,
    )
    authorization = AcquisitionAuthorizationEngine(repository).authorize_from_fields(
        source_id=SOURCE_ID,
        selection_decision_id=selection["id"],
        revision=SHA,
        allowed_paths=["README.md"],
        rationale="Authorize one file only.",
        actor=HUMAN,
        authorization_id=AUTHORIZATION_ID,
    )

    with pytest.raises(RuntimeError, match="persistence failure"):
        execute_authorized_acquisition(
            repository,
            authorization["id"],
            storage_root=tmp_path,
            fetch_file=_offline_fetch({"README.md": b"persist me only after DB succeeds"}),
            actor=TOOL,
            execution_id="ax:persistence-rollback",
        )

    _assert_no_published_or_temp_dirs(tmp_path)


def test_file_size_limit_is_enforced_before_publication(tmp_path: Path):
    repository, _selection, authorization = _authorized_repo(["large.bin"])
    content = b"x" * (execution_module.MAX_FILE_BYTES + 1)

    record = execute_authorized_acquisition(
        repository,
        authorization["id"],
        storage_root=tmp_path,
        fetch_file=lambda *_args: {"content": content, "git_blob_sha": _blob_sha(content)},
        actor=TOOL,
        execution_id="ax:too-large",
    )

    assert record["status"] == "FAILED"
    assert record["error_code"] == "FILE_TOO_LARGE"
    _assert_no_published_or_temp_dirs(tmp_path)


def test_execution_requires_tool_or_system_actor(tmp_path: Path):
    repository, _selection, authorization = _authorized_repo(["README.md"])
    with pytest.raises(AcquisitionExecutionError, match="tool or system"):
        execute_authorized_acquisition(
            repository,
            authorization["id"],
            storage_root=tmp_path,
            fetch_file=_offline_fetch({"README.md": b"x"}),
            actor=HUMAN,
        )


def test_validator_rejects_semantically_incomplete_success_record():
    malformed = {
        "record_type": "source_acquisition_execution",
        "id": "ax:malformed",
        "authorization_id": AUTHORIZATION_ID,
        "source_id": SOURCE_ID,
        "revision": SHA,
        "requested_paths": ["README.md"],
        "status": "SUCCEEDED",
        "file_results": [],
        "manifest_sha256": None,
        "storage_key": None,
        "error_code": None,
        "executed_by": HUMAN,
        "policy_version": "1.0.0",
        "executed_at": "2026-09-09T00:00:00Z",
        "authorization_effective_after": False,
    }
    with pytest.raises(HubValidationError):
        validate_record(malformed)


class _FakeResponse:
    def __init__(self, payload: dict) -> None:
        self.raw = json.dumps(payload).encode("utf-8")

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def read(self, _limit: int) -> bytes:
        return self.raw


def test_github_fetcher_verifies_path_and_strict_base64(monkeypatch):
    source = _source()
    content = b"hello"
    valid_payload = {
        "type": "file",
        "path": "README.md",
        "encoding": "base64",
        "content": base64.b64encode(content).decode("ascii"),
        "sha": _blob_sha(content),
    }
    monkeypatch.setattr(execution_module, "urlopen", lambda *_args, **_kwargs: _FakeResponse(valid_payload))
    assert fetch_github_file(source, SHA, "README.md") == {
        "content": content,
        "git_blob_sha": _blob_sha(content),
    }

    path_mismatch = dict(valid_payload, path="OTHER.md")
    monkeypatch.setattr(execution_module, "urlopen", lambda *_args, **_kwargs: _FakeResponse(path_mismatch))
    with pytest.raises(FileFetchError) as path_error:
        fetch_github_file(source, SHA, "README.md")
    assert path_error.value.code == "PATH_MISMATCH"

    invalid_base64 = dict(valid_payload, content="%%%not-base64%%%")
    monkeypatch.setattr(execution_module, "urlopen", lambda *_args, **_kwargs: _FakeResponse(invalid_base64))
    with pytest.raises(FileFetchError) as base64_error:
        fetch_github_file(source, SHA, "README.md")
    assert base64_error.value.code == "INVALID_BASE64"