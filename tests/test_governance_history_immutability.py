from __future__ import annotations

import os

import psycopg
import pytest
from psycopg.types.json import Jsonb

from kneekura_tech_hub.database import apply_migrations
from kneekura_tech_hub.repository import MemoryRepository


DSN = os.getenv("KTHUB_TEST_DATABASE_URL")

APPEND_ONLY_TYPES = {
    "review_decision",
    "source_selection_decision",
    "source_acquisition_authorization",
    "source_acquisition_execution",
    "source_acquisition_commit",
    "observation_triage_decision",
}

EXPECTED_TRIGGERS = {
    "review_decision": "trg_review_decision_append_only",
    "source_selection_decision": "trg_source_selection_decision_append_only",
    "source_acquisition_authorization": "trg_source_acquisition_authorization_append_only",
    "source_acquisition_execution": "trg_source_acquisition_execution_append_only",
    "source_acquisition_commit": "trg_source_acquisition_commit_append_only",
    "observation_triage_decision": "trg_observation_triage_decision_append_only",
}


def test_memory_governance_history_is_append_only() -> None:
    repository = MemoryRepository()

    for index, record_type in enumerate(sorted(APPEND_ONLY_TYPES)):
        record = {
            "record_type": record_type,
            "id": f"history:{index}",
            "payload": "original",
        }
        repository.put(record)
        changed = dict(record)
        changed["payload"] = "tampered"

        with pytest.raises(ValueError, match="immutable|append-only"):
            repository.put(changed, replace=True)

        assert repository.get(record["id"]) == record


@pytest.mark.skipif(not DSN, reason="KTHUB_TEST_DATABASE_URL is not set")
def test_postgres_all_governance_history_tables_have_mutation_guards() -> None:
    assert DSN is not None
    with psycopg.connect(DSN, autocommit=True) as connection:
        apply_migrations(connection)

        rows = connection.execute(
            """
            SELECT cls.relname, trg.tgname, pg_get_triggerdef(trg.oid)
            FROM pg_trigger AS trg
            JOIN pg_class AS cls ON cls.oid = trg.tgrelid
            WHERE NOT trg.tgisinternal
              AND cls.relname = ANY(%s)
            """,
            (list(EXPECTED_TRIGGERS),),
        ).fetchall()

        by_table = {(table, trigger): definition for table, trigger, definition in rows}
        for table, trigger in EXPECTED_TRIGGERS.items():
            definition = by_table[(table, trigger)]
            assert "BEFORE" in definition
            assert "UPDATE" in definition
            assert "DELETE" in definition
            assert "kthub_reject_governance_history_mutation" in definition


@pytest.mark.skipif(not DSN, reason="KTHUB_TEST_DATABASE_URL is not set")
def test_postgres_selection_decision_cannot_be_rewritten_or_deleted_directly() -> None:
    assert DSN is not None
    source_id = "src:governance-history"
    decision_id = "sd:governance-history"

    with psycopg.connect(DSN, autocommit=True) as connection:
        apply_migrations(connection)
        connection.execute(
            "TRUNCATE TABLE source_selection_decision, source RESTART IDENTITY CASCADE"
        )
        connection.execute(
            """
            INSERT INTO source(id, kind, origin, license, acquisition_level)
            VALUES (%s, 'repository', %s, %s, 'metadata-only')
            """,
            (
                source_id,
                Jsonb({"provider": "fixture", "repository": "example/history"}),
                Jsonb({"state": "KNOWN", "declared_expression": "MIT"}),
            ),
        )
        connection.execute(
            """
            INSERT INTO source_selection_decision(
                id, source_id, decision, rationale, created_by,
                policy_version, decided_at, supersedes_decision_id
            ) VALUES (%s,%s,'SELECT_FOR_REVIEW','original rationale',%s,'1.0.0',now(),NULL)
            """,
            (
                decision_id,
                source_id,
                Jsonb({"actor_type": "human", "actor_id": "history-reviewer"}),
            ),
        )

        with pytest.raises(psycopg.Error, match="append-only"):
            connection.execute(
                "UPDATE source_selection_decision SET rationale='tampered' WHERE id=%s",
                (decision_id,),
            )
        with pytest.raises(psycopg.Error, match="append-only"):
            connection.execute(
                "DELETE FROM source_selection_decision WHERE id=%s",
                (decision_id,),
            )

        row = connection.execute(
            "SELECT rationale FROM source_selection_decision WHERE id=%s",
            (decision_id,),
        ).fetchone()
        assert row == ("original rationale",)
