from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

import psycopg

from .database import apply_migrations
from .verified_commit import (
    VerifiedAcquisitionCommitError,
    commit_verified_acquisition,
    verify_execution_store,
)
from .verified_commit_postgres import VerifiedCommitPostgresRepository


def _repository() -> VerifiedCommitPostgresRepository:
    dsn = os.getenv("KTHUB_DATABASE_URL")
    if not dsn:
        raise VerifiedAcquisitionCommitError("KTHUB_DATABASE_URL is required")
    connection = psycopg.connect(dsn, autocommit=True)
    apply_migrations(connection)
    return VerifiedCommitPostgresRepository(connection)


def _render(value) -> None:
    print(json.dumps(value, ensure_ascii=False, indent=2))


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Re-verify and canonically commit one successful selected-file acquisition"
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    verify = subparsers.add_parser("verify", help="re-hash execution storage without canonical writes")
    verify.add_argument("execution_id")
    verify.add_argument("--storage-root", required=True)

    commit = subparsers.add_parser(
        "commit",
        help="atomically create SourceSnapshot and promote Source to selected-files",
    )
    commit.add_argument("execution_id")
    commit.add_argument("--storage-root", required=True)
    commit.add_argument("--actor-id", required=True)
    commit.add_argument("--actor-version", default="v1")
    commit.add_argument("--commit-id")

    history = subparsers.add_parser("history", help="show verified acquisition commit records")
    history.add_argument("--source-id")
    history.add_argument("--execution-id")

    args = parser.parse_args()
    repository: VerifiedCommitPostgresRepository | None = None
    try:
        repository = _repository()
        if args.command == "verify":
            verified = verify_execution_store(
                repository,
                args.execution_id,
                storage_root=Path(args.storage_root),
            )
            result = {
                "execution_id": verified["execution"]["id"],
                "source_id": verified["source"]["id"],
                "authorization_id": verified["authorization"]["id"],
                "manifest_sha256": verified["manifest_sha256"],
                "verified_paths": [item["path"] for item in verified["verified_file_results"]],
                "status": "VERIFIED_NOT_COMMITTED",
            }
        elif args.command == "commit":
            result = commit_verified_acquisition(
                repository,
                args.execution_id,
                storage_root=Path(args.storage_root),
                actor={
                    "actor_type": "tool",
                    "actor_id": args.actor_id,
                    "version": args.actor_version,
                },
                commit_id=args.commit_id,
            )
        else:
            records = repository.list("source_acquisition_commit")
            if args.source_id is not None:
                records = [item for item in records if item["source_id"] == args.source_id]
            if args.execution_id is not None:
                records = [item for item in records if item["execution_id"] == args.execution_id]
            result = records
        _render(result)
        return 0
    except VerifiedAcquisitionCommitError as exc:
        print(f"REJECTED VERIFIED ACQUISITION COMMIT: {exc}")
        return 1
    finally:
        if repository is not None:
            repository.close()


if __name__ == "__main__":
    raise SystemExit(main())
