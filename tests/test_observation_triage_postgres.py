from __future__ import annotations

import os

import psycopg
import pytest

from kneekura_tech_hub.database import apply_migrations
from kneekura_tech_hub.observation_triage import (
    ObservationTriageError,
    transition_observation,
)
from kneekura_tech_hub.observation_triage_postgres import ObservationTriagePostgresRepository
from kneekura_tech_hub.service import CurationEngine


DSN = os.getenv("KTHUB_TEST_DATABASE_URL")
pytestmark = pytest.mark.skipif(not DSN, reason="KTHUB_TEST_DATABASE_URL is not set")
HUMAN = {"actor_type": "human", "actor_id": "triage-reviewer"}
AI = {"actor_type": "ai", "actor_id": "extractor", "version": "v1"}
TOOL = {"actor_type": "tool", "actor_id": "triage-tool", "version": "v1"}
SOURCE_ID = "src:triage:postgres"
SNAPSHOT_ID = "ss:triage:postgres"
EVIDENCE_ID = "ev:triage:postgres"
OBSERVATION_ID = "obs:triage:postgres"
ENTITY_ID = "ke:triage:incremental"


def _truncate(connection) -> None:
    connection.execute(
        """
        TRUNCATE TABLE
            observation_triage_decision,
            source_acquisition_commit,
            source_acquisition_execution,
            source_acquisition_authorization,
            source_selection_decision,
            review_decision,
            staged_observation_evidence,
            claim_evidence, claim, evidence_relation, evidence,
            source_snapshot, staged_observation, curation_event,
            entity_relation, entity_kind, entity_alias, knowledge_entity, source
        RESTART IDENTITY CASCADE
        """
    )


def _seed(repository: ObservationTriagePostgresRepository) -> CurationEngine:
    engine = CurationEngine(repository)
    engine.register_source(
        {
            "record_type": "source",
            "id": SOURCE_ID,
            "kind": "repository",
            "origin": {"provider": "fixture", "repository": "example/triage-postgres"},
            "acquisition": {"level": "selected-files"},
            "license": {"state": "KNOWN", "declared_expression": "MIT"},
        },
        actor=HUMAN,
    )
    engine.register_source_snapshot(
        {
            "record_type": "source_snapshot",
            "id": SNAPSHOT_ID,
            "source_id": SOURCE_ID,
            "revision": "0123456789abcdef0123456789abcdef01234567",
            "captured_at": "2026-09-09T00:00:00Z",
            "metadata": {"fixture": True},
        },
        actor=HUMAN,
    )
    engine.register_evidence(
        {
            "record_type": "evidence",
            "id": EVIDENCE_ID,
            "source_id": SOURCE_ID,
            "source_snapshot_id": SNAPSHOT_ID,
            "locator": {
                "type": "source_lines",
                "path": "README.md",
                "line_start": 2,
                "line_end": 2,
                "content_hash": "sha256:" + "a" * 64,
            },
            "roles": ["SUPPORTS"],
        },
        actor=HUMAN,
    )
    engine.create_entity(
        {
            "record_type": "knowledge_entity",
            "id": ENTITY_ID,
            "canonical_name": "Incremental recomputation",
            "aliases": [],
            "kinds": ["technique"],
            "abstraction_level": "L1",
            "identity_state": "CANONICAL",
            "relations": [],
        },
        actor=HUMAN,
        reason="triage promotion fixture target",
    )
    engine.stage_observation(
        {
            "record_type": "staged_observation",
            "id": OBSERVATION_ID,
            "source_id": SOURCE_ID,
            "evidence_candidate_ids": [EVIDENCE_ID],
            "summary": "The pinned source describes incremental recomputation.",
            "candidate_names": ["incremental recomputation"],
            "status": "NEW",
            "created_by": AI,
        },
        actor=AI,
    )
    return engine


def _claim_candidate(claim_id: str = "cl:triage:postgres") -> dict:
    return {
        "id": claim_id,
        "entity_id": ENTITY_ID,
        "claim_type": "DIRECT_OBSERVATION",
        "statement": "The pinned source describes incremental recomputation.",
    }


def _repository(connection) -> ObservationTriagePostgresRepository:
    return ObservationTriagePostgresRepository(connection)


