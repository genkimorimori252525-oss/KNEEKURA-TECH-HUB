import pytest

from kneekura_tech_hub.repository import MemoryRepository
from kneekura_tech_hub.service import CurationEngine, CurationError
from kneekura_tech_hub.validator import HubValidationError, validate_record


HUMAN = {"actor_type": "human", "actor_id": "reviewer"}
AI = {"actor_type": "ai", "actor_id": "extractor", "version": "test"}


def test_source_lines_evidence_requires_exact_locator_fields():
    record = {
        "record_type": "evidence",
        "id": "ev:weak",
        "source_id": "src:test",
        "source_snapshot_id": "ss:test",
        "locator": {"type": "source_lines", "path": "src/a.py"},
        "roles": ["SUPPORTS"],
    }

    with pytest.raises(HubValidationError, match="line_start, line_end, content_hash"):
        validate_record(record)


def test_source_lines_evidence_rejects_reversed_line_range():
    record = {
        "record_type": "evidence",
        "id": "ev:range",
        "source_id": "src:test",
        "source_snapshot_id": "ss:test",
        "locator": {
            "type": "source_lines",
            "path": "src/a.py",
            "line_start": 20,
            "line_end": 10,
            "content_hash": "sha256:test",
        },
        "roles": ["SUPPORTS"],
    }

    with pytest.raises(HubValidationError, match="line_end"):
        validate_record(record)


def test_claim_created_by_cannot_spoof_human_actor():
    repository = MemoryRepository()
    engine = CurationEngine(repository)

    engine.register_source(
        {
            "record_type": "source",
            "id": "src:test",
            "kind": "repository",
            "origin": {"provider": "github", "repository": "example/repo"},
            "acquisition": {"level": "snapshot"},
            "license": {"state": "KNOWN", "declared_expression": "MIT"},
        },
        actor=HUMAN,
    )
    engine.register_source_snapshot(
        {
            "record_type": "source_snapshot",
            "id": "ss:test",
            "source_id": "src:test",
            "revision": "0123456789abcdef",
            "captured_at": "2026-09-09T00:00:00Z",
        },
        actor=HUMAN,
    )
    engine.create_entity(
        {
            "record_type": "knowledge_entity",
            "id": "ke:test",
            "canonical_name": "Test Technique",
            "aliases": [],
            "kinds": ["technique"],
            "abstraction_level": "L1",
            "identity_state": "CANONICAL",
            "relations": [],
        },
        actor=HUMAN,
    )
    engine.register_evidence(
        {
            "record_type": "evidence",
            "id": "ev:test",
            "source_id": "src:test",
            "source_snapshot_id": "ss:test",
            "locator": {
                "type": "source_lines",
                "path": "src/a.py",
                "line_start": 1,
                "line_end": 2,
                "content_hash": "sha256:test",
            },
            "roles": ["SUPPORTS"],
        },
        actor=HUMAN,
    )

    forged_claim = {
        "record_type": "claim",
        "id": "cl:forged",
        "entity_id": "ke:test",
        "claim_type": "DIRECT_OBSERVATION",
        "statement": "A source path exists.",
        "maturity": "CANDIDATE",
        "evidence_ids": ["ev:test"],
        "created_by": HUMAN,
        "policy_version": "1.0.0",
    }

    with pytest.raises(CurationError, match="acting identity"):
        engine.create_claim(forged_claim, actor=AI)
