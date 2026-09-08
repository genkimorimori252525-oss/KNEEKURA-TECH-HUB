from __future__ import annotations

from pathlib import Path
from typing import Any

import psycopg


def migrations_directory() -> Path:
    return Path(__file__).resolve().parents[2] / "migrations"


def default_migration_path() -> Path:
    """Return the original foundation migration path for compatibility."""
    return migrations_directory() / "0001_foundation.sql"


def _apply_sql_file(connection: psycopg.Connection[Any], path: Path) -> None:
    sql = path.read_text(encoding="utf-8")
    with connection.transaction():
        for statement in sql.split(";"):
            statement = statement.strip()
            if not statement or statement in {"BEGIN", "COMMIT"}:
                continue
            connection.execute(statement)


def apply_migrations(
    connection: psycopg.Connection[Any],
    migration_dir: Path | None = None,
) -> list[Path]:
    """Apply all idempotent SQL migrations in filename order.

    Each migration is isolated in its own explicit transaction. Migration files
    are intentionally idempotent in v1 so this runner can safely initialize a
    fresh database or bring an existing Phase 1 database forward.
    """

    directory = migration_dir or migrations_directory()
    paths = sorted(directory.glob("[0-9][0-9][0-9][0-9]_*.sql"))
    if not paths:
        raise FileNotFoundError(f"no migrations found in {directory}")
    for path in paths:
        _apply_sql_file(connection, path)
    return paths


def apply_foundation_migration(
    connection: psycopg.Connection[Any],
    migration_path: Path | None = None,
) -> None:
    """Apply only the original foundation migration.

    Kept for backwards compatibility with callers that explicitly need 0001.
    New initialization paths should use :func:`apply_migrations`.
    """

    _apply_sql_file(connection, migration_path or default_migration_path())
