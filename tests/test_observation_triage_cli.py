from __future__ import annotations

import json
import os
from pathlib import Path
import sys

import psycopg
import pytest

import kneekura_tech_hub.observation_triage_cli as triage_cli
from kneekura_tech_hub.database import apply_migrations
from kneekura_tech_hub.observation_triage_postgres import ObservationTriagePostgresRepository
from kneekura_tech_hub.service import CurationEngine


DSN = os.getenv("KTHUB_TEST_DATABASE_URL")
HUMAN = {"actor_type": "human", "actor_id": "cli-reviewer"}
AI = {"actor_type": "ai", "actor_id": "cli-extractor", "version": "v1"}
SOURCE_ID = "src:triage:cli"
SNAPSHOT_ID = "ss:triage:cli"
EVIDENCE_ID = "ev:triage:cli"
OBSERVATION_ID = "obs:triage:cli"
ENTITY_ID = "ke:triage:cli"


def _truncate(connection) -> None:
    connection.execute(
        """
        TRUNCATE TABLE
            observation_triage_decision,
            source_acquisition_commit,
            source_acquisition_execution,
            source_acquisition_authorization,
            source_selection_decision,
            review_decision,
            staged_observation_evidence,
            claim_evidence, claim, evidence_relation, evidence,
            source_snapshot, staged_observation, curation_event,
            entity_relation, entity_kind, entity_alias, knowledge_entity, source
        RESTART IDENTITY CASCADE
        """
    )


def _setup() -> None:
    assert DSN is not None
    connection = psycopg.connect(DSN, autocommit=True)
    try:
        apply_migrations(connection)
        _truncate(connection)
        repository = ObservationTriagePostgresRepository(connection)
        engine = CurationEngine(repository)
        engine.register_source(
            {
                "record_type": "source",
                "id": SOURCE_ID,
                "kind": "repository",
                "origin": {"provider": "fixture", "repository": "example/triage-cli"},
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
                "metadata": {},
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
                    "line_end": 1,
                    "content_hash": "sha256:" + "a" * 64,
                },
                "roles": ["SUPPORTS"],
            },
            actor=HUMAN,
        )
        engine.create_entity(
            {
                "record_type": "knowledge_entity",
                "id": ENTITY_ID,
                "canonical_name": "CLI triage technique",
                "aliases": [],
                "kinds": ["technique"],
                "abstraction_level": "L1",
                "identity_state": "CANONICAL",
                "relations": [],
            },
            actor=HUMAN,
        )
        engine.stage_observation(
            {
                "record_type": "staged_observation",
                "id": OBSERVATION_ID,
                "source_id": SOURCE_ID,
                "evidence_candidate_ids": [EVIDENCE_ID],
                "summary": "CLI candidate from exact Evidence.",
                "candidate_names": ["CLI triage technique"],
                "status": "NEW",
                "created_by": AI,
            },
            actor=AI,
        )
    finally:
        connection.close()


def test_cli_requires_database_url(monkeypatch, capsys) -> None:
    monkeypatch.delenv("KTHUB_DATABASE_URL", raising=False)
    monkeypatch.setattr(sys, "argv", ["kneekura-observation-triage", "queue"])
    assert triage_cli.main() == 1
    assert "KTHUB_DATABASE_URL is required" in capsys.readouterr().out


@pytest.mark.skipif(not DSN, reason="KTHUB_TEST_DATABASE_URL is not set")
def test_cli_queue_then_governed_candidate_promotion(monkeypatch, tmp_path: Path, capsys) -> None:
    _setup()
    assert DSN is not None
    monkeypatch.setenv("KTHUB_DATABASE_URL", DSN)

    monkeypatch.setattr(sys, "argv", ["kneekura-observation-triage", "queue"])
    assert triage_cli.main() == 0
    queue_output = capsys.readouterr().out
    assert OBSERVATION_ID in queue_output
    assert '"status": "NEW"' in queue_output

    monkeypatch.setattr(
        sys,
        "argv",
        [
            "kneekura-observation-triage",
            "transition",
            OBSERVATION_ID,
            "MARK_TRIAGED",
            "--reason",
            "Mechanical triage found exact Evidence and a bounded candidate.",
            "--actor-type",
            "tool",
            "--actor-id",
            "cli-triage-tool",
            "--actor-version",
            "v1",
            "--decision-id",
            "otd:triage:cli",
        ],
    )
    assert triage_cli.main() == 0
    triage_output = capsys.readouterr().out
    assert '"status": "TRIAGED"' in triage_output

    claim_path = tmp_path / "claim-candidate.json"
    claim_path.write_text(
        json.dumps(
            {
                "id": "cl:triage:cli",
                "entity_id": ENTITY_ID,
                "claim_type": "DIRECT_OBSERVATION",
                "statement": "The pinned source contains the reviewed CLI triage technique.",
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "kneekura-observation-triage",
            "transition",
            OBSERVATION_ID,
            "PROMOTE_TO_CLAIM_CANDIDATE",
            "--reason",
            "Human accepts a candidate claim, not validated knowledge.",
            "--actor-type",
            "human",
            "--actor-id",
            "cli-reviewer",
            "--claim-candidate",
            str(claim_path),
            "--decision-id",
            "otd:promote:cli",
        ],
    )
    assert triage_cli.main() == 0
    promote_output = capsys.readouterr().out
    assert '"status": "PROMOTED"' in promote_output
    assert '"maturity": "CANDIDATE"' in promote_output
    assert EVIDENCE_ID in promote_output

    connection = psycopg.connect(DSN, autocommit=True)
    try:
        repository = ObservationTriagePostgresRepository(connection)
        assert repository.get(OBSERVATION_ID)["status"] == "PROMOTED"
        claim = repository.get("cl:triage:cli")
        assert claim is not None
        assert claim["maturity"] == "CANDIDATE"
        assert claim["evidence_ids"] == [EVIDENCE_ID]
        assert [item["id"] for item in repository.list("observation_triage_decision")] == [
            "otd:triage:cli",
            "otd:promote:cli",
        ]
    finally:
        connection.close()
