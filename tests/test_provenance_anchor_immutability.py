from __future__ import annotations

import os

import psycopg
import pytest

from kneekura_tech_hub.database import apply_migrations
from kneekura_tech_hub.postgres_repository import PostgresRepository
from kneekura_tech_hub.repository import MemoryRepository
from kneekura_tech_hub.service import CurationEngine


DSN = os.getenv("KTHUB_TEST_DATABASE_URL")
HUMAN = {"actor_type": "human", "actor_id": "provenance-curator"}
SOURCE_ID = "src:immutability:provenance"
SNAPSHOT_ID = "ss:immutability:provenance"
EVIDENCE_ID = "ev:immutability:provenance"


def _records() -> tuple[dict, dict, dict]:
    source = {
        "record_type": "source",
        "id": SOURCE_ID,
        "kind": "repository",
        "origin": {"provider": "fixture", "repository": "example/provenance"},
        "acquisition": {"level": "selected-files"},
        "license": {"state": "KNOWN", "declared_expression": "MIT"},
    }
    snapshot = {
        "record_type": "source_snapshot",
        "id": SNAPSHOT_ID,
        "source_id": SOURCE_ID,
        "revision": "0123456789abcdef0123456789abcdef01234567",
        "content_hash": "sha256:" + "a" * 64,
        "captured_at": "2026-09-09T00:00:00Z",
        "metadata": {"fixture": True},
    }
    evidence = {
        "record_type": "evidence",
        "id": EVIDENCE_ID,
        "source_id": SOURCE_ID,
        "source_snapshot_id": SNAPSHOT_ID,
        "locator": {
            "type": "source_lines",
            "path": "README.md",
            "line_start": 1,
            "line_end": 2,
            "content_hash": "sha256:" + "b" * 64,
        },
        "roles": ["SUPPORTS"],
        "observed_at": "2026-09-09T00:00:01Z",
    }
    return source, snapshot, evidence


def _seed(repository) -> None:
    source, snapshot, evidence = _records()
    engine = CurationEngine(repository)
    engine.register_source(source, actor=HUMAN)
    engine.register_source_snapshot(snapshot, actor=HUMAN)
    engine.register_evidence(evidence, actor=HUMAN)


def test_memory_snapshot_and_evidence_are_immutable_but_source_remains_mutable() -> None:
    repository = MemoryRepository()
    _seed(repository)
    before_snapshot = repository.get(SNAPSHOT_ID)
    before_evidence = repository.get(EVIDENCE_ID)

    snapshot = repository.get(SNAPSHOT_ID)
    assert snapshot is not None
    snapshot["revision"] = "f" * 40
    with pytest.raises(ValueError, match="source_snapshot is immutable"):
        repository.put(snapshot, replace=True)

    evidence = repository.get(EVIDENCE_ID)
    assert evidence is not None
    evidence["roles"] = ["REFUTES"]
    with pytest.raises(ValueError, match="evidence is immutable"):
        repository.put(evidence, replace=True)

    source = repository.get(SOURCE_ID)
    assert source is not None
    source["license"] = {"state": "REVIEW_REQUIRED", "declared_expression": "MIT"}
    repository.put(source, replace=True)

    assert repository.get(SNAPSHOT_ID) == before_snapshot
    assert repository.get(EVIDENCE_ID) == before_evidence
    assert repository.get(SOURCE_ID)["license"]["state"] == "REVIEW_REQUIRED"


@pytest.mark.skipif(not DSN, reason="KTHUB_TEST_DATABASE_URL is not set")
def test_postgres_rejects_repository_and_direct_sql_anchor_mutation() -> None:
    assert DSN is not None
    with psycopg.connect(DSN, autocommit=True) as setup:
        apply_migrations(setup)
        setup.execute("TRUNCATE TABLE source, knowledge_entity RESTART IDENTITY CASCADE")

    repository = PostgresRepository.connect(DSN)
    try:
        _seed(repository)
        before_snapshot = repository.get(SNAPSHOT_ID)
        before_evidence = repository.get(EVIDENCE_ID)

        snapshot = repository.get(SNAPSHOT_ID)
        assert snapshot is not None
        snapshot["revision"] = "f" * 40
        with pytest.raises(psycopg.Error, match="source_snapshot is immutable"):
            repository.put(snapshot, replace=True)

        evidence = repository.get(EVIDENCE_ID)
        assert evidence is not None
        evidence["roles"] = ["REFUTES"]
        with pytest.raises(psycopg.Error, match="evidence is immutable"):
            repository.put(evidence, replace=True)

        with pytest.raises(psycopg.Error, match="source_snapshot is immutable"):
            repository.connection.execute(
                "UPDATE source_snapshot SET revision=%s WHERE id=%s",
                ("e" * 40, SNAPSHOT_ID),
            )
        with pytest.raises(psycopg.Error, match="evidence is immutable"):
            repository.connection.execute(
                "UPDATE evidence SET roles=%s WHERE id=%s",
                (["REFUTES"], EVIDENCE_ID),
            )
        with pytest.raises(psycopg.Error, match="evidence is immutable"):
            repository.connection.execute("DELETE FROM evidence WHERE id=%s", (EVIDENCE_ID,))
        with pytest.raises(psycopg.Error, match="source_snapshot is immutable"):
            repository.connection.execute(
                "DELETE FROM source_snapshot WHERE id=%s",
                (SNAPSHOT_ID,),
            )

        source = repository.get(SOURCE_ID)
        assert source is not None
        source["license"] = {"state": "REVIEW_REQUIRED", "declared_expression": "MIT"}
        repository.put(source, replace=True)

        assert repository.get(SNAPSHOT_ID) == before_snapshot
        assert repository.get(EVIDENCE_ID) == before_evidence
        assert repository.get(SOURCE_ID)["license"]["state"] == "REVIEW_REQUIRED"
    finally:
        repository.close()
