# Staged Observation Triage v1

## Status

- Architecture slice: Phase 2 / guarded semantic intake
- Input: existing `StagedObservation` records backed by exact Evidence
- Output: append-only triage decisions and, only on human promotion, a `Claim` at `CANDIDATE`
- Canonical Entity merge: out of scope
- Claim `SUPPORTED` / `VALIDATED`: out of scope
- Semantic auto-merge: out of scope

## Purpose

`StagedObservation` is deliberately a lower-trust boundary. It may have been created by AI or another extractor and therefore must not silently become curated truth.

Triage v1 turns this lower-trust pool into an operational review queue while preserving the central TECH HUB rule:

> Discovery may be cheap. Promotion of meaning must remain governed.

Triage answers questions such as:

- Which observations still need review?
- Which observations are exact extraction duplicates?
- Which observations reuse the same Evidence but interpret it differently?
- What Source and SourceSnapshot support this observation?
- Who changed its lifecycle state, why, and under which policy version?
- Has a human chosen to turn it into a Claim Candidate?

Triage does **not** answer whether a technology is true, good, recommended, or canonical.

## Trust boundary

The pipeline after Canonical Selected-File Evidence Extraction is:

```text
Committed SourceSnapshot
        ↓
Exact Evidence
        ↓
StagedObservation (NEW, lower trust)
        ↓
Staged Observation Triage
        ├─ TRIAGED
        ├─ REJECTED
        ├─ EXPIRED
        └─ PROMOTED
              ↓
        Claim CANDIDATE
```

There is no path in this slice from a StagedObservation directly to:

- `SUPPORTED`
- `VALIDATED`
- a new canonical Knowledge Entity
- Entity merge
- recommendation/adoption authority

## Lifecycle

A newly created `StagedObservation` must always begin at:

```text
NEW
```

Allowed transitions are:

```text
NEW
 ├─ MARK_TRIAGED ───────────────→ TRIAGED
 ├─ REJECT ─────────────────────→ REJECTED
 └─ EXPIRE ─────────────────────→ EXPIRED

TRIAGED
 ├─ REJECT ─────────────────────→ REJECTED
 ├─ EXPIRE ─────────────────────→ EXPIRED
 └─ PROMOTE_TO_CLAIM_CANDIDATE → PROMOTED
                                      ↓
                                Claim CANDIDATE
```

`PROMOTED`, `REJECTED`, and `EXPIRED` are terminal in v1.

A new Observation cannot be inserted directly as `TRIAGED`, `PROMOTED`, `REJECTED`, or `EXPIRED`.

## Actor authority

### AI

AI may create a `NEW` StagedObservation through the extraction boundary.

AI may not mutate Observation lifecycle state.

This includes no AI authority for:

- `MARK_TRIAGED`
- `REJECT`
- `EXPIRE`
- `PROMOTE_TO_CLAIM_CANDIDATE`

### Tool / system

Tool and system actors may perform only bounded mechanical lifecycle work:

- `MARK_TRIAGED`
- `EXPIRE`

They may not:

- reject an interpretation as a substantive judgment;
- promote an Observation into a Claim Candidate.

### Human

Human actors may perform every v1 triage action:

- `MARK_TRIAGED`
- `REJECT`
- `EXPIRE`
- `PROMOTE_TO_CLAIM_CANDIDATE`

Human authority at this layer still does not imply `SUPPORTED` or `VALIDATED` knowledge.

## Append-only ObservationTriageDecision

Every lifecycle change after creation produces one immutable `observation_triage_decision` record containing:

- decision ID
- Observation ID
- action
- previous status
- next status
- non-empty reason
- actor
- optional resulting Claim ID
- policy version
- decision timestamp

The decision table is append-only.

A unique database index on:

```text
(observation_id, from_status)
```

prevents two different histories from branching out of the same Observation state.

## Database-level lifecycle pairing

Service-layer checks are not sufficient because repository or SQL callers could otherwise update `staged_observation.status` directly.

Migration `0010_observation_triage_decision.sql` therefore enforces the lifecycle boundary in PostgreSQL as well.

### Creation guard

A database trigger rejects insertion of a new Observation whose initial status is not `NEW`.

### Status → Decision check

A deferred constraint trigger requires every status mutation to have a matching triage decision in the same transaction:

```text
Observation ID
+ old status
+ new status
```

A direct status-only update cannot commit.

### Decision → Status check

A second deferred constraint trigger requires every inserted triage decision to correspond to the Observation's actual resulting status at transaction commit.

An audit-only decision that was never applied cannot commit either.

The pairing is intentionally bidirectional:

```text
status change without decision  → reject

decision without status change  → reject
```

The checks are deferred so the transaction may write the two sides in either internal order while still publishing them atomically.

## Promotion to Claim Candidate

`PROMOTE_TO_CLAIM_CANDIDATE` is human-only and valid only from `TRIAGED`.

Promotion is not a status-only operation. The same transaction must create a new Claim.

The caller may propose only the bounded semantic fields:

- Claim ID
- exactly one subject:
  - existing `entity_id`, or
  - existing relation subject
- Claim type
- statement
- optional scope
- optional applicability
- optional confidence
- optional reasoning basis
- optional alternative interpretations

The caller may **not** supply:

- `record_type`
- maturity
- Evidence IDs
- creator
- policy version
- verification timestamps
- supersession fields

The Hub supplies those governance fields itself.

The resulting Claim is forced to:

```text
maturity = CANDIDATE
```

and inherits the Observation's Evidence IDs exactly.

The caller therefore cannot replace or expand provenance during promotion.

## Promotion atomicity

For PostgreSQL, promotion runs inside one outer transaction:

