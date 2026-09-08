from __future__ import annotations

import json
import os
from pathlib import Path

import psycopg
import pytest

from kneekura_tech_hub.bundle import ingest_bundle
from kneekura_tech_hub.comparison import compare_claim
from kneekura_tech_hub.database import apply_migrations
from kneekura_tech_hub.postgres_repository import PostgresRepository
from kneekura_tech_hub.service import CurationEngine


DSN = os.getenv("KTHUB_TEST_DATABASE_URL")
pytestmark = pytest.mark.skipif(not DSN, reason="KTHUB_TEST_DATABASE_URL is not set")
ROOT = Path(__file__).resolve().parents[1]
HUMAN = {"actor_type": "human", "actor_id": "comparison-reviewer"}
AI = {"actor_type": "ai", "actor_id": "comparison-extractor", "version": "test"}
ORIGINAL = "cl:salsa:query-incremental:solves:repeated-recomputation:e021c01d"
SECOND = "cl:salsa:query-incremental:solves:repeated-recomputation:alternative"


def _load(name: str) -> dict:
    return json.loads((ROOT / "pilots" / name).read_text(encoding="utf-8"))


def test_real_salsa_competing_claims_are_exposed_without_automatic_winner():
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

        engine.create_claim(
            {
                "record_type": "claim",
                "id": SECOND,
                "relation": {
                    "source_entity_id": "ke:query-based-incremental-computation",
                    "relation_type": "solves",
                    "target_entity_id": "ke:problem:repeated-recomputation-after-input-change",
                },
                "claim_type": "INFERENCE",
                "statement": (
                    "The query model may mitigate repeated recomputation when dependencies "
                    "are tracked and invalidated correctly."
                ),
                "maturity": "CANDIDATE",
                "evidence_ids": ["ev:salsa:readme:query-model:e021c01d"],
                "confidence": "MEDIUM",
                "reasoning_basis": ["ev:salsa:readme:query-model:e021c01d"],
                "alternative_interpretations": [
                    "The benefit may depend on the workload and invalidation granularity."
                ],
                "created_by": AI,
                "policy_version": "1.0.0",
            },
            actor=AI,
            reason="comparison acceptance candidate",
        )

        before = repository.list()
        group = compare_claim(repository, ORIGINAL)

        assert group["claim_count"] == 2
        assert group["active_claim_count"] == 2
        assert group["active_claim_ids"] == sorted([ORIGINAL, SECOND])
        assert group["subject"] == {
            "kind": "relation",
            "source_entity_id": "ke:query-based-incremental-computation",
            "relation_type": "solves",
            "target_entity_id": "ke:problem:repeated-recomputation-after-input-change",
        }
        assert "MULTIPLE_ACTIVE_CLAIMS" in group["flags"]
        assert "STATEMENTS_DIFFER" in group["flags"]
        assert "HAS_CANDIDATE_CLAIM" in group["flags"]
        assert group["needs_review"] is True
        assert all("CONTRADICTION" not in flag for flag in group["flags"])
        assert "winner" not in group
        assert "preferred_claim_id" not in group

        by_id = {item["claim"]["id"]: item for item in group["claims"]}
        assert by_id[ORIGINAL]["review"]["evidence"]["count"] == 2
        assert by_id[SECOND]["review"]["evidence"]["count"] == 1
        assert repository.list() == before
    finally:
        connection.close()
