from __future__ import annotations

import json
import os
import sys

import psycopg
import pytest

from kneekura_tech_hub import selection_cli
from kneekura_tech_hub.database import apply_migrations
from kneekura_tech_hub.selection_postgres import SelectionPostgresRepository


DSN = os.getenv("KTHUB_TEST_DATABASE_URL")
pytestmark = pytest.mark.skipif(not DSN, reason="KTHUB_TEST_DATABASE_URL is not set")
SOURCE_ID = "src:github:example:selection-cli"


def _reset_and_seed() -> None:
    assert DSN is not None
    connection = psycopg.connect(DSN, autocommit=True)
    try:
        apply_migrations(connection)
        connection.execute(
            """
            TRUNCATE TABLE
                source_selection_decision,
                review_decision,
                staged_observation_evidence,
                claim_evidence, claim, evidence_relation, evidence,
                source_snapshot, staged_observation, curation_event,
                entity_relation, entity_kind, entity_alias, knowledge_entity, source
            RESTART IDENTITY CASCADE
            """
        )
        SelectionPostgresRepository(connection).put(
            {
                "record_type": "source",
                "id": SOURCE_ID,
                "kind": "repository",
                "origin": {
                    "provider": "github",
                    "repository": "example/selection-cli",
                    "url": "https://github.com/example/selection-cli",
                },
                "acquisition": {"level": "metadata-only"},
                "license": {
                    "state": "REVIEW_REQUIRED",
                    "declared_expression": None,
                    "handling_policy": "DISCOVERY_METADATA_ONLY",
                },
            }
        )
    finally:
        connection.close()


def test_cli_decide_and_selected_keep_source_metadata_only(monkeypatch, capsys):
    assert DSN is not None
    _reset_and_seed()
    monkeypatch.setenv("KTHUB_DATABASE_URL", DSN)
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "kneekura-source-selection",
            "decide",
            SOURCE_ID,
            "SELECT_FOR_REVIEW",
            "--rationale",
            "Manual architecture review is warranted.",
            "--actor-id",
            "cli-reviewer",
            "--decision-id",
            "sd:cli:first",
        ],
    )

    assert selection_cli.main() == 0
    decision = json.loads(capsys.readouterr().out)
    assert decision["id"] == "sd:cli:first"
    assert decision["created_by"] == {"actor_type": "human", "actor_id": "cli-reviewer"}

    monkeypatch.setattr(sys, "argv", ["kneekura-source-selection", "selected"])
    assert selection_cli.main() == 0
    selected = json.loads(capsys.readouterr().out)
    assert selected[0]["decision"]["id"] == "sd:cli:first"
    assert selected[0]["source"]["id"] == SOURCE_ID
    assert selected[0]["source"]["acquisition"] == {"level": "metadata-only"}


def test_cli_requires_database_url(monkeypatch, capsys):
    monkeypatch.delenv("KTHUB_DATABASE_URL", raising=False)
    monkeypatch.setattr(sys, "argv", ["kneekura-source-selection", "selected"])

    assert selection_cli.main() == 1
    assert "KTHUB_DATABASE_URL is required" in capsys.readouterr().out
