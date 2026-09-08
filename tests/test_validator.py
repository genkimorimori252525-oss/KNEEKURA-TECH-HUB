import pytest

from kneekura_tech_hub.validator import HubValidationError, validate_record


def test_direct_observation_requires_evidence():
    record = {
        "record_type": "claim",
        "id": "cl:test",
        "entity_id": "ke:test",
        "claim_type": "DIRECT_OBSERVATION",
        "statement": "A class exists at the pinned revision.",
        "maturity": "SUPPORTED",
        "evidence_ids": [],
        "created_by": {"actor_type": "human"},
        "policy_version": "1.0.0",
    }
    with pytest.raises(HubValidationError, match="requires at least one evidence_id"):
        validate_record(record)


def test_ai_cannot_validate_claim():
    record = {
        "record_type": "claim",
        "id": "cl:test",
        "entity_id": "ke:test",
        "claim_type": "INFERENCE",
        "statement": "The design may reduce repeated work.",
        "maturity": "VALIDATED",
        "evidence_ids": ["ev:test"],
        "confidence": "MEDIUM",
        "reasoning_basis": ["ev:test"],
        "created_by": {"actor_type": "ai", "version": "test-model"},
        "policy_version": "1.0.0",
    }
    with pytest.raises(HubValidationError, match="cannot be VALIDATED"):
        validate_record(record)


def test_unknown_license_blocks_full_source():
    record = {
        "record_type": "source",
        "id": "src:test",
        "kind": "repository",
        "origin": {"url": "https://example.invalid/repo"},
        "acquisition": {"level": "full-source"},
        "license": {"state": "UNKNOWN"},
    }
    with pytest.raises(HubValidationError, match="metadata-only"):
        validate_record(record)


def test_automatic_entity_merge_is_rejected():
    record = {
        "record_type": "curation_event",
        "id": "ce:test",
        "operation": "ENTITY_MERGE",
        "actor": {"actor_type": "ai", "version": "test-model"},
        "subject_ids": ["ke:a", "ke:b"],
        "policy_version": "1.0.0",
        "occurred_at": "2026-09-09T00:00:00Z",
        "reversible": True,
    }
    with pytest.raises(HubValidationError, match="requires a human actor"):
        validate_record(record)


def test_valid_human_supported_observation_passes():
    record = {
        "record_type": "claim",
        "id": "cl:test",
        "entity_id": "ke:test",
        "claim_type": "DIRECT_OBSERVATION",
        "statement": "A class exists at the pinned revision.",
        "maturity": "SUPPORTED",
        "evidence_ids": ["ev:test"],
        "created_by": {"actor_type": "human"},
        "policy_version": "1.0.0",
    }
    validate_record(record)
