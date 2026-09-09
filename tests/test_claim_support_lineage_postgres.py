from __future__ import annotations

import os

import psycopg
import pytest

from kneekura_tech_hub.claim_resupport import ClaimResupportError, promote_challenged_to_supported
from kneekura_tech_hub.claim_support import claim_support_history, promote_candidate_to_supported
from kneekura_tech_hub.claim_support_postgres import ClaimSupportPostgresRepository
from kneekura_tech_hub.claim_validation import validate_claim
from kneekura_tech_hub.database import apply_migrations
from kneekura_tech_hub.service import CurationEngine


DSN = os.getenv("KTHUB_TEST_DATABASE_URL")
pytestmark = pytest.mark.skipif(not DSN, reason="KTHUB_TEST_DATABASE_URL is not set")
HUMAN = {"actor_type": "human", "actor_id": "lineage-reviewer"}
AI = {"actor_type": "ai", "actor_id": "lineage-model", "version": "v1"}
SOURCE_ID = "src:support-lineage:postgres"
SNAPSHOT_ID = "ss:support-lineage:postgres"
EVIDENCE_ID = "ev:support-lineage:postgres"
ENTITY_ID = "ke:support-lineage:postgres"
CLAIM_ID = "cl:support-lineage:postgres"


def _truncate(connection) -> None:
    connection.execute(
        """
        TRUNCATE TABLE
            claim_validation_decision,
            claim_support_decision,
            observation_triage_decision,
            source_acquisition_commit,
            source_acquisition_execution,
            source_acquisition_authorization,
            source_selection_decision,
            review_decision,
            staged_observation_evidence,
            claim_evidence, claim, evidence_relation, evidence,
            source_snapshot, staged_observation, curation_event,
            entity_relation, entity_kind, entity_alias, knowledge_entity, source
        RESTART IDENTITY CASCADE
        """
    )


def _seed(repository: ClaimSupportPostgresRepository) -> CurationEngine:
    engine = CurationEngine(repository)
    engine.register_source(
        {
            "record_type": "source",
            "id": SOURCE_ID,
            "kind": "repository",
            "origin": {"provider": "fixture", "repository": "example/support-lineage"},
            "acquisition": {"level": "selected-files"},
            "license": {"state": "KNOWN", "declared_expression": "MIT"},
        },
        actor=HUMAN,
    )
    engine.register_source_snapshot(
        {
            "record_type": "source_snapshot",
            "id": SNAPSHOT_ID,
            "source_id": SOURCE_ID,
            "revision": "0123456789abcdef0123456789abcdef01234567",
            "captured_at": "2026-09-09T00:00:00Z",
            "metadata": {"fixture": True},
        },
        actor=HUMAN,
    )
    engine.register_evidence(
        {
            "record_type": "evidence",
            "id": EVIDENCE_ID,
            "source_id": SOURCE_ID,
            "source_snapshot_id": SNAPSHOT_ID,
            "locator": {
                "type": "source_lines",
                "path": "README.md",
                "line_start": 1,
                "line_end": 2,
                "content_hash": "sha256:" + "c" * 64,
            },
            "roles": ["SUPPORTS"],
        },
        actor=HUMAN,
    )
    engine.create_entity(
        {
            "record_type": "knowledge_entity",
            "id": ENTITY_ID,
            "canonical_name": "Support lineage fixture",
            "aliases": [],
            "kinds": ["technique"],
            "abstraction_level": "L1",
            "identity_state": "CANONICAL",
            "relations": [],
        },
        actor=HUMAN,
    )
    engine.create_claim(
        {
            "record_type": "claim",
            "id": CLAIM_ID,
            "entity_id": ENTITY_ID,
            "claim_type": "INFERENCE",
            "statement": "The fixture demonstrates append-only support lineage.",
            "maturity": "CANDIDATE",
            "evidence_ids": [EVIDENCE_ID],
            "confidence": "MEDIUM",
            "reasoning_basis": [EVIDENCE_ID],
            "created_by": HUMAN,
            "policy_version": "1.0.0",
        },
        actor=HUMAN,
        reason="fixture candidate",
    )
    return engine


@pytest.fixture()
def repository():
    assert DSN is not None
    with psycopg.connect(DSN, autocommit=True) as setup:
        apply_migrations(setup)
        _truncate(setup)
    repo = ClaimSupportPostgresRepository.connect(DSN)
    try:
        yield repo
    finally:
        repo.close()


def _support_then_challenge(repository):
    engine = _seed(repository)
    first = promote_candidate_to_supported(
        repository,
        CLAIM_ID,
        actor=HUMAN,
        reason="initial support review",
        independence_assessment="NOT_ASSESSED",
        decision_id="csd:lineage:first",
    )
    engine.transition_claim(CLAIM_ID, "CHALLENGED", actor=AI, reason="new concern")
    return engine, first


def test_resupport_appends_to_same_support_history_and_validation_uses_latest(repository) -> None:
    _engine, first = _support_then_challenge(repository)
    second = promote_challenged_to_supported(
        repository,
        CLAIM_ID,
        actor=HUMAN,
        reason="challenge reviewed and support restored",
        independence_assessment="NOT_ASSESSED",
        decision_id="csd:lineage:second",
    )

    history = claim_support_history(repository, claim_id=CLAIM_ID)
    assert [record["id"] for record in history] == ["csd:lineage:first", "csd:lineage:second"]
    assert [record["from_maturity"] for record in history] == ["CANDIDATE", "CHALLENGED"]
    assert second["claim"]["maturity"] == "SUPPORTED"

    validated = validate_claim(
        repository,
        CLAIM_ID,
        actor=HUMAN,
        reason="validated after fresh resupport",
        validation_basis="EVIDENCE_REVIEW",
        validation_note="Reviewed the pinned Evidence after the challenge was resolved.",
        independence_assessment="NOT_ASSESSED",
        decision_id="cvd:lineage:latest-support",
    )
    assert validated["claim"]["maturity"] == "VALIDATED"
    assert validated["decision"]["support_decision_id"] == second["decision"]["id"]
    assert validated["decision"]["support_decision_id"] != first["decision"]["id"]


def test_second_return_to_supported_requires_another_fresh_support_decision(repository) -> None:
    engine, _first = _support_then_challenge(repository)
    promote_challenged_to_supported(
        repository,
        CLAIM_ID,
        actor=HUMAN,
        reason="first challenge resolved",
        independence_assessment="NOT_ASSESSED",
        decision_id="csd:lineage:second",
    )
    engine.transition_claim(CLAIM_ID, "CHALLENGED", actor=AI, reason="another concern")

    bypass = repository.get(CLAIM_ID)
    assert bypass is not None
    bypass["maturity"] = "SUPPORTED"
    with pytest.raises(psycopg.Error, match="requires a fresh claim support decision"):
        repository.put(bypass, replace=True)
    assert repository.get(CLAIM_ID)["maturity"] == "CHALLENGED"
    assert len(claim_support_history(repository, claim_id=CLAIM_ID)) == 2


def test_ai_cannot_resupport_and_writes_nothing(repository) -> None:
    _engine, _first = _support_then_challenge(repository)
    before = repository.list()
    with pytest.raises(ClaimResupportError, match="human reviewer"):
        promote_challenged_to_supported(
            repository,
            CLAIM_ID,
            actor=AI,
            reason="model approves resupport",
            independence_assessment="NOT_ASSESSED",
        )
    assert repository.list() == before
