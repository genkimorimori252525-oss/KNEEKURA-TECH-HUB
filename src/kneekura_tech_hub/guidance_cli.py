from __future__ import annotations

import argparse
import json
import os
from typing import Any

from .explanation import ExplanationError, explain_contextual_guidance
from .postgres_repository import PostgresRepository
from .queries import QueryError


def _open_repository(dsn: str) -> PostgresRepository:
    return PostgresRepository.connect(dsn)


def _reject_duplicate_object_pairs(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate context key: {key}")
        result[key] = value
    return result


def _reject_non_finite_number(value: str) -> None:
    raise ValueError(f"non-finite JSON number: {value}")


def _parse_context(raw: str | None) -> dict[str, Any] | None:
    if raw is None:
        return None
    try:
        value = json.loads(
            raw,
            object_pairs_hook=_reject_duplicate_object_pairs,
            parse_constant=_reject_non_finite_number,
        )
    except json.JSONDecodeError as exc:
        raise ValueError(f"context must be valid JSON: {exc.msg}") from exc
    if not isinstance(value, dict):
        raise ValueError("context must be a JSON object")
    return value


def _render(value: object) -> None:
    print(json.dumps(value, ensure_ascii=False, indent=2))


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Read-only context-aware evidence guidance for KNEEKURA TECH HUB"
    )
    parser.add_argument("entity_id", help="Knowledge Entity ID to query")
    parser.add_argument(
        "--context-json",
        help="exact applicability context as one JSON object; no fuzzy matching or fallback",
    )
    parser.add_argument("--dsn", help="PostgreSQL DSN; defaults to KTHUB_DATABASE_URL")
    args = parser.parse_args()

    try:
        context = _parse_context(args.context_json)
    except ValueError as exc:
        print(f"INVALID CONTEXT: {exc}")
        return 1

    dsn = args.dsn or os.getenv("KTHUB_DATABASE_URL")
    if not dsn:
        print("database DSN required via --dsn or KTHUB_DATABASE_URL")
        return 1

    repository: PostgresRepository | None = None
    try:
        repository = _open_repository(dsn)
        result = explain_contextual_guidance(
            repository,
            args.entity_id,
            context=context,
        )
        _render(result)
        return 0
    except (QueryError, ExplanationError) as exc:
        print(f"GUIDANCE ERROR: {exc}")
        return 1
    finally:
        if repository is not None:
            repository.close()


if __name__ == "__main__":
    raise SystemExit(main())
