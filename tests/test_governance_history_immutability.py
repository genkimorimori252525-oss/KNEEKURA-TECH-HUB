from __future__ import annotations

import os

import psycopg
import pytest
from psycopg.types.json import Jsonb

from kneekura_tech_hub.database import apply_migrations
from kneekura_tech_hub.repository import MemoryRepository


DSN = os.getenv("KTHUB_TEST_DATABASE_URL")

APPEND_ONLY_TYPES = {
    "curation_event",
    "review_decision",
    "source_selection_decision",
    "source_acquisition_authorization",
    "source_acquisition_execution",
    "source_acquisition_commit",
    "observation_triage_decision",
}

EXPECTED_TRIGGERS = {
    "curation_event": "trg_curation_event_append_only",
    "review_decision": "trg_review_decision_append_only",
    "source_selection_decision": "trg_source_selection_decision_append_only",
    "source_acquisition_authorization": "trg_source_acquisition_authorization_append_only",
    "source_acquisition_execution": "trg_source_acquisition_execution_append_only",
    "source_acquisition_commit": "trg_source_acquisition_commit_append_only",
    "observation_triage_decision": "trg_observation_triage_decision_append_only",
}


def test_memory_declared_governance_history_is_append_only() -> None:
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

        with pytest.raises(ValueError, match="append-only"):
            repository.put(changed, replace=True)

        assert repository.get(record["id"]) == record


@pytest.mark.skipif(not DSN, reason="KTHUB_TEST_DATABASE_URL is not set")
def test_postgres_all_declared_governance_history_tables_have_mutation_guards() -> None:
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
            assert "BEFORE UPDATE OR DELETE" in definition
            assert "kthub_reject_governance_history_mutation" in definition


@pytest.mark.skipif(not DSN, reason="KTHUB_TEST_DATABASE_URL is not set")
def test_postgres_curation_event_cannot_be_rewritten_or_deleted_directly() -> None:
    assert DSN is not None
    event_id = "ce:governance-history-immutability"

    with psycopg.connect(DSN, autocommit=True) as connection:
        apply_migrations(connection)
        connection.execute("TRUNCATE TABLE curation_event")
        connection.execute(
            """
            INSERT INTO curation_event(
                id, operation, actor, subject_ids, reason,
                policy_version, occurred_at, reversible
            ) VALUES (%s,%s,%s,%s,%s,%s,now(),false)
            """,
            (
                event_id,
                "TEST_AUDIT_EVENT",
                Jsonb({"actor_type": "human", "actor_id": "audit-test"}),
                Jsonb(["subject:test"]),
                "original reason",
                "1.0.0",
            ),
        )

        with pytest.raises(psycopg.Error, match="append-only"):
            connection.execute(
                "UPDATE curation_event SET reason='tampered' WHERE id=%s",
                (event_id,),
            )
        with pytest.raises(psycopg.Error, match="append-only"):
            connection.execute("DELETE FROM curation_event WHERE id=%s", (event_id,))

        row = connection.execute(
            "SELECT reason FROM curation_event WHERE id=%s", (event_id,)
        ).fetchone()
        assert row == ("original reason",)
