from __future__ import annotations

import pytest

from kneekura_tech_hub.repository import MemoryRepository
from kneekura_tech_hub.service import CurationEngine, CurationError


HUMAN = {"actor_type": "human", "actor_id": "reviewer"}
AI = {"actor_type": "ai", "actor_id": "extractor", "version": "v1"}


def _engine() -> CurationEngine:
    engine = CurationEngine(MemoryRepository())
    engine.register_source(
        {
            "record_type": "source",
            "id": "src:stage-guard",
            "kind": "repository",
            "origin": {"provider": "fixture", "repository": "example/stage-guard"},
            "acquisition": {"level": "selected-files"},
            "license": {"state": "KNOWN", "declared_expression": "MIT"},
        },
        actor=HUMAN,
    )
    engine.register_source_snapshot(
        {
            "record_type": "source_snapshot",
            "id": "ss:stage-guard",
            "source_id": "src:stage-guard",
            "revision": "0123456789abcdef0123456789abcdef01234567",
            "captured_at": "2026-09-09T00:00:00Z",
            "metadata": {},
        },
        actor=HUMAN,
    )
    engine.register_evidence(
        {
            "record_type": "evidence",
            "id": "ev:stage-guard",
            "source_id": "src:stage-guard",
            "source_snapshot_id": "ss:stage-guard",
            "locator": {
                "type": "source_lines",
                "path": "README.md",
                "line_start": 1,
                "line_end": 1,
                "content_hash": "sha256:" + "a" * 64,
            },
            "roles": ["SUPPORTS"],
        },
        actor=HUMAN,
    )
    return engine


def _observation(status: str) -> dict:
    return {
        "record_type": "staged_observation",
        "id": f"obs:stage-guard:{status.lower()}",
        "source_id": "src:stage-guard",
        "evidence_candidate_ids": ["ev:stage-guard"],
        "summary": "Candidate technique from exact evidence.",
        "candidate_names": ["candidate technique"],
        "status": status,
        "created_by": AI,
    }


def test_new_observation_is_accepted() -> None:
    engine = _engine()
    stored = engine.stage_observation(_observation("NEW"), actor=AI)
    assert stored["status"] == "NEW"


@pytest.mark.parametrize("status", ["TRIAGED", "PROMOTED", "REJECTED", "EXPIRED"])
def test_new_observation_cannot_smuggle_terminal_or_reviewed_status(status: str) -> None:
    engine = _engine()
    with pytest.raises(CurationError, match="must start at NEW"):
        engine.stage_observation(_observation(status), actor=AI)
    assert engine.list("staged_observation") == []
