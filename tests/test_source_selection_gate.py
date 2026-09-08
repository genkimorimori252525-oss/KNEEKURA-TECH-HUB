from __future__ import annotations

import pytest

from kneekura_tech_hub.repository import MemoryRepository
from kneekura_tech_hub.selection import (
    SourceSelectionEngine,
    SourceSelectionError,
    active_source_selection_decisions,
    selected_for_review,
    source_selection_history,
)


HUMAN = {"actor_type": "human", "actor_id": "reviewer"}
AI = {"actor_type": "ai", "actor_id": "scanner", "version": "1.0"}


def _source(source_id: str = "src:github:example:repo", *, level: str = "metadata-only") -> dict:
    return {
        "record_type": "source",
        "id": source_id,
        "kind": "repository",
        "origin": {
            "provider": "github",
            "repository": "example/repo",
            "url": "https://github.com/example/repo",
        },
        "acquisition": {"level": level},
        "license": {
            "state": "REVIEW_REQUIRED",
            "declared_expression": None,
            "handling_policy": "DISCOVERY_METADATA_ONLY",
        },
    }


def _repo() -> MemoryRepository:
    repository = MemoryRepository()
    repository.put(_source())
    return repository


def test_human_selection_is_append_only_and_does_not_upgrade_source():
    repository = _repo()
    engine = SourceSelectionEngine(repository)
    before = repository.get("src:github:example:repo")

    first = engine.create_from_fields(
        source_id="src:github:example:repo",
        decision="SELECT_FOR_REVIEW",
        rationale="Query match is worth manual metadata and license review.",
        actor=HUMAN,
        decision_id="sd:first",
    )

    assert first["decision"] == "SELECT_FOR_REVIEW"
    assert repository.get("src:github:example:repo") == before
    assert repository.get("src:github:example:repo")["acquisition"] == {"level": "metadata-only"}
    assert [item["id"] for item in active_source_selection_decisions(repository)] == ["sd:first"]
    assert selected_for_review(repository)[0]["source"] == before

    second = engine.create_from_fields(
        source_id="src:github:example:repo",
        decision="DEFER",
        rationale="Defer until license metadata is manually resolved.",
        actor=HUMAN,
        decision_id="sd:second",
        supersedes_decision_id="sd:first",
    )

    assert second["supersedes_decision_id"] == "sd:first"
    assert [item["id"] for item in source_selection_history(repository)] == ["sd:first", "sd:second"]
    assert [item["id"] for item in active_source_selection_decisions(repository)] == ["sd:second"]
    assert selected_for_review(repository) == []
    assert repository.get("src:github:example:repo") == before


def test_ai_cannot_create_canonical_source_selection_decision():
    repository = _repo()
    engine = SourceSelectionEngine(repository)

    with pytest.raises(SourceSelectionError, match="human actor"):
        engine.create_from_fields(
            source_id="src:github:example:repo",
            decision="SELECT_FOR_REVIEW",
            rationale="AI thinks this is interesting.",
            actor=AI,
        )

    assert repository.list("source_selection_decision") == []


def test_existing_active_decision_requires_explicit_supersession():
    repository = _repo()
    engine = SourceSelectionEngine(repository)
    engine.create_from_fields(
        source_id="src:github:example:repo",
        decision="SELECT_FOR_REVIEW",
        rationale="Review manually.",
        actor=HUMAN,
        decision_id="sd:first",
    )

    with pytest.raises(SourceSelectionError, match="supersede it explicitly"):
        engine.create_from_fields(
            source_id="src:github:example:repo",
            decision="REJECT_FOR_REVIEW",
            rationale="Changed judgment.",
            actor=HUMAN,
            decision_id="sd:parallel",
        )


def test_superseding_decision_must_target_same_source_and_active_predecessor():
    repository = _repo()
    repository.put(
        _source("src:github:example:other")
        | {
            "origin": {
                "provider": "github",
                "repository": "example/other",
                "url": "https://github.com/example/other",
            }
        }
    )
    engine = SourceSelectionEngine(repository)
    engine.create_from_fields(
        source_id="src:github:example:repo",
        decision="SELECT_FOR_REVIEW",
        rationale="Review.",
        actor=HUMAN,
        decision_id="sd:first",
    )

    with pytest.raises(SourceSelectionError, match="same Source"):
        engine.create_from_fields(
            source_id="src:github:example:other",
            decision="DEFER",
            rationale="Wrong predecessor.",
            actor=HUMAN,
            decision_id="sd:wrong-source",
            supersedes_decision_id="sd:first",
        )

    engine.create_from_fields(
        source_id="src:github:example:repo",
        decision="DEFER",
        rationale="Correct successor.",
        actor=HUMAN,
        decision_id="sd:second",
        supersedes_decision_id="sd:first",
    )

    with pytest.raises(SourceSelectionError, match="active decision"):
        engine.create_from_fields(
            source_id="src:github:example:repo",
            decision="REJECT_FOR_REVIEW",
            rationale="Cannot branch from history.",
            actor=HUMAN,
            decision_id="sd:branch",
            supersedes_decision_id="sd:first",
        )


def test_v1_selection_gate_rejects_sources_already_deeper_than_metadata_only():
    repository = MemoryRepository()
    repository.put(_source(level="selected-files"))
    engine = SourceSelectionEngine(repository)

    with pytest.raises(SourceSelectionError, match="metadata-only Sources"):
        engine.create_from_fields(
            source_id="src:github:example:repo",
            decision="SELECT_FOR_REVIEW",
            rationale="This layer must not govern an already-deep Source.",
            actor=HUMAN,
        )
