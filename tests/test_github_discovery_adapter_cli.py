from __future__ import annotations

import json
import sys
from pathlib import Path

from kneekura_tech_hub import github_cli


ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "tests" / "fixtures" / "github_repository_search_v1.json"


def test_offline_cli_writes_controlled_discovery_batch(monkeypatch, tmp_path, capsys):
    output = tmp_path / "batch.json"
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "kneekura-github-discover",
            "--query",
            "incremental analysis",
            "--input-json",
            str(FIXTURE),
            "--output",
            str(output),
            "--actor-type",
            "tool",
            "--actor-id",
            "fixture-adapter",
            "--actor-version",
            "1.0",
            "--discovered-at",
            "2026-09-09T06:00:00+09:00",
        ],
    )

    assert github_cli.main() == 0
    batch = json.loads(output.read_text(encoding="utf-8"))

    assert len(batch["records"]) == 2
    assert all(item["record_type"] == "source" for item in batch["records"])
    assert all(item["acquisition"]["level"] == "metadata-only" for item in batch["records"])
    assert all(item["license"]["state"] == "REVIEW_REQUIRED" for item in batch["records"])
    assert "WROTE" in capsys.readouterr().out


def test_offline_cli_rejects_invalid_input_without_creating_output(monkeypatch, tmp_path, capsys):
    payload = tmp_path / "bad.json"
    payload.write_text('{"items": []}', encoding="utf-8")
    output = tmp_path / "batch.json"
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "kneekura-github-discover",
            "--query",
            "incremental analysis",
            "--input-json",
            str(payload),
            "--output",
            str(output),
        ],
    )

    assert github_cli.main() == 1
    assert not output.exists()
    assert "REJECTED GITHUB DISCOVERY" in capsys.readouterr().out
