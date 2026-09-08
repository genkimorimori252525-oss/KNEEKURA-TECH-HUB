from __future__ import annotations

import json
from copy import deepcopy
from hashlib import sha256
from typing import Any, Callable

from .discovery import DiscoveryIntakeError, preflight_discovery_intake
from .github_adapter import GitHubDiscoveryAdapterError, build_metadata_discovery_batch
from .repository import Record


MAX_QUERIES = 32
MAX_PAGES_PER_QUERY = 10
MAX_REQUESTS = 100
MAX_UNIQUE_SOURCES = 1000


class DiscoveryRunError(ValueError):
    """Raised when a bounded discovery run cannot be executed safely."""


FetchPage = Callable[[str, int, int, str | None, str | None], dict[str, Any]]


def _fingerprint(value: Any) -> str:
    encoded = json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return "sha256:" + sha256(encoded).hexdigest()


def _validate_actor(actor: Record) -> Record:
    if actor.get("actor_type") not in {"human", "ai", "tool", "system"}:
        raise DiscoveryRunError("discovered_by requires a supported actor_type")
    extra = sorted(set(actor) - {"actor_type", "actor_id", "version"})
    if extra:
        raise DiscoveryRunError(f"discovered_by has unsupported fields: {extra!r}")
    return dict(actor)


def _validate_query(item: dict[str, Any], index: int) -> dict[str, Any]:
    query_id = item.get("query_id")
    query = item.get("query")
    page_count = item.get("page_count", 1)
    per_page = item.get("per_page", 100)
    search_sort = item.get("sort")
    search_order = item.get("order")

    if not isinstance(query_id, str) or not query_id.startswith("query:"):
        raise DiscoveryRunError(f"queries[{index}] requires query_id beginning query:")
    if not isinstance(query, str) or not query.strip():
        raise DiscoveryRunError(f"queries[{index}] requires a non-empty query")
    if not isinstance(page_count, int) or not 1 <= page_count <= MAX_PAGES_PER_QUERY:
        raise DiscoveryRunError(
            f"queries[{index}].page_count must be between 1 and {MAX_PAGES_PER_QUERY}"
        )
    if not isinstance(per_page, int) or not 1 <= per_page <= 100:
        raise DiscoveryRunError(f"queries[{index}].per_page must be between 1 and 100")
    if search_sort is not None and search_sort not in {
        "stars",
        "forks",
        "help-wanted-issues",
        "updated",
    }:
        raise DiscoveryRunError(f"queries[{index}] has unsupported sort")
    if search_order is not None and search_order not in {"asc", "desc"}:
        raise DiscoveryRunError(f"queries[{index}] has unsupported order")

    return {
        "query_id": query_id,
        "query": query.strip(),
        "page_count": page_count,
        "per_page": per_page,
        "sort": search_sort,
        "order": search_order,
    }


