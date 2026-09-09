from __future__ import annotations

from hashlib import sha1
import os
from pathlib import Path

import psycopg
import pytest

from kneekura_tech_hub.authorization import AcquisitionAuthorizationEngine, authorization_effectiveness
from kneekura_tech_hub.database import apply_migrations
from kneekura_tech_hub.execution import execute_authorized_acquisition, record_fingerprint_sha256
from kneekura_tech_hub.selection import SourceSelectionEngine
from kneekura_tech_hub.verified_commit import (
    VerifiedAcquisitionCommitError,
    commit_verified_acquisition,
)
from kneekura_tech_hub.verified_commit_postgres import VerifiedCommitPostgresRepository


DSN = os.getenv("KTHUB_TEST_DATABASE_URL")
pytestmark = pytest.mark.skipif(not DSN, reason="KTHUB_TEST_DATABASE_URL is not set")
SHA = "0123456789abcdef0123456789abcdef01234567"
SOURCE_ID = "src:github:example:verified-commit-postgres"
HUMAN = {"actor_type": "human", "actor_id": "postgres-reviewer"}
TOOL = {"actor_type": "tool", "actor_id": "postgres-verifier", "version": "v1"}


def _blob_sha(content: bytes) -> str:
    header = f"blob {len(content)}\0".encode("ascii")
    return sha1(header + content).hexdigest()  # noqa: S324 - Git identity


def _truncate(connection) -> None:
    connection.execute(
        """
        TRUNCATE TABLE
            source_acquisition_commit,
            source_acquisition_execution,
            source_acquisition_authorization,
            source_selection_decision,
            review_decision,
            staged_observation_evidence,
            claim_evidence, claim, evidence_relation, evidence,
            source_snapshot, staged_observation, curation_event,
            entity_relation, entity_kind, entity_alias, knowledge_entity, source
        RESTART IDENTITY CASCADE
        """
    )


def _setup(repository: VerifiedCommitPostgresRepository, storage_root: Path):
    source = {
        "record_type": "source",
        "id": SOURCE_ID,
        "kind": "repository",
        "origin": {
            "provider": "github",
            "repository": "example/verified-commit-postgres",
            "url": "https://github.com/example/verified-commit-postgres",
        },
        "acquisition": {"level": "metadata-only"},
        "license": {
            "state": "KNOWN",
            "declared_expression": "MIT",
            "handling_policy": "REFERENCE_ONLY",
        },
    }
    repository.put(source)
    selection = SourceSelectionEngine(repository).create_from_fields(
        source_id=SOURCE_ID,
        decision="SELECT_FOR_REVIEW",
        rationale="Select exact Source for commit test.",
        actor=HUMAN,
        decision_id="sd:verified-commit-postgres",
    )
    authorization = AcquisitionAuthorizationEngine(repository).authorize_from_fields(
        source_id=SOURCE_ID,
        selection_decision_id=selection["id"],
        revision=SHA,
        allowed_paths=["README.md", "src/lib.rs"],
        rationale="Authorize exact files for commit test.",
        actor=HUMAN,
        authorization_id="aa:verified-commit-postgres",
    )
    contents = {"README.md": b"postgres commit\n", "src/lib.rs": b"pub fn commit() {}\n"}

    def fetch(_source, revision, path):
        assert revision == SHA
        content = contents[path]
        return {"content": content, "git_blob_sha": _blob_sha(content)}

    execution = execute_authorized_acquisition(
        repository,
        authorization["id"],
        storage_root=storage_root,
        fetch_file=fetch,
        actor={"actor_type": "tool", "actor_id": "postgres-fetcher", "version": "v1"},
        execution_id="ax:verified-commit-postgres",
    )
    return source, selection, authorization, execution, contents


