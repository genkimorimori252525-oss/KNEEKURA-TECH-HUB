from __future__ import annotations

import argparse
import json
import os

import psycopg

from .authorization import (
    AcquisitionAuthorizationEngine,
    AcquisitionAuthorizationError,
    acquisition_authorization_history,
    active_acquisition_authorizations,
    authorized_acquisition_requests,
)
from .authorization_postgres import AuthorizationPostgresRepository
from .database import apply_migrations


def _repository() -> AuthorizationPostgresRepository:
    dsn = os.getenv("KTHUB_DATABASE_URL")
    if not dsn:
        raise AcquisitionAuthorizationError("KTHUB_DATABASE_URL is required")
    connection = psycopg.connect(dsn, autocommit=True)
    apply_migrations(connection)
    return AuthorizationPostgresRepository(connection)


def _render(value) -> None:
    print(json.dumps(value, ensure_ascii=False, indent=2))


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Human bounded selected-file acquisition authorization for KNEEKURA TECH HUB"
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    authorize = subparsers.add_parser(
        "authorize",
        help="authorize an exact selected-file scope without performing retrieval",
    )
    authorize.add_argument("source_id")
    authorize.add_argument("--selection-id", required=True)
    authorize.add_argument("--revision", required=True)
    authorize.add_argument("--path", action="append", dest="paths", required=True)
    authorize.add_argument("--rationale", required=True)
    authorize.add_argument("--actor-id", required=True)
    authorize.add_argument("--authorization-id")
    authorize.add_argument("--supersedes")

    revoke = subparsers.add_parser("revoke", help="revoke the active exact authorization scope")
    revoke.add_argument("authorization_id")
    revoke.add_argument("--rationale", required=True)
    revoke.add_argument("--actor-id", required=True)
    revoke.add_argument("--revocation-id")

    history = subparsers.add_parser("history", help="show append-only authorization history")
    history.add_argument("--source-id")

    active = subparsers.add_parser("active", help="show active authorization decisions")
    active.add_argument("--source-id")

    subparsers.add_parser(
        "authorized",
        help="show active AUTHORIZE records with unchanged Source records; does not fetch files",
    )

    args = parser.parse_args()
    repository: AuthorizationPostgresRepository | None = None
    try:
        repository = _repository()
        engine = AcquisitionAuthorizationEngine(repository)
        if args.command == "authorize":
            actor = {"actor_type": "human", "actor_id": args.actor_id}
            result = engine.authorize_from_fields(
                source_id=args.source_id,
                selection_decision_id=args.selection_id,
                revision=args.revision,
                allowed_paths=args.paths,
                rationale=args.rationale,
                actor=actor,
                authorization_id=args.authorization_id,
                supersedes_authorization_id=args.supersedes,
            )
        elif args.command == "revoke":
            actor = {"actor_type": "human", "actor_id": args.actor_id}
            result = engine.revoke(
                args.authorization_id,
                rationale=args.rationale,
                actor=actor,
                revocation_id=args.revocation_id,
            )
        elif args.command == "history":
            result = acquisition_authorization_history(repository, source_id=args.source_id)
        elif args.command == "active":
            result = active_acquisition_authorizations(repository, source_id=args.source_id)
        else:
            result = authorized_acquisition_requests(repository)
        _render(result)
        return 0
    except AcquisitionAuthorizationError as exc:
        print(f"REJECTED ACQUISITION AUTHORIZATION: {exc}")
        return 1
    finally:
        if repository is not None:
            repository.close()


if __name__ == "__main__":
    raise SystemExit(main())
