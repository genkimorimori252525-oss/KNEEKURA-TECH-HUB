from __future__ import annotations

from hashlib import sha1
import os
from pathlib import Path
import sys

import psycopg
import pytest

import kneekura_tech_hub.verified_commit_cli as commit_cli
from kneekura_tech_hub.authorization import AcquisitionAuthorizationEngine
from kneekura_tech_hub.database import apply_migrations
from kneekura_tech_hub.execution import execute_authorized_acquisition
from kneekura_tech_hub.selection import SourceSelectionEngine
from kneekura_tech_hub.verified_commit_postgres import VerifiedCommitPostgresRepository


DSN = os.getenv("KTHUB_TEST_DATABASE_URL")
SHA = "0123456789abcdef0123456789abcdef01234567"
SOURCE_ID = "src:github:example:verified-commit-cli"
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


def _setup(storage_root: Path) -> None:
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
                    "repository": "example/verified-commit-cli",
                    "url": "https://github.com/example/verified-commit-cli",
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
            rationale="CLI commit fixture selected.",
            actor=HUMAN,
            decision_id="sd:verified-commit-cli",
        )
        authorization = AcquisitionAuthorizationEngine(repository).authorize_from_fields(
            source_id=SOURCE_ID,
            selection_decision_id=selection["id"],
            revision=SHA,
            allowed_paths=["README.md"],
            rationale="CLI commit fixture authorizes README only.",
            actor=HUMAN,
            authorization_id="aa:verified-commit-cli",
        )
        content = b"verified commit cli\n"
        execute_authorized_acquisition(
            repository,
            authorization["id"],
            storage_root=storage_root,
            fetch_file=lambda *_args: {"content": content, "git_blob_sha": _blob_sha(content)},
            actor={"actor_type": "tool", "actor_id": "cli-fetcher", "version": "v1"},
            execution_id="ax:verified-commit-cli",
        )
    finally:
        connection.close()


def test_cli_requires_database_url(monkeypatch, capsys):
    monkeypatch.delenv("KTHUB_DATABASE_URL", raising=False)
    monkeypatch.setattr(sys, "argv", ["kneekura-acquisition-commit", "history"])
    assert commit_cli.main() == 1
    assert "KTHUB_DATABASE_URL is required" in capsys.readouterr().out


@pytest.mark.skipif(not DSN, reason="KTHUB_TEST_DATABASE_URL is not set")
def test_cli_verify_is_read_only_then_commit_promotes_source(monkeypatch, tmp_path: Path, capsys):
    _setup(tmp_path)
    assert DSN is not None
    monkeypatch.setenv("KTHUB_DATABASE_URL", DSN)

    monkeypatch.setattr(
        sys,
        "argv",
        [
            "kneekura-acquisition-commit",
            "verify",
            "ax:verified-commit-cli",
            "--storage-root",
            str(tmp_path),
        ],
    )
    assert commit_cli.main() == 0
    output = capsys.readouterr().out
    assert "VERIFIED_NOT_COMMITTED" in output

    connection = psycopg.connect(DSN, autocommit=True)
    try:
        repository = VerifiedCommitPostgresRepository(connection)
        assert repository.get(SOURCE_ID)["acquisition"] == {"level": "metadata-only"}
        assert repository.list("source_snapshot") == []
        assert repository.list("source_acquisition_commit") == []
    finally:
        connection.close()

    monkeypatch.setattr(
        sys,
        "argv",
        [
            "kneekura-acquisition-commit",
            "commit",
            "ax:verified-commit-cli",
            "--storage-root",
            str(tmp_path),
            "--actor-id",
            "cli-committer",
            "--actor-version",
            "test",
            "--commit-id",
            "vc:verified-commit-cli",
        ],
    )
    assert commit_cli.main() == 0
    output = capsys.readouterr().out
    assert '"id": "vc:verified-commit-cli"' in output

    connection = psycopg.connect(DSN, autocommit=True)
    try:
        repository = VerifiedCommitPostgresRepository(connection)
        assert repository.get(SOURCE_ID)["acquisition"] == {"level": "selected-files"}
        assert len(repository.list("source_snapshot")) == 1
        assert len(repository.list("source_acquisition_commit")) == 1
        assert repository.list("evidence") == []
    finally:
        connection.close()
