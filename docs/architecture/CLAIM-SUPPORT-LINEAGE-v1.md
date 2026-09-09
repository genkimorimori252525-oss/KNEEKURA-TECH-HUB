# Claim Support Lineage v1

## Purpose

Support review is one concept even when a Claim returns from `CHALLENGED` to `SUPPORTED`.

The Hub therefore keeps one canonical append-only record vocabulary:

```text
claim_support_decision
```

It is used for both:

```text
CANDIDATE  ── human support review ──> SUPPORTED
CHALLENGED ── human support review ──> SUPPORTED
```

There is deliberately no second canonical `claim_resupport_decision` store.

## Why one lineage

A separate resupport record type would split the maturity lineage. In particular, a later Validation Decision could still point at the original Candidate support review instead of the human review that actually restored a challenged Claim to `SUPPORTED`.

The unified history remains reconstructable:

```text
CANDIDATE
  ↓ csd:first
SUPPORTED
  ↓ challenge
CHALLENGED
  ↓ csd:second
SUPPORTED
  ↓ validation references csd:second
VALIDATED
```

Repeated challenge/support cycles append more `claim_support_decision` rows. Existing rows are never rewritten.

## Fresh support review

Every transition into `SUPPORTED` requires a fresh support decision whose:

- `claim_id` matches the Claim;
- `from_maturity` matches the actual previous maturity;
- `to_maturity` is `SUPPORTED`;
- `decided_at` is newer than the Claim's previous support-lineage anchor.

Migration `0017_claim_support_lineage.sql` stores the current anchor in the database-only `claim.last_support_reviewed_at` column.

The anchor is not a new epistemic property exposed in Claim JSON. It is a transactional integrity mechanism used to prevent replay of an old decision.

## Evidence and review semantics

Initial support and restored support use the same review rules:

- at least one actual `SUPPORTS` Evidence;
- exact Evidence / Source / SourceSnapshot profile;
- explicit acknowledgement of actual `REFUTES` Evidence;
- explicit acknowledgement of actual `QUALIFIES` Evidence;
- explicit acknowledgement of active exact-subject competing Claims;
- evidence independence remains `NOT_ASSESSED` or `HUMAN_REVIEWED`;
- no scalar quality score or automatic independence inference.

The existing PostgreSQL Evidence-integrity, competition-integrity, and append-only decision triggers continue to apply to every support decision.

## Validation lineage

A Validation Decision must reference the newest `claim_support_decision` for the Claim.

This is enforced twice:

1. `claim_validation.py` selects the latest append-only support history record.
2. PostgreSQL rejects a `claim_validation_decision` whose `support_decision_id` is not the latest support decision.

Therefore a Claim cannot be re-supported and then validated using an obsolete support review.

## Public interfaces

The existing public API remains the entry point:

```python
engine.transition_claim(
    claim_id,
    "SUPPORTED",
    actor=human,
    reason="reviewed",
)
```

The service routes based on current maturity:

- `CANDIDATE` -> initial Support Gate;
- `CHALLENGED` -> fresh Support Gate review.

The CLI remains one command surface:

```bash
kneekura-claim-support promote cl:... \
  --actor-id curator \
  --reason "reviewed the challenge" \
  --independence-assessment NOT_ASSESSED
```

It also dispatches by the Claim's current maturity.

## Deliberately not included

- a second canonical resupport decision table;
- automatic restoration of challenged Claims;
- AI-only support or resupport;
- semantic winner selection among competing Claims;
- automatic evidence-independence inference;
- fixed minimum Source count;
- a claim that `SUPPORTED` or `VALIDATED` means universal truth.
