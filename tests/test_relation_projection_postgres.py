from __future__ import annotations

import json
import os
from pathlib import Path

import psycopg
import pytest

from kneekura_tech_hub.bundle import ingest_bundle
from kneekura_tech_hub.database import apply_migrations
from kneekura_tech_hub.postgres_repository import PostgresRepository
from kneekura_tech_hub.projection import project_relations
from kneekura_tech_hub.service import CurationEngine


DSN = os.getenv("KTHUB_TEST_DATABASE_URL")
pytestmark = pytest.mark.skipif(not DSN, reason="KTHUB_TEST_DATABASE_URL is not set")
HUMAN = {"actor_type": "human", "actor_id": "projection-reviewer"}
ROOT = Path(__file__).resolve().parents[1]
RELATION_CLAIM_ID = "cl:salsa:query-incremental:narrower-than:incremental:e021c01d"


def _load(name: str) -> dict:
    return json.loads((ROOT / "pilots" / name).read_text(encoding="utf-8"))


def test_real_pilot_relation_projection_changes_only_with_claim_maturity():
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
            ingest_bundle(
                engine,
                _load("incremental-computation-relations-v1.json"),
                actor=HUMAN,
            )

        assert project_relations(repository, view="validated") == []
        research = project_relations(repository, view="research")
        assert [edge["claim_id"] for edge in research] == [RELATION_CLAIM_ID]
        assert research[0]["maturity"] == "CANDIDATE"
        assert research[0]["claim_type"] == "INFERENCE"
        assert research[0]["evidence_ids"] == [
            "ev:salsa:readme:incrementalized-computation:e021c01d",
            "ev:salsa:readme:query-model:e021c01d",
        ]

        engine.transition_claim(
            RELATION_CLAIM_ID,
            "SUPPORTED",
            actor=HUMAN,
            reason="pilot relation reviewed",
        )
        assert project_relations(repository, view="validated") == []

        engine.transition_claim(
            RELATION_CLAIM_ID,
            "VALIDATED",
            actor=HUMAN,
            reason="pilot relation verified",
        )
        validated = project_relations(repository, view="validated")
        assert [edge["claim_id"] for edge in validated] == [RELATION_CLAIM_ID]
        assert validated[0]["maturity"] == "VALIDATED"
        assert validated[0]["relation"] == {
            "source_entity_id": "ke:query-based-incremental-computation",
            "relation_type": "narrower_than",
            "target_entity_id": "ke:incremental-computation",
        }
        assert repository.get("ke:query-based-incremental-computation")["relations"] == []
        assert repository.get("ke:incremental-computation")["relations"] == []
    finally:
        connection.close()