```text
lock Observation row
  ↓
re-read current state
  ↓
validate actor + transition
  ↓
create Claim CANDIDATE
  ↓
update Observation → PROMOTED
  ↓
append ObservationTriageDecision
  ↓
round-trip verification
  ↓
commit
```

If any later operation fails, all earlier operations roll back, including:

- Claim creation
- `CLAIM_CREATE` curation event
- Observation status update
- triage decision

There must never be a Claim created from a promotion transaction whose Observation remained `TRIAGED`, nor a `PROMOTED` Observation without its Claim and triage decision.

## Duplicate candidate discovery

Triage v1 provides two read-only grouping signals.

### Exact-content candidate group

The content signature uses:

- Source ID
- sorted Evidence candidate IDs
- summary
- normalized candidate names

It intentionally excludes:

- Observation ID
- creator actor
- lifecycle status

Therefore two independent extractors may produce an exact-content duplicate candidate without losing their separate provenance records.

No records are merged.

### Shared-Evidence candidate group

Observations that point to the same Evidence set are grouped as a weaker signal.

If their content signatures differ, the group explicitly reports multiple interpretations of the same Evidence.

This is **not** semantic equivalence.

For example:

```text
same Evidence
  ├─ "incremental recomputation"
  └─ "cache invalidation"
```

must remain two interpretations until separately reviewed.

## Why semantic auto-merge is deferred

A semantic model can easily collapse neighboring but materially different concepts.

Examples include:

- caching vs memoization
- invalidation vs incremental recomputation
- event sourcing vs audit logging
- retry vs idempotency

At Hub scale, a small false-merge rate would corrupt a large amount of knowledge.

Therefore v1 deliberately supports:

- exact grouping;
- shared-Evidence grouping;
- human review;

but not semantic canonical merge.

## Provenance display

`observation_context()` reconstructs the review context from existing records:

```text
StagedObservation
  ↓
Evidence[]
  ↓
exactly one SourceSnapshot
  ↓
Source
  ↓
ObservationTriageDecision history
```

It rejects corrupted context where:

- Evidence belongs to another Source;
- Evidence spans multiple SourceSnapshots;
- Snapshot belongs to another Source.

Triage does not re-run acquisition or reinterpret the physical source store. That responsibility belongs to the earlier acquisition/extraction boundary.

## Review queue

The default queue contains:

- `NEW`
- `TRIAGED`

Terminal observations are omitted by default.

Each queue item contains:

- Observation
- Evidence
- SourceSnapshot
- Source
- prior triage decisions
- exact duplicate candidate IDs
- shared-Evidence candidate IDs

This keeps large lower-trust discovery pools searchable without pretending every item deserves canonical promotion.

## CLI

Read-only queue:

```bash
kneekura-observation-triage queue
```

Filter by lifecycle status:

```bash
kneekura-observation-triage queue --status NEW
```

Inspect exact provenance:

```bash
kneekura-observation-triage show obs:<id>
```

Inspect duplicate candidates without merging:

```bash
kneekura-observation-triage duplicates
```

Inspect append-only decision history:

```bash
kneekura-observation-triage history --observation-id obs:<id>
```

Mechanical triage:

```bash
kneekura-observation-triage transition obs:<id> MARK_TRIAGED \
  --reason "Exact Evidence and bounded extraction are structurally reviewable." \
  --actor-type tool \
  --actor-id triage-worker \
  --actor-version v1
```

Human promotion:

```bash
kneekura-observation-triage transition obs:<id> PROMOTE_TO_CLAIM_CANDIDATE \
  --reason "Human accepts this interpretation as worth formal Claim review." \
  --actor-type human \
  --actor-id reviewer \
  --claim-candidate claim-candidate.json
```

The Claim Candidate JSON cannot contain maturity or Evidence IDs.

## Migration parser hardening

Triage v1 requires deferred PostgreSQL constraint triggers implemented with PL/pgSQL functions.

The previous migration loader split SQL with `str.split(';')`, which corrupts:

- function bodies;
- quoted strings;
- comments containing semicolons;
- dollar-quoted PostgreSQL blocks.

The migration splitter is hardened in this slice with a deterministic lexer that recognizes:

- single-quoted strings;
- double-quoted identifiers;
- `--` line comments;
- nested `/* ... */` block comments;
- `$$ ... $$` dollar quotes;
- `$tag$ ... $tag$` dollar quotes.

Only top-level semicolons terminate migration statements.

This is infrastructure hardening, not a relaxation of migration drift checks. Migration filenames and SHA-256 checksums remain the authority for applied migration history.

## V1 invariants

The slice is accepted only if all of the following remain true:

1. New Observations enter through `NEW` only.
2. AI lifecycle mutations = 0.
3. Tool/system substantive reject/promote authority = 0.
4. Status-only PostgreSQL lifecycle updates = 0.
5. Decision-only PostgreSQL lifecycle updates = 0.
6. Branching transition histories from one state = 0.
7. Promotion without human actor = 0.
8. Promotion without existing subject = 0.
9. Promotion caller-controlled Evidence IDs = 0.
10. Promotion caller-controlled maturity = 0.
11. Promotion result above `CANDIDATE` = 0.
12. Partial promotion transactions = 0.
13. Automatic semantic duplicate merge = 0.
14. Automatic canonical Entity creation/merge = 0.
15. Triage decisions are append-only.

## Next boundary

After Triage v1, the next safe semantic boundary is **Claim Candidate Review / Support Gate**.

That later slice may decide when a `CANDIDATE` Claim has sufficient support to move to `SUPPORTED`, while preserving:

- Claim type-specific evidence requirements;
- evidence independence families;
- counterevidence;
- human authority ceilings;
- no AI-only `VALIDATED` promotion.

Those rules do not belong inside Observation Triage.
