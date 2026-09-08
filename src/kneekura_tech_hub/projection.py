from __future__ import annotations

from copy import deepcopy
from typing import Literal

from .repository import Record, RecordRepository


RelationView = Literal["validated", "research", "challenged", "history"]
Direction = Literal["any", "out", "in"]

RELATION_VIEWS: dict[str, frozenset[str]] = {
    "validated": frozenset({"VALIDATED"}),
    "research": frozenset({"CANDIDATE", "SUPPORTED", "VALIDATED", "CHALLENGED"}),
    "challenged": frozenset({"CHALLENGED"}),
    "history": frozenset(
        {"CANDIDATE", "SUPPORTED", "VALIDATED", "CHALLENGED", "SUPERSEDED", "REJECTED"}
    ),
}


class ProjectionError(ValueError):
    """Raised when canonical records cannot be projected safely."""


def resolve_entity_id(repository: RecordRepository, entity_id: str) -> str:
    """Resolve a Knowledge Entity through MERGED redirects without rewriting history."""

    current = entity_id
    visited: set[str] = set()
    while True:
        if current in visited:
            raise ProjectionError(f"entity redirect cycle detected at {current}")
        visited.add(current)

        entity = repository.get(current)
        if entity is None:
            raise ProjectionError(f"unknown knowledge entity: {current}")
        if entity.get("record_type") != "knowledge_entity":
            raise ProjectionError(f"relation endpoint is not a knowledge entity: {current}")

        if entity.get("identity_state") != "MERGED":
            return current

        redirect = entity.get("redirect_to")
        if not isinstance(redirect, str) or not redirect:
            raise ProjectionError(f"merged entity has no redirect target: {current}")
        current = redirect


def _matches_entity(
    relation: Record,
    entity_id: str | None,
    direction: Direction,
) -> bool:
    if entity_id is None:
        return True
    if direction == "out":
        return relation["source_entity_id"] == entity_id
    if direction == "in":
        return relation["target_entity_id"] == entity_id
    return entity_id in {relation["source_entity_id"], relation["target_entity_id"]}


def project_relations(
    repository: RecordRepository,
    *,
    view: RelationView = "validated",
    entity_id: str | None = None,
    relation_type: str | None = None,
    direction: Direction = "any",
) -> list[Record]:
    """Build a disposable relation read model from canonical Claim records.

    One projected row corresponds to one Relation Claim. Competing Claims are not
    deduplicated because their Evidence, maturity, and provenance are meaningful.
    Entity redirects are resolved only in the read model; asserted endpoints remain
    available unchanged under ``asserted_relation``.
    """

    if view not in RELATION_VIEWS:
        raise ProjectionError(f"unknown relation view: {view}")
    if direction not in {"any", "out", "in"}:
        raise ProjectionError(f"unknown relation direction: {direction}")

    query_entity = resolve_entity_id(repository, entity_id) if entity_id else None
    allowed_maturities = RELATION_VIEWS[view]
    projected: list[Record] = []

    for claim in repository.list("claim"):
        asserted = claim.get("relation")
        if not isinstance(asserted, dict):
            continue
        if claim.get("maturity") not in allowed_maturities:
            continue
        if relation_type is not None and asserted.get("relation_type") != relation_type:
            continue

        resolved: Record = {
            "source_entity_id": resolve_entity_id(repository, asserted["source_entity_id"]),
            "relation_type": asserted["relation_type"],
            "target_entity_id": resolve_entity_id(repository, asserted["target_entity_id"]),
        }
        if not _matches_entity(resolved, query_entity, direction):
            continue

        edge: Record = {
            "claim_id": claim["id"],
            "asserted_relation": deepcopy(asserted),
            "relation": resolved,
            "redirected": asserted != resolved,
            "maturity": claim["maturity"],
            "claim_type": claim["claim_type"],
            "statement": claim["statement"],
            "evidence_ids": list(claim.get("evidence_ids", [])),
            "created_by": deepcopy(claim["created_by"]),
        }
        for optional in (
            "confidence",
            "scope",
            "applicability",
            "alternative_interpretations",
            "last_verified",
            "superseded_by",
        ):
            if optional in claim:
                edge[optional] = deepcopy(claim[optional])
        projected.append(edge)

    return sorted(
        projected,
        key=lambda edge: (
            edge["relation"]["source_entity_id"],
            edge["relation"]["relation_type"],
            edge["relation"]["target_entity_id"],
            edge["maturity"],
            edge["claim_id"],
        ),
    )
