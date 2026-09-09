from __future__ import annotations

import pytest

from kneekura_tech_hub.authorization import (
    AcquisitionAuthorizationEngine,
    AcquisitionAuthorizationError,
    authorization_effectiveness,
)
from kneekura_tech_hub.repository import MemoryRepository
from kneekura_tech_hub.selection import SourceSelectionEngine


HUMAN = {"actor_type": "human", "actor_id": "refresh-reviewer"}
SOURCE_ID = "src:github:example:refresh-unit"
REV1 = "1111111111111111111111111111111111111111"
REV2 = "2222222222222222222222222222222222222222"


def _repository() -> tuple[MemoryRepository, dict]:
    repository = MemoryRepository()
    repository.put(
        {
            "record_type": "source",
            "id": SOURCE_ID,
            "kind": "repository",
            "origin": {
                "provider": "github",
                "repository": "example/refresh-unit",
                "url": "https://github.com/example/refresh-unit",
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
        rationale="Human selects the Source for bounded refresh tests.",
        actor=HUMAN,
        decision_id="sd:refresh-unit",
    )
    return repository, selection


def _mark_committed(repository: MemoryRepository, authorization_id: str, revision: str, suffix: str) -> None:
    snapshot_id = f"ss:refresh-unit:{suffix}"
    repository.put(
        {
            "record_type": "source_snapshot",
            "id": snapshot_id,
            "source_id": SOURCE_ID,
            "revision": revision,
            "captured_at": "2026-09-10T00:00:00Z",
            "metadata": {"acquisition_level": "selected-files"},
        }
    )
    repository.put(
        {
            "record_type": "source_acquisition_commit",
            "id": f"vc:refresh-unit:{suffix}",
            "execution_id": f"ax:refresh-unit:{suffix}",
            "authorization_id": authorization_id,
            "source_id": SOURCE_ID,
            "snapshot_id": snapshot_id,
            "revision": revision,
            "acquisition_level": "selected-files",
            "manifest_sha256": "a" * 64,
            "source_fingerprint_sha256": "b" * 64,
            "authorization_fingerprint_sha256": "c" * 64,
            "committed_by": {"actor_type": "tool", "actor_id": "refresh-unit-commit", "version": "v1"},
            "policy_version": "1.0.0",
            "committed_at": "2026-09-10T00:00:00Z",
        }
    )
    source = repository.get(SOURCE_ID)
    assert source is not None
    source["acquisition"] = {"level": "selected-files"}
    repository.put(source, replace=True)


def test_committed_initial_grant_is_consumed_but_can_be_explicitly_superseded_for_refresh() -> None:
    repository, selection = _repository()
    engine = AcquisitionAuthorizationEngine(repository)
    first = engine.authorize_from_fields(
        source_id=SOURCE_ID,
        selection_decision_id=selection["id"],
        revision=REV1,
        allowed_paths=["README.md"],
        rationale="Initial exact selected-file grant.",
        actor=HUMAN,
        authorization_id="aa:refresh-unit:v1",
    )
    _mark_committed(repository, first["id"], REV1, "v1")

    consumed = authorization_effectiveness(repository, first["id"])
    assert consumed["effective"] is False
    assert "AUTHORIZATION_ALREADY_COMMITTED" in consumed["blockers"]
    assert "SOURCE_NO_LONGER_METADATA_ONLY" in consumed["blockers"]

    second = engine.authorize_from_fields(
        source_id=SOURCE_ID,
        selection_decision_id=selection["id"],
        revision=REV2,
        allowed_paths=["README.md"],
        rationale="Fresh human authority for the newer exact revision.",
        actor=HUMAN,
        authorization_id="aa:refresh-unit:v2",
        supersedes_authorization_id=first["id"],
    )
    assert second["supersedes_authorization_id"] == first["id"]
    assert authorization_effectiveness(repository, second["id"])["effective"] is True

    _mark_committed(repository, second["id"], REV2, "v2")
    consumed_refresh = authorization_effectiveness(repository, second["id"])
    assert consumed_refresh["effective"] is False
    assert consumed_refresh["blockers"] == ["AUTHORIZATION_ALREADY_COMMITTED"]


def test_selected_files_refresh_requires_verified_commit_proof_for_predecessor() -> None:
    repository, selection = _repository()
    engine = AcquisitionAuthorizationEngine(repository)
    first = engine.authorize_from_fields(
        source_id=SOURCE_ID,
        selection_decision_id=selection["id"],
        revision=REV1,
        allowed_paths=["README.md"],
        rationale="Initial exact selected-file grant.",
        actor=HUMAN,
        authorization_id="aa:refresh-unit:uncommitted",
    )

    source = repository.get(SOURCE_ID)
    assert source is not None
    source["acquisition"] = {"level": "selected-files"}
    repository.put(source, replace=True)

    with pytest.raises(AcquisitionAuthorizationError, match="verified acquisition commit"):
        engine.authorize_from_fields(
            source_id=SOURCE_ID,
            selection_decision_id=selection["id"],
            revision=REV2,
            allowed_paths=["README.md"],
            rationale="Must fail without append-only proof that the predecessor was consumed.",
            actor=HUMAN,
            authorization_id="aa:refresh-unit:forbidden",
            supersedes_authorization_id=first["id"],
        )
