from __future__ import annotations

import json
import sys
from copy import deepcopy

from kneekura_tech_hub import cli
from kneekura_tech_hub.repository import MemoryRepository


class ClosableMemoryRepository(MemoryRepository):
    def close(self) -> None:
        pass


def _repository() -> ClosableMemoryRepository:
    repository = ClosableMemoryRepository()
    records = [
        {
            "record_type": "source",
            "id": "src:test",
            "kind": "repository",
            "origin": {"provider": "github", "repository": "example/repo"},
            "acquisition": {"level": "snapshot"},
            "license": {"state": "KNOWN", "declared_expression": "MIT"},
        },
        {
            "record_type": "source_snapshot",
            "id": "ss:test",
            "source_id": "src:test",
            "revision": "0123456789abcdef",
            "captured_at": "2026-09-09T00:00:00Z",
        },
        {
            "record_type": "evidence",
            "id": "ev:test",
            "source_id": "src:test",
            "source_snapshot_id": "ss:test",
            "locator": {
                "type": "source_lines",
                "path": "README.md",
                "line_start": 1,
                "line_end": 1,
                "content_hash": "sha256:test",
            },
            "roles": ["SUPPORTS"],
        },
        {
            "record_type": "claim",
            "id": "cl:a",
            "entity_id": "ke:test",
            "claim_type": "INFERENCE",
            "statement": "The technique may reduce repeated work.",
            "maturity": "CANDIDATE",
            "evidence_ids": ["ev:test"],
            "confidence": "MEDIUM",
            "reasoning_basis": ["ev:test"],
            "created_by": {"actor_type": "ai", "actor_id": "a"},
            "policy_version": "1.0.0",
        },
        {
            "record_type": "claim",
            "id": "cl:b",
            "entity_id": "ke:test",
            "claim_type": "JUDGMENT",
            "statement": "The technique may increase maintenance cost.",
            "maturity": "SUPPORTED",
            "evidence_ids": ["ev:test"],
            "created_by": {"actor_type": "human", "actor_id": "reviewer"},
            "policy_version": "1.0.0",
        },
    ]
    for record in records:
        repository.put(record)
    return repository


def test_compare_claim_cli_returns_group_without_winner_or_writes(monkeypatch, capsys):
    repository = _repository()
    before = deepcopy(repository.list())
    monkeypatch.setattr(cli, "_open_repository", lambda dsn: repository)
    monkeypatch.setattr(
        sys,
        "argv",
        ["kneekura-hub", "compare-claim", "cl:a", "--dsn", "ignored"],
    )

    assert cli.main() == 0
    output = json.loads(capsys.readouterr().out)

    assert output["claim_count"] == 2
    assert output["active_claim_count"] == 2
    assert output["needs_review"] is True
    assert "MULTIPLE_ACTIVE_CLAIMS" in output["flags"]
    assert "STATEMENTS_DIFFER" in output["flags"]
    assert "winner" not in output
    assert "preferred_claim_id" not in output
    assert repository.list() == before


def test_compare_claims_cli_filters_multiple_review_groups_without_ranking(monkeypatch, capsys):
    repository = _repository()
    before = deepcopy(repository.list())
    monkeypatch.setattr(cli, "_open_repository", lambda dsn: repository)
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "kneekura-hub",
            "compare-claims",
            "--multiple-only",
            "--needs-review",
            "--dsn",
            "ignored",
        ],
    )

    assert cli.main() == 0
    output = json.loads(capsys.readouterr().out)

    assert len(output) == 1
    assert output[0]["subject"] == {"kind": "entity", "entity_id": "ke:test"}
    assert "score" not in output[0]
    assert repository.list() == before


def test_compare_claim_cli_rejects_missing_claim(monkeypatch, capsys):
    repository = _repository()
    monkeypatch.setattr(cli, "_open_repository", lambda dsn: repository)
    monkeypatch.setattr(
        sys,
        "argv",
        ["kneekura-hub", "compare-claim", "cl:missing", "--dsn", "ignored"],
    )

    assert cli.main() == 1
    assert "missing claim" in capsys.readouterr().out
