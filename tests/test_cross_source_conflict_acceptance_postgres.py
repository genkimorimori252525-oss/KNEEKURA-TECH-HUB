from __future__ import annotations

import os

import psycopg
import pytest

from kneekura_tech_hub.claim_support import claim_support_history
from kneekura_tech_hub.claim_validation import claim_validation_history
from kneekura_tech_hub.comparison import compare_claim
from kneekura_tech_hub.database import apply_migrations
from kneekura_tech_hub.explanation import explain_claim
from kneekura_tech_hub.postgres_repository import PostgresRepository
from kneekura_tech_hub.service import CurationEngine, CurationError


DSN = os.getenv("KTHUB_TEST_DATABASE_URL")
pytestmark = pytest.mark.skipif(not DSN, reason="KTHUB_TEST_DATABASE_URL is not set")

HUMAN = {"actor_type": "human", "actor_id": "cross-source-conflict-reviewer"}
AI = {"actor_type": "ai", "actor_id": "cross-source-conflict-agent", "version": "v1"}
TOOL = {"actor_type": "tool", "actor_id": "cross-source-conflict-fixture", "version": "v1"}

SOURCE_A = "src:conflict:small-source"
SOURCE_B = "src:conflict:huge-source"
SNAPSHOT_A = "ss:conflict:small-source:rev-a"
SNAPSHOT_B = "ss:conflict:huge-source:rev-b"
EVIDENCE_A = "ev:conflict:small-source:default-enabled"
EVIDENCE_B = "ev:conflict:huge-source:default-disabled"
ENTITY_ID = "ke:conflict:cache-reuse-default"
CLAIM_A = "cl:conflict:cache-reuse:enabled"
CLAIM_B = "cl:conflict:cache-reuse:disabled"


def _truncate(connection) -> None:
    connection.execute(
        """
        TRUNCATE TABLE
            claim_disposition_decision,
            claim_validation_decision,
            claim_support_decision,
            observation_triage_decision,
            review_decision,
            staged_observation_evidence,
            claim_evidence, claim, evidence_relation, evidence,
            source_snapshot, staged_observation, curation_event,
            entity_relation, entity_kind, entity_alias, knowledge_entity, source
        RESTART IDENTITY CASCADE
        """
    )


def _seed_source_chain(
    engine: CurationEngine,
    *,
    source_id: str,
    snapshot_id: str,
    evidence_id: str,
    repository_name: str,
    stars: int,
    revision: str,
    locator_url: str,
) -> None:
    engine.register_source(
        {
            "record_type": "source",
            "id": source_id,
            "kind": "repository",
            "origin": {
                "provider": "github",
                "repository": repository_name,
                "canonical_url": f"https://github.com/{repository_name}",
                "stargazers_count": stars,
            },
            "acquisition": {"level": "snapshot"},
            "license": {
                "state": "KNOWN",
                "declared_expression": "MIT",
                "handling_policy": "REFERENCE_ONLY",
            },
        },
        actor=TOOL,
    )
    engine.register_source_snapshot(
        {
            "record_type": "source_snapshot",
            "id": snapshot_id,
            "source_id": source_id,
            "revision": revision,
            "captured_at": "2026-09-10T02:00:00Z",
            "metadata": {"fixture": "cross-source-conflict-acceptance-v1"},
        },
        actor=TOOL,
    )
    engine.register_evidence(
        {
            "record_type": "evidence",
            "id": evidence_id,
            "source_id": source_id,
            "source_snapshot_id": snapshot_id,
            "locator": {
                "type": "stable_url",
                "url": locator_url,
                "content_hash": f"sha256:{'a' * 64 if source_id == SOURCE_A else 'b' * 64}",
            },
            "roles": ["SUPPORTS"],
        },
        actor=TOOL,
    )


def _create_claim(
    engine: CurationEngine,
    *,
    claim_id: str,
    statement: str,
    evidence_id: str,
) -> None:
    engine.create_claim(
        {
            "record_type": "claim",
            "id": claim_id,
            "entity_id": ENTITY_ID,
            "claim_type": "AUTHOR_CLAIM",
            "statement": statement,
            "maturity": "CANDIDATE",
            "evidence_ids": [evidence_id],
            "scope": {
                "system": "fixture-engine",
                "version": "1.0",
                "setting": "cache-reuse-default",
            },
            "created_by": AI,
            "policy_version": "1.0.0",
        },
        actor=AI,
        reason="AI proposes a source-backed Candidate; trust still requires human gates.",
    )


