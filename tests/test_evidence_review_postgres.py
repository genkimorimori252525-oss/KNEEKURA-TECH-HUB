from __future__ import annotations

import json
import os
from pathlib import Path

import psycopg
import pytest

from kneekura_tech_hub.bundle import ingest_bundle
from kneekura_tech_hub.database import apply_migrations
from kneekura_tech_hub.postgres_repository import PostgresRepository
from kneekura_tech_hub.review import review_claim
from kneekura_tech_hub.service import CurationEngine


DSN = os.getenv("KTHUB_TEST_DATABASE_URL")
pytestmark = pytest.mark.skipif(not DSN, reason="KTHUB_TEST_DATABASE_URL is not set")
ROOT = Path(__file__).resolve().parents[1]
HUMAN = {"actor_type": "human", "actor_id": "review-profile-reviewer"}
CLAIM_ID = "cl:salsa:query-incremental:solves:repeated-recomputation:e021c01d"
SALSA_SOURCE = "src:github:salsa-rs:salsa"
SALSA_SNAPSHOT = "ss:github:salsa-rs:salsa:e021c01d"


def _load(name: str) -> dict:
    return json.loads((ROOT / "pilots" / name).read_text(encoding="utf-8"))


def test_real_salsa_review_separates_evidence_profile_from_claim_maturity():
    assert DSN is not None
    connection = psycopg.connect(DSN, autocommit=True)
    try:
        apply_migrations(connection)
        connection.execute(
            """
            TRUNCATE TABLE
                staged_observation_evidence,
                claim_evidence, claim, evidence_relation, evidence,
                source_snapshot, staged_observation, curation_event,
                entity_relation, entity_kind, entity_alias, knowledge_entity, source
            RESTART IDENTITY CASCADE
            """
        )
        repository = PostgresRepository(connection)
        engine = CurationEngine(repository)

        with connection.transaction():
            ingest_bundle(engine, _load("incremental-computation-v1.json"), actor=HUMAN)
            ingest_bundle(engine, _load("incremental-computation-problems-v1.json"), actor=HUMAN)

        before = review_claim(repository, CLAIM_ID)

        assert before["maturity"] == "CANDIDATE"
        assert before["verification"]["freshness"] == "NEVER_VERIFIED"
        assert before["evidence"]["count"] == 2
        assert before["evidence"]["distinct_source_count"] == 1
        assert before["evidence"]["distinct_snapshot_count"] == 1
        assert before["evidence"]["source_ids"] == [SALSA_SOURCE]
        assert before["evidence"]["snapshot_ids"] == [SALSA_SNAPSHOT]
        assert before["evidence"]["role_counts"] == {"SUPPORTS": 2}
        assert before["evidence"]["locator_type_counts"] == {"source_lines": 2}
        assert "SINGLE_SOURCE" in before["flags"]
        assert "score" not in before
        assert "strength" not in before

        engine.transition_claim(
            CLAIM_ID,
            "SUPPORTED",
            actor=HUMAN,
            reason="review profile pilot reviewed",
        )
        engine.transition_claim(
            CLAIM_ID,
            "VALIDATED",
            actor=HUMAN,
            reason="review profile pilot verified",
        )

        after = review_claim(repository, CLAIM_ID)

        assert after["maturity"] == "VALIDATED"
        assert after["verification"]["freshness"] == "NO_DUE_DATE"
        assert after["verification"]["last_verified"] is not None

        # Human validation changes trust state, not the underlying evidence profile.
        assert after["evidence"] == before["evidence"]
        assert "SINGLE_SOURCE" in after["flags"]
        assert repository.get(CLAIM_ID)["created_by"]["actor_type"] == "ai"
    finally:
        connection.close()
