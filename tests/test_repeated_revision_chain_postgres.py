from __future__ import annotations

from hashlib import sha1
import os
from pathlib import Path

import psycopg
import pytest

from kneekura_tech_hub.authorization import (
    AcquisitionAuthorizationEngine,
    acquisition_authorization_history,
    active_acquisition_authorizations,
    authorization_effectiveness,
    authorized_acquisition_requests,
)
from kneekura_tech_hub.authorization_postgres import AuthorizationPostgresRepository
from kneekura_tech_hub.claim_disposition import claim_disposition_history, dispose_claim
from kneekura_tech_hub.claim_support import claim_support_history
from kneekura_tech_hub.claim_validation import claim_validation_history
from kneekura_tech_hub.comparison import compare_claim
from kneekura_tech_hub.database import apply_migrations
from kneekura_tech_hub.execution import AcquisitionExecutionError, execute_authorized_acquisition
from kneekura_tech_hub.explanation import explain_claim
from kneekura_tech_hub.observation_triage_postgres import ObservationTriagePostgresRepository
from kneekura_tech_hub.selected_file_extraction import ingest_selected_file_extraction
from kneekura_tech_hub.selection import SourceSelectionEngine
from kneekura_tech_hub.service import CurationEngine
from kneekura_tech_hub.verified_commit import commit_verified_acquisition


DSN = os.getenv("KTHUB_TEST_DATABASE_URL")
pytestmark = pytest.mark.skipif(not DSN, reason="KTHUB_TEST_DATABASE_URL is not set")

DISCOVERY_TOOL = {"actor_type": "tool", "actor_id": "revision-chain-discovery", "version": "v1"}
FETCH_TOOL = {"actor_type": "tool", "actor_id": "revision-chain-fetch", "version": "v1"}
COMMIT_TOOL = {"actor_type": "tool", "actor_id": "revision-chain-commit", "version": "v1"}
EXTRACTOR_AI = {"actor_type": "ai", "actor_id": "revision-chain-extractor", "version": "v1"}
CHALLENGER_AI = {"actor_type": "ai", "actor_id": "revision-chain-challenger", "version": "v1"}
HUMAN = {"actor_type": "human", "actor_id": "revision-chain-reviewer"}

SOURCE_ID = "src:github:example:revision-chain"
SELECTION_ID = "sd:revision-chain"
ENTITY_ID = "ke:revision-chain:cache-mode"

REVISIONS = [str(index) * 40 for index in range(1, 5)]
AUTHORIZATION_IDS = [f"aa:revision-chain:v{index}" for index in range(1, 5)]
CLAIM_IDS = [f"cl:revision-chain:cache-mode:v{index}" for index in range(1, 5)]

CONTENTS = [
    b"# Cache mode\ncache_mode defaults to enabled.\n",
    b"# Cache mode\ncache_mode defaults to disabled.\n",
    # v3 deliberately reverts to the same semantic statement as v1. It must still create a new
    # generation rather than resurrecting or rewriting the superseded v1 Claim.
    b"# Cache mode\ncache_mode defaults to enabled.\n",
    b"# Cache mode\ncache_mode defaults to adaptive.\n",
]
STATEMENTS = [
    "The current upstream cache_mode default is enabled.",
    "The current upstream cache_mode default is disabled.",
    "The current upstream cache_mode default is enabled.",
    "The current upstream cache_mode default is adaptive.",
]


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
    generation: int,
    authorization_id: str,
    revision: str,
    content: bytes,
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
        execution_id=f"ax:revision-chain:v{generation}",
    )
    assert execution["status"] == "SUCCEEDED"

    commit = commit_verified_acquisition(
        repository,
        execution["id"],
        storage_root=storage_root,
        actor=COMMIT_TOOL,
        commit_id=f"vc:revision-chain:v{generation}",
    )
    snapshot = repository.get(commit["snapshot_id"])
    assert snapshot is not None
    assert snapshot["source_id"] == SOURCE_ID
    assert snapshot["revision"] == revision
    return commit, snapshot


