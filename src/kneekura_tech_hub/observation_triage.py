from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timezone
from hashlib import sha256
import json
from pathlib import Path
from typing import Any, Iterable
from uuid import uuid4

from jsonschema import Draft202012Validator

from .repository import Record, RecordRepository
from .service import CurationEngine, CurationError
from .validator import validate_record


class ObservationTriageError(ValueError):
    """Raised when a staged-observation triage operation violates governance."""


_ACTION_TO_STATUS = {
    "MARK_TRIAGED": "TRIAGED",
    "REJECT": "REJECTED",
    "EXPIRE": "EXPIRED",
    "PROMOTE_TO_CLAIM_CANDIDATE": "PROMOTED",
}

_ALLOWED_TRANSITIONS = {
    "NEW": {"MARK_TRIAGED", "REJECT", "EXPIRE"},
    "TRIAGED": {"REJECT", "EXPIRE", "PROMOTE_TO_CLAIM_CANDIDATE"},
    "PROMOTED": set(),
    "REJECTED": set(),
    "EXPIRED": set(),
}


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def load_observation_triage_decision_schema(
    schema_path: Path | None = None,
) -> dict[str, Any]:
    if schema_path is None:
        schema_path = (
            Path(__file__).resolve().parents[2]
            / "schemas"
            / "v1"
            / "observation-triage-decision.schema.json"
        )
    return json.loads(schema_path.read_text(encoding="utf-8"))


def validate_observation_triage_decision(
    record: Record,
    *,
    schema_path: Path | None = None,
) -> None:
    validator = Draft202012Validator(load_observation_triage_decision_schema(schema_path))
    errors = sorted(validator.iter_errors(record), key=lambda error: list(error.path))
    if errors:
        raise ObservationTriageError("; ".join(error.message for error in errors))


def _observation(repository: RecordRepository, observation_id: str) -> Record:
    record = repository.get(observation_id)
    if record is None or record.get("record_type") != "staged_observation":
        raise ObservationTriageError(f"missing staged_observation: {observation_id}")
    validate_record(record)
    return record


def _actor_allowed(action: str, actor: Record) -> None:
    allowed_fields = {"actor_type", "actor_id", "version"}
    if set(actor) - allowed_fields:
        raise ObservationTriageError("triage actor contains unsupported fields")
    actor_type = actor.get("actor_type")
    if actor_type == "ai":
        raise ObservationTriageError("AI actors cannot change staged-observation lifecycle")
    if actor_type == "human":
        return
    if actor_type in {"tool", "system"} and action in {"MARK_TRIAGED", "EXPIRE"}:
        return
    if actor_type in {"tool", "system"}:
        raise ObservationTriageError(
            f"{actor_type} actor cannot perform observation triage action {action}"
        )
    raise ObservationTriageError("observation triage requires human, tool, or system actor")


def _transactional_repository(repository: RecordRepository):
    connection = getattr(repository, "connection", None)
    lock = getattr(repository, "lock_observation_for_triage", None)
    if connection is None or not callable(lock):
        raise ObservationTriageError(
            "observation lifecycle writes require transactional PostgreSQL triage repository"
        )
    return connection, lock


def triage_decision_history(
    repository: RecordRepository,
    *,
    observation_id: str | None = None,
) -> list[Record]:
    if observation_id is not None:
        _observation(repository, observation_id)
    records = repository.list("observation_triage_decision")
    for record in records:
        validate_observation_triage_decision(record)
        if repository.get(record["observation_id"]) is None:
            raise ObservationTriageError(
                f"triage decision references missing Observation: {record['id']}"
            )
        if record.get("resulting_claim_id") is not None:
            claim = repository.get(record["resulting_claim_id"])
            if claim is None or claim.get("record_type") != "claim":
                raise ObservationTriageError(
                    f"triage decision references missing Claim: {record['id']}"
                )
    if observation_id is not None:
        records = [item for item in records if item["observation_id"] == observation_id]
    return sorted(records, key=lambda item: (item["decided_at"], item["id"]))


