import pytest

from kneekura_tech_hub.repository import MemoryRepository
from kneekura_tech_hub.service import CurationEngine, CurationError


HUMAN = {"actor_type": "human", "actor_id": "reviewer"}
AI = {"actor_type": "ai", "actor_id": "extractor", "version": "test"}


def entity(entity_id: str, name: str) -> dict:
    return {
        "record_type": "knowledge_entity",
        "id": entity_id,
        "canonical_name": name,
        "aliases": [],
        "kinds": ["technique"],
        "abstraction_level": "L1",
        "identity_state": "CANONICAL",
        "relations": [],
    }


def seeded_engine() -> CurationEngine:
    engine = CurationEngine(MemoryRepository())
    engine.register_source(
        {
            "record_type": "source",
            "id": "src:relations",
            "kind": "repository",
            "origin": {"provider": "github", "repository": "example/relations"},
            "acquisition": {"level": "snapshot"},
            "license": {"state": "KNOWN", "declared_expression": "MIT"},
        },
        actor=HUMAN,
    )
    engine.register_source_snapshot(
        {
            "record_type": "source_snapshot",
            "id": "ss:relations",
            "source_id": "src:relations",
            "revision": "0123456789abcdef",
            "captured_at": "2026-09-09T00:00:00Z",
        },
        actor=HUMAN,
    )
    engine.register_evidence(
        {
            "record_type": "evidence",
            "id": "ev:relations",
            "source_id": "src:relations",
            "source_snapshot_id": "ss:relations",
            "locator": {
                "type": "source_lines",
                "path": "README.md",
                "line_start": 1,
                "line_end": 2,
                "content_hash": "sha256:relations",
            },
            "roles": ["SUPPORTS"],
        },
        actor=HUMAN,
    )
    engine.create_entity(entity("ke:general", "Incremental Computation"), actor=HUMAN)
    engine.create_entity(entity("ke:specific", "Query-based Incremental Computation"), actor=HUMAN)
    engine.create_entity(entity("ke:other", "Incremental Parsing"), actor=HUMAN)
    return engine


def relation_claim(claim_id: str, *, target: str = "ke:general") -> dict:
    return {
        "record_type": "claim",
        "id": claim_id,
        "relation": {
            "source_entity_id": "ke:specific",
            "relation_type": "narrower_than",
            "target_entity_id": target,
        },
        "claim_type": "INFERENCE",
        "statement": "The specific technique appears to be a specialization of the general technique.",
        "maturity": "CANDIDATE",
        "evidence_ids": ["ev:relations"],
        "confidence": "MEDIUM",
        "reasoning_basis": ["ev:relations"],
        "created_by": AI,
        "policy_version": "1.0.0",
    }


def test_relation_claim_uses_normal_lifecycle_without_mutating_entity_relations():
    engine = seeded_engine()
    engine.create_claim(relation_claim("cl:relation"), actor=AI)

    engine.transition_claim("cl:relation", "SUPPORTED", actor=HUMAN, reason="reviewed")
    validated = engine.transition_claim(
        "cl:relation", "VALIDATED", actor=HUMAN, reason="relation reproduced"
    )

    assert validated["maturity"] == "VALIDATED"
    assert validated["relation"]["relation_type"] == "narrower_than"
    assert engine.get("ke:specific")["relations"] == []
    assert engine.get("ke:general")["relations"] == []


def test_relation_claim_requires_existing_distinct_endpoints_and_evidence():
    engine = seeded_engine()

    missing_endpoint = relation_claim("cl:missing", target="ke:missing")
    with pytest.raises(CurationError, match="unknown record"):
        engine.create_claim(missing_endpoint, actor=AI)

    self_relation = relation_claim("cl:self", target="ke:specific")
    with pytest.raises(CurationError, match="different entities"):
        engine.create_claim(self_relation, actor=AI)

    no_evidence = relation_claim("cl:no-evidence")
    no_evidence["evidence_ids"] = []
    with pytest.raises(CurationError, match="at least one evidence_id"):
        engine.create_claim(no_evidence, actor=AI)


def test_supersede_requires_same_subject_distinct_mature_successor():
    engine = seeded_engine()
    original = relation_claim("cl:old")
    successor = relation_claim("cl:new")
    other_subject = relation_claim("cl:other", target="ke:other")

    engine.create_claim(original, actor=AI)
    engine.create_claim(successor, actor=AI)
    engine.create_claim(other_subject, actor=AI)
    engine.transition_claim(
        "cl:old",
        "SUPPORTED",
        actor=HUMAN,
        reason="reviewed",
        support_review={
            "competition_note": "The successor is an alternative formulation kept for supersession testing."
        },
    )
    engine.transition_claim("cl:old", "VALIDATED", actor=HUMAN, reason="verified")

    with pytest.raises(CurationError, match="cannot supersede itself"):
        engine.transition_claim(
            "cl:old", "SUPERSEDED", actor=HUMAN, reason="bad", superseded_by="cl:old"
        )

    with pytest.raises(CurationError, match="at least SUPPORTED"):
        engine.transition_claim(
            "cl:old", "SUPERSEDED", actor=HUMAN, reason="too early", superseded_by="cl:new"
        )

    engine.transition_claim(
        "cl:new",
        "SUPPORTED",
        actor=HUMAN,
        reason="reviewed successor",
        support_review={
            "competition_note": "The validated prior Claim is being compared as the supersession predecessor."
        },
    )
    engine.transition_claim("cl:other", "SUPPORTED", actor=HUMAN, reason="reviewed alternate")

    with pytest.raises(CurationError, match="same claim subject"):
        engine.transition_claim(
            "cl:old", "SUPERSEDED", actor=HUMAN, reason="wrong subject", superseded_by="cl:other"
        )

    superseded = engine.transition_claim(
        "cl:old", "SUPERSEDED", actor=HUMAN, reason="better formulation", superseded_by="cl:new"
    )
    assert superseded["maturity"] == "SUPERSEDED"
    assert superseded["superseded_by"] == "cl:new"
