from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

import psycopg

from .database import apply_migrations
from .observation_triage import (
    ObservationTriageError,
    observation_context,
    observation_duplicate_candidates,
    triage_decision_history,
    triage_queue,
    transition_observation,
)
from .observation_triage_postgres import ObservationTriagePostgresRepository


_STATUSES = ["NEW", "TRIAGED", "PROMOTED", "REJECTED", "EXPIRED"]
_ACTIONS = ["MARK_TRIAGED", "REJECT", "EXPIRE", "PROMOTE_TO_CLAIM_CANDIDATE"]


def _repository() -> ObservationTriagePostgresRepository:
    dsn = os.getenv("KTHUB_DATABASE_URL")
    if not dsn:
        raise ObservationTriageError("KTHUB_DATABASE_URL is required")
    connection = psycopg.connect(dsn, autocommit=True)
    apply_migrations(connection)
    return ObservationTriagePostgresRepository(connection)


def _render(value) -> None:
    print(json.dumps(value, ensure_ascii=False, indent=2, default=str))


def _load_json_object(path: str) -> dict:
    value = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ObservationTriageError("Claim Candidate JSON must be an object")
    return value


def _actor(args) -> dict:
    actor = {"actor_type": args.actor_type, "actor_id": args.actor_id}
    if args.actor_version is not None:
        actor["version"] = args.actor_version
    return actor


def _statuses(values: list[str] | None, *, default: tuple[str, ...]) -> tuple[str, ...]:
    return tuple(values) if values else default


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Governed review queue and lifecycle transitions for StagedObservations"
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    queue = subparsers.add_parser(
        "queue",
        help="show review queue; defaults to NEW and TRIAGED observations",
    )
    queue.add_argument("--status", action="append", choices=_STATUSES)

    show = subparsers.add_parser("show", help="show one Observation with exact provenance context")
    show.add_argument("observation_id")

    duplicates = subparsers.add_parser(
        "duplicates",
        help="show exact-content and shared-Evidence duplicate candidates without merging",
    )
    duplicates.add_argument("--status", action="append", choices=_STATUSES)

    history = subparsers.add_parser("history", help="show append-only observation triage decisions")
    history.add_argument("--observation-id")

    transition = subparsers.add_parser(
        "transition",
        help="perform one governed Observation lifecycle transition",
    )
    transition.add_argument("observation_id")
    transition.add_argument("action", choices=_ACTIONS)
    transition.add_argument("--reason", required=True)
    transition.add_argument(
        "--actor-type",
        required=True,
        choices=["human", "tool", "system"],
        help="AI is intentionally not a lifecycle actor",
    )
    transition.add_argument("--actor-id", required=True)
    transition.add_argument("--actor-version")
    transition.add_argument("--claim-candidate")
    transition.add_argument("--decision-id")
    transition.add_argument("--policy-version", default="1.0.0")

    args = parser.parse_args()
    repository: ObservationTriagePostgresRepository | None = None
    try:
        repository = _repository()
        if args.command == "queue":
            result = triage_queue(
                repository,
                statuses=_statuses(args.status, default=("NEW", "TRIAGED")),
            )
        elif args.command == "show":
            result = observation_context(repository, args.observation_id)
        elif args.command == "duplicates":
            result = observation_duplicate_candidates(
                repository,
                statuses=args.status,
            )
        elif args.command == "history":
            result = triage_decision_history(
                repository,
                observation_id=args.observation_id,
            )
        else:
            claim_candidate = (
                _load_json_object(args.claim_candidate)
                if args.claim_candidate is not None
                else None
            )
            result = transition_observation(
                repository,
                args.observation_id,
                args.action,
                reason=args.reason,
                actor=_actor(args),
                claim_candidate=claim_candidate,
                decision_id=args.decision_id,
                policy_version=args.policy_version,
            )
        _render(result)
        return 0
    except (ObservationTriageError, OSError, json.JSONDecodeError, ValueError, psycopg.Error) as exc:
        print(f"REJECTED OBSERVATION TRIAGE: {exc}")
        return 1
    finally:
        if repository is not None:
            repository.close()


if __name__ == "__main__":
    raise SystemExit(main())
