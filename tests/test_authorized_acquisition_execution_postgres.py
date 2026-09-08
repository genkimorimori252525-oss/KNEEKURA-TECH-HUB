from __future__ import annotations

from hashlib import sha1
import os
from pathlib import Path

import psycopg
import pytest

from kneekura_tech_hub.authorization import AcquisitionAuthorizationEngine
from kneekura_tech_hub.database import apply_migrations
from kneekura_tech_hub.execution import acquisition_execution_history, execute_authorized_acquisition
from kneekura_tech_hub.execution_postgres import ExecutionPostgresRepository
from kneekura_tech_hub.selection import SourceSelectionEngine


DSN = os.getenv("KTHUB_TEST_DATABASE_URL")
pytestmark = pytest.mark.skipif(not DSN, reason="KTHUB_TEST_DATABASE_URL is not set")
SHA = "0123456789abcdef0123456789abcdef01234567"
SOURCE_ID = "src:github:example:execution-postgres"
HUMAN = {"actor_type": "human", "actor_id": "postgres-reviewer"}
TOOL = {"actor_type": "tool", "actor_id": "postgres-fetcher", "version": "v1"}


def _blob_sha(content: bytes) -> str:
    header = f"blob {len(content)}\0".encode("ascii")
    return sha1(header + content).hexdigest()  # noqa: S324 - Git identity


def _truncate(connection) -> None:
    connection.execute(
        """
        TRUNCATE TABLE
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


def _source() -> dict:
    return {
        "record_type": "source",
        "id": SOURCE_ID,
        "kind": "repository",
        "origin": {
            "provider": "github",
            "repository": "example/execution-postgres",
            "url": "https://github.com/example/execution-postgres",
        },
        "acquisition": {"level": "metadata-only"},
        "license": {
            "state": "KNOWN",
            "declared_expression": "MIT",
            "handling_policy": "REFERENCE_ONLY",
        },
    }


def _setup(repository: ExecutionPostgresRepository) -> dict:
    repository.put(_source())
    selection = SourceSelectionEngine(repository).create_from_fields(
        source_id=SOURCE_ID,
        decision="SELECT_FOR_REVIEW",
        rationale="Review the exact pinned files.",
        actor=HUMAN,
        decision_id="sd:execution-postgres",
    )
    return AcquisitionAuthorizationEngine(repository).authorize_from_fields(
        source_id=SOURCE_ID,
        selection_decision_id=selection["id"],
        revision=SHA,
        allowed_paths=["README.md", "src/lib.rs"],
        rationale="Authorize only the exact two files.",
        actor=HUMAN,
        authorization_id="aa:execution-postgres",
    )


def test_execution_round_trip_preserves_source_and_files(tmp_path: Path):
    assert DSN is not None
    connection = psycopg.connect(DSN, autocommit=True)
    try:
        apply_migrations(connection)
        _truncate(connection)
        repository = ExecutionPostgresRepository(connection)
        authorization = _setup(repository)
        before = repository.get(SOURCE_ID)
        contents = {"README.md": b"postgres readme\n", "src/lib.rs": b"pub fn p() {}\n"}

        def fetch(_source: dict, revision: str, path: str) -> dict:
            assert revision == SHA
            content = contents[path]
            return {"content": content, "git_blob_sha": _blob_sha(content)}

        record = execute_authorized_acquisition(
            repository,
            authorization["id"],
            storage_root=tmp_path,
            fetch_file=fetch,
            actor=TOOL,
            execution_id="ax:execution-postgres",
        )

        assert record["status"] == "SUCCEEDED"
        assert repository.get(record["id"]) == record
        assert acquisition_execution_history(repository) == [record]
        assert repository.get(SOURCE_ID) == before
        assert repository.list("source_snapshot") == []
        assert (tmp_path / record["storage_key"] / "README.md").read_bytes() == contents["README.md"]
        assert (tmp_path / record["storage_key"] / "src" / "lib.rs").read_bytes() == contents[
            "src/lib.rs"
        ]
    finally:
        connection.close()


def test_execution_table_is_append_only_through_repository(tmp_path: Path):
    assert DSN is not None
    connection = psycopg.connect(DSN, autocommit=True)
    try:
        apply_migrations(connection)
        _truncate(connection)
        repository = ExecutionPostgresRepository(connection)
        authorization = _setup(repository)
        content = b"one file"
        record = execute_authorized_acquisition(
            repository,
            authorization["id"],
            storage_root=tmp_path,
            fetch_file=lambda *_args: {"content": content, "git_blob_sha": _blob_sha(content)},
            actor=TOOL,
            execution_id="ax:append-only",
        )

        with pytest.raises(ValueError, match="append-only"):
            repository.put(record, replace=True)
    finally:
        connection.close()


def test_database_constraints_reject_human_execution_actor():
    assert DSN is not None
    connection = psycopg.connect(DSN, autocommit=True)
    try:
        apply_migrations(connection)
        _truncate(connection)
        repository = ExecutionPostgresRepository(connection)
        authorization = _setup(repository)
        with pytest.raises(psycopg.errors.CheckViolation):
            connection.execute(
                """
                INSERT INTO source_acquisition_execution(
                    id, authorization_id, source_id, revision, requested_paths, status,
                    file_results, manifest_sha256, storage_key, error_code, executed_by,
                    policy_version, executed_at, authorization_effective_after
                ) VALUES (%s,%s,%s,%s,%s::jsonb,'FAILED',%s::jsonb,NULL,NULL,%s,%s::jsonb,%s,now(),TRUE)
                """,
                (
                    "ax:bad-actor",
                    authorization["id"],
                    SOURCE_ID,
                    SHA,
                    '["README.md","src/lib.rs"]',
                    '[{"path":"README.md","status":"FAILED","byte_count":null,"sha256":null,"git_blob_sha":null,"error_code":"X"},{"path":"src/lib.rs","status":"FAILED","byte_count":null,"sha256":null,"git_blob_sha":null,"error_code":"X"}]',
                    "X",
                    '{"actor_type":"human","actor_id":"bad"}',
                    "1.0.0",
                ),
            )
    finally:
        connection.close()