def observation_context(repository: RecordRepository, observation_id: str) -> dict[str, Any]:
    observation = _observation(repository, observation_id)
    evidence_records: list[Record] = []
    snapshot_ids: set[str] = set()
    for evidence_id in observation.get("evidence_candidate_ids") or []:
        evidence = repository.get(evidence_id)
        if evidence is None or evidence.get("record_type") != "evidence":
            raise ObservationTriageError(
                f"Observation references missing Evidence: {observation_id} -> {evidence_id}"
            )
        validate_record(evidence)
        if evidence["source_id"] != observation["source_id"]:
            raise ObservationTriageError(
                f"Observation/Evidence Source mismatch: {observation_id} -> {evidence_id}"
            )
        snapshot_ids.add(evidence["source_snapshot_id"])
        evidence_records.append(evidence)
    if len(snapshot_ids) != 1:
        raise ObservationTriageError(
            f"Observation must resolve to exactly one SourceSnapshot: {observation_id}"
        )
    snapshot_id = next(iter(snapshot_ids))
    snapshot = repository.get(snapshot_id)
    if snapshot is None or snapshot.get("record_type") != "source_snapshot":
        raise ObservationTriageError(f"missing SourceSnapshot for Observation: {observation_id}")
    validate_record(snapshot)
    if snapshot["source_id"] != observation["source_id"]:
        raise ObservationTriageError(
            f"Observation Snapshot belongs to another Source: {observation_id}"
        )
    source = repository.get(observation["source_id"])
    if source is None or source.get("record_type") != "source":
        raise ObservationTriageError(f"missing Source for Observation: {observation_id}")
    validate_record(source)
    decisions = triage_decision_history(repository, observation_id=observation_id)
    return {
        "observation": deepcopy(observation),
        "evidence": [deepcopy(item) for item in evidence_records],
        "source_snapshot": deepcopy(snapshot),
        "source": deepcopy(source),
        "triage_decisions": [deepcopy(item) for item in decisions],
    }


