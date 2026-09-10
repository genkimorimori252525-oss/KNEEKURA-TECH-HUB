from __future__ import annotations

import json
import os
import sys

import psycopg
import pytest

from kneekura_tech_hub import guidance_cli
from kneekura_tech_hub.database import apply_migrations
from kneekura_tech_hub.postgres_repository import PostgresRepository
from kneekura_tech_hub.service import CurationEngine


DSN = os.getenv("KTHUB_TEST_DATABASE_URL")
pytestmark = pytest.mark.skipif(not DSN, reason="KTHUB_TEST_DATABASE_URL is not set")

HUMAN = {"actor_type": "human", "actor_id": "guidance-cli-postgres-reviewer"}
AI = {"actor_type": "ai", "actor_id": "guidance-cli-postgres-agent", "version": "v1"}
TOOL = {"actor_type": "tool", "actor_id": "guidance-cli-postgres-capture", "version": "v1"}
ENTITY_ID = "ke:guidance:cli:postgres:indentation"
SOURCE_ID = "src:github:golang:go:guidance-cli-postgres"
SNAPSHOT_ID = "ss:guidance:cli:postgres:go"
EVIDENCE_ID = "ev:guidance:cli:postgres:go"
CLAIM_ID = "cl:guidance:cli:postgres:go-tabs"
REVISION = "5d12b248d5520ff5adafeb9be9acc2148399ca49"


def _truncate(connection) -> None:
    connection.execute(
        """
        TRUNCATE TABLE
            claim_disposition_decision,
            claim_validation_decision,
            claim_support_decision,
            observation_triage_decision,
            review_decision,
            staged_observation_evidence,
            claim_evidence, claim, evidence_relation, evidence,
            source_snapshot, staged_observation, curation_event,
            entity_relation, entity_kind, entity_alias, knowledge_entity, source
        RESTART IDENTITY CASCADE
        """
    )


def _seed_postgres() -> None:
    assert DSN is not None
    connection = psycopg.connect(DSN, autocommit=True)
    try:
        apply_migrations(connection)
        _truncate(connection)
        repository = PostgresRepository(connection)
        engine = CurationEngine(repository)

        engine.register_source(
            {
                "record_type": "source",
                "id": SOURCE_ID,
                "kind": "repository",
                "origin": {
                    "provider": "github",
                    "repository": "golang/go",
                    "canonical_url": "https://github.com/golang/go",
                },
                "acquisition": {"level": "metadata-only"},
                "license": {
                    "state": "KNOWN",
                    "declared_expression": "BSD-3-Clause",
                    "handling_policy": "REFERENCE_ONLY",
                },
            },
            actor=TOOL,
        )
        engine.register_source_snapshot(
            {
                "record_type": "source_snapshot",
                "id": SNAPSHOT_ID,
                "source_id": SOURCE_ID,
                "revision": REVISION,
                "captured_at": "2026-09-10T11:00:00+09:00",
                "metadata": {"fixture": "context-guidance-query-surface-v1"},
            },
            actor=TOOL,
        )
        engine.register_evidence(
            {
                "record_type": "evidence",
                "id": EVIDENCE_ID,
                "source_id": SOURCE_ID,
                "source_snapshot_id": SNAPSHOT_ID,
                "locator": {
                    "type": "document_section",
                    "path": "src/go/format/format.go",
                    "section": "gofmt package documentation",
                },
                "roles": ["SUPPORTS"],
            },
            actor=TOOL,
        )
        engine.create_entity(
            {
                "record_type": "knowledge_entity",
                "id": ENTITY_ID,
                "canonical_name": "Source-code indentation character policy",
                "aliases": [],
                "kinds": ["design-decision", "style-policy"],
                "abstraction_level": "L1",
                "identity_state": "CANONICAL",
                "relations": [],
            },
            actor=HUMAN,
            reason="Human establishes the narrow guidance subject.",
        )
        engine.create_claim(
            {
                "record_type": "claim",
                "id": CLAIM_ID,
                "entity_id": ENTITY_ID,
                "claim_type": "AUTHOR_CLAIM",
                "statement": "Go's canonical gofmt formatter uses tabs for indentation and blanks for alignment.",
                "maturity": "CANDIDATE",
                "evidence_ids": [EVIDENCE_ID],
                "scope": {"decision": "indentation-character"},
                "applicability": {"ecosystem": "Go", "authority": "gofmt"},
                "created_by": AI,
                "policy_version": "1.0.0",
            },
            actor=AI,
            reason="AI proposes a provenance-backed narrow Claim.",
        )
        engine.transition_claim(
            CLAIM_ID,
            "SUPPORTED",
            actor=HUMAN,
            reason="Human reviewed the pinned evidence.",
            support_review={"decision_id": "csd:guidance:cli:postgres:go"},
        )
        engine.transition_claim(
            CLAIM_ID,
            "VALIDATED",
            actor=HUMAN,
            reason="Human validates only the Go/gofmt applicability.",
            validation_review={
                "validation_basis": "EVIDENCE_REVIEW",
                "validation_note": "Pinned evidence supports the narrow Claim.",
                "independence_assessment": "NOT_ASSESSED",
                "decision_id": "cvd:guidance:cli:postgres:go",
            },
        )
    finally:
        connection.close()


def test_guidance_cli_reads_real_postgres_and_preserves_exact_provenance(monkeypatch, capsys) -> None:
    assert DSN is not None
    _seed_postgres()
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "kneekura-guidance",
            ENTITY_ID,
            "--context-json",
            '{"ecosystem":"Go"}',
            "--dsn",
            DSN,
        ],
    )

    assert guidance_cli.main() == 0
    result = json.loads(capsys.readouterr().out)

    assert result["resolution"] == "ONE_MATCH"
    assert result["candidate_claim_ids"] == [CLAIM_ID]
    assert result["explanation_count"] == 1
    explanation = result["claim_explanations"][0]
    assert explanation["claim"]["id"] == CLAIM_ID
    assert explanation["claim"]["maturity"] == "VALIDATED"
    chain = explanation["evidence_chains"][0]
    assert chain["evidence"]["id"] == EVIDENCE_ID
    assert chain["source_snapshot"]["id"] == SNAPSHOT_ID
    assert chain["source_snapshot"]["revision"] == REVISION
    assert chain["source"]["id"] == SOURCE_ID
    assert "winner" not in result
    assert "preferred_claim_id" not in result
