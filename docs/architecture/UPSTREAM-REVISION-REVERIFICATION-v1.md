# Upstream Revision / Re-verification v1

## Purpose

KNEEKURA TECH HUB must be able to observe a newer upstream revision without rewriting the history captured from an older revision.

The Freshness Rule is therefore implemented as **append new evidence, then govern knowledge lifecycle**:

```text
same Source identity
    ├─ exact revision v1 -> immutable SourceSnapshot S1 -> reviewed Claim C1
    └─ exact revision v2 -> immutable SourceSnapshot S2 -> new Claim C2

C1 is never rewritten to look as if it came from v2.
```

This contract applies to the existing bounded `selected-files` acquisition path. It does not introduce a crawler, background polling, automatic contradiction inference, or automatic Claim disposition.

## Stable Source identity

An upstream repository remains the same `src:*` identity across revisions. A new commit SHA is not a new Source.

Changing upstream state creates another immutable `SourceSnapshot` under that Source. Previous Snapshots remain resolvable and immutable.

```text
src:S
  ├─ ss:S:v1
  └─ ss:S:v2
```

## One-shot acquisition authority

A human `AUTHORIZE` record is an exact, bounded, one-shot grant. It is not permanent permission to keep fetching a Source forever.

A grant becomes consumed only when an append-only `source_acquisition_commit` exists for that exact `authorization_id`.

`SourceSnapshot.metadata` is not used as the authority proof for consumption. Snapshot metadata may describe provenance, but only the Verified Acquisition Commit path is authoritative for proving that the grant was actually consumed.

After the initial verified commit, `source.acquisition.level` is `selected-files`. A later refresh is allowed only when all normal live prerequisites still hold and the new human grant:

1. is itself an exact `AUTHORIZE` for `selected-files`;
2. explicitly supersedes the current active authorization;
3. supersedes an `AUTHORIZE` for the same Source;
4. the predecessor has an append-only Verified Acquisition Commit;
5. the active Source selection is still `SELECT_FOR_REVIEW`;
6. license metadata is still resolved;
7. the new grant has not itself already been committed.

Conceptually:

```text
A1 --verified commit--> S1
 |
 +-- consumed

human creates fresh exact authority

A1 <-supersedes- A2 --execution--> verified commit --> S2
                  |
                  +-- consumed after commit
```

A consumed A1 cannot be reused. After A2 is committed, A2 cannot be reused either. A future refresh requires A3.

## No acquisition-depth escalation

Refresh does not expand acquisition authority. The authorization schema continues to fix this path to `selected-files`.

A Source already at another acquisition depth is not accepted by this refresh contract. In particular, this mechanism is not a path to `full-source` acquisition.

## Atomic refresh commit

Verified refresh uses the same atomic publication boundary as the initial acquisition.

Inside the PostgreSQL transaction the implementation:

- locks Source, selection, authorization, and execution authority rows;
- rechecks exact Source and Authorization fingerprints;
- rechecks live authorization effectiveness;
- re-verifies the fetched filesystem bytes;
- inserts the new immutable SourceSnapshot;
- keeps Source acquisition depth at `selected-files` while advancing acquisition freshness metadata;
- inserts the append-only `source_acquisition_commit`;
- appends the `SOURCE_ACQUIRE` curation event.

The expected pre-commit Source acquisition level is included in the guarded Source update. A concurrent state change therefore fails closed.

Because authorization effectiveness checks the Verified Acquisition Commit history, a second execution cannot successfully consume the same refresh grant after the first commit wins the transaction.

## Knowledge re-verification

A new SourceSnapshot does not automatically modify Claim maturity.

If v2 supports a statement that differs from a reviewed v1 Claim:

```text
C1 VALIDATED from S1

new S2 arrives
  -> create separate C2 CANDIDATE
  -> Comparison exposes multiple active Claims / differing statements
  -> no automatic winner
  -> no automatic contradiction label
  -> human competition acknowledgement is required for Support/Validation
```

Automation or AI may move an old reviewed Claim to `CHALLENGED` as a re-verification warning under the existing lifecycle authority. `CHALLENGED` preserves the reviewed Claim's epistemic payload, Evidence set, and historical `last_verified` value.

AI may not resolve its own warning by promoting the Claim to `VALIDATED`, and AI may not make protected terminal decisions.

If a newer Claim is ultimately accepted as the replacement, a human may use the existing Claim Disposition Gate to mark the old Claim `SUPERSEDED` by the newer Claim. The successor must describe the same exact subject and be at least `SUPPORTED`.

## Historical explanation invariant

After supersession, both generations remain independently explainable:

```text
old Claim C1
  -> Evidence E1
  -> SourceSnapshot S1
  -> Source S

new Claim C2
  -> Evidence E2
  -> SourceSnapshot S2
  -> Source S
```

The old evidence chain is historical truth about what was observed at v1. Supersession changes current knowledge lifecycle; it does not erase past provenance.

## Deliberate non-goals

v1 does not add:

- automatic upstream polling;
- automatic refresh authorization;
- automatic Claim challenge on every new Snapshot;
- automatic contradiction classification;
- automatic winner selection;
- automatic supersession or rejection;
- a new freshness score;
- mutable SourceSnapshots or mutable reviewed Claims.

The governing principle is:

> New upstream state adds a new immutable observation of reality. It never rewrites the old observation into a different history.
