from __future__ import annotations

from hashlib import sha256
import json
import os
from pathlib import Path

import psycopg
import pytest

from kneekura_tech_hub.claim_support import claim_support_history
from kneekura_tech_hub.claim_validation import claim_validation_history
from kneekura_tech_hub.comparison import compare_claim
from kneekura_tech_hub.database import apply_migrations
from kneekura_tech_hub.explanation import explain_claim
from kneekura_tech_hub.postgres_repository import PostgresRepository
from kneekura_tech_hub.service import CurationEngine, CurationError


DSN = os.getenv("KTHUB_TEST_DATABASE_URL")
pytestmark = pytest.mark.skipif(not DSN, reason="KTHUB_TEST_DATABASE_URL is not set")

FIXTURE_DIR = Path(__file__).parent / "fixtures" / "live-cross-source-conflict" / "indentation-policy"
HUMAN = {"actor_type": "human", "actor_id": "live-cross-source-reviewer"}
AI = {"actor_type": "ai", "actor_id": "live-cross-source-agent", "version": "v1"}
TOOL = {"actor_type": "tool", "actor_id": "live-cross-source-capture", "version": "v1"}

GO_SOURCE = "src:github:golang:go"
PY_SOURCE = "src:github:python:peps"
GO_SNAPSHOT = "ss:live-conflict:golang-go:5d12b248"
PY_SNAPSHOT = "ss:live-conflict:python-peps:3b6032df"
GO_EVIDENCE = "ev:live-conflict:gofmt:tabs"
PY_EVIDENCE = "ev:live-conflict:pep8:spaces"
ENTITY_ID = "ke:live-conflict:indentation-character-policy"
GO_CLAIM = "cl:live-conflict:indentation:go-tabs"
PY_CLAIM = "cl:live-conflict:indentation:python-spaces"


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


def _load_capture() -> dict:
    capture = json.loads((FIXTURE_DIR / "capture.json").read_text(encoding="utf-8"))
    assert capture["capture_version"] == "1.0"
    assert capture["theme"] == "source-code indentation character policy"
    assert len(capture["sources"]) == 2
    for source in capture["sources"]:
        excerpt = (FIXTURE_DIR / source["excerpt_file"]).read_bytes()
        assert sha256(excerpt).hexdigest() == source["excerpt_sha256"]
    return capture


def _seed_source_chain(
    engine: CurationEngine,
    source: dict,
    *,
    snapshot_id: str,
    evidence_id: str,
    section: str,
) -> None:
    handling_policy = "REFERENCE_ONLY" if source["license_state"] == "KNOWN" else "DISCOVERY_METADATA_ONLY"
    engine.register_source(
        {
            "record_type": "source",
            "id": source["id"],
            "kind": "repository",
            "origin": {
                "provider": "github",
                "repository": source["repository"],
                "canonical_url": f"https://github.com/{source['repository']}",
                "default_branch": source["default_branch"],
                "stargazers_count": source["stargazers_count"],
            },
            "acquisition": {"level": "metadata-only"},
            "license": {
                "state": source["license_state"],
                "declared_expression": source["declared_expression"],
                "handling_policy": handling_policy,
            },
        },
        actor=TOOL,
    )
    engine.register_source_snapshot(
        {
            "record_type": "source_snapshot",
            "id": snapshot_id,
            "source_id": source["id"],
            "revision": source["revision"],
            "tree_hash": source["tree_sha"],
            "captured_at": "2026-09-10T05:00:00+09:00",
            "metadata": {
                "fixture": "live-cross-source-conflict-trial-v1",
                "path": source["path"],
                "git_blob_sha": source["git_blob_sha"],
                "excerpt_sha256": source["excerpt_sha256"],
            },
        },
        actor=TOOL,
    )
    engine.register_evidence(
        {
            "record_type": "evidence",
            "id": evidence_id,
            "source_id": source["id"],
            "source_snapshot_id": snapshot_id,
            "locator": {
                "type": "document_section",
                "path": source["path"],
                "section": section,
                "content_hash": f"git-blob:{source['git_blob_sha']}",
                "excerpt_sha256": source["excerpt_sha256"],
                "url": (
                    f"https://github.com/{source['repository']}/blob/"
                    f"{source['revision']}/{source['path']}"
                ),
            },
            "roles": ["SUPPORTS"],
        },
        actor=TOOL,
    )


def _create_claim(
    engine: CurationEngine,
    *,
    claim_id: str,
    statement: str,
    evidence_id: str,
    ecosystem: str,
    authority: str,
) -> None:
    engine.create_claim(
        {
            "record_type": "claim",
            "id": claim_id,
            "entity_id": ENTITY_ID,
            "claim_type": "AUTHOR_CLAIM",
            "statement": statement,
            "maturity": "CANDIDATE",
            "evidence_ids": [evidence_id],
            "scope": {
                "decision": "indentation-character",
                "comparison": "language-style-policy",
                "question": "tabs-or-spaces",
            },
            "applicability": {"ecosystem": ecosystem, "authority": authority},
            "created_by": AI,
            "policy_version": "1.0.0",
        },
        actor=AI,
        reason="AI proposes a commit-pinned author Claim; human review controls maturity.",
    )


