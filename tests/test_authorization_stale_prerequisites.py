from __future__ import annotations

import pytest

from kneekura_tech_hub.authorization import (
    AcquisitionAuthorizationEngine,
    AcquisitionAuthorizationError,
    authorization_effectiveness,
    authorized_acquisition_requests,
)
from kneekura_tech_hub.repository import MemoryRepository
from kneekura_tech_hub.selection import SourceSelectionEngine


HUMAN = {"actor_type": "human", "actor_id": "reviewer"}
SOURCE_ID = "src:github:example:stale-authorization"
SHA = "0123456789abcdef0123456789abcdef01234567"


def _authorized_repo():
    repository = MemoryRepository()
    repository.put(
        {
            "record_type": "source",
            "id": SOURCE_ID,
            "kind": "repository",
            "origin": {
                "provider": "github",
                "repository": "example/stale-authorization",
                "url": "https://github.com/example/stale-authorization",
            },
            "acquisition": {"level": "metadata-only"},
            "license": {
                "state": "KNOWN",
                "declared_expression": "MIT",
                "handling_policy": "REFERENCE_ONLY",
            },
        }
    )
    selection = SourceSelectionEngine(repository).create_from_fields(
        source_id=SOURCE_ID,
        decision="SELECT_FOR_REVIEW",
        rationale="Review exact pinned material.",
        actor=HUMAN,
        decision_id="sd:stale:selected",
    )
    AcquisitionAuthorizationEngine(repository).authorize_from_fields(
        source_id=SOURCE_ID,
        selection_decision_id=selection["id"],
        revision=SHA,
        allowed_paths=["README.md"],
        rationale="Exact README authorization.",
        actor=HUMAN,
        authorization_id="aa:stale:first",
    )
    return repository, selection


def test_selection_change_immediately_removes_effective_authority_before_explicit_revoke():
    repository, selection = _authorized_repo()
    assert authorization_effectiveness(repository, "aa:stale:first")["effective"] is True
    assert len(authorized_acquisition_requests(repository)) == 1

    SourceSelectionEngine(repository).create_from_fields(
        source_id=SOURCE_ID,
        decision="DEFER",
        rationale="New concern means execution must stop immediately.",
        actor=HUMAN,
        decision_id="sd:stale:defer",
        supersedes_decision_id=selection["id"],
    )

    status = authorization_effectiveness(repository, "aa:stale:first")
    assert status["effective"] is False
    assert "SELECTION_NO_LONGER_CURRENT" in status["blockers"]
    assert authorized_acquisition_requests(repository) == []

    # Historical grant remains auditable and can still be explicitly revoked.
    revoked = AcquisitionAuthorizationEngine(repository).revoke(
        "aa:stale:first",
        rationale="Record an explicit cancellation after the prerequisite became stale.",
        actor=HUMAN,
        revocation_id="aa:stale:revoke",
    )
    assert revoked["decision"] == "REVOKE"


def test_license_regression_invalidates_effective_authority_fail_closed():
    repository, _ = _authorized_repo()
    source = repository.get(SOURCE_ID)
    assert source is not None
    source["license"] = {
        "state": "REVIEW_REQUIRED",
        "declared_expression": None,
        "handling_policy": "DISCOVERY_METADATA_ONLY",
    }
    repository.put(source, replace=True)

    status = authorization_effectiveness(repository, "aa:stale:first")
    assert status["effective"] is False
    assert "LICENSE_NO_LONGER_RESOLVED" in status["blockers"]
    assert authorized_acquisition_requests(repository) == []


def test_reserved_repository_control_path_is_rejected():
    repository, selection = _authorized_repo()
    # Supersede the active grant explicitly so path validation is the relevant guard.
    with pytest.raises(AcquisitionAuthorizationError, match="repository control data"):
        AcquisitionAuthorizationEngine(repository).authorize_from_fields(
            source_id=SOURCE_ID,
            selection_decision_id=selection["id"],
            revision=SHA,
            allowed_paths=[".git/config"],
            rationale="Repository control data is not an allowed review target.",
            actor=HUMAN,
            authorization_id="aa:stale:git",
            supersedes_authorization_id="aa:stale:first",
        )
