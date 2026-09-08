# Problem Query v1

## Purpose

KNEEKURA TECH HUB is centered on technologies and design ideas, but practical research usually begins with a problem:

> **What techniques have evidence-backed claims that they solve this problem?**

Problem Query v1 answers that question without inventing a new storage model. It reads the Relation Projection layer, which is itself rebuilt from canonical Claims.

```text
Problem
  ↑ solves
Technique / Design Idea
  │
  └─ requires → prerequisite
```

Every result still leads back to the Relation Claim and Evidence that caused it to appear.

## Problem is a first-class Knowledge Entity

A Problem is a normal `knowledge_entity` whose `kinds` includes `problem`.

Example:

```json
{
  "record_type": "knowledge_entity",
  "id": "ke:problem:repeated-recomputation-after-input-change",
  "canonical_name": "Repeated recomputation after input changes",
  "kinds": ["problem"],
  "abstraction_level": "L1",
  "identity_state": "CANONICAL",
  "relations": []
}
```

The Hub does not infer Problem status from a name or from being the target of a relation.

## `solves` semantic contract

Problem Query v1 gives `solves` an explicit direction:

```text
solution entity --solves→ problem entity
```

A Relation Claim with type `solves` is rejected at creation time unless its target Knowledge Entity is explicitly classified with `kinds: ["problem", ...]`.

The query layer checks the same invariant again. If corrupted or legacy data contains `solves` pointing to a non-Problem, the query fails closed instead of silently treating the target as a Problem.

This double check protects both ingestion and read-time interpretation.

## Queries

### Solutions for a Problem

`solutions_for_problem(problem_id, view=...)`

Returns only explicit incoming `solves` Relation Claims for the selected Problem.

It does not infer solutions from:

- `related_to`;
- `inspired_by`;
- text similarity;
- repository popularity;
- shared tags;
- an AI guess made during query execution.

### Problems solved by one entity

`problems_solved_by(entity_id, view=...)`

Returns explicit outgoing `solves` Relation Claims whose targets are first-class Problem entities.

### Requirements for one entity

`requirements_for(entity_id, view=...)`

Returns explicit outgoing `requires` Relation Claims.

`requires` is not interpreted as a universal law. Scope, applicability, confidence, Evidence, and alternative interpretations remain attached through the projected Claim.

## Maturity views

Problem queries reuse Relation Projection views.

### `validated`

Only human-validated Relation Claims are returned. This is the trusted/default view.

### `research`

Includes Candidate, Supported, Validated, and Challenged Relation Claims. Use this when exploring possibilities rather than asking for accepted Hub knowledge.

### `challenged`

Shows only challenged assertions. This is useful for finding disputed problem/solution or dependency relationships.

### `history`

Includes rejected and superseded history for audit and design lineage.

The query function does not promote anything. Changing a result from research-only to validated requires the normal Claim maturity transition through the Curation Engine.

## Result shape

A solution result contains:

```json
{
  "solution": {
    "id": "ke:query-based-incremental-computation",
    "canonical_name": "Query-based Incremental Computation",
    "kinds": ["technique"],
    "abstraction_level": "L1",
    "identity_state": "CANONICAL"
  },
  "problem": {
    "id": "ke:problem:repeated-recomputation-after-input-change",
    "canonical_name": "Repeated recomputation after input changes",
    "kinds": ["problem"],
    "abstraction_level": "L1",
    "identity_state": "CANONICAL"
  },
  "relation_claim": {
    "claim_id": "...",
    "maturity": "...",
    "evidence_ids": ["..."],
    "created_by": {"...": "..."}
  }
}
```

The result intentionally includes the projected Relation Claim rather than returning only names. Consumers can therefore inspect Evidence, maturity, creator provenance, confidence, applicability, and alternative interpretations.

## Real Salsa pilot overlay

`pilots/incremental-computation-problems-v1.json` extends the immutable base pilot without rewriting it.

It introduces:

- Problem: `Repeated recomputation after input changes`;
- Technique: `Memoization`;
- Candidate inference: `Query-based Incremental Computation solves Repeated recomputation after input changes`;
- Candidate inference: `Query-based Incremental Computation requires Memoization`.

Both relation claims are scoped to the pinned Salsa material and begin at `CANDIDATE` with `MEDIUM` confidence.

The `solves` claim explicitly records that a future vocabulary might prefer `mitigates`. The `requires` claim explicitly records that Memoization may be better modeled as an implementation technique/component rather than a universal prerequisite.

These alternatives are preserved rather than being hidden by the query layer.

## Real-pilot acceptance behavior

Before human validation:

```text
validated solutions      → none
research solutions       → Query-based Incremental Computation
validated requirements   → none
research requirements    → Memoization
```

After human promotion of the two Relation Claims through `SUPPORTED` to `VALIDATED`:

```text
validated solutions      → Query-based Incremental Computation
validated requirements   → Memoization
```

No `KnowledgeEntity.relations` field is populated during this process. The result changes because Claim maturity changes, not because a duplicate graph is rewritten.

## CLI

```bash
# trusted solutions for a Problem
kneekura-hub solutions \
  ke:problem:repeated-recomputation-after-input-change \
  --view validated

# research candidates for the same Problem
kneekura-hub solutions \
  ke:problem:repeated-recomputation-after-input-change \
  --view research

# Problems an entity explicitly claims to solve
kneekura-hub solved-problems \
  ke:query-based-incremental-computation \
  --view research

# Explicit prerequisites / dependencies
kneekura-hub requirements \
  ke:query-based-incremental-computation \
  --view research
```

All three commands are read-only.

## Non-goals

Problem Query v1 does not:

- infer unstored relations at query time;
- rank technologies by GitHub stars or popularity;
- merge competing solution Claims;
- decide that `related_to` means alternative;
- turn a target into a Problem merely because a `solves` string points at it;
- claim that a scoped `requires` relation is universally necessary;
- create a graph database or materialized query table.

## Next pressure

The strongest next addition is not more relation vocabulary. It is an **Evidence Explanation query** that can answer:

> Why did this result appear?

Given a Claim or projected result, it should walk:

```text
Claim → Evidence → SourceSnapshot → Source
```

and expose the exact provenance chain without modifying canonical records.
