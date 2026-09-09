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


def _dollar_quote_tag(sql: str, index: int) -> str | None:
    """Return a PostgreSQL dollar-quote delimiter beginning at ``index``."""

    if sql[index] != "$":
        return None
    end = sql.find("$", index + 1)
    if end == -1:
        return None
    tag = sql[index + 1 : end]
    if tag and not (tag[0].isalpha() or tag[0] == "_"):
        return None
    if any(not (character.isalnum() or character == "_") for character in tag):
        return None
    return sql[index : end + 1]


def _statements(sql: str) -> list[str]:
    """Split PostgreSQL migration text on top-level semicolons only.

    Migration files may contain PL/pgSQL bodies, quoted strings, identifiers,
    and comments containing semicolons. A plain ``str.split(';')`` corrupts
    those constructs, so this small lexer recognizes the PostgreSQL quoting and
    comment forms relevant to migration files. Comments outside quoted bodies
    are discarded; semicolons inside them never become statement boundaries.
    """

    statements: list[str] = []
    current: list[str] = []
    index = 0
    length = len(sql)
    single_quote = False
    double_quote = False
    dollar_quote: str | None = None
    block_comment_depth = 0
    line_comment = False

    def finish() -> None:
        statement = "".join(current).strip()
        current.clear()
        if statement and statement.upper() not in {"BEGIN", "COMMIT"}:
            statements.append(statement)

    while index < length:
        character = sql[index]
        following = sql[index + 1] if index + 1 < length else ""

        if line_comment:
            if character == "\n":
                line_comment = False
                current.append("\n")
            index += 1
            continue

        if block_comment_depth:
            if character == "/" and following == "*":
                block_comment_depth += 1
                index += 2
                continue
            if character == "*" and following == "/":
                block_comment_depth -= 1
                index += 2
                if block_comment_depth == 0:
                    current.append(" ")
                continue
            index += 1
            continue

        if dollar_quote is not None:
            if sql.startswith(dollar_quote, index):
                current.append(dollar_quote)
                index += len(dollar_quote)
                dollar_quote = None
                continue
            current.append(character)
            index += 1
            continue

        if single_quote:
            current.append(character)
            if character == "'":
                if following == "'":
                    current.append(following)
                    index += 2
                    continue
                single_quote = False
            elif character == "\\" and following:
                # Conservative support for PostgreSQL E'...' strings. Treating
                # the escaped byte as part of the literal is also safe for the
                # splitter when standard_conforming_strings is enabled.
                current.append(following)
                index += 2
                continue
            index += 1
            continue

        if double_quote:
            current.append(character)
            if character == '"':
                if following == '"':
                    current.append(following)
                    index += 2
                    continue
                double_quote = False
            index += 1
            continue

        if character == "-" and following == "-":
            line_comment = True
            index += 2
            continue
        if character == "/" and following == "*":
            block_comment_depth = 1
            index += 2
            continue
        if character == "'":
            single_quote = True
            current.append(character)
            index += 1
            continue
        if character == '"':
            double_quote = True
            current.append(character)
            index += 1
            continue
        if character == "$":
            tag = _dollar_quote_tag(sql, index)
            if tag is not None:
                dollar_quote = tag
                current.append(tag)
                index += len(tag)
                continue
        if character == ";":
            finish()
            index += 1
            continue

        current.append(character)
        index += 1

    if single_quote or double_quote or dollar_quote is not None or block_comment_depth:
        raise ValueError("unterminated quoted string or comment in migration SQL")

    finish()
    return statements


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
