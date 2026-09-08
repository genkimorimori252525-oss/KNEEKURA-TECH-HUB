from __future__ import annotations

from copy import deepcopy

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


def explain_relation_result(repository: RecordRepository, result: Record) -> Record:
    """Explain a projected/problem-query result that carries a Relation Claim ID."""

    relation_claim = result.get("relation_claim")
    if not isinstance(relation_claim, dict):
        raise ExplanationError("result does not contain a relation_claim object")
    claim_id = relation_claim.get("claim_id")
    if not isinstance(claim_id, str) or not claim_id:
        raise ExplanationError("result relation_claim does not contain a claim_id")
    return explain_claim(repository, claim_id)
