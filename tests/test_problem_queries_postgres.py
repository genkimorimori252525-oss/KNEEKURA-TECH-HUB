from __future__ import annotations

import json
import os
from pathlib import Path

import psycopg
import pytest

from kneekura_tech_hub.bundle import ingest_bundle
from kneekura_tech_hub.database import apply_migrations
from kneekura_tech_hub.postgres_repository import PostgresRepository
from kneekura_tech_hub.queries import problems_solved_by, requirements_for, solutions_for_problem
from kneekura_tech_hub.service import CurationEngine


DSN = os.getenv("KTHUB_TEST_DATABASE_URL")
pytestmark = pytest.mark.skipif(not DSN, reason="KTHUB_TEST_DATABASE_URL is not set")
HUMAN = {"actor_type": "human", "actor_id": "problem-reviewer"}
ROOT = Path(__file__).resolve().parents[1]
PROBLEM_ID = "ke:problem:repeated-recomputation-after-input-change"
SOLUTION_ID = "ke:query-based-incremental-computation"
MEMOIZATION_ID = "ke:memoization"
SOLVES_CLAIM = "cl:salsa:query-incremental:solves:repeated-recomputation:e021c01d"
REQUIRES_CLAIM = "cl:salsa:query-incremental:requires:memoization:e021c01d"


def _load(name: str) -> dict:
    return json.loads((ROOT / "pilots" / name).read_text(encoding="utf-8"))


def test_real_salsa_problem_and_requirement_queries_follow_claim_maturity():
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
                _load("incremental-computation-problems-v1.json"),
                actor=HUMAN,
            )

        assert solutions_for_problem(repository, PROBLEM_ID, view="validated") == []
        assert problems_solved_by(repository, SOLUTION_ID, view="validated") == []
        assert requirements_for(repository, SOLUTION_ID, view="validated") == []

        research_solutions = solutions_for_problem(repository, PROBLEM_ID, view="research")
        research_problems = problems_solved_by(repository, SOLUTION_ID, view="research")
        research_requirements = requirements_for(repository, SOLUTION_ID, view="research")

        assert [item["solution"]["id"] for item in research_solutions] == [SOLUTION_ID]
        assert [item["problem"]["id"] for item in research_problems] == [PROBLEM_ID]
        assert [item["requirement"]["id"] for item in research_requirements] == [MEMOIZATION_ID]
        assert research_solutions[0]["relation_claim"]["claim_id"] == SOLVES_CLAIM
        assert research_requirements[0]["relation_claim"]["claim_id"] == REQUIRES_CLAIM
        assert research_solutions[0]["relation_claim"]["maturity"] == "CANDIDATE"

        for claim_id in (SOLVES_CLAIM, REQUIRES_CLAIM):
            engine.transition_claim(
                claim_id,
                "SUPPORTED",
                actor=HUMAN,
                reason="problem-oriented pilot reviewed",
            )
            engine.transition_claim(
                claim_id,
                "VALIDATED",
                actor=HUMAN,
                reason="problem-oriented pilot verified",
            )

        trusted_solutions = solutions_for_problem(repository, PROBLEM_ID, view="validated")
        trusted_problems = problems_solved_by(repository, SOLUTION_ID, view="validated")
        trusted_requirements = requirements_for(repository, SOLUTION_ID, view="validated")

        assert [item["solution"]["id"] for item in trusted_solutions] == [SOLUTION_ID]
        assert [item["problem"]["id"] for item in trusted_problems] == [PROBLEM_ID]
        assert [item["requirement"]["id"] for item in trusted_requirements] == [MEMOIZATION_ID]
        assert trusted_solutions[0]["relation_claim"]["maturity"] == "VALIDATED"
        assert trusted_requirements[0]["relation_claim"]["maturity"] == "VALIDATED"
        assert repository.get(SOLUTION_ID)["relations"] == []
        assert repository.get(PROBLEM_ID)["relations"] == []
    finally:
        connection.close()
