from copy import deepcopy

import pytest

from kneekura_tech_hub.comparison import (
    ComparisonError,
    claim_subject_key,
    compare_claim,
    comparison_groups,
)
from kneekura_tech_hub.repository import MemoryRepository


def _repository() -> MemoryRepository:
    repository = MemoryRepository()
    records = [
        {
            "record_type": "source",
            "id": "src:a",
            "kind": "repository",
            "origin": {"provider": "github", "repository": "example/a"},
            "acquisition": {"level": "snapshot"},
            "license": {"state": "KNOWN", "declared_expression": "MIT"},
        },
        {
            "record_type": "source",
            "id": "src:b",
            "kind": "repository",
            "origin": {"provider": "github", "repository": "example/b"},
            "acquisition": {"level": "snapshot"},
            "license": {"state": "KNOWN", "declared_expression": "MIT"},
        },
        {
            "record_type": "source_snapshot",
            "id": "ss:a",
            "source_id": "src:a",
            "revision": "aaaaaaaa",
            "captured_at": "2026-09-09T00:00:00Z",
        },
        {
            "record_type": "source_snapshot",
            "id": "ss:b",
            "source_id": "src:b",
            "revision": "bbbbbbbb",
            "captured_at": "2026-09-09T00:00:00Z",
        },
        {
            "record_type": "evidence",
            "id": "ev:support",
            "source_id": "src:a",
            "source_snapshot_id": "ss:a",
            "locator": {
                "type": "source_lines",
                "path": "README.md",
                "line_start": 1,
                "line_end": 1,
                "content_hash": "sha256:support",
            },
            "roles": ["SUPPORTS"],
        },
        {
            "record_type": "evidence",
            "id": "ev:refute",
            "source_id": "src:b",
            "source_snapshot_id": "ss:b",
            "locator": {
                "type": "source_lines",
                "path": "README.md",
                "line_start": 2,
                "line_end": 2,
                "content_hash": "sha256:refute",
            },
            "roles": ["REFUTES"],
        },
        {
            "record_type": "claim",
            "id": "cl:entity:a",
            "entity_id": "ke:technique",
            "claim_type": "INFERENCE",
            "statement": "The technique reduces repeated work.",
            "maturity": "SUPPORTED",
            "evidence_ids": ["ev:support"],
            "confidence": "MEDIUM",
            "reasoning_basis": ["ev:support"],
            "created_by": {"actor_type": "ai", "actor_id": "a"},
            "policy_version": "1.0.0",
        },
        {
            "record_type": "claim",
            "id": "cl:entity:b",
            "entity_id": "ke:technique",
            "claim_type": "JUDGMENT",
            "statement": "The technique may increase maintenance cost.",
            "maturity": "CHALLENGED",
            "evidence_ids": ["ev:refute"],
            "created_by": {"actor_type": "human", "actor_id": "reviewer"},
            "policy_version": "1.0.0",
        },
        {
            "record_type": "claim",
            "id": "cl:entity:old",
            "entity_id": "ke:technique",
            "claim_type": "INFERENCE",
            "statement": "The technique reduces repeated work.",
            "maturity": "SUPERSEDED",
            "evidence_ids": ["ev:support"],
            "confidence": "MEDIUM",
            "reasoning_basis": ["ev:support"],
            "superseded_by": "cl:entity:a",
            "created_by": {"actor_type": "ai", "actor_id": "old"},
            "policy_version": "1.0.0",
        },
        {
            "record_type": "claim",
            "id": "cl:relation:a",
            "relation": {
                "source_entity_id": "ke:solution",
                "relation_type": "solves",
                "target_entity_id": "ke:problem",
            },
            "claim_type": "INFERENCE",
            "statement": "The solution addresses the problem.",
            "maturity": "CANDIDATE",
            "evidence_ids": ["ev:support"],
            "confidence": "MEDIUM",
            "reasoning_basis": ["ev:support"],
            "created_by": {"actor_type": "ai", "actor_id": "rel-a"},
            "policy_version": "1.0.0",
        },
        {
            "record_type": "claim",
            "id": "cl:relation:requires",
            "relation": {
                "source_entity_id": "ke:solution",
                "relation_type": "requires",
                "target_entity_id": "ke:problem",
            },
            "claim_type": "INFERENCE",
            "statement": "Different relation subject.",
            "maturity": "CANDIDATE",
            "evidence_ids": ["ev:support"],
            "confidence": "MEDIUM",
            "reasoning_basis": ["ev:support"],
            "created_by": {"actor_type": "ai", "actor_id": "rel-b"},
            "policy_version": "1.0.0",
        },
    ]
    for record in records:
        repository.put(record)
    return repository


