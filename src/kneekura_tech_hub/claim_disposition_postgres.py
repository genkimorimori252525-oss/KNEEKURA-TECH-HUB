from __future__ import annotations

import psycopg
from psycopg.types.json import Jsonb

from .claim_disposition import validate_claim_disposition_decision
from .claim_validation_postgres import ClaimValidationPostgresRepository
from .repository import DuplicateRecordError, Record


class ClaimDispositionPostgresRepository(ClaimValidationPostgresRepository):
    """PostgreSQL extension for append-only Claim disposition decisions."""

    @classmethod
    def connect(cls, dsn: str) -> "ClaimDispositionPostgresRepository":
        return cls(psycopg.connect(dsn, autocommit=True))

    def get(self, record_id: str) -> Record | None:
        if record_id.startswith("cdd:"):
            return self._get_claim_disposition_decision(record_id)
        return super().get(record_id)

    def put(self, record: Record, *, replace: bool = False) -> None:
        if record.get("record_type") != "claim_disposition_decision":
            super().put(record, replace=replace)
            return
        if replace:
            raise ValueError("claim disposition decisions are append-only")
        validate_claim_disposition_decision(record)
        with self.connection.transaction():
            if self.get(record["id"]) is not None:
                raise DuplicateRecordError(f"record already exists: {record['id']}")
            self.connection.execute(
                """
                INSERT INTO claim_disposition_decision(
                    id, claim_id, from_maturity, to_maturity, successor_claim_id,
                    reason, decided_by, evidence_ids, supporting_evidence_ids,
                    refuting_evidence_ids, qualifying_evidence_ids,
                    distinct_source_ids, distinct_snapshot_ids, review_flags,
                    competing_active_claim_ids, competition_note,
                    policy_version, decided_at
                ) VALUES (
                    %s,%s,%s,%s,%s,%s,%s,%s,%s,
                    %s,%s,%s,%s,%s,%s,%s,%s,%s
                )
                """,
                (
                    record["id"],
                    record["claim_id"],
                    record["from_maturity"],
                    record["to_maturity"],
                    record.get("successor_claim_id"),
                    record["reason"],
                    Jsonb(record["decided_by"]),
                    Jsonb(record["evidence_ids"]),
                    Jsonb(record["supporting_evidence_ids"]),
                    Jsonb(record["refuting_evidence_ids"]),
                    Jsonb(record["qualifying_evidence_ids"]),
                    Jsonb(record["distinct_source_ids"]),
                    Jsonb(record["distinct_snapshot_ids"]),
                    Jsonb(record["review_flags"]),
                    Jsonb(record["competing_active_claim_ids"]),
                    record.get("competition_note"),
                    record["policy_version"],
                    record["decided_at"],
                ),
            )

    def list(self, record_type: str | None = None) -> list[Record]:
        if record_type == "claim_disposition_decision":
            return self._list_claim_disposition_decisions()
        records = super().list(record_type)
        if record_type is None:
            records.extend(self._list_claim_disposition_decisions())
        return records

    def lock_claim_for_disposition(self, claim_id: str) -> None:
        row = self.connection.execute(
            "SELECT id FROM claim WHERE id=%s FOR UPDATE",
            (claim_id,),
        ).fetchone()
        if row is None:
            raise ValueError(f"missing claim: {claim_id}")

    def _list_claim_disposition_decisions(self) -> list[Record]:
        records: list[Record] = []
        for (record_id,) in self.connection.execute(
            "SELECT id FROM claim_disposition_decision ORDER BY decided_at, id"
        ).fetchall():
            record = self._get_claim_disposition_decision(record_id)
            if record is not None:
                records.append(record)
        return records

    def _get_claim_disposition_decision(self, record_id: str) -> Record | None:
        row = self.connection.execute(
            """
            SELECT claim_id, from_maturity, to_maturity, successor_claim_id,
                   reason, decided_by, evidence_ids, supporting_evidence_ids,
                   refuting_evidence_ids, qualifying_evidence_ids,
                   distinct_source_ids, distinct_snapshot_ids, review_flags,
                   competing_active_claim_ids, competition_note,
                   policy_version, decided_at
              FROM claim_disposition_decision
             WHERE id=%s
            """,
            (record_id,),
        ).fetchone()
        if row is None:
            return None
        record: Record = {
            "record_type": "claim_disposition_decision",
            "id": record_id,
            "claim_id": row[0],
            "from_maturity": row[1],
            "to_maturity": row[2],
            "reason": row[4],
            "decided_by": row[5],
            "evidence_ids": row[6],
            "supporting_evidence_ids": row[7],
            "refuting_evidence_ids": row[8],
            "qualifying_evidence_ids": row[9],
            "distinct_source_ids": row[10],
            "distinct_snapshot_ids": row[11],
            "review_flags": row[12],
            "competing_active_claim_ids": row[13],
            "policy_version": row[15],
            "decided_at": row[16].isoformat(),
        }
        if row[3] is not None:
            record["successor_claim_id"] = row[3]
        if row[14] is not None:
            record["competition_note"] = row[14]
        validate_claim_disposition_decision(record)
        return record
