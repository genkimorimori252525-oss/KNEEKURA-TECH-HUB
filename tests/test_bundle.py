import pytest

from kneekura_tech_hub.bundle import BundleValidationError, ingest_bundle, preflight_bundle
from kneekura_tech_hub.repository import MemoryRepository
from kneekura_tech_hub.service import CurationEngine


HUMAN = {"actor_type": "human", "actor_id": "prototype-reviewer"}
AI = {"actor_type": "ai", "actor_id": "prototype-extractor", "version": "test"}


def records(*, claim_actor: dict | None = None) -> list[dict]:
    source = {
        "record_type": "source",
        "id": "src:bundle",
        "kind": "repository",
        "origin": {"provider": "github", "repository": "example/bundle"},
        "acquisition": {"level": "snapshot"},
        "license": {"state": "KNOWN", "declared_expression": "MIT"},
    }
    snapshot = {
        "record_type": "source_snapshot",
        "id": "ss:bundle",
        "source_id": "src:bundle",
        "revision": "0123456789abcdef",
        "captured_at": "2026-09-09T00:00:00Z",
    }
    entity = {
        "record_type": "knowledge_entity",
        "id": "ke:bundle",
        "canonical_name": "Incremental Computation",
        "aliases": ["Incremental Recalculation"],
        "kinds": ["technique"],
        "abstraction_level": "L1",
        "identity_state": "CANONICAL",
        "relations": [],
    }
    evidence = {
        "record_type": "evidence",
        "id": "ev:bundle",
        "source_id": "src:bundle",
        "source_snapshot_id": "ss:bundle",
        "locator": {
            "type": "source_lines",
            "path": "src/cache.rs",
            "line_start": 10,
            "line_end": 20,
            "content_hash": "sha256:bundle",
        },
        "roles": ["SUPPORTS"],
    }
    claim = {
        "record_type": "claim",
        "id": "cl:bundle",
        "entity_id": "ke:bundle",
        "claim_type": "DIRECT_OBSERVATION",
        "statement": "The pinned source contains an invalidation path.",
        "maturity": "CANDIDATE",
        "evidence_ids": ["ev:bundle"],
        "created_by": claim_actor or HUMAN,
        "policy_version": "1.0.0",
    }
    return [claim, evidence, entity, snapshot, source]


def bundle(items: list[dict] | None = None) -> dict:
    return {
        "bundle_version": "1.0",
        "bundle_id": "bundle:test",
        "title": "Curated prototype test bundle",
        "domains": ["static-analysis"],
        "records": items or records(),
    }


def test_preflight_returns_dependency_safe_order_without_writes():
    repository = MemoryRepository()
    ordered = preflight_bundle(bundle(), repository=repository)

    ids = [record["id"] for record in ordered]
    assert ids.index("src:bundle") < ids.index("ss:bundle") < ids.index("ev:bundle")
    assert ids.index("ke:bundle") < ids.index("cl:bundle")
    assert ids.index("ev:bundle") < ids.index("cl:bundle")
    assert repository.list() == []


def test_bundle_ingests_through_governed_curation_engine():
    repository = MemoryRepository()
    engine = CurationEngine(repository)

    stored = ingest_bundle(engine, bundle(), actor=HUMAN)

    assert set(stored) == {"src:bundle", "ss:bundle", "ke:bundle", "ev:bundle", "cl:bundle"}
    assert engine.get("cl:bundle")["maturity"] == "CANDIDATE"
    assert len(engine.list("curation_event")) >= 4


def test_ai_created_candidate_claim_keeps_ai_provenance_under_human_review():
    repository = MemoryRepository()
    engine = CurationEngine(repository)
    pilot = bundle(records(claim_actor=AI))

    ingest_bundle(engine, pilot, actor=HUMAN)

    stored = engine.get("cl:bundle")
    assert stored is not None
    assert stored["created_by"] == AI
    claim_events = [
        event for event in engine.list("curation_event") if event["operation"] == "CLAIM_CREATE"
    ]
    assert claim_events[-1]["actor"] == AI


def test_human_created_claim_must_match_bundle_reviewer():
    other_human = {"actor_type": "human", "actor_id": "someone-else"}
    engine = CurationEngine(MemoryRepository())

    with pytest.raises(BundleValidationError, match="must match the bundle reviewer"):
        ingest_bundle(engine, bundle(records(claim_actor=other_human)), actor=HUMAN)


def test_non_human_bundle_reviewer_is_rejected():
    engine = CurationEngine(MemoryRepository())

    with pytest.raises(BundleValidationError, match="reviewer must be a human actor"):
        ingest_bundle(engine, bundle(records(claim_actor=AI)), actor=AI)


def test_duplicate_bundle_ids_are_rejected():
    items = records()
    items.append(dict(items[-1]))

    with pytest.raises(BundleValidationError, match="duplicate bundle record id"):
        preflight_bundle(bundle(items))


def test_missing_reference_is_rejected_before_writes():
    items = records()
    items[1]["source_snapshot_id"] = "ss:missing"

    with pytest.raises(BundleValidationError, match="references missing record"):
        preflight_bundle(bundle(items))


def test_existing_record_cannot_be_redefined():
    repository = MemoryRepository()
    repository.put(records()[-1])

    with pytest.raises(BundleValidationError, match="redefine existing record"):
        preflight_bundle(bundle(), repository=repository)


def test_unproven_entity_relations_are_rejected_during_preflight():
    source = records()[-1]
    parent = {
        "record_type": "knowledge_entity",
        "id": "ke:parent",
        "canonical_name": "Parent",
        "aliases": [],
        "kinds": ["technique"],
        "abstraction_level": "L1",
        "identity_state": "CANONICAL",
        "relations": [],
    }
    child = {
        "record_type": "knowledge_entity",
        "id": "ke:child",
        "canonical_name": "Child",
        "aliases": [],
        "kinds": ["technique"],
        "abstraction_level": "L1",
        "identity_state": "CANONICAL",
        "relations": [{"type": "derived_from", "target": "ke:parent"}],
    }

    with pytest.raises(BundleValidationError, match="relation provenance"):
        preflight_bundle(bundle([source, parent, child]))
