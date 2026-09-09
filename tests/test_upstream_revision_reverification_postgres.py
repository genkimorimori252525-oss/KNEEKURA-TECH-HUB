from __future__ import annotations

from hashlib import sha1
import os
from pathlib import Path

import psycopg
import pytest

from kneekura_tech_hub.authorization import (
    AcquisitionAuthorizationEngine,
    authorization_effectiveness,
)
from kneekura_tech_hub.claim_disposition import (
    ClaimDispositionError,
    claim_disposition_history,
    dispose_claim,
)
from kneekura_tech_hub.claim_support import claim_support_history
from kneekura_tech_hub.claim_validation import claim_validation_history
from kneekura_tech_hub.comparison import compare_claim
from kneekura_tech_hub.database import apply_migrations
from kneekura_tech_hub.execution import execute_authorized_acquisition
from kneekura_tech_hub.explanation import explain_claim
from kneekura_tech_hub.observation_triage_postgres import ObservationTriagePostgresRepository
from kneekura_tech_hub.selected_file_extraction import ingest_selected_file_extraction
from kneekura_tech_hub.selection import SourceSelectionEngine
from kneekura_tech_hub.service import CurationEngine, CurationError
from kneekura_tech_hub.verified_commit import commit_verified_acquisition


DSN = os.getenv("KTHUB_TEST_DATABASE_URL")
pytestmark = pytest.mark.skipif(not DSN, reason="KTHUB_TEST_DATABASE_URL is not set")

DISCOVERY_TOOL = {"actor_type": "tool", "actor_id": "upstream-discovery", "version": "v1"}
FETCH_TOOL = {"actor_type": "tool", "actor_id": "upstream-fetch", "version": "v1"}
COMMIT_TOOL = {"actor_type": "tool", "actor_id": "upstream-commit", "version": "v1"}
EXTRACTOR_AI = {"actor_type": "ai", "actor_id": "upstream-extractor", "version": "v1"}
CHALLENGER_AI = {"actor_type": "ai", "actor_id": "upstream-challenger", "version": "v1"}
HUMAN = {"actor_type": "human", "actor_id": "upstream-reviewer"}

SOURCE_ID = "src:github:example:upstream-refresh"
SELECTION_ID = "sd:upstream-refresh"
AUTH_V1 = "aa:upstream-refresh:v1"
AUTH_V2 = "aa:upstream-refresh:v2"
REV_V1 = "1111111111111111111111111111111111111111"
REV_V2 = "2222222222222222222222222222222222222222"
ENTITY_ID = "ke:upstream-refresh:cache-mode"
CLAIM_V1 = "cl:upstream-refresh:cache-mode:v1"
CLAIM_V2 = "cl:upstream-refresh:cache-mode:v2"

README_V1 = b"# Cache mode\ncache_mode defaults to enabled for all workloads.\n"
README_V2 = b"# Cache mode\ncache_mode now defaults to disabled; enable it only for read-heavy workloads.\n"


def _blob_sha(content: bytes) -> str:
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


def _execute_and_commit(
    repository,
    *,
    authorization_id: str,
    revision: str,
    content: bytes,
    suffix: str,
    storage_root: Path,
):
    def fetch_file(source, actual_revision, path):
        assert source["id"] == SOURCE_ID
        assert actual_revision == revision
        assert path == "README.md"
        return {"content": content, "git_blob_sha": _blob_sha(content)}

    execution = execute_authorized_acquisition(
        repository,
        authorization_id,
        storage_root=storage_root,
        fetch_file=fetch_file,
        actor=FETCH_TOOL,
        execution_id=f"ax:upstream-refresh:{suffix}",
    )
    assert execution["status"] == "SUCCEEDED"

    commit = commit_verified_acquisition(
        repository,
        execution["id"],
        storage_root=storage_root,
        actor=COMMIT_TOOL,
        commit_id=f"vc:upstream-refresh:{suffix}",
    )
    snapshot = repository.get(commit["snapshot_id"])
    assert snapshot is not None
    assert snapshot["source_id"] == SOURCE_ID
    assert snapshot["revision"] == revision
    return commit, snapshot


