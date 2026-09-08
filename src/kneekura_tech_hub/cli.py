from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from typing import Any

import psycopg

from .bundle import BundleValidationError, ingest_bundle, preflight_bundle
from .database import apply_foundation_migration
from .postgres_repository import PostgresRepository
from .service import CurationEngine, CurationError
from .validator import HubValidationError, validate_record


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _actor(args: argparse.Namespace) -> dict[str, Any]:
    actor: dict[str, Any] = {"actor_type": args.actor_type}
    if args.actor_id:
        actor["actor_id"] = args.actor_id
    if args.actor_version:
        actor["version"] = args.actor_version
    return actor


def _dsn(args: argparse.Namespace) -> str:
    value = getattr(args, "dsn", None) or os.getenv("KTHUB_DATABASE_URL")
    if not value:
        raise SystemExit("database DSN required via --dsn or KTHUB_DATABASE_URL")
    return value


def _add_database_argument(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--dsn", help="PostgreSQL DSN; defaults to KTHUB_DATABASE_URL")


def _add_actor_arguments(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--actor-type",
        choices=["human", "ai", "tool", "system"],
        default="human",
    )
    parser.add_argument("--actor-id")
    parser.add_argument("--actor-version")


def _open_repository(dsn: str) -> PostgresRepository:
    return PostgresRepository.connect(dsn)


def _ingest(engine: CurationEngine, record: dict[str, Any], actor: dict[str, Any]) -> None:
    record_type = record.get("record_type")
    if record_type == "source":
        engine.register_source(record, actor=actor)
    elif record_type == "source_snapshot":
        engine.register_source_snapshot(record, actor=actor)
    elif record_type == "evidence":
        engine.register_evidence(record, actor=actor)
    elif record_type == "knowledge_entity":
        engine.create_entity(record, actor=actor, reason="CLI ingestion")
    elif record_type == "claim":
        engine.create_claim(record, actor=actor, reason="CLI ingestion")
    elif record_type == "staged_observation":
        engine.stage_observation(record)
    else:
        raise CurationError(f"record_type cannot be ingested directly: {record_type!r}")


def validate_main() -> int:
    parser = argparse.ArgumentParser(description="Validate a KNEEKURA TECH HUB v1 JSON record")
    parser.add_argument("record", type=Path)
    args = parser.parse_args()

    try:
        validate_record(_load_json(args.record))
    except HubValidationError as exc:
        print(f"INVALID: {exc}")
        return 1
    print("VALID")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="KNEEKURA TECH HUB curation CLI")
    subparsers = parser.add_subparsers(dest="command", required=True)

    validate_parser = subparsers.add_parser("validate", help="validate one JSON record")
    validate_parser.add_argument("record", type=Path)

    bundle_check_parser = subparsers.add_parser(
        "bundle-check", help="preflight a self-contained curated prototype bundle"
    )
    bundle_check_parser.add_argument("bundle", type=Path)

    init_parser = subparsers.add_parser("init-db", help="apply the foundation PostgreSQL migration")
    _add_database_argument(init_parser)

    ingest_parser = subparsers.add_parser("ingest", help="validate and store one record")
    ingest_parser.add_argument("record", type=Path)
    _add_database_argument(ingest_parser)
    _add_actor_arguments(ingest_parser)

    bundle_ingest_parser = subparsers.add_parser(
        "ingest-bundle",
        help="preflight and atomically store a curated prototype bundle",
    )
    bundle_ingest_parser.add_argument("bundle", type=Path)
    _add_database_argument(bundle_ingest_parser)
    _add_actor_arguments(bundle_ingest_parser)

    get_parser = subparsers.add_parser("get", help="retrieve one record by immutable ID")
    get_parser.add_argument("record_id")
    _add_database_argument(get_parser)

    list_parser = subparsers.add_parser("list", help="list records")
    list_parser.add_argument(
        "--type",
        dest="record_type",
        choices=[
            "knowledge_entity",
            "source",
            "source_snapshot",
            "evidence",
            "claim",
            "staged_observation",
            "curation_event",
        ],
    )
    _add_database_argument(list_parser)

    transition_parser = subparsers.add_parser(
        "transition-claim",
        help="move a claim through the governed maturity lifecycle",
    )
    transition_parser.add_argument("claim_id")
    transition_parser.add_argument(
        "target_maturity",
        choices=["SUPPORTED", "VALIDATED", "CHALLENGED", "SUPERSEDED", "REJECTED"],
    )
    transition_parser.add_argument("--reason", required=True)
    transition_parser.add_argument("--superseded-by")
    _add_database_argument(transition_parser)
    _add_actor_arguments(transition_parser)

    merge_parser = subparsers.add_parser(
        "merge-entities",
        help="human-approved canonical entity merge with redirect preservation",
    )
    merge_parser.add_argument("survivor_id")
    merge_parser.add_argument("merged_id")
    merge_parser.add_argument("--reason", required=True)
    _add_database_argument(merge_parser)
    _add_actor_arguments(merge_parser)

    args = parser.parse_args()

    if args.command == "validate":
        try:
            validate_record(_load_json(args.record))
        except HubValidationError as exc:
            print(f"INVALID: {exc}")
            return 1
        print("VALID")
        return 0

    if args.command == "bundle-check":
        try:
            bundle = _load_json(args.bundle)
            ordered = preflight_bundle(bundle)
        except (BundleValidationError, HubValidationError, ValueError) as exc:
            print(f"INVALID BUNDLE: {exc}")
            return 1
        print(f"BUNDLE VALID {bundle['bundle_id']} records={len(ordered)}")
        return 0

    repo = _open_repository(_dsn(args))
    try:
        if args.command == "init-db":
            apply_foundation_migration(repo.connection)
            print("FOUNDATION DB READY")
            return 0

        engine = CurationEngine(repo)

        if args.command == "ingest":
            try:
                record = _load_json(args.record)
                _ingest(engine, record, _actor(args))
            except (HubValidationError, CurationError, ValueError) as exc:
                print(f"REJECTED: {exc}")
                return 1
            print(f"STORED {record['id']}")
            return 0

        if args.command == "ingest-bundle":
            try:
                bundle = _load_json(args.bundle)
                # One outer transaction makes the bundle all-or-nothing. The
                # repository's per-record transactions become nested savepoints.
                with repo.connection.transaction():
                    stored = ingest_bundle(engine, bundle, actor=_actor(args))
            except (BundleValidationError, HubValidationError, CurationError, ValueError) as exc:
                print(f"REJECTED BUNDLE: {exc}")
                return 1
            print(f"STORED BUNDLE {bundle['bundle_id']} records={len(stored)}")
            return 0

        if args.command == "get":
            record = engine.get(args.record_id)
            if record is None:
                print("NOT FOUND")
                return 1
            print(json.dumps(record, ensure_ascii=False, indent=2))
            return 0

        if args.command == "list":
            records = engine.list(args.record_type)
            print(json.dumps(records, ensure_ascii=False, indent=2))
            return 0

        if args.command == "transition-claim":
            try:
                updated = engine.transition_claim(
                    args.claim_id,
                    args.target_maturity,
                    actor=_actor(args),
                    reason=args.reason,
                    superseded_by=args.superseded_by,
                )
            except (HubValidationError, CurationError, ValueError) as exc:
                print(f"REJECTED: {exc}")
                return 1
            print(json.dumps(updated, ensure_ascii=False, indent=2))
            return 0

        if args.command == "merge-entities":
            try:
                _, merged = engine.merge_entities(
                    args.survivor_id,
                    args.merged_id,
                    actor=_actor(args),
                    reason=args.reason,
                )
            except (HubValidationError, CurationError, ValueError) as exc:
                print(f"REJECTED: {exc}")
                return 1
            print(json.dumps(merged, ensure_ascii=False, indent=2))
            return 0
    finally:
        repo.close()

    return 2


if __name__ == "__main__":
    raise SystemExit(main())
