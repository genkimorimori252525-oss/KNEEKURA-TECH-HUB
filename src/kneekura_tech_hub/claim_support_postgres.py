from __future__ import annotations

import psycopg
from psycopg.types.json import Jsonb

from .claim_support import validate_claim_support_decision
from .observation_triage_postgres import ObservationTriagePostgresRepository
from .repository import DuplicateRecordError, Record


class ClaimSupportPostgresRepository(ObservationTriagePostgresRepository):
    """PostgreSQL extension for append-only Claim support decisions."""

    @classmethod
    def connect(cls, dsn: str) -> "ClaimSupportPostgresRepository":
        return cls(psycopg.connect(dsn, autocommit=True))

    def get(self, record_id: str) -> Record | None:
        if record_id.startswith("csd:"):
            return self._get_claim_support_decision(record_id)
        return super().get(record_id)

    def put(self, record: Record, *, replace: bool = False) -> None:
        if record.get("record_type") != "claim_support_decision":
            super().put(record, replace=replace)
            return
        if replace:
            raise ValueError("claim support decisions are append-only")
        validate_claim_support_decision(record)
        with self.connection.transaction():
            if self.get(record["id"]) is not None:
                raise DuplicateRecordError(f"record already exists: {record['id']}")
            self.connection.execute(
                """
                INSERT INTO claim_support_decision(
                    id, claim_id, from_maturity, to_maturity, reason, reviewed_by,
                    evidence_ids, supporting_evidence_ids, refuting_evidence_ids,
                    qualifying_evidence_ids, distinct_source_ids, distinct_snapshot_ids,
                    review_flags, competing_active_claim_ids, independence_assessment,
                    independence_note, counterevidence_note, qualification_note,
                    competition_note, policy_version, decided_at
                ) VALUES (
                    %s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s
                )
                """,
                (
                    record["id"],
                    record["claim_id"],
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
        if record_type == "claim_support_decision":
            return self._list_claim_support_decisions()
        records = super().list(record_type)
        if record_type is None:
            records.extend(self._list_claim_support_decisions())
        return records

    def lock_claim_for_support(self, claim_id: str) -> None:
        row = self.connection.execute(
            "SELECT id FROM claim WHERE id=%s FOR UPDATE",
            (claim_id,),
        ).fetchone()
        if row is None:
            raise ValueError(f"missing claim: {claim_id}")

    def arm_support_review(self, claim_id: str, decided_at: str) -> None:
        result = self.connection.execute(
            "UPDATE claim SET pending_support_reviewed_at=%s WHERE id=%s",
            (decided_at, claim_id),
        )
        if result.rowcount != 1:
            raise ValueError(f"missing claim: {claim_id}")

    def _list_claim_support_decisions(self) -> list[Record]:
        records: list[Record] = []
        for (record_id,) in self.connection.execute(
            "SELECT id FROM claim_support_decision ORDER BY decided_at, id"
        ).fetchall():
            record = self._get_claim_support_decision(record_id)
            if record is not None:
                records.append(record)
        return records

    def _get_claim_support_decision(self, record_id: str) -> Record | None:
        row = self.connection.execute(
            """
            SELECT claim_id, from_maturity, to_maturity, reason, reviewed_by,
                   evidence_ids, supporting_evidence_ids, refuting_evidence_ids,
                   qualifying_evidence_ids, distinct_source_ids, distinct_snapshot_ids,
                   review_flags, competing_active_claim_ids, independence_assessment,
                   independence_note, counterevidence_note, qualification_note,
                   competition_note, policy_version, decided_at
              FROM claim_support_decision
             WHERE id=%s
            """,
            (record_id,),
        ).fetchone()
        if row is None:
            return None
        record: Record = {
            "record_type": "claim_support_decision",
            "id": record_id,
            "claim_id": row[0],
            "from_maturity": row[1],
            "to_maturity": row[2],
            "reason": row[3],
            "reviewed_by": row[4],
            "evidence_ids": row[5],
            "supporting_evidence_ids": row[6],
            "refuting_evidence_ids": row[7],
            "qualifying_evidence_ids": row[8],
            "distinct_source_ids": row[9],
            "distinct_snapshot_ids": row[10],
            "review_flags": row[11],
            "competing_active_claim_ids": row[12],
            "independence_assessment": row[13],
            "policy_version": row[18],
            "decided_at": row[19].isoformat(),
        }
        optional = (
            "independence_note",
            "counterevidence_note",
            "qualification_note",
            "competition_note",
        )
        for field, value in zip(optional, row[14:18], strict=True):
            if value is not None:
                record[field] = value
        validate_claim_support_decision(record)
        return record
