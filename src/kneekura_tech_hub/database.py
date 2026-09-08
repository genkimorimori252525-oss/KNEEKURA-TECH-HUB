from __future__ import annotations

from pathlib import Path
from typing import Any

import psycopg


def default_migration_path() -> Path:
    return Path(__file__).resolve().parents[2] / "migrations" / "0001_foundation.sql"


def apply_foundation_migration(
    connection: psycopg.Connection[Any],
    migration_path: Path | None = None,
) -> None:
    """Apply the idempotent foundation migration using simple statements."""
    path = migration_path or default_migration_path()
    sql = path.read_text(encoding="utf-8")
    for statement in sql.split(";"):
        statement = statement.strip()
        if not statement or statement in {"BEGIN", "COMMIT"}:
            continue
        connection.execute(statement)
