from __future__ import annotations

import os
from copy import deepcopy

import psycopg
import pytest

from kneekura_tech_hub.database import apply_migrations
from kneekura_tech_hub.postgres_repository import PostgresRepository
from kneekura_tech_hub.repository import MemoryRepository
from kneekura_tech_hub.service import CurationEngine


DSN = os.getenv("KTHUB_TEST_DATABASE_URL")
HUMAN = {"actor_type": "human", "actor_id": "audit-reviewer"}


def _source(source_id: str) -> dict:
    return {
        "record_type": "source",
        "id": source_id,
        "kind": "repository",
        "origin": {"provider": "fixture", "repository": f"example/{source_id}"},
        "acquisition": {"level": "metadata-only"},
        "license": {"state": "KNOWN", "declared_expression": "MIT"},
    }


def test_memory_curation_event_is_append_only() -> None:
    repository = MemoryRepository()
    engine = CurationEngine(repository)
    engine.register_source(_source("src:audit:memory"), actor=HUMAN)

    events = repository.list("curation_event")
    assert len(events) == 1
    original = deepcopy(events[0])
    tampered = deepcopy(original)
    tampered["reason"] = "rewritten audit history"

    with pytest.raises(ValueError, match="curation_event is immutable"):
        repository.put(tampered, replace=True)

    assert repository.get(original["id"]) == original

    engine.register_source(_source("src:audit:memory:second"), actor=HUMAN)
    assert len(repository.list("curation_event")) == 2


@pytest.mark.skipif(not DSN, reason="KTHUB_TEST_DATABASE_URL is not set")
def test_postgres_curation_event_rejects_repository_and_direct_sql_mutation() -> None:
    assert DSN is not None
    with psycopg.connect(DSN, autocommit=True) as setup:
        apply_migrations(setup)
        setup.execute("TRUNCATE TABLE curation_event, source RESTART IDENTITY CASCADE")

    repository = PostgresRepository.connect(DSN)
    try:
        engine = CurationEngine(repository)
        engine.register_source(_source("src:audit:postgres"), actor=HUMAN)
        original = repository.list("curation_event")[0]

        tampered = deepcopy(original)
        tampered["reason"] = "rewritten through repository"
        with pytest.raises(ValueError, match="append-only"):
            repository.put(tampered, replace=True)

        with pytest.raises(psycopg.Error, match="append-only"):
            repository.connection.execute(
                "UPDATE curation_event SET reason='rewritten through sql' WHERE id=%s",
                (original["id"],),
            )
        with pytest.raises(psycopg.Error, match="append-only"):
            repository.connection.execute(
                "DELETE FROM curation_event WHERE id=%s",
                (original["id"],),
            )

        assert repository.get(original["id"]) == original

        engine.register_source(_source("src:audit:postgres:second"), actor=HUMAN)
        assert len(repository.list("curation_event")) == 2
    finally:
        repository.close()