def test_entity_claims_are_grouped_by_exact_subject_without_winner_selection():
    repository = _repository()

    group = compare_claim(repository, "cl:entity:a")

    assert group["subject"] == {"kind": "entity", "entity_id": "ke:technique"}
    assert group["claim_count"] == 3
    assert group["active_claim_count"] == 2
    assert group["active_claim_ids"] == ["cl:entity:a", "cl:entity:b"]
    assert group["needs_review"] is True
    assert "MULTIPLE_CLAIMS" in group["flags"]
    assert "MULTIPLE_ACTIVE_CLAIMS" in group["flags"]
    assert "STATEMENTS_DIFFER" in group["flags"]
    assert "EPISTEMIC_TYPES_DIFFER" in group["flags"]
    assert "MATURITIES_DIFFER" in group["flags"]
    assert "HAS_CHALLENGED_CLAIM" in group["flags"]
    assert "HAS_REFUTING_EVIDENCE" in group["flags"]
    assert "HAS_SUPERSEDED_CLAIM" in group["flags"]

    # The system reports disagreement signals but does not invent a contradiction verdict.
    assert all("CONTRADICTION" not in flag for flag in group["flags"])
    assert "winner" not in group
    assert "preferred_claim_id" not in group


def test_each_competing_claim_keeps_its_own_evidence_review():
    group = compare_claim(_repository(), "cl:entity:b")
    by_id = {item["claim"]["id"]: item for item in group["claims"]}

    assert by_id["cl:entity:a"]["review"]["evidence"]["role_counts"] == {"SUPPORTS": 1}
    assert by_id["cl:entity:b"]["review"]["evidence"]["role_counts"] == {"REFUTES": 1}
    assert "HAS_REFUTING_EVIDENCE" in by_id["cl:entity:b"]["review"]["flags"]


def test_exact_relation_subject_includes_relation_type():
    repository = _repository()

    solves = compare_claim(repository, "cl:relation:a")
    requires = compare_claim(repository, "cl:relation:requires")

    assert solves["claim_count"] == 1
    assert solves["subject"]["relation_type"] == "solves"
    assert requires["claim_count"] == 1
    assert requires["subject"]["relation_type"] == "requires"


def test_group_filters_are_explicit_not_ranked():
    repository = _repository()

    multiple = comparison_groups(repository, multiple_only=True)
    review = comparison_groups(repository, needs_review_only=True)

    assert len(multiple) == 1
    assert multiple[0]["subject"] == {"kind": "entity", "entity_id": "ke:technique"}
    assert len(review) == 3
    assert all(group["needs_review"] for group in review)
    assert all("score" not in group for group in review)


def test_comparison_is_read_only():
    repository = _repository()
    before = deepcopy(repository.list())

    compare_claim(repository, "cl:entity:a")
    comparison_groups(repository)

    assert repository.list() == before


def test_claim_subject_key_rejects_ambiguous_subject():
    with pytest.raises(ComparisonError, match="ambiguous or missing"):
        claim_subject_key(
            {
                "record_type": "claim",
                "id": "cl:bad",
                "entity_id": "ke:a",
                "relation": {
                    "source_entity_id": "ke:a",
                    "relation_type": "related_to",
                    "target_entity_id": "ke:b",
                },
            }
        )


def test_missing_claim_is_rejected():
    with pytest.raises(ComparisonError, match="missing claim"):
        compare_claim(_repository(), "cl:missing")
