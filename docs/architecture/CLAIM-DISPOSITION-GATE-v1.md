# Claim Disposition Gate v1

## Purpose

`REJECTED` and `SUPERSEDED` remove a Claim from the active knowledge surface. Once a Claim has passed human review, that terminalization must not be available to automation merely because automation can raise a challenge.

The gate therefore protects **terminal transitions of reviewed knowledge**, not every rejection in the discovery pipeline.

## Authority boundary

The v1 policy is deliberately asymmetric:

```text
CANDIDATE  -> REJECTED      automation allowed

SUPPORTED  -> REJECTED      human disposition required
CHALLENGED -> REJECTED      human disposition required

VALIDATED  -> SUPERSEDED    human disposition required
CHALLENGED -> SUPERSEDED    human disposition required

* -> CHALLENGED             remains available to automation when lifecycle-valid
```

This preserves two useful properties at once:

1. Cheap discovery candidates can still be discarded cheaply.
2. Automation can still surface warnings and request re-verification without being able to erase the result of prior human review.

In particular, automation cannot use the two-step path:

```text
VALIDATED -> CHALLENGED -> REJECTED
```

to bypass the human Validation Gate.

## Canonical decision record

There is one append-only decision vocabulary:

```text
claim_disposition_decision
```

A decision records:

- the exact Claim;
- actual previous and terminal maturities;
- the human reviewer and reason;
- the Claim's exact Evidence profile;
- distinct Sources and SourceSnapshots;
- review flags;
- active exact-subject competing Claims;
- an explicit competition note when competitors exist;
- for supersession, the exact successor Claim;
- policy version and decision timestamp.

There are deliberately not separate rejection and supersession decision tables.

## Supersession integrity

A `SUPERSEDED` decision requires a successor Claim that:

- exists;
- is not the Claim being superseded;
- describes the same exact Claim subject;
- is already `SUPPORTED` or `VALIDATED`.

The decision does not infer that one formulation is globally better. It records a human-governed lineage choice between Claims about the same subject.

## Transactional pairing

A protected disposition is valid only when the decision and terminal Claim state become true together.

```text
human review
    ↓
claim_disposition_decision
    ↓ same transaction
Claim -> REJECTED / SUPERSEDED
    ↓
curation_event
```

PostgreSQL enforces both directions with deferred constraint triggers:

1. a protected terminal transition requires a matching disposition decision;
2. a disposition decision requires the matching terminal Claim state.

The decision table is append-only.

## Memory / PostgreSQL parity

`MemoryRepository` preserves the same authority ceiling for actual lifecycle transitions.

It tracks protected terminal transitions during a transaction and verifies that a matching disposition decision exists when the transaction completes. It also rejects a disposition decision that is not paired with its terminal Claim state.

Historical read fixtures are different from lifecycle writes. A fixture may load a Claim already marked `SUPERSEDED` or `REJECTED` without replaying the original historical decision transaction. The guard applies when an existing Claim is changed through a protected transition, matching the PostgreSQL UPDATE-trigger semantics.

## Public write path

The governed write API is:

```python
from kneekura_tech_hub.claim_disposition import dispose_claim

result = dispose_claim(
    repository,
    claim_id,
    "REJECTED",  # or "SUPERSEDED"
    actor=human,
    reason="reviewed terminal disposition",
)
```

The command-line surface is:

```bash
kneekura-claim-disposition context cl:...
kneekura-claim-disposition history --claim-id cl:...
kneekura-claim-disposition decide cl:... REJECTED \
  --actor-id curator \
  --reason "reviewed terminal disposition"
```

For `SUPERSEDED`, the successor Claim must also be supplied.

A generic direct terminal transition of reviewed knowledge is intentionally not the governed success path; the repository boundary rejects it unless the matching human decision is part of the same transaction.

## Deliberately not included

- human approval for `CANDIDATE -> REJECTED`;
- blocking automated `CHALLENGED` warnings;
- automatic winner selection among competing Claims;
- automatic supersession based on confidence or a scalar score;
- hard deletion of rejected or superseded history;
- a second rejection-specific or supersession-specific canonical decision store.
