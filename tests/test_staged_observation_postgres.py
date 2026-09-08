from __future__ import annotations

import os

import psycopg
import pytest

from kneekura_tech_hub.database import apply_migrations
from kneekura_tech_hub.postgres_repository import PostgresRepository
from kneekura_tech_hub.service import CurationEngine


DSN = os.getenv("KTHUB_TEST_DATABASE_URL")
pytestmark = pytest.mark.skipif(not DSN, reason="KTHUB_TEST_DATABASE_URL is not set")

HUMAN = {"actor_type": "human", "actor_id": "reviewer"}
AI = {"actor_type": "ai", "actor_id": "extractor", "version": "test"}


@pytest.fixture
def repository() -> PostgresRepository:
    assert DSN is not None
    connection = psycopg.connect(DSN, autocommit=True)
    applied = apply_migrations(connection)
    assert "0002_staged_observation_evidence.sql" in {path.name for path in applied}
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


def test_staged_observation_evidence_candidates_round_trip(repository: PostgresRepository):
    engine = CurationEngine(repository)
    source = {
        "record_type": "source",
        "id": "src:obs-pg",
        "kind": "repository",
        "origin": {"provider": "github", "repository": "example/obs-pg"},
        "acquisition": {"level": "metadata-only"},
        "license": {"state": "UNKNOWN"},
    }
    snapshot = {
        "record_type": "source_snapshot",
        "id": "ss:obs-pg",
        "source_id": "src:obs-pg",
        "revision": "0123456789abcdef",
        "captured_at": "2026-09-09T00:00:00Z",
    }
    evidence = {
        "record_type": "evidence",
        "id": "ev:obs-pg",
        "source_id": "src:obs-pg",
        "source_snapshot_id": "ss:obs-pg",
        "locator": {
            "type": "source_lines",
            "path": "src/lib.rs",
            "line_start": 1,
            "line_end": 2,
            "content_hash": "sha256:obs-pg",
        },
        "roles": ["SUPPORTS"],
    }
    observation = {
        "record_type": "staged_observation",
        "id": "obs:pg",
        "source_id": "src:obs-pg",
        "evidence_candidate_ids": ["ev:obs-pg"],
        "summary": "Possible incremental design",
        "candidate_names": ["Incremental design"],
        "status": "NEW",
        "created_by": AI,
    }

    engine.register_source(source, actor=HUMAN)
    engine.register_source_snapshot(snapshot, actor=HUMAN)
    engine.register_evidence(evidence, actor=HUMAN)
    engine.stage_observation(observation, actor=AI)

    reloaded = repository.get("obs:pg")
    assert reloaded is not None
    assert reloaded["evidence_candidate_ids"] == ["ev:obs-pg"]
    assert reloaded["created_by"] == AI

    anchor = repository.get(reloaded["evidence_candidate_ids"][0])
    assert anchor is not None
    assert anchor["source_snapshot_id"] == "ss:obs-pg"
