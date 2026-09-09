from __future__ import annotations

from copy import deepcopy

from .observation_triage import (
    ObservationTriageError,
    _now,
    _observation,
    validate_observation_triage_decision,
)
from .repository import Record, RecordRepository
from .validator import validate_record


class ObservationCandidateAttachmentError(ValueError):
    """Raised when a TRIAGED Observation cannot join an existing Claim Candidate."""


def _human_actor(actor: Record) -> None:
    if set(actor) - {"actor_type", "actor_id", "version"}:
        raise ObservationCandidateAttachmentError("attachment actor contains unsupported fields")
    if actor.get("actor_type") != "human":
        raise ObservationCandidateAttachmentError(
            "attaching an Observation to a Claim Candidate requires a human actor"
        )


def attach_observation_to_candidate_claim(
    repository: RecordRepository,
    observation_id: str,
    claim_id: str,
    *,
    actor: Record,
    reason: str,
    decision_id: str,
    policy_version: str = "1.0.0",
) -> dict:
    """Promote one TRIAGED Observation into an existing CANDIDATE Claim.

    The operation deliberately reuses the existing
    ``PROMOTE_TO_CLAIM_CANDIDATE`` triage decision vocabulary. The difference is
    only whether the human creates a new Candidate or attaches this Observation's
    immutable Evidence set to an already-existing Candidate.
    """

    _human_actor(actor)
    if not isinstance(reason, str) or not reason.strip():
        raise ObservationCandidateAttachmentError("attachment requires a non-empty reason")
    if not isinstance(decision_id, str) or not decision_id.startswith("otd:"):
        raise ObservationCandidateAttachmentError("attachment requires an explicit otd: decision ID")

    connection = getattr(repository, "connection", None)
    lock_observation = getattr(repository, "lock_observation_for_triage", None)
    if connection is None or not callable(lock_observation):
        raise ObservationCandidateAttachmentError(
            "Observation attachment requires transactional PostgreSQL triage repository"
        )

    with connection.transaction():
        try:
            lock_observation(observation_id)
        except ValueError as exc:
            raise ObservationCandidateAttachmentError(str(exc)) from exc

        observation = _observation(repository, observation_id)
        if observation["status"] != "TRIAGED":
            raise ObservationCandidateAttachmentError(
                f"Observation attachment requires TRIAGED status, got {observation['status']}"
            )

        locked = connection.execute(
            "SELECT id FROM claim WHERE id=%s FOR UPDATE",
            (claim_id,),
        ).fetchone()
        if locked is None:
            raise ObservationCandidateAttachmentError(f"missing claim: {claim_id}")

        claim = repository.get(claim_id)
        if claim is None or claim.get("record_type") != "claim":
            raise ObservationCandidateAttachmentError(f"missing claim: {claim_id}")
        validate_record(claim)
        if claim["maturity"] != "CANDIDATE":
            raise ObservationCandidateAttachmentError(
                f"Observation attachment requires CANDIDATE maturity, got {claim['maturity']}"
            )

        incoming_ids = sorted(set(observation.get("evidence_candidate_ids") or []))
        if not incoming_ids:
            raise ObservationCandidateAttachmentError(
                "Observation attachment requires immutable Observation Evidence"
            )

        for evidence_id in incoming_ids:
            evidence = repository.get(evidence_id)
            if evidence is None or evidence.get("record_type") != "evidence":
                raise ObservationCandidateAttachmentError(
                    f"Observation references missing Evidence: {evidence_id}"
                )
            validate_record(evidence)
            if evidence["source_id"] != observation["source_id"]:
                raise ObservationCandidateAttachmentError(
                    f"Observation/Evidence Source mismatch: {observation_id} -> {evidence_id}"
                )

        existing_ids = sorted(set(claim.get("evidence_ids") or []))
        added_ids = sorted(set(incoming_ids) - set(existing_ids))
        if not added_ids:
            raise ObservationCandidateAttachmentError(
                "Observation contributes no new Evidence to the target Claim Candidate"
            )

        updated_claim = deepcopy(claim)
        updated_claim["evidence_ids"] = sorted(set(existing_ids) | set(incoming_ids))
        validate_record(updated_claim)
        repository.put(updated_claim, replace=True)

        updated_observation = deepcopy(observation)
        updated_observation["status"] = "PROMOTED"
        validate_record(updated_observation)
        repository.put(updated_observation, replace=True)

        decision: Record = {
            "record_type": "observation_triage_decision",
            "id": decision_id,
            "observation_id": observation_id,
            "action": "PROMOTE_TO_CLAIM_CANDIDATE",
            "from_status": "TRIAGED",
            "to_status": "PROMOTED",
            "reason": reason.strip(),
            "created_by": deepcopy(actor),
            "resulting_claim_id": claim_id,
            "policy_version": policy_version,
            "decided_at": _now(),
        }
        try:
            validate_observation_triage_decision(decision)
        except ObservationTriageError as exc:
            raise ObservationCandidateAttachmentError(str(exc)) from exc
        repository.put(decision)

        stored_claim = repository.get(claim_id)
        stored_observation = repository.get(observation_id)
        stored_decision = repository.get(decision_id)
        if stored_claim != updated_claim:
            raise ObservationCandidateAttachmentError("Claim Candidate round-trip mismatch")
        if stored_observation != updated_observation:
            raise ObservationCandidateAttachmentError("Observation round-trip mismatch")
        if stored_decision != decision:
            raise ObservationCandidateAttachmentError("triage decision round-trip mismatch")

        return {
            "claim_candidate": deepcopy(stored_claim),
            "observation": deepcopy(stored_observation),
            "decision": deepcopy(stored_decision),
            "added_evidence_ids": added_ids,
        }
