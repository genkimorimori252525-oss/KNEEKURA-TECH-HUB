from __future__ import annotations

import psycopg
from psycopg.types.json import Jsonb

from .authorization_postgres import AuthorizationPostgresRepository
from .repository import DuplicateRecordError, Record


class ExecutionPostgresRepository(AuthorizationPostgresRepository):
    """PostgreSQL extension for append-only acquisition execution records."""

    @classmethod
    def connect(cls, dsn: str) -> "ExecutionPostgresRepository":
        return cls(psycopg.connect(dsn, autocommit=True))

    def get(self, record_id: str) -> Record | None:
        if record_id.startswith("ax:"):
            return self._get_acquisition_execution(record_id)
        return super().get(record_id)

    def put(self, record: Record, *, replace: bool = False) -> None:
        if record.get("record_type") != "source_acquisition_execution":
            super().put(record, replace=replace)
            return
        if replace:
            raise ValueError("source acquisition executions are append-only")
        with self.connection.transaction():
            if self.get(record["id"]) is not None:
                raise DuplicateRecordError(f"record already exists: {record['id']}")
            self.connection.execute(
                """
                INSERT INTO source_acquisition_execution(
                    authorization_id, source_id, revision, requested_paths, status,
                    file_results, manifest_sha256, storage_key, error_code, executed_by,
                    policy_version, executed_at, authorization_effective_after,
                    source_fingerprint_sha256, authorization_fingerprint_sha256, id
                ) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                """,
                (
                    record["authorization_id"],
                    record["source_id"],
                    record["revision"],
                    Jsonb(record["requested_paths"]),
                    record["status"],
                    Jsonb(record["file_results"]),
                    record.get("manifest_sha256"),
                    record.get("storage_key"),
                    record.get("error_code"),
                    Jsonb(record["executed_by"]),
                    record["policy_version"],
                    record["executed_at"],
                    record["authorization_effective_after"],
                    record.get("source_fingerprint_sha256"),
                    record.get("authorization_fingerprint_sha256"),
                    record["id"],
                ),
            )

    def list(self, record_type: str | None = None) -> list[Record]:
        if record_type == "source_acquisition_execution":
            return self._list_acquisition_executions()
        records = super().list(record_type)
        if record_type is None:
            records.extend(self._list_acquisition_executions())
        return records

    def _list_acquisition_executions(self) -> list[Record]:
        records: list[Record] = []
        for (record_id,) in self.connection.execute(
            "SELECT id FROM source_acquisition_execution ORDER BY id"
        ).fetchall():
            record = self._get_acquisition_execution(record_id)
            if record is not None:
                records.append(record)
        return records

    def _get_acquisition_execution(self, record_id: str) -> Record | None:
        row = self.connection.execute(
            """
            SELECT authorization_id, source_id, revision, requested_paths, status,
                   file_results, manifest_sha256, storage_key, error_code, executed_by,
                   policy_version, executed_at, authorization_effective_after,
                   source_fingerprint_sha256, authorization_fingerprint_sha256
            FROM source_acquisition_execution WHERE id=%s
            """,
            (record_id,),
        ).fetchone()
        if row is None:
            return None
        record: Record = {
            "record_type": "source_acquisition_execution",
            "id": record_id,
            "authorization_id": row[0],
            "source_id": row[1],
            "revision": row[2],
            "requested_paths": list(row[3]),
            "status": row[4],
            "file_results": list(row[5]),
            "manifest_sha256": row[6],
            "storage_key": row[7],
            "error_code": row[8],
            "executed_by": row[9],
            "policy_version": row[10],
            "executed_at": row[11].isoformat(),
            "authorization_effective_after": row[12],
        }
        if row[13] is not None:
            record["source_fingerprint_sha256"] = row[13]
        if row[14] is not None:
            record["authorization_fingerprint_sha256"] = row[14]
        return record
