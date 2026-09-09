from __future__ import annotations

import pytest

from kneekura_tech_hub.queries import QueryError, contextual_claims_for_entity
from kneekura_tech_hub.repository import MemoryRepository


ENTITY_ID = "ke:live-conflict:indentation-character-policy"
GO_CLAIM = "cl:live-conflict:indentation:go-tabs"
PY_CLAIM = "cl:live-conflict:indentation:python-spaces"
RUST_CANDIDATE = "cl:context:indentation:rust-candidate"


def _claim(
    claim_id: str,
    statement: str,
    *,
    maturity: str,
    ecosystem: str,
    authority: str,
) -> dict:
    return {
        "record_type": "claim",
        "id": claim_id,
        "entity_id": ENTITY_ID,
        "claim_type": "AUTHOR_CLAIM",
        "statement": statement,
        "maturity": maturity,
        "scope": {
            "decision": "indentation-character",
            "comparison": "language-style-policy",
            "question": "tabs-or-spaces",
        },
        "applicability": {
            "domain": "source-code",
            "ecosystem": ecosystem,
            "authority": authority,
            "typed_marker": True,
        },
        "evidence_ids": [],
        "created_by": {"actor_type": "ai", "actor_id": "context-query-fixture", "version": "v1"},
        "policy_version": "1.0.0",
    }


def _repository() -> MemoryRepository:
    repository = MemoryRepository()
    repository.put(
        {
            "record_type": "knowledge_entity",
            "id": ENTITY_ID,
            "canonical_name": "Source-code indentation character policy",
            "aliases": ["Tabs versus spaces policy"],
            "kinds": ["design-decision", "style-policy"],
            "abstraction_level": "L1",
            "identity_state": "CANONICAL",
            "relations": [],
        }
    )
    repository.put(
        _claim(
            GO_CLAIM,
            "Go's canonical gofmt formatter uses tabs for indentation and blanks for alignment.",
            maturity="VALIDATED",
            ecosystem="Go",
            authority="gofmt",
        )
    )
    repository.put(
        _claim(
            PY_CLAIM,
            "Python PEP 8 prefers spaces for indentation.",
            maturity="VALIDATED",
            ecosystem="Python",
            authority="PEP 8",
        )
    )
    repository.put(
        _claim(
            RUST_CANDIDATE,
            "A research-only Rust indentation candidate exists.",
            maturity="CANDIDATE",
            ecosystem="Rust",
            authority="fixture",
        )
    )
    return repository


def test_exact_context_selects_only_the_matching_validated_claim() -> None:
    repository = _repository()

    go = contextual_claims_for_entity(repository, ENTITY_ID, context={"ecosystem": "Go"})
    assert go["resolution"] == "ONE_MATCH"
    assert go["candidate_claim_ids"] == [GO_CLAIM]
    assert go["candidate_count"] == 1
    assert go["claims"][0]["applicability"]["authority"] == "gofmt"
    assert "winner" not in go
    assert "preferred_claim_id" not in go
    assert "score" not in go

    python = contextual_claims_for_entity(repository, ENTITY_ID, context={"ecosystem": "Python"})
    assert python["resolution"] == "ONE_MATCH"
    assert python["candidate_claim_ids"] == [PY_CLAIM]
    assert python["candidate_count"] == 1
    assert python["claims"][0]["applicability"]["authority"] == "PEP 8"


def test_context_matching_is_exact_subset_matching_not_semantic_guessing() -> None:
    repository = _repository()

    exact = contextual_claims_for_entity(
        repository,
        ENTITY_ID,
        context={"ecosystem": "Go", "authority": "gofmt"},
    )
    assert exact["resolution"] == "ONE_MATCH"
    assert exact["candidate_claim_ids"] == [GO_CLAIM]

    wrong_case = contextual_claims_for_entity(repository, ENTITY_ID, context={"ecosystem": "go"})
    assert wrong_case["resolution"] == "NO_MATCH"
    assert wrong_case["candidate_claim_ids"] == []

    impossible_mix = contextual_claims_for_entity(
        repository,
        ENTITY_ID,
        context={"ecosystem": "Go", "authority": "PEP 8"},
    )
    assert impossible_mix["resolution"] == "NO_MATCH"
    assert impossible_mix["candidate_claim_ids"] == []

    # Exact JSON-shaped comparison must not inherit Python's True == 1 behavior.
    boolean_marker = contextual_claims_for_entity(repository, ENTITY_ID, context={"typed_marker": True})
    assert boolean_marker["resolution"] == "MULTIPLE_MATCHES"
    assert boolean_marker["candidate_claim_ids"] == sorted([GO_CLAIM, PY_CLAIM])

    integer_marker = contextual_claims_for_entity(repository, ENTITY_ID, context={"typed_marker": 1})
    assert integer_marker["resolution"] == "NO_MATCH"
    assert integer_marker["candidate_claim_ids"] == []

    # Research-only Claims are never promoted into trusted guidance by this query.
    rust = contextual_claims_for_entity(repository, ENTITY_ID, context={"ecosystem": "Rust"})
    assert rust["resolution"] == "NO_MATCH"
    assert rust["candidate_claim_ids"] == []


def test_missing_or_broad_context_never_forces_a_single_recommendation() -> None:
    repository = _repository()

    missing = contextual_claims_for_entity(repository, ENTITY_ID)
    assert missing["resolution"] == "CONTEXT_REQUIRED"
    assert missing["candidate_claim_ids"] == sorted([GO_CLAIM, PY_CLAIM])
    assert missing["candidate_count"] == 2
    assert "winner" not in missing
    assert "preferred_claim_id" not in missing

    broad = contextual_claims_for_entity(repository, ENTITY_ID, context={"domain": "source-code"})
    assert broad["resolution"] == "MULTIPLE_MATCHES"
    assert broad["candidate_claim_ids"] == sorted([GO_CLAIM, PY_CLAIM])
    assert broad["candidate_count"] == 2
    assert "winner" not in broad
    assert "preferred_claim_id" not in broad


def test_query_is_read_only_and_fails_closed_for_unknown_subject_or_bad_context() -> None:
    repository = _repository()
    before = repository.list()

    with pytest.raises(QueryError, match="unknown knowledge entity"):
        contextual_claims_for_entity(repository, "ke:missing", context={"ecosystem": "Go"})

    with pytest.raises(QueryError, match="context must be a mapping"):
        contextual_claims_for_entity(repository, ENTITY_ID, context=["Go"])  # type: ignore[arg-type]

    with pytest.raises(QueryError, match="context keys must be strings"):
        contextual_claims_for_entity(repository, ENTITY_ID, context={1: "Go"})  # type: ignore[dict-item]

    assert repository.list() == before
