from __future__ import annotations

from typing import Any

import psycopg
from psycopg.types.json import Jsonb

from .postgres_repository import PostgresRepository
from .repository import DuplicateRecordError, Record


class SelectionPostgresRepository(PostgresRepository):
    """PostgreSQL repository extension for append-only Source selection decisions.

    The core PostgresRepository remains unchanged; this governance extension adds only the
    `source_selection_decision` record family and delegates all existing record types to the
    established repository implementation.
    """

    @classmethod
    def connect(cls, dsn: str) -> "SelectionPostgresRepository":
        return cls(psycopg.connect(dsn, autocommit=True))

    def get(self, record_id: str) -> Record | None:
        if record_id.startswith("sd:"):
            return self._get_source_selection_decision(record_id)
        return super().get(record_id)

    def put(self, record: Record, *, replace: bool = False) -> None:
        if record.get("record_type") != "source_selection_decision":
            super().put(record, replace=replace)
            return
        if replace:
            raise ValueError("source selection decisions are append-only")
        with self.connection.transaction():
            if self.get(record["id"]) is not None:
                raise DuplicateRecordError(f"record already exists: {record['id']}")
            self.connection.execute(
                """
                INSERT INTO source_selection_decision(
                    source_id, decision, rationale, created_by, policy_version,
                    decided_at, supersedes_decision_id, id
                ) VALUES (%s,%s,%s,%s,%s,%s,%s,%s)
                """,
                (
                    record["source_id"],
                    record["decision"],
                    record["rationale"],
                    Jsonb(record["created_by"]),
                    record["policy_version"],
                    record["decided_at"],
                    record.get("supersedes_decision_id"),
                    record["id"],
                ),
            )

    def list(self, record_type: str | None = None) -> list[Record]:
        if record_type == "source_selection_decision":
            return self._list_source_selection_decisions()
        records = super().list(record_type)
        if record_type is None:
            records.extend(self._list_source_selection_decisions())
        return records

    def _list_source_selection_decisions(self) -> list[Record]:
        records: list[Record] = []
        for (record_id,) in self.connection.execute(
            "SELECT id FROM source_selection_decision ORDER BY id"
        ).fetchall():
            record = self._get_source_selection_decision(record_id)
            if record is not None:
                records.append(record)
        return records

    def _get_source_selection_decision(self, record_id: str) -> Record | None:
        row = self.connection.execute(
            """
            SELECT source_id, decision, rationale, created_by, policy_version,
                   decided_at, supersedes_decision_id
            FROM source_selection_decision WHERE id=%s
            """,
            (record_id,),
        ).fetchone()
        if row is None:
            return None
        record: Record = {
            "record_type": "source_selection_decision",
            "id": record_id,
            "source_id": row[0],
            "decision": row[1],
            "rationale": row[2],
            "created_by": row[3],
            "policy_version": row[4],
            "decided_at": row[5].isoformat(),
        }
        if row[6] is not None:
            record["supersedes_decision_id"] = row[6]
        return record
