from __future__ import annotations

from copy import deepcopy
import os

import psycopg
import pytest

from kneekura_tech_hub.database import apply_migrations
from kneekura_tech_hub.postgres_repository import PostgresRepository
from kneekura_tech_hub.repository import MemoryRepository
from kneekura_tech_hub.service import CurationEngine


DSN = os.getenv("KTHUB_TEST_DATABASE_URL")
HUMAN = {"actor_type": "human", "actor_id": "source-curator"}
SOURCE_ID = "src:github:example:identity"


def _source() -> dict:
    return {
        "record_type": "source",
        "id": SOURCE_ID,
        "kind": "repository",
        "origin": {
            "provider": "github",
            "repository": "example/identity",
            "url": "https://github.com/example/identity",
            "github_repository_id": 123456,
            "node_id": "R_example_identity",
            "default_branch": "main",
            "description": "Initial description",
            "language": "Python",
            "visibility": "public",
            "stargazers_count": 10,
            "forks_count": 2,
            "open_issues_count": 1,
            "pushed_at": "2026-09-09T00:00:00Z",
            "updated_at": "2026-09-09T00:00:00Z",
            "topics": ["incremental"],
            "github_license_hint": {"spdx_id": "MIT"},
            "discovery_hits": [{"query_id": "query:first", "page": 1}],
        },
        "acquisition": {"level": "metadata-only"},
        "license": {
            "state": "REVIEW_REQUIRED",
            "declared_expression": None,
            "handling_policy": "DISCOVERY_METADATA_ONLY",
        },
    }


def _seed(repository) -> None:
    CurationEngine(repository).register_source(_source(), actor=HUMAN)


def _volatile_update(source: dict) -> dict:
    updated = deepcopy(source)
    updated["origin"].update(
        {
            "default_branch": "trunk",
            "description": "Fresh description",
            "language": "Rust",
            "visibility": "public",
            "stargazers_count": 999,
            "forks_count": 42,
            "open_issues_count": 9,
            "pushed_at": "2026-09-10T00:00:00Z",
            "updated_at": "2026-09-10T00:00:00Z",
            "topics": ["incremental", "parser"],
            "github_license_hint": {"spdx_id": "Apache-2.0"},
            "discovery_hits": [
                {"query_id": "query:first", "page": 1},
                {"query_id": "query:second", "page": 2},
            ],
        }
    )
    return updated


def test_memory_source_identity_is_stable_but_metadata_and_governed_state_are_mutable() -> None:
    repository = MemoryRepository()
    _seed(repository)
    original = repository.get(SOURCE_ID)
    assert original is not None

    changed_kind = deepcopy(original)
    changed_kind["kind"] = "blog"
    with pytest.raises(ValueError, match="source identity is immutable"):
        repository.put(changed_kind, replace=True)

    changed_repository = deepcopy(original)
    changed_repository["origin"]["repository"] = "other/repository"
    with pytest.raises(ValueError, match="source identity is immutable"):
        repository.put(changed_repository, replace=True)

    changed_url = deepcopy(original)
    changed_url["origin"]["url"] = "https://github.com/other/repository"
    with pytest.raises(ValueError, match="source identity is immutable"):
        repository.put(changed_url, replace=True)

    changed_provider_id = deepcopy(original)
    changed_provider_id["origin"]["github_repository_id"] = 654321
    with pytest.raises(ValueError, match="source identity is immutable"):
        repository.put(changed_provider_id, replace=True)

    volatile = _volatile_update(original)
    repository.put(volatile, replace=True)

    mutable = repository.get(SOURCE_ID)
    assert mutable is not None
    mutable["license"] = {"state": "KNOWN", "declared_expression": "MIT"}
    mutable["acquisition"] = {"level": "selected-files"}
    repository.put(mutable, replace=True)

    final = repository.get(SOURCE_ID)
    assert final is not None
    assert final["origin"]["repository"] == "example/identity"
    assert final["origin"]["stargazers_count"] == 999
    assert final["origin"]["default_branch"] == "trunk"
    assert final["license"]["state"] == "KNOWN"
    assert final["acquisition"] == {"level": "selected-files"}


@pytest.mark.skipif(not DSN, reason="KTHUB_TEST_DATABASE_URL is not set")
def test_postgres_source_identity_rejects_stable_repointing_but_allows_volatile_updates() -> None:
    assert DSN is not None
    with psycopg.connect(DSN, autocommit=True) as setup:
        apply_migrations(setup)
        setup.execute("TRUNCATE TABLE source, knowledge_entity RESTART IDENTITY CASCADE")

    repository = PostgresRepository.connect(DSN)
    try:
        _seed(repository)
        original = repository.get(SOURCE_ID)
        assert original is not None

        changed = deepcopy(original)
        changed["origin"]["repository"] = "other/repository"
        with pytest.raises(psycopg.Error, match="source identity is immutable"):
            repository.put(changed, replace=True)

        with pytest.raises(psycopg.Error, match="source identity is immutable"):
            repository.connection.execute(
                "UPDATE source SET origin=jsonb_set(origin, '{repository}', %s::jsonb) WHERE id=%s",
                ('"other/repository"', SOURCE_ID),
            )

        with pytest.raises(psycopg.Error, match="source identity is immutable"):
            repository.connection.execute(
                "UPDATE source SET kind='blog' WHERE id=%s",
                (SOURCE_ID,),
            )

        # Discovery freshness metadata may evolve without changing what src:* identifies.
        repository.connection.execute(
            """
            UPDATE source
            SET origin = jsonb_set(
                jsonb_set(origin, '{stargazers_count}', '777'::jsonb),
                '{description}', '"Updated description"'::jsonb
            )
            WHERE id=%s
            """,
            (SOURCE_ID,),
        )

        volatile = _volatile_update(repository.get(SOURCE_ID))
        repository.put(volatile, replace=True)

        # License and acquisition are governed mutable state, not Source identity.
        mutable = repository.get(SOURCE_ID)
        assert mutable is not None
        mutable["license"] = {"state": "KNOWN", "declared_expression": "MIT"}
        mutable["acquisition"] = {"level": "selected-files"}
        repository.put(mutable, replace=True)

        final = repository.get(SOURCE_ID)
        assert final is not None
        assert final["kind"] == "repository"
        assert final["origin"]["provider"] == "github"
        assert final["origin"]["repository"] == "example/identity"
        assert final["origin"]["url"] == "https://github.com/example/identity"
        assert final["origin"]["github_repository_id"] == 123456
        assert final["origin"]["stargazers_count"] == 999
        assert final["license"]["state"] == "KNOWN"
        assert final["acquisition"] == {"level": "selected-files"}
    finally:
        repository.close()
