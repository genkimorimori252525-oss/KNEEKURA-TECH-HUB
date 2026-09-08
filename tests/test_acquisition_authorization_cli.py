from __future__ import annotations

import json
import os
import sys

import psycopg
import pytest

from kneekura_tech_hub import authorization_cli
from kneekura_tech_hub.authorization_postgres import AuthorizationPostgresRepository
from kneekura_tech_hub.database import apply_migrations
from kneekura_tech_hub.selection import SourceSelectionEngine


DSN = os.getenv("KTHUB_TEST_DATABASE_URL")
pytestmark = pytest.mark.skipif(not DSN, reason="KTHUB_TEST_DATABASE_URL is not set")
SOURCE_ID = "src:github:example:authorization-cli"
SELECTION_ID = "sd:authorization-cli"
SHA = "0123456789abcdef0123456789abcdef01234567"
HUMAN = {"actor_type": "human", "actor_id": "cli-reviewer"}


def _reset_and_seed() -> None:
    assert DSN is not None
    connection = psycopg.connect(DSN, autocommit=True)
    try:
        apply_migrations(connection)
        connection.execute(
            """
            TRUNCATE TABLE
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
        repository = AuthorizationPostgresRepository(connection)
        repository.put(
            {
                "record_type": "source",
                "id": SOURCE_ID,
                "kind": "repository",
                "origin": {
                    "provider": "github",
                    "repository": "example/authorization-cli",
                    "url": "https://github.com/example/authorization-cli",
                },
                "acquisition": {"level": "metadata-only"},
                "license": {
                    "state": "KNOWN",
                    "declared_expression": "MIT",
                    "handling_policy": "REFERENCE_ONLY",
                },
            }
        )
        SourceSelectionEngine(repository).create_from_fields(
            source_id=SOURCE_ID,
            decision="SELECT_FOR_REVIEW",
            rationale="CLI authorization acceptance fixture.",
            actor=HUMAN,
            decision_id=SELECTION_ID,
        )
    finally:
        connection.close()


def test_cli_authorize_read_and_revoke_without_acquisition_mutation(monkeypatch, capsys):
    assert DSN is not None
    _reset_and_seed()
    monkeypatch.setenv("KTHUB_DATABASE_URL", DSN)
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "kneekura-acquisition-auth",
            "authorize",
            SOURCE_ID,
            "--selection-id",
            SELECTION_ID,
            "--revision",
            SHA,
            "--path",
            "README.md",
            "--path",
            "src/lib.rs",
            "--rationale",
            "Authorize exactly two pinned files; do not fetch them yet.",
            "--actor-id",
            "cli-reviewer",
            "--authorization-id",
            "aa:cli:first",
        ],
    )

    assert authorization_cli.main() == 0
    authorization = json.loads(capsys.readouterr().out)
    assert authorization["id"] == "aa:cli:first"
    assert authorization["allowed_paths"] == ["README.md", "src/lib.rs"]

    monkeypatch.setattr(sys, "argv", ["kneekura-acquisition-auth", "authorized"])
    assert authorization_cli.main() == 0
    authorized = json.loads(capsys.readouterr().out)
    assert authorized[0]["authorization"]["id"] == "aa:cli:first"
    assert authorized[0]["source"]["acquisition"] == {"level": "metadata-only"}

    monkeypatch.setattr(
        sys,
        "argv",
        [
            "kneekura-acquisition-auth",
            "revoke",
            "aa:cli:first",
            "--rationale",
            "Cancel before retrieval execution.",
            "--actor-id",
            "cli-reviewer",
            "--revocation-id",
            "aa:cli:revoke",
        ],
    )
    assert authorization_cli.main() == 0
    revoked = json.loads(capsys.readouterr().out)
    assert revoked["decision"] == "REVOKE"
    assert revoked["supersedes_authorization_id"] == "aa:cli:first"

    monkeypatch.setattr(sys, "argv", ["kneekura-acquisition-auth", "authorized"])
    assert authorization_cli.main() == 0
    assert json.loads(capsys.readouterr().out) == []


def test_cli_requires_database_url(monkeypatch, capsys):
    monkeypatch.delenv("KTHUB_DATABASE_URL", raising=False)
    monkeypatch.setattr(sys, "argv", ["kneekura-acquisition-auth", "authorized"])

    assert authorization_cli.main() == 1
    assert "KTHUB_DATABASE_URL is required" in capsys.readouterr().out
