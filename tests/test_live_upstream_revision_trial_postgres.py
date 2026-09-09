from __future__ import annotations

from hashlib import sha1
import json
import os
from pathlib import Path

import psycopg
import pytest

from kneekura_tech_hub.authorization import (
    AcquisitionAuthorizationEngine,
    authorization_effectiveness,
)
from kneekura_tech_hub.authorization_postgres import AuthorizationPostgresRepository
from kneekura_tech_hub.claim_disposition import dispose_claim
from kneekura_tech_hub.comparison import compare_claim
from kneekura_tech_hub.database import apply_migrations
from kneekura_tech_hub.execution import execute_authorized_acquisition
from kneekura_tech_hub.explanation import explain_claim
from kneekura_tech_hub.observation_triage_postgres import ObservationTriagePostgresRepository
from kneekura_tech_hub.selected_file_extraction import ingest_selected_file_extraction
from kneekura_tech_hub.selection import SourceSelectionEngine
from kneekura_tech_hub.service import CurationEngine
from kneekura_tech_hub.verified_commit import commit_verified_acquisition


DSN = os.getenv("KTHUB_TEST_DATABASE_URL")
pytestmark = pytest.mark.skipif(not DSN, reason="KTHUB_TEST_DATABASE_URL is not set")

FIXTURE_DIR = Path(__file__).parent / "fixtures" / "live-upstream-revision" / "salsa-msrv"
CAPTURE_PATH = FIXTURE_DIR / "capture.json"
BEFORE_FILE = FIXTURE_DIR / "Cargo.before.toml"

SOURCE_ID = "src:github:salsa-rs:salsa"
SELECTION_ID = "sd:live-salsa-msrv"
AUTH_BEFORE = "aa:live-salsa-msrv:before"
AUTH_AFTER = "aa:live-salsa-msrv:after"
ENTITY_ID = "ke:live-salsa-msrv"
CLAIM_BEFORE = "cl:live-salsa-msrv:1.85"
CLAIM_AFTER = "cl:live-salsa-msrv:1.88"

DISCOVERY_TOOL = {"actor_type": "tool", "actor_id": "live-salsa-discovery", "version": "v1"}
FETCH_TOOL = {"actor_type": "tool", "actor_id": "live-salsa-fetch", "version": "v1"}
COMMIT_TOOL = {"actor_type": "tool", "actor_id": "live-salsa-commit", "version": "v1"}
EXTRACTOR_AI = {"actor_type": "ai", "actor_id": "live-salsa-extractor", "version": "v1"}
CHALLENGER_AI = {"actor_type": "ai", "actor_id": "live-salsa-challenger", "version": "v1"}
HUMAN = {"actor_type": "human", "actor_id": "live-salsa-reviewer"}


def _git_blob_sha(content: bytes) -> str:
    header = f"blob {len(content)}\0".encode("ascii")
    return sha1(header + content).hexdigest()  # noqa: S324 - Git object identity


