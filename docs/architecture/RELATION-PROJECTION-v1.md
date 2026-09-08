# Relation Projection v1

## Purpose

Relation Provenance v1 made Relation Claims the authoritative store for relationships between Knowledge Entities. Relation Projection v1 provides useful graph-like views without creating a second source of truth.

> **Store Claims. Project edges. Rebuild the view at any time.**

No projection result is persisted as canonical knowledge.

## Views

### `validated`

Includes only Relation Claims whose maturity is `VALIDATED`.

Use this when downstream tooling needs the strongest currently accepted relationship view.

### `research`

Includes:

- `CANDIDATE`
- `SUPPORTED`
- `VALIDATED`
- `CHALLENGED`

It excludes `REJECTED` and `SUPERSEDED` claims. This view is intended for design research, comparison, and curator investigation where unresolved hypotheses are useful but dead history should not dominate the result.

### `challenged`

Includes only `CHALLENGED` Relation Claims.

This is a first-class disagreement surface rather than an error state. It makes it possible to ask which parts of the current knowledge graph need human attention.

### `history`

Includes all Relation Claim maturities, including `REJECTED` and `SUPERSEDED`.

Use this for audit, lineage, and explaining why an earlier graph looked different.

## One projected edge per Claim

Projection does not deduplicate multiple Claims that resolve to the same relation triple.

Two Claims can have the same source, relation type, and target but different:

- Evidence;
- source snapshots;
- epistemic types;
- authors;
- confidence;
- applicability;
- alternative interpretations;
- maturity histories.

Collapsing them at projection time would destroy knowledge history. Deduplication or supersession is a curation decision, not a rendering optimization.

## Asserted versus resolved endpoints

A Relation Claim stores immutable asserted endpoints. Entity identity may later change through a human-approved merge.

Projection therefore exposes both:

- `asserted_relation` — the exact entity IDs stored in the Claim;
- `relation` — the current endpoint IDs after following `MERGED → redirect_to` chains.

Example:

```text
Claim asserted: ke:old-parser related_to ke:incremental
Entity merge:   ke:old-parser → ke:parser
Projection:     ke:parser related_to ke:incremental
```

The Claim itself is never rewritten. This preserves historical provenance while allowing current searches to find the relationship through the surviving canonical identity.

A `redirected` boolean tells consumers whether the projected endpoint differs from the asserted endpoint.

## Corruption handling

Projection fails closed when it cannot resolve an endpoint safely. Examples include:

- missing Knowledge Entity;
- relation endpoint pointing to a non-entity record;
- `MERGED` entity without `redirect_to`;
- redirect cycle.

These are canonical-data integrity failures and should not be silently hidden by a graph renderer.

## Query filters

Projection supports:

- view;
- entity ID;
- direction: `any`, `out`, or `in`;
- relation type.

Entity filters use resolved canonical identity. Querying either a merged ID or its survivor therefore reaches the same current relation set.

Directional queries require an entity anchor. `out` or `in` without `entity_id` is rejected as ambiguous.

## CLI

```bash
# strongest accepted graph view
kneekura-hub relations --view validated

# research surface including candidates and challenged claims
kneekura-hub relations --view research

# all current outgoing relations for one technique
kneekura-hub relations \
  --view research \
  --entity-id ke:incremental-computation \
  --direction out

# audit every historical assertion of one relation type
kneekura-hub relations \
  --view history \
  --relation-type narrower_than
```

## Current implementation boundary

The prototype rebuilds the projection from `repository.list("claim")`. This favors correctness and simplicity while the corpus is small.

It deliberately does not yet introduce:

- a graph database;
- a materialized edge table;
- a cache invalidation subsystem;
- specialized SQL traversal;
- vector retrieval.

Those optimizations should only be introduced after real corpus size and query measurements demonstrate a need.

## Real-pilot acceptance rule

The Salsa relation overlay starts as an AI-authored `CANDIDATE` Relation Claim.

Expected projection behavior:

```text
CANDIDATE  → research: yes   validated: no
SUPPORTED  → research: yes   validated: no
VALIDATED  → research: yes   validated: yes
```

The underlying `KnowledgeEntity.relations` fields remain empty throughout. Only Claim maturity changes the projection.

## Next pressure after v1

Once the relation projection is stable, the Hub can build problem-oriented queries on top of the same read model, for example:

- technologies that `solve` a Problem;
- alternatives connected by competing or conflicting claims;
- prerequisites via `requires`;
- design lineage through `derived_from` and `inspired_by`;
- challenged relationships needing review.

The query layer should remain evidence-aware: a result should always be able to lead back to the Claim and Evidence that caused the edge to appear.
