from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from .repository import RecordRepository
from .validator import validate_record


Record = dict[str, Any]


class CurationError(ValueError):
    pass


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _event_id() -> str:
    return f"ce:{uuid4()}"


def _claim_subject_key(claim: Record) -> tuple[str, ...]:
    if "entity_id" in claim:
        return ("entity", claim["entity_id"])
    relation = claim["relation"]
    return (
        "relation",
        relation["source_entity_id"],
        relation["relation_type"],
        relation["target_entity_id"],
    )


class CurationEngine:
    """Policy-aware orchestration layer for curated Hub records."""

    _CLAIM_TRANSITIONS: dict[str, set[str]] = {
        "CANDIDATE": {"SUPPORTED", "REJECTED"},
        "SUPPORTED": {"VALIDATED", "CHALLENGED", "REJECTED"},
        "VALIDATED": {"CHALLENGED", "SUPERSEDED"},
        "CHALLENGED": {"SUPPORTED", "VALIDATED", "SUPERSEDED", "REJECTED"},
        "SUPERSEDED": set(),
        "REJECTED": set(),
    }

    def __init__(self, repository: RecordRepository, *, policy_version: str = "1.0.0") -> None:
        self.repository = repository
        self.policy_version = policy_version

    def get(self, record_id: str) -> Record | None:
        return self.repository.get(record_id)

    def list(self, record_type: str | None = None) -> list[Record]:
        return self.repository.list(record_type)

    def register_source(self, source: Record, *, actor: Record) -> Record:
        self._require_type(source, "source")
        validate_record(source)
        self.repository.put(source)
        self._append_event("SOURCE_ACQUIRE", actor, [source["id"]], reason=None)
        return deepcopy(source)

    def register_source_snapshot(self, snapshot: Record, *, actor: Record) -> Record:
        self._require_type(snapshot, "source_snapshot")
        self._require_existing(snapshot["source_id"], "source")
        validate_record(snapshot)
        self.repository.put(snapshot)
        self._append_event(
            "SOURCE_ACQUIRE",
            actor,
            [snapshot["source_id"], snapshot["id"]],
            reason="immutable source snapshot pinned",
        )
        return deepcopy(snapshot)

    def register_evidence(self, evidence: Record, *, actor: Record) -> Record:
        self._require_type(evidence, "evidence")
        source = self._require_existing(evidence["source_id"], "source")
        snapshot = self._require_existing(evidence["source_snapshot_id"], "source_snapshot")
        if snapshot["source_id"] != source["id"]:
            raise CurationError("evidence snapshot does not belong to evidence source")
        validate_record(evidence)
        self.repository.put(evidence)
        return deepcopy(evidence)

    def create_entity(self, entity: Record, *, actor: Record, reason: str | None = None) -> Record:
        self._require_type(entity, "knowledge_entity")
        self._require_human(actor, "canonical entity creation")
        if entity.get("identity_state") in {"MERGED", "RETIRED"}:
            raise CurationError("new entities cannot start as MERGED or RETIRED")
        self._require_entity_targets_exist(entity)
        validate_record(entity)
        self.repository.put(entity)
        self._append_event("ENTITY_CREATE", actor, [entity["id"]], reason=reason)
        return deepcopy(entity)

    def stage_observation(self, observation: Record, *, actor: Record) -> Record:
        self._require_type(observation, "staged_observation")
        self._require_actor_match(observation.get("created_by"), actor, "observation created_by")
        source = self._require_existing(observation["source_id"], "source")

        evidence_ids = observation.get("evidence_candidate_ids") or []
        snapshots: set[str] = set()
        for evidence_id in evidence_ids:
            evidence = self._require_existing(evidence_id, "evidence")
            if evidence["source_id"] != source["id"]:
                raise CurationError("observation evidence does not belong to observation source")
            snapshots.add(evidence["source_snapshot_id"])

        if len(snapshots) != 1:
            raise CurationError("staged observation must resolve to exactly one source snapshot")

        validate_record(observation)
        self.repository.put(observation)
        return deepcopy(observation)

    def create_claim(self, claim: Record, *, actor: Record, reason: str | None = None) -> Record:
        self._require_type(claim, "claim")
        self._require_actor_match(claim.get("created_by"), actor, "claim created_by")
        if claim.get("maturity") != "CANDIDATE":
            raise CurationError("new claims must start at CANDIDATE")
        self._require_claim_subject_exists(claim)
        evidence_ids = claim.get("evidence_ids", [])
        if "relation" in claim and not evidence_ids:
            raise CurationError("relation claims require at least one evidence_id")
        self._require_evidence_exists(evidence_ids)
        validate_record(claim)
        self.repository.put(claim)
        self._append_event("CLAIM_CREATE", actor, [claim["id"]], reason=reason)
        return deepcopy(claim)

    def transition_claim(
        self,
        claim_id: str,
        target_maturity: str,
        *,
        actor: Record,
        reason: str,
        superseded_by: str | None = None,
    ) -> Record:
        claim = self._require_existing(claim_id, "claim")
        current = claim["maturity"]
        if target_maturity not in self._CLAIM_TRANSITIONS[current]:
            raise CurationError(f"invalid claim transition: {current} -> {target_maturity}")
        if target_maturity == "VALIDATED":
            self._require_human(actor, "VALIDATED promotion")
        if target_maturity == "SUPERSEDED":
            if not superseded_by:
                raise CurationError("SUPERSEDED requires superseded_by")
            successor = self._require_existing(superseded_by, "claim")
            if _claim_subject_key(successor) != _claim_subject_key(claim):
                raise CurationError("superseding claim must describe the same claim subject")
            claim["superseded_by"] = superseded_by
        claim["maturity"] = target_maturity
        if target_maturity == "VALIDATED":
            claim["last_verified"] = _now()
        validate_record(claim)
        self.repository.put(claim, replace=True)
        operation = {
            "CHALLENGED": "CLAIM_CHALLENGE",
            "SUPERSEDED": "CLAIM_SUPERSEDE",
            "REJECTED": "CLAIM_REJECT",
        }.get(target_maturity, "CLAIM_PROMOTE")
        self._append_event(operation, actor, [claim_id], reason=reason)
        return deepcopy(claim)

    def merge_entities(
        self,
        survivor_id: str,
        merged_id: str,
        *,
        actor: Record,
        reason: str,
    ) -> tuple[Record, Record]:
        self._require_human(actor, "entity merge")
        if survivor_id == merged_id:
            raise CurationError("cannot merge an entity into itself")
        survivor = self._require_existing(survivor_id, "knowledge_entity")
        merged = self._require_existing(merged_id, "knowledge_entity")
        if survivor["identity_state"] == "MERGED" or merged["identity_state"] == "MERGED":
            raise CurationError("cannot merge an entity that is already merged")
        merged["identity_state"] = "MERGED"
        merged["redirect_to"] = survivor_id
        validate_record(merged)
        self.repository.put(merged, replace=True)
        self._append_event(
            "ENTITY_MERGE",
            actor,
            [survivor_id, merged_id],
            reason=reason,
            reversible=True,
        )
        return deepcopy(survivor), deepcopy(merged)

    def _append_event(
        self,
        operation: str,
        actor: Record,
        subject_ids: list[str],
        *,
        reason: str | None,
        reversible: bool = False,
    ) -> None:
        event: Record = {
            "record_type": "curation_event",
            "id": _event_id(),
            "operation": operation,
            "actor": actor,
            "subject_ids": subject_ids,
            "reason": reason,
            "policy_version": self.policy_version,
            "occurred_at": _now(),
            "reversible": reversible,
        }
        validate_record(event)
        self.repository.put(event)

    def _require_entity_targets_exist(self, entity: Record) -> None:
        for relation in entity.get("relations", []):
            target = relation["target"]
            self._require_existing(target, "knowledge_entity")

    def _require_claim_subject_exists(self, claim: Record) -> None:
        if "entity_id" in claim:
            self._require_existing(claim["entity_id"], "knowledge_entity")
            return

        relation = claim.get("relation")
        if not isinstance(relation, dict):
            raise CurationError("claim requires exactly one entity or relation subject")
        source_id = relation["source_entity_id"]
        target_id = relation["target_entity_id"]
        if source_id == target_id:
            raise CurationError("relation claim endpoints must be different entities")
        self._require_existing(source_id, "knowledge_entity")
        self._require_existing(target_id, "knowledge_entity")

    def _require_evidence_exists(self, evidence_ids: list[str]) -> None:
        for evidence_id in evidence_ids:
            self._require_existing(evidence_id, "evidence")

    def _require_existing(self, record_id: str, expected_type: str) -> Record:
        record = self.repository.get(record_id)
        if record is None:
            raise CurationError(f"unknown record: {record_id}")
        self._require_type(record, expected_type)
        return record

    @staticmethod
    def _require_actor_match(record_actor: Record | None, actor: Record, field: str) -> None:
        if record_actor != actor:
            raise CurationError(f"{field} must match the acting identity")

    @staticmethod
    def _require_type(record: Record, expected_type: str) -> None:
        actual = record.get("record_type")
        if actual != expected_type:
            raise CurationError(f"expected {expected_type}, got {actual!r}")

    @staticmethod
    def _require_human(actor: Record, action: str) -> None:
        if actor.get("actor_type") != "human":
            raise CurationError(f"{action} requires a human actor")