def test_cross_source_conflict_stays_visible_until_humans_resolve_it() -> None:
    assert DSN is not None
    connection = psycopg.connect(DSN, autocommit=True)
    try:
        apply_migrations(connection)
        _truncate(connection)
        repository = PostgresRepository(connection)
        engine = CurationEngine(repository)

        # Two immutable source chains deliberately disagree about the exact same scoped setting.
        # Popularity is recorded as source metadata only; it has no authority over Claim maturity.
        _seed_source_chain(
            engine,
            source_id=SOURCE_A,
            snapshot_id=SNAPSHOT_A,
            evidence_id=EVIDENCE_A,
            repository_name="example/small-source",
            stars=7,
            revision="aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
            locator_url="https://github.com/example/small-source/blob/aaaaaaaa/README.md#L10",
        )
        _seed_source_chain(
            engine,
            source_id=SOURCE_B,
            snapshot_id=SNAPSHOT_B,
            evidence_id=EVIDENCE_B,
            repository_name="example/huge-source",
            stars=900000,
            revision="bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb",
            locator_url="https://github.com/example/huge-source/blob/bbbbbbbb/README.md#L20",
        )

        engine.create_entity(
            {
                "record_type": "knowledge_entity",
                "id": ENTITY_ID,
                "canonical_name": "Fixture engine cache-reuse default",
                "aliases": [],
                "kinds": ["technique"],
                "abstraction_level": "L1",
                "identity_state": "CANONICAL",
                "relations": [],
            },
            actor=HUMAN,
            reason="Human establishes the exact subject that later source claims may disagree about.",
        )

        # Source A is reviewed first, before any competing Claim exists.
        _create_claim(
            engine,
            claim_id=CLAIM_A,
            statement="Fixture Engine 1.0 enables cache reuse by default.",
            evidence_id=EVIDENCE_A,
        )
        supported_a = engine.transition_claim(
            CLAIM_A,
            "SUPPORTED",
            actor=HUMAN,
            reason="Human reviews Source A's pinned statement.",
            support_review={"decision_id": "csd:conflict:a:initial"},
        )
        assert supported_a["maturity"] == "SUPPORTED"
        validated_a = engine.transition_claim(
            CLAIM_A,
            "VALIDATED",
            actor=HUMAN,
            reason="Human validates only the narrow Source A-backed Claim.",
            validation_review={
                "validation_basis": "EVIDENCE_REVIEW",
                "validation_note": "Reviewed the immutable Source A locator and Snapshot.",
                "independence_assessment": "NOT_ASSESSED",
                "decision_id": "cvd:conflict:a:initial",
            },
        )
        assert validated_a["maturity"] == "VALIDATED"
        original_last_verified = validated_a["last_verified"]

        # Later, a much more popular Source produces an opposite Candidate for the same subject.
        # The Hub must expose the disagreement without calling it a contradiction or choosing a winner.
        _create_claim(
            engine,
            claim_id=CLAIM_B,
            statement="Fixture Engine 1.0 disables cache reuse by default.",
            evidence_id=EVIDENCE_B,
        )
        group = compare_claim(repository, CLAIM_A)
        assert group["active_claim_ids"] == sorted([CLAIM_A, CLAIM_B])
        assert group["active_claim_count"] == 2
        assert group["statements_are_identical"] is False
        assert "MULTIPLE_ACTIVE_CLAIMS" in group["flags"]
        assert "STATEMENTS_DIFFER" in group["flags"]
        assert "HAS_CANDIDATE_CLAIM" in group["flags"]
        assert group["needs_review"] is True
        assert all("CONTRADICTION" not in flag for flag in group["flags"])
        assert "winner" not in group
        assert "preferred_claim_id" not in group
        assert repository.get(CLAIM_A)["maturity"] == "VALIDATED"
        assert repository.get(CLAIM_B)["maturity"] == "CANDIDATE"
        assert repository.get(SOURCE_B)["origin"]["stargazers_count"] == 900000

        # Human acknowledgement of the competing active Claim is mandatory before B can be supported.
        with pytest.raises(CurationError, match="competing active Claims require an explicit competition_note"):
            engine.transition_claim(
                CLAIM_B,
                "SUPPORTED",
                actor=HUMAN,
                reason="This must fail because the existing Validated Claim is not acknowledged.",
            )
        assert repository.get(CLAIM_B)["maturity"] == "CANDIDATE"

        supported_b = engine.transition_claim(
            CLAIM_B,
            "SUPPORTED",
            actor=HUMAN,
            reason="Human records Source B as supported without treating it as the winner.",
            support_review={
                "competition_note": (
                    "Source A asserts enabled-by-default while Source B asserts disabled-by-default; "
                    "both source-backed Claims remain active pending resolution."
                ),
                "decision_id": "csd:conflict:b:with-competition",
            },
        )
        assert supported_b["maturity"] == "SUPPORTED"
        support_b = claim_support_history(repository, claim_id=CLAIM_B)[0]
        assert support_b["competing_active_claim_ids"] == [CLAIM_A]
        assert support_b["distinct_source_ids"] == [SOURCE_B]
        assert "competition_note" in support_b

        # Validation also refuses to hide the still-active competitor.
        with pytest.raises(CurationError, match="competing active Claims require an explicit competition_note"):
            engine.transition_claim(
                CLAIM_B,
                "VALIDATED",
                actor=HUMAN,
                reason="This must fail until the competing Validated Claim is acknowledged.",
                validation_review={
                    "validation_basis": "EVIDENCE_REVIEW",
                    "validation_note": "Source B was reviewed, but competition was omitted.",
                    "independence_assessment": "NOT_ASSESSED",
                },
            )
        assert repository.get(CLAIM_B)["maturity"] == "SUPPORTED"

        # AI is allowed to raise a re-verification warning by challenging the old Validated Claim.
        challenged_a = engine.transition_claim(
            CLAIM_A,
            "CHALLENGED",
            actor=AI,
            reason=(
                f"New active Claim {CLAIM_B} from {SOURCE_B} reports the opposite default; "
                "human re-verification is required."
            ),
        )
        assert challenged_a["maturity"] == "CHALLENGED"
        assert challenged_a["last_verified"] == original_last_verified
        assert repository.get(CLAIM_B)["maturity"] == "SUPPORTED"

        challenged_group = compare_claim(repository, CLAIM_A)
        assert challenged_group["active_claim_ids"] == sorted([CLAIM_A, CLAIM_B])
        assert "HAS_CHALLENGED_CLAIM" in challenged_group["flags"]
        assert "STATEMENTS_DIFFER" in challenged_group["flags"]
        assert challenged_group["needs_review"] is True
        assert "winner" not in challenged_group
        assert "preferred_claim_id" not in challenged_group

        challenge_events = [
            event
            for event in repository.list("curation_event")
            if event["operation"] == "CLAIM_CHALLENGE" and event["subject_ids"] == [CLAIM_A]
        ]
        assert len(challenge_events) == 1
        assert challenge_events[0]["actor"] == AI
        assert CLAIM_B in challenge_events[0]["reason"]
        assert SOURCE_B in challenge_events[0]["reason"]

        # Automation may warn, but it cannot restore trust or erase a reviewed Claim by itself.
        with pytest.raises(CurationError, match="VALIDATED promotion requires a human reviewer"):
            engine.transition_claim(
                CLAIM_A,
                "VALIDATED",
                actor=AI,
                reason="AI must not resolve its own conflict warning.",
                validation_review={
                    "validation_basis": "EVIDENCE_REVIEW",
                    "validation_note": "AI attempted to revalidate.",
                    "independence_assessment": "NOT_ASSESSED",
                    "competition_note": "A competing Claim still exists.",
                },
            )
        assert repository.get(CLAIM_A)["maturity"] == "CHALLENGED"

        with pytest.raises(psycopg.Error, match="requires matching human disposition decision"):
            engine.transition_claim(
                CLAIM_A,
                "REJECTED",
                actor=AI,
                reason="AI must not terminally delete the reviewed side of a conflict.",
            )
        assert repository.get(CLAIM_A)["maturity"] == "CHALLENGED"
        assert repository.get(CLAIM_B)["maturity"] == "SUPPORTED"

        # Historical validation and both immutable provenance chains remain explainable while unresolved.
        validation_a = claim_validation_history(repository, claim_id=CLAIM_A)
        assert len(validation_a) == 1
        assert validation_a[0]["id"] == "cvd:conflict:a:initial"

        explanation_a = explain_claim(repository, CLAIM_A)
        explanation_b = explain_claim(repository, CLAIM_B)
        assert explanation_a["claim"]["maturity"] == "CHALLENGED"
        assert explanation_b["claim"]["maturity"] == "SUPPORTED"
        assert explanation_a["evidence_chains"][0]["source"]["id"] == SOURCE_A
        assert explanation_a["evidence_chains"][0]["source_snapshot"]["id"] == SNAPSHOT_A
        assert explanation_b["evidence_chains"][0]["source"]["id"] == SOURCE_B
        assert explanation_b["evidence_chains"][0]["source_snapshot"]["id"] == SNAPSHOT_B

        final_group = compare_claim(repository, CLAIM_A)
        assert final_group["active_claim_count"] == 2
        assert final_group["needs_review"] is True
        assert {item["claim"]["maturity"] for item in final_group["claims"]} == {
            "CHALLENGED",
            "SUPPORTED",
        }
    finally:
        connection.close()
