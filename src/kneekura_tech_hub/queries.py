from __future__ import annotations

from copy import deepcopy

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
