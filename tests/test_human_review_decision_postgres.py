from __future__ import annotations

import json
import os
from copy import deepcopy
from pathlib import Path

import psycopg
import pytest

from kneekura_tech_hub.bundle import ingest_bundle
from kneekura_tech_hub.database import apply_migrations
from kneekura_tech_hub.decision import (
    HumanReviewDecisionEngine,
    active_review_decisions,
    decision_context_for_claim,
    review_decision_history,
)
from kneekura_tech_hub.postgres_repository import PostgresRepository
from kneekura_tech_hub.service import CurationEngine


DSN = os.getenv("KTHUB_TEST_DATABASE_URL")
pytestmark = pytest.mark.skipif(not DSN, reason="KTHUB_TEST_DATABASE_URL is not set")
ROOT = Path(__file__).resolve().parents[1]
HUMAN = {"actor_type": "human", "actor_id": "decision-reviewer"}
AI = {"actor_type": "ai", "actor_id": "decision-extractor", "version": "test"}
ORIGINAL = "cl:salsa:query-incremental:solves:repeated-recomputation:e021c01d"
SECOND = "cl:salsa:query-incremental:solves:repeated-recomputation:decision-alternative"


def _load(name: str) -> dict:
    return json.loads((ROOT / "pilots" / name).read_text(encoding="utf-8"))


def test_real_salsa_human_decision_is_separate_append_only_governance_record():
    assert DSN is not None
    connection = psycopg.connect(DSN, autocommit=True)
    try:
        apply_migrations(connection)
        connection.execute(
            """
            TRUNCATE TABLE
                review_decision,
                staged_observation_evidence,
                claim_evidence, claim, evidence_relation, evidence,
                source_snapshot, staged_observation, curation_event,
                entity_relation, entity_kind, entity_alias, knowledge_entity, source
            RESTART IDENTITY CASCADE
            """
        )
        repository = PostgresRepository(connection)
        curation = CurationEngine(repository)

        with connection.transaction():
            ingest_bundle(curation, _load("incremental-computation-v1.json"), actor=HUMAN)
            ingest_bundle(curation, _load("incremental-computation-problems-v1.json"), actor=HUMAN)

        curation.create_claim(
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
                    "The query model may mitigate repeated recomputation when dependency "
                    "tracking and invalidation granularity fit the workload."
                ),
                "maturity": "CANDIDATE",
                "evidence_ids": ["ev:salsa:readme:query-model:e021c01d"],
                "confidence": "MEDIUM",
                "reasoning_basis": ["ev:salsa:readme:query-model:e021c01d"],
                "alternative_interpretations": [
                    "The observed benefit may not generalize to every workload."
                ],
                "created_by": AI,
                "policy_version": "1.0.0",
            },
            actor=AI,
            reason="human decision acceptance comparison candidate",
        )

        claims_before = {
            ORIGINAL: deepcopy(repository.get(ORIGINAL)),
            SECOND: deepcopy(repository.get(SECOND)),
        }

        decisions = HumanReviewDecisionEngine(repository)
        first = decisions.create_from_fields(
            decision_id="rd:salsa:unresolved",
            source_claim_id=ORIGINAL,
            target_claim_id=SECOND,
            decision="UNRESOLVED",
            rationale=(
                "Both Claims concern the same solves relation, but statement difference alone "
                "does not establish contradiction."
            ),
            actor=HUMAN,
        )

        assert repository.get(first["id"]) == first
        assert repository.get(ORIGINAL) == claims_before[ORIGINAL]
        assert repository.get(SECOND) == claims_before[SECOND]

        context = decision_context_for_claim(repository, ORIGINAL)
        assert context["comparison"]["claim_count"] == 2
        assert context["active_decision_count"] == 1
        assert context["active_decisions"][0]["decision"] == "UNRESOLVED"
        assert "winner" not in context["comparison"]

        second = decisions.create_from_fields(
            decision_id="rd:salsa:compatible",
            source_claim_id=SECOND,
            target_claim_id=ORIGINAL,
            decision="COMPATIBLE",
            rationale=(
                "After human scope review, the conditional Claim is compatible with the broader "
                "Claim rather than a contradiction."
            ),
            actor=HUMAN,
            supersedes_decision_id=first["id"],
        )

        assert repository.get(first["id"]) == first
        assert repository.get(second["id"]) == second
        assert [item["id"] for item in review_decision_history(repository)] == [
            first["id"],
            second["id"],
        ]
        assert [item["id"] for item in active_review_decisions(repository)] == [second["id"]]
        assert repository.get(ORIGINAL) == claims_before[ORIGINAL]
        assert repository.get(SECOND) == claims_before[SECOND]
    finally:
        connection.close()
