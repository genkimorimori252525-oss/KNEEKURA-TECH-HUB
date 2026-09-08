from __future__ import annotations

from collections import defaultdict
from copy import deepcopy
from typing import Any

from .repository import Record, RecordRepository
from .review import review_claim


class ComparisonError(ValueError):
    """Raised when Claims cannot be grouped or compared safely."""


def claim_subject_key(claim: Record) -> tuple[str, ...]:
    """Return the immutable semantic subject key used for comparison grouping."""

    if claim.get("record_type") != "claim":
        raise ComparisonError(f"expected claim, got {claim.get('record_type')!r}")

    entity_id = claim.get("entity_id")
    relation = claim.get("relation")
    if isinstance(entity_id, str) and not relation:
        return ("entity", entity_id)
    if isinstance(relation, dict) and not entity_id:
        try:
            return (
                "relation",
                relation["source_entity_id"],
                relation["relation_type"],
                relation["target_entity_id"],
            )
        except KeyError as exc:
            raise ComparisonError(f"incomplete relation subject: {claim['id']}") from exc
    raise ComparisonError(f"claim has ambiguous or missing subject: {claim.get('id')}")


def _subject_record(key: tuple[str, ...]) -> Record:
    if key[0] == "entity":
        return {"kind": "entity", "entity_id": key[1]}
    return {
        "kind": "relation",
        "source_entity_id": key[1],
        "relation_type": key[2],
        "target_entity_id": key[3],
    }


def compare_subject_claims(
    repository: RecordRepository,
    subject_key: tuple[str, ...],
) -> Record:
    """Compare all Claims for one exact subject without choosing a winner.

    Statement differences are reported as differences, never automatically labeled as
    contradictions. Explicit review signals come from maturity and Evidence roles.
    """

    matching: list[Record] = []
    for claim in repository.list("claim"):
        if claim_subject_key(claim) == subject_key:
            matching.append(claim)

    if not matching:
        raise ComparisonError(f"no claims for subject: {subject_key!r}")

    matching.sort(key=lambda claim: claim["id"])
    profiles = [review_claim(repository, claim["id"]) for claim in matching]

    active = [
        claim
        for claim in matching
        if claim["maturity"] not in {"SUPERSEDED", "REJECTED"}
    ]
    active_ids = [claim["id"] for claim in active]
    statements = {claim["statement"] for claim in matching}
    claim_types = {claim["claim_type"] for claim in matching}
    maturities = {claim["maturity"] for claim in matching}

    flags: list[str] = []
    if len(matching) > 1:
        flags.append("MULTIPLE_CLAIMS")
    if len(active) > 1:
        flags.append("MULTIPLE_ACTIVE_CLAIMS")
    if len(statements) > 1:
        flags.append("STATEMENTS_DIFFER")
    if len(claim_types) > 1:
        flags.append("EPISTEMIC_TYPES_DIFFER")
    if len(maturities) > 1:
        flags.append("MATURITIES_DIFFER")
    if any(claim["maturity"] == "CHALLENGED" for claim in matching):
        flags.append("HAS_CHALLENGED_CLAIM")
    if any("HAS_REFUTING_EVIDENCE" in profile["flags"] for profile in profiles):
        flags.append("HAS_REFUTING_EVIDENCE")
    if any(claim["maturity"] == "SUPERSEDED" for claim in matching):
        flags.append("HAS_SUPERSEDED_CLAIM")
    if any(claim["maturity"] == "REJECTED" for claim in matching):
        flags.append("HAS_REJECTED_CLAIM")

    needs_review = any(
        flag in flags
        for flag in (
            "MULTIPLE_ACTIVE_CLAIMS",
            "HAS_CHALLENGED_CLAIM",
            "HAS_REFUTING_EVIDENCE",
        )
    )

    return {
        "subject": _subject_record(subject_key),
        "claim_count": len(matching),
        "active_claim_count": len(active),
        "active_claim_ids": active_ids,
        "statements_are_identical": len(statements) == 1,
        "flags": flags,
        "needs_review": needs_review,
        "claims": [
            {
                "claim": deepcopy(claim),
                "review": profile,
            }
            for claim, profile in zip(matching, profiles, strict=True)
        ],
    }


def compare_claim(repository: RecordRepository, claim_id: str) -> Record:
    claim = repository.get(claim_id)
    if claim is None:
        raise ComparisonError(f"missing claim: {claim_id}")
    return compare_subject_claims(repository, claim_subject_key(claim))


def comparison_groups(
    repository: RecordRepository,
    *,
    multiple_only: bool = False,
    needs_review_only: bool = False,
) -> list[Record]:
    """Return all exact-subject Claim groups, with optional explicit filters."""

    grouped: dict[tuple[str, ...], list[str]] = defaultdict(list)
    for claim in repository.list("claim"):
        grouped[claim_subject_key(claim)].append(claim["id"])

    results = [compare_subject_claims(repository, key) for key in sorted(grouped)]
    if multiple_only:
        results = [result for result in results if result["claim_count"] > 1]
    if needs_review_only:
        results = [result for result in results if result["needs_review"]]
    return results
