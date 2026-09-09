from __future__ import annotations

import os

import psycopg
import pytest

from kneekura_tech_hub.claim_validation_postgres import ClaimValidationPostgresRepository
from kneekura_tech_hub.database import apply_migrations
from kneekura_tech_hub.service import CurationEngine


DSN = os.getenv("KTHUB_TEST_DATABASE_URL")
pytestmark = pytest.mark.skipif(not DSN, reason="KTHUB_TEST_DATABASE_URL is not set")
HUMAN = {"actor_type": "human", "actor_id": "audit-reviewer"}
SOURCE_ID = "src:audit:postgres"
SNAPSHOT_ID = "ss:audit:postgres"
EVIDENCE_ID = "ev:audit:postgres"
ENTITY_ID = "ke:audit:postgres"
CLAIM_A = "cl:audit:a"
CLAIM_B = "cl:audit:b"


@pytest.fixture()
def repository():
    assert DSN is not None
    with psycopg.connect(DSN, autocommit=True) as setup:
        apply_migrations(setup)
        setup.execute(
            "TRUNCATE TABLE source, knowledge_entity, curation_event RESTART IDENTITY CASCADE"
        )
    repo = ClaimValidationPostgresRepository.connect(DSN)
    try:
        yield repo
    finally:
        repo.close()


def _seed_two_candidates(repository: ClaimValidationPostgresRepository) -> CurationEngine:
    engine = CurationEngine(repository)
    engine.register_source(
        {
            "record_type": "source",
            "id": SOURCE_ID,
            "kind": "repository",
            "origin": {"provider": "fixture", "repository": "example/audit"},
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
            "canonical_name": "Audit integrity fixture",
            "aliases": [],
            "kinds": ["technique"],
            "abstraction_level": "L1",
            "identity_state": "CANONICAL",
            "relations": [],
        },
        actor=HUMAN,
    )
    for claim_id, statement in (
        (CLAIM_A, "Primary exact-subject claim."),
        (CLAIM_B, "Competing exact-subject claim."),
    ):
        engine.create_claim(
            {
                "record_type": "claim",
                "id": claim_id,
                "entity_id": ENTITY_ID,
                "claim_type": "INFERENCE",
                "statement": statement,
                "maturity": "CANDIDATE",
                "evidence_ids": [EVIDENCE_ID],
                "confidence": "MEDIUM",
                "reasoning_basis": [EVIDENCE_ID],
                "created_by": HUMAN,
                "policy_version": "1.0.0",
            },
            actor=HUMAN,
            reason="audit fixture",
        )
    return engine


def _forged_support_decision() -> dict:
    return {
        "record_type": "claim_support_decision",
        "id": "csd:audit:forged",
        "claim_id": CLAIM_A,
        "from_maturity": "CANDIDATE",
        "to_maturity": "SUPPORTED",
        "reason": "attempt to hide competition",
        "reviewed_by": HUMAN,
        "evidence_ids": [EVIDENCE_ID],
        "supporting_evidence_ids": [EVIDENCE_ID],
        "refuting_evidence_ids": [],
        "qualifying_evidence_ids": [],
        "distinct_source_ids": [SOURCE_ID],
        "distinct_snapshot_ids": [SNAPSHOT_ID],
        "review_flags": ["SINGLE_SOURCE"],
        "competing_active_claim_ids": [],
        "independence_assessment": "NOT_ASSESSED",
        "policy_version": "1.0.0",
        "decided_at": "2026-09-09T01:00:00Z",
    }


def test_database_rejects_forged_support_competition_snapshot(repository) -> None:
    _seed_two_candidates(repository)

    with pytest.raises(psycopg.Error, match="competing_active_claim_ids"):
        repository.put(_forged_support_decision())

    assert repository.get("csd:audit:forged") is None


def test_database_rejects_forged_validation_competition_snapshot(repository) -> None:
    engine = _seed_two_candidates(repository)
    engine.transition_claim(
        CLAIM_A,
        "SUPPORTED",
        actor=HUMAN,
        reason="reviewed with competitor",
        support_review={"competition_note": "The competing Claim remains active."},
    )
    support_decision = repository.list("claim_support_decision")[0]
    forged = {
        "record_type": "claim_validation_decision",
        "id": "cvd:audit:forged",
        "claim_id": CLAIM_A,
        "support_decision_id": support_decision["id"],
        "from_maturity": "SUPPORTED",
        "to_maturity": "VALIDATED",
        "reason": "attempt to hide competition",
        "validated_by": HUMAN,
        "validation_basis": "EVIDENCE_REVIEW",
        "validation_note": "Pretend review.",
        "evidence_ids": [EVIDENCE_ID],
        "supporting_evidence_ids": [EVIDENCE_ID],
        "refuting_evidence_ids": [],
        "qualifying_evidence_ids": [],
        "distinct_source_ids": [SOURCE_ID],
        "distinct_snapshot_ids": [SNAPSHOT_ID],
        "review_flags": ["SINGLE_SOURCE"],
        "competing_active_claim_ids": [],
        "independence_assessment": "NOT_ASSESSED",
        "policy_version": "1.0.0",
        "validated_at": "2026-09-09T02:00:00Z",
    }

    with pytest.raises(psycopg.Error, match="competing_active_claim_ids"):
        repository.put(forged)

    assert repository.get("cvd:audit:forged") is None


def test_support_and_validation_decisions_are_database_append_only(repository) -> None:
    engine = _seed_two_candidates(repository)
    engine.transition_claim(
        CLAIM_A,
        "SUPPORTED",
        actor=HUMAN,
        reason="reviewed with competitor",
        support_review={"competition_note": "The competing Claim remains active."},
    )
    support_decision = repository.list("claim_support_decision")[0]

    with pytest.raises(psycopg.Error, match="append-only"):
        repository.connection.execute(
            "UPDATE claim_support_decision SET reason='tampered' WHERE id=%s",
            (support_decision["id"],),
        )
    with pytest.raises(psycopg.Error, match="append-only"):
        repository.connection.execute(
            "DELETE FROM claim_support_decision WHERE id=%s",
            (support_decision["id"],),
        )

    engine.transition_claim(
        CLAIM_A,
        "VALIDATED",
        actor=HUMAN,
        reason="validated with competitor",
        validation_review={
            "validation_basis": "EVIDENCE_REVIEW",
            "validation_note": "Reviewed the pinned Evidence and active competing Claim.",
            "competition_note": "The competing Claim remains visible and unresolved.",
        },
    )
    validation_decision = repository.list("claim_validation_decision")[0]

    with pytest.raises(psycopg.Error, match="append-only"):
        repository.connection.execute(
            "UPDATE claim_validation_decision SET validation_note='tampered' WHERE id=%s",
            (validation_decision["id"],),
        )
    with pytest.raises(psycopg.Error, match="append-only"):
        repository.connection.execute(
            "DELETE FROM claim_validation_decision WHERE id=%s",
            (validation_decision["id"],),
        )

    assert repository.get(support_decision["id"]) == support_decision
    assert repository.get(validation_decision["id"]) == validation_decision
