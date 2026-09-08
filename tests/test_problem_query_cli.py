from __future__ import annotations

import json
import sys

import pytest

from kneekura_tech_hub import cli
from kneekura_tech_hub.repository import MemoryRepository


class ClosableMemoryRepository(MemoryRepository):
    def close(self) -> None:
        pass


def _entity(entity_id: str, kind: str = "technique") -> dict:
    return {
        "record_type": "knowledge_entity",
        "id": entity_id,
        "canonical_name": entity_id,
        "aliases": [],
        "kinds": [kind],
        "abstraction_level": "L1",
        "identity_state": "CANONICAL",
        "relations": [],
    }


def _claim(claim_id: str, relation_type: str, target: str) -> dict:
    return {
        "record_type": "claim",
        "id": claim_id,
        "relation": {
            "source_entity_id": "ke:solution",
            "relation_type": relation_type,
            "target_entity_id": target,
        },
        "claim_type": "INFERENCE",
        "statement": claim_id,
        "maturity": "VALIDATED",
        "evidence_ids": ["ev:test"],
        "confidence": "MEDIUM",
        "reasoning_basis": ["ev:test"],
        "created_by": {"actor_type": "ai", "actor_id": "extractor"},
        "policy_version": "1.0.0",
    }


def _repository() -> ClosableMemoryRepository:
    repository = ClosableMemoryRepository()
    for record in (
        _entity("ke:solution"),
        _entity("ke:problem", "problem"),
        _entity("ke:requirement"),
        _claim("cl:solves", "solves", "ke:problem"),
        _claim("cl:requires", "requires", "ke:requirement"),
    ):
        repository.put(record)
    return repository


@pytest.mark.parametrize(
    ("argv", "result_key", "expected_id"),
    [
        (["solutions", "ke:problem"], "solution", "ke:solution"),
        (["solved-problems", "ke:solution"], "problem", "ke:problem"),
        (["requirements", "ke:solution"], "requirement", "ke:requirement"),
    ],
)
def test_problem_query_cli_returns_evidence_aware_results_without_writes(
    monkeypatch,
    capsys,
    argv: list[str],
    result_key: str,
    expected_id: str,
):
    repository = _repository()
    before = repository.list()
    monkeypatch.setattr(cli, "_open_repository", lambda dsn: repository)
    monkeypatch.setattr(
        sys,
        "argv",
        ["kneekura-hub", *argv, "--view", "validated", "--dsn", "ignored"],
    )

    assert cli.main() == 0
    output = json.loads(capsys.readouterr().out)

    assert output[0][result_key]["id"] == expected_id
    assert output[0]["relation_claim"]["evidence_ids"] == ["ev:test"]
    assert repository.list() == before


def test_solutions_cli_rejects_non_problem_query(monkeypatch, capsys):
    repository = _repository()
    before = repository.list()
    monkeypatch.setattr(cli, "_open_repository", lambda dsn: repository)
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "kneekura-hub",
            "solutions",
            "ke:solution",
            "--view",
            "research",
            "--dsn",
            "ignored",
        ],
    )

    assert cli.main() == 1
    assert "not classified as a problem" in capsys.readouterr().out
    assert repository.list() == before
