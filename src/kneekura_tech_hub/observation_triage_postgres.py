from __future__ import annotations

import psycopg
from psycopg.types.json import Jsonb

from .observation_triage import validate_observation_triage_decision
from .repository import DuplicateRecordError, Record
from .verified_commit_postgres import VerifiedCommitPostgresRepository


def _canonicalize_claim_defaults(record: Record) -> None:
    """Align valid Claim writes with the normalized PostgreSQL read shape.

    ``PostgresRepository._get_claim`` always materializes empty scope,
    applicability and alternative-interpretation containers. It also materializes
    an empty reasoning basis for non-INFERENCE claims. Triage promotion performs a
    strict write/read round-trip, so the write-side record must use that same
    canonical shape rather than treating omitted and empty fields as different.

    INFERENCE is deliberately excluded from the reasoning-basis default: its
    schema requires an explicit reasoning basis and confidence, and this helper
    must never manufacture the field needed to satisfy that epistemic gate.
    """

    record.setdefault("scope", {})
    record.setdefault("applicability", {})
    record.setdefault("alternative_interpretations", [])
    if record.get("claim_type") != "INFERENCE":
        record.setdefault("reasoning_basis", [])


class ObservationTriagePostgresRepository(VerifiedCommitPostgresRepository):
    """PostgreSQL extension for append-only observation triage decisions."""

    @classmethod
    def connect(cls, dsn: str) -> "ObservationTriagePostgresRepository":
        return cls(psycopg.connect(dsn, autocommit=True))

    def get(self, record_id: str) -> Record | None:
        if record_id.startswith("otd:"):
            return self._get_observation_triage_decision(record_id)
        return super().get(record_id)

    def put(self, record: Record, *, replace: bool = False) -> None:
        if record.get("record_type") == "claim":
            # CurationEngine validates the semantic record before this persistence
            # boundary. Normalizing optional containers here keeps the mutable
            # record and its durable round-trip representation identical.
            _canonicalize_claim_defaults(record)
            super().put(record, replace=replace)
            return
        if record.get("record_type") != "observation_triage_decision":
            super().put(record, replace=replace)
            return
        if replace:
            raise ValueError("observation triage decisions are append-only")
        validate_observation_triage_decision(record)
        with self.connection.transaction():
            if self.get(record["id"]) is not None:
                raise DuplicateRecordError(f"record already exists: {record['id']}")
            self.connection.execute(
                """
                INSERT INTO observation_triage_decision(
                    id, observation_id, action, from_status, to_status, reason,
                    created_by, resulting_claim_id, policy_version, decided_at
                ) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                """,
                (
                    record["id"],
                    record["observation_id"],
                    record["action"],
                    record["from_status"],
                    record["to_status"],
                    record["reason"],
                    Jsonb(record["created_by"]),
                    record.get("resulting_claim_id"),
                    record["policy_version"],
                    record["decided_at"],
                ),
            )

    def list(self, record_type: str | None = None) -> list[Record]:
        if record_type == "observation_triage_decision":
            return self._list_observation_triage_decisions()
        records = super().list(record_type)
        if record_type is None:
            records.extend(self._list_observation_triage_decisions())
        return records

    def lock_observation_for_triage(self, observation_id: str) -> None:
        row = self.connection.execute(
            "SELECT id FROM staged_observation WHERE id=%s FOR UPDATE",
            (observation_id,),
        ).fetchone()
        if row is None:
            raise ValueError(f"missing staged_observation: {observation_id}")

    def _list_observation_triage_decisions(self) -> list[Record]:
        records: list[Record] = []
        for (record_id,) in self.connection.execute(
            "SELECT id FROM observation_triage_decision ORDER BY decided_at, id"
        ).fetchall():
            record = self._get_observation_triage_decision(record_id)
            if record is not None:
                records.append(record)
        return records

    def _get_observation_triage_decision(self, record_id: str) -> Record | None:
        row = self.connection.execute(
            """
            SELECT observation_id, action, from_status, to_status, reason,
                   created_by, resulting_claim_id, policy_version, decided_at
            FROM observation_triage_decision WHERE id=%s
            """,
            (record_id,),
        ).fetchone()
        if row is None:
            return None
        record: Record = {
            "record_type": "observation_triage_decision",
            "id": record_id,
            "observation_id": row[0],
            "action": row[1],
            "from_status": row[2],
            "to_status": row[3],
            "reason": row[4],
            "created_by": row[5],
            "policy_version": row[7],
            "decided_at": row[8].isoformat(),
        }
        if row[6] is not None:
            record["resulting_claim_id"] = row[6]
        validate_observation_triage_decision(record)
        return record
