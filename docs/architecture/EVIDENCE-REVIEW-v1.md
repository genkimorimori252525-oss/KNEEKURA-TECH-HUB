# Evidence Review v1

## Purpose

Evidence Explanation answers:

> Where did this Claim come from?

Evidence Review v1 answers a different question:

> What observable review signals surround this Claim right now?

It is a derived, read-only view built from the existing Claim and its exact Evidence provenance. It does not alter Claim maturity and does not create a new knowledge store.

## No single strength score

Evidence Review v1 deliberately does **not** produce fields such as:

- `score: 87`;
- `strength: high`;
- `quality: 0.92`.

Those numbers would collapse unlike dimensions into one value and could make a context-sensitive design judgment look objective.

Instead the view exposes separate dimensions so a human or later policy can reason about them explicitly.

## Review profile

`review_claim(repository, claim_id)` returns:

```json
{
  "claim_id": "cl:...",
  "claim_type": "INFERENCE",
  "maturity": "CANDIDATE",
  "confidence": "MEDIUM",
  "evidence": {
    "count": 2,
    "distinct_source_count": 1,
    "distinct_snapshot_count": 1,
    "source_ids": ["src:..."],
    "snapshot_ids": ["ss:..."],
    "role_counts": {"SUPPORTS": 2},
    "locator_type_counts": {"source_lines": 2},
    "source_ids_by_role": {
      "SUPPORTS": ["src:..."]
    }
  },
  "verification": {
    "last_verified": null,
    "verification_due_at": null,
    "freshness": "NEVER_VERIFIED"
  },
  "flags": ["SINGLE_SOURCE"]
}
```

## Distinct Sources are not automatically independent

`distinct_source_count` means only that Evidence references different canonical Source IDs.

It does **not** mean:

- independent corroboration;
- different authors;
- no shared upstream source;
- no copied documentation;
- greater truth probability.

For that reason the field is named `distinct_source_count`, not `independent_source_count`.

The flag `MULTIPLE_DISTINCT_SOURCES` is descriptive, not praise.

## Evidence roles remain visible

Evidence roles are counted independently:

- `SUPPORTS`;
- `REFUTES`;
- `QUALIFIES`.

Refuting Evidence is not converted into a hidden numerical penalty. The review profile exposes it directly through `role_counts`, `source_ids_by_role`, and `HAS_REFUTING_EVIDENCE`.

Qualifying Evidence similarly remains visible through `HAS_QUALIFYING_EVIDENCE`.

This makes disagreement inspectable rather than averaging it away.

## Locator types

`locator_type_counts` summarizes how Evidence is anchored, for example:

- `source_lines`;
- `symbol`;
- `document_section`;
- `issue_comment`;
- `experiment_artifact`;
- `stable_url`.

The review layer does not assert that one locator type is universally better than another. The meaning depends on the Claim type and context.

## Verification freshness

Evidence Review distinguishes four states:

- `NEVER_VERIFIED` — no `last_verified` exists;
- `NO_DUE_DATE` — verified, but no verification deadline is recorded;
- `NOT_DUE` — a future `verification_due_at` exists;
- `DUE` — the verification deadline has arrived or passed.

A malformed verification due date fails closed instead of being silently ignored.

## Flags

Current descriptive flags are:

- `NO_EVIDENCE`;
- `SINGLE_SOURCE`;
- `MULTIPLE_DISTINCT_SOURCES`;
- `HAS_REFUTING_EVIDENCE`;
- `HAS_QUALIFYING_EVIDENCE`;
- `MULTIPLE_SNAPSHOTS`;
- `VERIFICATION_DUE`.

Flags are not a hidden score. They are explicit review signals.

## Review queue

`review_claims(repository, needs_review_only=True)` returns Claims matching explicit conditions:

- maturity is `CANDIDATE`;
- maturity is `CHALLENGED`;
- verification is `DUE`;
- refuting Evidence exists.

The queue is sorted by immutable Claim ID. It is not ranked by an opaque importance or quality formula.

## Real Salsa acceptance

The real Salsa Problem Query Claim:

`cl:salsa:query-incremental:solves:repeated-recomputation:e021c01d`

starts with two Evidence anchors from one Salsa SourceSnapshot.

Before human validation, its review profile reports:

- maturity `CANDIDATE`;
- Evidence count `2`;
- distinct Source count `1`;
- distinct Snapshot count `1`;
- `SUPPORTS: 2`;
- `source_lines: 2`;
- `SINGLE_SOURCE`;
- verification freshness `NEVER_VERIFIED`.

After the normal human transition through `SUPPORTED` to `VALIDATED`:

- maturity becomes `VALIDATED`;
- `last_verified` is populated;
- freshness becomes `NO_DUE_DATE`;
- the Evidence profile itself remains unchanged.

This is intentional. Claim trust state and Evidence composition are related but different facts.

## CLI

```bash
# inspect one Claim
kneekura-hub review-claim cl:example

# inspect every Claim
kneekura-hub review-claims

# operational review queue using explicit conditions
kneekura-hub review-claims --needs-review
```

All commands are read-only.

## Non-goals

Evidence Review v1 does not:

- calculate a universal evidence-strength score;
- infer source independence;
- decide that more Sources automatically means better Evidence;
- hide refutation inside an average;
- automatically promote/demote Claims;
- automatically resolve contradictions;
- rank technologies by popularity;
- mutate Evidence or Claim records.

## Next pressure

A natural next slice is **competing / contradictory Claim review**: group Claims that address the same entity or relation subject, preserve their separate provenance, and expose disagreement without automatically choosing a winner.
