from __future__ import annotations

from collections import Counter
from datetime import datetime, timezone

from .explanation import explain_claim
from .repository import Record, RecordRepository


class ReviewError(ValueError):
    """Raised when a derived evidence review cannot be produced safely."""


def _parse_datetime(value: str) -> datetime:
    normalized = value.replace("Z", "+00:00")
    parsed = datetime.fromisoformat(normalized)
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def _verification_view(claim: Record, now: datetime) -> Record:
    last_verified = claim.get("last_verified")
    due_at = claim.get("verification_due_at")

    if last_verified is None:
        freshness = "NEVER_VERIFIED"
    elif due_at is None:
        freshness = "NO_DUE_DATE"
    else:
        try:
            due = _parse_datetime(due_at)
        except (TypeError, ValueError) as exc:
            raise ReviewError(f"invalid verification_due_at: {due_at!r}") from exc
        freshness = "DUE" if due <= now else "NOT_DUE"

    return {
        "last_verified": last_verified,
        "verification_due_at": due_at,
        "freshness": freshness,
    }


def review_claim(
    repository: RecordRepository,
    claim_id: str,
    *,
    now: datetime | None = None,
) -> Record:
    """Return a non-scalar, read-only review profile for one Claim.

    The review deliberately reports observable dimensions instead of collapsing them
    into a single quality/strength score.
    """

    if now is None:
        now = datetime.now(timezone.utc)
    elif now.tzinfo is None:
        now = now.replace(tzinfo=timezone.utc)
    else:
        now = now.astimezone(timezone.utc)

    explanation = explain_claim(repository, claim_id)
    claim = explanation["claim"]
    chains = explanation["evidence_chains"]

    role_counts: Counter[str] = Counter()
    locator_counts: Counter[str] = Counter()
    source_ids: set[str] = set()
    snapshot_ids: set[str] = set()
    sources_by_role: dict[str, set[str]] = {
        "SUPPORTS": set(),
        "REFUTES": set(),
        "QUALIFIES": set(),
    }

    for chain in chains:
        evidence = chain["evidence"]
        source_id = chain["source"]["id"]
        snapshot_id = chain["source_snapshot"]["id"]
        source_ids.add(source_id)
        snapshot_ids.add(snapshot_id)

        locator_type = (evidence.get("locator") or {}).get("type", "UNKNOWN")
        locator_counts[locator_type] += 1

        for role in evidence.get("roles", []):
            role_counts[role] += 1
            sources_by_role.setdefault(role, set()).add(source_id)

    flags: list[str] = []
    if not chains:
        flags.append("NO_EVIDENCE")
    if len(source_ids) == 1:
        flags.append("SINGLE_SOURCE")
    elif len(source_ids) > 1:
        flags.append("MULTIPLE_DISTINCT_SOURCES")
    if role_counts["REFUTES"]:
        flags.append("HAS_REFUTING_EVIDENCE")
    if role_counts["QUALIFIES"]:
        flags.append("HAS_QUALIFYING_EVIDENCE")
    if len(snapshot_ids) > 1:
        flags.append("MULTIPLE_SNAPSHOTS")

    verification = _verification_view(claim, now)
    if verification["freshness"] == "DUE":
        flags.append("VERIFICATION_DUE")

    return {
        "claim_id": claim["id"],
        "claim_type": claim["claim_type"],
        "maturity": claim["maturity"],
        "confidence": claim.get("confidence", "UNKNOWN"),
        "evidence": {
            "count": len(chains),
            "distinct_source_count": len(source_ids),
            "distinct_snapshot_count": len(snapshot_ids),
            "source_ids": sorted(source_ids),
            "snapshot_ids": sorted(snapshot_ids),
            "role_counts": dict(sorted(role_counts.items())),
            "locator_type_counts": dict(sorted(locator_counts.items())),
            "source_ids_by_role": {
                role: sorted(ids)
                for role, ids in sorted(sources_by_role.items())
                if ids
            },
        },
        "verification": verification,
        "flags": flags,
    }


def review_claims(
    repository: RecordRepository,
    *,
    needs_review_only: bool = False,
    now: datetime | None = None,
) -> list[Record]:
    """Build review profiles for all Claims without changing canonical records."""

    profiles = [
        review_claim(repository, claim["id"], now=now)
        for claim in repository.list("claim")
    ]

    if needs_review_only:
        profiles = [profile for profile in profiles if _needs_review(profile)]

    return sorted(profiles, key=lambda profile: profile["claim_id"])


def _needs_review(profile: Record) -> bool:
    if profile["maturity"] in {"CANDIDATE", "CHALLENGED"}:
        return True
    if profile["verification"]["freshness"] == "DUE":
        return True
    if "HAS_REFUTING_EVIDENCE" in profile["flags"]:
        return True
    return False
