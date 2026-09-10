from __future__ import annotations

import json
import sys

from kneekura_tech_hub import guidance_cli
from kneekura_tech_hub.repository import MemoryRepository


ENTITY_ID = "ke:guidance:cache-policy"
GO_CLAIM = "cl:guidance:go"
PYTHON_CLAIM = "cl:guidance:python"


class _Connection:
    def __init__(self) -> None:
        self.closed = False

    def close(self) -> None:
        self.closed = True


class _Repository(MemoryRepository):
    def __init__(self) -> None:
        super().__init__()
        self.connection = _Connection()

    def close(self) -> None:
        self.connection.close()


def _seed(*, broken_go_snapshot: bool = False) -> _Repository:
    repository = _Repository()
    repository.put(
        {
            "record_type": "knowledge_entity",
            "id": ENTITY_ID,
            "canonical_name": "Cache policy guidance",
            "aliases": [],
            "kinds": ["guidance"],
            "abstraction_level": "pattern",
            "identity_state": "CANONICAL",
            "created_by": {"actor_type": "human", "actor_id": "fixture"},
            "policy_version": "1.0.0",
        }
    )
    for language, claim_id in (("Go", GO_CLAIM), ("Python", PYTHON_CLAIM)):
        source_id = f"src:guidance:{language.lower()}"
        snapshot_id = f"ss:guidance:{language.lower()}:v1"
        evidence_id = f"ev:guidance:{language.lower()}:v1"
        repository.put(
            {
                "record_type": "source",
                "id": source_id,
                "kind": "repository",
                "origin": {
                    "provider": "github",
                    "repository": f"example/{language.lower()}-guidance",
                    "url": f"https://github.com/example/{language.lower()}-guidance",
                },
                "license": {"state": "KNOWN", "declared_expression": "MIT"},
                "acquisition": {"level": "selected-files"},
            }
        )
        if not (broken_go_snapshot and language == "Go"):
            repository.put(
                {
                    "record_type": "source_snapshot",
                    "id": snapshot_id,
                    "source_id": source_id,
                    "revision": f"{language.lower()}-revision-v1",
                    "captured_at": "2026-09-10T00:00:00Z",
                    "metadata": {},
                }
            )
        repository.put(
            {
                "record_type": "evidence",
                "id": evidence_id,
                "source_id": source_id,
                "source_snapshot_id": snapshot_id,
                "locator": {"kind": "line", "path": "README.md", "line_start": 1, "line_end": 1},
                "roles": ["SUPPORTING"],
                "observed_at": "2026-09-10T00:00:00Z",
            }
        )
        repository.put(
            {
                "record_type": "claim",
                "id": claim_id,
                "entity_id": ENTITY_ID,
                "claim_type": "JUDGMENT",
                "statement": f"Use the {language} cache policy.",
                "maturity": "VALIDATED",
                "scope": {},
                "applicability": {
                    "language": language,
                    "minimum_version": 1,
                    "race_detector": True,
                },
                "evidence_ids": [evidence_id],
                "created_by": {"actor_type": "human", "actor_id": "fixture"},
                "policy_version": "1.0.0",
                "last_verified": "2026-09-10T00:00:00Z",
            }
        )
    return repository


def test_guidance_cli_preserves_json_context_types_and_exact_provenance(monkeypatch, capsys):
    repository = _seed()
    monkeypatch.setattr(guidance_cli, "_open_repository", lambda dsn: repository)
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "kneekura-guidance",
            ENTITY_ID,
            "--context-json",
            '{"language":"Go","minimum_version":1,"race_detector":true}',
            "--dsn",
            "postgresql://unused",
        ],
    )

    assert guidance_cli.main() == 0
    result = json.loads(capsys.readouterr().out)
    assert result["resolution"] == "ONE_MATCH"
    assert result["context"] == {"language": "Go", "minimum_version": 1, "race_detector": True}
    assert result["candidate_claim_ids"] == [GO_CLAIM]
    assert result["explanation_count"] == 1
    chain = result["claim_explanations"][0]["evidence_chains"][0]
    assert chain["source_snapshot"]["revision"] == "go-revision-v1"
    assert chain["source"]["id"] == "src:guidance:go"
    assert repository.connection.closed is True


def test_guidance_cli_does_not_coerce_bool_to_int(monkeypatch, capsys):
    repository = _seed()
    monkeypatch.setattr(guidance_cli, "_open_repository", lambda dsn: repository)
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "kneekura-guidance",
            ENTITY_ID,
            "--context-json",
            '{"language":"Go","minimum_version":true,"race_detector":true}',
            "--dsn",
            "postgresql://unused",
        ],
    )

    assert guidance_cli.main() == 0
    result = json.loads(capsys.readouterr().out)
    assert result["resolution"] == "NO_MATCH"
    assert result["candidate_count"] == 0
    assert result["claim_explanations"] == []
    assert repository.connection.closed is True


def test_guidance_cli_preserves_ambiguity_without_context(monkeypatch, capsys):
    repository = _seed()
    monkeypatch.setattr(guidance_cli, "_open_repository", lambda dsn: repository)
    monkeypatch.setattr(
        sys,
        "argv",
        ["kneekura-guidance", ENTITY_ID, "--dsn", "postgresql://unused"],
    )

    assert guidance_cli.main() == 0
    result = json.loads(capsys.readouterr().out)
    assert result["resolution"] == "CONTEXT_REQUIRED"
    assert result["candidate_claim_ids"] == [GO_CLAIM, PYTHON_CLAIM]
    assert result["explanation_count"] == 2
    assert repository.connection.closed is True


def test_guidance_cli_rejects_invalid_or_non_object_context_before_database_open(monkeypatch, capsys):
    opened = False

    def _unexpected_open(dsn: str):
        nonlocal opened
        opened = True
        raise AssertionError("database must not open for invalid context")

    monkeypatch.setattr(guidance_cli, "_open_repository", _unexpected_open)

    for invalid in ("{bad-json", '["Go"]'):
        monkeypatch.setattr(
            sys,
            "argv",
            [
                "kneekura-guidance",
                ENTITY_ID,
                "--context-json",
                invalid,
                "--dsn",
                "postgresql://unused",
            ],
        )
        assert guidance_cli.main() == 1
        assert "INVALID CONTEXT:" in capsys.readouterr().out

    assert opened is False


def test_guidance_cli_fails_closed_on_broken_provenance(monkeypatch, capsys):
    repository = _seed(broken_go_snapshot=True)
    monkeypatch.setattr(guidance_cli, "_open_repository", lambda dsn: repository)
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "kneekura-guidance",
            ENTITY_ID,
            "--context-json",
            '{"language":"Go"}',
            "--dsn",
            "postgresql://unused",
        ],
    )

    assert guidance_cli.main() == 1
    output = capsys.readouterr().out
    assert output.startswith("GUIDANCE ERROR:")
    assert "missing source_snapshot" in output
    assert '"resolution"' not in output
    assert repository.connection.closed is True


def test_guidance_cli_requires_database_dsn(monkeypatch, capsys):
    monkeypatch.delenv("KTHUB_DATABASE_URL", raising=False)
    monkeypatch.setattr(sys, "argv", ["kneekura-guidance", ENTITY_ID])

    assert guidance_cli.main() == 1
    assert "database DSN required" in capsys.readouterr().out
