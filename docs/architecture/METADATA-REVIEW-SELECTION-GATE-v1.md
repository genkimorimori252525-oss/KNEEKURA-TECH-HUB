# Metadata Review & Selection Gate v1

## Purpose

KNEEKURA TECH HUB can now discover public GitHub repositories at bounded scale while keeping every discovered Source at `metadata-only` acquisition.

The next danger is not discovery itself. It is **depth escalation**.

A crawler can find hundreds of repositories. If a popularity signal, repeated search hit, or AI interpretation can silently turn one of those Sources into selected-file or full-source acquisition, the Hub has recreated the same authority problem at a later stage.

Metadata Review & Selection Gate v1 therefore separates:

```text
Discovery
   ↓
metadata-only Source
   ↓
Human Selection Decision
   ↓
SELECT_FOR_REVIEW / DEFER / REJECT_FOR_REVIEW
   ↓
(no acquisition mutation)
```

A selection decision is a governance record about **what deserves further human investigation**. It is not permission to fetch files.

## Core invariant

```text
SELECT_FOR_REVIEW
      ≠
selected-files acquisition
```

Recording any v1 Source selection decision must leave the Source unchanged:

```text
source.acquisition.level == metadata-only
```

before and after the decision.

SourceSnapshot creation, selected-file retrieval, license resolution, Evidence extraction, and acquisition-level upgrade remain outside this layer.

## Record type

v1 introduces an append-only governance record:

```text
source_selection_decision
```

IDs use:

```text
sd:<id>
```

Required fields:

- `source_id`
- `decision`
- `rationale`
- `created_by`
- `policy_version`
- `decided_at`

Optional correction linkage:

- `supersedes_decision_id`

Decision vocabulary:

- `SELECT_FOR_REVIEW`
- `DEFER`
- `REJECT_FOR_REVIEW`

`REJECT_FOR_REVIEW` rejects deeper review at this selection layer. It does not delete the Source, blacklist the repository forever, or make a claim that the technology is bad.

## Human authority boundary

Canonical Source selection decisions are human-only in v1.

AI, scanners, and tools may discover Sources and may later gain a separate suggestion mechanism, but they cannot create `source_selection_decision` records.

The acting identity must exactly match `created_by`.

This deliberately avoids:

```text
AI finds repo
→ AI marks it selected
→ later system interprets selected as authorized
```

No AI-only path crosses the selection boundary.

## Metadata-only scope

Selection Gate v1 accepts only Sources whose current acquisition level is:

```text
metadata-only
```

It refuses to govern Sources already at `snapshot`, `selected-files`, or `full-source` depth. Those states belong to later acquisition governance.

This prevents the selection layer from becoming a generic mutation mechanism for every Source lifecycle state.

## Append-only correction model

A Source may have only one active selection decision.

If a human changes judgment, the new record must explicitly supersede the active record:

```text
sd:first
SELECT_FOR_REVIEW
      ↓ superseded by
sd:second
DEFER
```

Both remain in history.

A correction must:

- concern the same Source;
- supersede the currently active decision;
- never supersede itself;
- never branch one old decision into multiple active successors.

Parallel conflicting active decisions are rejected rather than silently resolved by timestamp or majority vote.

## No popularity authority

The selection decision schema contains no:

- star score;
- popularity score;
- repeated-hit score;
- repository rank;
- global quality scalar.

A human may inspect metadata while deciding, but the Hub does not convert GitHub popularity into selection authority.

Repeated discovery hits remain provenance, not votes.

## No license laundering

A Source can be selected for **review** even when its license state is `REVIEW_REQUIRED` or `UNKNOWN`, because selection does not deepen acquisition.

Selection must not:

- convert a GitHub Search API license hint into `KNOWN`;
- change `declared_expression`;
- change `handling_policy`;
- bypass the metadata-only restriction for unresolved licensing.

License verification remains a separate action before any future depth escalation.

## PostgreSQL persistence

Migration `0005_source_selection_decision.sql` adds an append-only table with:

- Source foreign key;
- decision vocabulary check;
- non-empty rationale constraint;
- self-supersession guard;
- one direct successor per decision.

`SelectionPostgresRepository` is intentionally a thin governance extension over the existing `PostgresRepository`.

Existing core record persistence is not rewritten for this slice.

## Read views

Three read concepts are exposed:

### History

All decisions for a Source, including superseded judgments.

### Active

Only decisions that have not been superseded.

### Selected for review

Active `SELECT_FOR_REVIEW` decisions paired with the current unchanged Source record.

This view remains descriptive. It is not an acquisition work queue with implicit file-fetch permission.

## CLI

Record a human selection:

```bash
kneekura-source-selection decide \
  src:github:owner:repo \
  SELECT_FOR_REVIEW \
  --rationale 'Architecture is relevant enough for manual review.' \
  --actor-id reviewer
```

Correct an earlier decision without rewriting it:

```bash
kneekura-source-selection decide \
  src:github:owner:repo \
  DEFER \
  --rationale 'License provenance needs manual resolution first.' \
  --actor-id reviewer \
  --supersedes sd:previous
```

Read history and active state:

```bash
kneekura-source-selection history --source-id src:github:owner:repo
kneekura-source-selection active --source-id src:github:owner:repo
kneekura-source-selection selected
```

`KTHUB_DATABASE_URL` is required for the CLI.

## Security / governance posture

Selection Gate v1:

- is human-only;
- is append-only;
- does not mutate Source records;
- does not change acquisition depth;
- does not create SourceSnapshots;
- does not create Evidence;
- does not create StagedObservations;
- does not create Claims or Knowledge Entities;
- does not treat popularity as quality;
- does not verify licenses implicitly;
- does not execute repository code.

## Non-goals

v1 does not:

- automatically recommend Sources with a universal score;
- automatically select Sources after N search hits;
- automatically select high-star repositories;
- let AI create canonical selection decisions;
- fetch README or source files;
- create a SourceSnapshot;
- upgrade `acquisition.level`;
- resolve licenses;
- infer technology quality;
- promote knowledge.

## Next pressure

After this gate is verified, the next safe slice is **Acquisition Authorization v1**.

That future layer should require an active human `SELECT_FOR_REVIEW` decision plus explicit license/provenance checks before allowing a specific, bounded acquisition request such as README-only or an exact selected-file set.

Even then, authorization and actual retrieval should remain separate records/actions so that the Hub can answer:

```text
Who selected this Source?
Why was it selected?
Who authorized deeper acquisition?
What exact files/revision were authorized?
What was actually retrieved?
```

without reconstructing intent from mutable Source state.
