from __future__ import annotations

import psycopg
from psycopg.types.json import Jsonb

from .claim_resupport import validate_claim_resupport_decision
from .claim_validation_postgres import ClaimValidationPostgresRepository
from .repository import DuplicateRecordError, Record


class ClaimResupportPostgresRepository(ClaimValidationPostgresRepository):
    """PostgreSQL extension for append-only Claim resupport decisions."""

    @classmethod
    def connect(cls, dsn: str) -> "ClaimResupportPostgresRepository":
        return cls(psycopg.connect(dsn, autocommit=True))

    def get(self, record_id: str) -> Record | None:
        if record_id.startswith("crsd:"):
            return self._get_claim_resupport_decision(record_id)
        return super().get(record_id)

    def put(self, record: Record, *, replace: bool = False) -> None:
        if record.get("record_type") != "claim_resupport_decision":
            super().put(record, replace=replace)
            return
        if replace:
            raise ValueError("claim resupport decisions are append-only")
        validate_claim_resupport_decision(record)
        with self.connection.transaction():
            if self.get(record["id"]) is not None:
                raise DuplicateRecordError(f"record already exists: {record['id']}")
            self.connection.execute(
                """
                INSERT INTO claim_resupport_decision(
                    id, claim_id, initial_support_decision_id, from_maturity, to_maturity,
                    reason, reviewed_by, evidence_ids, supporting_evidence_ids,
                    refuting_evidence_ids, qualifying_evidence_ids, distinct_source_ids,
                    distinct_snapshot_ids, review_flags, competing_active_claim_ids,
                    independence_assessment, independence_note, counterevidence_note,
                    qualification_note, competition_note, policy_version, decided_at
                ) VALUES (
                    %s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,
                    %s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s
                )
                """,
                (
                    record["id"],
                    record["claim_id"],
                    record["initial_support_decision_id"],
                    record["from_maturity"],
                    record["to_maturity"],
                    record["reason"],
                    Jsonb(record["reviewed_by"]),
                    Jsonb(record["evidence_ids"]),
                    Jsonb(record["supporting_evidence_ids"]),
                    Jsonb(record["refuting_evidence_ids"]),
                    Jsonb(record["qualifying_evidence_ids"]),
                    Jsonb(record["distinct_source_ids"]),
                    Jsonb(record["distinct_snapshot_ids"]),
                    Jsonb(record["review_flags"]),
                    Jsonb(record["competing_active_claim_ids"]),
                    record["independence_assessment"],
                    record.get("independence_note"),
                    record.get("counterevidence_note"),
                    record.get("qualification_note"),
                    record.get("competition_note"),
                    record["policy_version"],
                    record["decided_at"],
                ),
            )

    def list(self, record_type: str | None = None) -> list[Record]:
        if record_type == "claim_resupport_decision":
            return self._list_claim_resupport_decisions()
        records = super().list(record_type)
        if record_type is None:
            records.extend(self._list_claim_resupport_decisions())
        return records

    def lock_claim_for_resupport(self, claim_id: str) -> None:
        row = self.connection.execute(
            "SELECT id FROM claim WHERE id=%s FOR UPDATE",
            (claim_id,),
        ).fetchone()
        if row is None:
            raise ValueError(f"missing claim: {claim_id}")

    def _list_claim_resupport_decisions(self) -> list[Record]:
        records: list[Record] = []
        for (record_id,) in self.connection.execute(
            "SELECT id FROM claim_resupport_decision ORDER BY decided_at, id"
        ).fetchall():
            record = self._get_claim_resupport_decision(record_id)
            if record is not None:
                records.append(record)
        return records

    def _get_claim_resupport_decision(self, record_id: str) -> Record | None:
        row = self.connection.execute(
            """
            SELECT claim_id, initial_support_decision_id, from_maturity, to_maturity,
                   reason, reviewed_by, evidence_ids, supporting_evidence_ids,
                   refuting_evidence_ids, qualifying_evidence_ids, distinct_source_ids,
                   distinct_snapshot_ids, review_flags, competing_active_claim_ids,
                   independence_assessment, independence_note, counterevidence_note,
                   qualification_note, competition_note, policy_version, decided_at
              FROM claim_resupport_decision
             WHERE id=%s
            """,
            (record_id,),
        ).fetchone()
        if row is None:
            return None
        record: Record = {
            "record_type": "claim_resupport_decision",
            "id": record_id,
            "claim_id": row[0],
            "initial_support_decision_id": row[1],
            "from_maturity": row[2],
            "to_maturity": row[3],
            "reason": row[4],
            "reviewed_by": row[5],
            "evidence_ids": row[6],
            "supporting_evidence_ids": row[7],
            "refuting_evidence_ids": row[8],
            "qualifying_evidence_ids": row[9],
            "distinct_source_ids": row[10],
            "distinct_snapshot_ids": row[11],
            "review_flags": row[12],
            "competing_active_claim_ids": row[13],
            "independence_assessment": row[14],
            "policy_version": row[19],
            "decided_at": row[20].isoformat(),
        }
        optional = (
            "independence_note",
            "counterevidence_note",
            "qualification_note",
            "competition_note",
        )
        for field, value in zip(optional, row[15:19], strict=True):
            if value is not None:
                record[field] = value
        validate_claim_resupport_decision(record)
        return record
