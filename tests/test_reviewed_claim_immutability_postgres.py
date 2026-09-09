from __future__ import annotations

import os

import psycopg
import pytest

from kneekura_tech_hub.claim_disposition_postgres import ClaimDispositionPostgresRepository
from kneekura_tech_hub.database import apply_migrations
from kneekura_tech_hub.service import CurationEngine


DSN = os.getenv("KTHUB_TEST_DATABASE_URL")
pytestmark = pytest.mark.skipif(not DSN, reason="KTHUB_TEST_DATABASE_URL is not set")
HUMAN = {"actor_type": "human", "actor_id": "immutability-reviewer"}
AI = {"actor_type": "ai", "actor_id": "immutability-model", "version": "v1"}
SOURCE_ID = "src:immutability:postgres"
SNAPSHOT_ID = "ss:immutability:postgres"
EVIDENCE_ID = "ev:immutability:postgres"
SECOND_EVIDENCE_ID = "ev:immutability:postgres:second"
ENTITY_ID = "ke:immutability:postgres"
CLAIM_ID = "cl:immutability:postgres"


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


def _seed(repository: ClaimDispositionPostgresRepository) -> CurationEngine:
    engine = CurationEngine(repository)
    engine.register_source(
        {
            "record_type": "source",
            "id": SOURCE_ID,
            "kind": "repository",
            "origin": {"provider": "fixture", "repository": "example/immutability-postgres"},
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
    for evidence_id, line_start in ((EVIDENCE_ID, 1), (SECOND_EVIDENCE_ID, 3)):
        engine.register_evidence(
            {
                "record_type": "evidence",
                "id": evidence_id,
                "source_id": SOURCE_ID,
                "source_snapshot_id": SNAPSHOT_ID,
                "locator": {
                    "type": "source_lines",
                    "path": "README.md",
                    "line_start": line_start,
                    "line_end": line_start + 1,
                    "content_hash": "sha256:" + ("c" if line_start == 1 else "d") * 64,
                },
                "roles": ["SUPPORTS"],
            },
            actor=HUMAN,
        )
    engine.create_entity(
        {
            "record_type": "knowledge_entity",
            "id": ENTITY_ID,
            "canonical_name": "PostgreSQL reviewed Claim immutability fixture",
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
            "statement": "Original PostgreSQL candidate statement.",
            "maturity": "CANDIDATE",
            "evidence_ids": [EVIDENCE_ID],
            "confidence": "MEDIUM",
            "reasoning_basis": [EVIDENCE_ID],
            "created_by": AI,
            "policy_version": "1.0.0",
        },
        actor=AI,
        reason="fixture candidate",
    )
    return engine


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


def test_postgres_candidate_content_and_evidence_remain_editable(repository) -> None:
    _seed(repository)
    claim = repository.get(CLAIM_ID)
    assert claim is not None
    claim["statement"] = "Revised while still Candidate."
    claim["evidence_ids"] = [EVIDENCE_ID, SECOND_EVIDENCE_ID]
    claim["reasoning_basis"] = [EVIDENCE_ID, SECOND_EVIDENCE_ID]

    repository.put(claim, replace=True)

    stored = repository.get(CLAIM_ID)
    assert stored["statement"] == "Revised while still Candidate."
    assert stored["evidence_ids"] == [EVIDENCE_ID, SECOND_EVIDENCE_ID]


def test_postgres_reviewed_statement_swap_is_rejected_and_rolled_back(repository) -> None:
    engine = _seed(repository)
    engine.transition_claim(CLAIM_ID, "SUPPORTED", actor=HUMAN, reason="reviewed")

    claim = repository.get(CLAIM_ID)
    assert claim is not None
    claim["statement"] = "Swap the reviewed statement without changing maturity."

    with pytest.raises(psycopg.Error, match="epistemic content is immutable"):
        repository.put(claim, replace=True)

    stored = repository.get(CLAIM_ID)
    assert stored["maturity"] == "SUPPORTED"
    assert stored["statement"] == "Original PostgreSQL candidate statement."


def test_postgres_reviewed_evidence_swap_is_rejected_and_rolled_back(repository) -> None:
    engine = _seed(repository)
    engine.transition_claim(CLAIM_ID, "SUPPORTED", actor=HUMAN, reason="reviewed")

    claim = repository.get(CLAIM_ID)
    assert claim is not None
    claim["evidence_ids"] = [EVIDENCE_ID, SECOND_EVIDENCE_ID]
    claim["reasoning_basis"] = [EVIDENCE_ID]

    with pytest.raises(psycopg.Error, match="Evidence set differs from latest support decision"):
        repository.put(claim, replace=True)

    stored = repository.get(CLAIM_ID)
    assert stored["evidence_ids"] == [EVIDENCE_ID]
    assert stored["reasoning_basis"] == [EVIDENCE_ID]


def test_postgres_created_by_is_immutable_even_for_candidate(repository) -> None:
    _seed(repository)
    claim = repository.get(CLAIM_ID)
    assert claim is not None
    claim["created_by"] = HUMAN

    with pytest.raises(psycopg.Error, match="created_by is immutable"):
        repository.put(claim, replace=True)

    assert repository.get(CLAIM_ID)["created_by"] == AI


def test_postgres_content_cannot_change_while_leaving_candidate(repository) -> None:
    _seed(repository)
    with pytest.raises(psycopg.Error, match="epistemic content is immutable"):
        repository.connection.execute(
            "UPDATE claim SET statement=%s, maturity='SUPPORTED' WHERE id=%s",
            ("Changed during promotion.", CLAIM_ID),
        )

    stored = repository.get(CLAIM_ID)
    assert stored["maturity"] == "CANDIDATE"
    assert stored["statement"] == "Original PostgreSQL candidate statement."


def test_postgres_normal_review_lifecycle_still_works(repository) -> None:
    engine = _seed(repository)
    supported = engine.transition_claim(CLAIM_ID, "SUPPORTED", actor=HUMAN, reason="reviewed")
    validated = engine.transition_claim(
        CLAIM_ID,
        "VALIDATED",
        actor=HUMAN,
        reason="validated",
        validation_review={
            "validation_basis": "EVIDENCE_REVIEW",
            "validation_note": "Validated the immutable reviewed payload.",
        },
    )
    challenged = engine.transition_claim(CLAIM_ID, "CHALLENGED", actor=AI, reason="new warning")

    assert supported["maturity"] == "SUPPORTED"
    assert validated["maturity"] == "VALIDATED"
    assert challenged["maturity"] == "CHALLENGED"
    assert challenged["statement"] == "Original PostgreSQL candidate statement."
    assert challenged["evidence_ids"] == [EVIDENCE_ID]
