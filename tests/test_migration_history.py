from __future__ import annotations

import os
from pathlib import Path

import psycopg
import pytest

from kneekura_tech_hub.database import MigrationDriftError, apply_migrations


DSN = os.getenv("KTHUB_TEST_DATABASE_URL")
pytestmark = pytest.mark.skipif(not DSN, reason="KTHUB_TEST_DATABASE_URL is not set")


def test_default_migrations_are_recorded_and_idempotently_skipped():
    assert DSN is not None
    connection = psycopg.connect(DSN, autocommit=True)
    try:
        paths = apply_migrations(connection)
        versions = [path.name for path in paths]
        rows = connection.execute(
            "SELECT version, checksum FROM schema_migration ORDER BY version"
        ).fetchall()
        recorded = {row[0]: row[1] for row in rows}

        assert "0001_foundation.sql" in versions
        assert "0002_staged_observation_evidence.sql" in versions
        assert all(recorded[version] for version in versions)

        before = dict(recorded)
        apply_migrations(connection)
        after = dict(
            connection.execute(
                "SELECT version, checksum FROM schema_migration ORDER BY version"
            ).fetchall()
        )
        assert after == before
    finally:
        connection.close()


def test_changed_applied_migration_is_rejected(tmp_path: Path):
    assert DSN is not None
    migration = tmp_path / "9001_test_history.sql"
    migration.write_text(
        "CREATE TABLE IF NOT EXISTS migration_history_probe (id INTEGER PRIMARY KEY);\n",
        encoding="utf-8",
    )

    connection = psycopg.connect(DSN, autocommit=True)
    try:
        connection.execute(
            "DELETE FROM schema_migration WHERE version='9001_test_history.sql'"
        )
        connection.execute("DROP TABLE IF EXISTS migration_history_probe")

        apply_migrations(connection, tmp_path)
        migration.write_text(
            "CREATE TABLE IF NOT EXISTS migration_history_probe (id BIGINT PRIMARY KEY);\n",
            encoding="utf-8",
        )

        with pytest.raises(MigrationDriftError, match="applied migration changed"):
            apply_migrations(connection, tmp_path)
    finally:
        connection.execute(
            "DELETE FROM schema_migration WHERE version='9001_test_history.sql'"
        )
        connection.execute("DROP TABLE IF EXISTS migration_history_probe")
        connection.close()
