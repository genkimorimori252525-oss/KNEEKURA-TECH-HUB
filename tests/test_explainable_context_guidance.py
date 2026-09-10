from __future__ import annotations

from copy import deepcopy

import pytest

from kneekura_tech_hub.explanation import ExplanationError, explain_contextual_guidance
from kneekura_tech_hub.repository import MemoryRepository


ENTITY_ID = "ke:guidance:indentation-character-policy"
GO_SOURCE = "src:guidance:go"
PY_SOURCE = "src:guidance:python"
GO_SNAPSHOT = "ss:guidance:go"
PY_SNAPSHOT = "ss:guidance:python"
GO_EVIDENCE = "ev:guidance:go"
PY_EVIDENCE = "ev:guidance:python"
GO_CLAIM = "cl:guidance:go-tabs"
PY_CLAIM = "cl:guidance:python-spaces"


def _source(source_id: str, repository: str) -> dict:
    return {
        "record_type": "source",
        "id": source_id,
        "kind": "repository",
        "origin": {"provider": "github", "repository": repository},
        "acquisition": {"level": "selected-files"},
        "license": {"state": "KNOWN", "declared_expression": "BSD-3-Clause"},
    }


def _snapshot(snapshot_id: str, source_id: str, revision: str) -> dict:
    return {
        "record_type": "source_snapshot",
        "id": snapshot_id,
        "source_id": source_id,
        "revision": revision,
        "captured_at": "2026-09-10T11:00:00+09:00",
        "metadata": {"fixture": "explainable-context-guidance-v1"},
    }


def _evidence(evidence_id: str, source_id: str, snapshot_id: str, path: str) -> dict:
    return {
        "record_type": "evidence",
        "id": evidence_id,
        "source_id": source_id,
        "source_snapshot_id": snapshot_id,
        "locator": {"type": "document_section", "path": path},
        "roles": ["SUPPORTS"],
    }


def _claim(
    claim_id: str,
    statement: str,
    *,
    evidence_id: str,
    ecosystem: str,
    authority: str,
) -> dict:
    return {
        "record_type": "claim",
        "id": claim_id,
        "entity_id": ENTITY_ID,
        "claim_type": "AUTHOR_CLAIM",
        "statement": statement,
        "maturity": "VALIDATED",
        "scope": {
            "decision": "indentation-character",
            "comparison": "language-style-policy",
            "question": "tabs-or-spaces",
        },
        "applicability": {
            "domain": "source-code",
            "ecosystem": ecosystem,
            "authority": authority,
        },
        "evidence_ids": [evidence_id],
        "created_by": {"actor_type": "ai", "actor_id": "guidance-fixture", "version": "v1"},
        "policy_version": "1.0.0",
    }


def _repository() -> MemoryRepository:
    repository = MemoryRepository()
    records = [
        _source(GO_SOURCE, "golang/go"),
        _source(PY_SOURCE, "python/peps"),
        _snapshot(GO_SNAPSHOT, GO_SOURCE, "go-revision"),
        _snapshot(PY_SNAPSHOT, PY_SOURCE, "python-revision"),
        _evidence(GO_EVIDENCE, GO_SOURCE, GO_SNAPSHOT, "src/go/format/format.go"),
        _evidence(PY_EVIDENCE, PY_SOURCE, PY_SNAPSHOT, "peps/pep-0008.rst"),
        {
            "record_type": "knowledge_entity",
            "id": ENTITY_ID,
            "canonical_name": "Source-code indentation character policy",
            "aliases": ["Tabs versus spaces policy"],
            "kinds": ["design-decision", "style-policy"],
            "abstraction_level": "L1",
            "identity_state": "CANONICAL",
            "relations": [],
        },
        _claim(
            GO_CLAIM,
            "Go's canonical gofmt formatter uses tabs for indentation and blanks for alignment.",
            evidence_id=GO_EVIDENCE,
            ecosystem="Go",
            authority="gofmt",
        ),
        _claim(
            PY_CLAIM,
            "Python PEP 8 prefers spaces for indentation.",
            evidence_id=PY_EVIDENCE,
            ecosystem="Python",
            authority="PEP 8",
        ),
    ]
    for record in records:
        repository.put(record)
    return repository


