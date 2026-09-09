from __future__ import annotations

from copy import deepcopy

import pytest

from kneekura_tech_hub.observation_triage import (
    ObservationTriageError,
    observation_context,
    observation_duplicate_candidates,
    triage_queue,
    validate_observation_triage_decision,
)
from kneekura_tech_hub.repository import MemoryRepository


SOURCE_ID = "src:triage:fixture"
SNAPSHOT_ID = "ss:triage:fixture"
EVIDENCE_ID = "ev:triage:fixture"


def _seed_repository() -> MemoryRepository:
    repository = MemoryRepository()
    repository.put(
        {
            "record_type": "source",
            "id": SOURCE_ID,
            "kind": "repository",
            "origin": {"provider": "fixture", "repository": "example/triage"},
            "acquisition": {"level": "selected-files"},
            "license": {"state": "KNOWN", "declared_expression": "MIT"},
        }
    )
    repository.put(
        {
            "record_type": "source_snapshot",
            "id": SNAPSHOT_ID,
            "source_id": SOURCE_ID,
            "revision": "0123456789abcdef0123456789abcdef01234567",
            "captured_at": "2026-09-09T00:00:00Z",
            "metadata": {"fixture": True},
        }
    )
    repository.put(
        {
            "record_type": "evidence",
            "id": EVIDENCE_ID,
            "source_id": SOURCE_ID,
            "source_snapshot_id": SNAPSHOT_ID,
            "locator": {
                "type": "source_lines",
                "path": "README.md",
                "line_start": 1,
                "line_end": 1,
                "content_hash": "sha256:" + "a" * 64,
            },
            "roles": ["SUPPORTS"],
            "observed_at": "2026-09-09T00:00:01Z",
        }
    )
    return repository


def _observation(
    observation_id: str,
    *,
    status: str = "NEW",
    actor_id: str = "extractor-a",
    summary: str = "The implementation performs incremental recomputation.",
    candidate_names: list[str] | None = None,
) -> dict:
    return {
        "record_type": "staged_observation",
        "id": observation_id,
        "source_id": SOURCE_ID,
        "evidence_candidate_ids": [EVIDENCE_ID],
        "summary": summary,
        "candidate_names": candidate_names or ["incremental recomputation"],
        "status": status,
        "created_by": {"actor_type": "ai", "actor_id": actor_id, "version": "v1"},
    }


def test_exact_duplicate_grouping_ignores_creator_status_and_id_without_merging() -> None:
    repository = _seed_repository()
    first = _observation("obs:triage:a", status="NEW", actor_id="extractor-a")
    second = _observation("obs:triage:b", status="TRIAGED", actor_id="extractor-b")
    repository.put(first)
    repository.put(second)

    grouped = observation_duplicate_candidates(repository)

    assert len(grouped["exact_content_groups"]) == 1
    assert grouped["exact_content_groups"][0]["observation_ids"] == [
        "obs:triage:a",
        "obs:triage:b",
    ]
    assert repository.get("obs:triage:a") == first
    assert repository.get("obs:triage:b") == second


def test_shared_evidence_group_is_only_a_candidate_not_semantic_equivalence() -> None:
    repository = _seed_repository()
    repository.put(_observation("obs:triage:a"))
    repository.put(
        _observation(
            "obs:triage:b",
            summary="The same lines may instead describe cache invalidation.",
            candidate_names=["cache invalidation"],
        )
    )

    grouped = observation_duplicate_candidates(repository)

    assert grouped["exact_content_groups"] == []
    assert len(grouped["shared_evidence_groups"]) == 1
    assert grouped["shared_evidence_groups"][0]["content_signature_count"] == 2
    assert grouped["shared_evidence_groups"][0]["observation_ids"] == [
        "obs:triage:a",
        "obs:triage:b",
    ]


def test_triage_queue_excludes_terminal_statuses_and_reconstructs_provenance() -> None:
    repository = _seed_repository()
    repository.put(_observation("obs:triage:new", status="NEW"))
    repository.put(_observation("obs:triage:triaged", status="TRIAGED", actor_id="extractor-b"))
    repository.put(_observation("obs:triage:rejected", status="REJECTED", actor_id="extractor-c"))

    queue = triage_queue(repository)

    assert [item["observation"]["id"] for item in queue] == [
        "obs:triage:new",
        "obs:triage:triaged",
    ]
    context = observation_context(repository, "obs:triage:new")
    assert context["source"]["id"] == SOURCE_ID
    assert context["source_snapshot"]["id"] == SNAPSHOT_ID
    assert [item["id"] for item in context["evidence"]] == [EVIDENCE_ID]
    assert context["triage_decisions"] == []


def test_context_rejects_cross_source_evidence_corruption() -> None:
    repository = _seed_repository()
    corrupted = _observation("obs:triage:corrupt")
    repository.put(corrupted)
    evidence = repository.get(EVIDENCE_ID)
    assert evidence is not None
    evidence["source_id"] = "src:other"
    repository.put(evidence, replace=True)

    with pytest.raises(ObservationTriageError, match="Source mismatch"):
        observation_context(repository, corrupted["id"])


def test_triage_decision_schema_rejects_ai_and_claim_on_nonpromotion() -> None:
    base = {
        "record_type": "observation_triage_decision",
        "id": "otd:fixture",
        "observation_id": "obs:triage:a",
        "action": "MARK_TRIAGED",
        "from_status": "NEW",
        "to_status": "TRIAGED",
        "reason": "Evidence and candidate name are ready for human review.",
        "created_by": {"actor_type": "tool", "actor_id": "triage-tool", "version": "v1"},
        "policy_version": "1.0.0",
        "decided_at": "2026-09-09T00:00:00Z",
    }
    validate_observation_triage_decision(base)

    ai = deepcopy(base)
    ai["created_by"] = {"actor_type": "ai", "actor_id": "extractor"}
    with pytest.raises(ObservationTriageError):
        validate_observation_triage_decision(ai)

    smuggled_claim = deepcopy(base)
    smuggled_claim["resulting_claim_id"] = "cl:smuggled"
    with pytest.raises(ObservationTriageError):
        validate_observation_triage_decision(smuggled_claim)
