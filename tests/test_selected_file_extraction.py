from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timezone
from hashlib import sha1, sha256
from pathlib import Path

import pytest

from kneekura_tech_hub.authorization import AcquisitionAuthorizationEngine
from kneekura_tech_hub.execution import execute_authorized_acquisition
from kneekura_tech_hub.repository import MemoryRepository
from kneekura_tech_hub.selected_file_extraction import (
    SelectedFileExtractionError,
    ingest_selected_file_extraction,
    prepare_selected_file_extraction,
    verify_committed_selected_file_snapshot,
)
from kneekura_tech_hub.selection import SourceSelectionEngine
from kneekura_tech_hub.service import CurationEngine
from kneekura_tech_hub.validator import validate_record
from kneekura_tech_hub.verified_commit import _snapshot_id


SHA = "0123456789abcdef0123456789abcdef01234567"
SOURCE_ID = "src:github:example:extract"
SELECTION_ID = "sd:extract"
AUTHORIZATION_ID = "aa:extract"
HUMAN = {"actor_type": "human", "actor_id": "reviewer"}
TOOL = {"actor_type": "tool", "actor_id": "fetcher", "version": "v1"}
AI = {"actor_type": "ai", "actor_id": "extractor", "version": "v1"}


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
            "repository": "example/extract",
            "url": "https://github.com/example/extract",
        },
        "acquisition": {"level": "metadata-only"},
        "license": {
            "state": "KNOWN",
            "declared_expression": "MIT",
            "handling_policy": "REFERENCE_ONLY",
        },
    }


def _fixture(tmp_path: Path, contents: dict[str, bytes] | None = None):
    contents = contents or {
        "README.md": b"# Example\nUses an incremental cache.\nInvalidation is explicit.\n",
        "src/lib.rs": b"pub fn update() {\n    // recompute changed inputs only\n}\n",
    }
    repository = MemoryRepository()
    repository.put(_source())
    selection = SourceSelectionEngine(repository).create_from_fields(
        source_id=SOURCE_ID,
        decision="SELECT_FOR_REVIEW",
        rationale="Review exact selected files.",
        actor=HUMAN,
        decision_id=SELECTION_ID,
    )
    authorization = AcquisitionAuthorizationEngine(repository).authorize_from_fields(
        source_id=SOURCE_ID,
        selection_decision_id=selection["id"],
        revision=SHA,
        allowed_paths=list(contents),
        rationale="Acquire only exact selected files.",
        actor=HUMAN,
        authorization_id=AUTHORIZATION_ID,
    )

    def fetch(_source_record: dict, revision: str, path: str) -> dict:
        assert revision == SHA
        content = contents[path]
        return {"content": content, "git_blob_sha": _blob_sha(content)}

    execution = execute_authorized_acquisition(
        repository,
        authorization["id"],
        storage_root=tmp_path,
        fetch_file=fetch,
        actor=TOOL,
        execution_id="ax:extract",
    )
    assert execution["status"] == "SUCCEEDED"

    source_after = deepcopy(repository.get(SOURCE_ID))
    source_after["acquisition"] = {"level": "selected-files"}
    repository.put(source_after, replace=True)

    snapshot_id = _snapshot_id(SOURCE_ID, SHA, execution["manifest_sha256"])
    captured_at = datetime.now(timezone.utc).isoformat()
    snapshot = {
        "record_type": "source_snapshot",
        "id": snapshot_id,
        "source_id": SOURCE_ID,
        "revision": SHA,
        "content_hash": execution["manifest_sha256"],
        "captured_at": captured_at,
        "metadata": {
            "acquisition_level": "selected-files",
            "content_hash_kind": "selected-files-manifest-sha256",
            "execution_id": execution["id"],
            "authorization_id": authorization["id"],
            "manifest_sha256": execution["manifest_sha256"],
            "storage_key": execution["storage_key"],
            "selected_files": deepcopy(execution["file_results"]),
            "source_fingerprint_sha256": execution["source_fingerprint_sha256"],
            "authorization_fingerprint_sha256": execution[
                "authorization_fingerprint_sha256"
            ],
        },
    }
    validate_record(snapshot)
    repository.put(snapshot)

    commit = {
        "record_type": "source_acquisition_commit",
        "id": "vc:" + sha256(snapshot_id.encode("utf-8")).hexdigest(),
        "execution_id": execution["id"],
        "authorization_id": authorization["id"],
        "source_id": SOURCE_ID,
        "snapshot_id": snapshot_id,
        "revision": SHA,
        "acquisition_level": "selected-files",
        "manifest_sha256": execution["manifest_sha256"],
        "source_fingerprint_sha256": execution["source_fingerprint_sha256"],
        "authorization_fingerprint_sha256": execution[
            "authorization_fingerprint_sha256"
        ],
        "committed_by": TOOL,
        "policy_version": "1.0.0",
        "committed_at": captured_at,
    }
    validate_record(commit)
    repository.put(commit)
    return repository, snapshot, execution, authorization, contents


