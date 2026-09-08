from __future__ import annotations

import os

import psycopg
import pytest

from kneekura_tech_hub.authorization import (
    AcquisitionAuthorizationEngine,
    acquisition_authorization_history,
    active_acquisition_authorizations,
    authorized_acquisition_requests,
)
from kneekura_tech_hub.authorization_postgres import AuthorizationPostgresRepository
from kneekura_tech_hub.database import apply_migrations
from kneekura_tech_hub.selection import SourceSelectionEngine


DSN = os.getenv("KTHUB_TEST_DATABASE_URL")
pytestmark = pytest.mark.skipif(not DSN, reason="KTHUB_TEST_DATABASE_URL is not set")
HUMAN = {"actor_type": "human", "actor_id": "authorization-reviewer"}
SOURCE_ID = "src:github:example:authorization-postgres"
SHA = "0123456789abcdef0123456789abcdef01234567"


def _truncate(connection) -> None:
    connection.execute(
        """
        TRUNCATE TABLE
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


def _source() -> dict:
    return {
        "record_type": "source",
        "id": SOURCE_ID,
        "kind": "repository",
        "origin": {
            "provider": "github",
            "repository": "example/authorization-postgres",
            "url": "https://github.com/example/authorization-postgres",
        },
        "acquisition": {"level": "metadata-only"},
        "license": {
            "state": "KNOWN",
            "declared_expression": "MIT",
            "handling_policy": "REFERENCE_ONLY",
        },
    }


def test_postgres_authorize_revoke_round_trip_preserves_source():
    assert DSN is not None
    connection = psycopg.connect(DSN, autocommit=True)
    try:
        apply_migrations(connection)
        _truncate(connection)
        repository = AuthorizationPostgresRepository(connection)
        repository.put(_source())
        before = repository.get(SOURCE_ID)
        selection = SourceSelectionEngine(repository).create_from_fields(
            source_id=SOURCE_ID,
            decision="SELECT_FOR_REVIEW",
            rationale="Manual review warrants an exact selected-file authorization.",
            actor=HUMAN,
            decision_id="sd:authorization-postgres",
        )
        engine = AcquisitionAuthorizationEngine(repository)

        first = engine.authorize_from_fields(
            source_id=SOURCE_ID,
            selection_decision_id=selection["id"],
            revision=SHA,
            allowed_paths=["README.md", "src/lib.rs"],
            rationale="Authorize only two files at one immutable revision.",
            actor=HUMAN,
            authorization_id="aa:postgres:first",
        )

        assert repository.get(first["id"]) == first
        assert repository.get(SOURCE_ID) == before
        requests = authorized_acquisition_requests(repository)
        assert [item["authorization"]["id"] for item in requests] == ["aa:postgres:first"]
        assert requests[0]["source"]["acquisition"] == {"level": "metadata-only"}

        revoked = engine.revoke(
            first["id"],
            rationale="Cancel the exact scope before any execution.",
            actor=HUMAN,
            revocation_id="aa:postgres:revoke",
        )
        assert repository.get(revoked["id"]) == revoked
        assert [item["id"] for item in acquisition_authorization_history(repository)] == [
            "aa:postgres:first",
            "aa:postgres:revoke",
        ]
        assert [item["id"] for item in active_acquisition_authorizations(repository)] == [
            "aa:postgres:revoke"
        ]
        assert authorized_acquisition_requests(repository) == []
        assert repository.get(SOURCE_ID) == before
    finally:
        connection.close()


def test_authorization_table_is_append_only_through_repository():
    assert DSN is not None
    connection = psycopg.connect(DSN, autocommit=True)
    try:
        apply_migrations(connection)
        _truncate(connection)
        repository = AuthorizationPostgresRepository(connection)
        repository.put(_source())
        selection = SourceSelectionEngine(repository).create_from_fields(
            source_id=SOURCE_ID,
            decision="SELECT_FOR_REVIEW",
            rationale="Select for review.",
            actor=HUMAN,
            decision_id="sd:authorization-append-only",
        )
        record = AcquisitionAuthorizationEngine(repository).authorize_from_fields(
            source_id=SOURCE_ID,
            selection_decision_id=selection["id"],
            revision=SHA,
            allowed_paths=["README.md"],
            rationale="Exact immutable scope.",
            actor=HUMAN,
            authorization_id="aa:postgres:append-only",
        )

        with pytest.raises(ValueError, match="append-only"):
            repository.put(record, replace=True)
    finally:
        connection.close()
