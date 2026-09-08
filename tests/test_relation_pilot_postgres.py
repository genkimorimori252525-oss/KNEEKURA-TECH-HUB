from __future__ import annotations

import json
import os
from pathlib import Path

import psycopg
import pytest

from kneekura_tech_hub.bundle import ingest_bundle
from kneekura_tech_hub.database import apply_migrations
from kneekura_tech_hub.postgres_repository import PostgresRepository
from kneekura_tech_hub.service import CurationEngine


DSN = os.getenv("KTHUB_TEST_DATABASE_URL")
pytestmark = pytest.mark.skipif(not DSN, reason="KTHUB_TEST_DATABASE_URL is not set")
HUMAN = {"actor_type": "human", "actor_id": "pilot-reviewer"}
ROOT = Path(__file__).resolve().parents[1]


def _load(name: str) -> dict:
    return json.loads((ROOT / "pilots" / name).read_text(encoding="utf-8"))


def test_relation_overlay_ingests_after_real_oss_base_pilot():
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

        base = _load("incremental-computation-v1.json")
        overlay = _load("incremental-computation-relations-v1.json")

        with connection.transaction():
            base_ids = ingest_bundle(engine, base, actor=HUMAN)
            overlay_ids = ingest_bundle(engine, overlay, actor=HUMAN)

        assert len(base_ids) == 18
        assert overlay_ids == [
            "cl:salsa:query-incremental:narrower-than:incremental:e021c01d"
        ]

        relation_claim = repository.get(overlay_ids[0])
        assert relation_claim is not None
        assert relation_claim["maturity"] == "CANDIDATE"
        assert relation_claim["claim_type"] == "INFERENCE"
        assert relation_claim["confidence"] == "MEDIUM"
        assert relation_claim["created_by"]["actor_type"] == "ai"
        assert relation_claim["relation"] == {
            "source_entity_id": "ke:query-based-incremental-computation",
            "relation_type": "narrower_than",
            "target_entity_id": "ke:incremental-computation",
        }
        assert repository.get("ke:query-based-incremental-computation")["relations"] == []
        assert repository.get("ke:incremental-computation")["relations"] == []
    finally:
        connection.close()
