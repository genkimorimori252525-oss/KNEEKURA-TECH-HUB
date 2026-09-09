from __future__ import annotations

from typing import Any, Callable
from uuid import uuid4

import psycopg
from psycopg.types.json import Jsonb

from .authorization import authorization_effectiveness
from .execution import record_fingerprint_sha256
from .execution_postgres import ExecutionPostgresRepository
from .repository import DuplicateRecordError, Record


class VerifiedCommitPostgresRepository(ExecutionPostgresRepository):
    """PostgreSQL extension that atomically canonicalizes one verified execution."""

    @classmethod
    def connect(cls, dsn: str) -> "VerifiedCommitPostgresRepository":
        return cls(psycopg.connect(dsn, autocommit=True))

    def get(self, record_id: str) -> Record | None:
        if record_id.startswith("vc:"):
            return self._get_acquisition_commit(record_id)
        return super().get(record_id)

    def put(self, record: Record, *, replace: bool = False) -> None:
        if record.get("record_type") == "source_acquisition_commit":
            raise ValueError(
                "source acquisition commits must be created through atomic verified commit"
            )
        super().put(record, replace=replace)

    def list(self, record_type: str | None = None) -> list[Record]:
        if record_type == "source_acquisition_commit":
            return self._list_acquisition_commits()
        records = super().list(record_type)
        if record_type is None:
            records.extend(self._list_acquisition_commits())
        return records

    def _list_acquisition_commits(self) -> list[Record]:
        records: list[Record] = []
        for (record_id,) in self.connection.execute(
            "SELECT id FROM source_acquisition_commit ORDER BY id"
        ).fetchall():
            record = self._get_acquisition_commit(record_id)
            if record is not None:
                records.append(record)
        return records

    def _get_acquisition_commit(self, record_id: str) -> Record | None:
        row = self.connection.execute(
            """
            SELECT execution_id, authorization_id, source_id, snapshot_id, revision,
                   acquisition_level, manifest_sha256, source_fingerprint_sha256,
                   authorization_fingerprint_sha256, committed_by, policy_version, committed_at
            FROM source_acquisition_commit WHERE id=%s
            """,
            (record_id,),
        ).fetchone()
        if row is None:
            return None
        return {
            "record_type": "source_acquisition_commit",
            "id": record_id,
            "execution_id": row[0],
            "authorization_id": row[1],
            "source_id": row[2],
            "snapshot_id": row[3],
            "revision": row[4],
            "acquisition_level": row[5],
            "manifest_sha256": row[6],
            "source_fingerprint_sha256": row[7],
            "authorization_fingerprint_sha256": row[8],
            "committed_by": row[9],
            "policy_version": row[10],
            "committed_at": row[11].isoformat(),
        }

    def commit_verified_acquisition_atomic(
        self,
        *,
        expected_source: Record,
        expected_authorization: Record,
        expected_execution: Record,
        source_after: Record,
        snapshot: Record,
        commit_record: Record,
        event: Record,
        prewrite_check: Callable[[], None],
    ) -> tuple[Record, Record, Record]:
        """Lock live authority, reverify bytes, then publish all canonical records atomically."""

        source_id = expected_source["id"]
        authorization_id = expected_authorization["id"]
        execution_id = expected_execution["id"]

        with self.connection.transaction():
            if self.connection.execute(
                "SELECT 1 FROM source_acquisition_commit WHERE execution_id=%s",
                (execution_id,),
            ).fetchone():
                raise DuplicateRecordError(
                    f"execution already has a verified acquisition commit: {execution_id}"
                )

            # Lock the Source and all authority rows that can change effectiveness.
            self.connection.execute(
                "SELECT id FROM source WHERE id=%s FOR UPDATE",
                (source_id,),
            ).fetchone()
            self.connection.execute(
                "SELECT id FROM source_selection_decision WHERE source_id=%s ORDER BY id FOR UPDATE",
                (source_id,),
            ).fetchall()
            self.connection.execute(
                "SELECT id FROM source_acquisition_authorization WHERE source_id=%s ORDER BY id FOR UPDATE",
                (source_id,),
            ).fetchall()
            self.connection.execute(
                "SELECT id FROM source_acquisition_execution WHERE id=%s FOR UPDATE",
                (execution_id,),
            ).fetchone()

            current_source = super().get(source_id)
            current_authorization = super().get(authorization_id)
            current_execution = super().get(execution_id)
            if current_source != expected_source:
                raise ValueError("Source changed before verified acquisition commit")
            if current_authorization != expected_authorization:
                raise ValueError("Authorization changed before verified acquisition commit")
            if current_execution != expected_execution:
                raise ValueError("Execution changed before verified acquisition commit")

            if record_fingerprint_sha256(current_source) != expected_execution.get(
                "source_fingerprint_sha256"
            ):
                raise ValueError("Source fingerprint no longer matches execution provenance")
            if record_fingerprint_sha256(current_authorization) != expected_execution.get(
                "authorization_fingerprint_sha256"
            ):
                raise ValueError("Authorization fingerprint no longer matches execution provenance")

            effectiveness = authorization_effectiveness(self, authorization_id)
            if not effectiveness["effective"]:
                raise ValueError(
                    "Authorization is no longer effective at commit: "
                    + ",".join(effectiveness["blockers"])
                )
            if (current_source.get("acquisition") or {}).get("level") != "metadata-only":
                raise ValueError("verified acquisition commit requires metadata-only Source")
            if current_execution.get("status") != "SUCCEEDED":
                raise ValueError("verified acquisition commit requires SUCCEEDED execution")

            # Close the filesystem verification -> DB commit race as far as the local model can:
            # after authority rows are locked, re-read and re-hash the store again before writes.
            prewrite_check()

            if self.connection.execute(
                "SELECT 1 FROM source_snapshot WHERE id=%s",
                (snapshot["id"],),
            ).fetchone():
                raise DuplicateRecordError(f"snapshot already exists: {snapshot['id']}")

            self.connection.execute(
                """
                INSERT INTO source_snapshot(
                    source_id, revision, tree_hash, content_hash, swhid, captured_at, metadata, id
                ) VALUES (%s,%s,%s,%s,%s,%s,%s,%s)
                """,
                (
                    snapshot["source_id"],
                    snapshot.get("revision"),
                    snapshot.get("tree_hash"),
                    snapshot.get("content_hash"),
                    snapshot.get("swhid"),
                    snapshot["captured_at"],
                    Jsonb(snapshot.get("metadata", {})),
                    snapshot["id"],
                ),
            )

            cursor = self.connection.execute(
                """
                UPDATE source
                SET acquisition_level='selected-files', last_checked=%s
                WHERE id=%s AND acquisition_level='metadata-only'
                """,
                (commit_record["committed_at"], source_id),
            )
            if cursor.rowcount != 1:
                raise ValueError("Source acquisition level changed during verified commit")

            self.connection.execute(
                """
                INSERT INTO source_acquisition_commit(
                    id, execution_id, authorization_id, source_id, snapshot_id, revision,
                    acquisition_level, manifest_sha256, source_fingerprint_sha256,
                    authorization_fingerprint_sha256, committed_by, policy_version, committed_at
                ) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                """,
                (
                    commit_record["id"],
                    commit_record["execution_id"],
                    commit_record["authorization_id"],
                    commit_record["source_id"],
                    commit_record["snapshot_id"],
                    commit_record["revision"],
                    commit_record["acquisition_level"],
                    commit_record["manifest_sha256"],
                    commit_record["source_fingerprint_sha256"],
                    commit_record["authorization_fingerprint_sha256"],
                    Jsonb(commit_record["committed_by"]),
                    commit_record["policy_version"],
                    commit_record["committed_at"],
                ),
            )

            self.connection.execute(
                """
                INSERT INTO curation_event(
                    operation, actor, subject_ids, reason, policy_version, occurred_at, reversible, id
                ) VALUES (%s,%s,%s,%s,%s,%s,%s,%s)
                """,
                (
                    event["operation"],
                    Jsonb(event["actor"]),
                    Jsonb(event["subject_ids"]),
                    event.get("reason"),
                    event["policy_version"],
                    event["occurred_at"],
                    event.get("reversible", False),
                    event.get("id") or f"ce:{uuid4()}",
                ),
            )

            stored_commit = self._get_acquisition_commit(commit_record["id"])
            stored_snapshot = super().get(snapshot["id"])
            stored_source = super().get(source_id)
            if stored_commit is None or stored_snapshot is None or stored_source is None:
                raise RuntimeError("verified acquisition commit did not round-trip inside transaction")
            if stored_source != source_after:
                raise RuntimeError("Source after verified commit differs from planned Source")
            return stored_commit, stored_snapshot, stored_source
