# Explainable Context Guidance v1

## Status

Acceptance architecture for the read-only bridge from context-aware Claim selection to exact provenance explanation.

This slice builds on two already-proven capabilities:

1. `contextual_claims_for_entity(...)` preserves multiple VALIDATED Claims and narrows them only by explicit exact applicability context.
2. `explain_claim(...)` reconstructs the exact `Claim -> Evidence -> SourceSnapshot -> Source` chain and fails closed when the chain is incomplete or inconsistent.

The purpose of this slice is to compose those capabilities without introducing a new authority mechanism.

## Problem

Before this slice the Hub could answer two separate questions:

```text
Which VALIDATED Claims exactly match this explicit context?
```

and

```text
What Evidence / SourceSnapshot / Source supports this Claim?
```

But there was no single read boundary that guaranteed a context-selected Claim was the same Claim whose provenance was then explained.

That gap matters because an application could otherwise perform selection and explanation independently and accidentally present a stale or mismatched provenance chain as the reason for trusted guidance.

The test-first Defect Proof reproduced the missing boundary as:

```text
ImportError: cannot import name 'explain_contextual_guidance'
```

No storage defect was required to explain the gap. The missing capability was a narrow composition boundary.

## Canonical read path

```text
Knowledge Entity
      +
explicit context
      |
      v
contextual_claims_for_entity(...)
      |
      +-- exact applicability subset matching
      +-- VALIDATED non-relation Claims only
      +-- no fuzzy fallback
      +-- no ranking
      +-- no winner
      |
      v
candidate Claim(s)
      |
      v
explain_contextual_guidance(...)
      |
      +-- explain_claim(candidate)
      +-- verify explained Claim == selected Claim copy
      |
      v
Claim
  -> Evidence
  -> SourceSnapshot
  -> Source
```

The combined function is read-only.

## Resolution preservation

`explain_contextual_guidance(...)` does not reinterpret the context query's resolution.

### Exact one-match context

```text
context = {"ecosystem": "Go"}

context query
  -> ONE_MATCH
  -> Go/gofmt Claim

explanation
  -> same Go/gofmt Claim
  -> Evidence
  -> exact SourceSnapshot
  -> Source
```

The presence of a full provenance explanation does not create a new score or increase Claim authority. It only exposes why the existing VALIDATED Claim is available for that explicit context.

### Ambiguous or missing context

If multiple VALIDATED Claims remain applicable:

```text
no context
  -> CONTEXT_REQUIRED
  -> Claim A
  -> Claim B
```

both candidates are explained independently:

```text
Claim A -> Evidence A -> Snapshot A -> Source A
Claim B -> Evidence B -> Snapshot B -> Source B
```

The explanation layer does not create:

- `winner`
- `preferred_claim_id`
- a score
- a popularity tie-breaker
- a freshness tie-breaker
- semantic similarity arbitration

Explanation is not selection authority.

### No match

```text
context = {"ecosystem": "Rust"}
  -> NO_MATCH
  -> zero candidate Claims
  -> zero explanations
```

There is no nearest-neighbor or best-effort fallback.

## Fail-closed provenance

Every candidate is passed through the existing `explain_claim(...)` chain reconstruction.

If any required record is absent or inconsistent, the entire combined read fails instead of returning a partial explanation that could appear complete.

Examples include:

- missing Evidence
- missing SourceSnapshot
- missing Source
- wrong record type
- Evidence Snapshot belonging to a different Source

This preserves the existing evidence-explanation integrity boundary rather than duplicating it.

## Observed Claim-change guard

The context query returns a copy of every selected Claim. During explanation the Claim is read again through `explain_claim(...)`.

The combined read requires:

```text
selected Claim copy == explained Claim
```

If they differ, the operation raises `ExplanationError`:

```text
contextual guidance Claim changed during explanation
```

The acceptance test deliberately simulates a Claim changing from `VALIDATED` to `CHALLENGED` after context selection. The stale selected Claim is not returned as trusted explained guidance.

This check protects against a change that is actually observed by the second read.

## Concurrency boundary

This v1 contract does **not** claim transactionally snapshot-isolated or serializable reads across the whole operation.

For example, it does not promise to detect every possible change that happens after a candidate has already been explained but before the caller receives the result.

That stronger guarantee would require a repository/transaction semantics decision broader than this proven defect. No new transaction machinery is introduced here without evidence that the current read contract is insufficient in practice.

The guarantee is intentionally narrower:

> If the Claim re-read used for provenance explanation differs from the Claim selected by the context query, fail closed rather than present stale trusted guidance.

## PostgreSQL acceptance

The production repository path is covered separately from the MemoryRepository contract.

The PostgreSQL acceptance creates a governed Claim lifecycle:

```text
Source
  -> SourceSnapshot at exact revision
  -> Evidence
  -> CANDIDATE Claim
  -> human SUPPORTED
  -> human VALIDATED
  -> exact context query
  -> provenance explanation
```

The pinned Go revision used by the acceptance is:

```text
5d12b248d5520ff5adafeb9be9acc2148399ca49
```

The proof confirms that `PostgresRepository.list("claim")` and `PostgresRepository.get(claim_id)` materialize compatible Claim representations for the equality guard and that the final explanation preserves the exact Claim, Evidence, Snapshot revision, and Source.

## Authority Ceiling

This slice does not authorize any new write or epistemic transition.

It does not:

- create Claims
- validate Claims
- challenge Claims
- supersede Claims
- create Evidence
- mutate SourceSnapshots
- resolve conflicts
- choose a universal best practice

It only reads records whose authority was already established elsewhere and exposes their provenance.

## Preservation properties

The design preserves:

1. **Claim identity** — explanation refers to the exact Claim selected by context.
2. **Evidence identity** — the Claim's recorded Evidence IDs are followed without substitution.
3. **Snapshot identity** — Evidence resolves to the exact immutable SourceSnapshot.
4. **Source identity** — provenance terminates at the exact Source represented by the Evidence chain.
5. **Ambiguity** — multiple valid contextual candidates remain multiple candidates.
6. **No-match truth** — absence of an exact match remains absence rather than a guessed recommendation.
7. **Read-only behavior** — explaining guidance does not mutate repository state.

## Non-goals

This v1 intentionally does not introduce:

- a recommendation table
- a context ontology
- fuzzy context matching
- semantic embeddings
- ranking or scoring
- source popularity weighting
- automatic freshness preference
- automatic conflict resolution
- a preferred Claim field
- automatic lifecycle changes
- new schema or migrations
- transactionally snapshot-isolated multi-record reads
- UI or CLI formatting policy

## Governing principle

> Context may narrow already-governed knowledge, and provenance may explain that narrowing, but explanation must never become a hidden authority mechanism. If the selected Claim and the Claim actually explained no longer agree, fail closed.