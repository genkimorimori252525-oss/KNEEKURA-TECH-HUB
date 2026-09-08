from copy import deepcopy
from datetime import datetime, timezone

import pytest

from kneekura_tech_hub.repository import MemoryRepository
from kneekura_tech_hub.review import ReviewError, review_claim, review_claims


NOW = datetime(2026, 9, 9, 0, 0, tzinfo=timezone.utc)


def _source(source_id: str) -> dict:
    return {
        "record_type": "source",
        "id": source_id,
        "kind": "repository",
        "origin": {"provider": "github", "repository": source_id},
        "acquisition": {"level": "snapshot"},
        "license": {"state": "KNOWN", "declared_expression": "MIT"},
    }


def _snapshot(snapshot_id: str, source_id: str) -> dict:
    return {
        "record_type": "source_snapshot",
        "id": snapshot_id,
        "source_id": source_id,
        "revision": snapshot_id,
        "captured_at": "2026-09-08T00:00:00Z",
    }


def _evidence(
    evidence_id: str,
    source_id: str,
    snapshot_id: str,
    *,
    roles: list[str],
    locator_type: str = "source_lines",
) -> dict:
    locator = {"type": locator_type}
    if locator_type == "source_lines":
        locator.update(
            {
                "path": "src/lib.rs",
                "line_start": 1,
                "line_end": 1,
                "content_hash": f"sha256:{evidence_id}",
            }
        )
    elif locator_type == "stable_url":
        locator["url"] = "https://example.invalid/evidence"
    return {
        "record_type": "evidence",
        "id": evidence_id,
        "source_id": source_id,
        "source_snapshot_id": snapshot_id,
        "locator": locator,
        "roles": roles,
    }


def _claim(
    claim_id: str,
    evidence_ids: list[str],
    *,
    maturity: str = "SUPPORTED",
    last_verified: str | None = None,
    verification_due_at: str | None = None,
) -> dict:
    record = {
        "record_type": "claim",
        "id": claim_id,
        "entity_id": "ke:test",
        "claim_type": "INFERENCE",
        "statement": claim_id,
        "maturity": maturity,
        "evidence_ids": evidence_ids,
        "confidence": "MEDIUM",
        "reasoning_basis": evidence_ids,
        "created_by": {"actor_type": "ai", "actor_id": "extractor"},
        "policy_version": "1.0.0",
    }
    if last_verified is not None:
        record["last_verified"] = last_verified
    if verification_due_at is not None:
        record["verification_due_at"] = verification_due_at
    return record


def _repository() -> MemoryRepository:
    repository = MemoryRepository()
    for record in (
        _source("src:a"),
        _source("src:b"),
        _snapshot("ss:a", "src:a"),
        _snapshot("ss:b", "src:b"),
        _evidence("ev:support-a", "src:a", "ss:a", roles=["SUPPORTS"]),
        _evidence(
            "ev:mixed-b",
            "src:b",
            "ss:b",
            roles=["SUPPORTS", "QUALIFIES"],
            locator_type="stable_url",
        ),
        _evidence("ev:refute-b", "src:b", "ss:b", roles=["REFUTES"]),
        _claim(
            "cl:review",
            ["ev:support-a", "ev:mixed-b", "ev:refute-b"],
            maturity="VALIDATED",
            last_verified="2026-08-01T00:00:00Z",
            verification_due_at="2026-09-01T00:00:00Z",
        ),
        _claim("cl:candidate", ["ev:support-a"], maturity="CANDIDATE"),
        _claim(
            "cl:fresh",
            ["ev:support-a"],
            maturity="VALIDATED",
            last_verified="2026-09-08T00:00:00Z",
            verification_due_at="2026-10-01T00:00:00Z",
        ),
    ):
        repository.put(record)
    return repository


def test_review_reports_dimensions_without_single_strength_score():
    repository = _repository()

    profile = review_claim(repository, "cl:review", now=NOW)

    assert "score" not in profile
    assert "strength" not in profile
    assert profile["claim_type"] == "INFERENCE"
    assert profile["maturity"] == "VALIDATED"
    assert profile["confidence"] == "MEDIUM"
    assert profile["evidence"]["count"] == 3
    assert profile["evidence"]["distinct_source_count"] == 2
    assert profile["evidence"]["distinct_snapshot_count"] == 2
    assert profile["evidence"]["role_counts"] == {
        "QUALIFIES": 1,
        "REFUTES": 1,
        "SUPPORTS": 2,
    }
    assert profile["evidence"]["locator_type_counts"] == {
        "source_lines": 2,
        "stable_url": 1,
    }
    assert profile["evidence"]["source_ids_by_role"]["SUPPORTS"] == ["src:a", "src:b"]
    assert profile["evidence"]["source_ids_by_role"]["REFUTES"] == ["src:b"]
    assert profile["verification"]["freshness"] == "DUE"
    assert "MULTIPLE_DISTINCT_SOURCES" in profile["flags"]
    assert "MULTIPLE_SNAPSHOTS" in profile["flags"]
    assert "HAS_REFUTING_EVIDENCE" in profile["flags"]
    assert "HAS_QUALIFYING_EVIDENCE" in profile["flags"]
    assert "VERIFICATION_DUE" in profile["flags"]


def test_review_is_read_only():
    repository = _repository()
    before = deepcopy(repository.list())

    review_claim(repository, "cl:review", now=NOW)
    review_claims(repository, now=NOW)

    assert repository.list() == before


def test_single_source_candidate_is_reported_without_calling_it_independent():
    profile = review_claim(_repository(), "cl:candidate", now=NOW)

    assert profile["evidence"]["distinct_source_count"] == 1
    assert profile["evidence"]["source_ids"] == ["src:a"]
    assert "SINGLE_SOURCE" in profile["flags"]
    assert profile["verification"]["freshness"] == "NEVER_VERIFIED"


def test_not_due_and_no_due_date_are_distinct_states():
    repository = _repository()
    fresh = review_claim(repository, "cl:fresh", now=NOW)
    candidate = review_claim(repository, "cl:candidate", now=NOW)

    assert fresh["verification"]["freshness"] == "NOT_DUE"
    assert candidate["verification"]["freshness"] == "NEVER_VERIFIED"


def test_needs_review_queue_uses_explicit_conditions_not_quality_score():
    repository = _repository()

    profiles = review_claims(repository, needs_review_only=True, now=NOW)

    assert [profile["claim_id"] for profile in profiles] == ["cl:candidate", "cl:review"]


def test_invalid_due_date_fails_closed():
    repository = _repository()
    broken = repository.get("cl:fresh")
    assert broken is not None
    broken["verification_due_at"] = "not-a-date"
    repository.put(broken, replace=True)

    with pytest.raises(ReviewError, match="invalid verification_due_at"):
        review_claim(repository, "cl:fresh", now=NOW)
