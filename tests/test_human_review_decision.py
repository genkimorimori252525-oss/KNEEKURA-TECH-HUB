from __future__ import annotations

from copy import deepcopy

import pytest

from kneekura_tech_hub.decision import (
    DecisionError,
    HumanReviewDecisionEngine,
    active_review_decisions,
    review_decision_history,
)
from kneekura_tech_hub.repository import MemoryRepository
from kneekura_tech_hub.validator import HubValidationError, validate_record


HUMAN = {"actor_type": "human", "actor_id": "reviewer"}
AI = {"actor_type": "ai", "actor_id": "review-bot", "version": "test"}


def _claim(claim_id: str, entity_id: str = "ke:topic") -> dict:
    return {
        "record_type": "claim",
        "id": claim_id,
        "entity_id": entity_id,
        "claim_type": "JUDGMENT",
        "statement": f"statement for {claim_id}",
        "maturity": "CANDIDATE",
        "evidence_ids": [],
        "created_by": HUMAN,
        "policy_version": "1.0.0",
    }


def _repo() -> MemoryRepository:
    repo = MemoryRepository()
    repo.put(_claim("cl:a"))
    repo.put(_claim("cl:b"))
    return repo


def test_human_decision_is_append_only_and_does_not_mutate_claims():
    repo = _repo()
    before_a = deepcopy(repo.get("cl:a"))
    before_b = deepcopy(repo.get("cl:b"))

    record = HumanReviewDecisionEngine(repo).create_from_fields(
        decision_id="rd:first",
        source_claim_id="cl:a",
        target_claim_id="cl:b",
        decision="UNRESOLVED",
        rationale="The statements differ, but the current evidence does not prove contradiction.",
        actor=HUMAN,
    )

    assert record["id"] == "rd:first"
    assert record["decision"] == "UNRESOLVED"
    assert repo.get("cl:a") == before_a
    assert repo.get("cl:b") == before_b
    assert repo.get("rd:first") == record


def test_ai_cannot_create_human_review_decision():
    repo = _repo()
    with pytest.raises(DecisionError, match="human actor"):
        HumanReviewDecisionEngine(repo).create_from_fields(
            decision_id="rd:ai",
            source_claim_id="cl:a",
            target_claim_id="cl:b",
            decision="COMPATIBLE",
            rationale="AI must not be allowed to make this canonical human judgment.",
            actor=AI,
        )


def test_decision_cannot_cross_exact_claim_subjects():
    repo = _repo()
    repo.put(_claim("cl:other", "ke:other"))
    with pytest.raises(DecisionError, match="same exact subject"):
        HumanReviewDecisionEngine(repo).create_from_fields(
            decision_id="rd:cross",
            source_claim_id="cl:a",
            target_claim_id="cl:other",
            decision="CONTRADICTS",
            rationale="Cross-subject comparison is not a v1 human decision subject.",
            actor=HUMAN,
        )


def test_decision_revision_is_new_record_and_old_record_remains():
    repo = _repo()
    engine = HumanReviewDecisionEngine(repo)
    first = engine.create_from_fields(
        decision_id="rd:first",
        source_claim_id="cl:a",
        target_claim_id="cl:b",
        decision="UNRESOLVED",
        rationale="Need more review.",
        actor=HUMAN,
    )
    second = engine.create_from_fields(
        decision_id="rd:second",
        source_claim_id="cl:b",
        target_claim_id="cl:a",
        decision="COMPATIBLE",
        rationale="Human review found the statements can both hold under the same scope.",
        actor=HUMAN,
        supersedes_decision_id="rd:first",
    )

    assert repo.get("rd:first") == first
    assert repo.get("rd:second") == second
    assert [item["id"] for item in review_decision_history(repo)] == ["rd:first", "rd:second"]
    assert [item["id"] for item in active_review_decisions(repo)] == ["rd:second"]


def test_one_decision_cannot_have_two_superseding_successors():
    repo = _repo()
    engine = HumanReviewDecisionEngine(repo)
    engine.create_from_fields(
        decision_id="rd:first",
        source_claim_id="cl:a",
        target_claim_id="cl:b",
        decision="UNRESOLVED",
        rationale="Initial human review.",
        actor=HUMAN,
    )
    engine.create_from_fields(
        decision_id="rd:second",
        source_claim_id="cl:a",
        target_claim_id="cl:b",
        decision="COMPATIBLE",
        rationale="First correction.",
        actor=HUMAN,
        supersedes_decision_id="rd:first",
    )

    with pytest.raises(DecisionError, match="already has a superseding successor"):
        engine.create_from_fields(
            decision_id="rd:branch",
            source_claim_id="cl:a",
            target_claim_id="cl:b",
            decision="CONTRADICTS",
            rationale="A branching successor would make the active decision ambiguous.",
            actor=HUMAN,
            supersedes_decision_id="rd:first",
        )


def test_review_decision_schema_and_policy_reject_nonhuman_or_same_claim():
    base = {
        "record_type": "review_decision",
        "id": "rd:test",
        "source_claim_id": "cl:a",
        "target_claim_id": "cl:b",
        "decision": "UNRESOLVED",
        "rationale": "Human review remains unresolved.",
        "created_by": HUMAN,
        "policy_version": "1.0.0",
        "decided_at": "2026-09-09T00:00:00+00:00",
    }
    validate_record(base)

    nonhuman = deepcopy(base)
    nonhuman["id"] = "rd:ai"
    nonhuman["created_by"] = AI
    with pytest.raises(HubValidationError, match="human"):
        validate_record(nonhuman)

    same = deepcopy(base)
    same["id"] = "rd:same"
    same["target_claim_id"] = "cl:a"
    with pytest.raises(HubValidationError, match="different"):
        validate_record(same)


def test_decision_timestamp_must_be_timezone_aware():
    repo = _repo()
    record = {
        "record_type": "review_decision",
        "id": "rd:naive",
        "source_claim_id": "cl:a",
        "target_claim_id": "cl:b",
        "decision": "UNRESOLVED",
        "rationale": "Naive timestamps cannot establish an audit chronology.",
        "created_by": HUMAN,
        "policy_version": "1.0.0",
        "decided_at": "2026-09-09T00:00:00",
    }
    with pytest.raises(DecisionError, match="include timezone"):
        HumanReviewDecisionEngine(repo).create(record, actor=HUMAN)


def test_decision_history_orders_by_real_instant_not_iso_text():
    repo = _repo()
    repo.put(
        {
            "record_type": "review_decision",
            "id": "rd:later-text-earlier-time",
            "source_claim_id": "cl:a",
            "target_claim_id": "cl:b",
            "decision": "UNRESOLVED",
            "rationale": "Earlier instant expressed with a positive timezone offset.",
            "created_by": HUMAN,
            "policy_version": "1.0.0",
            "decided_at": "2026-09-09T09:00:00+09:00",
        }
    )
    repo.put(
        {
            "record_type": "review_decision",
            "id": "rd:earlier-text-later-time",
            "source_claim_id": "cl:a",
            "target_claim_id": "cl:b",
            "decision": "COMPATIBLE",
            "rationale": "Later instant expressed in UTC.",
            "created_by": HUMAN,
            "policy_version": "1.0.0",
            "decided_at": "2026-09-09T00:30:00+00:00",
        }
    )

    assert [item["id"] for item in review_decision_history(repo)] == [
        "rd:later-text-earlier-time",
        "rd:earlier-text-later-time",
    ]
