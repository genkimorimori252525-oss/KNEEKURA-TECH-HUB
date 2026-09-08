import pytest

from kneekura_tech_hub.bundle import BundleValidationError, ingest_bundle, preflight_bundle
from kneekura_tech_hub.repository import MemoryRepository
from kneekura_tech_hub.service import CurationEngine


HUMAN = {"actor_type": "human", "actor_id": "prototype-reviewer"}


def records() -> list[dict]:
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
        "created_by": HUMAN,
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


def test_cyclic_entity_dependencies_are_rejected():
    source = records()[-1]
    a = {
        "record_type": "knowledge_entity",
        "id": "ke:a",
        "canonical_name": "A",
        "aliases": [],
        "kinds": ["technique"],
        "abstraction_level": "L1",
        "identity_state": "CANONICAL",
        "relations": [{"type": "related_to", "target": "ke:b"}],
    }
    b = {
        "record_type": "knowledge_entity",
        "id": "ke:b",
        "canonical_name": "B",
        "aliases": [],
        "kinds": ["technique"],
        "abstraction_level": "L1",
        "identity_state": "CANONICAL",
        "relations": [{"type": "related_to", "target": "ke:a"}],
    }

    with pytest.raises(BundleValidationError, match="cyclic record dependencies"):
        preflight_bundle(bundle([source, a, b]))
