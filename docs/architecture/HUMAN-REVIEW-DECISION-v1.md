# Human Review Decision v1

## Purpose

Claim Comparison v1 intentionally stops before deciding that two Claims contradict, agree, qualify one another, or should replace one another.

Human Review Decision v1 adds the missing governance layer:

```text
Claim A ─┐
         ├─ Human Review Decision
Claim B ─┘
```

The decision is its own canonical record. It does not rewrite either Claim and it does not merge their Evidence.

## Record type

Human decisions use `record_type: review_decision` and IDs beginning with `rd:`.

Required fields:

- `source_claim_id`;
- `target_claim_id`;
- `decision`;
- `rationale`;
- `created_by`;
- `policy_version`;
- `decided_at`.

Optional field:

- `supersedes_decision_id`.

## Decision vocabulary

v1 supports:

- `CONTRADICTS` — the reviewer judges the two Claims incompatible in the reviewed scope;
- `COMPATIBLE` — the reviewer judges that both Claims can hold together;
- `QUALIFIES` — the source Claim narrows or conditions the target Claim;
- `DUPLICATE` — the reviewer judges the Claims semantically duplicative;
- `SUPERSEDES` — the source Claim is judged to replace the target Claim for this review context;
- `UNRESOLVED` — review is explicit, but the reviewer does not yet assert one of the stronger relationships.

`source_claim_id → target_claim_id` is directional. That matters for `QUALIFIES` and `SUPERSEDES`. Symmetric decisions still preserve the authored direction as provenance.

## Human-only gate

A `review_decision` is a canonical human judgment.

Therefore:

- `created_by.actor_type` must be `human`;
- the acting identity must exactly match `created_by`;
- AI, tools, and system actors cannot create these records.

AI may still surface comparison groups, Evidence, possible disagreement, or a proposed review question. It cannot write the human verdict.

## Exact-subject boundary

Both referenced Claims must exist and must share the same exact Claim subject used by Claim Comparison v1.

Entity Claim key:

```text
(entity, entity_id)
```

Relation Claim key:

```text
(relation, source_entity_id, relation_type, target_entity_id)
```

This prevents a reviewer action intended for one question from accidentally becoming a verdict across unrelated Claims.

v1 does not silently resolve entity-merge redirects before checking this boundary.

## No automatic Claim mutation

Creating a Decision does **not**:

- change Claim maturity;
- set `superseded_by`;
- validate a Claim;
- challenge a Claim;
- reject a Claim;
- combine Evidence;
- choose a query winner.

For example:

```text
review_decision.decision = SUPERSEDES
```

records the human judgment only. If the reviewer also intends to move a Claim to `SUPERSEDED`, the normal governed Claim transition remains a separate explicit action.

This separation keeps:

```text
what the reviewer judged
```

and

```text
what lifecycle transition was applied
```

as different auditable facts.

## Append-only correction

Review Decisions are append-only.

A Decision is not edited in place when a reviewer later changes their mind. Instead, a new Decision can name:

```text
supersedes_decision_id: rd:previous
```

The successor must concern the same unordered Claim pair.

v1 allows one direct successor per Decision. A branching correction would make the active human judgment ambiguous, so it fails closed.

The previous Decision remains retrievable as history.

## Active Decision view

A Decision is active when no later Decision explicitly names it as `supersedes_decision_id`.

The read layer exposes both:

- full history;
- currently active Decisions.

No timestamp heuristic is used to guess which Decision wins. Supersession must be explicit.

## Decision context

`decision_context_for_claim` combines two read models without changing either one:

```text
Claim Comparison
      +
Human Decision History
      ↓
Decision Context
```

The result contains:

- the exact-subject Claim comparison;
- full Decision history for Claims in that comparison group;
- active Decisions;
- Decision counts.

Claim Comparison still does not generate a `winner` or contradiction verdict by itself.

## PostgreSQL persistence

Migration `0004_human_review_decision.sql` adds normalized `review_decision` persistence with:

- Claim foreign keys;
- allowed Decision vocabulary;
- distinct source/target Claim constraint;
- non-empty rationale;
- self-supersession rejection;
- one-successor-per-Decision uniqueness;
- source/target indexes.

The domain layer additionally verifies same-subject semantics and acting human identity because those rules depend on Claim content and governance context, not only row-local SQL constraints.

## Schema

`schemas/v1/review-decision.schema.json` is intentionally separate from the original Hub core schema.

This makes the governance extension explicit rather than silently rewriting the already-established v1 core record union. `validate_record` dispatches `review_decision` records to this schema and keeps existing records on `hub.schema.json`.

## CLI

Create a human Decision:

```bash
kneekura-hub decide-claims \
  cl:source \
  cl:target \
  UNRESOLVED \
  --reason "statement difference alone is not enough" \
  --actor-id reviewer
```

Optionally provide a stable ID:

```bash
--decision-id rd:example
```

Supersede an earlier Decision without deleting it:

```bash
kneekura-hub decide-claims \
  cl:source \
  cl:target \
  COMPATIBLE \
  --reason "scope review shows both can hold" \
  --supersedes-decision-id rd:example \
  --actor-id reviewer
```

Read Decision history:

```bash
kneekura-hub review-decisions
kneekura-hub review-decisions --claim-id cl:example
kneekura-hub review-decisions --active
```

Read comparison plus Decisions:

```bash
kneekura-hub decision-context cl:example
```

## Real Salsa acceptance

The real Salsa Problem Query pilot is loaded at its pinned revision and a second Candidate inference is added for the same `solves` subject.

The acceptance path then records:

1. `UNRESOLVED` — the human reviewer refuses to infer contradiction from statement difference alone;
2. a later `COMPATIBLE` Decision that explicitly supersedes the first Decision.

The test verifies that:

- both Decision records remain stored;
- only the second is active;
- both Claims are unchanged before and after both Decisions;
- Claim Comparison still contains no winner field;
- PostgreSQL round-trip preserves Decision provenance.

## Non-goals

Human Review Decision v1 does not:

- let AI issue canonical contradiction judgments;
- infer contradiction from text difference;
- mutate Claim lifecycle automatically;
- perform semantic entailment;
- score reviewer authority;
- resolve reviewer disagreement by voting;
- delete old Decisions;
- group across entity redirects;
- turn `SUPERSEDES` Decision into an automatic Claim transition.

## Next pressure

After this layer is stable, the Hub can safely consider either:

1. an explicit resolved-identity comparison view that crosses approved entity redirects while retaining historical subjects; or
2. the first controlled Discovery ingestion slice, because disagreements now have a place to remain visible and receive traceable human judgment instead of being collapsed during large-scale collection.
