from __future__ import annotations

import pytest

from kneekura_tech_hub.discovery import DiscoveryIntakeError, preflight_discovery_intake
from kneekura_tech_hub.repository import MemoryRepository


ACTOR = {"actor_type": "ai", "actor_id": "crawler", "version": "test"}


def test_existing_metadata_only_source_cannot_receive_new_discovery_observation():
    repository = MemoryRepository()
    repository.put(
        {
            "record_type": "source",
            "id": "src:github:example:legacy",
            "kind": "repository",
            "origin": {"provider": "github", "repository": "example/legacy"},
            "acquisition": {"level": "metadata-only"},
            "license": {"state": "KNOWN", "declared_expression": "MIT"},
        }
    )
    # Historical state may predate the controlled-intake acquisition guard.
    repository.put(
        {
            "record_type": "source_snapshot",
            "id": "ss:github:example:legacy:abc123",
            "source_id": "src:github:example:legacy",
            "revision": "abc123",
            "captured_at": "2026-09-08T00:00:00Z",
        }
    )
    repository.put(
        {
            "record_type": "evidence",
            "id": "ev:legacy",
            "source_id": "src:github:example:legacy",
            "source_snapshot_id": "ss:github:example:legacy:abc123",
            "locator": {"type": "stable_url", "url": "https://github.com/example/legacy"},
            "roles": ["SUPPORTS"],
        }
    )

    batch = {
        "intake_version": "1.0",
        "batch_id": "discovery:legacy-observation",
        "discovered_by": ACTOR,
        "discovered_at": "2026-09-09T00:00:00Z",
        "scope": {"provider": "github", "query": "legacy"},
        "records": [
            {
                "record_type": "staged_observation",
                "id": "obs:legacy:new",
                "source_id": "src:github:example:legacy",
                "evidence_candidate_ids": ["ev:legacy"],
                "summary": "A new discovery observation must not deepen a metadata-only source.",
                "candidate_names": ["Legacy Candidate"],
                "status": "NEW",
                "created_by": ACTOR,
            }
        ],
    }

    with pytest.raises(DiscoveryIntakeError, match="metadata-only"):
        preflight_discovery_intake(batch, repository=repository)
