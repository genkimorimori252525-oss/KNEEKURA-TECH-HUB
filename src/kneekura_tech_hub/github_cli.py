from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

from .github_adapter import (
    GitHubDiscoveryAdapterError,
    build_metadata_discovery_batch,
    fetch_repository_search_page,
    load_search_payload,
)


def _actor(args: argparse.Namespace) -> dict[str, str]:
    actor: dict[str, str] = {"actor_type": args.actor_type}
    if args.actor_id:
        actor["actor_id"] = args.actor_id
    if args.actor_version:
        actor["version"] = args.actor_version
    return actor


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Build a metadata-only KNEEKURA Controlled Discovery batch from GitHub repository search"
        )
    )
    parser.add_argument("--query", required=True)
    parser.add_argument("--input-json", type=Path, help="offline GitHub Search API response fixture")
    parser.add_argument("--output", type=Path, help="write batch JSON to this path; stdout otherwise")
    parser.add_argument("--page", type=int, default=1)
    parser.add_argument("--per-page", type=int, default=100)
    parser.add_argument("--max-records", type=int, default=100)
    parser.add_argument("--sort", choices=["stars", "forks", "help-wanted-issues", "updated"])
    parser.add_argument("--order", choices=["asc", "desc"])
    parser.add_argument("--token-env", default="GITHUB_TOKEN")
    parser.add_argument("--actor-type", choices=["human", "ai", "tool", "system"], default="tool")
    parser.add_argument("--actor-id", default="github-discovery-adapter")
    parser.add_argument("--actor-version", default="1.0")
    parser.add_argument("--discovered-at")
    args = parser.parse_args()

    try:
        if args.input_json is not None:
            payload = load_search_payload(args.input_json)
        else:
            payload = fetch_repository_search_page(
                args.query,
                token=os.getenv(args.token_env) if args.token_env else None,
                per_page=args.per_page,
                page=args.page,
                sort=args.sort,
                order=args.order,
            )
        batch = build_metadata_discovery_batch(
            payload,
            query=args.query,
            discovered_by=_actor(args),
            discovered_at=args.discovered_at,
            page=args.page,
            max_records=args.max_records,
            search_sort=args.sort,
            search_order=args.order,
        )
    except GitHubDiscoveryAdapterError as exc:
        print(f"REJECTED GITHUB DISCOVERY: {exc}")
        return 1

    rendered = json.dumps(batch, ensure_ascii=False, indent=2) + "\n"
    if args.output is None:
        print(rendered, end="")
    else:
        args.output.write_text(rendered, encoding="utf-8")
        print(f"WROTE {args.output} records={len(batch['records'])}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
