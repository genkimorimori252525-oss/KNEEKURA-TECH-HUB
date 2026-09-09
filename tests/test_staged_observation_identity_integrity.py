from __future__ import annotations

import os

import psycopg
import pytest

from kneekura_tech_hub.database import apply_migrations
from kneekura_tech_hub.observation_triage import transition_observation
from kneekura_tech_hub.postgres_repository import PostgresRepository
from kneekura_tech_hub.repository import MemoryRepository
from kneekura_tech_hub.service import CurationEngine


DSN = os.getenv("KTHUB_TEST_DATABASE_URL")
HUMAN = {"actor_type": "human", "actor_id": "observation-integrity-curator"}
AI = {"actor_type": "ai", "actor_id": "extractor", "version": "v1"}
TOOL = {"actor_type": "tool", "actor_id": "triage-tool", "version": "v1"}
SOURCE_ID = "src:observation:identity"
SNAPSHOT_ID = "ss:observation:identity"
EVIDENCE_A = "ev:observation:identity:a"
EVIDENCE_B = "ev:observation:identity:b"
OBSERVATION_ID = "obs:observation:identity"


def _source() -> dict:
    return {
        "record_type": "source",
        "id": SOURCE_ID,
        "kind": "repository",
        "origin": {"provider": "fixture", "repository": "example/observation-identity"},
        "acquisition": {"level": "selected-files"},
        "license": {"state": "KNOWN", "declared_expression": "MIT"},
    }


def _snapshot() -> dict:
    return {
        "record_type": "source_snapshot",
        "id": SNAPSHOT_ID,
        "source_id": SOURCE_ID,
        "revision": "0123456789abcdef0123456789abcdef01234567",
        "captured_at": "2026-09-09T00:00:00Z",
        "metadata": {"fixture": True},
    }


def _evidence(evidence_id: str, line: int) -> dict:
    return {
        "record_type": "evidence",
        "id": evidence_id,
        "source_id": SOURCE_ID,
        "source_snapshot_id": SNAPSHOT_ID,
        "locator": {
            "type": "source_lines",
            "path": "README.md",
            "line_start": line,
            "line_end": line,
            "content_hash": "sha256:" + ("a" if line == 1 else "b") * 64,
        },
        "roles": ["SUPPORTS"],
        "observed_at": f"2026-09-09T00:00:0{line}Z",
    }


def _observation() -> dict:
    return {
        "record_type": "staged_observation",
        "id": OBSERVATION_ID,
        "source_id": SOURCE_ID,
        "evidence_candidate_ids": [EVIDENCE_A],
        "summary": "The selected implementation uses incremental recomputation.",
        "candidate_names": ["incremental recomputation"],
        "status": "NEW",
        "created_by": AI,
    }


def _seed(repository) -> None:
    engine = CurationEngine(repository)
    engine.register_source(_source(), actor=HUMAN)
    engine.register_source_snapshot(_snapshot(), actor=HUMAN)
    engine.register_evidence(_evidence(EVIDENCE_A, 1), actor=HUMAN)
    engine.register_evidence(_evidence(EVIDENCE_B, 2), actor=HUMAN)
    engine.stage_observation(_observation(), actor=AI)


def test_memory_rejects_staged_observation_payload_substitution() -> None:
    repository = MemoryRepository()
    _seed(repository)
    original = repository.get(OBSERVATION_ID)
    assert original is not None

    attacks = [
        ("summary", "Rewritten meaning."),
        ("candidate_names", ["different concept"]),
        ("created_by", {"actor_type": "ai", "actor_id": "other", "version": "v1"}),
        ("evidence_candidate_ids", [EVIDENCE_B]),
    ]
    for field, value in attacks:
        mutated = repository.get(OBSERVATION_ID)
        assert mutated is not None
        mutated[field] = value
        with pytest.raises(ValueError, match="staged_observation identity payload is immutable"):
            repository.put(mutated, replace=True)
        assert repository.get(OBSERVATION_ID) == original

    # Identity integrity does not itself freeze lifecycle state. The governed
    # triage boundary remains responsible for status authority.
    status_only = repository.get(OBSERVATION_ID)
    assert status_only is not None
    status_only["status"] = "TRIAGED"
    repository.put(status_only, replace=True)
    assert repository.get(OBSERVATION_ID)["status"] == "TRIAGED"


@pytest.mark.skipif(not DSN, reason="KTHUB_TEST_DATABASE_URL is not set")
def test_postgres_rejects_payload_and_evidence_identity_substitution_but_allows_triage() -> None:
    assert DSN is not None
    with psycopg.connect(DSN, autocommit=True) as setup:
        apply_migrations(setup)
        setup.execute("TRUNCATE TABLE source, knowledge_entity RESTART IDENTITY CASCADE")

    repository = PostgresRepository.connect(DSN)
    try:
        _seed(repository)
        original = repository.get(OBSERVATION_ID)
        assert original is not None

        rewritten = repository.get(OBSERVATION_ID)
        assert rewritten is not None
        rewritten["summary"] = "Rewritten meaning."
        with pytest.raises(psycopg.Error, match="identity payload is immutable"):
            repository.put(rewritten, replace=True)

        relinked = repository.get(OBSERVATION_ID)
        assert relinked is not None
        relinked["evidence_candidate_ids"] = [EVIDENCE_B]
        with pytest.raises(psycopg.Error, match="Evidence identity is immutable"):
            repository.put(relinked, replace=True)

        with pytest.raises(psycopg.Error, match="identity payload is immutable"):
            repository.connection.execute(
                "UPDATE staged_observation SET summary='sql rewrite' WHERE id=%s",
                (OBSERVATION_ID,),
            )
        with pytest.raises(psycopg.Error, match="retained history"):
            repository.connection.execute(
                "DELETE FROM staged_observation WHERE id=%s",
                (OBSERVATION_ID,),
            )
        with pytest.raises(psycopg.Error, match="Evidence identity is immutable"):
            repository.connection.execute(
                "DELETE FROM staged_observation_evidence WHERE observation_id=%s AND evidence_id=%s",
                (OBSERVATION_ID, EVIDENCE_A),
            )
        with pytest.raises(psycopg.Error, match="evidence anchor is immutable"):
            repository.connection.execute(
                "UPDATE staged_observation_evidence_anchor SET evidence_ids=%s WHERE observation_id=%s",
                ([EVIDENCE_B], OBSERVATION_ID),
            )

        assert repository.get(OBSERVATION_ID) == original

        result = transition_observation(
            repository,
            OBSERVATION_ID,
            "MARK_TRIAGED",
            reason="The exact extracted payload is ready for review.",
            actor=TOOL,
        )
        triaged = result["observation"]
        assert triaged["status"] == "TRIAGED"
        for field in (
            "source_id",
            "summary",
            "candidate_names",
            "created_by",
            "evidence_candidate_ids",
        ):
            assert triaged[field] == original[field]
        decisions = repository.list("observation_triage_decision")
        assert len(decisions) == 1
        assert decisions[0]["observation_id"] == OBSERVATION_ID

        anchor = repository.connection.execute(
            "SELECT evidence_ids FROM staged_observation_evidence_anchor WHERE observation_id=%s",
            (OBSERVATION_ID,),
        ).fetchone()
        assert anchor is not None
        assert list(anchor[0]) == [EVIDENCE_A]
    finally:
        repository.close()
