# Knowledge Entity Identity Integrity v1

## Purpose

Claims identify concepts through stable `ke:*` Knowledge Entity IDs.

If the concept payload behind an existing Entity ID can be rewritten in place, a reviewed Claim can keep the same subject ID while silently changing what that subject means. This is the Entity-side equivalent of rewriting an Evidence or SourceSnapshot behind a stable ID.

Knowledge Entity Identity Integrity v1 closes that substitution path.

## Immutable concept payload

After a Knowledge Entity is created, the following meaning-bearing fields are immutable under that `ke:*` identity:

- `canonical_name`
- `aliases`
- `kinds`
- `abstraction_level`
- direct `relations`

Array/set order is not semantic. The canonical comparison sorts aliases, kinds, and relation tuples before comparison.

Corrections that change concept meaning require a new Knowledge Entity ID. Existing governed merge semantics can then redirect an old identity when the concepts are determined to represent the same thing.

## Lifecycle fields

`identity_state` and `redirect_to` are not part of the immutable concept payload because canonicalization needs to record merges.

In v1, the only persisted lifecycle mutation currently supported is:

```text
CANONICAL + no redirect
    ->
MERGED + redirect_to another CANONICAL Entity
```

Other future lifecycle transitions must receive their own explicit governance path rather than being enabled by generic replacement.

## PostgreSQL enforcement

Migration `0022_knowledge_entity_identity_integrity.sql` creates a private identity anchor for each Knowledge Entity.

The anchor stores a normalized JSON payload containing:

- canonical name
- abstraction level
- sorted aliases
- sorted kinds
- sorted direct relations

Existing Entities are backfilled when the migration is applied. New Entities receive their anchor at the end of their creation transaction, after normalized child-table rows have been inserted.

Deferred constraint triggers compare the final transaction state against the anchor whenever these tables change:

- `knowledge_entity`
- `entity_alias`
- `entity_kind`
- `entity_relation`

This is deliberately transaction-final rather than statement-local. `PostgresRepository` currently rewrites alias/kind/relation child rows during a normal Entity replacement; an unchanged final set is therefore permitted, while an actual semantic change fails at commit and rolls the whole transaction back.

The `knowledge_entity_identity_anchor` row itself is immutable. Deleting or rewriting the anchor cannot be used to bypass the check.

## MemoryRepository parity

`MemoryRepository` computes the same normalized concept payload and rejects replacements that change it.

It also permits the same currently supported lifecycle mutation, `CANONICAL -> MERGED` with a non-self redirect, while rejecting generic lifecycle rewrites such as direct retirement.

## What this does not do

This slice does not:

- automatically merge duplicate concepts;
- add semantic similarity merging;
- turn names into IDs;
- add new lifecycle states;
- make relations stored inside Knowledge Entity canonical graph truth again;
- infer that two differently named Entities are equivalent.

Relation Claims remain the canonical evidence-backed representation of inter-Entity relationships. The direct Entity relation payload is frozen only so an existing Entity identity cannot be silently rewritten through legacy/storage fields.

## Relationship to other integrity gates

Reviewed Claim Immutability freezes reviewed Claim meaning.

Provenance Anchor Immutability freezes the Evidence/Snapshot identities those Claims cite.

Knowledge Entity Identity Integrity freezes the concept identities those Claims describe.

Together, a reviewed Claim cannot be silently changed by rewriting the Claim, its Evidence anchor, or its Entity subject behind stable IDs.
