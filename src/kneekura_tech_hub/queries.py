from __future__ import annotations

from collections.abc import Mapping
from copy import deepcopy
from typing import Any

from .projection import RelationView, project_relations, resolve_entity_id
from .repository import Record, RecordRepository


class QueryError(ValueError):
    """Raised when a semantic query cannot be answered safely."""


def _entity(repository: RecordRepository, entity_id: str) -> Record:
    resolved = resolve_entity_id(repository, entity_id)
    entity = repository.get(resolved)
    if entity is None or entity.get("record_type") != "knowledge_entity":
        raise QueryError(f"unknown knowledge entity: {resolved}")
    return entity


def _summary(entity: Record) -> Record:
    return {
        "id": entity["id"],
        "canonical_name": entity["canonical_name"],
        "kinds": list(entity.get("kinds", [])),
        "abstraction_level": entity["abstraction_level"],
        "identity_state": entity["identity_state"],
    }


def _require_problem(entity: Record) -> None:
    if "problem" not in entity.get("kinds", []):
        raise QueryError(f"entity is not classified as a problem: {entity['id']}")


def _normalize_context(context: Mapping[str, Any] | None) -> dict[str, Any]:
    if context is None:
        return {}
    if not isinstance(context, Mapping):
        raise QueryError("context must be a mapping")
    normalized = dict(context)
    if any(not isinstance(key, str) for key in normalized):
        raise QueryError("context keys must be strings")
    return deepcopy(normalized)


def _applicability_matches(applicability: object, context: Mapping[str, Any]) -> bool:
    if not isinstance(applicability, Mapping):
        return False
    return all(key in applicability and applicability[key] == value for key, value in context.items())


def contextual_claims_for_entity(
    repository: RecordRepository,
    entity_id: str,
    *,
    context: Mapping[str, Any] | None = None,
) -> Record:
    """Return trusted entity Claims matching explicit applicability context.

    This query deliberately performs no ranking, fuzzy matching, popularity weighting,
    semantic guessing, or fallback. A supplied context is an exact subset constraint on
    the immutable ``applicability`` mapping of VALIDATED entity Claims.
    """

    entity = _entity(repository, entity_id)
    normalized_context = _normalize_context(context)

    validated = [
        claim
        for claim in repository.list("claim")
        if claim.get("entity_id") == entity["id"]
        and not claim.get("relation")
        and claim.get("maturity") == "VALIDATED"
    ]
    validated.sort(key=lambda claim: claim["id"])

    if normalized_context:
        matches = [
            claim
            for claim in validated
            if _applicability_matches(claim.get("applicability", {}), normalized_context)
        ]
        if not matches:
            resolution = "NO_MATCH"
        elif len(matches) == 1:
            resolution = "ONE_MATCH"
        else:
            resolution = "MULTIPLE_MATCHES"
    else:
        matches = list(validated)
        if not matches:
            resolution = "NO_VALIDATED_CLAIMS"
        elif len(matches) == 1:
            resolution = "ONE_MATCH"
        else:
            resolution = "CONTEXT_REQUIRED"

    return {
        "subject": _summary(entity),
        "context": normalized_context,
        "resolution": resolution,
        "validated_claim_count": len(validated),
        "candidate_count": len(matches),
        "candidate_claim_ids": [claim["id"] for claim in matches],
        "claims": [deepcopy(claim) for claim in matches],
    }


def solutions_for_problem(
    repository: RecordRepository,
    problem_id: str,
    *,
    view: RelationView = "validated",
) -> list[Record]:
    """Return entities with explicit ``solves`` Claims pointing at one Problem."""

    problem = _entity(repository, problem_id)
    _require_problem(problem)
    results: list[Record] = []

    for edge in project_relations(
        repository,
        view=view,
        entity_id=problem["id"],
        relation_type="solves",
        direction="in",
    ):
        target = _entity(repository, edge["relation"]["target_entity_id"])
        _require_problem(target)
        solution = _entity(repository, edge["relation"]["source_entity_id"])
        results.append(
            {
                "solution": _summary(solution),
                "problem": _summary(target),
                "relation_claim": deepcopy(edge),
            }
        )
    return results


def problems_solved_by(
    repository: RecordRepository,
    entity_id: str,
    *,
    view: RelationView = "validated",
) -> list[Record]:
    """Return Problems reached by explicit outgoing ``solves`` Claims."""

    subject = _entity(repository, entity_id)
    results: list[Record] = []

    for edge in project_relations(
        repository,
        view=view,
        entity_id=subject["id"],
        relation_type="solves",
        direction="out",
    ):
        problem = _entity(repository, edge["relation"]["target_entity_id"])
        _require_problem(problem)
        solution = _entity(repository, edge["relation"]["source_entity_id"])
        results.append(
            {
                "solution": _summary(solution),
                "problem": _summary(problem),
                "relation_claim": deepcopy(edge),
            }
        )
    return results


def requirements_for(
    repository: RecordRepository,
    entity_id: str,
    *,
    view: RelationView = "validated",
) -> list[Record]:
    """Return explicit outgoing ``requires`` relationships for one entity."""

    subject = _entity(repository, entity_id)
    results: list[Record] = []

    for edge in project_relations(
        repository,
        view=view,
        entity_id=subject["id"],
        relation_type="requires",
        direction="out",
    ):
        requirement = _entity(repository, edge["relation"]["target_entity_id"])
        requiring = _entity(repository, edge["relation"]["source_entity_id"])
        results.append(
            {
                "entity": _summary(requiring),
                "requirement": _summary(requirement),
                "relation_claim": deepcopy(edge),
            }
        )
    return results
