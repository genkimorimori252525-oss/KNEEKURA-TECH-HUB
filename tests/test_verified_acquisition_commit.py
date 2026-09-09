from __future__ import annotations

from copy import deepcopy
from hashlib import sha1
import os
from pathlib import Path

import pytest

from kneekura_tech_hub.authorization import AcquisitionAuthorizationEngine
from kneekura_tech_hub.execution import execute_authorized_acquisition
from kneekura_tech_hub.repository import MemoryRepository
from kneekura_tech_hub.selection import SourceSelectionEngine
from kneekura_tech_hub.verified_commit import (
    VerifiedAcquisitionCommitError,
    verify_execution_store,
)


SHA = "0123456789abcdef0123456789abcdef01234567"
SOURCE_ID = "src:github:example:verified-commit"
HUMAN = {"actor_type": "human", "actor_id": "reviewer"}
TOOL = {"actor_type": "tool", "actor_id": "fetcher", "version": "v1"}


def _blob_sha(content: bytes) -> str:
    header = f"blob {len(content)}\0".encode("ascii")
    return sha1(header + content).hexdigest()  # noqa: S324 - Git identity


def _source() -> dict:
    return {
        "record_type": "source",
        "id": SOURCE_ID,
        "kind": "repository",
        "origin": {
            "provider": "github",
            "repository": "example/verified-commit",
            "url": "https://github.com/example/verified-commit",
        },
        "acquisition": {"level": "metadata-only"},
        "license": {
            "state": "KNOWN",
            "declared_expression": "MIT",
            "handling_policy": "REFERENCE_ONLY",
        },
    }


def _successful_execution(tmp_path: Path):
    repository = MemoryRepository()
    repository.put(_source())
    selection = SourceSelectionEngine(repository).create_from_fields(
        source_id=SOURCE_ID,
        decision="SELECT_FOR_REVIEW",
        rationale="Select exact source for bounded verification.",
        actor=HUMAN,
        decision_id="sd:verified-commit",
    )
    authorization = AcquisitionAuthorizationEngine(repository).authorize_from_fields(
        source_id=SOURCE_ID,
        selection_decision_id=selection["id"],
        revision=SHA,
        allowed_paths=["README.md", "src/lib.rs"],
        rationale="Authorize two exact files.",
        actor=HUMAN,
        authorization_id="aa:verified-commit",
    )
    contents = {"README.md": b"readme\n", "src/lib.rs": b"pub fn verified() {}\n"}

    def fetch(_source, revision, path):
        assert revision == SHA
        content = contents[path]
        return {"content": content, "git_blob_sha": _blob_sha(content)}

    execution = execute_authorized_acquisition(
        repository,
        authorization["id"],
        storage_root=tmp_path,
        fetch_file=fetch,
        actor=TOOL,
        execution_id="ax:verified-commit",
    )
    return repository, selection, authorization, execution, contents


def test_verify_store_rehashes_every_file_and_preserves_no_mutation(tmp_path: Path):
    repository, _selection, authorization, execution, contents = _successful_execution(tmp_path)
    before_source = deepcopy(repository.get(SOURCE_ID))
    result = verify_execution_store(repository, execution["id"], storage_root=tmp_path)

    assert result["manifest_sha256"] == execution["manifest_sha256"]
    assert result["authorization"] == authorization
    assert [item["path"] for item in result["verified_file_results"]] == [
        "README.md",
        "src/lib.rs",
    ]
    assert (result["storage_directory"] / "README.md").read_bytes() == contents["README.md"]
    assert repository.get(SOURCE_ID) == before_source
    assert repository.list("source_snapshot") == []


def test_tampered_file_is_rejected(tmp_path: Path):
    repository, _selection, _authorization, execution, _contents = _successful_execution(tmp_path)
    directory = tmp_path / execution["storage_key"]
    (directory / "README.md").write_bytes(b"tampered after successful execution")

    with pytest.raises(VerifiedAcquisitionCommitError, match="content mismatch"):
        verify_execution_store(repository, execution["id"], storage_root=tmp_path)


def test_missing_and_extra_files_are_rejected(tmp_path: Path):
    repository, _selection, _authorization, execution, _contents = _successful_execution(tmp_path)
    directory = tmp_path / execution["storage_key"]
    (directory / "README.md").unlink()
    with pytest.raises(VerifiedAcquisitionCommitError, match="file set differs"):
        verify_execution_store(repository, execution["id"], storage_root=tmp_path)

    # Recreate from a fresh execution fixture for the extra-file case.
    other_root = tmp_path / "other"
    other_root.mkdir()
    repository, _selection, _authorization, execution, _contents = _successful_execution(other_root)
    directory = other_root / execution["storage_key"]
    (directory / "EXTRA.txt").write_text("not authorized", encoding="utf-8")
    with pytest.raises(VerifiedAcquisitionCommitError, match="file set differs"):
        verify_execution_store(repository, execution["id"], storage_root=other_root)


def test_unexpected_empty_directory_is_rejected(tmp_path: Path):
    repository, _selection, _authorization, execution, _contents = _successful_execution(tmp_path)
    directory = tmp_path / execution["storage_key"]
    (directory / "not-authorized").mkdir()
    with pytest.raises(VerifiedAcquisitionCommitError, match="unexpected directories"):
        verify_execution_store(repository, execution["id"], storage_root=tmp_path)


@pytest.mark.skipif(os.name == "nt", reason="symlink creation may require elevated Windows privilege")
def test_symlink_is_rejected(tmp_path: Path):
    repository, _selection, _authorization, execution, _contents = _successful_execution(tmp_path)
    directory = tmp_path / execution["storage_key"]
    (directory / "README.md").unlink()
    (directory / "README.md").symlink_to(directory / "src" / "lib.rs")
    with pytest.raises(VerifiedAcquisitionCommitError, match="symlink"):
        verify_execution_store(repository, execution["id"], storage_root=tmp_path)


def test_source_change_after_success_is_detected_by_execution_fingerprint(tmp_path: Path):
    repository, _selection, _authorization, execution, _contents = _successful_execution(tmp_path)
    changed = deepcopy(repository.get(SOURCE_ID))
    changed["origin"]["description"] = "changed after fetch"
    repository.put(changed, replace=True)

    with pytest.raises(VerifiedAcquisitionCommitError, match="Source fingerprint differs"):
        verify_execution_store(repository, execution["id"], storage_root=tmp_path)


def test_authorization_change_after_success_is_detected_by_execution_fingerprint(tmp_path: Path):
    repository, _selection, authorization, execution, _contents = _successful_execution(tmp_path)
    changed = deepcopy(repository.get(authorization["id"]))
    changed["rationale"] = "changed after fetch"
    repository.put(changed, replace=True)

    with pytest.raises(VerifiedAcquisitionCommitError, match="Authorization fingerprint differs"):
        verify_execution_store(repository, execution["id"], storage_root=tmp_path)


def test_legacy_success_without_provenance_fingerprints_cannot_be_committed(tmp_path: Path):
    repository, _selection, _authorization, execution, _contents = _successful_execution(tmp_path)
    legacy = deepcopy(execution)
    legacy["id"] = "ax:legacy-without-fingerprints"
    legacy.pop("source_fingerprint_sha256", None)
    legacy.pop("authorization_fingerprint_sha256", None)
    repository.put(legacy)

    with pytest.raises(VerifiedAcquisitionCommitError, match="predates required"):
        verify_execution_store(repository, legacy["id"], storage_root=tmp_path)