def _extract(
    engine: CurationEngine,
    *,
    generation: int,
    snapshot_id: str,
    storage_root: Path,
) -> str:
    result = ingest_selected_file_extraction(
        engine,
        {
            "proposal_version": "1.0",
            "snapshot_id": snapshot_id,
            "findings": [
                {
                    "summary": (
                        f"At revision v{generation}, README states the cache_mode default for this generation."
                    ),
                    "candidate_names": ["cache_mode default"],
                    "anchors": [{"path": "README.md", "line_start": 2, "line_end": 2}],
                }
            ],
        },
        storage_root=storage_root,
        actor=EXTRACTOR_AI,
    )
    assert len(result["evidence_ids"]) == 1
    return result["evidence_ids"][0]


def _create_reviewed_claim(
    engine: CurationEngine,
    repository,
    *,
    generation: int,
    evidence_id: str,
    snapshot_id: str,
    competing_claim_id: str | None,
) -> dict:
    claim_id = CLAIM_IDS[generation - 1]
    engine.create_claim(
        {
            "record_type": "claim",
            "id": claim_id,
            "entity_id": ENTITY_ID,
            "claim_type": "AUTHOR_CLAIM",
            "statement": STATEMENTS[generation - 1],
            "maturity": "CANDIDATE",
            "evidence_ids": [evidence_id],
            "scope": {
                "source_id": SOURCE_ID,
                "setting": "cache_mode",
                "meaning": "current upstream default",
            },
            "applicability": {"context": "project default configuration"},
            "created_by": EXTRACTOR_AI,
            "policy_version": "1.0.0",
        },
        actor=EXTRACTOR_AI,
        reason=f"AI proposes generation v{generation} from its pinned immutable Snapshot.",
    )

    comparison = compare_claim(repository, claim_id)
    expected_active = [claim_id] if competing_claim_id is None else sorted([competing_claim_id, claim_id])
    assert comparison["active_claim_ids"] == expected_active
    assert "winner" not in comparison
    assert "preferred_claim_id" not in comparison

    support_review = {"decision_id": f"csd:revision-chain:v{generation}"}
    if competing_claim_id is not None:
        support_review["competition_note"] = (
            f"{competing_claim_id} is the still-active previous generation while {claim_id} is reviewed."
        )
    supported = engine.transition_claim(
        claim_id,
        "SUPPORTED",
        actor=HUMAN,
        reason=f"Human reviews the exact v{generation} Snapshot before support.",
        support_review=support_review,
    )
    assert supported["maturity"] == "SUPPORTED"

    validation_review = {
        "validation_basis": "EVIDENCE_REVIEW",
        "validation_note": f"Pinned Snapshot {snapshot_id} directly states the v{generation} default.",
        "decision_id": f"cvd:revision-chain:v{generation}",
    }
    if competing_claim_id is not None:
        validation_review["competition_note"] = (
            f"{competing_claim_id} remains active until a separate human disposition decision."
        )
    validated = engine.transition_claim(
        claim_id,
        "VALIDATED",
        actor=HUMAN,
        reason=f"Human validates generation v{generation} against its pinned Snapshot.",
        validation_review=validation_review,
    )
    assert validated["maturity"] == "VALIDATED"

    support = claim_support_history(repository, claim_id=claim_id)
    validation = claim_validation_history(repository, claim_id=claim_id)
    assert len(support) == 1
    assert len(validation) == 1
    assert support[0]["evidence_ids"] == [evidence_id]
    assert validation[0]["evidence_ids"] == [evidence_id]
    assert support[0]["distinct_snapshot_ids"] == [snapshot_id]
    assert validation[0]["distinct_snapshot_ids"] == [snapshot_id]
    return validated


