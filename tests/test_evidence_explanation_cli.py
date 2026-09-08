from __future__ import annotations

import json
import sys

from kneekura_tech_hub import cli
from kneekura_tech_hub.repository import MemoryRepository


class ClosableMemoryRepository(MemoryRepository):
    def close(self) -> None:
        pass


def _repository() -> ClosableMemoryRepository:
    repository = ClosableMemoryRepository()
    for record in (
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
                "line_end": 2,
                "content_hash": "sha256:test",
            },
            "roles": ["SUPPORTS"],
        },
        {
            "record_type": "claim",
            "id": "cl:test",
            "entity_id": "ke:test",
            "claim_type": "AUTHOR_CLAIM",
            "statement": "Example claim",
            "maturity": "CANDIDATE",
            "evidence_ids": ["ev:test"],
            "created_by": {"actor_type": "ai", "actor_id": "extractor"},
            "policy_version": "1.0.0",
        },
    ):
        repository.put(record)
    return repository


def test_explain_claim_cli_returns_full_chain_without_writes(monkeypatch, capsys):
    repository = _repository()
    before = repository.list()
    monkeypatch.setattr(cli, "_open_repository", lambda dsn: repository)
    monkeypatch.setattr(
        sys,
        "argv",
        ["kneekura-hub", "explain-claim", "cl:test", "--dsn", "ignored"],
    )

    assert cli.main() == 0
    output = json.loads(capsys.readouterr().out)

    assert output["claim"]["id"] == "cl:test"
    assert output["evidence_count"] == 1
    assert output["evidence_chains"][0]["evidence"]["id"] == "ev:test"
    assert output["evidence_chains"][0]["source_snapshot"]["id"] == "ss:test"
    assert output["evidence_chains"][0]["source"]["id"] == "src:test"
    assert repository.list() == before


def test_explain_claim_cli_rejects_missing_claim(monkeypatch, capsys):
    repository = _repository()
    monkeypatch.setattr(cli, "_open_repository", lambda dsn: repository)
    monkeypatch.setattr(
        sys,
        "argv",
        ["kneekura-hub", "explain-claim", "cl:missing", "--dsn", "ignored"],
    )

    assert cli.main() == 1
    assert "missing claim" in capsys.readouterr().out
