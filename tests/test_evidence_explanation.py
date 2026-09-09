from copy import deepcopy

import pytest

from kneekura_tech_hub.explanation import (
    ExplanationError,
    explain_claim,
    explain_relation_result,
)
from kneekura_tech_hub.repository import MemoryRepository


def source(source_id: str = "src:test") -> dict:
    return {
        "record_type": "source",
        "id": source_id,
        "kind": "repository",
        "origin": {"provider": "github", "repository": "example/repo"},
        "acquisition": {"level": "snapshot"},
        "license": {"state": "KNOWN", "declared_expression": "MIT"},
    }


def snapshot(snapshot_id: str = "ss:test", source_id: str = "src:test") -> dict:
    return {
        "record_type": "source_snapshot",
        "id": snapshot_id,
        "source_id": source_id,
        "revision": "0123456789abcdef",
        "captured_at": "2026-09-09T00:00:00Z",
    }


def evidence(evidence_id: str, line: int, *, source_id: str = "src:test", snapshot_id: str = "ss:test") -> dict:
    return {
        "record_type": "evidence",
        "id": evidence_id,
        "source_id": source_id,
        "source_snapshot_id": snapshot_id,
        "locator": {
            "type": "source_lines",
            "path": "src/lib.rs",
            "line_start": line,
            "line_end": line,
            "content_hash": f"sha256:{evidence_id}",
        },
        "roles": ["SUPPORTS"],
    }


def claim() -> dict:
    return {
        "record_type": "claim",
        "id": "cl:test",
        "entity_id": "ke:test",
        "claim_type": "INFERENCE",
        "statement": "The technique reduces repeated work.",
        "maturity": "CANDIDATE",
        "evidence_ids": ["ev:second", "ev:first"],
        "confidence": "MEDIUM",
        "reasoning_basis": ["ev:second", "ev:first"],
        "created_by": {"actor_type": "ai", "actor_id": "extractor"},
        "policy_version": "1.0.0",
    }


def seeded_repository() -> MemoryRepository:
    repository = MemoryRepository()
    for record in (
        source(),
        snapshot(),
        evidence("ev:first", 10),
        evidence("ev:second", 20),
        claim(),
    ):
        repository.put(record)
    return repository


def test_explain_claim_preserves_claim_evidence_order_and_full_chain():
    repository = seeded_repository()

    explanation = explain_claim(repository, "cl:test")

    assert explanation["claim"]["id"] == "cl:test"
    assert explanation["evidence_count"] == 2
    assert [item["evidence"]["id"] for item in explanation["evidence_chains"]] == [
        "ev:second",
        "ev:first",
    ]
    for item in explanation["evidence_chains"]:
        assert item["source_snapshot"]["id"] == "ss:test"
        assert item["source"]["id"] == "src:test"


def test_explanation_is_read_only():
    repository = seeded_repository()
    before = deepcopy(repository.list())

    explain_claim(repository, "cl:test")

    assert repository.list() == before


def test_missing_referenced_evidence_fails_closed():
    repository = seeded_repository()
    broken = repository.get("cl:test")
    assert broken is not None
    broken["evidence_ids"] = ["ev:missing"]
    repository.put(broken, replace=True)

    with pytest.raises(ExplanationError, match="missing evidence"):
        explain_claim(repository, "cl:test")


def test_snapshot_source_mismatch_fails_closed():
    repository = seeded_repository()
    repository.put(source("src:other"))
    repository.put(snapshot("ss:other", source_id="src:other"))
    repository.put(evidence("ev:mismatch", 30, snapshot_id="ss:other"))
    broken = repository.get("cl:test")
    assert broken is not None
    broken["evidence_ids"] = ["ev:mismatch"]
    broken["reasoning_basis"] = ["ev:mismatch"]
    repository.put(broken, replace=True)

    with pytest.raises(ExplanationError, match="different source"):
        explain_claim(repository, "cl:test")


def test_wrong_record_type_fails_closed():
    repository = seeded_repository()
    repository.put(
        {
            "record_type": "knowledge_entity",
            "id": "cl:not-a-claim",
            "canonical_name": "Wrong type",
            "aliases": [],
            "kinds": ["technique"],
            "abstraction_level": "L1",
            "identity_state": "CANONICAL",
            "relations": [],
        }
    )

    with pytest.raises(ExplanationError, match="expected claim"):
        explain_claim(repository, "cl:not-a-claim")


def test_relation_query_result_can_be_explained_by_claim_id():
    repository = seeded_repository()
    result = {
        "solution": {"id": "ke:a"},
        "problem": {"id": "ke:b"},
        "relation_claim": {"claim_id": "cl:test", "maturity": "CANDIDATE"},
    }

    explanation = explain_relation_result(repository, result)

    assert explanation["claim"]["id"] == "cl:test"
    assert explanation["evidence_count"] == 2


def test_relation_result_without_claim_id_is_rejected():
    repository = seeded_repository()

    with pytest.raises(ExplanationError, match="claim_id"):
        explain_relation_result(repository, {"relation_claim": {}})
