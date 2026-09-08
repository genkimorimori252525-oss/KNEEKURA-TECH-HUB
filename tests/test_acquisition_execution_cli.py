from __future__ import annotations

from hashlib import sha1
import os
from pathlib import Path
import sys

import psycopg
import pytest

import kneekura_tech_hub.execution_cli as execution_cli
from kneekura_tech_hub.authorization import AcquisitionAuthorizationEngine
from kneekura_tech_hub.database import apply_migrations
from kneekura_tech_hub.execution_postgres import ExecutionPostgresRepository
from kneekura_tech_hub.selection import SourceSelectionEngine


DSN = os.getenv("KTHUB_TEST_DATABASE_URL")
SHA = "0123456789abcdef0123456789abcdef01234567"
SOURCE_ID = "src:github:example:execution-cli"
HUMAN = {"actor_type": "human", "actor_id": "cli-reviewer"}


def _blob_sha(content: bytes) -> str:
    header = f"blob {len(content)}\0".encode("ascii")
    return sha1(header + content).hexdigest()  # noqa: S324 - Git identity


def _truncate(connection) -> None:
    connection.execute(
        """
        TRUNCATE TABLE
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


def _setup() -> None:
    assert DSN is not None
    connection = psycopg.connect(DSN, autocommit=True)
    try:
        apply_migrations(connection)
        _truncate(connection)
        repository = ExecutionPostgresRepository(connection)
        repository.put(
            {
                "record_type": "source",
                "id": SOURCE_ID,
                "kind": "repository",
                "origin": {
                    "provider": "github",
                    "repository": "example/execution-cli",
                    "url": "https://github.com/example/execution-cli",
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
            rationale="CLI fixture selected for exact review.",
            actor=HUMAN,
            decision_id="sd:execution-cli",
        )
        AcquisitionAuthorizationEngine(repository).authorize_from_fields(
            source_id=SOURCE_ID,
            selection_decision_id=selection["id"],
            revision=SHA,
            allowed_paths=["README.md"],
            rationale="CLI fixture authorizes one exact file.",
            actor=HUMAN,
            authorization_id="aa:execution-cli",
        )
    finally:
        connection.close()


def test_cli_requires_database_url(monkeypatch, capsys):
    monkeypatch.delenv("KTHUB_DATABASE_URL", raising=False)
    monkeypatch.setattr(sys, "argv", ["kneekura-acquisition-exec", "history"])
    assert execution_cli.main() == 1
    assert "KTHUB_DATABASE_URL is required" in capsys.readouterr().out


@pytest.mark.skipif(not DSN, reason="KTHUB_TEST_DATABASE_URL is not set")
def test_cli_executes_exact_authorization_without_printing_token(monkeypatch, tmp_path: Path, capsys):
    _setup()
    assert DSN is not None
    monkeypatch.setenv("KTHUB_DATABASE_URL", DSN)
    monkeypatch.setenv("TEST_EXEC_TOKEN", "super-secret-token")
    content = b"cli offline content\n"

    def fake_fetch(source, revision, path, *, token=None):
        assert source["id"] == SOURCE_ID
        assert revision == SHA
        assert path == "README.md"
        assert token == "super-secret-token"
        return {"content": content, "git_blob_sha": _blob_sha(content)}

    monkeypatch.setattr(execution_cli, "fetch_github_file", fake_fetch)
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "kneekura-acquisition-exec",
            "execute",
            "aa:execution-cli",
            "--storage-root",
            str(tmp_path),
            "--actor-id",
            "cli-fetcher",
            "--actor-version",
            "test",
            "--execution-id",
            "ax:execution-cli",
            "--github-token-env",
            "TEST_EXEC_TOKEN",
        ],
    )

    assert execution_cli.main() == 0
    output = capsys.readouterr().out
    assert '"status": "SUCCEEDED"' in output
    assert "super-secret-token" not in output

    connection = psycopg.connect(DSN, autocommit=True)
    try:
        repository = ExecutionPostgresRepository(connection)
        record = repository.get("ax:execution-cli")
        assert record is not None
        assert (tmp_path / record["storage_key"] / "README.md").read_bytes() == content
        assert repository.get(SOURCE_ID)["acquisition"] == {"level": "metadata-only"}
        assert repository.list("source_snapshot") == []
    finally:
        connection.close()


@pytest.mark.skipif(not DSN, reason="KTHUB_TEST_DATABASE_URL is not set")
def test_cli_history_is_read_only(monkeypatch, capsys):
    _setup()
    assert DSN is not None
    monkeypatch.setenv("KTHUB_DATABASE_URL", DSN)
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "kneekura-acquisition-exec",
            "history",
            "--authorization-id",
            "aa:execution-cli",
        ],
    )
    assert execution_cli.main() == 0
    assert capsys.readouterr().out.strip() == "[]"