def _run_hash(spec: dict[str, Any], source_ids: list[str]) -> str:
    material = {
        "run_version": spec["run_version"],
        "queries": spec["queries"],
        "max_unique_sources": spec["max_unique_sources"],
        "source_ids": source_ids,
    }
    return sha256(
        json.dumps(material, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()[:20]


def execute_bounded_discovery_run(
    spec: dict[str, Any],
    *,
    fetch_page: FetchPage,
) -> dict[str, Any]:
    """Execute a bounded multi-query GitHub discovery run without writing Hub data.

    The result is one metadata-only Controlled Discovery batch. Repositories found through
    multiple query/page paths are stored once, while every accepted discovery path is retained
    under ``origin.discovery_hits``.
    """

    if spec.get("run_version") != "1.0":
        raise DiscoveryRunError("run_version must be 1.0")
    actor = _validate_actor(spec.get("discovered_by") or {})
    discovered_at = spec.get("discovered_at")
    if not isinstance(discovered_at, str):
        raise DiscoveryRunError("discovered_at is required")

    raw_queries = spec.get("queries")
    if not isinstance(raw_queries, list) or not raw_queries:
        raise DiscoveryRunError("queries must be a non-empty array")
    if len(raw_queries) > MAX_QUERIES:
        raise DiscoveryRunError(f"query count exceeds {MAX_QUERIES}")

    queries = [_validate_query(item, index) for index, item in enumerate(raw_queries)]
    query_ids = [item["query_id"] for item in queries]
    if len(query_ids) != len(set(query_ids)):
        raise DiscoveryRunError("query_id values must be unique")

    request_count = sum(item["page_count"] for item in queries)
    if request_count > MAX_REQUESTS:
        raise DiscoveryRunError(f"request count exceeds {MAX_REQUESTS}")

    max_unique_sources = spec.get("max_unique_sources", MAX_UNIQUE_SOURCES)
    if not isinstance(max_unique_sources, int) or not 1 <= max_unique_sources <= MAX_UNIQUE_SOURCES:
        raise DiscoveryRunError(
            f"max_unique_sources must be between 1 and {MAX_UNIQUE_SOURCES}"
        )

    unique: dict[str, Record] = {}
    source_order: list[str] = []
    page_receipts: list[dict[str, Any]] = []
    duplicate_hits = 0
    truncated = False

    for query_spec in queries:
        for page in range(1, query_spec["page_count"] + 1):
            if len(unique) >= max_unique_sources:
                truncated = True
                break

            try:
                payload = fetch_page(
                    query_spec["query"],
                    page,
                    query_spec["per_page"],
                    query_spec["sort"],
                    query_spec["order"],
                )
                page_batch = build_metadata_discovery_batch(
                    payload,
                    query=query_spec["query"],
                    discovered_by=actor,
                    discovered_at=discovered_at,
                    page=page,
                    max_records=min(query_spec["per_page"], max_unique_sources),
                    search_sort=query_spec["sort"],
                    search_order=query_spec["order"],
                )
            except GitHubDiscoveryAdapterError as exc:
                raise DiscoveryRunError(
                    f"query {query_spec['query_id']} page {page} failed: {exc}"
                ) from exc

            accepted_on_page = 0
            for accepted_position, source in enumerate(page_batch["records"], start=1):
                source_id = source["id"]
                fingerprint = _fingerprint(source["origin"])
                hit = {
                    "query_id": query_spec["query_id"],
                    "query": query_spec["query"],
                    "page": page,
                    "accepted_position": accepted_position,
                    "api_sort": query_spec["sort"],
                    "api_order": query_spec["order"],
                    "page_batch_id": page_batch["batch_id"],
                    "metadata_fingerprint": fingerprint,
                }

                if source_id in unique:
                    duplicate_hits += 1
                    unique[source_id]["origin"].setdefault("discovery_hits", []).append(hit)
                    continue

                if len(unique) >= max_unique_sources:
                    truncated = True
                    break

                stored = deepcopy(source)
                stored["origin"]["discovery_hits"] = [hit]
                unique[source_id] = stored
                source_order.append(source_id)
                accepted_on_page += 1

            page_receipts.append(
                {
                    "query_id": query_spec["query_id"],
                    "page": page,
                    "page_batch_id": page_batch["batch_id"],
                    "page_source_count": len(page_batch["records"]),
                    "new_unique_source_count": accepted_on_page,
                    "api_total_count": page_batch["scope"]["filters"].get("api_total_count"),
                    "api_incomplete_results": page_batch["scope"]["filters"].get(
                        "api_incomplete_results"
                    ),
                }
            )

            if truncated:
                break
        if truncated:
            break

    if not source_order:
        raise DiscoveryRunError("discovery run produced no public repository Sources")

    normalized_spec = {
        "run_version": "1.0",
        "queries": queries,
        "max_unique_sources": max_unique_sources,
    }
    run_digest = _run_hash(normalized_spec, source_order)
    batch = {
        "intake_version": "1.0",
        "batch_id": f"discovery:github-run:{run_digest}",
        "discovered_by": actor,
        "discovered_at": discovered_at,
        "scope": {
            "provider": "github",
            "query": None,
            "selection_basis": (
                "bounded GitHub query-set provider order; no popularity-based Hub ranking"
            ),
            "filters": {
                "orchestrator": "bounded-discovery-run-v1",
                "metadata_only": True,
                "public_only": True,
                "query_count": len(queries),
                "planned_request_count": request_count,
                "executed_request_count": len(page_receipts),
                "max_unique_sources": max_unique_sources,
                "unique_source_count": len(source_order),
                "duplicate_hit_count": duplicate_hits,
                "truncated": truncated,
                "queries": queries,
                "pages": page_receipts,
            },
        },
        "records": [unique[source_id] for source_id in source_order],
    }

    try:
        preflight_discovery_intake(batch)
    except DiscoveryIntakeError as exc:
        raise DiscoveryRunError(f"run produced invalid Controlled Discovery batch: {exc}") from exc
    return batch
