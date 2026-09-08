from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path

import pytest

from kneekura_tech_hub.discovery import preflight_discovery_intake
from kneekura_tech_hub.github_adapter import (
    GitHubDiscoveryAdapterError,
    build_metadata_discovery_batch,
)


ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "tests" / "fixtures" / "github_repository_search_v1.json"
ACTOR = {"actor_type": "tool", "actor_id": "github-adapter-test", "version": "1.0"}


def _payload() -> dict:
    return json.loads(FIXTURE.read_text(encoding="utf-8"))


def test_adapter_emits_only_metadata_sources_and_preserves_provider_order():
    batch = build_metadata_discovery_batch(
        _payload(),
        query="incremental analysis",
        discovered_by=ACTOR,
        discovered_at="2026-09-09T06:00:00+09:00",
    )

    assert batch["discovered_by"] == ACTOR
    assert [record["id"] for record in batch["records"]] == [
        "src:github:example:small-but-relevant",
        "src:github:example:huge-star-repo",
    ]
    assert all(record["record_type"] == "source" for record in batch["records"])
    assert all(record["acquisition"] == {"level": "metadata-only"} for record in batch["records"])
    assert all(record["license"]["state"] == "REVIEW_REQUIRED" for record in batch["records"])

    # A huge star count is metadata only. The adapter does not reorder provider results.
    assert batch["records"][0]["origin"]["stargazers_count"] == 7
    assert batch["records"][1]["origin"]["stargazers_count"] == 900000
    assert batch["scope"]["filters"]["duplicate_source_count"] == 1
    assert "rank" not in batch["records"][0]
    assert "score" not in batch["records"][0]

    # The adapter output is accepted by the Controlled Discovery gate as-is.
    assert preflight_discovery_intake(batch) == batch["records"]


def test_search_api_license_is_only_a_hint_not_a_verified_expression():
    batch = build_metadata_discovery_batch(
        _payload(),
        query="incremental analysis",
        discovered_by=ACTOR,
        discovered_at="2026-09-09T06:00:00Z",
    )
    first = batch["records"][0]

    assert first["origin"]["github_license_hint"]["spdx_id"] == "MIT"
    assert first["license"] == {
        "state": "REVIEW_REQUIRED",
        "declared_expression": None,
        "handling_policy": "DISCOVERY_METADATA_ONLY",
    }


def test_batch_id_is_stable_for_same_query_page_and_provider_order():
    kwargs = {
        "query": "incremental analysis",
        "discovered_by": ACTOR,
        "discovered_at": "2026-09-09T06:00:00Z",
        "page": 2,
    }
    first = build_metadata_discovery_batch(_payload(), **kwargs)
    second = build_metadata_discovery_batch(deepcopy(_payload()), **kwargs)
    assert first["batch_id"] == second["batch_id"]


def test_adapter_rejects_empty_results_and_malformed_repository_identity():
    with pytest.raises(GitHubDiscoveryAdapterError, match="no usable repositories"):
        build_metadata_discovery_batch(
            {"total_count": 0, "items": []},
            query="incremental analysis",
            discovered_by=ACTOR,
        )

    malformed = _payload()
    malformed["items"] = [
        {
            "full_name": "not-owner-name",
            "html_url": "https://github.com/not-owner-name",
        }
    ]
    with pytest.raises(GitHubDiscoveryAdapterError, match="invalid GitHub full_name"):
        build_metadata_discovery_batch(
            malformed,
            query="incremental analysis",
            discovered_by=ACTOR,
        )


def test_adapter_rejects_naive_discovery_timestamp():
    with pytest.raises(GitHubDiscoveryAdapterError, match="include a timezone"):
        build_metadata_discovery_batch(
            _payload(),
            query="incremental analysis",
            discovered_by=ACTOR,
            discovered_at="2026-09-09T06:00:00",
        )


def test_max_records_is_bounded_by_controlled_intake_limit():
    with pytest.raises(GitHubDiscoveryAdapterError, match="between 1 and 1000"):
        build_metadata_discovery_batch(
            _payload(),
            query="incremental analysis",
            discovered_by=ACTOR,
            max_records=1001,
        )
