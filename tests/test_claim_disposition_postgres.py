from __future__ import annotations

import os

import psycopg
import pytest

from kneekura_tech_hub.claim_disposition import ClaimDispositionError, dispose_claim
from kneekura_tech_hub.claim_disposition_postgres import ClaimDispositionPostgresRepository
from kneekura_tech_hub.database import apply_migrations
from kneekura_tech_hub.service import CurationEngine


DSN = os.getenv("KTHUB_TEST_DATABASE_URL")
pytestmark = pytest.mark.skipif(not DSN, reason="KTHUB_TEST_DATABASE_URL is not set")
HUMAN = {"actor_type": "human", "actor_id": "disposition-reviewer"}
AI = {"actor_type": "ai", "actor_id": "disposition-model", "version": "v1"}
SOURCE_ID = "src:disposition:postgres"
SNAPSHOT_ID = "ss:disposition:postgres"
EVIDENCE_ID = "ev:disposition:postgres"
ENTITY_ID = "ke:disposition:postgres"
CLAIM_ID = "cl:disposition:postgres"
SUCCESSOR_ID = "cl:disposition:successor"


def _truncate(connection) -> None:
    connection.execute(
        """
        TRUNCATE TABLE
            claim_disposition_decision,
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


def _seed(repository: ClaimDispositionPostgresRepository, *, claim_id: str = CLAIM_ID):
    engine = CurationEngine(repository)
    if repository.get(SOURCE_ID) is None:
        engine.register_source(
            {
                "record_type": "source",
                "id": SOURCE_ID,
                "kind": "repository",
                "origin": {"provider": "fixture", "repository": "example/disposition"},
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
                    "content_hash": "sha256:" + "d" * 64,
                },
                "roles": ["SUPPORTS"],
            },
            actor=HUMAN,
        )
        engine.create_entity(
            {
                "record_type": "knowledge_entity",
                "id": ENTITY_ID,
                "canonical_name": "Disposition gate fixture",
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
            "id": claim_id,
            "entity_id": ENTITY_ID,
            "claim_type": "INFERENCE",
            "statement": f"Disposition fixture statement {claim_id}.",
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


def _support(repository, claim_id=CLAIM_ID):
    engine = CurationEngine(repository)
    return engine.transition_claim(
        claim_id,
        "SUPPORTED",
        actor=HUMAN,
        reason="support review",
        support_review={
            "decision_id": f"csd:{claim_id}:support",
            "competition_note": "Any active exact-subject competitors were explicitly reviewed.",
        },
    )


def _validate(repository, claim_id=CLAIM_ID):
    engine = CurationEngine(repository)
    return engine.transition_claim(
        claim_id,
        "VALIDATED",
        actor=HUMAN,
        reason="validation review",
        validation_review={
            "decision_id": f"cvd:{claim_id}:validate",
            "validation_basis": "EVIDENCE_REVIEW",
            "validation_note": "Reviewed the pinned fixture evidence.",
        },
    )


@pytest.fixture()
def repository():
    assert DSN is not None
    with psycopg.connect(DSN, autocommit=True) as setup:
        apply_migrations(setup)
        _truncate(setup)
    repo = ClaimDispositionPostgresRepository.connect(DSN)
    try:
        yield repo
    finally:
        repo.close()


def test_candidate_rejection_remains_available_to_ai_cleanup(repository) -> None:
    engine = _seed(repository)
    rejected = engine.transition_claim(CLAIM_ID, "REJECTED", actor=AI, reason="discard weak candidate")
    assert rejected["maturity"] == "REJECTED"
    assert repository.list("claim_disposition_decision") == []


def test_direct_supported_rejection_without_disposition_is_rejected_by_database(repository) -> None:
    _seed(repository)
    _support(repository)
    bypass = repository.get(CLAIM_ID)
    assert bypass is not None
    bypass["maturity"] = "REJECTED"
    with pytest.raises(psycopg.Error, match="requires matching human disposition decision"):
        repository.put(bypass, replace=True)
    assert repository.get(CLAIM_ID)["maturity"] == "SUPPORTED"


def test_ai_cannot_dispose_human_reviewed_claim(repository) -> None:
    _seed(repository)
    _support(repository)
    before = repository.list()
    with pytest.raises(ClaimDispositionError, match="human reviewer"):
        dispose_claim(
            repository,
            CLAIM_ID,
            "REJECTED",
            actor=AI,
            reason="model wants terminal rejection",
        )
    assert repository.list() == before


def test_human_rejection_writes_decision_claim_and_event_atomically(repository) -> None:
    _seed(repository)
    _support(repository)
    result = dispose_claim(
        repository,
        CLAIM_ID,
        "REJECTED",
        actor=HUMAN,
        reason="human reviewed the supported Claim and rejects it",
        decision_id="cdd:reject",
    )
    assert result["claim"]["maturity"] == "REJECTED"
    assert result["decision"]["from_maturity"] == "SUPPORTED"
    assert result["decision"]["to_maturity"] == "REJECTED"
    assert repository.get("cdd:reject") == result["decision"]
    assert any(
        event["operation"] == "CLAIM_REJECT" and CLAIM_ID in event["subject_ids"]
        for event in repository.list("curation_event")
    )


def test_ai_can_challenge_validated_but_cannot_terminally_reject_afterward(repository) -> None:
    engine = _seed(repository)
    _support(repository)
    _validate(repository)
    challenged = engine.transition_claim(CLAIM_ID, "CHALLENGED", actor=AI, reason="new warning")
    assert challenged["maturity"] == "CHALLENGED"

    with pytest.raises(ClaimDispositionError, match="human reviewer"):
        dispose_claim(
            repository,
            CLAIM_ID,
            "REJECTED",
            actor=AI,
            reason="model tries terminal rejection",
        )
    assert repository.get(CLAIM_ID)["maturity"] == "CHALLENGED"


def test_human_supersession_requires_supported_same_subject_successor(repository) -> None:
    _seed(repository)
    _support(repository)
    _validate(repository)
    _seed(repository, claim_id=SUCCESSOR_ID)
    _support(repository, claim_id=SUCCESSOR_ID)

    result = dispose_claim(
        repository,
        CLAIM_ID,
        "SUPERSEDED",
        actor=HUMAN,
        reason="newer reviewed Claim replaces the validated Claim",
        successor_claim_id=SUCCESSOR_ID,
        competition_note="The active successor was reviewed as the intended replacement.",
        decision_id="cdd:supersede",
    )
    assert result["claim"]["maturity"] == "SUPERSEDED"
    assert result["claim"]["superseded_by"] == SUCCESSOR_ID
    assert result["decision"]["successor_claim_id"] == SUCCESSOR_ID


def test_disposition_transaction_rolls_back_on_late_event_failure(repository, monkeypatch) -> None:
    _seed(repository)
    _support(repository)
    original_put = repository.put

    def failing_put(record, *, replace=False):
        if record.get("record_type") == "curation_event" and record.get("operation") == "CLAIM_REJECT":
            raise RuntimeError("synthetic disposition event failure")
        return original_put(record, replace=replace)

    monkeypatch.setattr(repository, "put", failing_put)
    with pytest.raises(RuntimeError, match="synthetic disposition event failure"):
        dispose_claim(
            repository,
            CLAIM_ID,
            "REJECTED",
            actor=HUMAN,
            reason="reviewed terminal disposition",
            decision_id="cdd:rollback",
        )
    monkeypatch.setattr(repository, "put", original_put)

    assert repository.get(CLAIM_ID)["maturity"] == "SUPPORTED"
    assert repository.get("cdd:rollback") is None
