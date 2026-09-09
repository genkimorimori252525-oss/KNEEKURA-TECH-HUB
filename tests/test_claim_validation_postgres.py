from __future__ import annotations

import os

import psycopg
import pytest

from kneekura_tech_hub.claim_validation import ClaimValidationError, validate_claim
from kneekura_tech_hub.claim_validation_postgres import ClaimValidationPostgresRepository
from kneekura_tech_hub.database import apply_migrations
from kneekura_tech_hub.service import CurationEngine


DSN = os.getenv("KTHUB_TEST_DATABASE_URL")
pytestmark = pytest.mark.skipif(not DSN, reason="KTHUB_TEST_DATABASE_URL is not set")
HUMAN = {"actor_type": "human", "actor_id": "validation-reviewer"}
AI = {"actor_type": "ai", "actor_id": "validation-model", "version": "v1"}
SOURCE_ID = "src:validation:postgres"
SNAPSHOT_ID = "ss:validation:postgres"
EVIDENCE_ID = "ev:validation:postgres"
ENTITY_ID = "ke:validation:postgres"
CLAIM_ID = "cl:validation:postgres"


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


def _seed_supported(
    repository: ClaimValidationPostgresRepository,
    *,
    roles: list[str] | None = None,
) -> CurationEngine:
    roles = roles or ["SUPPORTS"]
    engine = CurationEngine(repository)
    engine.register_source(
        {
            "record_type": "source",
            "id": SOURCE_ID,
            "kind": "repository",
            "origin": {"provider": "fixture", "repository": "example/validation"},
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
                "content_hash": "sha256:" + "b" * 64,
            },
            "roles": roles,
        },
        actor=HUMAN,
    )
    engine.create_entity(
        {
            "record_type": "knowledge_entity",
            "id": ENTITY_ID,
            "canonical_name": "Validation gate fixture",
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
            "statement": "The fixture demonstrates a governed validation boundary.",
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
    support_review = {}
    if "REFUTES" in roles:
        support_review["counterevidence_note"] = "Counterevidence was reviewed at support time."
    if "QUALIFIES" in roles:
        support_review["qualification_note"] = "Qualification was reviewed at support time."
    engine.transition_claim(
        CLAIM_ID,
        "SUPPORTED",
        actor=HUMAN,
        reason="fixture support review",
        support_review=support_review or None,
    )
    return engine


@pytest.fixture()
def repository():
    assert DSN is not None
    with psycopg.connect(DSN, autocommit=True) as setup:
        apply_migrations(setup)
        _truncate(setup)
    repo = ClaimValidationPostgresRepository.connect(DSN)
    try:
        yield repo
    finally:
        repo.close()


def test_public_validated_transition_routes_through_validation_gate(repository) -> None:
    engine = _seed_supported(repository)
    validated = engine.transition_claim(
        CLAIM_ID,
        "VALIDATED",
        actor=HUMAN,
        reason="reviewed pinned evidence again",
    )

    assert validated["maturity"] == "VALIDATED"
    assert validated["last_verified"]
    decisions = repository.list("claim_validation_decision")
    assert len(decisions) == 1
    decision = decisions[0]
    assert decision["from_maturity"] == "SUPPORTED"
    assert decision["validation_basis"] == "EVIDENCE_REVIEW"
    assert decision["validation_note"] == "reviewed pinned evidence again"
    assert decision["evidence_ids"] == [EVIDENCE_ID]
    assert decision["supporting_evidence_ids"] == [EVIDENCE_ID]
    assert decision["support_decision_id"].startswith("csd:")
    assert decision["validated_at"] == validated["last_verified"]


def test_ai_cannot_validate_and_writes_nothing(repository) -> None:
    _seed_supported(repository)
    before = repository.list()
    with pytest.raises(ClaimValidationError, match="human reviewer"):
        validate_claim(
            repository,
            CLAIM_ID,
            actor=AI,
            reason="model approves",
            validation_basis="EVIDENCE_REVIEW",
            validation_note="model-only review",
            independence_assessment="NOT_ASSESSED",
        )
    assert repository.list() == before


def test_direct_repository_validated_transition_is_rejected_by_database(repository) -> None:
    _seed_supported(repository)
    bypass = repository.get(CLAIM_ID)
    assert bypass is not None
    bypass["maturity"] = "VALIDATED"
    bypass["last_verified"] = "2026-09-09T01:00:00+00:00"
    with pytest.raises(psycopg.Error, match="requires matching claim validation decision"):
        repository.put(bypass, replace=True)
    assert repository.get(CLAIM_ID)["maturity"] == "SUPPORTED"
    assert repository.list("claim_validation_decision") == []


def test_validation_requires_new_decision_after_challenge(repository) -> None:
    engine = _seed_supported(repository)
    first = validate_claim(
        repository,
        CLAIM_ID,
        actor=HUMAN,
        reason="initial validation",
        validation_basis="REPRODUCTION",
        validation_note="Reproduced the pinned behavior manually.",
        independence_assessment="NOT_ASSESSED",
        decision_id="cvd:initial",
    )
    first_timestamp = first["decision"]["validated_at"]

    engine.transition_claim(CLAIM_ID, "CHALLENGED", actor=AI, reason="new concern")
    bypass = repository.get(CLAIM_ID)
    assert bypass is not None
    bypass["maturity"] = "VALIDATED"
    bypass["last_verified"] = first_timestamp
    with pytest.raises(psycopg.Error, match="requires matching claim validation decision"):
        repository.put(bypass, replace=True)

    second = validate_claim(
        repository,
        CLAIM_ID,
        actor=HUMAN,
        reason="challenge rechecked",
        validation_basis="EVIDENCE_REVIEW",
        validation_note="Re-read the pinned evidence after the challenge.",
        independence_assessment="NOT_ASSESSED",
        decision_id="cvd:revalidation",
    )
    assert second["claim"]["maturity"] == "VALIDATED"
    assert second["decision"]["from_maturity"] == "CHALLENGED"
    assert second["claim"]["last_verified"] == second["decision"]["validated_at"]
    history = repository.list("claim_validation_decision")
    assert [record["id"] for record in history] == ["cvd:initial", "cvd:revalidation"]


def test_refuting_evidence_requires_fresh_validation_acknowledgement(repository) -> None:
    _seed_supported(repository, roles=["SUPPORTS", "REFUTES"])
    with pytest.raises(ClaimValidationError, match="counterevidence_note"):
        validate_claim(
            repository,
            CLAIM_ID,
            actor=HUMAN,
            reason="validation review",
            validation_basis="EVIDENCE_REVIEW",
            validation_note="Reviewed the current evidence.",
            independence_assessment="NOT_ASSESSED",
        )

    result = validate_claim(
        repository,
        CLAIM_ID,
        actor=HUMAN,
        reason="validation review with counterevidence",
        validation_basis="EVIDENCE_REVIEW",
        validation_note="Reviewed the current evidence and its limiting material.",
        independence_assessment="NOT_ASSESSED",
        counterevidence_note="The limiting material was considered and does not erase the scoped claim.",
    )
    assert result["claim"]["maturity"] == "VALIDATED"
    assert result["decision"]["refuting_evidence_ids"] == [EVIDENCE_ID]


def test_database_rejects_forged_validation_evidence_profile(repository) -> None:
    _seed_supported(repository)
    support_decision = repository.list("claim_support_decision")[0]
    decision = {
        "record_type": "claim_validation_decision",
        "id": "cvd:forged",
        "claim_id": CLAIM_ID,
        "support_decision_id": support_decision["id"],
        "from_maturity": "SUPPORTED",
        "to_maturity": "VALIDATED",
        "reason": "direct SQL bypass attempt",
        "validated_by": HUMAN,
        "validation_basis": "EVIDENCE_REVIEW",
        "validation_note": "Pretend review.",
        "evidence_ids": ["ev:forged"],
        "supporting_evidence_ids": [EVIDENCE_ID],
        "refuting_evidence_ids": [],
        "qualifying_evidence_ids": [],
        "distinct_source_ids": [SOURCE_ID],
        "distinct_snapshot_ids": [SNAPSHOT_ID],
        "review_flags": ["SINGLE_SOURCE"],
        "competing_active_claim_ids": [],
        "independence_assessment": "NOT_ASSESSED",
        "policy_version": "1.0.0",
        "validated_at": "2026-09-09T02:00:00+00:00",
    }
    with pytest.raises(psycopg.Error, match="evidence_ids do not match"):
        repository.put(decision)
    assert repository.get("cvd:forged") is None


def test_validation_transaction_rolls_back_decision_claim_and_event_on_late_failure(
    repository, monkeypatch
) -> None:
    _seed_supported(repository)
    before_events = len(repository.list("curation_event"))
    original_put = repository.put

    def failing_put(record, *, replace=False):
        if record.get("record_type") == "curation_event" and record.get("operation") == "CLAIM_PROMOTE":
            raise RuntimeError("synthetic validation event failure")
        return original_put(record, replace=replace)

    monkeypatch.setattr(repository, "put", failing_put)
    with pytest.raises(RuntimeError, match="synthetic validation event failure"):
        validate_claim(
            repository,
            CLAIM_ID,
            actor=HUMAN,
            reason="reviewed",
            validation_basis="EVIDENCE_REVIEW",
            validation_note="Reviewed exact evidence.",
            independence_assessment="NOT_ASSESSED",
            decision_id="cvd:rollback",
        )
    monkeypatch.setattr(repository, "put", original_put)

    assert repository.get(CLAIM_ID)["maturity"] == "SUPPORTED"
    assert repository.get(CLAIM_ID).get("last_verified") is None
    assert repository.get("cvd:rollback") is None
    assert len(repository.list("curation_event")) == before_events