def test_verified_commit_atomically_creates_snapshot_and_promotes_source(tmp_path: Path):
    assert DSN is not None
    connection = psycopg.connect(DSN, autocommit=True)
    try:
        apply_migrations(connection)
        _truncate(connection)
        repository = VerifiedCommitPostgresRepository(connection)
        source, _selection, authorization, execution, contents = _setup(repository, tmp_path)

        assert execution["source_fingerprint_sha256"] == record_fingerprint_sha256(source)
        assert execution["authorization_fingerprint_sha256"] == record_fingerprint_sha256(authorization)

        commit = commit_verified_acquisition(
            repository,
            execution["id"],
            storage_root=tmp_path,
            actor=TOOL,
            commit_id="vc:verified-commit-postgres",
        )

        assert repository.get(commit["id"]) == commit
        stored_source = repository.get(SOURCE_ID)
        assert stored_source is not None
        assert stored_source["acquisition"] == {"level": "selected-files"}
        assert stored_source["origin"] == source["origin"]
        assert stored_source["license"] == source["license"]

        snapshot = repository.get(commit["snapshot_id"])
        assert snapshot is not None
        assert snapshot["source_id"] == SOURCE_ID
        assert snapshot["revision"] == SHA
        assert snapshot["content_hash"] == execution["manifest_sha256"]
        assert snapshot["metadata"]["content_hash_kind"] == "selected-files-manifest-sha256"
        assert snapshot["metadata"]["execution_id"] == execution["id"]
        assert snapshot["metadata"]["authorization_id"] == authorization["id"]
        assert snapshot["metadata"]["storage_key"] == execution["storage_key"]
        assert [item["path"] for item in snapshot["metadata"]["selected_files"]] == [
            "README.md",
            "src/lib.rs",
        ]
        assert (tmp_path / execution["storage_key"] / "README.md").read_bytes() == contents[
            "README.md"
        ]

        assert repository.list("evidence") == []
        events = repository.list("curation_event")
        assert len(events) == 1
        assert events[0]["operation"] == "SOURCE_ACQUIRE"
        assert events[0]["subject_ids"] == [
            SOURCE_ID,
            commit["snapshot_id"],
            execution["id"],
            commit["id"],
        ]

        # Canonicalization consumes the metadata-only prerequisite, making the old authority
        # historical rather than still executable.
        effectiveness = authorization_effectiveness(repository, authorization["id"])
        assert effectiveness["effective"] is False
        assert "SOURCE_NO_LONGER_METADATA_ONLY" in effectiveness["blockers"]
    finally:
        connection.close()


def test_duplicate_execution_commit_is_rejected_without_second_snapshot(tmp_path: Path):
    assert DSN is not None
    connection = psycopg.connect(DSN, autocommit=True)
    try:
        apply_migrations(connection)
        _truncate(connection)
        repository = VerifiedCommitPostgresRepository(connection)
        _source, _selection, _authorization, execution, _contents = _setup(repository, tmp_path)
        first = commit_verified_acquisition(
            repository,
            execution["id"],
            storage_root=tmp_path,
            actor=TOOL,
        )
        with pytest.raises(VerifiedAcquisitionCommitError):
            commit_verified_acquisition(
                repository,
                execution["id"],
                storage_root=tmp_path,
                actor=TOOL,
            )
        assert len(repository.list("source_acquisition_commit")) == 1
        assert len(repository.list("source_snapshot")) == 1
        assert repository.list("source_acquisition_commit")[0] == first
    finally:
        connection.close()


def test_conflicting_snapshot_causes_transaction_rollback(tmp_path: Path):
    assert DSN is not None
    connection = psycopg.connect(DSN, autocommit=True)
    try:
        apply_migrations(connection)
        _truncate(connection)
        repository = VerifiedCommitPostgresRepository(connection)
        source, _selection, _authorization, execution, _contents = _setup(repository, tmp_path)

        # Determine the deterministic snapshot ID by running verification logic through a first
        # failed canonicalization attempt in a transaction with a deliberately preoccupied ID.
        from kneekura_tech_hub.verified_commit import _snapshot_id  # focused invariant test

        snapshot_id = _snapshot_id(SOURCE_ID, SHA, execution["manifest_sha256"])
        repository.put(
            {
                "record_type": "source_snapshot",
                "id": snapshot_id,
                "source_id": SOURCE_ID,
                "revision": "f" * 40,
                "captured_at": "2026-09-09T00:00:00Z",
                "metadata": {"fixture": "preexisting conflict"},
            }
        )

        with pytest.raises(VerifiedAcquisitionCommitError, match="snapshot already exists"):
            commit_verified_acquisition(
                repository,
                execution["id"],
                storage_root=tmp_path,
                actor=TOOL,
            )

        assert repository.get(SOURCE_ID) == source
        assert repository.list("source_acquisition_commit") == []
        assert repository.list("curation_event") == []
        assert len(repository.list("source_snapshot")) == 1
    finally:
        connection.close()
