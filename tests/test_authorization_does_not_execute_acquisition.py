from __future__ import annotations

import pytest

from kneekura_tech_hub.authorization import AcquisitionAuthorizationEngine
from kneekura_tech_hub.discovery import DiscoveryIntakeError, preflight_discovery_intake
from kneekura_tech_hub.repository import MemoryRepository
from kneekura_tech_hub.selection import SourceSelectionEngine


HUMAN = {"actor_type": "human", "actor_id": "reviewer"}
CRAWLER = {"actor_type": "ai", "actor_id": "crawler", "version": "1.0"}
SOURCE_ID = "src:github:example:authorized-not-executed"
SHA = "0123456789abcdef0123456789abcdef01234567"


def test_authorization_record_does_not_unlock_discovery_snapshot_write():
    repository = MemoryRepository()
    repository.put(
        {
            "record_type": "source",
            "id": SOURCE_ID,
            "kind": "repository",
            "origin": {
                "provider": "github",
                "repository": "example/authorized-not-executed",
                "url": "https://github.com/example/authorized-not-executed",
            },
            "acquisition": {"level": "metadata-only"},
            "license": {
                "state": "KNOWN",
                "declared_expression": "MIT",
                "handling_policy": "REFERENCE_ONLY",
            },
        }
    )
    selection = SourceSelectionEngine(repository).create_from_fields(
        source_id=SOURCE_ID,
        decision="SELECT_FOR_REVIEW",
        rationale="Review exact README content at a pinned revision.",
        actor=HUMAN,
        decision_id="sd:authorized-not-executed",
    )
    AcquisitionAuthorizationEngine(repository).authorize_from_fields(
        source_id=SOURCE_ID,
        selection_decision_id=selection["id"],
        revision=SHA,
        allowed_paths=["README.md"],
        rationale="Authorization exists, but execution remains a separate future layer.",
        actor=HUMAN,
        authorization_id="aa:authorized-not-executed",
    )

    assert repository.get(SOURCE_ID)["acquisition"] == {"level": "metadata-only"}

    attempted_execution = {
        "intake_version": "1.0",
        "batch_id": "discovery:authorization-is-not-execution",
        "discovered_by": CRAWLER,
        "discovered_at": "2026-09-09T00:00:00Z",
        "scope": {"provider": "github", "query": "authorized source"},
        "records": [
            {
                "record_type": "source_snapshot",
                "id": "ss:github:example:authorized-not-executed:01234567",
                "source_id": SOURCE_ID,
                "revision": SHA,
                "captured_at": "2026-09-09T00:00:00Z",
            }
        ],
    }

    with pytest.raises(DiscoveryIntakeError, match="metadata-only"):
        preflight_discovery_intake(attempted_execution, repository=repository)

    assert repository.get(SOURCE_ID)["acquisition"] == {"level": "metadata-only"}
    assert repository.get("ss:github:example:authorized-not-executed:01234567") is None
