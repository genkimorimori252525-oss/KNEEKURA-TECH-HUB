from __future__ import annotations

import json
from hashlib import sha1
import os
from pathlib import Path

import psycopg
import pytest

from kneekura_tech_hub.authorization import AcquisitionAuthorizationEngine
from kneekura_tech_hub.claim_support import claim_support_history
from kneekura_tech_hub.claim_validation import claim_validation_history
from kneekura_tech_hub.database import apply_migrations
from kneekura_tech_hub.discovery import ingest_discovery_intake
from kneekura_tech_hub.execution import execute_authorized_acquisition
from kneekura_tech_hub.explanation import explain_claim
from kneekura_tech_hub.github_adapter import build_metadata_discovery_batch
from kneekura_tech_hub.observation_candidate_attachment import (
    ObservationCandidateAttachmentError,
    attach_observation_to_candidate_claim,
)
from kneekura_tech_hub.observation_triage import transition_observation
from kneekura_tech_hub.observation_triage_postgres import ObservationTriagePostgresRepository
from kneekura_tech_hub.selected_file_extraction import ingest_selected_file_extraction
from kneekura_tech_hub.selection import SourceSelectionEngine
from kneekura_tech_hub.service import CurationEngine
from kneekura_tech_hub.verified_commit import commit_verified_acquisition


DSN = os.getenv("KTHUB_TEST_DATABASE_URL")
pytestmark = pytest.mark.skipif(not DSN, reason="KTHUB_TEST_DATABASE_URL is not set")
ROOT = Path(__file__).resolve().parents[1]
SEARCH_FIXTURE = ROOT / "tests" / "fixtures" / "github_repository_search_v1.json"

DISCOVERY_TOOL = {"actor_type": "tool", "actor_id": "cross-source-discovery", "version": "v1"}
FETCH_TOOL = {"actor_type": "tool", "actor_id": "cross-source-fetch", "version": "v1"}
COMMIT_TOOL = {"actor_type": "tool", "actor_id": "cross-source-commit", "version": "v1"}
EXTRACTOR_AI = {"actor_type": "ai", "actor_id": "cross-source-extractor", "version": "v1"}
TRIAGE_TOOL = {"actor_type": "tool", "actor_id": "cross-source-triage", "version": "v1"}
HUMAN = {"actor_type": "human", "actor_id": "cross-source-reviewer"}
AI = {"actor_type": "ai", "actor_id": "cross-source-attacker", "version": "v1"}

SOURCE_A = "src:github:example:small-but-relevant"
SOURCE_B = "src:github:example:huge-star-repo"
REVISION_A = "1111111111111111111111111111111111111111"
REVISION_B = "2222222222222222222222222222222222222222"
ENTITY_ID = "ke:acceptance:cross-source-incremental"
CLAIM_ID = "cl:acceptance:cross-source-incremental"

README_A = b"# Incremental engine\nIncremental recomputation avoids unchanged work.\n"
README_B = (
    b"# Partial rebuilds\n"
    b"Incremental processing reuses unaffected results instead of recomputing unchanged work.\n"
)


def _blob_sha(content: bytes) -> str:
    header = f"blob {len(content)}\0".encode("ascii")
    return sha1(header + content).hexdigest()  # noqa: S324 - Git object identity


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


def _search_payload() -> dict:
    return json.loads(SEARCH_FIXTURE.read_text(encoding="utf-8"))


def _resolve_license(repository, source_id: str, expression: str) -> None:
    source = repository.get(source_id)
    assert source is not None
    assert source["license"]["state"] == "REVIEW_REQUIRED"
    source["license"] = {
        "state": "KNOWN",
        "declared_expression": expression,
        "handling_policy": "REFERENCE_ONLY",
    }
    repository.put(source, replace=True)


def _acquire(
    repository,
    *,
    source_id: str,
    revision: str,
    content: bytes,
    suffix: str,
    license_expression: str,
    storage_root: Path,
) -> str:
    selection = SourceSelectionEngine(repository).create_from_fields(
        source_id=source_id,
        decision="SELECT_FOR_REVIEW",
        rationale=f"Human selected independent cross-source fixture {suffix} for review.",
        actor=HUMAN,
        decision_id=f"sd:cross-source:{suffix}",
    )
    _resolve_license(repository, source_id, license_expression)

    authorization = AcquisitionAuthorizationEngine(repository).authorize_from_fields(
        source_id=source_id,
        selection_decision_id=selection["id"],
        revision=revision,
        allowed_paths=["README.md"],
        rationale=f"Human authorizes only the pinned README for cross-source fixture {suffix}.",
        actor=HUMAN,
        authorization_id=f"aa:cross-source:{suffix}",
    )

    def fetch_file(_source, actual_revision, path):
        assert _source["id"] == source_id
        assert actual_revision == revision
        assert path == "README.md"
        return {"content": content, "git_blob_sha": _blob_sha(content)}

    execution = execute_authorized_acquisition(
        repository,
        authorization["id"],
        storage_root=storage_root,
        fetch_file=fetch_file,
        actor=FETCH_TOOL,
        execution_id=f"ax:cross-source:{suffix}",
    )
    assert execution["status"] == "SUCCEEDED"

    verified = commit_verified_acquisition(
        repository,
        execution["id"],
        storage_root=storage_root,
        actor=COMMIT_TOOL,
        commit_id=f"vc:cross-source:{suffix}",
    )
    snapshot = repository.get(verified["snapshot_id"])
    assert snapshot is not None
    assert snapshot["source_id"] == source_id
    assert snapshot["revision"] == revision
    return verified["snapshot_id"]


