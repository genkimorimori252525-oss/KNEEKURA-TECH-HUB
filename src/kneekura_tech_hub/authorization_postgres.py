from __future__ import annotations

import psycopg
from psycopg.types.json import Jsonb

from .repository import DuplicateRecordError, Record
from .selection_postgres import SelectionPostgresRepository


class AuthorizationPostgresRepository(SelectionPostgresRepository):
    """PostgreSQL governance extension for bounded acquisition authorizations."""

    @classmethod
    def connect(cls, dsn: str) -> "AuthorizationPostgresRepository":
        return cls(psycopg.connect(dsn, autocommit=True))

    def get(self, record_id: str) -> Record | None:
        if record_id.startswith("aa:"):
            return self._get_acquisition_authorization(record_id)
        return super().get(record_id)

    def put(self, record: Record, *, replace: bool = False) -> None:
        if record.get("record_type") != "source_acquisition_authorization":
            super().put(record, replace=replace)
            return
        if replace:
            raise ValueError("source acquisition authorizations are append-only")
        with self.connection.transaction():
            if self.get(record["id"]) is not None:
                raise DuplicateRecordError(f"record already exists: {record['id']}")
            self.connection.execute(
                """
                INSERT INTO source_acquisition_authorization(
                    source_id, decision, selection_decision_id, acquisition_level,
                    revision, allowed_paths, rationale, created_by, policy_version,
                    decided_at, supersedes_authorization_id, id
                ) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                """,
                (
                    record["source_id"],
                    record["decision"],
                    record["selection_decision_id"],
                    record["acquisition_level"],
                    record["revision"],
                    Jsonb(record["allowed_paths"]),
                    record["rationale"],
                    Jsonb(record["created_by"]),
                    record["policy_version"],
                    record["decided_at"],
                    record.get("supersedes_authorization_id"),
                    record["id"],
                ),
            )

    def list(self, record_type: str | None = None) -> list[Record]:
        if record_type == "source_acquisition_authorization":
            return self._list_acquisition_authorizations()
        if record_type == "source_acquisition_commit":
            return self._list_acquisition_commit_authority_refs()
        records = super().list(record_type)
        if record_type is None:
            records.extend(self._list_acquisition_authorizations())
        return records

    def _list_acquisition_authorizations(self) -> list[Record]:
        records: list[Record] = []
        for (record_id,) in self.connection.execute(
            "SELECT id FROM source_acquisition_authorization ORDER BY id"
        ).fetchall():
            record = self._get_acquisition_authorization(record_id)
            if record is not None:
                records.append(record)
        return records

    def _list_acquisition_commit_authority_refs(self) -> list[Record]:
        """Expose only the immutable fields Authorization needs to prove grant consumption."""

        return [
            {
                "record_type": "source_acquisition_commit",
                "id": record_id,
                "authorization_id": authorization_id,
            }
            for record_id, authorization_id in self.connection.execute(
                "SELECT id, authorization_id FROM source_acquisition_commit ORDER BY id"
            ).fetchall()
        ]

    def _get_acquisition_authorization(self, record_id: str) -> Record | None:
        row = self.connection.execute(
            """
            SELECT source_id, decision, selection_decision_id, acquisition_level,
                   revision, allowed_paths, rationale, created_by, policy_version,
                   decided_at, supersedes_authorization_id
            FROM source_acquisition_authorization WHERE id=%s
            """,
            (record_id,),
        ).fetchone()
        if row is None:
            return None
        record: Record = {
            "record_type": "source_acquisition_authorization",
            "id": record_id,
            "source_id": row[0],
            "decision": row[1],
            "selection_decision_id": row[2],
            "acquisition_level": row[3],
            "revision": row[4],
            "allowed_paths": list(row[5]),
            "rationale": row[6],
            "created_by": row[7],
            "policy_version": row[8],
            "decided_at": row[9].isoformat(),
        }
        if row[10] is not None:
            record["supersedes_authorization_id"] = row[10]
        return record
