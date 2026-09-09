from __future__ import annotations

import argparse
import json
import os

import psycopg

from .claim_support import (
    ClaimSupportError,
    claim_support_context,
    claim_support_history,
    promote_candidate_to_supported,
)
from .claim_support_postgres import ClaimSupportPostgresRepository
from .database import apply_migrations


def _repository() -> ClaimSupportPostgresRepository:
    dsn = os.getenv("KTHUB_DATABASE_URL")
    if not dsn:
        raise ClaimSupportError("KTHUB_DATABASE_URL is required")
    connection = psycopg.connect(dsn, autocommit=True)
    apply_migrations(connection)
    return ClaimSupportPostgresRepository(connection)


def _render(value) -> None:
    print(json.dumps(value, ensure_ascii=False, indent=2, default=str))


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Human-gated review boundary for CANDIDATE -> SUPPORTED Claims"
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    context = subparsers.add_parser(
        "context",
        help="show one Candidate Claim with Evidence Review and competing-Claim context",
    )
    context.add_argument("claim_id")

    history = subparsers.add_parser(
        "history",
        help="show append-only Claim support decisions",
    )
    history.add_argument("--claim-id")

    promote = subparsers.add_parser(
        "promote",
        help="perform one governed CANDIDATE -> SUPPORTED promotion",
    )
    promote.add_argument("claim_id")
    promote.add_argument("--reason", required=True)
    promote.add_argument("--actor-id", required=True)
    promote.add_argument("--actor-version")
    promote.add_argument(
        "--independence-assessment",
        required=True,
        choices=["NOT_ASSESSED", "HUMAN_REVIEWED"],
    )
    promote.add_argument("--independence-note")
    promote.add_argument("--counterevidence-note")
    promote.add_argument("--qualification-note")
    promote.add_argument("--competition-note")
    promote.add_argument("--decision-id")
    promote.add_argument("--policy-version", default="1.0.0")

    args = parser.parse_args()
    repository: ClaimSupportPostgresRepository | None = None
    try:
        repository = _repository()
        if args.command == "context":
            result = claim_support_context(repository, args.claim_id)
        elif args.command == "history":
            result = claim_support_history(repository, claim_id=args.claim_id)
        else:
            actor = {"actor_type": "human", "actor_id": args.actor_id}
            if args.actor_version is not None:
                actor["version"] = args.actor_version
            result = promote_candidate_to_supported(
                repository,
                args.claim_id,
                actor=actor,
                reason=args.reason,
                independence_assessment=args.independence_assessment,
                independence_note=args.independence_note,
                counterevidence_note=args.counterevidence_note,
                qualification_note=args.qualification_note,
                competition_note=args.competition_note,
                decision_id=args.decision_id,
                policy_version=args.policy_version,
            )
        _render(result)
        return 0
    except (ClaimSupportError, ValueError, psycopg.Error) as exc:
        print(f"REJECTED CLAIM SUPPORT: {exc}")
        return 1
    finally:
        if repository is not None:
            repository.close()


if __name__ == "__main__":
    raise SystemExit(main())
