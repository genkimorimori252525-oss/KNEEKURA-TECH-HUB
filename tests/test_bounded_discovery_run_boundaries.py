from __future__ import annotations

import pytest

from kneekura_tech_hub.discovery_run import DiscoveryRunError, execute_bounded_discovery_run


ACTOR = {"actor_type": "tool", "actor_id": "run-boundary-test", "version": "1.0"}


def _item(name: str) -> dict:
    return {
        "id": 1,
        "full_name": name,
        "html_url": f"https://github.com/{name}",
        "private": False,
        "visibility": "public",
    }


def _spec() -> dict:
    return {
        "run_version": "1.0",
        "discovered_by": ACTOR,
        "discovered_at": "2026-09-09T06:30:00+09:00",
        "queries": [
            {
                "query_id": "query:alpha",
                "query": "alpha",
                "page_count": 3,
                "per_page": 100,
            },
            {
                "query_id": "query:beta",
                "query": "beta",
                "page_count": 1,
                "per_page": 100,
            },
        ],
    }


def test_empty_page_ends_only_that_query_and_later_queries_still_run():
    calls: list[tuple[str, int]] = []

    def fetch(query, page, per_page, sort, order):
        calls.append((query, page))
        if (query, page) == ("alpha", 1):
            return {"total_count": 1, "items": [_item("example/alpha")]}
        if (query, page) == ("alpha", 2):
            return {"total_count": 1, "items": []}
        if query == "beta":
            return {"total_count": 1, "items": [_item("example/beta")]}
        raise AssertionError("alpha page 3 must not be fetched after an empty page")

    batch = execute_bounded_discovery_run(_spec(), fetch_page=fetch)

    assert calls == [("alpha", 1), ("alpha", 2), ("beta", 1)]
    assert [record["id"] for record in batch["records"]] == [
        "src:github:example:alpha",
        "src:github:example:beta",
    ]
    pages = batch["scope"]["filters"]["pages"]
    empty = next(item for item in pages if item["query_id"] == "query:alpha" and item["page"] == 2)
    assert empty["empty"] is True
    assert batch["scope"]["filters"]["executed_request_count"] == 3


def test_run_rejects_naive_timestamp_before_fetch():
    spec = _spec()
    spec["discovered_at"] = "2026-09-09T06:30:00"
    called = False

    def fetch(*args):
        nonlocal called
        called = True
        return {"items": []}

    with pytest.raises(DiscoveryRunError, match="timezone"):
        execute_bounded_discovery_run(spec, fetch_page=fetch)
    assert called is False
