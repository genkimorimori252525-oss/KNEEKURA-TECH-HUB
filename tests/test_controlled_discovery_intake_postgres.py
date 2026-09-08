from __future__ import annotations

import json
import os
from pathlib import Path

import psycopg
import pytest

from kneekura_tech_hub.database import apply_migrations
from kneekura_tech_hub.discovery import ingest_discovery_intake
from kneekura_tech_hub.postgres_repository import PostgresRepository
from kneekura_tech_hub.service import CurationEngine


DSN = os.getenv("KTHUB_TEST_DATABASE_URL")
pytestmark = pytest.mark.skipif(not DSN, reason="KTHUB_TEST_DATABASE_URL is not set")
ROOT = Path(__file__).resolve().parents[1]
PILOT = ROOT / "pilots" / "controlled-discovery-intake-v1.json"


def _load() -> dict:
    return json.loads(PILOT.read_text(encoding="utf-8"))


def _truncate(connection) -> None:
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


class FailingEvidenceEngine(CurationEngine):
    def register_evidence(self, evidence, *, actor):
        raise RuntimeError("synthetic evidence write failure")


def test_real_postgres_discovery_intake_never_creates_canonical_knowledge():
    assert DSN is not None
    connection = psycopg.connect(DSN, autocommit=True)
    try:
        apply_migrations(connection)
        _truncate(connection)
        repository = PostgresRepository(connection)
        batch = _load()

        with connection.transaction():
            receipt = ingest_discovery_intake(
                CurationEngine(repository),
                batch,
                actor=batch["discovered_by"],
            )

        assert receipt["canonical_knowledge_writes"] == 0
        assert receipt["counts"] == {
            "evidence": 2,
            "source": 2,
            "source_snapshot": 2,
            "staged_observation": 2,
        }
        assert len(repository.list("source")) == 2
        assert len(repository.list("source_snapshot")) == 2
        assert len(repository.list("evidence")) == 2
        observations = repository.list("staged_observation")
        assert len(observations) == 2
        assert all(item["status"] == "NEW" for item in observations)

        assert repository.list("knowledge_entity") == []
        assert repository.list("claim") == []
        assert repository.list("review_decision") == []

        events = repository.list("curation_event")
        assert len(events) == 6
        assert all(event["operation"] == "SOURCE_ACQUIRE" for event in events)
        assert all(event["actor"] == batch["discovered_by"] for event in events)
        evidence_event_subjects = [
            event["subject_ids"]
            for event in events
            if any(subject_id.startswith("ev:") for subject_id in event["subject_ids"])
        ]
        assert len(evidence_event_subjects) == 2
        assert {
            subject_id
            for subjects in evidence_event_subjects
            for subject_id in subjects
            if subject_id.startswith("ev:")
        } == {
            "ev:discovery:tree-sitter:readme:incremental-parsing:8351896b",
            "ev:discovery:salsa:readme:query-model:e021c01d",
        }
    finally:
        connection.close()


def test_postgres_transaction_rolls_back_partial_discovery_writes():
    assert DSN is not None
    connection = psycopg.connect(DSN, autocommit=True)
    try:
        apply_migrations(connection)
        _truncate(connection)
        repository = PostgresRepository(connection)
        batch = _load()

        with pytest.raises(RuntimeError, match="synthetic evidence write failure"):
            with connection.transaction():
                ingest_discovery_intake(
                    FailingEvidenceEngine(repository),
                    batch,
                    actor=batch["discovered_by"],
                )

        assert repository.list("source") == []
        assert repository.list("source_snapshot") == []
        assert repository.list("evidence") == []
        assert repository.list("staged_observation") == []
        assert repository.list("curation_event") == []
        assert repository.list("knowledge_entity") == []
        assert repository.list("claim") == []
        assert repository.list("review_decision") == []
    finally:
        connection.close()
