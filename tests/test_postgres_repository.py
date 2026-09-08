from __future__ import annotations

import os
from pathlib import Path

import psycopg
import pytest

from kneekura_tech_hub.postgres_repository import PostgresRepository
from kneekura_tech_hub.service import CurationEngine


DSN = os.getenv("KTHUB_TEST_DATABASE_URL")
pytestmark = pytest.mark.skipif(not DSN, reason="KTHUB_TEST_DATABASE_URL is not set")

HUMAN = {"actor_type": "human", "actor_id": "integration-reviewer"}


def _apply_migration(connection: psycopg.Connection) -> None:
    sql = Path("migrations/0001_foundation.sql").read_text(encoding="utf-8")
    for statement in sql.split(";"):
        statement = statement.strip()
        if not statement or statement in {"BEGIN", "COMMIT"}:
            continue
        connection.execute(statement)


@pytest.fixture
def repository() -> PostgresRepository:
    assert DSN is not None
    connection = psycopg.connect(DSN, autocommit=True)
    _apply_migration(connection)
    connection.execute(
        """
        TRUNCATE TABLE
            claim_evidence, claim, evidence_relation, evidence,
            source_snapshot, staged_observation, curation_event,
            entity_relation, entity_kind, entity_alias, knowledge_entity, source
        RESTART IDENTITY CASCADE
        """
    )
    repo = PostgresRepository(connection)
    yield repo
    repo.close()


def test_postgres_round_trip_and_claim_lifecycle(repository: PostgresRepository):
    engine = CurationEngine(repository)

    source = {
        "record_type": "source",
        "id": "src:integration",
        "kind": "repository",
        "origin": {"provider": "github", "repository": "example/integration"},
        "acquisition": {"level": "snapshot"},
        "license": {
            "state": "KNOWN",
            "declared_expression": "MIT",
            "handling_policy": "reference_only",
        },
    }
    snapshot = {
        "record_type": "source_snapshot",
        "id": "ss:integration",
        "source_id": "src:integration",
        "revision": "0123456789abcdef0123456789abcdef01234567",
        "captured_at": "2026-09-09T00:00:00+00:00",
        "metadata": {"branch": "main"},
    }
    entity = {
        "record_type": "knowledge_entity",
        "id": "ke:integration",
        "canonical_name": "Incremental Computation",
        "aliases": ["Incremental Recalculation"],
        "kinds": ["technique"],
        "abstraction_level": "L1",
        "identity_state": "CANONICAL",
        "relations": [],
    }
    evidence = {
        "record_type": "evidence",
        "id": "ev:integration",
        "source_id": "src:integration",
        "source_snapshot_id": "ss:integration",
        "locator": {
            "type": "source_lines",
            "path": "src/cache.rs",
            "line_start": 10,
            "line_end": 20,
            "content_hash": "sha256:integration",
        },
        "roles": ["SUPPORTS"],
    }
    claim = {
        "record_type": "claim",
        "id": "cl:integration",
        "entity_id": "ke:integration",
        "claim_type": "DIRECT_OBSERVATION",
        "statement": "The pinned source contains an invalidation path.",
        "maturity": "CANDIDATE",
        "evidence_ids": ["ev:integration"],
        "created_by": HUMAN,
        "policy_version": "1.0.0",
    }

    engine.register_source(source, actor=HUMAN)
    engine.register_source_snapshot(snapshot, actor=HUMAN)
    engine.create_entity(entity, actor=HUMAN)
    engine.register_evidence(evidence, actor=HUMAN)
    engine.create_claim(claim, actor=HUMAN)
    engine.transition_claim(
        "cl:integration",
        "SUPPORTED",
        actor=HUMAN,
        reason="anchored evidence reviewed",
    )
    engine.transition_claim(
        "cl:integration",
        "VALIDATED",
        actor=HUMAN,
        reason="integration verification",
    )

    stored_snapshot = repository.get("ss:integration")
    stored_claim = repository.get("cl:integration")
    stored_entity = repository.get("ke:integration")

    assert stored_snapshot is not None
    assert stored_snapshot["revision"] == snapshot["revision"]
    assert stored_entity is not None
    assert stored_entity["aliases"] == ["Incremental Recalculation"]
    assert stored_claim is not None
    assert stored_claim["maturity"] == "VALIDATED"
    assert stored_claim["evidence_ids"] == ["ev:integration"]
    assert stored_claim["last_verified"]
    assert len(repository.list("curation_event")) >= 5
