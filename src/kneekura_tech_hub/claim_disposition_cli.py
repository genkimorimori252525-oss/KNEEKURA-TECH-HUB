from __future__ import annotations

import argparse
import json
import os

import psycopg

from .claim_disposition import (
    ClaimDispositionError,
    claim_disposition_context,
    claim_disposition_history,
    dispose_claim,
)
from .claim_disposition_postgres import ClaimDispositionPostgresRepository
from .database import apply_migrations


def _repository() -> ClaimDispositionPostgresRepository:
    dsn = os.getenv("KTHUB_DATABASE_URL")
    if not dsn:
        raise ClaimDispositionError("KTHUB_DATABASE_URL is required")
    connection = psycopg.connect(dsn, autocommit=True)
    apply_migrations(connection)
    return ClaimDispositionPostgresRepository(connection)


def _render(value) -> None:
    print(json.dumps(value, ensure_ascii=False, indent=2, default=str))


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Human-gated terminal disposition for reviewed Claims"
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    context = subparsers.add_parser("context", help="show review context without writing")
    context.add_argument("claim_id")

    history = subparsers.add_parser("history", help="show append-only disposition decisions")
    history.add_argument("--claim-id")

    decide = subparsers.add_parser("decide", help="apply a governed terminal disposition")
    decide.add_argument("claim_id")
    decide.add_argument("target_maturity", choices=["REJECTED", "SUPERSEDED"])
    decide.add_argument("--actor-id", required=True)
    decide.add_argument("--actor-version")
    decide.add_argument("--reason", required=True)
    decide.add_argument("--successor-claim-id")
    decide.add_argument("--competition-note")
    decide.add_argument("--decision-id")
    decide.add_argument("--policy-version", default="1.0.0")

    args = parser.parse_args()
    repository: ClaimDispositionPostgresRepository | None = None
    try:
        repository = _repository()
        if args.command == "context":
            result = claim_disposition_context(repository, args.claim_id)
        elif args.command == "history":
            result = claim_disposition_history(repository, claim_id=args.claim_id)
        else:
            actor = {"actor_type": "human", "actor_id": args.actor_id}
            if args.actor_version is not None:
                actor["version"] = args.actor_version
            result = dispose_claim(
                repository,
                args.claim_id,
                args.target_maturity,
                actor=actor,
                reason=args.reason,
                successor_claim_id=args.successor_claim_id,
                competition_note=args.competition_note,
                decision_id=args.decision_id,
                policy_version=args.policy_version,
            )
        _render(result)
        return 0
    except (ClaimDispositionError, ValueError, psycopg.Error) as exc:
        print(f"REJECTED CLAIM DISPOSITION: {exc}")
        return 1
    finally:
        if repository is not None:
            repository.close()


if __name__ == "__main__":
    raise SystemExit(main())