def test_four_generation_revision_chain_preserves_one_shot_authority_and_history(
    tmp_path: Path,
) -> None:
    assert DSN is not None
    connection = psycopg.connect(DSN, autocommit=True)
    try:
        apply_migrations(connection)
        _truncate(connection)
        repository = ObservationTriagePostgresRepository(connection)
        authorization_repository = AuthorizationPostgresRepository(connection)
        engine = CurationEngine(repository)

        engine.register_source(
            {
                "record_type": "source",
                "id": SOURCE_ID,
                "kind": "repository",
                "origin": {
                    "provider": "github",
                    "repository": "example/revision-chain",
                    "url": "https://github.com/example/revision-chain",
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
            rationale="Human selects one stable Source for repeated bounded revision review.",
            actor=HUMAN,
            decision_id=SELECTION_ID,
        )
        engine.create_entity(
            {
                "record_type": "knowledge_entity",
                "id": ENTITY_ID,
                "canonical_name": "cache_mode upstream default across revisions",
                "aliases": [],
                "kinds": ["configuration"],
                "abstraction_level": "L1",
                "identity_state": "CANONICAL",
                "relations": [],
            },
            actor=HUMAN,
            reason="Human creates one stable semantic subject for the revision-chain acceptance test.",
        )

        commits: list[dict] = []
        snapshots: list[dict] = []
        evidence_ids: list[str] = []
        last_verified: dict[str, str] = {}
        previous_authorization_id: str | None = None
        previous_claim_id: str | None = None

        for generation, (revision, authorization_id, content) in enumerate(
            zip(REVISIONS, AUTHORIZATION_IDS, CONTENTS, strict=True),
            start=1,
        ):
            authorization = AcquisitionAuthorizationEngine(
                authorization_repository
            ).authorize_from_fields(
                source_id=SOURCE_ID,
                selection_decision_id=selection["id"],
                revision=revision,
                allowed_paths=["README.md"],
                rationale=f"Human authorizes exact revision v{generation} and README only.",
                actor=HUMAN,
                authorization_id=authorization_id,
                supersedes_authorization_id=previous_authorization_id,
            )
            assert authorization_effectiveness(
                authorization_repository,
                authorization_id,
            )["effective"] is True
            assert [
                record["id"]
                for record in active_acquisition_authorizations(
                    authorization_repository,
                    source_id=SOURCE_ID,
                )
            ] == [authorization_id]

            commit, snapshot = _execute_and_commit(
                repository,
                generation=generation,
                authorization_id=authorization_id,
                revision=revision,
                content=content,
                storage_root=tmp_path,
            )
            commits.append(commit)
            snapshots.append(snapshot)

            consumed = authorization_effectiveness(authorization_repository, authorization_id)
            assert consumed["effective"] is False
            assert "AUTHORIZATION_ALREADY_COMMITTED" in consumed["blockers"]
            assert repository.get(SOURCE_ID)["acquisition"] == {"level": "selected-files"}

            evidence_id = _extract(
                engine,
                generation=generation,
                snapshot_id=snapshot["id"],
                storage_root=tmp_path,
            )
            evidence_ids.append(evidence_id)
            validated = _create_reviewed_claim(
                engine,
                repository,
                generation=generation,
                evidence_id=evidence_id,
                snapshot_id=snapshot["id"],
                competing_claim_id=previous_claim_id,
            )
            claim_id = CLAIM_IDS[generation - 1]
            last_verified[claim_id] = validated["last_verified"]

            if previous_claim_id is not None:
                challenged = engine.transition_claim(
                    previous_claim_id,
                    "CHALLENGED",
                    actor=CHALLENGER_AI,
                    reason=(
                        f"Newer immutable generation v{generation} supports {claim_id}; "
                        f"re-verification of {previous_claim_id} is required."
                    ),
                )
                assert challenged["maturity"] == "CHALLENGED"
                assert challenged["last_verified"] == last_verified[previous_claim_id]

                disposed = dispose_claim(
                    repository,
                    previous_claim_id,
                    "SUPERSEDED",
                    actor=HUMAN,
                    reason=(
                        f"Human confirms generation v{generation} replaces the previous current-use Claim "
                        "without rewriting historical provenance."
                    ),
                    successor_claim_id=claim_id,
                    competition_note=f"{claim_id} is VALIDATED from the newer immutable Snapshot.",
                    decision_id=f"cdd:revision-chain:v{generation - 1}-to-v{generation}",
                )
                assert disposed["claim"]["maturity"] == "SUPERSEDED"
                assert disposed["claim"]["superseded_by"] == claim_id
                assert disposed["claim"]["last_verified"] == last_verified[previous_claim_id]

                after_disposition = compare_claim(repository, claim_id)
                assert after_disposition["active_claim_ids"] == [claim_id]
                assert "MULTIPLE_ACTIVE_CLAIMS" not in after_disposition["flags"]

            previous_authorization_id = authorization_id
            previous_claim_id = claim_id

        # Every human grant remains in append-only history, but only A4 is lineage-active and it
        # is already consumed. Therefore no effective acquisition request remains.
        authorization_history = acquisition_authorization_history(
            authorization_repository,
            source_id=SOURCE_ID,
        )
        assert [record["id"] for record in authorization_history] == AUTHORIZATION_IDS
        assert [
            record["id"]
            for record in active_acquisition_authorizations(
                authorization_repository,
                source_id=SOURCE_ID,
            )
        ] == [AUTHORIZATION_IDS[-1]]
        assert authorized_acquisition_requests(authorization_repository) == []

        for index, authorization_id in enumerate(AUTHORIZATION_IDS):
            status = authorization_effectiveness(authorization_repository, authorization_id)
            assert status["effective"] is False
            assert "AUTHORIZATION_ALREADY_COMMITTED" in status["blockers"]
            if index < len(AUTHORIZATION_IDS) - 1:
                assert "NOT_ACTIVE_AUTHORIZATION" in status["blockers"]
            else:
                assert "NOT_ACTIVE_AUTHORIZATION" not in status["blockers"]

        # An old committed grant cannot become usable again after later generations exist.
        def forbidden_fetch(*_args, **_kwargs):
            raise AssertionError("stale authority must fail before any fetch is attempted")

        with pytest.raises(AcquisitionExecutionError, match="not currently effective"):
            execute_authorized_acquisition(
                repository,
                AUTHORIZATION_IDS[1],
                storage_root=tmp_path,
                fetch_file=forbidden_fetch,
                actor=FETCH_TOOL,
                execution_id="ax:revision-chain:stale-reuse",
            )

        assert {commit["authorization_id"] for commit in commits} == set(AUTHORIZATION_IDS)
        assert len({commit["id"] for commit in commits}) == 4
        assert len({snapshot["id"] for snapshot in snapshots}) == 4
        assert {snapshot["revision"] for snapshot in snapshots} == set(REVISIONS)
        assert {
            item["id"]
            for item in repository.list("source_snapshot")
            if item["source_id"] == SOURCE_ID
        } == {snapshot["id"] for snapshot in snapshots}

        # Claim generations form a forward-only terminal chain. v3 repeats v1's statement, but
        # v1 stays SUPERSEDED instead of being resurrected or rewritten.
        for index, claim_id in enumerate(CLAIM_IDS[:-1]):
            claim = repository.get(claim_id)
            assert claim is not None
            assert claim["maturity"] == "SUPERSEDED"
            assert claim["superseded_by"] == CLAIM_IDS[index + 1]
            assert claim["last_verified"] == last_verified[claim_id]
            disposition = claim_disposition_history(repository, claim_id=claim_id)
            assert len(disposition) == 1
            assert disposition[0]["successor_claim_id"] == CLAIM_IDS[index + 1]

        final_claim = repository.get(CLAIM_IDS[-1])
        assert final_claim is not None
        assert final_claim["maturity"] == "VALIDATED"
        assert final_claim.get("superseded_by") is None

        assert repository.get(CLAIM_IDS[0])["statement"] == repository.get(CLAIM_IDS[2])["statement"]
        assert repository.get(CLAIM_IDS[0])["maturity"] == "SUPERSEDED"
        assert repository.get(CLAIM_IDS[2])["maturity"] == "SUPERSEDED"
        assert evidence_ids[0] != evidence_ids[2]

        final_comparison = compare_claim(repository, CLAIM_IDS[-1])
        assert final_comparison["claim_count"] == 4
        assert final_comparison["active_claim_count"] == 1
        assert final_comparison["active_claim_ids"] == [CLAIM_IDS[-1]]
        assert "HAS_SUPERSEDED_CLAIM" in final_comparison["flags"]
        assert "MULTIPLE_ACTIVE_CLAIMS" not in final_comparison["flags"]
        assert final_comparison["needs_review"] is False

        # Every generation remains independently explainable to the exact immutable Snapshot that
        # existed when that generation was reviewed.
        for index, claim_id in enumerate(CLAIM_IDS):
            explanation = explain_claim(repository, claim_id)
            assert explanation["claim"]["id"] == claim_id
            assert explanation["evidence_chains"][0]["evidence"]["id"] == evidence_ids[index]
            assert explanation["evidence_chains"][0]["source_snapshot"]["id"] == snapshots[index]["id"]
            assert explanation["evidence_chains"][0]["source_snapshot"]["revision"] == REVISIONS[index]
            assert explanation["evidence_chains"][0]["source"]["id"] == SOURCE_ID
    finally:
        connection.close()
