from __future__ import annotations

import json
from pathlib import Path

import pytest

from kneekura_tech_hub.discovery import DiscoveryIntakeError, preflight_discovery_intake


ROOT = Path(__file__).resolve().parents[1]
PILOT = ROOT / "pilots" / "controlled-discovery-intake-v1.json"


def _batch() -> dict:
    return json.loads(PILOT.read_text(encoding="utf-8"))


def test_snapshot_timestamp_must_include_timezone():
    batch = _batch()
    for record in batch["records"]:
        if record["record_type"] == "source_snapshot":
            record["captured_at"] = "2026-09-09T00:00:00"
            snapshot_id = record["id"]
            break

    with pytest.raises(DiscoveryIntakeError, match=rf"{snapshot_id}\.captured_at.*timezone"):
        preflight_discovery_intake(batch)


def test_evidence_observed_at_must_be_valid_timezone_aware_time():
    batch = _batch()
    for record in batch["records"]:
        if record["record_type"] == "evidence":
            record["observed_at"] = "not-a-time"
            evidence_id = record["id"]
            break

    with pytest.raises(DiscoveryIntakeError, match=rf"{evidence_id}\.observed_at.*timezone"):
        preflight_discovery_intake(batch)


@pytest.mark.parametrize("license_state", ["CONFLICT", "REVIEW_REQUIRED"])
def test_ambiguous_license_state_cannot_acquire_selected_files(license_state: str):
    batch = _batch()
    for record in batch["records"]:
        if record.get("id") == "src:github:salsa-rs:salsa":
            record["license"]["state"] = license_state
            break

    with pytest.raises(DiscoveryIntakeError, match=rf"{license_state}.*metadata-only"):
        preflight_discovery_intake(batch)


@pytest.mark.parametrize("license_state", ["UNKNOWN", "CONFLICT", "REVIEW_REQUIRED"])
def test_restricted_license_state_can_enter_as_metadata_only_source(license_state: str):
    batch = {
        "intake_version": "1.0",
        "batch_id": f"discovery:license:{license_state.lower()}",
        "discovered_by": {"actor_type": "tool", "actor_id": "github-search"},
        "discovered_at": "2026-09-09T00:00:00Z",
        "scope": {"provider": "github", "query": "candidate"},
        "records": [
            {
                "record_type": "source",
                "id": "src:github:example:license-review",
                "kind": "repository",
                "origin": {
                    "provider": "github",
                    "repository": "example/license-review"
                },
                "acquisition": {"level": "metadata-only"},
                "license": {
                    "state": license_state,
                    "handling_policy": "REFERENCE_ONLY"
                }
            }
        ]
    }

    ordered = preflight_discovery_intake(batch)
    assert [record["id"] for record in ordered] == ["src:github:example:license-review"]