def _extract(engine, snapshot_id: str, summary: str, candidate_name: str, storage_root: Path):
    return ingest_selected_file_extraction(
        engine,
        {
            "proposal_version": "1.0",
            "snapshot_id": snapshot_id,
            "findings": [
                {
                    "summary": summary,
                    "candidate_names": [candidate_name],
                    "anchors": [{"path": "README.md", "line_start": 2, "line_end": 2}],
                }
            ],
        },
        storage_root=storage_root,
        actor=EXTRACTOR_AI,
    )


def test_two_sources_join_one_candidate_before_support_and_validation(tmp_path: Path) -> None:
    assert DSN is not None
    connection = psycopg.connect(DSN, autocommit=True)
    try:
        apply_migrations(connection)
        _truncate(connection)
        repository = ObservationTriagePostgresRepository(connection)
        engine = CurationEngine(repository)

        # Discovery keeps provider identity and metadata, but does not rank truth by popularity.
        with repository.connection.transaction():
            discovery = ingest_discovery_intake(
                engine,
                build_metadata_discovery_batch(
                    _search_payload(),
                    query="incremental analysis",
                    discovered_by=DISCOVERY_TOOL,
                    discovered_at="2026-09-10T00:00:00Z",
                ),
                actor=DISCOVERY_TOOL,
            )
        assert discovery["counts"] == {"source": 2}
        assert set(discovery["stored_ids"]) == {SOURCE_A, SOURCE_B}
        assert repository.get(SOURCE_A)["origin"]["stargazers_count"] == 7
        assert repository.get(SOURCE_B)["origin"]["stargazers_count"] == 900000

        snapshot_a = _acquire(
            repository,
            source_id=SOURCE_A,
            revision=REVISION_A,
            content=README_A,
            suffix="a",
            license_expression="MIT",
            storage_root=tmp_path,
        )
        snapshot_b = _acquire(
            repository,
            source_id=SOURCE_B,
            revision=REVISION_B,
            content=README_B,
            suffix="b",
            license_expression="Apache-2.0",
            storage_root=tmp_path,
        )
        assert snapshot_a != snapshot_b

        extracted_a = _extract(
            engine,
            snapshot_a,
            "The first repository states that incremental recomputation avoids unchanged work.",
            "incremental recomputation",
            tmp_path,
        )
        extracted_b = _extract(
            engine,
            snapshot_b,
            "The second repository states that incremental processing reuses unaffected results.",
            "incremental processing",
            tmp_path,
        )
        evidence_a = extracted_a["evidence_ids"][0]
        evidence_b = extracted_b["evidence_ids"][0]
        observation_a = extracted_a["observation_ids"][0]
        observation_b = extracted_b["observation_ids"][0]
        assert repository.get(evidence_a)["source_id"] == SOURCE_A
        assert repository.get(evidence_b)["source_id"] == SOURCE_B

        for observation_id, suffix in ((observation_a, "a"), (observation_b, "b")):
            transition_observation(
                repository,
                observation_id,
                "MARK_TRIAGED",
                reason="Exact committed Evidence is ready for human cross-source review.",
                actor=TRIAGE_TOOL,
                decision_id=f"otd:cross-source:triage:{suffix}",
            )

        engine.create_entity(
            {
                "record_type": "knowledge_entity",
                "id": ENTITY_ID,
                "canonical_name": "Incremental recomputation",
                "aliases": ["incremental processing"],
                "kinds": ["technique"],
                "abstraction_level": "L1",
                "identity_state": "CANONICAL",
                "relations": [],
            },
            actor=HUMAN,
            reason="Human identifies one canonical technique shared by the two observations.",
        )

        promoted = transition_observation(
            repository,
            observation_a,
            "PROMOTE_TO_CLAIM_CANDIDATE",
            reason="Human starts a Candidate from the first independently acquired Source.",
            actor=HUMAN,
            claim_candidate={
                "id": CLAIM_ID,
                "entity_id": ENTITY_ID,
                "claim_type": "DIRECT_OBSERVATION",
                "statement": (
                    "Incremental techniques can avoid recomputing unchanged work by reusing "
                    "unaffected results."
                ),
            },
            decision_id="otd:cross-source:promote:a",
        )
        assert promoted["claim_candidate"]["evidence_ids"] == [evidence_a]

        # AI may propose Evidence but cannot consume a TRIAGED Observation into canonical review state.
        with pytest.raises(ObservationCandidateAttachmentError, match="human actor"):
            attach_observation_to_candidate_claim(
                repository,
                observation_b,
                CLAIM_ID,
                actor=AI,
                reason="AI must not be allowed to attach cross-source Evidence.",
                decision_id="otd:cross-source:forbidden-ai",
            )
        assert repository.get(observation_b)["status"] == "TRIAGED"
        assert repository.get(CLAIM_ID)["evidence_ids"] == [evidence_a]

        attached = attach_observation_to_candidate_claim(
            repository,
            observation_b,
            CLAIM_ID,
            actor=HUMAN,
            reason=(
                "Human confirms the second Observation addresses the same Candidate and attaches "
                "its immutable Evidence before review."
            ),
            decision_id="otd:cross-source:promote:b",
        )
        assert attached["added_evidence_ids"] == [evidence_b]
        assert attached["observation"]["status"] == "PROMOTED"
        assert attached["decision"]["action"] == "PROMOTE_TO_CLAIM_CANDIDATE"
        assert attached["decision"]["resulting_claim_id"] == CLAIM_ID
        assert attached["claim_candidate"]["maturity"] == "CANDIDATE"
        assert attached["claim_candidate"]["evidence_ids"] == sorted([evidence_a, evidence_b])
        assert len(repository.list("claim")) == 1

        supported = engine.transition_claim(
            CLAIM_ID,
            "SUPPORTED",
            actor=HUMAN,
            reason="Human reviews both pinned Evidence chains before supporting the Claim.",
            support_review={
                "independence_assessment": "HUMAN_REVIEWED",
                "independence_note": (
                    "Reviewed as two separately discovered GitHub repository identities with "
                    "different pinned revisions and immutable SourceSnapshots."
                ),
                "decision_id": "csd:cross-source:two-source-support",
            },
        )
        assert supported["maturity"] == "SUPPORTED"

        support_history = claim_support_history(repository, claim_id=CLAIM_ID)
        assert len(support_history) == 1
        support = support_history[0]
        assert support["evidence_ids"] == sorted([evidence_a, evidence_b])
        assert support["distinct_source_ids"] == sorted([SOURCE_A, SOURCE_B])
        assert support["distinct_snapshot_ids"] == sorted([snapshot_a, snapshot_b])
        assert support["independence_assessment"] == "HUMAN_REVIEWED"

        # Once reviewed, the exact two-Source Evidence set is frozen under the existing contract.
        tampered = repository.get(CLAIM_ID)
        tampered["evidence_ids"] = [evidence_a]
        with pytest.raises(psycopg.Error, match="Evidence set differs from latest support decision"):
            repository.put(tampered, replace=True)
        assert repository.get(CLAIM_ID)["evidence_ids"] == sorted([evidence_a, evidence_b])

        validated = engine.transition_claim(
            CLAIM_ID,
            "VALIDATED",
            actor=HUMAN,
            reason="Human validates the narrow cross-source Claim against both pinned lines.",
            validation_review={
                "validation_basis": "EVIDENCE_REVIEW",
                "validation_note": (
                    "Reviewed both immutable line locators and their distinct SourceSnapshot chains."
                ),
                "independence_assessment": "HUMAN_REVIEWED",
                "independence_note": (
                    "The two repository identities, revisions, and acquisition chains were "
                    "reviewed separately; no automatic independence inference is claimed."
                ),
                "decision_id": "cvd:cross-source:two-source-validation",
            },
        )
        assert validated["maturity"] == "VALIDATED"

        validation_history = claim_validation_history(repository, claim_id=CLAIM_ID)
        assert len(validation_history) == 1
        validation = validation_history[0]
        assert validation["support_decision_id"] == support["id"]
        assert validation["evidence_ids"] == sorted([evidence_a, evidence_b])
        assert validation["distinct_source_ids"] == sorted([SOURCE_A, SOURCE_B])
        assert validation["distinct_snapshot_ids"] == sorted([snapshot_a, snapshot_b])
        assert validation["independence_assessment"] == "HUMAN_REVIEWED"

        explanation = explain_claim(repository, CLAIM_ID)
        assert explanation["claim"]["maturity"] == "VALIDATED"
        assert explanation["evidence_count"] == 2
        assert {chain["source"]["id"] for chain in explanation["evidence_chains"]} == {
            SOURCE_A,
            SOURCE_B,
        }
        assert {
            chain["source_snapshot"]["id"] for chain in explanation["evidence_chains"]
        } == {snapshot_a, snapshot_b}
    finally:
        connection.close()
