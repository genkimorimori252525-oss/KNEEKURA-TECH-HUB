from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path

import pytest

from kneekura_tech_hub.discovery import (
    DiscoveryIntakeError,
    github_source_id,
    ingest_discovery_intake,
    preflight_discovery_intake,
)
from kneekura_tech_hub.repository import MemoryRepository
from kneekura_tech_hub.service import CurationEngine


ROOT = Path(__file__).resolve().parents[1]
PILOT = ROOT / "pilots" / "controlled-discovery-intake-v1.json"


def _batch() -> dict:
    return json.loads(PILOT.read_text(encoding="utf-8"))


def test_github_source_id_is_deterministic_and_case_normalized():
    assert github_source_id("Salsa-RS/Salsa") == "src:github:salsa-rs:salsa"


def test_preflight_reorders_scrambled_crawler_output_without_writes():
    repository = MemoryRepository()
    before = repository.list()
    ordered = preflight_discovery_intake(_batch(), repository=repository)
    ids = [record["id"] for record in ordered]

    for source_id, snapshot_id, evidence_id, observation_id in [
        (
            "src:github:tree-sitter:tree-sitter",
            "ss:github:tree-sitter:tree-sitter:8351896b",
            "ev:discovery:tree-sitter:readme:incremental-parsing:8351896b",
            "obs:discovery:tree-sitter:incremental-parsing:8351896b",
        ),
        (
            "src:github:salsa-rs:salsa",
            "ss:github:salsa-rs:salsa:e021c01d",
            "ev:discovery:salsa:readme:query-model:e021c01d",
            "obs:discovery:salsa:query-model:e021c01d",
        ),
    ]:
        assert ids.index(source_id) < ids.index(snapshot_id)
        assert ids.index(snapshot_id) < ids.index(evidence_id)
        assert ids.index(evidence_id) < ids.index(observation_id)

    assert repository.list() == before


def test_discovery_intake_cannot_contain_claim_or_other_canonical_record():
    batch = _batch()
    batch["records"].append(
        {
            "record_type": "claim",
            "id": "cl:forbidden",
            "entity_id": "ke:forbidden",
            "claim_type": "JUDGMENT",
            "statement": "Discovery must never write this Claim.",
            "maturity": "CANDIDATE",
            "evidence_ids": [],
            "created_by": batch["discovered_by"],
            "policy_version": "1.0.0",
        }
    )

    with pytest.raises(DiscoveryIntakeError, match="claim"):
        preflight_discovery_intake(batch)


def test_invalid_batch_fails_before_any_write():
    batch = _batch()
    for record in batch["records"]:
        if record["record_type"] == "staged_observation":
            record["status"] = "PROMOTED"
            break

    repository = MemoryRepository()
    before = deepcopy(repository.list())
    with pytest.raises(DiscoveryIntakeError, match="status NEW"):
        ingest_discovery_intake(
            CurationEngine(repository),
            batch,
            actor=batch["discovered_by"],
        )
    assert repository.list() == before


def test_discovery_observation_creator_must_match_batch_actor():
    batch = _batch()
    for record in batch["records"]:
        if record["record_type"] == "staged_observation":
            record["created_by"] = {"actor_type": "ai", "actor_id": "other"}
            break

    with pytest.raises(DiscoveryIntakeError, match="created_by must match discovered_by"):
        preflight_discovery_intake(batch)


def test_acting_identity_must_match_batch_discovery_provenance():
    batch = _batch()
    repository = MemoryRepository()
    with pytest.raises(DiscoveryIntakeError, match="acting identity"):
        ingest_discovery_intake(
            CurationEngine(repository),
            batch,
            actor={"actor_type": "ai", "actor_id": "impersonator"},
        )
    assert repository.list() == []


def test_metadata_only_source_cannot_grow_snapshot_or_evidence():
    batch = _batch()
    for record in batch["records"]:
        if record.get("id") == "src:github:salsa-rs:salsa":
            record["acquisition"] = {"level": "metadata-only"}
            break

    with pytest.raises(DiscoveryIntakeError, match="metadata-only"):
        preflight_discovery_intake(batch)


def test_unknown_license_metadata_only_source_can_be_discovered_without_code():
    batch = {
        "intake_version": "1.0",
        "batch_id": "discovery:unknown-license",
        "discovered_by": {"actor_type": "tool", "actor_id": "github-search"},
        "discovered_at": "2026-09-09T00:00:00Z",
        "scope": {"provider": "github", "query": "candidate"},
        "records": [
            {
                "record_type": "source",
                "id": "src:github:example:unknown-license",
                "kind": "repository",
                "origin": {
                    "provider": "github",
                    "repository": "example/unknown-license"
                },
                "acquisition": {"level": "metadata-only"},
                "license": {"state": "UNKNOWN", "handling_policy": "REFERENCE_ONLY"}
            }
        ]
    }

    ordered = preflight_discovery_intake(batch)
    assert [record["id"] for record in ordered] == ["src:github:example:unknown-license"]


def test_non_deterministic_github_source_id_is_rejected():
    batch = _batch()
    for record in batch["records"]:
        if record.get("id") == "src:github:salsa-rs:salsa":
            record["id"] = "src:github:duplicate-name"
            break

    with pytest.raises(DiscoveryIntakeError, match="deterministic"):
        preflight_discovery_intake(batch)


def test_ingestion_writes_only_provenance_and_staging_records():
    batch = _batch()
    repository = MemoryRepository()
    receipt = ingest_discovery_intake(
        CurationEngine(repository),
        batch,
        actor=batch["discovered_by"],
    )

    assert receipt["canonical_knowledge_writes"] == 0
    assert receipt["counts"] == {
        "evidence": 2,
        "source": 2,
        "source_snapshot": 2,
        "staged_observation": 2,
    }
    assert len(repository.list("source")) == 2
    assert len(repository.list("source_snapshot")) == 2
    assert len(repository.list("evidence")) == 2
    assert len(repository.list("staged_observation")) == 2
    assert repository.list("knowledge_entity") == []
    assert repository.list("claim") == []
    assert repository.list("review_decision") == []

    # SOURCE_ACQUIRE events are provenance side effects from the existing CurationEngine.
    assert all(
        event["operation"] == "SOURCE_ACQUIRE"
        for event in repository.list("curation_event")
    )
