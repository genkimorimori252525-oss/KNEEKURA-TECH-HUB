from __future__ import annotations

from hashlib import sha256
from pathlib import Path
from typing import Any

import psycopg


class MigrationDriftError(RuntimeError):
    """Raised when an already-applied migration file changes on disk."""


def migrations_directory() -> Path:
    return Path(__file__).resolve().parents[2] / "migrations"


def default_migration_path() -> Path:
    """Return the original foundation migration path for compatibility."""
    return migrations_directory() / "0001_foundation.sql"


def _statements(sql: str) -> list[str]:
    return [
        statement
        for raw in sql.split(";")
        if (statement := raw.strip()) and statement not in {"BEGIN", "COMMIT"}
    ]


def _apply_sql_file(connection: psycopg.Connection[Any], path: Path) -> None:
    sql = path.read_text(encoding="utf-8")
    with connection.transaction():
        for statement in _statements(sql):
            connection.execute(statement)


def _ensure_migration_history(connection: psycopg.Connection[Any]) -> None:
    with connection.transaction():
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS schema_migration (
                version TEXT PRIMARY KEY,
                checksum TEXT NOT NULL,
                applied_at TIMESTAMPTZ NOT NULL DEFAULT now()
            )
            """
        )


def apply_migrations(
    connection: psycopg.Connection[Any],
    migration_dir: Path | None = None,
) -> list[Path]:
    """Apply ordered migrations exactly once and reject migration drift.

    A migration is identified by its filename and SHA-256 checksum. Previously
    applied files are skipped when their checksum matches. If an applied file is
    later edited, initialization fails instead of silently rewriting database
    history.

    Existing Phase 1/2 databases that predate ``schema_migration`` are safe: the
    first tracked run replays the already-idempotent 0001/0002 migrations once,
    records their checksums, and future runs skip them.
    """

    directory = migration_dir or migrations_directory()
    paths = sorted(directory.glob("[0-9][0-9][0-9][0-9]_*.sql"))
    if not paths:
        raise FileNotFoundError(f"no migrations found in {directory}")

    _ensure_migration_history(connection)

    for path in paths:
        content = path.read_text(encoding="utf-8")
        checksum = sha256(content.encode("utf-8")).hexdigest()
        version = path.name

        with connection.transaction():
            row = connection.execute(
                "SELECT checksum FROM schema_migration WHERE version=%s",
                (version,),
            ).fetchone()
            if row is not None:
                if row[0] != checksum:
                    raise MigrationDriftError(
                        f"applied migration changed: {version} "
                        f"stored={row[0]} current={checksum}"
                    )
                continue

            for statement in _statements(content):
                connection.execute(statement)
            connection.execute(
                "INSERT INTO schema_migration(version, checksum) VALUES (%s,%s)",
                (version, checksum),
            )

    return paths


def apply_foundation_migration(
    connection: psycopg.Connection[Any],
    migration_path: Path | None = None,
) -> None:
    """Compatibility initializer used by the Phase 1 CLI/tests.

    With no explicit path it brings the database to the latest known schema and
    uses tracked migrations. Supplying an explicit path preserves the old
    single-file behavior for focused compatibility tests.
    """

    if migration_path is not None:
        _apply_sql_file(connection, migration_path)
        return
    apply_migrations(connection)
