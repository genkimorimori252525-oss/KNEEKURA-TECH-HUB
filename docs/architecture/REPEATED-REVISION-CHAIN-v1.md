# Repeated Revision Chain v1

## Purpose

`UPSTREAM-REVISION-REVERIFICATION-v1` proves one governed transition from an older upstream revision to a newer one. This acceptance layer proves that the same contract remains stable when the Source keeps changing repeatedly.

The governing rule stays append-only:

```text
same Source identity

A1 -> Verified Commit -> S1 -> C1
  \\-> A2 -> Verified Commit -> S2 -> C2 -> C1 SUPERSEDED
       \\-> A3 -> Verified Commit -> S3 -> C3 -> C2 SUPERSEDED
            \\-> A4 -> Verified Commit -> S4 -> C4 -> C3 SUPERSEDED
```

No generation rewrites an older Authorization, Snapshot, Evidence record, reviewed Claim, support/validation decision, or disposition decision.

## What the acceptance test proves

The PostgreSQL acceptance test runs four complete generations through the real governed path.

For every generation it performs:

1. fresh exact human `AUTHORIZE`;
2. bounded selected-file Execution;
3. Verified Acquisition Commit;
4. new immutable SourceSnapshot;
5. Evidence extraction from that exact Snapshot;
6. new CANDIDATE Claim for the stable semantic subject;
7. human Support;
8. human Validation;
9. AI `CHALLENGED` transition of the previous reviewed Claim;
10. human `SUPERSEDED` disposition of that previous Claim.

After four generations, all four provenance generations remain explainable independently.

## Authorization chain invariant

Authorization history is a forward-only one-shot chain.

```text
A1 <- A2 <- A3 <- A4
```

Each arrow means the newer human grant explicitly supersedes the immediately active predecessor.

A Verified Acquisition Commit consumes the exact grant that authorized it. Consumed grants remain in append-only history but cannot execute again.

At the end of the four-generation acceptance scenario:

- `A1`, `A2`, and `A3` are no longer lineage-active and are committed;
- `A4` is the only lineage-active Authorization record;
- `A4` is also committed, so it is ineffective;
- the effective authorized-acquisition request set is empty;
- attempting to execute an older committed grant fails before any fetch occurs.

A later generation therefore requires a fresh `A5` that supersedes `A4`; old authority never becomes ambient reusable permission.

## Snapshot and Evidence invariant

Each generation creates a distinct immutable SourceSnapshot under the same stable Source:

```text
src:S
  ├─ S1 @ rev1
  ├─ S2 @ rev2
  ├─ S3 @ rev3
  └─ S4 @ rev4
```

The test verifies all four exact revision identities remain addressable and each reviewed Claim explains through its own Evidence to its own Snapshot.

A later generation does not retarget an older Evidence locator or Claim evidence set.

## Semantic revert invariant

The acceptance scenario deliberately uses this sequence:

```text
v1: enabled
v2: disabled
v3: enabled
v4: adaptive
```

`v3` therefore repeats the same Claim statement as `v1`.

This is intentional. Semantic equality across different upstream generations is not permission to resurrect an old reviewed Claim or rewrite its provenance.

The accepted behavior is:

```text
C1(enabled, S1)  -> SUPERSEDED
C2(disabled, S2) -> SUPERSEDED
C3(enabled, S3)  -> SUPERSEDED
C4(adaptive, S4) -> VALIDATED
```

`C1` and `C3` remain different immutable Claim identities with different Evidence/Snapshot chains even though their statement text matches.

This prevents history from being collapsed merely because upstream later reverts to an older behavior.

## Active competition invariant

Historical `SUPERSEDED` Claims remain visible in comparison history but do not count as active competitors.

When generation `Cn` is introduced, only the immediately previous active reviewed Claim and the new Claim participate in active competition. After the human supersession decision, only `Cn` remains active.

After v4:

- total Claim history for the subject is four Claims;
- exactly one Claim is active;
- the active Claim is `C4`;
- historical superseded Claims remain visible;
- there is no automatic winner or preferred-Claim field;
- no historical Claim is reactivated by statement equality.

## Forward-only disposition invariant

Supersession is not a mutable pointer update. Each transition is protected by a new append-only human disposition decision.

```text
C1 -> C2
C2 -> C3
C3 -> C4
```

Every predecessor remains terminally `SUPERSEDED`, retaining its original `last_verified`, Evidence set, and Snapshot lineage.

The existing Claim Disposition Gate also requires a successor to describe the same exact subject and to be at least `SUPPORTED`, preventing a terminal historical Claim from being used as a backward successor.

## Result

The four-generation acceptance test passed against the existing production implementation without any production-code, schema, or migration change.

This is evidence that the one-step Freshness Rule composes across repeated revisions rather than being a special-case two-generation path.

The acceptance does **not** prove automatic monitoring or automatic semantic change detection. It proves that once a new exact revision is presented through the governed intake path, the durable history can continue forward repeatedly without erasing or reviving older generations.

## Deliberate non-goals

Repeated Revision Chain v1 does not add:

- background polling;
- automatic creation of refresh Authorizations;
- automatic Claim generation;
- semantic deduplication;
- automatic revert detection;
- automatic resurrection of old Claims;
- automatic winner selection;
- automatic supersession;
- history compaction;
- Snapshot or reviewed-Claim mutation.

The governing principle is:

> A repeated upstream state is still a new observation at a new revision. Preserve the old generation, append the new generation, and move authority forward only through explicit governed decisions.
