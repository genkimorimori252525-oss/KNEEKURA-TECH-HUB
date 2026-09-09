from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

import psycopg

from .database import apply_migrations
from .selected_file_extraction import (
    SelectedFileExtractionError,
    check_selected_file_extraction,
    ingest_selected_file_extraction,
    verify_committed_selected_file_snapshot,
)
from .service import CurationEngine
from .verified_commit_postgres import VerifiedCommitPostgresRepository


def _repository() -> VerifiedCommitPostgresRepository:
    dsn = os.getenv("KTHUB_DATABASE_URL")
    if not dsn:
        raise SelectedFileExtractionError("KTHUB_DATABASE_URL is required")
    connection = psycopg.connect(dsn, autocommit=True)
    apply_migrations(connection)
    return VerifiedCommitPostgresRepository(connection)


def _actor(args) -> dict:
    actor = {"actor_type": args.actor_type, "actor_id": args.actor_id}
    if args.actor_version is not None:
        actor["version"] = args.actor_version
    return actor


def _load_proposal(path: str) -> dict:
    value = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise SelectedFileExtractionError("proposal JSON must be an object")
    return value


def _render(value) -> None:
    print(json.dumps(value, ensure_ascii=False, indent=2, default=str))


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Verify and ingest selected-file Evidence candidates from committed Snapshots"
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    snapshot_check = subparsers.add_parser(
        "snapshot-check",
        help="re-verify one committed selected-file Snapshot without creating Evidence",
    )
    snapshot_check.add_argument("snapshot_id")
    snapshot_check.add_argument("--storage-root", required=True)

    for name, help_text in (
        (
            "check",
            "validate an untrusted extraction proposal and deterministic-ID conflicts without writing",
        ),
        ("ingest", "validate and ingest Evidence + NEW StagedObservations"),
    ):
        command = subparsers.add_parser(name, help=help_text)
        command.add_argument("proposal")
        command.add_argument("--storage-root", required=True)
        command.add_argument(
            "--actor-type",
            required=True,
            choices=["human", "ai", "tool", "system"],
        )
        command.add_argument("--actor-id", required=True)
        command.add_argument("--actor-version")

    args = parser.parse_args()
    repository: VerifiedCommitPostgresRepository | None = None
    try:
        repository = _repository()
        if args.command == "snapshot-check":
            verified = verify_committed_selected_file_snapshot(
                repository,
                args.snapshot_id,
                storage_root=Path(args.storage_root),
            )
            _render(
                {
                    "snapshot_id": verified["snapshot"]["id"],
                    "source_id": verified["source"]["id"],
                    "commit_id": verified["commit"]["id"],
                    "execution_id": verified["execution"]["id"],
                    "revision": verified["snapshot"]["revision"],
                    "manifest_sha256": verified["manifest_sha256"],
                    "verified_paths": [
                        item["path"] for item in verified["verified_file_results"]
                    ],
                }
            )
            return 0

        proposal = _load_proposal(args.proposal)
        actor = _actor(args)
        if args.command == "check":
            checked = check_selected_file_extraction(
                repository,
                proposal,
                storage_root=Path(args.storage_root),
                actor=actor,
            )
            _render(checked)
        else:
            receipt = ingest_selected_file_extraction(
                CurationEngine(repository),
                proposal,
                storage_root=Path(args.storage_root),
                actor=actor,
            )
            _render(receipt)
        return 0
    except (SelectedFileExtractionError, OSError, json.JSONDecodeError, ValueError) as exc:
        print(f"REJECTED SELECTED-FILE EXTRACTION: {exc}")
        return 1
    finally:
        if repository is not None:
            repository.close()


if __name__ == "__main__":
    raise SystemExit(main())
