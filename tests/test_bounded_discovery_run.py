from __future__ import annotations

from copy import deepcopy

import pytest

from kneekura_tech_hub.discovery import preflight_discovery_intake
from kneekura_tech_hub.discovery_run import DiscoveryRunError, execute_bounded_discovery_run


ACTOR = {"actor_type": "tool", "actor_id": "run-test", "version": "1.0"}


def _item(name: str, stars: int = 0) -> dict:
    return {
        "id": abs(hash(name)) % 100000,
        "full_name": name,
        "html_url": f"https://github.com/{name}",
        "private": False,
        "visibility": "public",
        "default_branch": "main",
        "stargazers_count": stars,
        "forks_count": 0,
        "open_issues_count": 0,
    }


def _spec() -> dict:
    return {
        "run_version": "1.0",
        "discovered_by": ACTOR,
        "discovered_at": "2026-09-09T06:30:00+09:00",
        "max_unique_sources": 10,
        "queries": [
            {
                "query_id": "query:incremental",
                "query": "incremental analysis",
                "page_count": 2,
                "per_page": 100,
            },
            {
                "query_id": "query:parsing",
                "query": "incremental parsing",
                "page_count": 1,
                "per_page": 100,
                "sort": "updated",
                "order": "desc",
            },
        ],
    }


def test_run_deduplicates_sources_but_preserves_every_discovery_hit():
    pages = {
        ("incremental analysis", 1): [_item("example/alpha", 7), _item("example/shared", 50)],
        ("incremental analysis", 2): [_item("example/beta", 9)],
        ("incremental parsing", 1): [_item("example/shared", 51), _item("example/gamma", 2)],
    }

    def fetch(query, page, per_page, sort, order):
        return {"total_count": 5, "incomplete_results": False, "items": deepcopy(pages[(query, page)])}

    batch = execute_bounded_discovery_run(_spec(), fetch_page=fetch)

    assert [item["id"] for item in batch["records"]] == [
        "src:github:example:alpha",
        "src:github:example:shared",
        "src:github:example:beta",
        "src:github:example:gamma",
    ]
    shared = next(item for item in batch["records"] if item["id"].endswith(":shared"))
    hits = shared["origin"]["discovery_hits"]
    assert [hit["query_id"] for hit in hits] == ["query:incremental", "query:parsing"]
    assert hits[0]["metadata_fingerprint"] != hits[1]["metadata_fingerprint"]

    filters = batch["scope"]["filters"]
    assert filters["query_count"] == 2
    assert filters["executed_request_count"] == 3
    assert filters["unique_source_count"] == 4
    assert filters["duplicate_hit_count"] == 1
    assert filters["truncated"] is False
    assert filters["queries"][1]["sort"] == "updated"
    assert filters["queries"][1]["order"] == "desc"

    assert all(item["record_type"] == "source" for item in batch["records"])
    assert all(item["acquisition"]["level"] == "metadata-only" for item in batch["records"])
    assert all(item["license"]["state"] == "REVIEW_REQUIRED" for item in batch["records"])
    assert {item["id"] for item in preflight_discovery_intake(batch)} == {
        item["id"] for item in batch["records"]
    }


def test_run_stops_at_unique_source_cap_without_fetching_later_requests():
    spec = _spec()
    spec["max_unique_sources"] = 2
    calls: list[tuple[str, int]] = []

    def fetch(query, page, per_page, sort, order):
        calls.append((query, page))
        return {
            "total_count": 100,
            "items": [_item("example/one"), _item("example/two"), _item("example/three")],
        }

    batch = execute_bounded_discovery_run(spec, fetch_page=fetch)

    assert len(batch["records"]) == 2
    assert batch["scope"]["filters"]["truncated"] is True
    assert calls == [("incremental analysis", 1)]


def test_run_rejects_unbounded_or_duplicate_query_specs_before_fetch():
    spec = _spec()
    spec["queries"][1]["query_id"] = "query:incremental"
    called = False

    def fetch(*args):
        nonlocal called
        called = True
        return {"items": []}

    with pytest.raises(DiscoveryRunError, match="query_id values must be unique"):
        execute_bounded_discovery_run(spec, fetch_page=fetch)
    assert called is False

    too_many = _spec()
    too_many["queries"][0]["page_count"] = 11
    with pytest.raises(DiscoveryRunError, match="page_count"):
        execute_bounded_discovery_run(too_many, fetch_page=fetch)

    too_large = _spec()
    too_large["max_unique_sources"] = 1001
    with pytest.raises(DiscoveryRunError, match="max_unique_sources"):
        execute_bounded_discovery_run(too_large, fetch_page=fetch)
