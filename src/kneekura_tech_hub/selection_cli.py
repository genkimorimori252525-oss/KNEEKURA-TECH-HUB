from __future__ import annotations

import argparse
import json
import os

import psycopg

from .database import apply_migrations
from .selection import (
    SourceSelectionEngine,
    SourceSelectionError,
    active_source_selection_decisions,
    selected_for_review,
    source_selection_history,
)
from .selection_postgres import SelectionPostgresRepository


def _repository() -> SelectionPostgresRepository:
    dsn = os.getenv("KTHUB_DATABASE_URL")
    if not dsn:
        raise SourceSelectionError("KTHUB_DATABASE_URL is required")
    connection = psycopg.connect(dsn, autocommit=True)
    apply_migrations(connection)
    return SelectionPostgresRepository(connection)


def _render(value) -> None:
    print(json.dumps(value, ensure_ascii=False, indent=2))


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Human metadata review selection for KNEEKURA TECH HUB Sources"
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    decide = subparsers.add_parser(
        "decide",
        help="append a human Source selection decision without changing acquisition depth",
    )
    decide.add_argument("source_id")
    decide.add_argument(
        "decision",
        choices=["SELECT_FOR_REVIEW", "DEFER", "REJECT_FOR_REVIEW"],
    )
    decide.add_argument("--rationale", required=True)
    decide.add_argument("--actor-id", required=True)
    decide.add_argument("--supersedes")
    decide.add_argument("--decision-id")

    history = subparsers.add_parser("history", help="show append-only selection history")
    history.add_argument("--source-id")

    active = subparsers.add_parser("active", help="show active selection decisions")
    active.add_argument("--source-id")

    subparsers.add_parser(
        "selected",
        help="show active SELECT_FOR_REVIEW decisions with unchanged Source records",
    )

    args = parser.parse_args()
    repository: SelectionPostgresRepository | None = None
    try:
        repository = _repository()
        if args.command == "decide":
            actor = {"actor_type": "human", "actor_id": args.actor_id}
            result = SourceSelectionEngine(repository).create_from_fields(
                source_id=args.source_id,
                decision=args.decision,
                rationale=args.rationale,
                actor=actor,
                decision_id=args.decision_id,
                supersedes_decision_id=args.supersedes,
            )
        elif args.command == "history":
            result = source_selection_history(repository, source_id=args.source_id)
        elif args.command == "active":
            result = active_source_selection_decisions(repository, source_id=args.source_id)
        else:
            result = selected_for_review(repository)
        _render(result)
        return 0
    except SourceSelectionError as exc:
        print(f"REJECTED SOURCE SELECTION: {exc}")
        return 1
    finally:
        if repository is not None:
            repository.close()


if __name__ == "__main__":
    raise SystemExit(main())
