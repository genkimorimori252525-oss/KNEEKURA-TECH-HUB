from __future__ import annotations

import json
import os
from pathlib import Path

import psycopg
import pytest

from kneekura_tech_hub.bundle import ingest_bundle
from kneekura_tech_hub.database import apply_migrations
from kneekura_tech_hub.explanation import explain_claim, explain_relation_result
from kneekura_tech_hub.postgres_repository import PostgresRepository
from kneekura_tech_hub.queries import solutions_for_problem
from kneekura_tech_hub.service import CurationEngine


DSN = os.getenv("KTHUB_TEST_DATABASE_URL")
pytestmark = pytest.mark.skipif(not DSN, reason="KTHUB_TEST_DATABASE_URL is not set")
ROOT = Path(__file__).resolve().parents[1]
HUMAN = {"actor_type": "human", "actor_id": "explanation-reviewer"}
PROBLEM_ID = "ke:problem:repeated-recomputation-after-input-change"
SOLVES_CLAIM = "cl:salsa:query-incremental:solves:repeated-recomputation:e021c01d"
SALSA_SOURCE = "src:github:salsa-rs:salsa"
SALSA_SNAPSHOT = "ss:github:salsa-rs:salsa:e021c01d"
SALSA_REVISION = "e021c01d4939408c89c9325ad2426660117a8b32"


def _load(name: str) -> dict:
    return json.loads((ROOT / "pilots" / name).read_text(encoding="utf-8"))


def test_real_salsa_problem_result_explains_to_pinned_source_revision():
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

        result = solutions_for_problem(repository, PROBLEM_ID, view="research")[0]
        explanation = explain_relation_result(repository, result)

        assert explanation["claim"]["id"] == SOLVES_CLAIM
        assert explanation["evidence_count"] == 2
        assert [chain["evidence"]["id"] for chain in explanation["evidence_chains"]] == [
            "ev:salsa:readme:incrementalized-computation:e021c01d",
            "ev:salsa:readme:query-model:e021c01d",
        ]
        for chain in explanation["evidence_chains"]:
            assert chain["source"]["id"] == SALSA_SOURCE
            assert chain["source_snapshot"]["id"] == SALSA_SNAPSHOT
            assert chain["source_snapshot"]["revision"] == SALSA_REVISION
            assert chain["evidence"]["source_id"] == SALSA_SOURCE
            assert chain["evidence"]["source_snapshot_id"] == SALSA_SNAPSHOT

        direct = explain_claim(repository, SOLVES_CLAIM)
        assert direct == explanation
        assert repository.get(SOLVES_CLAIM)["maturity"] == "CANDIDATE"
    finally:
        connection.close()