def _extract(engine, *, snapshot_id: str, summary: str, storage_root: Path) -> str:
    result = ingest_selected_file_extraction(
        engine,
        {
            "proposal_version": "1.0",
            "snapshot_id": snapshot_id,
            "findings": [
                {
                    "summary": summary,
                    "candidate_names": ["cache_mode default"],
                    "anchors": [{"path": "README.md", "line_start": 2, "line_end": 2}],
                }
            ],
        },
        storage_root=storage_root,
        actor=EXTRACTOR_AI,
    )
    return result["evidence_ids"][0]


def test_new_upstream_revision_preserves_history_and_requires_fresh_human_authority(
    tmp_path: Path,
) -> None:
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
                "origin": {
                    "provider": "github",
                    "repository": "example/upstream-refresh",
                    "url": "https://github.com/example/upstream-refresh",
                    "default_branch": "main",
                },
                "acquisition": {"level": "metadata-only"},
                "license": {
                    "state": "KNOWN",
                    "declared_expression": "MIT",
                    "handling_policy": "REFERENCE_ONLY",
                },
            },
            actor=DISCOVERY_TOOL,
        )
        selection = SourceSelectionEngine(repository).create_from_fields(
            source_id=SOURCE_ID,
            decision="SELECT_FOR_REVIEW",
            rationale="Human selects this Source for bounded upstream revision tracking.",
            actor=HUMAN,
            decision_id=SELECTION_ID,
        )

        authorization_v1 = AcquisitionAuthorizationEngine(repository).authorize_from_fields(
            source_id=SOURCE_ID,
            selection_decision_id=selection["id"],
            revision=REV_V1,
            allowed_paths=["README.md"],
            rationale="Human authorizes the first exact revision and README only.",
            actor=HUMAN,
            authorization_id=AUTH_V1,
        )
        commit_v1, snapshot_v1 = _execute_and_commit(
            repository,
            authorization_id=authorization_v1["id"],
            revision=REV_V1,
            content=README_V1,
            suffix="v1",
            storage_root=tmp_path,
        )
        assert repository.get(SOURCE_ID)["acquisition"] == {"level": "selected-files"}
        first_effectiveness = authorization_effectiveness(repository, AUTH_V1)
        assert first_effectiveness["effective"] is False
        assert "SOURCE_NO_LONGER_METADATA_ONLY" in first_effectiveness["blockers"]

        evidence_v1 = _extract(
            engine,
            snapshot_id=snapshot_v1["id"],
            summary="At revision v1 the project says cache_mode defaults to enabled.",
            storage_root=tmp_path,
        )
        engine.create_entity(
            {
                "record_type": "knowledge_entity",
                "id": ENTITY_ID,
                "canonical_name": "cache_mode upstream default",
                "aliases": [],
                "kinds": ["configuration"],
                "abstraction_level": "L1",
                "identity_state": "CANONICAL",
                "relations": [],
            },
            actor=HUMAN,
            reason="Human creates one stable subject for the upstream setting.",
        )
        engine.create_claim(
            {
                "record_type": "claim",
                "id": CLAIM_V1,
                "entity_id": ENTITY_ID,
                "claim_type": "AUTHOR_CLAIM",
                "statement": "The current upstream cache_mode default is enabled.",
                "maturity": "CANDIDATE",
                "evidence_ids": [evidence_v1],
                "scope": {"source_id": SOURCE_ID, "setting": "cache_mode", "meaning": "current upstream default"},
                "applicability": {"context": "project default configuration"},
                "created_by": EXTRACTOR_AI,
                "policy_version": "1.0.0",
            },
            actor=EXTRACTOR_AI,
            reason="AI proposes the current-use Claim from the pinned v1 Snapshot.",
        )
        engine.transition_claim(
            CLAIM_V1,
            "SUPPORTED",
            actor=HUMAN,
            reason="Human reviews the v1 pinned line before support.",
            support_review={"decision_id": "csd:upstream-refresh:v1"},
        )
        validated_v1 = engine.transition_claim(
            CLAIM_V1,
            "VALIDATED",
            actor=HUMAN,
            reason="Human validates the current-use Claim against v1.",
            validation_review={
                "validation_basis": "EVIDENCE_REVIEW",
                "validation_note": "The pinned v1 README line directly states the default.",
                "decision_id": "cvd:upstream-refresh:v1",
            },
        )
        last_verified_v1 = validated_v1["last_verified"]
        explanation_v1_before = explain_claim(repository, CLAIM_V1)

        authorization_v2 = AcquisitionAuthorizationEngine(repository).authorize_from_fields(
            source_id=SOURCE_ID,
            selection_decision_id=selection["id"],
            revision=REV_V2,
            allowed_paths=["README.md"],
            rationale="Human explicitly authorizes re-acquisition at the newer exact revision.",
            actor=HUMAN,
            authorization_id=AUTH_V2,
            supersedes_authorization_id=AUTH_V1,
        )
        assert authorization_effectiveness(repository, AUTH_V2)["effective"] is True

        commit_v2, snapshot_v2 = _execute_and_commit(
            repository,
            authorization_id=authorization_v2["id"],
            revision=REV_V2,
            content=README_V2,
            suffix="v2",
            storage_root=tmp_path,
        )
        assert commit_v2["snapshot_id"] != commit_v1["snapshot_id"]
        assert snapshot_v2["id"] != snapshot_v1["id"]
        assert snapshot_v2["source_id"] == snapshot_v1["source_id"] == SOURCE_ID
        assert repository.get(snapshot_v1["id"]) == snapshot_v1
        assert repository.get(SOURCE_ID)["acquisition"] == {"level": "selected-files"}

        consumed_v2 = authorization_effectiveness(repository, AUTH_V2)
        assert consumed_v2["effective"] is False
        assert "AUTHORIZATION_ALREADY_COMMITTED" in consumed_v2["blockers"]

        evidence_v2 = _extract(
            engine,
            snapshot_id=snapshot_v2["id"],
            summary="At revision v2 the project says cache_mode now defaults to disabled.",
            storage_root=tmp_path,
        )
        engine.create_claim(
            {
                "record_type": "claim",
                "id": CLAIM_V2,
                "entity_id": ENTITY_ID,
                "claim_type": "AUTHOR_CLAIM",
                "statement": "The current upstream cache_mode default is disabled.",
                "maturity": "CANDIDATE",
                "evidence_ids": [evidence_v2],
                "scope": {"source_id": SOURCE_ID, "setting": "cache_mode", "meaning": "current upstream default"},
                "applicability": {"context": "project default configuration"},
                "created_by": EXTRACTOR_AI,
                "policy_version": "1.0.0",
            },
            actor=EXTRACTOR_AI,
            reason="AI proposes the newer current-use Claim without rewriting the reviewed v1 Claim.",
        )

        assert repository.get(CLAIM_V1)["maturity"] == "VALIDATED"
        comparison = compare_claim(repository, CLAIM_V1)
        assert comparison["active_claim_ids"] == sorted([CLAIM_V1, CLAIM_V2])
        assert "MULTIPLE_ACTIVE_CLAIMS" in comparison["flags"]
        assert "STATEMENTS_DIFFER" in comparison["flags"]
        assert "winner" not in comparison
        assert "preferred_claim_id" not in comparison

        with pytest.raises(CurationError, match="competition_note"):
            engine.transition_claim(
                CLAIM_V2,
                "SUPPORTED",
                actor=HUMAN,
                reason="Competition must not be hidden.",
            )
        supported_v2 = engine.transition_claim(
            CLAIM_V2,
            "SUPPORTED",
            actor=HUMAN,
            reason="Human reviews the newer Snapshot while preserving the older active Claim.",
            support_review={
                "competition_note": f"{CLAIM_V1} is the still-active Claim supported by the older v1 Snapshot.",
                "decision_id": "csd:upstream-refresh:v2",
            },
        )
        assert supported_v2["maturity"] == "SUPPORTED"
        support_v2 = claim_support_history(repository, claim_id=CLAIM_V2)[0]
        assert support_v2["evidence_ids"] == [evidence_v2]
        assert support_v2["distinct_source_ids"] == [SOURCE_ID]
        assert support_v2["distinct_snapshot_ids"] == [snapshot_v2["id"]]
        assert support_v2["competing_active_claim_ids"] == [CLAIM_V1]

        with pytest.raises(CurationError, match="competition_note"):
            engine.transition_claim(
                CLAIM_V2,
                "VALIDATED",
                actor=HUMAN,
                reason="Validation must not hide the old active Claim.",
            )
        validated_v2 = engine.transition_claim(
            CLAIM_V2,
            "VALIDATED",
            actor=HUMAN,
            reason="Human validates the new upstream default against the v2 Snapshot.",
            validation_review={
                "validation_basis": "EVIDENCE_REVIEW",
                "validation_note": "The pinned v2 README line directly states the new default.",
                "competition_note": f"{CLAIM_V1} remains historical reviewed knowledge from v1 and will be dispositioned separately.",
                "decision_id": "cvd:upstream-refresh:v2",
            },
        )
        assert validated_v2["maturity"] == "VALIDATED"
        validation_v2 = claim_validation_history(repository, claim_id=CLAIM_V2)[0]
        assert validation_v2["distinct_snapshot_ids"] == [snapshot_v2["id"]]
        assert validation_v2["competing_active_claim_ids"] == [CLAIM_V1]

        challenged_v1 = engine.transition_claim(
            CLAIM_V1,
            "CHALLENGED",
            actor=CHALLENGER_AI,
            reason=(
                f"Newer immutable Snapshot {snapshot_v2['id']} supports successor Claim {CLAIM_V2}; "
                "re-verification is required before treating the old current-use wording as current."
            ),
        )
        assert challenged_v1["maturity"] == "CHALLENGED"
        assert challenged_v1["last_verified"] == last_verified_v1
        assert challenged_v1["evidence_ids"] == [evidence_v1]

        with pytest.raises(ClaimDispositionError, match="human reviewer"):
            dispose_claim(
                repository,
                CLAIM_V1,
                "SUPERSEDED",
                actor=CHALLENGER_AI,
                reason="AI must not decide terminal supersession.",
                successor_claim_id=CLAIM_V2,
                competition_note="The newer Claim exists.",
            )

        disposed = dispose_claim(
            repository,
            CLAIM_V1,
            "SUPERSEDED",
            actor=HUMAN,
            reason="Human confirms v2 replaced the old current-use default while preserving v1 history.",
            successor_claim_id=CLAIM_V2,
            competition_note=f"{CLAIM_V2} is VALIDATED from the newer Snapshot and describes the same exact subject.",
            decision_id="cdd:upstream-refresh:v1-to-v2",
        )
        assert disposed["claim"]["maturity"] == "SUPERSEDED"
        assert disposed["claim"]["superseded_by"] == CLAIM_V2
        disposition = claim_disposition_history(repository, claim_id=CLAIM_V1)[0]
        assert disposition["successor_claim_id"] == CLAIM_V2

        explanation_v1_after = explain_claim(repository, CLAIM_V1)
        explanation_v2 = explain_claim(repository, CLAIM_V2)
        assert explanation_v1_after["claim"]["maturity"] == "SUPERSEDED"
        assert explanation_v1_after["claim"]["last_verified"] == last_verified_v1
        assert explanation_v1_after["evidence_chains"][0]["source_snapshot"]["id"] == snapshot_v1["id"]
        assert explanation_v2["claim"]["maturity"] == "VALIDATED"
        assert explanation_v2["evidence_chains"][0]["source_snapshot"]["id"] == snapshot_v2["id"]
        assert explanation_v1_before["evidence_chains"][0]["source_snapshot"] == (
            explanation_v1_after["evidence_chains"][0]["source_snapshot"]
        )
        assert {item["id"] for item in repository.list("source_snapshot") if item["source_id"] == SOURCE_ID} == {
            snapshot_v1["id"],
            snapshot_v2["id"],
        }
    finally:
        connection.close()
