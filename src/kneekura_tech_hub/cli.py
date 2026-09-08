from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from typing import Any

import psycopg

from .bundle import BundleValidationError, ingest_bundle, preflight_bundle
from .comparison import ComparisonError, compare_claim, comparison_groups
from .database import apply_foundation_migration
from .decision import (
    DecisionError,
    HumanReviewDecisionEngine,
    active_review_decisions,
    decision_context_for_claim,
    review_decision_history,
)
from .discovery import (
    DiscoveryIntakeError,
    ingest_discovery_intake,
    preflight_discovery_intake,
)
from .explanation import ExplanationError, explain_claim
from .postgres_repository import PostgresRepository
from .projection import ProjectionError, project_relations
from .queries import QueryError, problems_solved_by, requirements_for, solutions_for_problem
from .review import ReviewError, review_claim, review_claims
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


def _add_view_argument(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--view",
        choices=["validated", "research", "challenged", "history"],
        default="validated",
    )


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
        engine.stage_observation(record, actor=actor)
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

    discovery_check_parser = subparsers.add_parser(
        "discovery-check",
        help="preflight a self-contained controlled GitHub discovery batch without writes",
    )
    discovery_check_parser.add_argument("batch", type=Path)

    init_parser = subparsers.add_parser("init-db", help="apply PostgreSQL migrations")
    _add_database_argument(init_parser)

    ingest_parser = subparsers.add_parser("ingest", help="validate and store one record")
    ingest_parser.add_argument("record", type=Path)
    _add_database_argument(ingest_parser)
    _add_actor_arguments(ingest_parser)

    bundle_ingest_parser = subparsers.add_parser(
        "ingest-bundle", help="preflight and atomically store a curated prototype bundle"
    )
    bundle_ingest_parser.add_argument("bundle", type=Path)
    _add_database_argument(bundle_ingest_parser)
    _add_actor_arguments(bundle_ingest_parser)

    discovery_ingest_parser = subparsers.add_parser(
        "discovery-ingest",
        help="atomically ingest only Source/Snapshot/Evidence/NEW Observation discovery records",
    )
    discovery_ingest_parser.add_argument("batch", type=Path)
    _add_database_argument(discovery_ingest_parser)
    _add_actor_arguments(discovery_ingest_parser)

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
            "review_decision",
            "curation_event",
        ],
    )
    _add_database_argument(list_parser)

    relations_parser = subparsers.add_parser(
        "relations", help="project evidence-backed Relation Claims into a read view"
    )
    _add_view_argument(relations_parser)
    relations_parser.add_argument("--entity-id")
    relations_parser.add_argument("--relation-type")
    relations_parser.add_argument("--direction", choices=["any", "out", "in"], default="any")
    _add_database_argument(relations_parser)

    solutions_parser = subparsers.add_parser(
        "solutions", help="find entities with explicit solves Claims for one Problem"
    )
    solutions_parser.add_argument("problem_id")
    _add_view_argument(solutions_parser)
    _add_database_argument(solutions_parser)

    solved_parser = subparsers.add_parser(
        "solved-problems", help="find Problems explicitly solved by one entity"
    )
    solved_parser.add_argument("entity_id")
    _add_view_argument(solved_parser)
    _add_database_argument(solved_parser)

    requirements_parser = subparsers.add_parser(
        "requirements", help="find explicit requires Claims for one entity"
    )
    requirements_parser.add_argument("entity_id")
    _add_view_argument(requirements_parser)
    _add_database_argument(requirements_parser)

    explain_parser = subparsers.add_parser(
        "explain-claim",
        help="rebuild Claim -> Evidence -> SourceSnapshot -> Source provenance",
    )
    explain_parser.add_argument("claim_id")
    _add_database_argument(explain_parser)

    review_parser = subparsers.add_parser(
        "review-claim",
        help="show a non-scalar evidence/review profile for one Claim",
    )
    review_parser.add_argument("claim_id")
    _add_database_argument(review_parser)

    review_all_parser = subparsers.add_parser(
        "review-claims",
        help="show derived evidence/review profiles for Claims",
    )
    review_all_parser.add_argument(
        "--needs-review",
        action="store_true",
        help="return only Claims matching explicit review conditions",
    )
    _add_database_argument(review_all_parser)

    compare_parser = subparsers.add_parser(
        "compare-claim",
        help="compare all Claims with the exact same stored subject",
    )
    compare_parser.add_argument("claim_id")
    _add_database_argument(compare_parser)

    compare_all_parser = subparsers.add_parser(
        "compare-claims",
        help="show exact-subject Claim comparison groups",
    )
    compare_all_parser.add_argument(
        "--multiple-only",
        action="store_true",
        help="return only subjects with more than one Claim",
    )
    compare_all_parser.add_argument(
        "--needs-review",
        action="store_true",
        help="return only groups matching explicit review conditions",
    )
    _add_database_argument(compare_all_parser)

    decide_parser = subparsers.add_parser(
        "decide-claims",
        help="record a human decision about two Claims with the same exact subject",
    )
    decide_parser.add_argument("source_claim_id")
    decide_parser.add_argument("target_claim_id")
    decide_parser.add_argument(
        "decision",
        choices=[
            "CONTRADICTS",
            "COMPATIBLE",
            "QUALIFIES",
            "DUPLICATE",
            "SUPERSEDES",
            "UNRESOLVED",
        ],
    )
    decide_parser.add_argument("--reason", required=True)
    decide_parser.add_argument("--decision-id")
    decide_parser.add_argument("--supersedes-decision-id")
    _add_database_argument(decide_parser)
    _add_actor_arguments(decide_parser)

    decisions_parser = subparsers.add_parser(
        "review-decisions",
        help="show append-only human review decision history",
    )
    decisions_parser.add_argument("--claim-id")
    decisions_parser.add_argument("--active", action="store_true")
    _add_database_argument(decisions_parser)

    context_parser = subparsers.add_parser(
        "decision-context",
        help="show Claim comparison together with human decision history",
    )
    context_parser.add_argument("claim_id")
    _add_database_argument(context_parser)

    transition_parser = subparsers.add_parser(
        "transition-claim", help="move a claim through the governed maturity lifecycle"
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
        "merge-entities", help="human-approved canonical entity merge with redirect preservation"
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

    if args.command == "discovery-check":
        try:
            batch = _load_json(args.batch)
            ordered = preflight_discovery_intake(batch)
        except (DiscoveryIntakeError, HubValidationError, ValueError) as exc:
            print(f"INVALID DISCOVERY: {exc}")
            return 1
        print(f"DISCOVERY VALID {batch['batch_id']} records={len(ordered)}")
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
                with repo.connection.transaction():
                    stored = ingest_bundle(engine, bundle, actor=_actor(args))
            except (BundleValidationError, HubValidationError, CurationError, ValueError) as exc:
                print(f"REJECTED BUNDLE: {exc}")
                return 1
            print(f"STORED BUNDLE {bundle['bundle_id']} records={len(stored)}")
            return 0

        if args.command == "discovery-ingest":
            try:
                batch = _load_json(args.batch)
                with repo.connection.transaction():
                    receipt = ingest_discovery_intake(engine, batch, actor=_actor(args))
            except (DiscoveryIntakeError, HubValidationError, CurationError, ValueError) as exc:
                print(f"REJECTED DISCOVERY: {exc}")
                return 1
            print(json.dumps(receipt, ensure_ascii=False, indent=2))
            return 0

        if args.command == "get":
            record = engine.get(args.record_id)
            if record is None:
                print("NOT FOUND")
                return 1
            print(json.dumps(record, ensure_ascii=False, indent=2))
            return 0

        if args.command == "list":
            print(json.dumps(engine.list(args.record_type), ensure_ascii=False, indent=2))
            return 0

        if args.command == "decide-claims":
            try:
                result = HumanReviewDecisionEngine(repo).create_from_fields(
                    source_claim_id=args.source_claim_id,
                    target_claim_id=args.target_claim_id,
                    decision=args.decision,
                    rationale=args.reason,
                    actor=_actor(args),
                    decision_id=args.decision_id,
                    supersedes_decision_id=args.supersedes_decision_id,
                )
            except (HubValidationError, DecisionError, ValueError) as exc:
                print(f"REJECTED DECISION: {exc}")
                return 1
            print(json.dumps(result, ensure_ascii=False, indent=2))
            return 0

        try:
            if args.command == "relations":
                result = project_relations(
                    repo,
                    view=args.view,
                    entity_id=args.entity_id,
                    relation_type=args.relation_type,
                    direction=args.direction,
                )
            elif args.command == "solutions":
                result = solutions_for_problem(repo, args.problem_id, view=args.view)
            elif args.command == "solved-problems":
                result = problems_solved_by(repo, args.entity_id, view=args.view)
            elif args.command == "requirements":
                result = requirements_for(repo, args.entity_id, view=args.view)
            elif args.command == "explain-claim":
                result = explain_claim(repo, args.claim_id)
            elif args.command == "review-claim":
                result = review_claim(repo, args.claim_id)
            elif args.command == "review-claims":
                result = review_claims(repo, needs_review_only=args.needs_review)
            elif args.command == "compare-claim":
                result = compare_claim(repo, args.claim_id)
            elif args.command == "compare-claims":
                result = comparison_groups(
                    repo,
                    multiple_only=args.multiple_only,
                    needs_review_only=args.needs_review,
                )
            elif args.command == "review-decisions":
                if args.active:
                    result = active_review_decisions(repo, claim_id=args.claim_id)
                else:
                    result = review_decision_history(repo, claim_id=args.claim_id)
            elif args.command == "decision-context":
                result = decision_context_for_claim(repo, args.claim_id)
            else:
                result = None
        except (
            ProjectionError,
            QueryError,
            ExplanationError,
            ReviewError,
            ComparisonError,
            DecisionError,
        ) as exc:
            print(f"REJECTED QUERY: {exc}")
            return 1
        if result is not None:
            print(json.dumps(result, ensure_ascii=False, indent=2))
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