def _proposal(snapshot_id: str) -> dict:
    return {
        "proposal_version": "1.0",
        "snapshot_id": snapshot_id,
        "findings": [
            {
                "summary": "The selected README describes an incremental cache with explicit invalidation.",
                "candidate_names": ["incremental cache", "explicit invalidation"],
                "anchors": [
                    {"path": "README.md", "line_start": 2, "line_end": 3},
                ],
            },
            {
                "summary": "The implementation comment says recomputation is limited to changed inputs.",
                "candidate_names": ["changed-input recomputation"],
                "anchors": [
                    {"path": "src/lib.rs", "line_start": 1, "line_end": 3},
                    {"path": "README.md", "line_start": 2, "line_end": 2},
                ],
            },
        ],
    }


def test_prepare_reverifies_snapshot_and_generates_only_evidence_and_observations(tmp_path: Path):
    repository, snapshot, _execution, _authorization, _contents = _fixture(tmp_path)
    prepared = prepare_selected_file_extraction(
        repository,
        _proposal(snapshot["id"]),
        storage_root=tmp_path,
        actor=AI,
    )

    assert prepared["snapshot_id"] == snapshot["id"]
    assert len(prepared["evidence"]) == 3
    assert len(prepared["observations"]) == 2
    assert repository.list("evidence") == []
    assert repository.list("staged_observation") == []
    assert repository.list("claim") == []
    assert repository.list("knowledge_entity") == []

    first = next(item for item in prepared["evidence"] if item["locator"]["path"] == "README.md" and item["locator"]["line_start"] == 2 and item["locator"]["line_end"] == 3)
    expected_excerpt = b"Uses an incremental cache.\nInvalidation is explicit.\n"
    assert first["locator"]["content_hash"] == "sha256:" + sha256(expected_excerpt).hexdigest()
    assert first["source_snapshot_id"] == snapshot["id"]
    assert first["roles"] == ["SUPPORTS"]
    assert all(item["status"] == "NEW" for item in prepared["observations"])
    assert all(item["created_by"] == AI for item in prepared["observations"])


def test_ingest_is_idempotent_and_does_not_create_claims_or_entities(tmp_path: Path):
    repository, snapshot, _execution, _authorization, _contents = _fixture(tmp_path)
    engine = CurationEngine(repository)
    proposal = _proposal(snapshot["id"])

    first = ingest_selected_file_extraction(
        engine,
        proposal,
        storage_root=tmp_path,
        actor=AI,
    )
    assert first["new_evidence_count"] == 3
    assert first["new_observation_count"] == 2
    assert len(repository.list("evidence")) == 3
    assert len(repository.list("staged_observation")) == 2
    assert repository.list("claim") == []
    assert repository.list("knowledge_entity") == []

    event_count = len(repository.list("curation_event"))
    second = ingest_selected_file_extraction(
        engine,
        proposal,
        storage_root=tmp_path,
        actor=AI,
    )
    assert second["new_evidence_count"] == 0
    assert second["reused_evidence_count"] == 3
    assert second["new_observation_count"] == 0
    assert second["reused_observation_count"] == 2
    assert len(repository.list("curation_event")) == event_count


def test_tampered_committed_store_is_rejected_before_proposal_is_trusted(tmp_path: Path):
    repository, snapshot, execution, _authorization, _contents = _fixture(tmp_path)
    file_path = tmp_path / execution["storage_key"] / "README.md"
    file_path.write_bytes(b"tampered\n")

    with pytest.raises(SelectedFileExtractionError, match="bytes differ"):
        prepare_selected_file_extraction(
            repository,
            _proposal(snapshot["id"]),
            storage_root=tmp_path,
            actor=AI,
        )
    assert repository.list("evidence") == []
    assert repository.list("staged_observation") == []


