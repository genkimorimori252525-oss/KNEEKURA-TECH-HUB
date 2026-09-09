from __future__ import annotations

import os

import psycopg
import pytest

from kneekura_tech_hub.database import apply_migrations
from kneekura_tech_hub.postgres_repository import PostgresRepository
from kneekura_tech_hub.repository import MemoryRepository
from kneekura_tech_hub.service import CurationEngine


DSN = os.getenv("KTHUB_TEST_DATABASE_URL")
HUMAN = {"actor_type": "human", "actor_id": "entity-curator"}
ENTITY_A = "ke:identity:a"
ENTITY_B = "ke:identity:b"


def _entity(entity_id: str, name: str, *, aliases: list[str] | None = None) -> dict:
    return {
        "record_type": "knowledge_entity",
        "id": entity_id,
        "canonical_name": name,
        "aliases": aliases or [],
        "kinds": ["technique"],
        "abstraction_level": "L1",
        "identity_state": "CANONICAL",
        "relations": [],
    }


def _seed(repository) -> CurationEngine:
    engine = CurationEngine(repository)
    engine.create_entity(_entity(ENTITY_A, "Incremental Computation", aliases=["Incremental"]), actor=HUMAN)
    engine.create_entity(_entity(ENTITY_B, "Incremental Recalculation", aliases=["Recalculation"]), actor=HUMAN)
    return engine


def test_memory_rejects_entity_concept_rewrite_but_allows_governed_merge() -> None:
    repository = MemoryRepository()
    engine = _seed(repository)
    original = repository.get(ENTITY_B)
    assert original is not None

    renamed = dict(original)
    renamed["canonical_name"] = "Different Concept"
    with pytest.raises(ValueError, match="concept payload is immutable"):
        repository.put(renamed, replace=True)

    rekinded = dict(original)
    rekinded["kinds"] = ["problem"]
    with pytest.raises(ValueError, match="concept payload is immutable"):
        repository.put(rekinded, replace=True)

    reabstracted = dict(original)
    reabstracted["abstraction_level"] = "L4"
    with pytest.raises(ValueError, match="concept payload is immutable"):
        repository.put(reabstracted, replace=True)

    realiased = dict(original)
    realiased["aliases"] = ["Recalculation", "Different Alias"]
    with pytest.raises(ValueError, match="concept payload is immutable"):
        repository.put(realiased, replace=True)

    invalid_state = dict(original)
    invalid_state["identity_state"] = "RETIRED"
    with pytest.raises(ValueError, match="invalid knowledge_entity identity transition"):
        repository.put(invalid_state, replace=True)

    _, merged = engine.merge_entities(ENTITY_A, ENTITY_B, actor=HUMAN, reason="same concept")
    assert merged["identity_state"] == "MERGED"
    assert merged["redirect_to"] == ENTITY_A
    assert merged["canonical_name"] == original["canonical_name"]
    assert merged["aliases"] == original["aliases"]
    assert merged["kinds"] == original["kinds"]
    assert merged["abstraction_level"] == original["abstraction_level"]


@pytest.mark.skipif(not DSN, reason="KTHUB_TEST_DATABASE_URL is not set")
def test_postgres_rejects_entity_identity_rewrite_and_anchor_tampering() -> None:
    assert DSN is not None
    with psycopg.connect(DSN, autocommit=True) as setup:
        apply_migrations(setup)
        setup.execute("TRUNCATE TABLE source, knowledge_entity RESTART IDENTITY CASCADE")

    repository = PostgresRepository.connect(DSN)
    try:
        engine = _seed(repository)
        before = repository.get(ENTITY_B)
        assert before is not None

        renamed = dict(before)
        renamed["canonical_name"] = "Different Concept"
        with pytest.raises(psycopg.Error, match="concept payload is immutable"):
            repository.put(renamed, replace=True)

        with pytest.raises(psycopg.Error, match="concept payload is immutable"):
            repository.connection.execute(
                "UPDATE knowledge_entity SET canonical_name='Different Concept' WHERE id=%s",
                (ENTITY_B,),
            )

        with pytest.raises(psycopg.Error, match="concept payload is immutable"):
            repository.connection.execute(
                "INSERT INTO entity_alias(entity_id, alias) VALUES (%s, 'Injected Alias')",
                (ENTITY_B,),
            )

        with pytest.raises(psycopg.Error, match="concept payload is immutable"):
            repository.connection.execute(
                "DELETE FROM entity_kind WHERE entity_id=%s AND kind='technique'",
                (ENTITY_B,),
            )

        with pytest.raises(psycopg.Error, match="knowledge_entity_identity_anchor is immutable"):
            repository.connection.execute(
                "DELETE FROM knowledge_entity_identity_anchor WHERE entity_id=%s",
                (ENTITY_B,),
            )

        with pytest.raises(psycopg.Error, match="invalid knowledge_entity identity transition"):
            repository.connection.execute(
                "UPDATE knowledge_entity SET identity_state='RETIRED' WHERE id=%s",
                (ENTITY_B,),
            )

        assert repository.get(ENTITY_B) == before

        _, merged = engine.merge_entities(ENTITY_A, ENTITY_B, actor=HUMAN, reason="same concept")
        assert merged["identity_state"] == "MERGED"
        assert merged["redirect_to"] == ENTITY_A
        assert merged["canonical_name"] == before["canonical_name"]
        assert merged["aliases"] == before["aliases"]
        assert merged["kinds"] == before["kinds"]
        assert merged["abstraction_level"] == before["abstraction_level"]

        anchor_payload = repository.connection.execute(
            "SELECT payload FROM knowledge_entity_identity_anchor WHERE entity_id=%s",
            (ENTITY_B,),
        ).fetchone()[0]
        assert anchor_payload["canonical_name"] == before["canonical_name"]
        assert anchor_payload["aliases"] == sorted(before["aliases"])
        assert anchor_payload["kinds"] == sorted(before["kinds"])
    finally:
        repository.close()
