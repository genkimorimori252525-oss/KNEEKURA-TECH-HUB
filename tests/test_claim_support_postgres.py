from __future__ import annotations

import os

import psycopg
import pytest

from kneekura_tech_hub.claim_support import ClaimSupportError, promote_candidate_to_supported
from kneekura_tech_hub.claim_support_postgres import ClaimSupportPostgresRepository
from kneekura_tech_hub.database import apply_migrations
from kneekura_tech_hub.service import CurationEngine


DSN = os.getenv("KTHUB_TEST_DATABASE_URL")
pytestmark = pytest.mark.skipif(not DSN, reason="KTHUB_TEST_DATABASE_URL is not set")
HUMAN = {"actor_type": "human", "actor_id": "support-reviewer"}
AI = {"actor_type": "ai", "actor_id": "support-model", "version": "v1"}
SOURCE_ID = "src:support:postgres"
SNAPSHOT_ID = "ss:support:postgres"
EVIDENCE_ID = "ev:support:postgres"
ENTITY_ID = "ke:support:postgres"
CLAIM_ID = "cl:support:postgres"


def _truncate(connection) -> None:
    connection.execute(
        """
        TRUNCATE TABLE
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


def _seed(repository: ClaimSupportPostgresRepository, *, roles=None) -> CurationEngine:
    roles = roles or ["SUPPORTS"]
    engine = CurationEngine(repository)
    engine.register_source(
        {
            "record_type": "source",
            "id": SOURCE_ID,
            "kind": "repository",
            "origin": {"provider": "fixture", "repository": "example/support"},
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
                "content_hash": "sha256:" + "a" * 64,
            },
            "roles": roles,
        },
        actor=HUMAN,
    )
    engine.create_entity(
        {
            "record_type": "knowledge_entity",
            "id": ENTITY_ID,
            "canonical_name": "Support gate fixture",
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
            "statement": "The fixture demonstrates a candidate support gate.",
            "maturity": "CANDIDATE",
            "evidence_ids": [EVIDENCE_ID],
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


def test_direct_repository_candidate_to_supported_is_rejected_by_database(repository) -> None:
    _seed(repository)
    before_events = len(repository.list("curation_event"))
    bypass = repository.get(CLAIM_ID)
    assert bypass is not None
    bypass["maturity"] = "SUPPORTED"
    with pytest.raises(psycopg.Error, match="requires matching claim support decision"):
        repository.put(bypass, replace=True)
    assert repository.get(CLAIM_ID)["maturity"] == "CANDIDATE"
    assert repository.list("claim_support_decision") == []
    assert len(repository.list("curation_event")) == before_events


def test_public_transition_routes_through_support_gate(repository) -> None:
    engine = _seed(repository)
    supported = engine.transition_claim(
        CLAIM_ID,
        "SUPPORTED",
        actor=HUMAN,
        reason="public API review",
    )
    assert supported["maturity"] == "SUPPORTED"
    decisions = repository.list("claim_support_decision")
    assert len(decisions) == 1
    assert decisions[0]["claim_id"] == CLAIM_ID
    assert decisions[0]["independence_assessment"] == "NOT_ASSESSED"


def test_support_gate_promotes_with_auditable_non_scalar_review(repository) -> None:
    _seed(repository)
    result = promote_candidate_to_supported(
        repository,
        CLAIM_ID,
        actor=HUMAN,
        reason="reviewed exact pinned evidence",
        independence_assessment="NOT_ASSESSED",
        decision_id="csd:support:postgres",
    )
    assert result["claim"]["maturity"] == "SUPPORTED"
    decision = result["decision"]
    assert decision["evidence_ids"] == [EVIDENCE_ID]
    assert decision["supporting_evidence_ids"] == [EVIDENCE_ID]
    assert decision["refuting_evidence_ids"] == []
    assert decision["distinct_source_ids"] == [SOURCE_ID]
    assert decision["distinct_snapshot_ids"] == [SNAPSHOT_ID]
    assert decision["independence_assessment"] == "NOT_ASSESSED"
    assert "SINGLE_SOURCE" in decision["review_flags"]
    assert repository.get("csd:support:postgres") == decision


def test_ai_cannot_support_candidate_and_writes_nothing(repository) -> None:
    _seed(repository)
    before = repository.list()
    with pytest.raises(ClaimSupportError, match="human reviewer"):
        promote_candidate_to_supported(
            repository,
            CLAIM_ID,
            actor=AI,
            reason="model approves",
            independence_assessment="NOT_ASSESSED",
        )
    assert repository.list() == before


def test_refuting_evidence_requires_explicit_human_acknowledgement(repository) -> None:
    _seed(repository, roles=["SUPPORTS", "REFUTES"])
    with pytest.raises(ClaimSupportError, match="counterevidence_note"):
        promote_candidate_to_supported(
            repository,
            CLAIM_ID,
            actor=HUMAN,
            reason="reviewed",
            independence_assessment="NOT_ASSESSED",
        )
    result = promote_candidate_to_supported(
        repository,
        CLAIM_ID,
        actor=HUMAN,
        reason="reviewed with counterevidence",
        independence_assessment="NOT_ASSESSED",
        counterevidence_note="The same pinned evidence contains both supporting and limiting material.",
    )
    assert result["claim"]["maturity"] == "SUPPORTED"
    assert result["decision"]["refuting_evidence_ids"] == [EVIDENCE_ID]


def test_support_transaction_rolls_back_claim_decision_and_event_on_late_failure(
    repository, monkeypatch
) -> None:
    _seed(repository)
    original_put = repository.put

    def failing_put(record, *, replace=False):
        if record.get("record_type") == "curation_event" and record.get("operation") == "CLAIM_PROMOTE":
            raise RuntimeError("synthetic late failure")
        return original_put(record, replace=replace)

    monkeypatch.setattr(repository, "put", failing_put)
    with pytest.raises(RuntimeError, match="synthetic late failure"):
        promote_candidate_to_supported(
            repository,
            CLAIM_ID,
            actor=HUMAN,
            reason="reviewed",
            independence_assessment="NOT_ASSESSED",
            decision_id="csd:rollback",
        )
    monkeypatch.setattr(repository, "put", original_put)
    assert repository.get(CLAIM_ID)["maturity"] == "CANDIDATE"
    assert repository.get("csd:rollback") is None


def test_decision_without_applied_supported_state_is_rejected(repository) -> None:
    _seed(repository)
    decision = {
        "record_type": "claim_support_decision",
        "id": "csd:orphan",
        "claim_id": CLAIM_ID,
        "from_maturity": "CANDIDATE",
        "to_maturity": "SUPPORTED",
        "reason": "orphan decision",
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
        "decided_at": "2026-09-09T00:00:00Z",
    }
    with pytest.raises(psycopg.Error, match="requires SUPPORTED maturity"):
        repository.put(decision)
    assert repository.get("csd:orphan") is None
