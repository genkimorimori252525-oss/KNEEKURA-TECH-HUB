import pytest

from kneekura_tech_hub.repository import MemoryRepository
from kneekura_tech_hub.service import CurationEngine, CurationError


HUMAN = {"actor_type": "human", "actor_id": "reviewer"}
AI = {"actor_type": "ai", "actor_id": "extractor", "version": "test"}


def source(source_id: str = "src:repo") -> dict:
    return {
        "record_type": "source",
        "id": source_id,
        "kind": "repository",
        "origin": {"provider": "github", "repository": "example/repo"},
        "acquisition": {"level": "metadata-only"},
        "license": {"state": "UNKNOWN"},
    }


def entity(entity_id: str = "ke:incremental") -> dict:
    return {
        "record_type": "knowledge_entity",
        "id": entity_id,
        "canonical_name": "Incremental Computation",
        "aliases": [],
        "kinds": ["technique"],
        "abstraction_level": "L1",
        "identity_state": "CANONICAL",
        "relations": [],
    }


def evidence(evidence_id: str = "ev:1") -> dict:
    return {
        "record_type": "evidence",
        "id": evidence_id,
        "source_id": "src:repo",
        "locator": {
            "type": "source_lines",
            "path": "src/cache.rs",
            "line_start": 10,
            "line_end": 20,
            "content_hash": "sha256:test",
        },
        "roles": ["SUPPORTS"],
    }


def claim(claim_id: str = "cl:1", *, maturity: str = "CANDIDATE") -> dict:
    return {
        "record_type": "claim",
        "id": claim_id,
        "entity_id": "ke:incremental",
        "claim_type": "DIRECT_OBSERVATION",
        "statement": "The pinned source contains an invalidation path.",
        "maturity": maturity,
        "evidence_ids": ["ev:1"],
        "created_by": HUMAN,
        "policy_version": "1.0.0",
    }


def seeded_engine() -> CurationEngine:
    engine = CurationEngine(MemoryRepository())
    engine.register_source(source(), actor=HUMAN)
    engine.create_entity(entity(), actor=HUMAN)
    engine.register_evidence(evidence(), actor=HUMAN)
    return engine


def test_create_claim_requires_existing_evidence():
    engine = CurationEngine(MemoryRepository())
    engine.register_source(source(), actor=HUMAN)
    engine.create_entity(entity(), actor=HUMAN)

    with pytest.raises(CurationError, match="unknown record: ev:1"):
        engine.create_claim(claim(), actor=HUMAN)


def test_ai_cannot_create_canonical_entity():
    engine = CurationEngine(MemoryRepository())
    with pytest.raises(CurationError, match="requires a human actor"):
        engine.create_entity(entity(), actor=AI)


def test_claim_transition_requires_human_for_validated():
    engine = seeded_engine()
    engine.create_claim(claim(), actor=HUMAN)
    engine.transition_claim("cl:1", "SUPPORTED", actor=HUMAN, reason="evidence anchored")

    with pytest.raises(CurationError, match="requires a human actor"):
        engine.transition_claim("cl:1", "VALIDATED", actor=AI, reason="model says so")


def test_validated_transition_sets_verification_timestamp_and_event():
    engine = seeded_engine()
    engine.create_claim(claim(), actor=HUMAN)
    engine.transition_claim("cl:1", "SUPPORTED", actor=HUMAN, reason="reviewed")
    updated = engine.transition_claim("cl:1", "VALIDATED", actor=HUMAN, reason="reproduced")

    assert updated["maturity"] == "VALIDATED"
    assert updated["last_verified"]
    operations = [event["operation"] for event in engine.list("curation_event")]
    assert "CLAIM_PROMOTE" in operations


def test_merge_preserves_redirect_and_audit_event():
    engine = CurationEngine(MemoryRepository())
    engine.create_entity(entity("ke:a"), actor=HUMAN)
    other = entity("ke:b")
    other["canonical_name"] = "Incremental Recalculation"
    engine.create_entity(other, actor=HUMAN)

    _, merged = engine.merge_entities("ke:a", "ke:b", actor=HUMAN, reason="same concept")

    assert merged["identity_state"] == "MERGED"
    assert merged["redirect_to"] == "ke:a"
    merge_events = [
        event for event in engine.list("curation_event") if event["operation"] == "ENTITY_MERGE"
    ]
    assert len(merge_events) == 1
    assert merge_events[0]["reversible"] is True


def test_relation_target_must_exist():
    engine = CurationEngine(MemoryRepository())
    item = entity()
    item["relations"] = [{"type": "requires", "target": "ke:missing"}]

    with pytest.raises(CurationError, match="unknown relation target"):
        engine.create_entity(item, actor=HUMAN)


def test_staged_observation_stays_outside_curated_claims():
    engine = CurationEngine(MemoryRepository())
    engine.register_source(source(), actor=HUMAN)
    observation = {
        "record_type": "staged_observation",
        "id": "obs:1",
        "source_id": "src:repo",
        "summary": "Possible incremental invalidation pattern",
        "candidate_names": ["Incremental invalidation"],
        "status": "NEW",
        "created_by": AI,
    }

    engine.stage_observation(observation)

    assert len(engine.list("staged_observation")) == 1
    assert engine.list("claim") == []
