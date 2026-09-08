from __future__ import annotations

from typing import Any, Callable

import psycopg
from psycopg.types.json import Jsonb

from .repository import DuplicateRecordError, Record


class PostgresRepository:
    """Normalized PostgreSQL persistence for KNEEKURA TECH HUB records."""

    _TABLE_BY_TYPE = {
        "knowledge_entity": "knowledge_entity",
        "source": "source",
        "source_snapshot": "source_snapshot",
        "evidence": "evidence",
        "claim": "claim",
        "staged_observation": "staged_observation",
        "review_decision": "review_decision",
        "curation_event": "curation_event",
    }

    def __init__(self, connection: psycopg.Connection[Any]) -> None:
        self.connection = connection

    @classmethod
    def connect(cls, dsn: str) -> "PostgresRepository":
        return cls(psycopg.connect(dsn, autocommit=True))

    def close(self) -> None:
        self.connection.close()

    def get(self, record_id: str) -> Record | None:
        getter: Callable[[str], Record | None] | None = {
            "ke": self._get_entity,
            "src": self._get_source,
            "ss": self._get_snapshot,
            "ev": self._get_evidence,
            "cl": self._get_claim,
            "obs": self._get_observation,
            "rd": self._get_review_decision,
            "ce": self._get_event,
        }.get(record_id.split(":", 1)[0])
        return getter(record_id) if getter else None

    def put(self, record: Record, *, replace: bool = False) -> None:
        handler = {
            "knowledge_entity": self._put_entity,
            "source": self._put_source,
            "source_snapshot": self._put_snapshot,
            "evidence": self._put_evidence,
            "claim": self._put_claim,
            "staged_observation": self._put_observation,
            "review_decision": self._put_review_decision,
            "curation_event": self._put_event,
        }.get(record["record_type"])
        if handler is None:
            raise ValueError(f"unsupported record_type: {record['record_type']}")

        with self.connection.transaction():
            if not replace and self.get(record["id"]) is not None:
                raise DuplicateRecordError(f"record already exists: {record['id']}")
            handler(record, replace=replace)

    def list(self, record_type: str | None = None) -> list[Record]:
        types = [record_type] if record_type else list(self._TABLE_BY_TYPE)
        records: list[Record] = []
        for item_type in types:
            table = self._TABLE_BY_TYPE.get(item_type)
            if table is None:
                continue
            for (record_id,) in self.connection.execute(
                f"SELECT id FROM {table} ORDER BY id"
            ).fetchall():
                record = self.get(record_id)
                if record is not None:
                    records.append(record)
        return records

    def _executemany(self, query: str, rows: list[tuple[Any, ...]]) -> None:
        if rows:
            with self.connection.cursor() as cursor:
                cursor.executemany(query, rows)

    @staticmethod
    def _iso(value: Any) -> str | None:
        return value.isoformat() if value is not None else None

    def _column(self, query: str, record_id: str) -> list[Any]:
        return [row[0] for row in self.connection.execute(query, (record_id,)).fetchall()]

    # ---- writes ---------------------------------------------------------

    def _put_entity(self, record: Record, *, replace: bool) -> None:
        if replace:
            self.connection.execute(
                """
                UPDATE knowledge_entity
                SET canonical_name=%s, abstraction_level=%s, identity_state=%s, redirect_to=%s
                WHERE id=%s
                """,
                (
                    record["canonical_name"],
                    record["abstraction_level"],
                    record["identity_state"],
                    record.get("redirect_to"),
                    record["id"],
                ),
            )
            self.connection.execute("DELETE FROM entity_alias WHERE entity_id=%s", (record["id"],))
            self.connection.execute("DELETE FROM entity_kind WHERE entity_id=%s", (record["id"],))
            self.connection.execute(
                "DELETE FROM entity_relation WHERE source_entity_id=%s", (record["id"],)
            )
        else:
            self.connection.execute(
                """
                INSERT INTO knowledge_entity(id, canonical_name, abstraction_level, identity_state, redirect_to)
                VALUES (%s,%s,%s,%s,%s)
                """,
                (
                    record["id"],
                    record["canonical_name"],
                    record["abstraction_level"],
                    record["identity_state"],
                    record.get("redirect_to"),
                ),
            )

        self._executemany(
            "INSERT INTO entity_alias(entity_id, alias) VALUES (%s,%s)",
            [(record["id"], alias) for alias in record.get("aliases", [])],
        )
        self._executemany(
            "INSERT INTO entity_kind(entity_id, kind) VALUES (%s,%s)",
            [(record["id"], kind) for kind in record.get("kinds", [])],
        )
        self._executemany(
            """
            INSERT INTO entity_relation(source_entity_id, relation_type, target_entity_id)
            VALUES (%s,%s,%s)
            """,
            [
                (record["id"], relation["type"], relation["target"])
                for relation in record.get("relations", [])
            ],
        )

    def _put_source(self, record: Record, *, replace: bool) -> None:
        params = (
            record["kind"],
            Jsonb(record["origin"]),
            Jsonb(record["license"]),
            record["acquisition"]["level"],
            record["id"],
        )
        if replace:
            self.connection.execute(
                """
                UPDATE source SET kind=%s, origin=%s, license=%s, acquisition_level=%s
                WHERE id=%s
                """,
                params,
            )
        else:
            self.connection.execute(
                """
                INSERT INTO source(kind, origin, license, acquisition_level, id)
                VALUES (%s,%s,%s,%s,%s)
                """,
                params,
            )

    def _put_snapshot(self, record: Record, *, replace: bool) -> None:
        params = (
            record["source_id"],
            record.get("revision"),
            record.get("tree_hash"),
            record.get("content_hash"),
            record.get("swhid"),
            record["captured_at"],
            Jsonb(record.get("metadata", {})),
            record["id"],
        )
        if replace:
            self.connection.execute(
                """
                UPDATE source_snapshot
                SET source_id=%s, revision=%s, tree_hash=%s, content_hash=%s,
                    swhid=%s, captured_at=%s, metadata=%s
                WHERE id=%s
                """,
                params,
            )
        else:
            self.connection.execute(
                """
                INSERT INTO source_snapshot(
                    source_id, revision, tree_hash, content_hash, swhid, captured_at, metadata, id
                ) VALUES (%s,%s,%s,%s,%s,%s,%s,%s)
                """,
                params,
            )

    def _put_evidence(self, record: Record, *, replace: bool) -> None:
        params = (
            record["source_id"],
            record["source_snapshot_id"],
            Jsonb(record["locator"]),
            record["roles"],
            record.get("observed_at"),
            record["id"],
        )
        if replace:
            self.connection.execute(
                """
                UPDATE evidence
                SET source_id=%s, source_snapshot_id=%s, locator=%s, roles=%s,
                    observed_at=COALESCE(%s, observed_at)
                WHERE id=%s
                """,
                params,
            )
        else:
            self.connection.execute(
                """
                INSERT INTO evidence(source_id, source_snapshot_id, locator, roles, observed_at, id)
                VALUES (%s,%s,%s,%s,COALESCE(%s, now()),%s)
                """,
                params,
            )

    def _put_claim(self, record: Record, *, replace: bool) -> None:
        relation = record.get("relation") or {}
        params = (
            record.get("entity_id"),
            relation.get("source_entity_id"),
            relation.get("relation_type"),
            relation.get("target_entity_id"),
            record["claim_type"],
            record["statement"],
            record["maturity"],
            Jsonb(record.get("scope", {})),
            Jsonb(record.get("applicability", {})),
            record.get("confidence"),
            Jsonb(record.get("reasoning_basis", [])),
            Jsonb(record.get("alternative_interpretations", [])),
            record.get("first_observed"),
            record.get("last_verified"),
            record.get("verification_due_at"),
            record.get("superseded_by"),
            Jsonb(record["created_by"]),
            record["policy_version"],
            record["id"],
        )
        if replace:
            self.connection.execute(
                """
                UPDATE claim
                SET entity_id=%s,
                    relation_source_entity_id=%s, relation_type=%s, relation_target_entity_id=%s,
                    claim_type=%s, statement=%s, maturity=%s, scope=%s, applicability=%s,
                    confidence=%s, reasoning_basis=%s, alternative_interpretations=%s,
                    first_observed=%s, last_verified=%s, verification_due_at=%s,
                    superseded_by=%s, created_by=%s, policy_version=%s
                WHERE id=%s
                """,
                params,
            )
            self.connection.execute("DELETE FROM claim_evidence WHERE claim_id=%s", (record["id"],))
        else:
            self.connection.execute(
                """
                INSERT INTO claim(
                    entity_id, relation_source_entity_id, relation_type, relation_target_entity_id,
                    claim_type, statement, maturity, scope, applicability, confidence,
                    reasoning_basis, alternative_interpretations, first_observed, last_verified,
                    verification_due_at, superseded_by, created_by, policy_version, id
                ) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                """,
                params,
            )
        self._executemany(
            "INSERT INTO claim_evidence(claim_id, evidence_id) VALUES (%s,%s)",
            [(record["id"], evidence_id) for evidence_id in record.get("evidence_ids", [])],
        )

    def _put_observation(self, record: Record, *, replace: bool) -> None:
        params = (
            record["source_id"],
            record["summary"],
            Jsonb(record.get("candidate_names", [])),
            record["status"],
            Jsonb(record["created_by"]),
            record["id"],
        )
        if replace:
            self.connection.execute(
                """
                UPDATE staged_observation
                SET source_id=%s, summary=%s, candidate_names=%s, status=%s, created_by=%s
                WHERE id=%s
                """,
                params,
            )
            self.connection.execute(
                "DELETE FROM staged_observation_evidence WHERE observation_id=%s",
                (record["id"],),
            )
        else:
            self.connection.execute(
                """
                INSERT INTO staged_observation(source_id, summary, candidate_names, status, created_by, id)
                VALUES (%s,%s,%s,%s,%s,%s)
                """,
                params,
            )
        self._executemany(
            "INSERT INTO staged_observation_evidence(observation_id, evidence_id) VALUES (%s,%s)",
            [(record["id"], evidence_id) for evidence_id in record.get("evidence_candidate_ids", [])],
        )

    def _put_review_decision(self, record: Record, *, replace: bool) -> None:
        if replace:
            raise ValueError("review decisions are append-only")
        self.connection.execute(
            """
            INSERT INTO review_decision(
                source_claim_id, target_claim_id, decision, rationale, created_by,
                policy_version, decided_at, supersedes_decision_id, id
            ) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)
            """,
            (
                record["source_claim_id"],
                record["target_claim_id"],
                record["decision"],
                record["rationale"],
                Jsonb(record["created_by"]),
                record["policy_version"],
                record["decided_at"],
                record.get("supersedes_decision_id"),
                record["id"],
            ),
        )

    def _put_event(self, record: Record, *, replace: bool) -> None:
        if replace:
            raise ValueError("curation events are append-only")
        self.connection.execute(
            """
            INSERT INTO curation_event(
                operation, actor, subject_ids, reason, policy_version, occurred_at, reversible, id
            ) VALUES (%s,%s,%s,%s,%s,%s,%s,%s)
            """,
            (
                record["operation"],
                Jsonb(record["actor"]),
                Jsonb(record.get("subject_ids", [])),
                record.get("reason"),
                record["policy_version"],
                record["occurred_at"],
                record.get("reversible", False),
                record["id"],
            ),
        )

    # ---- reads ----------------------------------------------------------

    def _get_entity(self, record_id: str) -> Record | None:
        row = self.connection.execute(
            """
            SELECT canonical_name, abstraction_level, identity_state, redirect_to
            FROM knowledge_entity WHERE id=%s
            """,
            (record_id,),
        ).fetchone()
        if row is None:
            return None
        relations = self.connection.execute(
            """
            SELECT relation_type, target_entity_id
            FROM entity_relation WHERE source_entity_id=%s
            ORDER BY relation_type, target_entity_id
            """,
            (record_id,),
        ).fetchall()
        record: Record = {
            "record_type": "knowledge_entity",
            "id": record_id,
            "canonical_name": row[0],
            "aliases": self._column(
                "SELECT alias FROM entity_alias WHERE entity_id=%s ORDER BY alias", record_id
            ),
            "kinds": self._column(
                "SELECT kind FROM entity_kind WHERE entity_id=%s ORDER BY kind", record_id
            ),
            "abstraction_level": row[1],
            "identity_state": row[2],
            "relations": [{"type": item[0], "target": item[1]} for item in relations],
        }
        if row[3] is not None:
            record["redirect_to"] = row[3]
        return record

    def _get_source(self, record_id: str) -> Record | None:
        row = self.connection.execute(
            "SELECT kind, origin, license, acquisition_level FROM source WHERE id=%s",
            (record_id,),
        ).fetchone()
        if row is None:
            return None
        return {
            "record_type": "source",
            "id": record_id,
            "kind": row[0],
            "origin": row[1],
            "license": row[2],
            "acquisition": {"level": row[3]},
        }

    def _get_snapshot(self, record_id: str) -> Record | None:
        row = self.connection.execute(
            """
            SELECT source_id, revision, tree_hash, content_hash, swhid, captured_at, metadata
            FROM source_snapshot WHERE id=%s
            """,
            (record_id,),
        ).fetchone()
        if row is None:
            return None
        record: Record = {
            "record_type": "source_snapshot",
            "id": record_id,
            "source_id": row[0],
            "captured_at": row[5].isoformat(),
            "metadata": row[6],
        }
        for key, value in zip(("revision", "tree_hash", "content_hash", "swhid"), row[1:5]):
            if value is not None:
                record[key] = value
        return record

    def _get_evidence(self, record_id: str) -> Record | None:
        row = self.connection.execute(
            """
            SELECT source_id, source_snapshot_id, locator, roles, observed_at
            FROM evidence WHERE id=%s
            """,
            (record_id,),
        ).fetchone()
        if row is None:
            return None
        return {
            "record_type": "evidence",
            "id": record_id,
            "source_id": row[0],
            "source_snapshot_id": row[1],
            "locator": row[2],
            "roles": list(row[3]),
            "observed_at": row[4].isoformat(),
        }

    def _get_claim(self, record_id: str) -> Record | None:
        row = self.connection.execute(
            """
            SELECT entity_id, relation_source_entity_id, relation_type, relation_target_entity_id,
                   claim_type, statement, maturity, scope, applicability, confidence,
                   reasoning_basis, alternative_interpretations, first_observed, last_verified,
                   verification_due_at, superseded_by, created_by, policy_version
            FROM claim WHERE id=%s
            """,
            (record_id,),
        ).fetchone()
        if row is None:
            return None

        record: Record = {
            "record_type": "claim",
            "id": record_id,
            "claim_type": row[4],
            "statement": row[5],
            "maturity": row[6],
            "evidence_ids": self._column(
                "SELECT evidence_id FROM claim_evidence WHERE claim_id=%s ORDER BY evidence_id",
                record_id,
            ),
            "scope": row[7],
            "applicability": row[8],
            "reasoning_basis": row[10],
            "alternative_interpretations": row[11],
            "created_by": row[16],
            "policy_version": row[17],
        }
        if row[0] is not None:
            record["entity_id"] = row[0]
        else:
            record["relation"] = {
                "source_entity_id": row[1],
                "relation_type": row[2],
                "target_entity_id": row[3],
            }

        optional = {
            "confidence": row[9],
            "first_observed": self._iso(row[12]),
            "last_verified": self._iso(row[13]),
            "verification_due_at": self._iso(row[14]),
            "superseded_by": row[15],
        }
        record.update({key: value for key, value in optional.items() if value is not None})
        return record

    def _get_observation(self, record_id: str) -> Record | None:
        row = self.connection.execute(
            """
            SELECT source_id, summary, candidate_names, status, created_by
            FROM staged_observation WHERE id=%s
            """,
            (record_id,),
        ).fetchone()
        if row is None:
            return None
        return {
            "record_type": "staged_observation",
            "id": record_id,
            "source_id": row[0],
            "evidence_candidate_ids": self._column(
                """
                SELECT evidence_id FROM staged_observation_evidence
                WHERE observation_id=%s ORDER BY evidence_id
                """,
                record_id,
            ),
            "summary": row[1],
            "candidate_names": row[2],
            "status": row[3],
            "created_by": row[4],
        }

    def _get_review_decision(self, record_id: str) -> Record | None:
        row = self.connection.execute(
            """
            SELECT source_claim_id, target_claim_id, decision, rationale, created_by,
                   policy_version, decided_at, supersedes_decision_id
            FROM review_decision WHERE id=%s
            """,
            (record_id,),
        ).fetchone()
        if row is None:
            return None
        record: Record = {
            "record_type": "review_decision",
            "id": record_id,
            "source_claim_id": row[0],
            "target_claim_id": row[1],
            "decision": row[2],
            "rationale": row[3],
            "created_by": row[4],
            "policy_version": row[5],
            "decided_at": row[6].isoformat(),
        }
        if row[7] is not None:
            record["supersedes_decision_id"] = row[7]
        return record

    def _get_event(self, record_id: str) -> Record | None:
        row = self.connection.execute(
            """
            SELECT operation, actor, subject_ids, reason, policy_version, occurred_at, reversible
            FROM curation_event WHERE id=%s
            """,
            (record_id,),
        ).fetchone()
        if row is None:
            return None
        return {
            "record_type": "curation_event",
            "id": record_id,
            "operation": row[0],
            "actor": row[1],
            "subject_ids": row[2],
            "reason": row[3],
            "policy_version": row[4],
            "occurred_at": row[5].isoformat(),
            "reversible": row[6],
        }
