from __future__ import annotations

import json
from hashlib import sha1
import os
from pathlib import Path

import psycopg
import pytest

from kneekura_tech_hub.authorization import (
    AcquisitionAuthorizationEngine,
    AcquisitionAuthorizationError,
)
from kneekura_tech_hub.claim_support import claim_support_history
from kneekura_tech_hub.claim_validation import claim_validation_history
from kneekura_tech_hub.database import apply_migrations
from kneekura_tech_hub.discovery import ingest_discovery_intake
from kneekura_tech_hub.execution import execute_authorized_acquisition
from kneekura_tech_hub.explanation import explain_claim
from kneekura_tech_hub.github_adapter import build_metadata_discovery_batch
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

DISCOVERY_TOOL = {"actor_type": "tool", "actor_id": "acceptance-github-discovery", "version": "v1"}
FETCH_TOOL = {"actor_type": "tool", "actor_id": "acceptance-fetcher", "version": "v1"}
COMMIT_TOOL = {"actor_type": "tool", "actor_id": "acceptance-committer", "version": "v1"}
EXTRACTOR_AI = {"actor_type": "ai", "actor_id": "acceptance-extractor", "version": "v1"}
TRIAGE_TOOL = {"actor_type": "tool", "actor_id": "acceptance-triage", "version": "v1"}
HUMAN = {"actor_type": "human", "actor_id": "acceptance-reviewer"}

SOURCE_ID = "src:github:example:small-but-relevant"
UNSELECTED_SOURCE_ID = "src:github:example:huge-star-repo"
REVISION = "0123456789abcdef0123456789abcdef01234567"
ENTITY_ID = "ke:acceptance:incremental-recomputation"
CLAIM_ID = "cl:acceptance:incremental-recomputation"


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


