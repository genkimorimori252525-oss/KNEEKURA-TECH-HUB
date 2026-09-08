from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

import psycopg

from .database import apply_migrations
from .execution import (
    AcquisitionExecutionError,
    acquisition_execution_history,
    execute_authorized_acquisition,
    fetch_github_file,
)
from .execution_postgres import ExecutionPostgresRepository


def _repository() -> ExecutionPostgresRepository:
    dsn = os.getenv("KTHUB_DATABASE_URL")
    if not dsn:
        raise AcquisitionExecutionError("KTHUB_DATABASE_URL is required")
    connection = psycopg.connect(dsn, autocommit=True)
    apply_migrations(connection)
    return ExecutionPostgresRepository(connection)


def _render(value) -> None:
    print(json.dumps(value, ensure_ascii=False, indent=2))


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Execute one currently-effective bounded acquisition authorization"
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    execute = subparsers.add_parser(
        "execute",
        help="retrieve exactly the pinned revision and allowlisted files from one authorization",
    )
    execute.add_argument("authorization_id")
    execute.add_argument("--storage-root", required=True)
    execute.add_argument("--actor-id", required=True)
    execute.add_argument("--actor-version", default="v1")
    execute.add_argument("--execution-id")
    execute.add_argument(
        "--github-token-env",
        default="KTHUB_GITHUB_TOKEN",
        help="environment variable containing an optional GitHub token; token value is never accepted on CLI",
    )

    history = subparsers.add_parser("history", help="show append-only acquisition execution history")
    history.add_argument("--authorization-id")
    history.add_argument("--source-id")

    args = parser.parse_args()
    repository: ExecutionPostgresRepository | None = None
    try:
        repository = _repository()
        if args.command == "execute":
            token = os.getenv(args.github_token_env)

            def github_fetch(source, revision, path):
                return fetch_github_file(source, revision, path, token=token)

            result = execute_authorized_acquisition(
                repository,
                args.authorization_id,
                storage_root=Path(args.storage_root),
                fetch_file=github_fetch,
                actor={
                    "actor_type": "tool",
                    "actor_id": args.actor_id,
                    "version": args.actor_version,
                },
                execution_id=args.execution_id,
            )
        else:
            result = acquisition_execution_history(
                repository,
                authorization_id=args.authorization_id,
                source_id=args.source_id,
            )
        _render(result)
        return 0
    except AcquisitionExecutionError as exc:
        print(f"REJECTED ACQUISITION EXECUTION: {exc}")
        return 1
    finally:
        if repository is not None:
            repository.close()


if __name__ == "__main__":
    raise SystemExit(main())
