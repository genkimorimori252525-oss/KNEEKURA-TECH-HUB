from __future__ import annotations

import pytest

from kneekura_tech_hub.repository import MemoryRepository
from kneekura_tech_hub.service import CurationEngine


HUMAN = {"actor_type": "human", "actor_id": "immutability-reviewer"}
AI = {"actor_type": "ai", "actor_id": "immutability-model", "version": "v1"}
SOURCE_ID = "src:immutability:memory"
SNAPSHOT_ID = "ss:immutability:memory"
EVIDENCE_ID = "ev:immutability:memory"
SECOND_EVIDENCE_ID = "ev:immutability:memory:second"
ENTITY_ID = "ke:immutability:memory"
CLAIM_ID = "cl:immutability:memory"


def _seed() -> tuple[MemoryRepository, CurationEngine]:
    repository = MemoryRepository()
    engine = CurationEngine(repository)
    engine.register_source(
        {
            "record_type": "source",
            "id": SOURCE_ID,
            "kind": "repository",
            "origin": {"provider": "fixture", "repository": "example/immutability-memory"},
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
    for evidence_id, line_start in ((EVIDENCE_ID, 1), (SECOND_EVIDENCE_ID, 3)):
        engine.register_evidence(
            {
                "record_type": "evidence",
                "id": evidence_id,
                "source_id": SOURCE_ID,
                "source_snapshot_id": SNAPSHOT_ID,
                "locator": {
                    "type": "source_lines",
                    "path": "README.md",
                    "line_start": line_start,
                    "line_end": line_start + 1,
                    "content_hash": "sha256:" + ("a" if line_start == 1 else "b") * 64,
                },
                "roles": ["SUPPORTS"],
            },
            actor=HUMAN,
        )
    engine.create_entity(
        {
            "record_type": "knowledge_entity",
            "id": ENTITY_ID,
            "canonical_name": "Reviewed Claim immutability fixture",
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
            "statement": "Original candidate statement.",
            "maturity": "CANDIDATE",
            "evidence_ids": [EVIDENCE_ID],
            "confidence": "MEDIUM",
            "reasoning_basis": [EVIDENCE_ID],
            "created_by": AI,
            "policy_version": "1.0.0",
        },
        actor=AI,
        reason="fixture candidate",
    )
    return repository, engine


def test_candidate_epistemic_content_remains_editable() -> None:
    repository, _ = _seed()
    claim = repository.get(CLAIM_ID)
    assert claim is not None
    claim["statement"] = "Revised while still Candidate."
    claim["evidence_ids"] = [EVIDENCE_ID, SECOND_EVIDENCE_ID]
    claim["reasoning_basis"] = [EVIDENCE_ID, SECOND_EVIDENCE_ID]

    repository.put(claim, replace=True)

    stored = repository.get(CLAIM_ID)
    assert stored is not None
    assert stored["statement"] == "Revised while still Candidate."
    assert stored["evidence_ids"] == [EVIDENCE_ID, SECOND_EVIDENCE_ID]


def test_reviewed_statement_and_evidence_are_immutable() -> None:
    repository, engine = _seed()
    engine.transition_claim(CLAIM_ID, "SUPPORTED", actor=HUMAN, reason="reviewed")

    for mutation in (
        {"statement": "Swap the reviewed statement without changing maturity."},
        {
            "evidence_ids": [EVIDENCE_ID, SECOND_EVIDENCE_ID],
            "reasoning_basis": [EVIDENCE_ID, SECOND_EVIDENCE_ID],
        },
    ):
        claim = repository.get(CLAIM_ID)
        assert claim is not None
        claim.update(mutation)
        with pytest.raises(ValueError, match="epistemic content is immutable"):
            repository.put(claim, replace=True)

    stored = repository.get(CLAIM_ID)
    assert stored is not None
    assert stored["statement"] == "Original candidate statement."
    assert stored["evidence_ids"] == [EVIDENCE_ID]


def test_created_by_is_immutable_even_for_candidate() -> None:
    repository, _ = _seed()
    claim = repository.get(CLAIM_ID)
    assert claim is not None
    claim["created_by"] = HUMAN

    with pytest.raises(ValueError, match="created_by is immutable"):
        repository.put(claim, replace=True)

    assert repository.get(CLAIM_ID)["created_by"] == AI


def test_content_cannot_change_in_same_update_that_leaves_candidate() -> None:
    repository, _ = _seed()
    claim = repository.get(CLAIM_ID)
    assert claim is not None
    claim["statement"] = "Changed during promotion."
    claim["maturity"] = "SUPPORTED"

    with pytest.raises(ValueError, match="epistemic content is immutable"):
        repository.put(claim, replace=True)

    stored = repository.get(CLAIM_ID)
    assert stored["maturity"] == "CANDIDATE"
    assert stored["statement"] == "Original candidate statement."
