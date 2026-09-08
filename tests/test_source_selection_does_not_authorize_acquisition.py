from __future__ import annotations

import pytest

from kneekura_tech_hub.discovery import DiscoveryIntakeError, preflight_discovery_intake
from kneekura_tech_hub.repository import MemoryRepository
from kneekura_tech_hub.selection import SourceSelectionEngine


HUMAN = {"actor_type": "human", "actor_id": "selection-reviewer"}
CRAWLER = {"actor_type": "ai", "actor_id": "crawler", "version": "1.0"}
SOURCE_ID = "src:github:example:selected-but-metadata-only"


def test_select_for_review_does_not_unlock_snapshot_or_evidence_acquisition():
    repository = MemoryRepository()
    repository.put(
        {
            "record_type": "source",
            "id": SOURCE_ID,
            "kind": "repository",
            "origin": {
                "provider": "github",
                "repository": "example/selected-but-metadata-only",
                "url": "https://github.com/example/selected-but-metadata-only",
            },
            "acquisition": {"level": "metadata-only"},
            "license": {"state": "KNOWN", "declared_expression": "MIT"},
        }
    )

    SourceSelectionEngine(repository).create_from_fields(
        source_id=SOURCE_ID,
        decision="SELECT_FOR_REVIEW",
        rationale="Worth manual review, but not yet authorized for file acquisition.",
        actor=HUMAN,
        decision_id="sd:selected-but-not-authorized",
    )

    assert repository.get(SOURCE_ID)["acquisition"] == {"level": "metadata-only"}

    attempted_deepening = {
        "intake_version": "1.0",
        "batch_id": "discovery:selected-does-not-authorize",
        "discovered_by": CRAWLER,
        "discovered_at": "2026-09-09T00:00:00Z",
        "scope": {"provider": "github", "query": "selected source"},
        "records": [
            {
                "record_type": "source_snapshot",
                "id": "ss:github:example:selected-but-metadata-only:abc123",
                "source_id": SOURCE_ID,
                "revision": "abc123",
                "captured_at": "2026-09-09T00:00:00Z",
            }
        ],
    }

    with pytest.raises(DiscoveryIntakeError, match="metadata-only"):
        preflight_discovery_intake(attempted_deepening, repository=repository)

    assert repository.get(SOURCE_ID)["acquisition"] == {"level": "metadata-only"}
    assert repository.get("ss:github:example:selected-but-metadata-only:abc123") is None
