import pytest

from kneekura_tech_hub.queries import QueryError, problems_solved_by, requirements_for, solutions_for_problem
from kneekura_tech_hub.repository import MemoryRepository
from kneekura_tech_hub.service import CurationEngine, CurationError


HUMAN = {"actor_type": "human", "actor_id": "reviewer"}
AI = {"actor_type": "ai", "actor_id": "extractor", "version": "test"}


def entity(entity_id: str, kind: str = "technique") -> dict:
    return {
        "record_type": "knowledge_entity",
        "id": entity_id,
        "canonical_name": entity_id,
        "aliases": [],
        "kinds": [kind],
        "abstraction_level": "L1",
        "identity_state": "CANONICAL",
        "relations": [],
    }


def relation_claim(
    claim_id: str,
    source: str,
    relation_type: str,
    target: str,
    maturity: str,
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
        "created_by": AI,
        "policy_version": "1.0.0",
    }


def query_repository() -> MemoryRepository:
    repository = MemoryRepository()
    for record in (
        entity("ke:solution-a"),
        entity("ke:solution-b"),
        entity("ke:problem", "problem"),
        entity("ke:memo"),
        relation_claim("cl:solves-a", "ke:solution-a", "solves", "ke:problem", "VALIDATED"),
        relation_claim("cl:solves-b", "ke:solution-b", "solves", "ke:problem", "CANDIDATE"),
        relation_claim("cl:requires", "ke:solution-a", "requires", "ke:memo", "VALIDATED"),
    ):
        repository.put(record)
    return repository


def test_problem_queries_use_explicit_relation_claims_and_maturity_views():
    repository = query_repository()

    trusted = solutions_for_problem(repository, "ke:problem", view="validated")
    research = solutions_for_problem(repository, "ke:problem", view="research")
    solved = problems_solved_by(repository, "ke:solution-a", view="validated")
    requirements = requirements_for(repository, "ke:solution-a", view="validated")

    assert [item["solution"]["id"] for item in trusted] == ["ke:solution-a"]
    assert {item["solution"]["id"] for item in research} == {
        "ke:solution-a",
        "ke:solution-b",
    }
    assert [item["problem"]["id"] for item in solved] == ["ke:problem"]
    assert [item["requirement"]["id"] for item in requirements] == ["ke:memo"]
    assert trusted[0]["relation_claim"]["evidence_ids"] == ["ev:test"]


def test_solutions_query_requires_explicit_problem_classification():
    repository = query_repository()

    with pytest.raises(QueryError, match="not classified as a problem"):
        solutions_for_problem(repository, "ke:solution-a", view="research")


def test_corrupt_solves_edge_to_non_problem_fails_closed():
    repository = MemoryRepository()
    repository.put(entity("ke:solution"))
    repository.put(entity("ke:not-problem"))
    repository.put(
        relation_claim(
            "cl:bad-solves",
            "ke:solution",
            "solves",
            "ke:not-problem",
            "VALIDATED",
        )
    )

    with pytest.raises(QueryError, match="not classified as a problem"):
        problems_solved_by(repository, "ke:solution", view="validated")


def test_curation_engine_rejects_solves_target_that_is_not_a_problem():
    engine = CurationEngine(MemoryRepository())
    engine.register_source(
        {
            "record_type": "source",
            "id": "src:problem-gate",
            "kind": "repository",
            "origin": {"provider": "github", "repository": "example/problem-gate"},
            "acquisition": {"level": "snapshot"},
            "license": {"state": "KNOWN", "declared_expression": "MIT"},
        },
        actor=HUMAN,
    )
    engine.register_source_snapshot(
        {
            "record_type": "source_snapshot",
            "id": "ss:problem-gate",
            "source_id": "src:problem-gate",
            "revision": "0123456789abcdef",
            "captured_at": "2026-09-09T00:00:00Z",
        },
        actor=HUMAN,
    )
    engine.register_evidence(
        {
            "record_type": "evidence",
            "id": "ev:problem-gate",
            "source_id": "src:problem-gate",
            "source_snapshot_id": "ss:problem-gate",
            "locator": {
                "type": "source_lines",
                "path": "README.md",
                "line_start": 1,
                "line_end": 2,
                "content_hash": "sha256:problem-gate",
            },
            "roles": ["SUPPORTS"],
        },
        actor=HUMAN,
    )
    engine.create_entity(entity("ke:solution"), actor=HUMAN)
    engine.create_entity(entity("ke:not-problem"), actor=HUMAN)
    engine.create_entity(entity("ke:actual-problem", "problem"), actor=HUMAN)

    bad = relation_claim(
        "cl:bad",
        "ke:solution",
        "solves",
        "ke:not-problem",
        "CANDIDATE",
    )
    bad["evidence_ids"] = ["ev:problem-gate"]
    bad["reasoning_basis"] = ["ev:problem-gate"]
    with pytest.raises(CurationError, match="classified as a problem"):
        engine.create_claim(bad, actor=AI)

    good = relation_claim(
        "cl:good",
        "ke:solution",
        "solves",
        "ke:actual-problem",
        "CANDIDATE",
    )
    good["evidence_ids"] = ["ev:problem-gate"]
    good["reasoning_basis"] = ["ev:problem-gate"]
    engine.create_claim(good, actor=AI)
    assert engine.get("cl:good") is not None
