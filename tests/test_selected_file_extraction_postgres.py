from __future__ import annotations

from hashlib import sha1
import os
from pathlib import Path

import psycopg
import pytest

from kneekura_tech_hub.authorization import AcquisitionAuthorizationEngine
from kneekura_tech_hub.database import apply_migrations
from kneekura_tech_hub.execution import execute_authorized_acquisition
from kneekura_tech_hub.selected_file_extraction import (
    check_selected_file_extraction,
    ingest_selected_file_extraction,
)
from kneekura_tech_hub.selection import SourceSelectionEngine
from kneekura_tech_hub.service import CurationEngine
from kneekura_tech_hub.verified_commit import commit_verified_acquisition
from kneekura_tech_hub.verified_commit_postgres import VerifiedCommitPostgresRepository


DSN = os.getenv("KTHUB_TEST_DATABASE_URL")
pytestmark = pytest.mark.skipif(not DSN, reason="KTHUB_TEST_DATABASE_URL is not set")
SHA = "0123456789abcdef0123456789abcdef01234567"
SOURCE_ID = "src:github:example:selected-file-extraction-postgres"
HUMAN = {"actor_type": "human", "actor_id": "postgres-reviewer"}
FETCHER = {"actor_type": "tool", "actor_id": "postgres-fetcher", "version": "v1"}
COMMITTER = {"actor_type": "tool", "actor_id": "postgres-committer", "version": "v1"}
AI = {"actor_type": "ai", "actor_id": "postgres-extractor", "version": "v1"}


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
            "repository": "example/selected-file-extraction-postgres",
            "url": "https://github.com/example/selected-file-extraction-postgres",
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
        rationale="Select exact Source for extraction test.",
        actor=HUMAN,
        decision_id="sd:selected-file-extraction-postgres",
    )
    authorization = AcquisitionAuthorizationEngine(repository).authorize_from_fields(
        source_id=SOURCE_ID,
        selection_decision_id=selection["id"],
        revision=SHA,
        allowed_paths=["README.md", "src/lib.rs"],
        rationale="Authorize exact files for extraction test.",
        actor=HUMAN,
        authorization_id="aa:selected-file-extraction-postgres",
    )
    contents = {
        "README.md": b"# Cache\nIncremental recomputation avoids unchanged work.\nInvalidation is explicit.\n",
        "src/lib.rs": b"pub fn refresh() {\n    // recompute only changed inputs\n}\n",
    }

    def fetch(_source, revision, path):
        assert revision == SHA
        content = contents[path]
        return {"content": content, "git_blob_sha": _blob_sha(content)}

    execution = execute_authorized_acquisition(
        repository,
        authorization["id"],
        storage_root=storage_root,
        fetch_file=fetch,
        actor=FETCHER,
        execution_id="ax:selected-file-extraction-postgres",
    )
    commit = commit_verified_acquisition(
        repository,
        execution["id"],
        storage_root=storage_root,
        actor=COMMITTER,
        commit_id="vc:selected-file-extraction-postgres",
    )
    return commit


def _proposal(snapshot_id: str) -> dict:
    return {
        "proposal_version": "1.0",
        "snapshot_id": snapshot_id,
        "findings": [
            {
                "summary": "The README states that incremental recomputation avoids unchanged work.",
                "candidate_names": ["incremental recomputation"],
                "anchors": [{"path": "README.md", "line_start": 2, "line_end": 2}],
            },
            {
                "summary": "The README and implementation both describe changed-input-only recomputation.",
                "candidate_names": ["changed-input recomputation"],
                "anchors": [
                    {"path": "README.md", "line_start": 2, "line_end": 3},
                    {"path": "src/lib.rs", "line_start": 1, "line_end": 3},
                ],
            },
        ],
    }


def test_postgres_extraction_roundtrip_is_idempotent_and_stops_before_claims(tmp_path: Path):
    assert DSN is not None
    connection = psycopg.connect(DSN, autocommit=True)
    try:
        apply_migrations(connection)
        _truncate(connection)
        repository = VerifiedCommitPostgresRepository(connection)
        commit = _setup(repository, tmp_path)
        engine = CurationEngine(repository)
        proposal = _proposal(commit["snapshot_id"])

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

        for evidence_id in first["evidence_ids"]:
            evidence = repository.get(evidence_id)
            assert evidence is not None
            assert evidence["source_snapshot_id"] == commit["snapshot_id"]
            assert evidence["locator"]["snapshot_manifest_sha256"] == commit["manifest_sha256"]
            assert evidence["locator"]["content_hash"].startswith("sha256:")

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
        assert len(repository.list("evidence")) == 3
        assert len(repository.list("staged_observation")) == 2
    finally:
        connection.close()


def test_reextraction_preserves_existing_observation_lifecycle_status(tmp_path: Path):
    assert DSN is not None
    connection = psycopg.connect(DSN, autocommit=True)
    try:
        apply_migrations(connection)
        _truncate(connection)
        repository = VerifiedCommitPostgresRepository(connection)
        commit = _setup(repository, tmp_path)
        engine = CurationEngine(repository)
        proposal = _proposal(commit["snapshot_id"])

        first = ingest_selected_file_extraction(
            engine,
            proposal,
            storage_root=tmp_path,
            actor=AI,
        )
        observation_id = first["observation_ids"][0]
        observation = repository.get(observation_id)
        assert observation is not None
        observation["status"] = "TRIAGED"
        repository.put(observation, replace=True)

        checked = check_selected_file_extraction(
            repository,
            proposal,
            storage_root=tmp_path,
            actor=AI,
        )
        assert observation_id in checked["reused_observation_ids"]
        assert repository.get(observation_id)["status"] == "TRIAGED"

        second = ingest_selected_file_extraction(
            engine,
            proposal,
            storage_root=tmp_path,
            actor=AI,
        )
        assert second["new_observation_count"] == 0
        assert second["reused_observation_count"] == 2
        assert repository.get(observation_id)["status"] == "TRIAGED"
    finally:
        connection.close()


def test_postgres_extraction_rolls_back_entire_batch_on_midwrite_failure(tmp_path: Path):
    assert DSN is not None
    connection = psycopg.connect(DSN, autocommit=True)
    try:
        apply_migrations(connection)
        _truncate(connection)
        repository = VerifiedCommitPostgresRepository(connection)
        commit = _setup(repository, tmp_path)

        class FailingEngine(CurationEngine):
            def __init__(self, repo):
                super().__init__(repo)
                self.observation_calls = 0

            def stage_observation(self, observation, *, actor):
                self.observation_calls += 1
                if self.observation_calls == 2:
                    raise RuntimeError("simulated staging failure")
                return super().stage_observation(observation, actor=actor)

        events_before = list(repository.list("curation_event"))
        with pytest.raises(RuntimeError, match="simulated staging failure"):
            ingest_selected_file_extraction(
                FailingEngine(repository),
                _proposal(commit["snapshot_id"]),
                storage_root=tmp_path,
                actor=AI,
            )

        assert repository.list("evidence") == []
        assert repository.list("staged_observation") == []
        assert repository.list("curation_event") == events_before
        assert repository.list("claim") == []
        assert repository.list("knowledge_entity") == []
    finally:
        connection.close()
