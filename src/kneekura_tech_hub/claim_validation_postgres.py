from __future__ import annotations

import psycopg
from psycopg.types.json import Jsonb

from .claim_support_postgres import ClaimSupportPostgresRepository
from .claim_validation import validate_claim_validation_decision
from .repository import DuplicateRecordError, Record


class ClaimValidationPostgresRepository(ClaimSupportPostgresRepository):
    """PostgreSQL extension for append-only Claim validation decisions."""

    @classmethod
    def connect(cls, dsn: str) -> "ClaimValidationPostgresRepository":
        return cls(psycopg.connect(dsn, autocommit=True))

    def get(self, record_id: str) -> Record | None:
        if record_id.startswith("cvd:"):
            return self._get_claim_validation_decision(record_id)
        return super().get(record_id)

    def put(self, record: Record, *, replace: bool = False) -> None:
        if record.get("record_type") != "claim_validation_decision":
            super().put(record, replace=replace)
            return
        if replace:
            raise ValueError("claim validation decisions are append-only")
        validate_claim_validation_decision(record)
        with self.connection.transaction():
            if self.get(record["id"]) is not None:
                raise DuplicateRecordError(f"record already exists: {record['id']}")
            self.connection.execute(
                """
                INSERT INTO claim_validation_decision(
                    id, claim_id, support_decision_id, from_maturity, to_maturity,
                    reason, validated_by, validation_basis, validation_note,
                    evidence_ids, supporting_evidence_ids, refuting_evidence_ids,
                    qualifying_evidence_ids, distinct_source_ids, distinct_snapshot_ids,
                    review_flags, competing_active_claim_ids, independence_assessment,
                    independence_note, counterevidence_note, qualification_note,
                    competition_note, policy_version, validated_at
                ) VALUES (
                    %s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,
                    %s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s
                )
                """,
                (
                    record["id"],
                    record["claim_id"],
                    record["support_decision_id"],
                    record["from_maturity"],
                    record["to_maturity"],
                    record["reason"],
                    Jsonb(record["validated_by"]),
                    record["validation_basis"],
                    record["validation_note"],
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
                    record["validated_at"],
                ),
            )

    def list(self, record_type: str | None = None) -> list[Record]:
        if record_type == "claim_validation_decision":
            return self._list_claim_validation_decisions()
        records = super().list(record_type)
        if record_type is None:
            records.extend(self._list_claim_validation_decisions())
        return records

    def lock_claim_for_validation(self, claim_id: str) -> None:
        row = self.connection.execute(
            "SELECT id FROM claim WHERE id=%s FOR UPDATE",
            (claim_id,),
        ).fetchone()
        if row is None:
            raise ValueError(f"missing claim: {claim_id}")

    def _list_claim_validation_decisions(self) -> list[Record]:
        records: list[Record] = []
        for (record_id,) in self.connection.execute(
            "SELECT id FROM claim_validation_decision ORDER BY validated_at, id"
        ).fetchall():
            record = self._get_claim_validation_decision(record_id)
            if record is not None:
                records.append(record)
        return records

    def _get_claim_validation_decision(self, record_id: str) -> Record | None:
        row = self.connection.execute(
            """
            SELECT claim_id, support_decision_id, from_maturity, to_maturity,
                   reason, validated_by, validation_basis, validation_note,
                   evidence_ids, supporting_evidence_ids, refuting_evidence_ids,
                   qualifying_evidence_ids, distinct_source_ids, distinct_snapshot_ids,
                   review_flags, competing_active_claim_ids, independence_assessment,
                   independence_note, counterevidence_note, qualification_note,
                   competition_note, policy_version, validated_at
              FROM claim_validation_decision
             WHERE id=%s
            """,
            (record_id,),
        ).fetchone()
        if row is None:
            return None
        record: Record = {
            "record_type": "claim_validation_decision",
            "id": record_id,
            "claim_id": row[0],
            "support_decision_id": row[1],
            "from_maturity": row[2],
            "to_maturity": row[3],
            "reason": row[4],
            "validated_by": row[5],
            "validation_basis": row[6],
            "validation_note": row[7],
            "evidence_ids": row[8],
            "supporting_evidence_ids": row[9],
            "refuting_evidence_ids": row[10],
            "qualifying_evidence_ids": row[11],
            "distinct_source_ids": row[12],
            "distinct_snapshot_ids": row[13],
            "review_flags": row[14],
            "competing_active_claim_ids": row[15],
            "independence_assessment": row[16],
            "policy_version": row[21],
            "validated_at": row[22].isoformat(),
        }
        optional = (
            "independence_note",
            "counterevidence_note",
            "qualification_note",
            "competition_note",
        )
        for field, value in zip(optional, row[17:21], strict=True):
            if value is not None:
                record[field] = value
        validate_claim_validation_decision(record)
        return record
