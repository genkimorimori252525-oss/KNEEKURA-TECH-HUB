from __future__ import annotations

import json
import os
from pathlib import Path

import psycopg
import pytest

from kneekura_tech_hub.bundle import ingest_bundle
from kneekura_tech_hub.database import apply_foundation_migration
from kneekura_tech_hub.postgres_repository import PostgresRepository
from kneekura_tech_hub.service import CurationEngine, CurationError


DSN = os.getenv("KTHUB_TEST_DATABASE_URL")
pytestmark = pytest.mark.skipif(not DSN, reason="KTHUB_TEST_DATABASE_URL is not set")

HUMAN = {"actor_type": "human", "actor_id": "reviewer"}
AI = {"actor_type": "ai", "actor_id": "extractor", "version": "test"}
PILOT_REVIEWER = {"actor_type": "human", "actor_id": "prototype-reviewer"}


def _bundle(*, claim_creator: dict, entity_state: str = "CANONICAL") -> dict:
    return {
        "bundle_version": "1.0",
        "bundle_id": "bundle:atomic",
        "title": "Atomic prototype bundle",
        "records": [
            {
                "record_type": "source",
                "id": "src:atomic",
                "kind": "repository",
                "origin": {"provider": "github", "repository": "example/atomic"},
                "acquisition": {"level": "snapshot"},
                "license": {"state": "KNOWN", "declared_expression": "MIT"},
            },
            {
                "record_type": "source_snapshot",
                "id": "ss:atomic",
                "source_id": "src:atomic",
                "revision": "0123456789abcdef",
                "captured_at": "2026-09-09T00:00:00Z",
            },
            {
                "record_type": "knowledge_entity",
                "id": "ke:atomic",
                "canonical_name": "Atomic Test Technique",
                "aliases": [],
                "kinds": ["technique"],
                "abstraction_level": "L1",
                "identity_state": entity_state,
                "relations": [],
            },
            {
                "record_type": "evidence",
                "id": "ev:atomic",
                "source_id": "src:atomic",
                "source_snapshot_id": "ss:atomic",
                "locator": {
                    "type": "source_lines",
                    "path": "src/a.py",
                    "line_start": 1,
                    "line_end": 2,
                    "content_hash": "sha256:atomic",
                },
                "roles": ["SUPPORTS"],
            },
            {
                "record_type": "claim",
                "id": "cl:atomic",
                "entity_id": "ke:atomic",
                "claim_type": "DIRECT_OBSERVATION",
                "statement": "The pinned source contains a test path.",
                "maturity": "CANDIDATE",
                "evidence_ids": ["ev:atomic"],
                "created_by": claim_creator,
                "policy_version": "1.0.0",
            },
        ],
    }


@pytest.fixture
def repository() -> PostgresRepository:
    assert DSN is not None
    connection = psycopg.connect(DSN, autocommit=True)
    apply_foundation_migration(connection)
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


def test_outer_transaction_rolls_back_partial_bundle_on_governance_failure(
    repository: PostgresRepository,
):
    engine = CurationEngine(repository)

    with pytest.raises(CurationError, match="cannot start as MERGED"):
        with repository.connection.transaction():
            ingest_bundle(
                engine,
                _bundle(claim_creator=AI, entity_state="MERGED"),
                actor=HUMAN,
            )

    assert repository.get("src:atomic") is None
    assert repository.get("ss:atomic") is None
    assert repository.get("ke:atomic") is None
    assert repository.get("ev:atomic") is None
    assert repository.get("cl:atomic") is None


def test_outer_transaction_commits_ai_candidate_without_rewriting_creator(
    repository: PostgresRepository,
):
    engine = CurationEngine(repository)

    with repository.connection.transaction():
        stored = ingest_bundle(engine, _bundle(claim_creator=AI), actor=HUMAN)

    assert len(stored) == 5
    claim = repository.get("cl:atomic")
    assert claim is not None
    assert claim["created_by"] == AI
    assert claim["maturity"] == "CANDIDATE"


def test_real_incremental_computation_pilot_round_trips_through_postgres(
    repository: PostgresRepository,
):
    pilot = json.loads(
        Path("pilots/incremental-computation-v1.json").read_text(encoding="utf-8")
    )
    engine = CurationEngine(repository)

    with repository.connection.transaction():
        stored = ingest_bundle(engine, pilot, actor=PILOT_REVIEWER)

    assert len(stored) == 18
    assert len(repository.list("source")) == 3
    assert len(repository.list("source_snapshot")) == 3
    assert len(repository.list("evidence")) == 5
    assert len(repository.list("knowledge_entity")) == 3

    claims = repository.list("claim")
    assert len(claims) == 4
    assert {claim["maturity"] for claim in claims} == {"CANDIDATE"}
    assert {claim["created_by"]["actor_type"] for claim in claims} == {"ai"}
    assert repository.get("cl:rust-analyzer:salsa-hir-database:33a84d20") is not None
