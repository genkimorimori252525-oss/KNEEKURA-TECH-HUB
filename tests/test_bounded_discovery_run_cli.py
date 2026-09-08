from __future__ import annotations

import json
import sys
from pathlib import Path

from kneekura_tech_hub import discovery_run_cli


ROOT = Path(__file__).resolve().parents[1]
SPEC = ROOT / "tests" / "fixtures" / "bounded_discovery_run_spec_v1.json"
RESPONSES = ROOT / "tests" / "fixtures" / "bounded_discovery_run_responses_v1.json"


def test_offline_bounded_run_cli_writes_one_controlled_discovery_batch(monkeypatch, tmp_path, capsys):
    output = tmp_path / "run.json"
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "kneekura-discovery-run",
            "--spec",
            str(SPEC),
            "--responses",
            str(RESPONSES),
            "--output",
            str(output),
        ],
    )

    assert discovery_run_cli.main() == 0
    batch = json.loads(output.read_text(encoding="utf-8"))

    assert batch["batch_id"].startswith("discovery:github-run:")
    assert [item["id"] for item in batch["records"]] == [
        "src:github:example:alpha",
        "src:github:example:shared",
        "src:github:example:beta",
    ]
    filters = batch["scope"]["filters"]
    assert filters["unique_source_count"] == 3
    assert filters["duplicate_hit_count"] == 1
    assert filters["executed_request_count"] == 3
    assert filters["pages"][1]["empty"] is True
    assert "WROTE" in capsys.readouterr().out


def test_offline_cli_fails_without_required_page_response(monkeypatch, tmp_path, capsys):
    responses = tmp_path / "responses.json"
    responses.write_text('{"pages": []}', encoding="utf-8")
    output = tmp_path / "run.json"
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "kneekura-discovery-run",
            "--spec",
            str(SPEC),
            "--responses",
            str(responses),
            "--output",
            str(output),
        ],
    )

    assert discovery_run_cli.main() == 1
    assert not output.exists()
    assert "REJECTED DISCOVERY RUN" in capsys.readouterr().out
