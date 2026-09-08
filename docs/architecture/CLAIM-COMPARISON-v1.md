# Claim Comparison v1

## Purpose

KNEEKURA TECH HUB can now explain one Claim and expose its Evidence review profile. The next failure mode is subtler:

> What if multiple Claims exist about the same thing?

Claim Comparison v1 groups Claims that have the exact same stored subject and presents them side by side without automatically choosing a winner or declaring a contradiction.

## Exact stored subject

Entity Claim subject:

```text
(entity, entity_id)
```

Relation Claim subject:

```text
(relation, source_entity_id, relation_type, target_entity_id)
```

The relation type is part of the subject. Therefore:

```text
A --solves→ B
```

and

```text
A --requires→ B
```

are different comparison groups even if the endpoint IDs are identical.

## Why v1 does not resolve entity redirects while grouping

Claim Comparison v1 groups the exact immutable subject stored on each Claim.

It does not automatically group Claims across `MERGED → redirect_to` identity redirects. Doing so could combine Claims that were intentionally authored about separate identities before a later merge.

A future resolved-identity comparison view can be added explicitly if needed. It should not silently replace exact historical grouping.

## No automatic contradiction verdict

Different statements are not necessarily contradictory.

For example, both can be true:

- “This technique reduces repeated work.”
- “This technique may increase maintenance cost.”

Claim Comparison therefore emits:

`STATEMENTS_DIFFER`

but does not emit:

- `CONTRADICTION`;
- `winner`;
- `preferred_claim_id`;
- majority vote;
- truth probability.

Explicit disagreement signals must remain inspectable rather than being converted into an invented verdict.

## Group result

A comparison group contains:

- exact subject;
- total Claim count;
- active Claim count;
- active Claim IDs;
- whether all statements are textually identical;
- descriptive flags;
- `needs_review`;
- each full Claim;
- each Claim’s Evidence Review profile.

Claims with maturity `SUPERSEDED` or `REJECTED` remain visible in history but are not counted as active.

## Descriptive flags

Current group flags include:

- `MULTIPLE_CLAIMS`;
- `MULTIPLE_ACTIVE_CLAIMS`;
- `STATEMENTS_DIFFER`;
- `EPISTEMIC_TYPES_DIFFER`;
- `MATURITIES_DIFFER`;
- `HAS_CANDIDATE_CLAIM`;
- `HAS_CHALLENGED_CLAIM`;
- `HAS_REFUTING_EVIDENCE`;
- `VERIFICATION_DUE`;
- `HAS_SUPERSEDED_CLAIM`;
- `HAS_REJECTED_CLAIM`.

These are observations and workflow signals, not a hidden ranking system.

## Review conditions

A comparison group needs review when any explicit condition is true:

- more than one active Claim exists for the same exact subject;
- a Candidate Claim exists;
- a Challenged Claim exists;
- any member Claim has refuting Evidence;
- any member Claim is due for verification.

A group is not marked contradictory merely because its statements differ.

## Per-Claim provenance remains separate

Every Claim in the group keeps its own:

- statement;
- epistemic type;
- maturity;
- creator provenance;
- Evidence IDs;
- Evidence Explanation chain;
- Evidence Review profile.

Comparison never merges the Evidence sets of different Claims into a synthetic “combined truth.”

## Real Salsa acceptance

The real Salsa Problem Query pilot already contains:

```text
Query-based Incremental Computation
  --solves→
Repeated recomputation after input changes
```

The acceptance test adds a second Candidate inference with the exact same relation subject but a more conditional statement.

The comparison result reports:

- two Claims;
- two active Claims;
- different statements;
- Candidate Claims present;
- review required;
- two Evidence records on the original Claim;
- one Evidence record on the alternative Claim.

It does not choose either Claim and does not label the pair contradictory.

## CLI

```bash
# compare every Claim sharing one Claim's exact subject
kneekura-hub compare-claim cl:example

# list all comparison groups
kneekura-hub compare-claims

# only subjects with multiple Claims
kneekura-hub compare-claims --multiple-only

# only groups matching explicit review conditions
kneekura-hub compare-claims --needs-review
```

Commands are read-only.

## Non-goals

Claim Comparison v1 does not:

- perform natural-language contradiction detection;
- perform semantic entailment;
- vote by number of Claims;
- prefer more popular Sources;
- average Evidence profiles;
- automatically supersede or reject Claims;
- merge Claims across entity redirects;
- choose a canonical statement.

## Next pressure

A later slice may add **explicit human contradiction annotations** or **resolved-identity comparison views**, but those should be modeled as traceable review decisions rather than inferred truth written back into Claims automatically.
