from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from typing import Any

from .discovery_run import DiscoveryRunError, execute_bounded_discovery_run
from .github_adapter import GitHubDiscoveryAdapterError, fetch_repository_search_page


def _load(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise DiscoveryRunError(f"cannot read JSON: {path}") from exc
    if not isinstance(value, dict):
        raise DiscoveryRunError(f"JSON root must be an object: {path}")
    return value


def _offline_fetcher(responses: dict[str, Any]):
    pages = responses.get("pages")
    if not isinstance(pages, list):
        raise DiscoveryRunError("offline responses require a pages array")

    lookup: dict[tuple[str, int], dict[str, Any]] = {}
    for index, item in enumerate(pages):
        if not isinstance(item, dict):
            raise DiscoveryRunError(f"offline pages[{index}] must be an object")
        query = item.get("query")
        page = item.get("page")
        payload = item.get("payload")
        if not isinstance(query, str) or not isinstance(page, int) or not isinstance(payload, dict):
            raise DiscoveryRunError(
                f"offline pages[{index}] requires query, integer page, and object payload"
            )
        key = (query, page)
        if key in lookup:
            raise DiscoveryRunError(f"duplicate offline response for {query!r} page {page}")
        lookup[key] = payload

    def fetch(query: str, page: int, per_page: int, sort: str | None, order: str | None):
        key = (query, page)
        if key not in lookup:
            raise DiscoveryRunError(f"missing offline response for {query!r} page {page}")
        return lookup[key]

    return fetch


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Execute a bounded multi-query GitHub discovery run without writing Hub data"
    )
    parser.add_argument("--spec", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument(
        "--responses",
        type=Path,
        help="offline query/page response fixture; live GitHub API is used when omitted",
    )
    parser.add_argument("--token-env", default="GITHUB_TOKEN")
    args = parser.parse_args()

    try:
        spec = _load(args.spec)
        if args.responses is not None:
            fetcher = _offline_fetcher(_load(args.responses))
        else:
            token = os.getenv(args.token_env) if args.token_env else None

            def fetcher(query, page, per_page, sort, order):
                return fetch_repository_search_page(
                    query,
                    token=token,
                    per_page=per_page,
                    page=page,
                    sort=sort,
                    order=order,
                )

        batch = execute_bounded_discovery_run(spec, fetch_page=fetcher)
    except (DiscoveryRunError, GitHubDiscoveryAdapterError) as exc:
        print(f"REJECTED DISCOVERY RUN: {exc}")
        return 1

    args.output.write_text(json.dumps(batch, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    filters = batch["scope"]["filters"]
    print(
        f"WROTE {args.output} sources={filters['unique_source_count']} "
        f"requests={filters['executed_request_count']} truncated={filters['truncated']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