def test_exact_context_returns_one_explained_claim_with_full_provenance() -> None:
    repository = _repository()
    before = repository.list()

    guidance = explain_contextual_guidance(repository, ENTITY_ID, context={"ecosystem": "Go"})

    assert guidance["resolution"] == "ONE_MATCH"
    assert guidance["candidate_claim_ids"] == [GO_CLAIM]
    assert guidance["explanation_count"] == 1
    explanation = guidance["claim_explanations"][0]
    assert explanation["claim"]["id"] == GO_CLAIM
    assert explanation["evidence_chains"][0]["evidence"]["id"] == GO_EVIDENCE
    assert explanation["evidence_chains"][0]["source_snapshot"]["id"] == GO_SNAPSHOT
    assert explanation["evidence_chains"][0]["source"]["id"] == GO_SOURCE
    assert guidance["context"] == {"ecosystem": "Go"}
    assert "winner" not in guidance
    assert "preferred_claim_id" not in guidance
    assert "score" not in guidance
    assert repository.list() == before


def test_ambiguous_context_explains_every_candidate_without_inventing_a_winner() -> None:
    repository = _repository()

    guidance = explain_contextual_guidance(repository, ENTITY_ID)

    assert guidance["resolution"] == "CONTEXT_REQUIRED"
    assert guidance["candidate_claim_ids"] == sorted([GO_CLAIM, PY_CLAIM])
    assert guidance["explanation_count"] == 2
    assert [item["claim"]["id"] for item in guidance["claim_explanations"]] == sorted(
        [GO_CLAIM, PY_CLAIM]
    )
    assert "winner" not in guidance
    assert "preferred_claim_id" not in guidance


def test_no_match_returns_no_explanations_instead_of_fallback_guidance() -> None:
    repository = _repository()

    guidance = explain_contextual_guidance(repository, ENTITY_ID, context={"ecosystem": "Rust"})

    assert guidance["resolution"] == "NO_MATCH"
    assert guidance["candidate_claim_ids"] == []
    assert guidance["explanation_count"] == 0
    assert guidance["claim_explanations"] == []


def test_broken_provenance_fails_closed_instead_of_returning_partial_guidance() -> None:
    repository = _repository()
    broken = deepcopy(repository.get(GO_EVIDENCE))
    assert broken is not None
    broken["id"] = "ev:guidance:broken"
    broken["source_snapshot_id"] = "ss:guidance:missing"
    repository.put(broken)
    broken_claim = deepcopy(repository.get(GO_CLAIM))
    assert broken_claim is not None
    broken_claim["id"] = "cl:guidance:broken"
    broken_claim["evidence_ids"] = [broken["id"]]
    broken_claim["applicability"] = {"ecosystem": "Broken"}
    repository.put(broken_claim)

    with pytest.raises(ExplanationError, match="missing source_snapshot"):
        explain_contextual_guidance(repository, ENTITY_ID, context={"ecosystem": "Broken"})


class _DriftingRepository(MemoryRepository):
    """Expose a Claim-state race between context selection and provenance explanation."""

    def __init__(self, source: MemoryRepository) -> None:
        super().__init__()
        for record in source.list():
            self.put(record)
        self._claim_listed = False

    def list(self, record_type: str | None = None) -> list[dict]:
        result = super().list(record_type)
        if record_type == "claim":
            self._claim_listed = True
        return result

    def get(self, record_id: str) -> dict | None:
        record = super().get(record_id)
        if self._claim_listed and record_id == GO_CLAIM and record is not None:
            record["maturity"] = "CHALLENGED"
        return record


def test_guidance_fails_closed_if_claim_changes_after_context_selection() -> None:
    repository = _DriftingRepository(_repository())

    with pytest.raises(ExplanationError, match="changed during explanation"):
        explain_contextual_guidance(repository, ENTITY_ID, context={"ecosystem": "Go"})
