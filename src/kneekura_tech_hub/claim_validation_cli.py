from __future__ import annotations

import argparse
import json
import os

import psycopg

from .claim_validation import (
    ClaimValidationError,
    claim_validation_context,
    claim_validation_history,
    validate_claim,
)
from .claim_validation_postgres import ClaimValidationPostgresRepository
from .database import apply_migrations


def _repository() -> ClaimValidationPostgresRepository:
    dsn = os.getenv("KTHUB_DATABASE_URL")
    if not dsn:
        raise ClaimValidationError("KTHUB_DATABASE_URL is required")
    connection = psycopg.connect(dsn, autocommit=True)
    apply_migrations(connection)
    return ClaimValidationPostgresRepository(connection)


def _render(value) -> None:
    print(json.dumps(value, ensure_ascii=False, indent=2, default=str))


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Human-gated review boundary for SUPPORTED/CHALLENGED -> VALIDATED Claims"
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    context = subparsers.add_parser(
        "context",
        help="show one Claim with Evidence Review, support history, and validation history",
    )
    context.add_argument("claim_id")

    history = subparsers.add_parser(
        "history",
        help="show append-only Claim validation decisions",
    )
    history.add_argument("--claim-id")

    validate = subparsers.add_parser(
        "validate",
        help="perform one governed promotion or revalidation to VALIDATED",
    )
    validate.add_argument("claim_id")
    validate.add_argument("--reason", required=True)
    validate.add_argument("--actor-id", required=True)
    validate.add_argument("--actor-version")
    validate.add_argument(
        "--validation-basis",
        required=True,
        choices=["EVIDENCE_REVIEW", "REPRODUCTION", "EXPERIMENT", "OTHER"],
    )
    validate.add_argument("--validation-note", required=True)
    validate.add_argument(
        "--independence-assessment",
        required=True,
        choices=["NOT_ASSESSED", "HUMAN_REVIEWED"],
    )
    validate.add_argument("--independence-note")
    validate.add_argument("--counterevidence-note")
    validate.add_argument("--qualification-note")
    validate.add_argument("--competition-note")
    validate.add_argument("--decision-id")
    validate.add_argument("--policy-version", default="1.0.0")

    args = parser.parse_args()
    repository: ClaimValidationPostgresRepository | None = None
    try:
        repository = _repository()
        if args.command == "context":
            result = claim_validation_context(repository, args.claim_id)
        elif args.command == "history":
            result = claim_validation_history(repository, claim_id=args.claim_id)
        else:
            actor = {"actor_type": "human", "actor_id": args.actor_id}
            if args.actor_version is not None:
                actor["version"] = args.actor_version
            result = validate_claim(
                repository,
                args.claim_id,
                actor=actor,
                reason=args.reason,
                validation_basis=args.validation_basis,
                validation_note=args.validation_note,
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
    except (ClaimValidationError, ValueError, psycopg.Error) as exc:
        print(f"REJECTED CLAIM VALIDATION: {exc}")
        return 1
    finally:
        if repository is not None:
            repository.close()


if __name__ == "__main__":
    raise SystemExit(main())