def test_postgres_triage_promotes_only_to_candidate_and_inherits_exact_evidence() -> None:
    assert DSN is not None
    connection = psycopg.connect(DSN, autocommit=True)
    try:
        apply_migrations(connection)
        _truncate(connection)
        repository = _repository(connection)
        _seed(repository)

        first = transition_observation(
            repository,
            OBSERVATION_ID,
            "MARK_TRIAGED",
            reason="Evidence and candidate naming are coherent enough for human decision.",
            actor=TOOL,
            decision_id="otd:triage:postgres",
        )
        assert first["observation"]["status"] == "TRIAGED"
        assert first["claim_candidate"] is None

        promoted = transition_observation(
            repository,
            OBSERVATION_ID,
            "PROMOTE_TO_CLAIM_CANDIDATE",
            reason="Human accepts this as a Claim Candidate, not as validated knowledge.",
            actor=HUMAN,
            claim_candidate=_claim_candidate(),
            decision_id="otd:promote:postgres",
        )

        assert promoted["observation"]["status"] == "PROMOTED"
        claim = promoted["claim_candidate"]
        assert claim is not None
        assert claim["maturity"] == "CANDIDATE"
        assert claim["evidence_ids"] == [EVIDENCE_ID]
        assert claim["created_by"] == HUMAN
        assert repository.get(claim["id"]) == claim
        assert repository.get("otd:promote:postgres")["resulting_claim_id"] == claim["id"]
        assert len(repository.list("observation_triage_decision")) == 2
    finally:
        connection.close()


def test_ai_and_tool_cannot_cross_human_triage_authority() -> None:
    assert DSN is not None
    connection = psycopg.connect(DSN, autocommit=True)
    try:
        apply_migrations(connection)
        _truncate(connection)
        repository = _repository(connection)
        _seed(repository)

        with pytest.raises(ObservationTriageError, match="AI actors cannot"):
            transition_observation(
                repository,
                OBSERVATION_ID,
                "MARK_TRIAGED",
                reason="AI attempts lifecycle mutation.",
                actor=AI,
            )
        assert repository.get(OBSERVATION_ID)["status"] == "NEW"
        assert repository.list("observation_triage_decision") == []

        transition_observation(
            repository,
            OBSERVATION_ID,
            "MARK_TRIAGED",
            reason="Machine triage may perform bounded mechanical classification.",
            actor=TOOL,
            decision_id="otd:tool-triage",
        )

        with pytest.raises(ObservationTriageError, match="cannot perform"):
            transition_observation(
                repository,
                OBSERVATION_ID,
                "PROMOTE_TO_CLAIM_CANDIDATE",
                reason="Tool attempts promotion.",
                actor=TOOL,
                claim_candidate=_claim_candidate(),
            )
        assert repository.get(OBSERVATION_ID)["status"] == "TRIAGED"
        assert repository.list("claim") == []
        assert len(repository.list("observation_triage_decision")) == 1
    finally:
        connection.close()


def test_promotion_cannot_smuggle_maturity_or_evidence_ids() -> None:
    assert DSN is not None
    connection = psycopg.connect(DSN, autocommit=True)
    try:
        apply_migrations(connection)
        _truncate(connection)
        repository = _repository(connection)
        _seed(repository)
        transition_observation(
            repository,
            OBSERVATION_ID,
            "MARK_TRIAGED",
            reason="Ready for human review.",
            actor=HUMAN,
            decision_id="otd:pre-smuggle",
        )

        candidate = _claim_candidate("cl:smuggle")
        candidate["maturity"] = "VALIDATED"
        candidate["evidence_ids"] = ["ev:attacker-controlled"]
        with pytest.raises(ObservationTriageError, match="unsupported fields"):
            transition_observation(
                repository,
                OBSERVATION_ID,
                "PROMOTE_TO_CLAIM_CANDIDATE",
                reason="Attempt to smuggle authority and provenance.",
                actor=HUMAN,
                claim_candidate=candidate,
            )

        assert repository.get(OBSERVATION_ID)["status"] == "TRIAGED"
        assert repository.list("claim") == []
        assert len(repository.list("observation_triage_decision")) == 1
    finally:
        connection.close()


def test_direct_status_replace_without_decision_is_rejected_by_database() -> None:
    assert DSN is not None
    connection = psycopg.connect(DSN, autocommit=True)
    try:
        apply_migrations(connection)
        _truncate(connection)
        repository = _repository(connection)
        _seed(repository)

        observation = repository.get(OBSERVATION_ID)
        assert observation is not None
        observation["status"] = "REJECTED"
        with pytest.raises(psycopg.Error, match="requires matching triage decision"):
            repository.put(observation, replace=True)

        assert repository.get(OBSERVATION_ID)["status"] == "NEW"
        assert repository.list("observation_triage_decision") == []
    finally:
        connection.close()


