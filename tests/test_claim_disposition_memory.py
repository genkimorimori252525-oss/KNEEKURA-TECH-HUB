from __future__ import annotations

import pytest

from kneekura_tech_hub.claim_disposition import dispose_claim
from kneekura_tech_hub.repository import MemoryRepository
from kneekura_tech_hub.service import CurationEngine


HUMAN = {"actor_type": "human", "actor_id": "memory-reviewer"}
AI = {"actor_type": "ai", "actor_id": "memory-model", "version": "v1"}
SOURCE_ID = "src:disposition:memory"
SNAPSHOT_ID = "ss:disposition:memory"
EVIDENCE_ID = "ev:disposition:memory"
ENTITY_ID = "ke:disposition:memory"
CLAIM_ID = "cl:disposition:memory"


def _seed(repository: MemoryRepository) -> CurationEngine:
    engine = CurationEngine(repository)
    engine.register_source(
        {
            "record_type": "source",
            "id": SOURCE_ID,
            "kind": "repository",
            "origin": {"provider": "fixture", "repository": "example/disposition-memory"},
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
                "content_hash": "sha256:" + "e" * 64,
            },
            "roles": ["SUPPORTS"],
        },
        actor=HUMAN,
    )
    engine.create_entity(
        {
            "record_type": "knowledge_entity",
            "id": ENTITY_ID,
            "canonical_name": "Memory disposition parity fixture",
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
            "statement": "The memory backend preserves the disposition boundary.",
            "maturity": "CANDIDATE",
            "evidence_ids": [EVIDENCE_ID],
            "confidence": "MEDIUM",
            "reasoning_basis": [EVIDENCE_ID],
            "created_by": HUMAN,
            "policy_version": "1.0.0",
        },
        actor=HUMAN,
        reason="memory disposition fixture",
    )
    return engine


def _support(repository: MemoryRepository) -> None:
    CurationEngine(repository).transition_claim(
        CLAIM_ID,
        "SUPPORTED",
        actor=HUMAN,
        reason="human support review",
        support_review={"decision_id": "csd:disposition:memory"},
    )


def test_memory_candidate_rejection_remains_lightweight_for_ai() -> None:
    repository = MemoryRepository()
    engine = _seed(repository)

    rejected = engine.transition_claim(
        CLAIM_ID,
        "REJECTED",
        actor=AI,
        reason="discard weak candidate",
    )

    assert rejected["maturity"] == "REJECTED"
    assert repository.list("claim_disposition_decision") == []


def test_memory_direct_reviewed_rejection_requires_disposition_decision() -> None:
    repository = MemoryRepository()
    _seed(repository)
    _support(repository)

    bypass = repository.get(CLAIM_ID)
    assert bypass is not None
    bypass["maturity"] = "REJECTED"

    with pytest.raises(ValueError, match="requires matching human disposition decision"):
        repository.put(bypass, replace=True)

    assert repository.get(CLAIM_ID)["maturity"] == "SUPPORTED"
    assert repository.list("claim_disposition_decision") == []


def test_memory_orphan_disposition_decision_is_rejected_and_rolled_back() -> None:
    source_repository = MemoryRepository()
    _seed(source_repository)
    _support(source_repository)
    successful = dispose_claim(
        source_repository,
        CLAIM_ID,
        "REJECTED",
        actor=HUMAN,
        reason="human terminal review",
        decision_id="cdd:disposition:memory:orphan-template",
    )

    target_repository = MemoryRepository()
    _seed(target_repository)
    _support(target_repository)

    with pytest.raises(ValueError, match="requires matching terminal Claim state"):
        target_repository.put(successful["decision"])

    assert target_repository.get(CLAIM_ID)["maturity"] == "SUPPORTED"
    assert target_repository.get(successful["decision"]["id"]) is None


def test_memory_dispose_claim_commits_decision_and_terminal_state_together() -> None:
    repository = MemoryRepository()
    _seed(repository)
    _support(repository)

    result = dispose_claim(
        repository,
        CLAIM_ID,
        "REJECTED",
        actor=HUMAN,
        reason="human reviewed terminal disposition",
        decision_id="cdd:disposition:memory",
    )

    assert result["claim"]["maturity"] == "REJECTED"
    assert result["decision"]["from_maturity"] == "SUPPORTED"
    assert result["decision"]["to_maturity"] == "REJECTED"
    assert repository.get("cdd:disposition:memory") == result["decision"]
    assert repository._transaction_depth == 0


def test_memory_failed_transaction_restores_records_and_depth() -> None:
    repository = MemoryRepository()
    _seed(repository)
    _support(repository)
    before = repository.list()

    with pytest.raises(RuntimeError, match="synthetic rollback"):
        with repository.transaction():
            claim = repository.get(CLAIM_ID)
            assert claim is not None
            claim["verification_due_at"] = "2026-09-10T00:00:00Z"
            repository.put(claim, replace=True)
            raise RuntimeError("synthetic rollback")

    assert repository.list() == before
    assert repository._transaction_depth == 0
