# Provenance Anchor Immutability v1

## Purpose

A reviewed Claim is only as stable as the provenance records behind its Evidence IDs.

If an existing `SourceSnapshot` or `Evidence` ID can be rewritten in place, a Claim can keep the same reviewed lifecycle and the same Evidence IDs while the material those IDs mean silently changes.

This slice closes that indirect substitution path.

## Immutable anchors

From creation onward:

- `source_snapshot` is immutable;
- `evidence` is immutable.

The rule applies regardless of whether a Claim already references the record. Identity itself is the contract.

A correction therefore creates a new record ID instead of reusing the old identity.

## SourceSnapshot

A SourceSnapshot is the immutable capture anchor for a Source at a particular captured state. Its Source, revision/hash anchors, capture time, and metadata must not be rewritten under the same `ss:*` identity.

If a capture was wrong or a newer upstream state is needed, create a new SourceSnapshot.

## Evidence

Evidence binds a SourceSnapshot to an exact locator and evidence role set. Its Source, SourceSnapshot, locator, roles, and observation metadata must not be rewritten under the same `ev:*` identity.

If a locator, role interpretation, or provenance binding needs correction, create a new Evidence record and use normal Claim revision/supersession semantics where appropriate.

## PostgreSQL enforcement

Migration `0020_provenance_anchor_immutability.sql` rejects `UPDATE` and `DELETE` on both `source_snapshot` and `evidence`.

The database is the final enforcement boundary, so both repository-mediated writes and direct SQL mutation attempts fail.

`TRUNCATE` remains usable for isolated test/database reset. It is not a canonical mutation API.

## MemoryRepository parity

`MemoryRepository.put(..., replace=True)` rejects replacement of existing `source_snapshot` and `evidence` records.

This keeps the authority meaning aligned with PostgreSQL for normal repository writes.

## Deliberately mutable

`source` is not frozen by this slice. Source license handling and acquisition depth have legitimate governed updates elsewhere in the system.

This slice also does not automatically freeze every provenance-adjacent record type. Additional immutability should be introduced only when an actual integrity dependency requires it.

## Relationship to Reviewed Claim Immutability

Reviewed Claim Immutability freezes the reviewed Claim payload and Evidence-ID set after Candidate.

Provenance Anchor Immutability freezes what those Evidence IDs and their SourceSnapshot IDs mean.

Together they prevent both direct and indirect substitution of reviewed meaning.
