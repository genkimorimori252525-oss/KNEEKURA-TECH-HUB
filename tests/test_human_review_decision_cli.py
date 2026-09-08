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
            "statement": "The benefit depends on workload shape.",
            "maturity": "CANDIDATE",
            "evidence_ids": ["ev:test"],
            "created_by": {"actor_type": "human", "actor_id": "reviewer"},
            "policy_version": "1.0.0",
        },
    ]
    for record in records:
        repository.put(record)
    return repository


def test_decide_claims_cli_writes_only_review_decision(monkeypatch, capsys):
    repository = _repository()
    claims_before = [deepcopy(repository.get("cl:a")), deepcopy(repository.get("cl:b"))]
    monkeypatch.setattr(cli, "_open_repository", lambda dsn: repository)
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "kneekura-hub",
            "decide-claims",
            "cl:a",
            "cl:b",
            "UNRESOLVED",
            "--reason",
            "Human review cannot yet establish contradiction.",
            "--decision-id",
            "rd:cli",
            "--actor-id",
            "reviewer",
            "--dsn",
            "ignored",
        ],
    )

    assert cli.main() == 0
    output = json.loads(capsys.readouterr().out)
    assert output["id"] == "rd:cli"
    assert output["created_by"] == {"actor_type": "human", "actor_id": "reviewer"}
    assert repository.get("cl:a") == claims_before[0]
    assert repository.get("cl:b") == claims_before[1]


def test_review_decisions_and_context_cli_are_read_only(monkeypatch, capsys):
    repository = _repository()
    repository.put(
        {
            "record_type": "review_decision",
            "id": "rd:cli",
            "source_claim_id": "cl:a",
            "target_claim_id": "cl:b",
            "decision": "UNRESOLVED",
            "rationale": "More review is required.",
            "created_by": {"actor_type": "human", "actor_id": "reviewer"},
            "policy_version": "1.0.0",
            "decided_at": "2026-09-09T00:00:00+00:00",
        }
    )
    before = deepcopy(repository.list())
    monkeypatch.setattr(cli, "_open_repository", lambda dsn: repository)

    monkeypatch.setattr(
        sys,
        "argv",
        ["kneekura-hub", "review-decisions", "--claim-id", "cl:a", "--dsn", "ignored"],
    )
    assert cli.main() == 0
    decisions = json.loads(capsys.readouterr().out)
    assert [item["id"] for item in decisions] == ["rd:cli"]

    monkeypatch.setattr(
        sys,
        "argv",
        ["kneekura-hub", "decision-context", "cl:a", "--dsn", "ignored"],
    )
    assert cli.main() == 0
    context = json.loads(capsys.readouterr().out)
    assert context["comparison"]["claim_count"] == 2
    assert context["active_decision_count"] == 1
    assert context["active_decisions"][0]["decision"] == "UNRESOLVED"
    assert repository.list() == before


def test_decide_claims_cli_rejects_ai_actor(monkeypatch, capsys):
    repository = _repository()
    monkeypatch.setattr(cli, "_open_repository", lambda dsn: repository)
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "kneekura-hub",
            "decide-claims",
            "cl:a",
            "cl:b",
            "COMPATIBLE",
            "--reason",
            "AI should not be allowed to make this decision.",
            "--actor-type",
            "ai",
            "--actor-id",
            "bot",
            "--dsn",
            "ignored",
        ],
    )

    assert cli.main() == 1
    assert "human actor" in capsys.readouterr().out
