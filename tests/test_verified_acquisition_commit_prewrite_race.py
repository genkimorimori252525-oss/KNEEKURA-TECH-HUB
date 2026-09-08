from __future__ import annotations

from hashlib import sha1
import os
from pathlib import Path

import psycopg
import pytest

from kneekura_tech_hub.authorization import AcquisitionAuthorizationEngine
from kneekura_tech_hub.database import apply_migrations
from kneekura_tech_hub.execution import execute_authorized_acquisition
from kneekura_tech_hub.selection import SourceSelectionEngine
from kneekura_tech_hub.verified_commit import (
    VerifiedAcquisitionCommitError,
    commit_verified_acquisition,
)
from kneekura_tech_hub.verified_commit_postgres import VerifiedCommitPostgresRepository


DSN = os.getenv("KTHUB_TEST_DATABASE_URL")
pytestmark = pytest.mark.skipif(not DSN, reason="KTHUB_TEST_DATABASE_URL is not set")
SHA = "0123456789abcdef0123456789abcdef01234567"
SOURCE_ID = "src:github:example:prewrite-race"
HUMAN = {"actor_type": "human", "actor_id": "race-reviewer"}
TOOL = {"actor_type": "tool", "actor_id": "race-committer", "version": "v1"}


def _blob_sha(content: bytes) -> str:
    header = f"blob {len(content)}\0".encode("ascii")
    return sha1(header + content).hexdigest()  # noqa: S324 - Git identity


def _truncate(connection) -> None:
    connection.execute(
        """
        TRUNCATE TABLE
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


class TamperingRepository(VerifiedCommitPostgresRepository):
    storage_root: Path
    execution_storage_key: str

    def commit_verified_acquisition_atomic(self, **kwargs):
        # This happens after the first full verification but before the parent acquires locks and
        # invokes the second prewrite_check. The second rehash must catch it.
        target = self.storage_root / self.execution_storage_key / "README.md"
        target.write_bytes(b"mutated between verification passes")
        return super().commit_verified_acquisition_atomic(**kwargs)


def test_store_change_between_prepare_and_locked_prewrite_is_rejected(tmp_path: Path):
    assert DSN is not None
    connection = psycopg.connect(DSN, autocommit=True)
    try:
        apply_migrations(connection)
        _truncate(connection)
        repository = TamperingRepository(connection)
        repository.put(
            {
                "record_type": "source",
                "id": SOURCE_ID,
                "kind": "repository",
                "origin": {
                    "provider": "github",
                    "repository": "example/prewrite-race",
                    "url": "https://github.com/example/prewrite-race",
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
            rationale="Select exact race fixture.",
            actor=HUMAN,
            decision_id="sd:prewrite-race",
        )
        authorization = AcquisitionAuthorizationEngine(repository).authorize_from_fields(
            source_id=SOURCE_ID,
            selection_decision_id=selection["id"],
            revision=SHA,
            allowed_paths=["README.md"],
            rationale="Authorize one exact file.",
            actor=HUMAN,
            authorization_id="aa:prewrite-race",
        )
        content = b"original verified bytes"
        execution = execute_authorized_acquisition(
            repository,
            authorization["id"],
            storage_root=tmp_path,
            fetch_file=lambda *_args: {"content": content, "git_blob_sha": _blob_sha(content)},
            actor={"actor_type": "tool", "actor_id": "race-fetcher", "version": "v1"},
            execution_id="ax:prewrite-race",
        )
        repository.storage_root = tmp_path
        repository.execution_storage_key = execution["storage_key"]

        with pytest.raises(VerifiedAcquisitionCommitError, match="content mismatch"):
            commit_verified_acquisition(
                repository,
                execution["id"],
                storage_root=tmp_path,
                actor=TOOL,
            )

        assert repository.get(SOURCE_ID)["acquisition"] == {"level": "metadata-only"}
        assert repository.list("source_snapshot") == []
        assert repository.list("source_acquisition_commit") == []
        assert repository.list("curation_event") == []
    finally:
        connection.close()
