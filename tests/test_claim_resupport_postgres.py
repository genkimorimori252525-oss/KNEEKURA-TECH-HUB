from __future__ import annotations

import os

import psycopg
import pytest

from kneekura_tech_hub.claim_resupport_postgres import ClaimResupportPostgresRepository
from kneekura_tech_hub.database import apply_migrations
from kneekura_tech_hub.service import CurationEngine, CurationError


DSN = os.getenv("KTHUB_TEST_DATABASE_URL")
pytestmark = pytest.mark.skipif(not DSN, reason="KTHUB_TEST_DATABASE_URL is not set")
HUMAN = {"actor_type": "human", "actor_id": "resupport-reviewer"}
AI = {"actor_type": "ai", "actor_id": "resupport-model", "version": "test"}
SOURCE_ID = "src:resupport:postgres"
SNAPSHOT_ID = "ss:resupport:postgres"
EVIDENCE_ID = "ev:resupport:postgres"
ENTITY_ID = "ke:resupport:postgres"
CLAIM_ID = "cl:resupport:postgres"


@pytest.fixture()
def repository():
    assert DSN is not None
    with psycopg.connect(DSN, autocommit=True) as setup:
        apply_migrations(setup)
        setup.execute(
            "TRUNCATE TABLE source, knowledge_entity, curation_event RESTART IDENTITY CASCADE"
        )
    repo = ClaimResupportPostgresRepository.connect(DSN)
    try:
        yield repo
    finally:
        repo.close()


def _seed(repository: ClaimResupportPostgresRepository) -> CurationEngine:
    engine = CurationEngine(repository)
    engine.register_source(
        {
            "record_type": "source",
            "id": SOURCE_ID,
            "kind": "repository",
            "origin": {"provider": "fixture", "repository": "example/resupport"},
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
            "canonical_name": "Resupport fixture",
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
            "statement": "The fixture remains supportable after a challenge is reviewed.",
            "maturity": "CANDIDATE",
            "evidence_ids": [EVIDENCE_ID],
            "confidence": "MEDIUM",
            "reasoning_basis": [EVIDENCE_ID],
            "created_by": HUMAN,
            "policy_version": "1.0.0",
        },
        actor=HUMAN,
        reason="resupport fixture",
    )
    return engine


def _support_then_challenge(engine: CurationEngine) -> None:
    engine.transition_claim(CLAIM_ID, "SUPPORTED", actor=HUMAN, reason="initial human support")
    engine.transition_claim(CLAIM_ID, "CHALLENGED", actor=HUMAN, reason="new concern")


def test_human_resupport_creates_fresh_append_only_decision(repository) -> None:
    engine = _seed(repository)
    _support_then_challenge(engine)

    restored = engine.transition_claim(
        CLAIM_ID,
        "SUPPORTED",
        actor=HUMAN,
        reason="challenge reviewed against pinned evidence",
    )

    assert restored["maturity"] == "SUPPORTED"
    support = repository.list("claim_support_decision")
    resupport = repository.list("claim_resupport_decision")
    assert len(support) == 1
    assert len(resupport) == 1
    assert resupport[0]["initial_support_decision_id"] == support[0]["id"]
    row = repository.connection.execute(
        "SELECT pending_support_reviewed_at, last_support_reviewed_at FROM claim WHERE id=%s",
        (CLAIM_ID,),
    ).fetchone()
    assert row[0] is None
    assert row[1].isoformat() == resupport[0]["decided_at"]


def test_ai_cannot_restore_challenged_claim_to_supported(repository) -> None:
    engine = _seed(repository)
    _support_then_challenge(engine)

    with pytest.raises(CurationError, match="human reviewer"):
        engine.transition_claim(
            CLAIM_ID,
            "SUPPORTED",
            actor=AI,
            reason="model says challenge is resolved",
        )

    assert repository.get(CLAIM_ID)["maturity"] == "CHALLENGED"
    assert repository.list("claim_resupport_decision") == []


def test_direct_sql_resupport_without_fresh_decision_is_rejected(repository) -> None:
    engine = _seed(repository)
    _support_then_challenge(engine)

    with pytest.raises(psycopg.Error, match="fresh armed support review decision"):
        with repository.connection.transaction():
            repository.connection.execute(
                "UPDATE claim SET maturity='SUPPORTED' WHERE id=%s",
                (CLAIM_ID,),
            )

    assert repository.get(CLAIM_ID)["maturity"] == "CHALLENGED"


def test_old_resupport_decision_cannot_be_reused_after_second_challenge(repository) -> None:
    engine = _seed(repository)
    _support_then_challenge(engine)
    engine.transition_claim(
        CLAIM_ID,
        "SUPPORTED",
        actor=HUMAN,
        reason="first challenge reviewed",
    )
    old_decision = repository.list("claim_resupport_decision")[0]
    engine.transition_claim(CLAIM_ID, "CHALLENGED", actor=HUMAN, reason="second concern")

    with pytest.raises(psycopg.Error, match="cannot be reused"):
        repository.connection.execute(
            "UPDATE claim SET pending_support_reviewed_at=%s WHERE id=%s",
            (old_decision["decided_at"], CLAIM_ID),
        )

    restored = engine.transition_claim(
        CLAIM_ID,
        "SUPPORTED",
        actor=HUMAN,
        reason="second challenge independently reviewed",
    )
    decisions = repository.list("claim_resupport_decision")
    assert restored["maturity"] == "SUPPORTED"
    assert len(decisions) == 2
    assert decisions[0]["decided_at"] != decisions[1]["decided_at"]


def test_resupport_decision_is_database_append_only(repository) -> None:
    engine = _seed(repository)
    _support_then_challenge(engine)
    engine.transition_claim(CLAIM_ID, "SUPPORTED", actor=HUMAN, reason="reviewed")
    decision = repository.list("claim_resupport_decision")[0]

    with pytest.raises(psycopg.Error, match="append-only"):
        repository.connection.execute(
            "UPDATE claim_resupport_decision SET reason='tampered' WHERE id=%s",
            (decision["id"],),
        )
    with pytest.raises(psycopg.Error, match="append-only"):
        repository.connection.execute(
            "DELETE FROM claim_resupport_decision WHERE id=%s",
            (decision["id"],),
        )

    assert repository.get(decision["id"]) == decision
