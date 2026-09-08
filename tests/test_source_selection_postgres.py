from __future__ import annotations

import os

import psycopg
import pytest

from kneekura_tech_hub.database import apply_migrations
from kneekura_tech_hub.selection import (
    SourceSelectionEngine,
    active_source_selection_decisions,
    selected_for_review,
    source_selection_history,
)
from kneekura_tech_hub.selection_postgres import SelectionPostgresRepository


DSN = os.getenv("KTHUB_TEST_DATABASE_URL")
pytestmark = pytest.mark.skipif(not DSN, reason="KTHUB_TEST_DATABASE_URL is not set")
HUMAN = {"actor_type": "human", "actor_id": "postgres-reviewer"}


def _truncate(connection) -> None:
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


def _source() -> dict:
    return {
        "record_type": "source",
        "id": "src:github:example:selection-postgres",
        "kind": "repository",
        "origin": {
            "provider": "github",
            "repository": "example/selection-postgres",
            "url": "https://github.com/example/selection-postgres",
        },
        "acquisition": {"level": "metadata-only"},
        "license": {
            "state": "REVIEW_REQUIRED",
            "declared_expression": None,
            "handling_policy": "DISCOVERY_METADATA_ONLY",
        },
    }


def test_postgres_selection_round_trip_preserves_metadata_only_source():
    assert DSN is not None
    connection = psycopg.connect(DSN, autocommit=True)
    try:
        apply_migrations(connection)
        _truncate(connection)
        repository = SelectionPostgresRepository(connection)
        repository.put(_source())
        before = repository.get("src:github:example:selection-postgres")
        engine = SourceSelectionEngine(repository)

        first = engine.create_from_fields(
            source_id="src:github:example:selection-postgres",
            decision="SELECT_FOR_REVIEW",
            rationale="Manual review is warranted; this does not authorize acquisition.",
            actor=HUMAN,
            decision_id="sd:postgres:first",
        )

        assert repository.get(first["id"]) == first
        assert repository.get("src:github:example:selection-postgres") == before
        assert repository.get("src:github:example:selection-postgres")["acquisition"] == {
            "level": "metadata-only"
        }
        selected = selected_for_review(repository)
        assert [item["decision"]["id"] for item in selected] == ["sd:postgres:first"]
        assert selected[0]["source"] == before

        second = engine.create_from_fields(
            source_id="src:github:example:selection-postgres",
            decision="REJECT_FOR_REVIEW",
            rationale="Manual review found insufficient reason to deepen investigation.",
            actor=HUMAN,
            decision_id="sd:postgres:second",
            supersedes_decision_id="sd:postgres:first",
        )

        assert repository.get(second["id"]) == second
        assert [item["id"] for item in source_selection_history(repository)] == [
            "sd:postgres:first",
            "sd:postgres:second",
        ]
        assert [item["id"] for item in active_source_selection_decisions(repository)] == [
            "sd:postgres:second"
        ]
        assert selected_for_review(repository) == []
        assert repository.get("src:github:example:selection-postgres") == before
    finally:
        connection.close()


def test_selection_decision_table_is_append_only_through_repository():
    assert DSN is not None
    connection = psycopg.connect(DSN, autocommit=True)
    try:
        apply_migrations(connection)
        _truncate(connection)
        repository = SelectionPostgresRepository(connection)
        repository.put(_source())
        record = SourceSelectionEngine(repository).create_from_fields(
            source_id="src:github:example:selection-postgres",
            decision="DEFER",
            rationale="Wait for manual license resolution.",
            actor=HUMAN,
            decision_id="sd:postgres:append-only",
        )

        with pytest.raises(ValueError, match="append-only"):
            repository.put(record, replace=True)
    finally:
        connection.close()