def test_snapshot_without_verified_commit_is_rejected(tmp_path: Path):
    repository, snapshot, _execution, _authorization, _contents = _fixture(tmp_path)
    for commit in repository.list("source_acquisition_commit"):
        repository._records.pop(commit["id"])  # test-only corruption fixture

    with pytest.raises(SelectedFileExtractionError, match="exactly one verified acquisition commit"):
        verify_committed_selected_file_snapshot(
            repository,
            snapshot["id"],
            storage_root=tmp_path,
        )


def test_current_source_metadata_may_evolve_without_invalidating_historical_snapshot(tmp_path: Path):
    repository, snapshot, _execution, _authorization, _contents = _fixture(tmp_path)
    changed = repository.get(SOURCE_ID)
    changed["origin"]["description"] = "current metadata changed after the historical commit"
    repository.put(changed, replace=True)

    verified = verify_committed_selected_file_snapshot(
        repository,
        snapshot["id"],
        storage_root=tmp_path,
    )
    assert verified["snapshot"]["id"] == snapshot["id"]


def test_historical_authorization_mutation_is_detected_by_fingerprint(tmp_path: Path):
    repository, snapshot, _execution, authorization, _contents = _fixture(tmp_path)
    changed = deepcopy(authorization)
    changed["rationale"] = "corrupted after execution"
    repository.put(changed, replace=True)

    with pytest.raises(SelectedFileExtractionError, match="Authorization record changed"):
        verify_committed_selected_file_snapshot(
            repository,
            snapshot["id"],
            storage_root=tmp_path,
        )


def test_uncommitted_path_out_of_range_and_binary_anchor_fail_closed(tmp_path: Path):
    repository, snapshot, _execution, _authorization, _contents = _fixture(tmp_path)

    outside = _proposal(snapshot["id"])
    outside["findings"] = [{
        "summary": "Invented path.",
        "anchors": [{"path": "not-acquired.md", "line_start": 1, "line_end": 1}],
    }]
    with pytest.raises(SelectedFileExtractionError, match="not in committed Snapshot"):
        prepare_selected_file_extraction(repository, outside, storage_root=tmp_path, actor=AI)

    out_of_range = _proposal(snapshot["id"])
    out_of_range["findings"] = [{
        "summary": "Invented line.",
        "anchors": [{"path": "README.md", "line_start": 99, "line_end": 99}],
    }]
    with pytest.raises(SelectedFileExtractionError, match="outside committed file line range"):
        prepare_selected_file_extraction(repository, out_of_range, storage_root=tmp_path, actor=AI)

    binary_root = tmp_path / "binary"
    binary_root.mkdir()
    binary_repository, binary_snapshot, _e, _a, _c = _fixture(
        binary_root,
        {"data.bin": b"\xff\xfe\x00\x01"},
    )
    binary = {
        "proposal_version": "1.0",
        "snapshot_id": binary_snapshot["id"],
        "findings": [{
            "summary": "Binary bytes cannot be line-anchored as UTF-8 source evidence.",
            "anchors": [{"path": "data.bin", "line_start": 1, "line_end": 1}],
        }],
    }
    with pytest.raises(SelectedFileExtractionError, match="not UTF-8"):
        prepare_selected_file_extraction(binary_repository, binary, storage_root=binary_root, actor=AI)


def test_deterministic_id_conflict_is_rejected_before_new_records_are_written(tmp_path: Path):
    repository, snapshot, _execution, _authorization, _contents = _fixture(tmp_path)
    proposal = _proposal(snapshot["id"])
    prepared = prepare_selected_file_extraction(
        repository,
        proposal,
        storage_root=tmp_path,
        actor=AI,
    )
    conflicting = deepcopy(prepared["evidence"][0])
    conflicting["roles"] = ["QUALIFIES"]
    repository.put(conflicting)

    before_observations = repository.list("staged_observation")
    with pytest.raises(SelectedFileExtractionError, match="conflicts with deterministic Evidence"):
        ingest_selected_file_extraction(
            CurationEngine(repository),
            proposal,
            storage_root=tmp_path,
            actor=AI,
        )
    assert repository.list("staged_observation") == before_observations