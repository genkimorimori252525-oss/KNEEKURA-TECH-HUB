from __future__ import annotations

from collections.abc import Mapping
from copy import deepcopy
from typing import Any

from .queries import contextual_claims_for_entity
from .repository import Record, RecordRepository


class ExplanationError(ValueError):
    """Raised when an evidence provenance chain cannot be reconstructed safely."""


def _require(repository: RecordRepository, record_id: str, record_type: str) -> Record:
    record = repository.get(record_id)
    if record is None:
        raise ExplanationError(f"missing {record_type}: {record_id}")
    actual = record.get("record_type")
    if actual != record_type:
        raise ExplanationError(
            f"expected {record_type} for {record_id}, found {actual!r}"
        )
    return record


def explain_claim(repository: RecordRepository, claim_id: str) -> Record:
    """Rebuild the exact Claim -> Evidence -> Snapshot -> Source provenance chain.

    The function is read-only. Evidence is returned in the same order as the Claim's
    ``evidence_ids``. Referenced-record corruption fails closed instead of producing
    a partial explanation that could look complete.
    """

    claim = _require(repository, claim_id, "claim")
    chains: list[Record] = []

    for evidence_id in claim.get("evidence_ids", []):
        evidence = _require(repository, evidence_id, "evidence")
        snapshot = _require(
            repository,
            evidence["source_snapshot_id"],
            "source_snapshot",
        )
        source = _require(repository, evidence["source_id"], "source")

        if snapshot.get("source_id") != source["id"]:
            raise ExplanationError(
                "evidence source snapshot belongs to a different source: "
                f"evidence={evidence_id} snapshot={snapshot['id']} source={source['id']}"
            )

        chains.append(
            {
                "evidence": deepcopy(evidence),
                "source_snapshot": deepcopy(snapshot),
                "source": deepcopy(source),
            }
        )

    return {
        "claim": deepcopy(claim),
        "evidence_count": len(chains),
        "evidence_chains": chains,
    }


def explain_contextual_guidance(
    repository: RecordRepository,
    entity_id: str,
    *,
    context: Mapping[str, Any] | None = None,
) -> Record:
    """Return context-filtered trusted Claims together with exact provenance chains.

    Context selection remains wholly delegated to ``contextual_claims_for_entity``;
    this function adds no ranking, fallback, scoring, or winner selection. Every
    candidate is independently reconstructed through ``explain_claim``. If a Claim
    changes between context selection and explanation, the operation fails closed
    rather than returning stale trusted guidance.
    """

    query_result = contextual_claims_for_entity(
        repository,
        entity_id,
        context=context,
    )
    candidate_ids = query_result.get("candidate_claim_ids")
    claims = query_result.get("claims")
    if not isinstance(candidate_ids, list) or not isinstance(claims, list):
        raise ExplanationError("contextual query returned an invalid candidate shape")
    if len(candidate_ids) != len(claims):
        raise ExplanationError("contextual query candidate IDs and Claims differ in length")

    explanations: list[Record] = []
    for candidate_id, selected_claim in zip(candidate_ids, claims, strict=True):
        if not isinstance(candidate_id, str) or not candidate_id:
            raise ExplanationError("contextual query returned an invalid candidate Claim ID")
        if not isinstance(selected_claim, dict) or selected_claim.get("id") != candidate_id:
            raise ExplanationError(
                f"contextual query candidate Claim does not match its ID: {candidate_id}"
            )

        explanation = explain_claim(repository, candidate_id)
        if explanation["claim"] != selected_claim:
            raise ExplanationError(
                f"contextual guidance Claim changed during explanation: {candidate_id}"
            )
        explanations.append(explanation)

    result = deepcopy(query_result)
    result["explanation_count"] = len(explanations)
    result["claim_explanations"] = explanations
    return result


def explain_relation_result(repository: RecordRepository, result: Record) -> Record:
    """Explain a projected/problem-query result that carries a Relation Claim ID."""

    relation_claim = result.get("relation_claim")
    if not isinstance(relation_claim, dict):
        raise ExplanationError("result does not contain a relation_claim object")
    claim_id = relation_claim.get("claim_id")
    if not isinstance(claim_id, str) or not claim_id:
        raise ExplanationError("result relation_claim does not contain a claim_id")
    return explain_claim(repository, claim_id)
