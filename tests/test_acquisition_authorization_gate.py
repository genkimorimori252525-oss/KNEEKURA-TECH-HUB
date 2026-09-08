from __future__ import annotations

import pytest

from kneekura_tech_hub.authorization import (
    AcquisitionAuthorizationEngine,
    AcquisitionAuthorizationError,
    acquisition_authorization_history,
    active_acquisition_authorizations,
    authorized_acquisition_requests,
)
from kneekura_tech_hub.repository import MemoryRepository
from kneekura_tech_hub.selection import SourceSelectionEngine


HUMAN = {"actor_type": "human", "actor_id": "reviewer"}
AI = {"actor_type": "ai", "actor_id": "scanner", "version": "1.0"}
SHA = "0123456789abcdef0123456789abcdef01234567"
SOURCE_ID = "src:github:example:repo"


def _source(*, license_state: str = "KNOWN", expression: str | None = "MIT") -> dict:
    return {
        "record_type": "source",
        "id": SOURCE_ID,
        "kind": "repository",
        "origin": {
            "provider": "github",
            "repository": "example/repo",
            "url": "https://github.com/example/repo",
        },
        "acquisition": {"level": "metadata-only"},
        "license": {
            "state": license_state,
            "declared_expression": expression,
            "handling_policy": "REFERENCE_ONLY",
        },
    }


def _selected_repo(*, license_state: str = "KNOWN", expression: str | None = "MIT"):
    repository = MemoryRepository()
    repository.put(_source(license_state=license_state, expression=expression))
    selection = SourceSelectionEngine(repository).create_from_fields(
        source_id=SOURCE_ID,
        decision="SELECT_FOR_REVIEW",
        rationale="Manual review found a bounded deeper look worthwhile.",
        actor=HUMAN,
        decision_id="sd:selected",
    )
    return repository, selection


def test_authorize_exact_selected_files_without_mutating_source():
    repository, selection = _selected_repo()
    before = repository.get(SOURCE_ID)
    engine = AcquisitionAuthorizationEngine(repository)

    authorization = engine.authorize_from_fields(
        source_id=SOURCE_ID,
        selection_decision_id=selection["id"],
        revision=SHA,
        allowed_paths=["README.md", "src/lib.rs"],
        rationale="Only these pinned files are required for architecture review.",
        actor=HUMAN,
        authorization_id="aa:first",
    )

    assert authorization["decision"] == "AUTHORIZE"
    assert authorization["acquisition_level"] == "selected-files"
    assert repository.get(SOURCE_ID) == before
    assert repository.get(SOURCE_ID)["acquisition"] == {"level": "metadata-only"}
    assert [item["id"] for item in active_acquisition_authorizations(repository)] == ["aa:first"]
    requests = authorized_acquisition_requests(repository)
    assert requests[0]["authorization"]["id"] == "aa:first"
    assert requests[0]["source"] == before


def test_ai_cannot_authorize_and_selection_is_mandatory():
    repository, selection = _selected_repo()
    engine = AcquisitionAuthorizationEngine(repository)

    with pytest.raises(AcquisitionAuthorizationError, match="human actor"):
        engine.authorize_from_fields(
            source_id=SOURCE_ID,
            selection_decision_id=selection["id"],
            revision=SHA,
            allowed_paths=["README.md"],
            rationale="AI attempted authorization.",
            actor=AI,
        )

    no_selection = MemoryRepository()
    no_selection.put(_source())
    no_selection.put(
        {
            "record_type": "source_selection_decision",
            "id": "sd:deferred",
            "source_id": SOURCE_ID,
            "decision": "DEFER",
            "rationale": "Not selected yet.",
            "created_by": HUMAN,
            "policy_version": "1.0.0",
            "decided_at": "2026-09-09T00:00:00Z",
        }
    )
    with pytest.raises(AcquisitionAuthorizationError, match="SELECT_FOR_REVIEW"):
        AcquisitionAuthorizationEngine(no_selection).authorize_from_fields(
            source_id=SOURCE_ID,
            selection_decision_id="sd:deferred",
            revision=SHA,
            allowed_paths=["README.md"],
            rationale="Must not bypass selection.",
            actor=HUMAN,
        )


def test_authorize_requires_resolved_declared_license():
    for state, expression in [
        ("REVIEW_REQUIRED", None),
        ("UNKNOWN", None),
        ("KNOWN", None),
        ("KNOWN", ""),
    ]:
        repository, selection = _selected_repo(license_state=state, expression=expression)
        with pytest.raises(AcquisitionAuthorizationError, match="license.state=KNOWN"):
            AcquisitionAuthorizationEngine(repository).authorize_from_fields(
                source_id=SOURCE_ID,
                selection_decision_id=selection["id"],
                revision=SHA,
                allowed_paths=["README.md"],
                rationale="Unresolved licensing must block deeper authorization.",
                actor=HUMAN,
            )


