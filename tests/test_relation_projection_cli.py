from __future__ import annotations

import json
import sys

from kneekura_tech_hub import cli
from kneekura_tech_hub.projection import project_relations
from kneekura_tech_hub.repository import MemoryRepository


class ClosableMemoryRepository(MemoryRepository):
    def close(self) -> None:
        pass


def _entity(entity_id: str) -> dict:
    return {
        "record_type": "knowledge_entity",
        "id": entity_id,
        "canonical_name": entity_id,
        "aliases": [],
        "kinds": ["technique"],
        "abstraction_level": "L1",
        "identity_state": "CANONICAL",
        "relations": [],
    }


def _repository() -> ClosableMemoryRepository:
    repository = ClosableMemoryRepository()
    repository.put(_entity("ke:a"))
    repository.put(_entity("ke:b"))
    repository.put(
        {
            "record_type": "claim",
            "id": "cl:edge",
            "relation": {
                "source_entity_id": "ke:a",
                "relation_type": "requires",
                "target_entity_id": "ke:b",
            },
            "claim_type": "INFERENCE",
            "statement": "A requires B in this test context.",
            "maturity": "VALIDATED",
            "evidence_ids": ["ev:test"],
            "confidence": "MEDIUM",
            "reasoning_basis": ["ev:test"],
            "created_by": {"actor_type": "ai", "actor_id": "extractor"},
            "policy_version": "1.0.0",
        }
    )
    return repository


def test_projection_does_not_mutate_any_canonical_record():
    repository = _repository()
    before = repository.list()

    for view in ("validated", "research", "challenged", "history"):
        project_relations(repository, view=view)

    assert repository.list() == before


def test_relations_cli_returns_projection_without_writes(monkeypatch, capsys):
    repository = _repository()
    before = repository.list()
    monkeypatch.setattr(cli, "_open_repository", lambda dsn: repository)
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "kneekura-hub",
            "relations",
            "--view",
            "validated",
            "--entity-id",
            "ke:a",
            "--direction",
            "out",
            "--dsn",
            "ignored",
        ],
    )

    assert cli.main() == 0
    output = json.loads(capsys.readouterr().out)

    assert [edge["claim_id"] for edge in output] == ["cl:edge"]
    assert output[0]["relation"]["relation_type"] == "requires"
    assert repository.list() == before
