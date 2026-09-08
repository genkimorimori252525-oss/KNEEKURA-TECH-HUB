import pytest

from kneekura_tech_hub.validator import HubValidationError, validate_record


def test_direct_canonical_relation_write_is_rejected_until_provenance_exists():
    record = {
        "record_type": "knowledge_entity",
        "id": "ke:child",
        "canonical_name": "Child Technique",
        "aliases": [],
        "kinds": ["technique"],
        "abstraction_level": "L1",
        "identity_state": "CANONICAL",
        "relations": [
            {"type": "derived_from", "target": "ke:parent"},
        ],
    }

    with pytest.raises(HubValidationError, match="relation provenance"):
        validate_record(record)