def test_github_authorization_requires_full_commit_sha_and_safe_relative_paths():
    repository, selection = _selected_repo()
    engine = AcquisitionAuthorizationEngine(repository)

    for bad_revision in ["main", "latest", "0123456", SHA.upper()]:
        with pytest.raises(AcquisitionAuthorizationError, match="40-hex commit SHA"):
            engine.authorize_from_fields(
                source_id=SOURCE_ID,
                selection_decision_id=selection["id"],
                revision=bad_revision,
                allowed_paths=["README.md"],
                rationale="Moving or non-canonical revisions are forbidden.",
                actor=HUMAN,
            )

    for bad_path in ["/README.md", "../README.md", "src/../README.md", "src\\lib.rs", "C:/repo/x"]:
        with pytest.raises(AcquisitionAuthorizationError, match="allowed_paths"):
            engine.authorize_from_fields(
                source_id=SOURCE_ID,
                selection_decision_id=selection["id"],
                revision=SHA,
                allowed_paths=[bad_path],
                rationale="Unsafe paths are forbidden.",
                actor=HUMAN,
            )


def test_scope_change_requires_explicit_supersession():
    repository, selection = _selected_repo()
    engine = AcquisitionAuthorizationEngine(repository)
    engine.authorize_from_fields(
        source_id=SOURCE_ID,
        selection_decision_id=selection["id"],
        revision=SHA,
        allowed_paths=["README.md"],
        rationale="Initial exact scope.",
        actor=HUMAN,
        authorization_id="aa:first",
    )

    with pytest.raises(AcquisitionAuthorizationError, match="supersede it explicitly"):
        engine.authorize_from_fields(
            source_id=SOURCE_ID,
            selection_decision_id=selection["id"],
            revision=SHA,
            allowed_paths=["README.md", "src/lib.rs"],
            rationale="Parallel authority must not be created.",
            actor=HUMAN,
            authorization_id="aa:parallel",
        )

    second = engine.authorize_from_fields(
        source_id=SOURCE_ID,
        selection_decision_id=selection["id"],
        revision=SHA,
        allowed_paths=["README.md", "src/lib.rs"],
        rationale="Explicitly replace the old bounded scope.",
        actor=HUMAN,
        authorization_id="aa:second",
        supersedes_authorization_id="aa:first",
    )
    assert second["supersedes_authorization_id"] == "aa:first"
    assert [item["id"] for item in acquisition_authorization_history(repository)] == [
        "aa:first",
        "aa:second",
    ]
    assert [item["id"] for item in active_acquisition_authorizations(repository)] == ["aa:second"]


def test_revoke_remains_possible_after_selection_is_deferred():
    repository, selection = _selected_repo()
    engine = AcquisitionAuthorizationEngine(repository)
    before = repository.get(SOURCE_ID)
    engine.authorize_from_fields(
        source_id=SOURCE_ID,
        selection_decision_id=selection["id"],
        revision=SHA,
        allowed_paths=["README.md"],
        rationale="Authorize exact README at pinned revision.",
        actor=HUMAN,
        authorization_id="aa:first",
    )

    SourceSelectionEngine(repository).create_from_fields(
        source_id=SOURCE_ID,
        decision="DEFER",
        rationale="New concern means further review should pause.",
        actor=HUMAN,
        decision_id="sd:defer",
        supersedes_decision_id=selection["id"],
    )

    revoked = engine.revoke(
        "aa:first",
        rationale="Revoke previously granted scope immediately.",
        actor=HUMAN,
        revocation_id="aa:revoke",
    )
    assert revoked["decision"] == "REVOKE"
    assert revoked["supersedes_authorization_id"] == "aa:first"
    assert authorized_acquisition_requests(repository) == []
    assert [item["id"] for item in active_acquisition_authorizations(repository)] == ["aa:revoke"]
    assert repository.get(SOURCE_ID) == before


def test_revoke_must_copy_exact_previous_scope():
    repository, selection = _selected_repo()
    engine = AcquisitionAuthorizationEngine(repository)
    first = engine.authorize_from_fields(
        source_id=SOURCE_ID,
        selection_decision_id=selection["id"],
        revision=SHA,
        allowed_paths=["README.md"],
        rationale="Initial authorization.",
        actor=HUMAN,
        authorization_id="aa:first",
    )

    forged = dict(first)
    forged.update(
        {
            "id": "aa:forged-revoke",
            "decision": "REVOKE",
            "allowed_paths": ["src/lib.rs"],
            "rationale": "Attempt to revoke a different scope.",
            "supersedes_authorization_id": "aa:first",
        }
    )
    with pytest.raises(AcquisitionAuthorizationError, match="exact authorized scope"):
        engine.create(forged, actor=HUMAN)