def test_direct_decision_without_status_change_is_rejected_by_database() -> None:
    assert DSN is not None
    connection = psycopg.connect(DSN, autocommit=True)
    try:
        apply_migrations(connection)
        _truncate(connection)
        repository = _repository(connection)
        _seed(repository)

        decision = {
            "record_type": "observation_triage_decision",
            "id": "otd:orphaned-audit",
            "observation_id": OBSERVATION_ID,
            "action": "MARK_TRIAGED",
            "from_status": "NEW",
            "to_status": "TRIAGED",
            "reason": "Audit row without applying lifecycle state.",
            "created_by": HUMAN,
            "policy_version": "1.0.0",
            "decided_at": "2026-09-09T00:00:00Z",
        }
        with pytest.raises(psycopg.Error, match="is not applied"):
            repository.put(decision)

        assert repository.get(OBSERVATION_ID)["status"] == "NEW"
        assert repository.list("observation_triage_decision") == []
    finally:
        connection.close()


def test_database_rejects_direct_non_new_observation_insert() -> None:
    assert DSN is not None
    connection = psycopg.connect(DSN, autocommit=True)
    try:
        apply_migrations(connection)
        _truncate(connection)
        repository = _repository(connection)
        _seed(repository)

        observation = repository.get(OBSERVATION_ID)
        assert observation is not None
        observation["id"] = "obs:triage:smuggled-insert"
        observation["status"] = "PROMOTED"
        with pytest.raises(psycopg.Error, match="must start at NEW"):
            repository.put(observation)
        assert repository.get("obs:triage:smuggled-insert") is None
    finally:
        connection.close()


def test_failed_promotion_rolls_back_claim_event_status_and_decision() -> None:
    assert DSN is not None
    connection = psycopg.connect(DSN, autocommit=True)
    try:
        apply_migrations(connection)
        _truncate(connection)
        base_repository = _repository(connection)
        _seed(base_repository)
        transition_observation(
            base_repository,
            OBSERVATION_ID,
            "MARK_TRIAGED",
            reason="Ready for promotion rollback test.",
            actor=HUMAN,
            decision_id="otd:rollback-prep",
        )
        events_before = list(base_repository.list("curation_event"))

        class FailingDecisionRepository(ObservationTriagePostgresRepository):
            def put(self, record, *, replace=False):
                if (
                    record.get("record_type") == "observation_triage_decision"
                    and record.get("action") == "PROMOTE_TO_CLAIM_CANDIDATE"
                ):
                    raise RuntimeError("simulated triage decision persistence failure")
                return super().put(record, replace=replace)

        repository = FailingDecisionRepository(connection)
        with pytest.raises(RuntimeError, match="simulated triage decision"):
            transition_observation(
                repository,
                OBSERVATION_ID,
                "PROMOTE_TO_CLAIM_CANDIDATE",
                reason="This transaction must roll back completely.",
                actor=HUMAN,
                claim_candidate=_claim_candidate("cl:rollback"),
                decision_id="otd:rollback-fail",
            )

        assert base_repository.get(OBSERVATION_ID)["status"] == "TRIAGED"
        assert base_repository.get("cl:rollback") is None
        assert base_repository.get("otd:rollback-fail") is None
        assert base_repository.list("curation_event") == events_before
        assert [item["id"] for item in base_repository.list("observation_triage_decision")] == [
            "otd:rollback-prep"
        ]
    finally:
        connection.close()


def test_second_transition_from_same_observation_state_cannot_branch_history() -> None:
    assert DSN is not None
    connection = psycopg.connect(DSN, autocommit=True)
    try:
        apply_migrations(connection)
        _truncate(connection)
        repository = _repository(connection)
        _seed(repository)

        transition_observation(
            repository,
            OBSERVATION_ID,
            "REJECT",
            reason="Human rejects candidate after evidence review.",
            actor=HUMAN,
            decision_id="otd:first-terminal",
        )
        with pytest.raises(ObservationTriageError, match="invalid staged-observation transition"):
            transition_observation(
                repository,
                OBSERVATION_ID,
                "EXPIRE",
                reason="A second branch from the already consumed state is forbidden.",
                actor=HUMAN,
                decision_id="otd:second-terminal",
            )

        assert repository.get(OBSERVATION_ID)["status"] == "REJECTED"
        assert [item["id"] for item in repository.list("observation_triage_decision")] == [
            "otd:first-terminal"
        ]
    finally:
        connection.close()
