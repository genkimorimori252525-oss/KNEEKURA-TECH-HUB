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
            "id": "cl:candidate",
            "entity_id": "ke:test",
            "claim_type": "INFERENCE",
            "statement": "Candidate claim",
            "maturity": "CANDIDATE",
            "evidence_ids": ["ev:test"],
            "confidence": "MEDIUM",
            "reasoning_basis": ["ev:test"],
            "created_by": {"actor_type": "ai", "actor_id": "extractor"},
            "policy_version": "1.0.0",
        },
        {
            "record_type": "claim",
            "id": "cl:validated",
            "entity_id": "ke:test",
            "claim_type": "AUTHOR_CLAIM",
            "statement": "Validated claim",
            "maturity": "VALIDATED",
            "evidence_ids": ["ev:test"],
            "last_verified": "2026-09-09T00:00:00Z",
            "created_by": {"actor_type": "human", "actor_id": "reviewer"},
            "policy_version": "1.0.0",
        },
    ]
    for record in records:
        repository.put(record)
    return repository


def test_review_claim_cli_returns_non_scalar_profile_without_writes(monkeypatch, capsys):
    repository = _repository()
    before = deepcopy(repository.list())
    monkeypatch.setattr(cli, "_open_repository", lambda dsn: repository)
    monkeypatch.setattr(
        sys,
        "argv",
        ["kneekura-hub", "review-claim", "cl:candidate", "--dsn", "ignored"],
    )

    assert cli.main() == 0
    output = json.loads(capsys.readouterr().out)

    assert output["claim_id"] == "cl:candidate"
    assert output["maturity"] == "CANDIDATE"
    assert output["evidence"]["distinct_source_count"] == 1
    assert "SINGLE_SOURCE" in output["flags"]
    assert "score" not in output
    assert "strength" not in output
    assert repository.list() == before


def test_review_claims_cli_needs_review_is_condition_based_and_read_only(monkeypatch, capsys):
    repository = _repository()
    before = deepcopy(repository.list())
    monkeypatch.setattr(cli, "_open_repository", lambda dsn: repository)
    monkeypatch.setattr(
        sys,
        "argv",
        ["kneekura-hub", "review-claims", "--needs-review", "--dsn", "ignored"],
    )

    assert cli.main() == 0
    output = json.loads(capsys.readouterr().out)

    assert [item["claim_id"] for item in output] == ["cl:candidate"]
    assert repository.list() == before


def test_review_claim_cli_rejects_missing_claim(monkeypatch, capsys):
    repository = _repository()
    monkeypatch.setattr(cli, "_open_repository", lambda dsn: repository)
    monkeypatch.setattr(
        sys,
        "argv",
        ["kneekura-hub", "review-claim", "cl:missing", "--dsn", "ignored"],
    )

    assert cli.main() == 1
    assert "missing claim" in capsys.readouterr().out
