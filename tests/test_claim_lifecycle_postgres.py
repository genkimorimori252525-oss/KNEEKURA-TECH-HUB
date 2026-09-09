from __future__ import annotations

import os

import psycopg
import pytest

from kneekura_tech_hub.database import apply_migrations


DSN = os.getenv("KTHUB_TEST_DATABASE_URL")
pytestmark = pytest.mark.skipif(not DSN, reason="KTHUB_TEST_DATABASE_URL is not set")
ENTITY_ID = "ke:lifecycle:postgres"


@pytest.fixture()
def connection():
    assert DSN is not None
    with psycopg.connect(DSN, autocommit=True) as setup:
        apply_migrations(setup)
        setup.execute(
            "TRUNCATE TABLE source, knowledge_entity, curation_event RESTART IDENTITY CASCADE"
        )
        setup.execute(
            """
            INSERT INTO knowledge_entity(
                id, canonical_name, abstraction_level, identity_state
            ) VALUES (%s, %s, 'L1', 'CANONICAL')
            """,
            (ENTITY_ID, "Lifecycle fixture"),
        )
    conn = psycopg.connect(DSN, autocommit=True)
    try:
        yield conn
    finally:
        conn.close()


def _insert_claim(connection, claim_id: str, maturity: str, *, last_verified=None) -> None:
    connection.execute(
        """
        INSERT INTO claim(
            id, entity_id, claim_type, statement, maturity,
            created_by, policy_version, last_verified
        ) VALUES (%s, %s, 'JUDGMENT', %s, %s, %s::jsonb, '1.0.0', %s)
        """,
        (
            claim_id,
            ENTITY_ID,
            "Lifecycle fixture claim",
            maturity,
            '{"actor_type":"human","actor_id":"fixture"}',
            last_verified,
        ),
    )


def test_database_rejects_non_candidate_claim_inserts(connection) -> None:
    with pytest.raises(psycopg.Error, match="must start at CANDIDATE"):
        _insert_claim(connection, "cl:lifecycle:supported", "SUPPORTED")

    with pytest.raises(psycopg.Error, match="must start at CANDIDATE"):
        _insert_claim(
            connection,
            "cl:lifecycle:validated",
            "VALIDATED",
            last_verified="2026-09-09T01:00:00Z",
        )


def test_database_rejects_invalid_maturity_jump(connection) -> None:
    claim_id = "cl:lifecycle:jump"
    _insert_claim(connection, claim_id, "CANDIDATE")

    with pytest.raises(psycopg.Error, match="invalid claim lifecycle transition"):
        connection.execute(
            "UPDATE claim SET maturity='VALIDATED', last_verified=now() WHERE id=%s",
            (claim_id,),
        )

    row = connection.execute(
        "SELECT maturity, last_verified FROM claim WHERE id=%s", (claim_id,)
    ).fetchone()
    assert row == ("CANDIDATE", None)


def test_database_rejects_out_of_band_last_verified_mutation(connection) -> None:
    claim_id = "cl:lifecycle:timestamp"
    _insert_claim(connection, claim_id, "CANDIDATE")

    with pytest.raises(psycopg.Error, match="last_verified may change only"):
        connection.execute(
            "UPDATE claim SET last_verified=now() WHERE id=%s",
            (claim_id,),
        )

    assert connection.execute(
        "SELECT last_verified FROM claim WHERE id=%s", (claim_id,)
    ).fetchone()[0] is None


def test_database_still_allows_valid_candidate_rejection(connection) -> None:
    claim_id = "cl:lifecycle:reject"
    _insert_claim(connection, claim_id, "CANDIDATE")

    connection.execute("UPDATE claim SET maturity='REJECTED' WHERE id=%s", (claim_id,))

    assert connection.execute(
        "SELECT maturity FROM claim WHERE id=%s", (claim_id,)
    ).fetchone()[0] == "REJECTED"
