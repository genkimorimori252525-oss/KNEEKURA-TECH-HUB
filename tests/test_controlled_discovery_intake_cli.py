from __future__ import annotations

import json
import sys
from contextlib import nullcontext
from pathlib import Path

from kneekura_tech_hub import cli
from kneekura_tech_hub.repository import MemoryRepository


ROOT = Path(__file__).resolve().parents[1]
PILOT = ROOT / "pilots" / "controlled-discovery-intake-v1.json"


class FakeConnection:
    def transaction(self):
        return nullcontext()


class ClosableMemoryRepository(MemoryRepository):
    def __init__(self) -> None:
        super().__init__()
        self.connection = FakeConnection()

    def close(self) -> None:
        pass


def test_discovery_check_cli_is_read_only(monkeypatch, capsys):
    monkeypatch.setattr(
        sys,
        "argv",
        ["kneekura-hub", "discovery-check", str(PILOT)],
    )

    assert cli.main() == 0
    output = capsys.readouterr().out
    assert "DISCOVERY VALID discovery:pilot:incremental-techniques:v1 records=8" in output


def test_discovery_ingest_cli_writes_only_staging_surface(monkeypatch, capsys):
    repository = ClosableMemoryRepository()
    monkeypatch.setattr(cli, "_open_repository", lambda dsn: repository)
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "kneekura-hub",
            "discovery-ingest",
            str(PILOT),
            "--actor-type",
            "ai",
            "--actor-id",
            "jolly",
            "--actor-version",
            "gpt-5.6-sol",
            "--dsn",
            "ignored",
        ],
    )

    assert cli.main() == 0
    receipt = json.loads(capsys.readouterr().out)
    assert receipt["canonical_knowledge_writes"] == 0
    assert receipt["counts"] == {
        "evidence": 2,
        "source": 2,
        "source_snapshot": 2,
        "staged_observation": 2,
    }
    assert repository.list("knowledge_entity") == []
    assert repository.list("claim") == []
    assert repository.list("review_decision") == []


def test_discovery_ingest_cli_rejects_actor_spoof_before_writes(monkeypatch, capsys):
    repository = ClosableMemoryRepository()
    monkeypatch.setattr(cli, "_open_repository", lambda dsn: repository)
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "kneekura-hub",
            "discovery-ingest",
            str(PILOT),
            "--actor-type",
            "tool",
            "--actor-id",
            "different-crawler",
            "--dsn",
            "ignored",
        ],
    )

    assert cli.main() == 1
    assert "acting identity" in capsys.readouterr().out
    assert repository.list() == []