def _truncate(connection) -> None:
    connection.execute(
        """
        TRUNCATE TABLE
            claim_disposition_decision,
            claim_validation_decision,
            claim_support_decision,
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


def _load_live_capture() -> tuple[dict, bytes, bytes]:
    capture = json.loads(CAPTURE_PATH.read_text(encoding="utf-8"))
    before = BEFORE_FILE.read_bytes()
    before_line = capture["before"]["line_text"].encode()
    after_line = capture["after"]["line_text"].encode()

    assert capture["source"]["repository"] == "salsa-rs/salsa"
    assert capture["source"]["path"] == "Cargo.toml"
    assert capture["after"]["parent_revision"] == capture["before"]["revision"]
    assert len(before) == capture["before"]["byte_count"]
    assert _git_blob_sha(before) == capture["before"]["blob_sha"]

    old_lines = before.splitlines()
    line_index = capture["before"]["line"] - 1
    assert old_lines[line_index] == before_line
    assert old_lines.count(before_line) == 1

    after = before.replace(before_line, after_line, 1)
    assert len(after) == capture["after"]["byte_count"]
    assert _git_blob_sha(after) == capture["after"]["blob_sha"]
    assert after.splitlines()[capture["after"]["line"] - 1] == after_line

    differences = [
        (index, old, new)
        for index, (old, new) in enumerate(zip(before.splitlines(), after.splitlines(), strict=True), start=1)
        if old != new
    ]
    assert differences == [(149, before_line, after_line)]
    return capture, before, after


def _execute_and_commit(
    repository,
    *,
    authorization_id: str,
    revision: str,
    expected_blob_sha: str,
    content: bytes,
    suffix: str,
    storage_root: Path,
):
    def fetch_file(source, actual_revision, path):
        assert source["id"] == SOURCE_ID
        assert actual_revision == revision
        assert path == "Cargo.toml"
        return {"content": content, "git_blob_sha": expected_blob_sha}

    execution = execute_authorized_acquisition(
        repository,
        authorization_id,
        storage_root=storage_root,
        fetch_file=fetch_file,
        actor=FETCH_TOOL,
        execution_id=f"ax:live-salsa-msrv:{suffix}",
    )
    assert execution["status"] == "SUCCEEDED"
    assert execution["file_results"][0]["git_blob_sha"] == expected_blob_sha

    commit = commit_verified_acquisition(
        repository,
        execution["id"],
        storage_root=storage_root,
        actor=COMMIT_TOOL,
        commit_id=f"vc:live-salsa-msrv:{suffix}",
    )
    snapshot = repository.get(commit["snapshot_id"])
    assert snapshot is not None
    assert snapshot["source_id"] == SOURCE_ID
    assert snapshot["revision"] == revision
    return snapshot


def _extract(
    engine: CurationEngine,
    *,
    snapshot_id: str,
    line: int,
    version: str,
    storage_root: Path,
) -> str:
    result = ingest_selected_file_extraction(
        engine,
        {
            "proposal_version": "1.0",
            "snapshot_id": snapshot_id,
            "findings": [
                {
                    "summary": f"At the pinned Salsa revision, workspace rust-version is {version}.",
                    "candidate_names": ["Salsa workspace rust-version"],
                    "anchors": [
                        {
                            "path": "Cargo.toml",
                            "line_start": line,
                            "line_end": line,
                        }
                    ],
                }
            ],
        },
        storage_root=storage_root,
        actor=EXTRACTOR_AI,
    )
    assert len(result["evidence_ids"]) == 1
    return result["evidence_ids"][0]


def _create_claim(
    engine: CurationEngine,
    *,
    claim_id: str,
    evidence_id: str,
    version: str,
) -> None:
    engine.create_claim(
        {
            "record_type": "claim",
            "id": claim_id,
            "entity_id": ENTITY_ID,
            "claim_type": "DIRECT_OBSERVATION",
            "statement": f"Salsa's current declared workspace Rust version is {version}.",
            "maturity": "CANDIDATE",
            "evidence_ids": [evidence_id],
            "scope": {
                "source_id": SOURCE_ID,
                "path": "Cargo.toml",
                "key": "workspace.package.rust-version",
                "meaning": "current declared workspace Rust version",
            },
            "applicability": {"context": "Salsa workspace package metadata"},
            "created_by": EXTRACTOR_AI,
            "policy_version": "1.0.0",
        },
        actor=EXTRACTOR_AI,
        reason=f"AI proposes the pinned direct observation for Salsa rust-version {version}.",
    )


def test_live_salsa_msrv_revision_refresh_preserves_both_real_blobs(tmp_path: Path) -> None:
    assert DSN is not None
    capture, before_content, after_content = _load_live_capture()
    before = capture["before"]
    after = capture["after"]

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
                "origin": {
                    "provider": "github",
                    "repository": "salsa-rs/salsa",
                    "url": "https://github.com/salsa-rs/salsa",
                    "default_branch": "master",
                },
                "acquisition": {"level": "metadata-only"},
                "license": {
                    "state": "KNOWN",
                    "declared_expression": capture["source"]["license_expression"],
                    "handling_policy": "REFERENCE_ONLY",
                },
            },
            actor=DISCOVERY_TOOL,
        )
        selection = SourceSelectionEngine(repository).create_from_fields(
            source_id=SOURCE_ID,
            decision="SELECT_FOR_REVIEW",
            rationale="Human selects the real Salsa repository for bounded MSRV revision verification.",
            actor=HUMAN,
            decision_id=SELECTION_ID,
        )
        engine.create_entity(
            {
                "record_type": "knowledge_entity",
                "id": ENTITY_ID,
                "canonical_name": "Salsa workspace minimum Rust version",
                "aliases": ["Salsa MSRV"],
                "kinds": ["configuration", "compatibility-requirement"],
                "abstraction_level": "L1",
                "identity_state": "CANONICAL",
                "relations": [],
            },
            actor=HUMAN,
            reason="Human creates one stable subject for the real upstream compatibility declaration.",
        )

        authorization_before = AcquisitionAuthorizationEngine(repository).authorize_from_fields(
            source_id=SOURCE_ID,
            selection_decision_id=selection["id"],
            revision=before["revision"],
            allowed_paths=["Cargo.toml"],
            rationale="Human authorizes only Salsa Cargo.toml at the exact predecessor revision.",
            actor=HUMAN,
            authorization_id=AUTH_BEFORE,
        )
        snapshot_before = _execute_and_commit(
            repository,
            authorization_id=authorization_before["id"],
            revision=before["revision"],
            expected_blob_sha=before["blob_sha"],
            content=before_content,
            suffix="before",
            storage_root=tmp_path,
        )
        assert authorization_effectiveness(repository, AUTH_BEFORE)["effective"] is False

        evidence_before = _extract(
            engine,
            snapshot_id=snapshot_before["id"],
            line=before["line"],
            version="1.85",
            storage_root=tmp_path,
        )
        _create_claim(
            engine,
            claim_id=CLAIM_BEFORE,
            evidence_id=evidence_before,
            version="1.85",
        )
        engine.transition_claim(
            CLAIM_BEFORE,
            "SUPPORTED",
            actor=HUMAN,
            reason="Human reviews the real pinned Salsa 1.85 declaration.",
            support_review={"decision_id": "csd:live-salsa-msrv:before"},
        )
        validated_before = engine.transition_claim(
            CLAIM_BEFORE,
            "VALIDATED",
            actor=HUMAN,
            reason="Human validates the real Salsa predecessor MSRV observation.",
            validation_review={
                "validation_basis": "EVIDENCE_REVIEW",
                "validation_note": (
                    f"Captured Git blob {before['blob_sha']} line {before['line']} declares rust-version 1.85."
                ),
                "decision_id": "cvd:live-salsa-msrv:before",
            },
        )
        old_last_verified = validated_before["last_verified"]

        authorization_repository = AuthorizationPostgresRepository(connection)
        authorization_after = AcquisitionAuthorizationEngine(
            authorization_repository
        ).authorize_from_fields(
            source_id=SOURCE_ID,
            selection_decision_id=selection["id"],
            revision=after["revision"],
            allowed_paths=["Cargo.toml"],
            rationale=(
                "Human authorizes the exact Salsa commit that bumps the workspace MSRV from 1.85 to 1.88."
            ),
            actor=HUMAN,
            authorization_id=AUTH_AFTER,
            supersedes_authorization_id=AUTH_BEFORE,
        )
        assert authorization_effectiveness(
            authorization_repository, AUTH_AFTER
        )["effective"] is True

        snapshot_after = _execute_and_commit(
            repository,
            authorization_id=authorization_after["id"],
            revision=after["revision"],
            expected_blob_sha=after["blob_sha"],
            content=after_content,
            suffix="after",
            storage_root=tmp_path,
        )
        assert snapshot_after["id"] != snapshot_before["id"]
        assert repository.get(snapshot_before["id"]) == snapshot_before
        assert authorization_effectiveness(repository, AUTH_AFTER)["effective"] is False

        evidence_after = _extract(
            engine,
            snapshot_id=snapshot_after["id"],
            line=after["line"],
            version="1.88",
            storage_root=tmp_path,
        )
        _create_claim(
            engine,
            claim_id=CLAIM_AFTER,
            evidence_id=evidence_after,
            version="1.88",
        )

        comparison = compare_claim(repository, CLAIM_AFTER)
        assert comparison["active_claim_ids"] == sorted([CLAIM_BEFORE, CLAIM_AFTER])
        assert "MULTIPLE_ACTIVE_CLAIMS" in comparison["flags"]
        assert "STATEMENTS_DIFFER" in comparison["flags"]
        assert "winner" not in comparison
        assert "preferred_claim_id" not in comparison

        engine.transition_claim(
            CLAIM_AFTER,
            "SUPPORTED",
            actor=HUMAN,
            reason="Human reviews the real Salsa 1.88 declaration while the 1.85 Claim remains active.",
            support_review={
                "competition_note": (
                    f"{CLAIM_BEFORE} is still VALIDATED from the parent commit {before['revision']}."
                ),
                "decision_id": "csd:live-salsa-msrv:after",
            },
        )
        engine.transition_claim(
            CLAIM_AFTER,
            "VALIDATED",
            actor=HUMAN,
            reason="Human validates the newer real Salsa MSRV declaration.",
            validation_review={
                "validation_basis": "EVIDENCE_REVIEW",
                "validation_note": (
                    f"Captured Git blob {after['blob_sha']} line {after['line']} declares rust-version 1.88."
                ),
                "competition_note": (
                    f"{CLAIM_BEFORE} remains historical reviewed knowledge until separately dispositioned."
                ),
                "decision_id": "cvd:live-salsa-msrv:after",
            },
        )

        challenged = engine.transition_claim(
            CLAIM_BEFORE,
            "CHALLENGED",
            actor=CHALLENGER_AI,
            reason=(
                f"Real upstream commit {after['revision']} is a child of {before['revision']} and "
                f"changes the pinned declaration to 1.88; {CLAIM_BEFORE} requires re-verification."
            ),
        )
        assert challenged["last_verified"] == old_last_verified
        assert challenged["evidence_ids"] == [evidence_before]

        disposed = dispose_claim(
            repository,
            CLAIM_BEFORE,
            "SUPERSEDED",
            actor=HUMAN,
            reason="Human confirms the real Salsa MSRV update supersedes the former current-use Claim.",
            successor_claim_id=CLAIM_AFTER,
            competition_note=f"{CLAIM_AFTER} is VALIDATED from the child commit and exact new Git blob.",
            decision_id="cdd:live-salsa-msrv:before-to-after",
        )
        assert disposed["claim"]["maturity"] == "SUPERSEDED"
        assert disposed["claim"]["superseded_by"] == CLAIM_AFTER

        before_explanation = explain_claim(repository, CLAIM_BEFORE)
        after_explanation = explain_claim(repository, CLAIM_AFTER)
        assert before_explanation["claim"]["maturity"] == "SUPERSEDED"
        assert after_explanation["claim"]["maturity"] == "VALIDATED"
        assert before_explanation["evidence_chains"][0]["source_snapshot"]["revision"] == before["revision"]
        assert after_explanation["evidence_chains"][0]["source_snapshot"]["revision"] == after["revision"]
        assert before_explanation["evidence_chains"][0]["evidence"]["source_id"] == SOURCE_ID
        assert after_explanation["evidence_chains"][0]["evidence"]["source_id"] == SOURCE_ID
        assert {item["revision"] for item in repository.list("source_snapshot")} == {
            before["revision"],
            after["revision"],
        }
    finally:
        connection.close()