def test_discovery_to_validated_knowledge_requires_every_governed_boundary(tmp_path: Path) -> None:
    assert DSN is not None
    connection = psycopg.connect(DSN, autocommit=True)
    try:
        apply_migrations(connection)
        _truncate(connection)
        repository = ObservationTriagePostgresRepository(connection)
        engine = CurationEngine(repository)

        # 1. Public GitHub discovery produces metadata-only Sources. Provider order,
        # popularity and Search API license hints do not become quality or license truth.
        batch = build_metadata_discovery_batch(
            _search_payload(),
            query="incremental analysis",
            discovered_by=DISCOVERY_TOOL,
            discovered_at="2026-09-09T06:00:00Z",
        )
        with repository.connection.transaction():
            discovery_result = ingest_discovery_intake(
                engine,
                batch,
                actor=DISCOVERY_TOOL,
            )
        assert discovery_result["counts"] == {"source": 2}
        assert set(discovery_result["stored_ids"]) == {SOURCE_ID, UNSELECTED_SOURCE_ID}
        assert discovery_result["canonical_knowledge_writes"] == 0
        source = repository.get(SOURCE_ID)
        assert source is not None
        assert source["acquisition"] == {"level": "metadata-only"}
        assert source["license"]["state"] == "REVIEW_REQUIRED"
        assert source["origin"]["github_license_hint"]["spdx_id"] == "MIT"
        assert repository.get(UNSELECTED_SOURCE_ID)["origin"]["stargazers_count"] == 900000

        # 2. Human selection alone is not acquisition authority. The adapter's
        # license hint is intentionally insufficient for authorization.
        selection = SourceSelectionEngine(repository).create_from_fields(
            source_id=SOURCE_ID,
            decision="SELECT_FOR_REVIEW",
            rationale="This low-star repository is directly relevant to the research question.",
            actor=HUMAN,
            decision_id="sd:acceptance:small-but-relevant",
        )
        with pytest.raises(AcquisitionAuthorizationError, match="license"):
            AcquisitionAuthorizationEngine(repository).authorize_from_fields(
                source_id=SOURCE_ID,
                selection_decision_id=selection["id"],
                revision=REVISION,
                allowed_paths=["README.md"],
                rationale="This must fail until license review is resolved.",
                actor=HUMAN,
                authorization_id="aa:acceptance:premature",
            )
        assert repository.list("source_acquisition_authorization") == []

        # 3. A human review resolves the license metadata without changing Source
        # identity. License state is deliberately mutable under Source Identity Integrity.
        reviewed_source = repository.get(SOURCE_ID)
        assert reviewed_source is not None
        reviewed_source["license"] = {
            "state": "KNOWN",
            "declared_expression": "MIT",
            "handling_policy": "REFERENCE_ONLY",
        }
        repository.put(reviewed_source, replace=True)

        authorization = AcquisitionAuthorizationEngine(repository).authorize_from_fields(
            source_id=SOURCE_ID,
            selection_decision_id=selection["id"],
            revision=REVISION,
            allowed_paths=["README.md"],
            rationale="Human review permits only the pinned README at the pinned revision.",
            actor=HUMAN,
            authorization_id="aa:acceptance:readme",
        )
        assert repository.get(SOURCE_ID)["acquisition"] == {"level": "metadata-only"}

        # 4. Authorized execution fetches only the exact allowed file. Execution
        # success still does not create a canonical SourceSnapshot.
        readme = b"# Incremental engine\nIncremental recomputation avoids unchanged work.\n"

        def fetch_file(_source, revision, path):
            assert _source["id"] == SOURCE_ID
            assert revision == REVISION
            assert path == "README.md"
            return {"content": readme, "git_blob_sha": _blob_sha(readme)}

        execution = execute_authorized_acquisition(
            repository,
            authorization["id"],
            storage_root=tmp_path,
            fetch_file=fetch_file,
            actor=FETCH_TOOL,
            execution_id="ax:acceptance:readme",
        )
        assert execution["status"] == "SUCCEEDED"
        assert repository.list("source_snapshot") == []
        assert repository.get(SOURCE_ID)["acquisition"] == {"level": "metadata-only"}

        # 5. Verified Commit re-hashes the stored bytes and is the only step that
        # promotes acquisition state and creates the immutable SourceSnapshot.
        verified_commit = commit_verified_acquisition(
            repository,
            execution["id"],
            storage_root=tmp_path,
            actor=COMMIT_TOOL,
            commit_id="vc:acceptance:readme",
        )
        snapshot_id = verified_commit["snapshot_id"]
        assert repository.get(SOURCE_ID)["acquisition"] == {"level": "selected-files"}
        snapshot = repository.get(snapshot_id)
        assert snapshot is not None
        assert snapshot["source_id"] == SOURCE_ID
        assert snapshot["revision"] == REVISION

        # 6. Untrusted AI proposes meaning, but Hub-controlled extraction creates
        # exact Evidence and NEW StagedObservation from committed bytes only.
        proposal = {
            "proposal_version": "1.0",
            "snapshot_id": snapshot_id,
            "findings": [
                {
                    "summary": "The README states that incremental recomputation avoids unchanged work.",
                    "candidate_names": ["incremental recomputation"],
                    "anchors": [
                        {"path": "README.md", "line_start": 2, "line_end": 2}
                    ],
                }
            ],
        }
        extracted = ingest_selected_file_extraction(
            engine,
            proposal,
            storage_root=tmp_path,
            actor=EXTRACTOR_AI,
        )
        assert extracted["new_evidence_count"] == 1
        assert extracted["new_observation_count"] == 1
        assert repository.list("claim") == []
        observation_id = extracted["observation_ids"][0]
        evidence_id = extracted["evidence_ids"][0]
        observation = repository.get(observation_id)
        assert observation is not None
        assert observation["status"] == "NEW"
        assert observation["created_by"] == EXTRACTOR_AI
        assert observation["evidence_candidate_ids"] == [evidence_id]

        # 7. Tool triage may perform the bounded mechanical NEW -> TRIAGED step,
        # but only a human can create the canonical entity and promote to Claim Candidate.
        transition_observation(
            repository,
            observation_id,
            "MARK_TRIAGED",
            reason="Exact Evidence and candidate naming are ready for human review.",
            actor=TRIAGE_TOOL,
            decision_id="otd:acceptance:triage",
        )
        engine.create_entity(
            {
                "record_type": "knowledge_entity",
                "id": ENTITY_ID,
                "canonical_name": "Incremental recomputation",
                "aliases": [],
                "kinds": ["technique"],
                "abstraction_level": "L1",
                "identity_state": "CANONICAL",
                "relations": [],
            },
            actor=HUMAN,
            reason="Human creates the canonical concept targeted by this extraction.",
        )
        promoted = transition_observation(
            repository,
            observation_id,
            "PROMOTE_TO_CLAIM_CANDIDATE",
            reason="Human accepts the exact extraction as a Claim Candidate only.",
            actor=HUMAN,
            claim_candidate={
                "id": CLAIM_ID,
                "entity_id": ENTITY_ID,
                "claim_type": "DIRECT_OBSERVATION",
                "statement": "The pinned README states that incremental recomputation avoids unchanged work.",
            },
            decision_id="otd:acceptance:promote",
        )
        claim = promoted["claim_candidate"]
        assert claim is not None
        assert claim["maturity"] == "CANDIDATE"
        assert claim["evidence_ids"] == [evidence_id]
        assert claim["created_by"] == HUMAN

        # 8. Candidate does not become trusted merely because the pipeline reached
        # it. Human Support and Validation decisions remain distinct gates.
        supported = engine.transition_claim(
            CLAIM_ID,
            "SUPPORTED",
            actor=HUMAN,
            reason="Human reviewed the pinned Evidence supporting this narrow statement.",
        )
        assert supported["maturity"] == "SUPPORTED"
        assert len(claim_support_history(repository, claim_id=CLAIM_ID)) == 1

        validated = engine.transition_claim(
            CLAIM_ID,
            "VALIDATED",
            actor=HUMAN,
            reason="Human verifies this narrow source-description claim against the pinned line.",
            validation_review={
                "validation_basis": "EVIDENCE_REVIEW",
                "validation_note": (
                    "Reviewed the immutable Evidence locator and pinned README line; "
                    "no claim of independent corroboration is made."
                ),
                "independence_assessment": "NOT_ASSESSED",
            },
        )
        assert validated["maturity"] == "VALIDATED"
        assert len(claim_validation_history(repository, claim_id=CLAIM_ID)) == 1

        # 9. The final reviewed Claim still reconstructs all the way back to the
        # exact discovered Source and immutable Snapshot; popularity never enters the chain.
        explanation = explain_claim(repository, CLAIM_ID)
        assert explanation["claim"]["maturity"] == "VALIDATED"
        assert explanation["evidence_count"] == 1
        chain = explanation["evidence_chains"][0]
        assert chain["evidence"]["id"] == evidence_id
        assert chain["source_snapshot"]["id"] == snapshot_id
        assert chain["source_snapshot"]["revision"] == REVISION
        assert chain["source"]["id"] == SOURCE_ID
        assert chain["source"]["origin"]["stargazers_count"] == 7
        assert repository.get(UNSELECTED_SOURCE_ID)["acquisition"] == {"level": "metadata-only"}
    finally:
        connection.close()