def _signature(material: Any) -> str:
    encoded = json.dumps(
        material,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return sha256(encoded).hexdigest()


def observation_content_signature(observation: Record) -> str:
    """Strict non-semantic content signature; actor/status/ID are intentionally excluded."""
    return _signature(
        {
            "source_id": observation["source_id"],
            "evidence_candidate_ids": sorted(set(observation.get("evidence_candidate_ids") or [])),
            "summary": observation["summary"],
            "candidate_names": sorted(set(observation.get("candidate_names") or [])),
        }
    )


def observation_evidence_signature(observation: Record) -> str:
    """Weaker grouping key for observations anchored to the exact same Evidence set."""
    return _signature(
        {
            "source_id": observation["source_id"],
            "evidence_candidate_ids": sorted(set(observation.get("evidence_candidate_ids") or [])),
        }
    )


def observation_duplicate_candidates(
    repository: RecordRepository,
    *,
    statuses: Iterable[str] | None = None,
) -> dict[str, list[dict[str, Any]]]:
    allowed_statuses = set(statuses) if statuses is not None else None
    observations = repository.list("staged_observation")
    exact: dict[str, list[Record]] = {}
    shared_evidence: dict[str, list[Record]] = {}
    for observation in observations:
        validate_record(observation)
        if allowed_statuses is not None and observation["status"] not in allowed_statuses:
            continue
        exact.setdefault(observation_content_signature(observation), []).append(observation)
        shared_evidence.setdefault(observation_evidence_signature(observation), []).append(observation)

    exact_groups = [
        {
            "signature": signature,
            "observation_ids": sorted(item["id"] for item in group),
            "count": len(group),
        }
        for signature, group in exact.items()
        if len(group) > 1
    ]
    evidence_groups = [
        {
            "signature": signature,
            "observation_ids": sorted(item["id"] for item in group),
            "content_signature_count": len(
                {observation_content_signature(item) for item in group}
            ),
            "count": len(group),
        }
        for signature, group in shared_evidence.items()
        if len(group) > 1
    ]
    return {
        "exact_content_groups": sorted(exact_groups, key=lambda item: item["signature"]),
        "shared_evidence_groups": sorted(evidence_groups, key=lambda item: item["signature"]),
    }


def triage_queue(
    repository: RecordRepository,
    *,
    statuses: Iterable[str] = ("NEW", "TRIAGED"),
) -> list[dict[str, Any]]:
    wanted = set(statuses)
    duplicate_groups = observation_duplicate_candidates(repository, statuses=wanted)
    exact_sizes: dict[str, int] = {}
    shared_sizes: dict[str, int] = {}
    for group in duplicate_groups["exact_content_groups"]:
        for observation_id in group["observation_ids"]:
            exact_sizes[observation_id] = group["count"]
    for group in duplicate_groups["shared_evidence_groups"]:
        for observation_id in group["observation_ids"]:
            shared_sizes[observation_id] = group["count"]

    result: list[dict[str, Any]] = []
    for observation in repository.list("staged_observation"):
        validate_record(observation)
        if observation["status"] not in wanted:
            continue
        context = observation_context(repository, observation["id"])
        result.append(
            {
                "observation": context["observation"],
                "source_snapshot_id": context["source_snapshot"]["id"],
                "evidence_count": len(context["evidence"]),
                "triage_decision_count": len(context["triage_decisions"]),
                "exact_duplicate_group_size": exact_sizes.get(observation["id"], 1),
                "shared_evidence_group_size": shared_sizes.get(observation["id"], 1),
            }
        )
    return sorted(result, key=lambda item: (item["observation"]["status"], item["observation"]["id"]))


def _build_claim_candidate(
    observation: Record,
    claim_candidate: Record,
    *,
    actor: Record,
    policy_version: str,
) -> Record:
    allowed = {
        "id",
        "entity_id",
        "relation",
        "claim_type",
        "statement",
        "scope",
        "applicability",
        "confidence",
        "reasoning_basis",
        "alternative_interpretations",
    }
    extra = set(claim_candidate) - allowed
    if extra:
        raise ObservationTriageError(
            f"claim candidate contains unsupported fields: {sorted(extra)!r}"
        )
    claim_id = claim_candidate.get("id")
    if not isinstance(claim_id, str) or not claim_id.startswith("cl:"):
        raise ObservationTriageError("promotion requires an explicit cl: Claim ID")
    record: Record = {
        "record_type": "claim",
        "id": claim_id,
        "claim_type": claim_candidate.get("claim_type"),
        "statement": claim_candidate.get("statement"),
        "maturity": "CANDIDATE",
        "evidence_ids": sorted(set(observation.get("evidence_candidate_ids") or [])),
        "created_by": deepcopy(actor),
        "policy_version": policy_version,
    }
    for field in (
        "entity_id",
        "relation",
        "scope",
        "applicability",
        "confidence",
        "reasoning_basis",
        "alternative_interpretations",
    ):
        if field in claim_candidate:
            record[field] = deepcopy(claim_candidate[field])
    if not record["evidence_ids"]:
        raise ObservationTriageError("promoted Claim Candidate requires Observation Evidence")
    validate_record(record)
    return record


def transition_observation(
    repository: RecordRepository,
    observation_id: str,
    action: str,
    *,
    reason: str,
    actor: Record,
    claim_candidate: Record | None = None,
    decision_id: str | None = None,
    policy_version: str = "1.0.0",
) -> dict[str, Any]:
    if action not in _ACTION_TO_STATUS:
        raise ObservationTriageError(f"unsupported observation triage action: {action}")
    if not isinstance(reason, str) or not reason.strip():
        raise ObservationTriageError("observation triage requires a non-empty reason")
    _actor_allowed(action, actor)
    connection, lock = _transactional_repository(repository)

    with connection.transaction():
        try:
            lock(observation_id)
        except ValueError as exc:
            raise ObservationTriageError(str(exc)) from exc
        observation = _observation(repository, observation_id)
        current_status = observation["status"]
        if action not in _ALLOWED_TRANSITIONS[current_status]:
            raise ObservationTriageError(
                f"invalid staged-observation transition: {current_status} via {action}"
            )
        if action == "PROMOTE_TO_CLAIM_CANDIDATE" and actor.get("actor_type") != "human":
            raise ObservationTriageError("Claim Candidate promotion requires a human actor")
        if action == "PROMOTE_TO_CLAIM_CANDIDATE" and claim_candidate is None:
            raise ObservationTriageError("Claim Candidate promotion requires claim_candidate")
        if action != "PROMOTE_TO_CLAIM_CANDIDATE" and claim_candidate is not None:
            raise ObservationTriageError(
                "claim_candidate is allowed only for PROMOTE_TO_CLAIM_CANDIDATE"
            )

        resulting_claim: Record | None = None
        if claim_candidate is not None:
            resulting_claim = _build_claim_candidate(
                observation,
                claim_candidate,
                actor=actor,
                policy_version=policy_version,
            )
            try:
                resulting_claim = CurationEngine(
                    repository,
                    policy_version=policy_version,
                ).create_claim(
                    resulting_claim,
                    actor=actor,
                    reason=f"promoted from staged observation {observation_id}: {reason}",
                )
            except CurationError as exc:
                raise ObservationTriageError(str(exc)) from exc

        target_status = _ACTION_TO_STATUS[action]
        updated = deepcopy(observation)
        updated["status"] = target_status
        validate_record(updated)
        repository.put(updated, replace=True)

        decision: Record = {
            "record_type": "observation_triage_decision",
            "id": decision_id or f"otd:{uuid4()}",
            "observation_id": observation_id,
            "action": action,
            "from_status": current_status,
            "to_status": target_status,
            "reason": reason,
            "created_by": deepcopy(actor),
            "policy_version": policy_version,
            "decided_at": _now(),
        }
        if resulting_claim is not None:
            decision["resulting_claim_id"] = resulting_claim["id"]
        validate_observation_triage_decision(decision)
        repository.put(decision)

        stored = repository.get(observation_id)
        stored_decision = repository.get(decision["id"])
        if stored != updated or stored_decision != decision:
            raise ObservationTriageError("observation triage round-trip mismatch")
        if resulting_claim is not None and repository.get(resulting_claim["id"]) != resulting_claim:
            raise ObservationTriageError("promoted Claim Candidate round-trip mismatch")

        return {
            "observation": deepcopy(stored),
            "decision": deepcopy(stored_decision),
            "claim_candidate": deepcopy(resulting_claim),
        }
