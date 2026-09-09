from pathlib import Path

import pytest

from kneekura_tech_hub.repository import MemoryRepository


MIGRATION = Path("migrations/0023_source_identity_integrity.sql")
SOURCE_ID = "src:contract:source-identity"


def _source() -> dict:
    return {
        "record_type": "source",
        "id": SOURCE_ID,
        "kind": "repository",
        "origin": {
            "provider": "github",
            "repository": "example/source-identity",
            "url": "https://github.com/example/source-identity",
            "description": "initial description",
        },
        "acquisition": {"level": "metadata-only"},
        "license": {"state": "REVIEW_REQUIRED"},
    }


def test_migration_pins_stable_source_identity_and_explicit_volatile_fields() -> None:
    sql = MIGRATION.read_text(encoding="utf-8")
    assert "kthub_source_identity_payload" in sql
    assert "kthub_guard_source_identity" in sql
    assert "trg_source_identity_integrity" in sql
    assert "BEFORE UPDATE OF id, kind, origin ON source" in sql
    for key in (
        "default_branch",
        "description",
        "stargazers_count",
        "github_license_hint",
        "discovery_hits",
    ):
        assert f"'{key}'" in sql


def test_unknown_origin_key_is_stable_by_default() -> None:
    repository = MemoryRepository()
    repository.put(_source())

    changed = repository.get(SOURCE_ID)
    assert changed is not None
    changed["origin"]["future_provider_field"] = "new value"

    with pytest.raises(ValueError, match="source identity is immutable"):
        repository.put(changed, replace=True)


def test_explicit_volatile_origin_key_remains_mutable() -> None:
    repository = MemoryRepository()
    repository.put(_source())

    changed = repository.get(SOURCE_ID)
    assert changed is not None
    changed["origin"]["description"] = "fresh description"
    repository.put(changed, replace=True)

    assert repository.get(SOURCE_ID)["origin"]["description"] == "fresh description"
