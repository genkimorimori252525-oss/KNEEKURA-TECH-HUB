from __future__ import annotations

import os

import psycopg
import pytest

from kneekura_tech_hub.database import apply_migrations
from kneekura_tech_hub.postgres_repository import PostgresRepository
from kneekura_tech_hub.service import CurationEngine


DSN = os.getenv("KTHUB_TEST_DATABASE_URL")
pytestmark = pytest.mark.skipif(not DSN, reason="KTHUB_TEST_DATABASE_URL is not set")

HUMAN = {"actor_type": "human", "actor_id": "relation-reviewer"}
AI = {"actor_type": "ai", "actor_id": "relation-extractor", "version": "test"}


def _entity(entity_id: str, name: str) -> dict:
    return {
        "record_type": "knowledge_entity",
        "id": entity_id,
        "canonical_name": name,
        "aliases": [],
        "kinds": ["technique"],
        "abstraction_level": "L1",
        "identity_state": "CANONICAL",
        "relations": [],
    }


@pytest.fixture
def repository() -> PostgresRepository:
    assert DSN is not None
    connection = psycopg.connect(DSN, autocommit=True)
    applied = apply_migrations(connection)
    assert "0003_relation_claim_subject.sql" in {path.name for path in applied}
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
    repo = PostgresRepository(connection)
    yield repo
    repo.close()


def test_relation_claim_round_trip_and_validation_lifecycle(repository: PostgresRepository):
    engine = CurationEngine(repository)
    engine.register_source(
        {
            "record_type": "source",
            "id": "src:relation-pg",
            "kind": "repository",
            "origin": {"provider": "github", "repository": "example/relation-pg"},
            "acquisition": {"level": "snapshot"},
            "license": {"state": "KNOWN", "declared_expression": "MIT"},
        },
        actor=HUMAN,
    )
    engine.register_source_snapshot(
        {
            "record_type": "source_snapshot",
            "id": "ss:relation-pg",
            "source_id": "src:relation-pg",
            "revision": "0123456789abcdef",
            "captured_at": "2026-09-09T00:00:00Z",
        },
        actor=HUMAN,
    )
    engine.register_evidence(
        {
            "record_type": "evidence",
            "id": "ev:relation-pg",
            "source_id": "src:relation-pg",
            "source_snapshot_id": "ss:relation-pg",
            "locator": {
                "type": "source_lines",
                "path": "README.md",
                "line_start": 1,
                "line_end": 3,
                "content_hash": "sha256:relation-pg",
            },
            "roles": ["SUPPORTS"],
        },
        actor=HUMAN,
    )
    engine.create_entity(_entity("ke:pg-general", "Incremental Computation"), actor=HUMAN)
    engine.create_entity(
        _entity("ke:pg-specific", "Query-based Incremental Computation"), actor=HUMAN
    )

    claim = {
        "record_type": "claim",
        "id": "cl:relation-pg",
        "relation": {
            "source_entity_id": "ke:pg-specific",
            "relation_type": "narrower_than",
            "target_entity_id": "ke:pg-general",
        },
        "claim_type": "INFERENCE",
        "statement": "The query-based technique is a specialization of incremental computation.",
        "maturity": "CANDIDATE",
        "evidence_ids": ["ev:relation-pg"],
        "confidence": "MEDIUM",
        "reasoning_basis": ["ev:relation-pg"],
        "created_by": AI,
        "policy_version": "1.0.0",
    }
    engine.create_claim(claim, actor=AI)
    engine.transition_claim("cl:relation-pg", "SUPPORTED", actor=HUMAN, reason="reviewed")
    engine.transition_claim(
        "cl:relation-pg", "VALIDATED", actor=HUMAN, reason="relation verified"
    )

    reloaded = repository.get("cl:relation-pg")
    assert reloaded is not None
    assert "entity_id" not in reloaded
    assert reloaded["relation"] == claim["relation"]
    assert reloaded["maturity"] == "VALIDATED"
    assert reloaded["evidence_ids"] == ["ev:relation-pg"]
    assert reloaded["created_by"] == AI
    assert reloaded["last_verified"]
    assert repository.get("ke:pg-specific")["relations"] == []
    assert repository.get("ke:pg-general")["relations"] == []
