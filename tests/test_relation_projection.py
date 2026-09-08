import pytest

from kneekura_tech_hub.projection import ProjectionError, project_relations, resolve_entity_id
from kneekura_tech_hub.repository import MemoryRepository


def entity(entity_id: str, *, state: str = "CANONICAL", redirect_to: str | None = None) -> dict:
    record = {
        "record_type": "knowledge_entity",
        "id": entity_id,
        "canonical_name": entity_id,
        "aliases": [],
        "kinds": ["technique"],
        "abstraction_level": "L1",
        "identity_state": state,
        "relations": [],
    }
    if redirect_to is not None:
        record["redirect_to"] = redirect_to
    return record


def relation_claim(
    claim_id: str,
    maturity: str,
    *,
    source: str = "ke:a",
    relation_type: str = "related_to",
    target: str = "ke:b",
) -> dict:
    return {
        "record_type": "claim",
        "id": claim_id,
        "relation": {
            "source_entity_id": source,
            "relation_type": relation_type,
            "target_entity_id": target,
        },
        "claim_type": "INFERENCE",
        "statement": claim_id,
        "maturity": maturity,
        "evidence_ids": ["ev:test"],
        "confidence": "MEDIUM",
        "reasoning_basis": ["ev:test"],
        "created_by": {"actor_type": "ai", "actor_id": "extractor"},
        "policy_version": "1.0.0",
    }


def seeded_repository() -> MemoryRepository:
    repository = MemoryRepository()
    for record in (
        entity("ke:a"),
        entity("ke:b"),
        entity("ke:c"),
        entity("ke:old", state="MERGED", redirect_to="ke:a"),
        relation_claim("cl:candidate", "CANDIDATE"),
        relation_claim("cl:supported", "SUPPORTED", relation_type="requires"),
        relation_claim("cl:validated", "VALIDATED", source="ke:old"),
        relation_claim("cl:challenged", "CHALLENGED", target="ke:c"),
        relation_claim("cl:superseded", "SUPERSEDED", relation_type="enables"),
        relation_claim("cl:rejected", "REJECTED", relation_type="conflicts_with"),
    ):
        repository.put(record)
    return repository


def test_views_expose_only_their_intended_maturities():
    repository = seeded_repository()

    validated = project_relations(repository, view="validated")
    research = project_relations(repository, view="research")
    challenged = project_relations(repository, view="challenged")
    history = project_relations(repository, view="history")

    assert [edge["claim_id"] for edge in validated] == ["cl:validated"]
    assert {edge["claim_id"] for edge in research} == {
        "cl:candidate",
        "cl:supported",
        "cl:validated",
        "cl:challenged",
    }
    assert [edge["claim_id"] for edge in challenged] == ["cl:challenged"]
    assert {edge["claim_id"] for edge in history} == {
        "cl:candidate",
        "cl:supported",
        "cl:validated",
        "cl:challenged",
        "cl:superseded",
        "cl:rejected",
    }


def test_projection_preserves_asserted_endpoint_and_resolves_current_identity():
    repository = seeded_repository()

    edge = project_relations(repository, view="validated")[0]

    assert edge["asserted_relation"]["source_entity_id"] == "ke:old"
    assert edge["relation"]["source_entity_id"] == "ke:a"
    assert edge["redirected"] is True
    assert repository.get("cl:validated")["relation"]["source_entity_id"] == "ke:old"


def test_entity_and_direction_filters_use_resolved_identity():
    repository = seeded_repository()

    by_survivor = project_relations(repository, view="validated", entity_id="ke:a")
    by_merged_id = project_relations(repository, view="validated", entity_id="ke:old")
    outgoing = project_relations(
        repository, view="research", entity_id="ke:a", direction="out"
    )
    incoming = project_relations(
        repository, view="research", entity_id="ke:a", direction="in"
    )

    assert [edge["claim_id"] for edge in by_survivor] == ["cl:validated"]
    assert [edge["claim_id"] for edge in by_merged_id] == ["cl:validated"]
    assert {edge["claim_id"] for edge in outgoing} >= {"cl:validated"}
    assert incoming == []


def test_relation_type_filter_does_not_collapse_competing_claims():
    repository = seeded_repository()
    repository.put(relation_claim("cl:second-related", "CANDIDATE"))

    related = project_relations(repository, view="research", relation_type="related_to")

    assert {edge["claim_id"] for edge in related} == {
        "cl:candidate",
        "cl:validated",
        "cl:challenged",
        "cl:second-related",
    }


def test_redirect_cycle_is_reported_as_projection_corruption():
    repository = MemoryRepository()
    repository.put(entity("ke:x", state="MERGED", redirect_to="ke:y"))
    repository.put(entity("ke:y", state="MERGED", redirect_to="ke:x"))

    with pytest.raises(ProjectionError, match="redirect cycle"):
        resolve_entity_id(repository, "ke:x")


def test_unknown_view_and_direction_are_rejected():
    repository = seeded_repository()

    with pytest.raises(ProjectionError, match="unknown relation view"):
        project_relations(repository, view="wrong")  # type: ignore[arg-type]
    with pytest.raises(ProjectionError, match="unknown relation direction"):
        project_relations(repository, direction="sideways")  # type: ignore[arg-type]