def test_live_go_and_python_indentation_choices_remain_valid_without_automatic_winner() -> None:
    assert DSN is not None
    capture = _load_capture()
    by_id = {item["id"]: item for item in capture["sources"]}
    go = by_id[GO_SOURCE]
    python = by_id[PY_SOURCE]

    # These values were observed from live GitHub. Popularity is deliberately metadata only.
    assert go["revision"] == "5d12b248d5520ff5adafeb9be9acc2148399ca49"
    assert go["tree_sha"] == "73a4ee55f515fa641e4edc21ab89e6d4ead693a4"
    assert go["git_blob_sha"] == "8ac9c6a931711df3c65b58611d77fc000578175d"
    assert python["revision"] == "3b6032df5a42825474e00b75a4b1a8e9c7af459b"
    assert python["tree_sha"] == "ece03897c8329d793b51ec7b07bb583ae537533f"
    assert python["git_blob_sha"] == "d14c9e97b120daecadcd4afe742af69ddc07a34c"
    assert go["stargazers_count"] == 137991
    assert python["stargazers_count"] == 5003
    assert go["stargazers_count"] > python["stargazers_count"] * 20
    assert go["license_state"] == "KNOWN"
    assert python["license_state"] == "REVIEW_REQUIRED"

    connection = psycopg.connect(DSN, autocommit=True)
    try:
        apply_migrations(connection)
        _truncate(connection)
        repository = PostgresRepository(connection)
        engine = CurationEngine(repository)

        _seed_source_chain(
            engine,
            go,
            snapshot_id=GO_SNAPSHOT,
            evidence_id=GO_EVIDENCE,
            section="gofmt package documentation",
        )
        _seed_source_chain(
            engine,
            python,
            snapshot_id=PY_SNAPSHOT,
            evidence_id=PY_EVIDENCE,
            section="Tabs or Spaces?",
        )

        engine.create_entity(
            {
                "record_type": "knowledge_entity",
                "id": ENTITY_ID,
                "canonical_name": "Source-code indentation character policy",
                "aliases": ["Tabs versus spaces policy"],
                "kinds": ["design-decision", "style-policy"],
                "abstraction_level": "L1",
                "identity_state": "CANONICAL",
                "relations": [],
            },
            actor=HUMAN,
            reason="Human establishes one comparison theme without declaring either ecosystem globally correct.",
        )

        _create_claim(
            engine,
            claim_id=GO_CLAIM,
            statement="Go's canonical gofmt formatter uses tabs for indentation and blanks for alignment.",
            evidence_id=GO_EVIDENCE,
            ecosystem="Go",
            authority="gofmt",
        )
        engine.transition_claim(
            GO_CLAIM,
            "SUPPORTED",
            actor=HUMAN,
            reason="Human reviews the pinned gofmt documentation.",
            support_review={"decision_id": "csd:live-conflict:go"},
        )
        go_validated = engine.transition_claim(
            GO_CLAIM,
            "VALIDATED",
            actor=HUMAN,
            reason="Human validates only the narrow Go-specific author Claim.",
            validation_review={
                "validation_basis": "EVIDENCE_REVIEW",
                "validation_note": "The pinned gofmt documentation explicitly states the indentation behavior.",
                "independence_assessment": "NOT_ASSESSED",
                "decision_id": "cvd:live-conflict:go",
            },
        )
        assert go_validated["maturity"] == "VALIDATED"

        _create_claim(
            engine,
            claim_id=PY_CLAIM,
            statement=(
                "Python PEP 8 prefers spaces for indentation and reserves tabs for consistency with "
                "already tab-indented code."
            ),
            evidence_id=PY_EVIDENCE,
            ecosystem="Python",
            authority="PEP 8",
        )

        comparison = compare_claim(repository, GO_CLAIM)
        assert comparison["active_claim_ids"] == sorted([GO_CLAIM, PY_CLAIM])
        assert comparison["active_claim_count"] == 2
        assert comparison["statements_are_identical"] is False
        assert "MULTIPLE_ACTIVE_CLAIMS" in comparison["flags"]
        assert "STATEMENTS_DIFFER" in comparison["flags"]
        assert "HAS_CANDIDATE_CLAIM" in comparison["flags"]
        assert comparison["needs_review"] is True
        assert all("CONTRADICTION" not in flag for flag in comparison["flags"])
        assert "winner" not in comparison
        assert "preferred_claim_id" not in comparison
        assert repository.get(GO_CLAIM)["maturity"] == "VALIDATED"
        assert repository.get(PY_CLAIM)["maturity"] == "CANDIDATE"
        assert repository.get(GO_SOURCE)["origin"]["stargazers_count"] == 137991
        assert repository.get(PY_SOURCE)["origin"]["stargazers_count"] == 5003

        with pytest.raises(CurationError, match="competing active Claims require an explicit competition_note"):
            engine.transition_claim(
                PY_CLAIM,
                "SUPPORTED",
                actor=HUMAN,
                reason="The Go design choice must be acknowledged before reviewing the Python alternative.",
            )

        python_supported = engine.transition_claim(
            PY_CLAIM,
            "SUPPORTED",
            actor=HUMAN,
            reason="Human records the Python-specific design choice without demoting the Go-specific choice.",
            support_review={
                "competition_note": (
                    "gofmt uses tabs while PEP 8 prefers spaces; these are ecosystem-specific design "
                    "choices on the same comparison theme, not a global truth contest."
                ),
                "decision_id": "csd:live-conflict:python",
            },
        )
        assert python_supported["maturity"] == "SUPPORTED"
        support = claim_support_history(repository, claim_id=PY_CLAIM)[0]
        assert support["competing_active_claim_ids"] == [GO_CLAIM]
        assert support["distinct_source_ids"] == [PY_SOURCE]
        assert support["distinct_snapshot_ids"] == [PY_SNAPSHOT]

        with pytest.raises(CurationError, match="competing active Claims require an explicit competition_note"):
            engine.transition_claim(
                PY_CLAIM,
                "VALIDATED",
                actor=HUMAN,
                reason="Validation must still acknowledge the already Validated Go alternative.",
                validation_review={
                    "validation_basis": "EVIDENCE_REVIEW",
                    "validation_note": "The PEP 8 excerpt was reviewed.",
                    "independence_assessment": "NOT_ASSESSED",
                },
            )

        python_validated = engine.transition_claim(
            PY_CLAIM,
            "VALIDATED",
            actor=HUMAN,
            reason="Human validates the narrow Python-specific author Claim without selecting a global winner.",
            validation_review={
                "validation_basis": "EVIDENCE_REVIEW",
                "validation_note": "The pinned PEP 8 section explicitly prefers spaces for Python indentation.",
                "competition_note": (
                    "The Go Claim remains Validated because its applicability is Go/gofmt; the Python Claim is "
                    "validated for Python/PEP 8 rather than as a universal replacement."
                ),
                "independence_assessment": "NOT_ASSESSED",
                "decision_id": "cvd:live-conflict:python",
            },
        )
        assert python_validated["maturity"] == "VALIDATED"
        validation = claim_validation_history(repository, claim_id=PY_CLAIM)[0]
        assert validation["competing_active_claim_ids"] == [GO_CLAIM]
        assert validation["distinct_source_ids"] == [PY_SOURCE]
        assert validation["distinct_snapshot_ids"] == [PY_SNAPSHOT]

        final_group = compare_claim(repository, GO_CLAIM)
        assert final_group["active_claim_ids"] == sorted([GO_CLAIM, PY_CLAIM])
        assert {item["claim"]["maturity"] for item in final_group["claims"]} == {"VALIDATED"}
        assert "MULTIPLE_ACTIVE_CLAIMS" in final_group["flags"]
        assert "STATEMENTS_DIFFER" in final_group["flags"]
        assert "HAS_CANDIDATE_CLAIM" not in final_group["flags"]
        assert "HAS_CHALLENGED_CLAIM" not in final_group["flags"]
        assert all("CONTRADICTION" not in flag for flag in final_group["flags"])
        assert final_group["needs_review"] is True
        assert "winner" not in final_group
        assert "preferred_claim_id" not in final_group

        # Neither valid ecosystem-specific choice is challenged or terminally dispositioned.
        challenge_events = [
            event for event in repository.list("curation_event") if event["operation"] == "CLAIM_CHALLENGE"
        ]
        assert challenge_events == []
        assert repository.get(GO_CLAIM)["maturity"] == "VALIDATED"
        assert repository.get(PY_CLAIM)["maturity"] == "VALIDATED"

        go_explanation = explain_claim(repository, GO_CLAIM)
        python_explanation = explain_claim(repository, PY_CLAIM)
        assert go_explanation["evidence_chains"][0]["source"]["id"] == GO_SOURCE
        assert go_explanation["evidence_chains"][0]["source_snapshot"]["id"] == GO_SNAPSHOT
        assert go_explanation["evidence_chains"][0]["evidence"]["locator"]["content_hash"] == (
            "git-blob:8ac9c6a931711df3c65b58611d77fc000578175d"
        )
        assert python_explanation["evidence_chains"][0]["source"]["id"] == PY_SOURCE
        assert python_explanation["evidence_chains"][0]["source_snapshot"]["id"] == PY_SNAPSHOT
        assert python_explanation["evidence_chains"][0]["evidence"]["locator"]["content_hash"] == (
            "git-blob:d14c9e97b120daecadcd4afe742af69ddc07a34c"
        )
        assert python_explanation["evidence_chains"][0]["source"]["license"]["state"] == "REVIEW_REQUIRED"
    finally:
        connection.close()
