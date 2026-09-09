from __future__ import annotations

from hashlib import sha1
import json
import os
from pathlib import Path
import sys

import psycopg
import pytest

import kneekura_tech_hub.selected_file_extraction_cli as extraction_cli
from kneekura_tech_hub.authorization import AcquisitionAuthorizationEngine
from kneekura_tech_hub.database import apply_migrations
from kneekura_tech_hub.execution import execute_authorized_acquisition
from kneekura_tech_hub.selection import SourceSelectionEngine
from kneekura_tech_hub.verified_commit import commit_verified_acquisition
from kneekura_tech_hub.verified_commit_postgres import VerifiedCommitPostgresRepository


DSN = os.getenv("KTHUB_TEST_DATABASE_URL")
SHA = "0123456789abcdef0123456789abcdef01234567"
SOURCE_ID = "src:github:example:selected-file-extraction-cli"
HUMAN = {"actor_type": "human", "actor_id": "cli-reviewer"}


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


def _setup(storage_root: Path) -> str:
    assert DSN is not None
    connection = psycopg.connect(DSN, autocommit=True)
    try:
        apply_migrations(connection)
        _truncate(connection)
        repository = VerifiedCommitPostgresRepository(connection)
        repository.put(
            {
                "record_type": "source",
                "id": SOURCE_ID,
                "kind": "repository",
                "origin": {
                    "provider": "github",
                    "repository": "example/selected-file-extraction-cli",
                    "url": "https://github.com/example/selected-file-extraction-cli",
                },
                "acquisition": {"level": "metadata-only"},
                "license": {
                    "state": "KNOWN",
                    "declared_expression": "MIT",
                    "handling_policy": "REFERENCE_ONLY",
                },
            }
        )
        selection = SourceSelectionEngine(repository).create_from_fields(
            source_id=SOURCE_ID,
            decision="SELECT_FOR_REVIEW",
            rationale="CLI extraction fixture selected.",
            actor=HUMAN,
            decision_id="sd:selected-file-extraction-cli",
        )
        authorization = AcquisitionAuthorizationEngine(repository).authorize_from_fields(
            source_id=SOURCE_ID,
            selection_decision_id=selection["id"],
            revision=SHA,
            allowed_paths=["README.md"],
            rationale="CLI extraction fixture authorizes README only.",
            actor=HUMAN,
            authorization_id="aa:selected-file-extraction-cli",
        )
        content = b"# Example\nIncremental cache avoids repeated work.\n"
        execution = execute_authorized_acquisition(
            repository,
            authorization["id"],
            storage_root=storage_root,
            fetch_file=lambda *_args: {"content": content, "git_blob_sha": _blob_sha(content)},
            actor={"actor_type": "tool", "actor_id": "cli-fetcher", "version": "v1"},
            execution_id="ax:selected-file-extraction-cli",
        )
        commit = commit_verified_acquisition(
            repository,
            execution["id"],
            storage_root=storage_root,
            actor={"actor_type": "tool", "actor_id": "cli-committer", "version": "v1"},
            commit_id="vc:selected-file-extraction-cli",
        )
        return commit["snapshot_id"]
    finally:
        connection.close()


def test_cli_requires_database_url(monkeypatch, tmp_path: Path, capsys):
    proposal_path = tmp_path / "proposal.json"
    proposal_path.write_text("{}", encoding="utf-8")
    monkeypatch.delenv("KTHUB_DATABASE_URL", raising=False)
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "kneekura-selected-file-extract",
            "check",
            str(proposal_path),
            "--storage-root",
            str(tmp_path),
            "--actor-type",
            "ai",
            "--actor-id",
            "test",
        ],
    )
    assert extraction_cli.main() == 1
    assert "KTHUB_DATABASE_URL is required" in capsys.readouterr().out


@pytest.mark.skipif(not DSN, reason="KTHUB_TEST_DATABASE_URL is not set")
def test_cli_check_is_read_only_then_ingest_stages_only_evidence(monkeypatch, tmp_path: Path, capsys):
    snapshot_id = _setup(tmp_path)
    assert DSN is not None
    monkeypatch.setenv("KTHUB_DATABASE_URL", DSN)
    proposal = {
        "proposal_version": "1.0",
        "snapshot_id": snapshot_id,
        "findings": [
            {
                "summary": "The README says an incremental cache avoids repeated work.",
                "candidate_names": ["incremental cache"],
                "anchors": [{"path": "README.md", "line_start": 2, "line_end": 2}],
            }
        ],
    }
    proposal_path = tmp_path / "proposal.json"
    proposal_path.write_text(json.dumps(proposal), encoding="utf-8")

    monkeypatch.setattr(
        sys,
        "argv",
        [
            "kneekura-selected-file-extract",
            "check",
            str(proposal_path),
            "--storage-root",
            str(tmp_path),
            "--actor-type",
            "ai",
            "--actor-id",
            "cli-extractor",
            "--actor-version",
            "test-v1",
        ],
    )
    assert extraction_cli.main() == 0
    output = capsys.readouterr().out
    assert '"record_type": "evidence"' in output
    assert '"record_type": "staged_observation"' in output

    connection = psycopg.connect(DSN, autocommit=True)
    try:
        repository = VerifiedCommitPostgresRepository(connection)
        assert repository.list("evidence") == []
        assert repository.list("staged_observation") == []
    finally:
        connection.close()

    monkeypatch.setattr(
        sys,
        "argv",
        [
            "kneekura-selected-file-extract",
            "ingest",
            str(proposal_path),
            "--storage-root",
            str(tmp_path),
            "--actor-type",
            "ai",
            "--actor-id",
            "cli-extractor",
            "--actor-version",
            "test-v1",
        ],
    )
    assert extraction_cli.main() == 0
    output = capsys.readouterr().out
    assert '"new_evidence_count": 1' in output
    assert '"new_observation_count": 1' in output

    connection = psycopg.connect(DSN, autocommit=True)
    try:
        repository = VerifiedCommitPostgresRepository(connection)
        evidence = repository.list("evidence")
        observations = repository.list("staged_observation")
        assert len(evidence) == 1
        assert len(observations) == 1
        assert observations[0]["created_by"] == {
            "actor_type": "ai",
            "actor_id": "cli-extractor",
            "version": "test-v1",
        }
        assert repository.list("claim") == []
        assert repository.list("knowledge_entity") == []
    finally:
        connection.close()
