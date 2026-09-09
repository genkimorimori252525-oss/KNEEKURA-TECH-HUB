# Reviewed Claim Immutability v1

## Purpose

A maturity label is meaningful only if the Claim still means the same thing that was reviewed.

Without an immutability boundary, a caller could leave a Claim at `SUPPORTED` or `VALIDATED` while replacing its statement, subject, reasoning, or Evidence references. The lifecycle would still look governed, but the reviewed object would have been silently replaced.

The v1 rule is therefore:

```text
CANDIDATE -> CANDIDATE
    epistemic edits allowed

CANDIDATE -> any other maturity
    reviewed payload must not change in that transition

SUPPORTED / VALIDATED / CHALLENGED / SUPERSEDED / REJECTED
    reviewed epistemic payload immutable
```

## What is epistemic content

The protected payload includes:

- Claim subject (`entity_id` or relation endpoints/type)
- `claim_type`
- `statement`
- `scope`
- `applicability`
- `confidence`
- `reasoning_basis`
- `alternative_interpretations`
- `evidence_ids`
- `policy_version`

`created_by` is immutable regardless of maturity because it is provenance, not editable Claim content.

Lifecycle fields such as `maturity`, `last_verified`, and `superseded_by` remain controlled by the existing Support, Validation, and Disposition gates. Operational freshness metadata can continue to evolve independently where existing policy permits it.

## Revision model

v1 deliberately does not introduce a new `claim_revision` canonical table.

If reviewed content needs correction or reformulation:

1. create a new Claim with a new immutable Claim ID;
2. review the new Claim through the normal support / validation path;
3. when appropriate, disposition the old Claim as `SUPERSEDED` and point to the reviewed successor.

This preserves both meanings and the decision history instead of rewriting the old Claim in place.

## Evidence-set integrity

PostgreSQL stores Claim/Evidence links in `claim_evidence`, so Claim-row immutability alone is insufficient.

After a support decision exists, the current Evidence-ID set must equal the Evidence set captured by the latest append-only `claim_support_decision`.

This is enforced at transaction completion. Deferred checking is intentional because the normalized repository may delete and reinsert identical `claim_evidence` rows while replacing a Claim record during an ordinary lifecycle transition.

The final transaction state must still be exactly the reviewed Evidence set.

## Timing attacks

The boundary also prevents changing epistemic content in the same UPDATE that leaves `CANDIDATE`.

For example, this is forbidden even though the old row was still a Candidate:

```text
old: CANDIDATE, statement A
update: maturity -> REJECTED, statement -> B
```

For `CANDIDATE -> SUPPORTED`, the existing Support Gate independently requires a fresh support decision. Reviewed-content immutability adds the stronger invariant that the payload itself cannot be swapped while crossing the boundary.

## Memory / PostgreSQL parity

`MemoryRepository` stores Evidence IDs directly in the Claim record, so it applies the same content rule before replacement:

- Candidate-to-Candidate content edits are allowed;
- reviewed-content edits are rejected;
- `created_by` tampering is rejected;
- historical fixture insertion is unaffected because the rule protects mutation of an existing Claim, not replay of old history.

PostgreSQL applies the equivalent rule with Claim-row triggers plus deferred Claim/Evidence snapshot checks.

## Deliberately not included

- automatic semantic revision merging;
- mutable reviewed statements with hidden revision numbers;
- automatic supersession;
- scalar confidence-based rewrite authority;
- changing the meaning of a reviewed Claim while preserving its ID;
- a speculative `claim_revision` table before a real use case requires richer revision semantics.
