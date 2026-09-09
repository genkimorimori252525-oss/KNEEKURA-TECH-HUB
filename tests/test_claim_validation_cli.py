from __future__ import annotations

import json
import sys

from kneekura_tech_hub import claim_validation_cli
from kneekura_tech_hub.repository import MemoryRepository
from kneekura_tech_hub.service import CurationEngine


HUMAN = {"actor_type": "human", "actor_id": "cli-reviewer"}
SOURCE_ID = "src:validation:cli"
SNAPSHOT_ID = "ss:validation:cli"
EVIDENCE_ID = "ev:validation:cli"
ENTITY_ID = "ke:validation:cli"
CLAIM_ID = "cl:validation:cli"


class ClosableMemoryRepository(MemoryRepository):
    def close(self) -> None:
        pass


def _seed() -> ClosableMemoryRepository:
    repository = ClosableMemoryRepository()
    engine = CurationEngine(repository)
    engine.register_source(
        {
            "record_type": "source",
            "id": SOURCE_ID,
            "kind": "repository",
            "origin": {"provider": "fixture", "repository": "example/validation-cli"},
            "acquisition": {"level": "selected-files"},
            "license": {"state": "KNOWN", "declared_expression": "MIT"},
        },
        actor=HUMAN,
    )
    engine.register_source_snapshot(
        {
            "record_type": "source_snapshot",
            "id": SNAPSHOT_ID,
            "source_id": SOURCE_ID,
            "revision": "0123456789abcdef0123456789abcdef01234567",
            "captured_at": "2026-09-09T00:00:00Z",
            "metadata": {"fixture": True},
        },
        actor=HUMAN,
    )
    engine.register_evidence(
        {
            "record_type": "evidence",
            "id": EVIDENCE_ID,
            "source_id": SOURCE_ID,
            "source_snapshot_id": SNAPSHOT_ID,
            "locator": {
                "type": "source_lines",
                "path": "README.md",
                "line_start": 1,
                "line_end": 2,
                "content_hash": "sha256:" + "c" * 64,
            },
            "roles": ["SUPPORTS"],
        },
        actor=HUMAN,
    )
    engine.create_entity(
        {
            "record_type": "knowledge_entity",
            "id": ENTITY_ID,
            "canonical_name": "Validation CLI fixture",
            "aliases": [],
            "kinds": ["technique"],
            "abstraction_level": "L1",
            "identity_state": "CANONICAL",
            "relations": [],
        },
        actor=HUMAN,
    )
    engine.create_claim(
        {
            "record_type": "claim",
            "id": CLAIM_ID,
            "entity_id": ENTITY_ID,
            "claim_type": "DIRECT_OBSERVATION",
            "statement": "The pinned fixture contains the observed behavior.",
            "maturity": "CANDIDATE",
            "evidence_ids": [EVIDENCE_ID],
            "created_by": HUMAN,
            "policy_version": "1.0.0",
        },
        actor=HUMAN,
    )
    engine.transition_claim(
        CLAIM_ID,
        "SUPPORTED",
        actor=HUMAN,
        reason="CLI fixture support review",
    )
    return repository


def test_context_and_history_are_read_only(monkeypatch, capsys) -> None:
    repository = _seed()
    before = repository.list()
    monkeypatch.setattr(claim_validation_cli, "_repository", lambda: repository)

    monkeypatch.setattr(sys, "argv", ["kneekura-claim-validation", "context", CLAIM_ID])
    assert claim_validation_cli.main() == 0
    context = json.loads(capsys.readouterr().out)
    assert context["claim"]["maturity"] == "SUPPORTED"
    assert context["support_decisions"]
    assert context["validation_decisions"] == []
    assert repository.list() == before

    monkeypatch.setattr(
        sys,
        "argv",
        ["kneekura-claim-validation", "history", "--claim-id", CLAIM_ID],
    )
    assert claim_validation_cli.main() == 0
    assert json.loads(capsys.readouterr().out) == []
    assert repository.list() == before


def test_validate_cli_writes_one_auditable_validation_decision(monkeypatch, capsys) -> None:
    repository = _seed()
    monkeypatch.setattr(claim_validation_cli, "_repository", lambda: repository)
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "kneekura-claim-validation",
            "validate",
            CLAIM_ID,
            "--actor-id",
            "cli-reviewer",
            "--reason",
            "reproduced fixture behavior",
            "--validation-basis",
            "REPRODUCTION",
            "--validation-note",
            "Repeated the pinned fixture sequence and observed the same behavior.",
            "--independence-assessment",
            "NOT_ASSESSED",
            "--decision-id",
            "cvd:validation:cli",
        ],
    )

    assert claim_validation_cli.main() == 0
    result = json.loads(capsys.readouterr().out)
    assert result["claim"]["maturity"] == "VALIDATED"
    assert result["decision"]["id"] == "cvd:validation:cli"
    assert result["decision"]["validation_basis"] == "REPRODUCTION"
    assert result["decision"]["validated_at"] == result["claim"]["last_verified"]
    assert [item["id"] for item in repository.list("claim_validation_decision")] == [
        "cvd:validation:cli"
    ]
