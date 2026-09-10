from __future__ import annotations

import sys

from kneekura_tech_hub import guidance_cli


ENTITY_ID = "ke:guidance:cache-policy"


def _must_not_open_database(dsn: str):
    raise AssertionError("database must not open for semantically invalid context JSON")


def test_guidance_cli_rejects_duplicate_context_keys_before_database_open(monkeypatch, capsys):
    monkeypatch.setattr(guidance_cli, "_open_repository", _must_not_open_database)
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "kneekura-guidance",
            ENTITY_ID,
            "--context-json",
            '{"language":"Go","language":"Python"}',
            "--dsn",
            "postgresql://unused",
        ],
    )

    assert guidance_cli.main() == 1
    assert "duplicate context key" in capsys.readouterr().out


def test_guidance_cli_rejects_non_finite_json_numbers_before_database_open(monkeypatch, capsys):
    monkeypatch.setattr(guidance_cli, "_open_repository", _must_not_open_database)

    for raw in ('{"threshold":NaN}', '{"threshold":Infinity}', '{"threshold":-Infinity}'):
        monkeypatch.setattr(
            sys,
            "argv",
            [
                "kneekura-guidance",
                ENTITY_ID,
                "--context-json",
                raw,
                "--dsn",
                "postgresql://unused",
            ],
        )
        assert guidance_cli.main() == 1
        assert "non-finite JSON number" in capsys.readouterr().out
