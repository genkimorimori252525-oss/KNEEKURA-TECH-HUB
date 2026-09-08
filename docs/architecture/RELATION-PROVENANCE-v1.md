# Relation Provenance v1

## Purpose

KNEEKURA TECH HUB must be able to say that two Knowledge Entities are related without turning an AI taxonomy guess into canonical graph truth.

The v1 rule is:

> **A relationship is a Claim before it is a graph edge.**

`KnowledgeEntity.relations` remains write-quarantined. Relationship assertions use the same Evidence, provenance, maturity, challenge, and supersession machinery as ordinary Claims.

## Claim subjects

A Claim has exactly one subject form.

### Entity subject

```json
{
  "entity_id": "ke:incremental-computation"
}
```

### Relation subject

```json
{
  "relation": {
    "source_entity_id": "ke:query-based-incremental-computation",
    "relation_type": "narrower_than",
    "target_entity_id": "ke:incremental-computation"
  }
}
```

A Relation Claim cannot also carry `entity_id`. Both endpoints must already exist and must be different entities.

## Why Relation is not a second record lifecycle

Relation assertions need the same governance properties already implemented for Claims:

- immutable identity;
- Evidence links;
- source/snapshot provenance through Evidence;
- `AUTHOR_CLAIM`, `DIRECT_OBSERVATION`, `INFERENCE`, `EXPERIMENT_RESULT`, or `JUDGMENT` epistemic type;
- creator provenance;
- `CANDIDATE → SUPPORTED → VALIDATED` maturity;
- `CHALLENGED`, `SUPERSEDED`, and `REJECTED` states;
- human gate for `VALIDATED` promotion;
- append-only curation events.

Creating a separate relation lifecycle would duplicate this logic and create two subtly different definitions of evidence-backed knowledge.

## Authorship versus validation

`created_by` records who created the Claim. It is not rewritten when a later reviewer changes maturity.

An AI may create a `CANDIDATE` Relation Claim. A human may later promote that same Claim to `SUPPORTED` and `VALIDATED`. The stored Claim continues to say `created_by.actor_type = ai`; the human validation action is recorded separately in the curation-event trail.

This separation prevents two provenance errors:

1. falsely rewriting AI-authored knowledge as human-authored; and
2. falsely treating AI authorship as proof that no human validation ever occurred.

The service layer, not static record validation, enforces that only a human actor can perform the `VALIDATED` transition.

## Direct graph writes remain quarantined

`KnowledgeEntity.relations` is not used as the authoritative relationship store in v1. Non-empty direct writes are rejected by policy validation.

This is intentional even after Relation Claims exist. Copying a validated Relation Claim into `KnowledgeEntity.relations` would introduce two sources of truth that could diverge after challenge or supersession.

The authoritative relationship truth is the Claim set.

A future graph/query layer should project relationship edges dynamically from Claims according to an explicit view policy, for example:

- candidate view: include `CANDIDATE`, `SUPPORTED`, and `VALIDATED` with maturity labels;
- trusted view: include only `VALIDATED` Relation Claims;
- research view: include `CHALLENGED` claims and their competing successors;
- historical view: include superseded assertions with lineage.

The projection is a read model, not a second canonical store.

## Relation types

v1 supports:

- `broader_than`
- `narrower_than`
- `related_to`
- `solves`
- `requires`
- `enables`
- `implements`
- `derived_from`
- `inspired_by`
- `conflicts_with`
- `tradeoff_with`
- `supersedes`

The presence of a relation type in this vocabulary does not prove a particular edge. Every Relation Claim still requires its own Evidence and lifecycle.

## Supersession rules

A Claim may be marked `SUPERSEDED` only when:

- the successor is a different Claim ID;
- the successor describes the exact same Claim subject;
- the successor is already at least `SUPPORTED`.

For Relation Claims, "same subject" means the same source entity, relation type, and target entity. A change from `narrower_than` to `related_to`, for example, is a different relationship hypothesis and is not silently treated as a textual replacement of the same assertion.

## PostgreSQL representation

Migration `0003_relation_claim_subject.sql` extends the normalized `claim` table with relation endpoint/type columns and makes `entity_id` nullable.

A database CHECK constraint requires exactly one subject shape:

- `entity_id` present and all relation columns null; or
- `entity_id` null and all three relation columns present.

Both relation endpoints are foreign keys to `knowledge_entity`, and self-relations are rejected.

## Migration integrity

Before introducing the non-idempotent schema evolution needed for Relation Claims, migration execution was upgraded to a tracked history model.

`schema_migration` records each migration filename and SHA-256 checksum. An already-applied migration is skipped when the checksum matches and causes `MigrationDriftError` if its file later changes. This makes schema history append-only rather than dependent on repeatedly executing every SQL file.

## Real pilot overlay

`pilots/incremental-computation-relations-v1.json` is deliberately an overlay on top of `incremental-computation-v1.json` rather than a rewrite of the Phase 2 base pilot.

The first Relation Claim proposes, at `CANDIDATE` maturity and `MEDIUM` confidence, that:

`Query-based Incremental Computation narrower_than Incremental Computation`

It is explicitly an `INFERENCE`, supported by the pinned Salsa Evidence already present in the base pilot. It also stores an alternative interpretation that `related_to` may ultimately be more appropriate after broader cross-source comparison.

This tests additive knowledge evolution without rewriting the earlier experiment corpus.

## Non-goals

Relation Provenance v1 does not:

- automatically promote a Relation Claim to `VALIDATED`;
- infer relation quality from repository popularity;
- materialize validated edges into `KnowledgeEntity.relations`;
- decide that one taxonomy interpretation is universally correct;
- create a graph database dependency;
- automatically merge entities because a relation was asserted.

## Next slice

After this model is merged and stable, the natural next step is a **relation projection/query layer** that can answer questions such as:

- Which validated techniques solve this Problem?
- What alternatives or conflicting techniques exist?
- Which relations are only candidates or currently challenged?
- Why does this edge exist, and what Evidence supports it?

That layer should be derived from Claims and remain rebuildable from canonical records.
