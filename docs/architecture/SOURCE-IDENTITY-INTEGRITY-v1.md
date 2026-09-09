# Source Identity Integrity v1

## Purpose

`SourceSnapshot` and `Evidence` are immutable, but both refer back to a `src:*` Source identity. If the same Source ID could later be repointed from one repository/provider object to another, historical provenance would silently change even though every Snapshot and Evidence ID remained unchanged.

This slice freezes the identity-bearing portion of each Source while preserving the Source fields that legitimately evolve over time.

## Stable Source identity

For v1, a Source identity is:

- `kind`; and
- `origin` after removing the explicitly declared volatile discovery fields.

Changing the stable payload under the same `src:*` ID is forbidden. Examples include changing:

- provider;
- repository identity;
- canonical Source URL when stored as origin identity;
- provider object IDs such as GitHub repository/node IDs;
- any new/unknown origin key that has not explicitly been classified as volatile.

If the Source was registered against the wrong upstream object, create a new Source ID instead of rewriting the old identity.

## Explicitly volatile discovery metadata

The following origin fields may evolve in v1 without changing Source identity:

- `default_branch`
- `description`
- `language`
- `fork`
- `archived`
- `disabled`
- `visibility`
- `stargazers_count`
- `forks_count`
- `open_issues_count`
- `pushed_at`
- `updated_at`
- `topics`
- `github_license_hint`
- `discovery_hits`

These fields are freshness/discovery observations, not the identity of the upstream object.

The list is deliberately allowlisted. Unknown future origin fields are stable by default until deliberately reviewed and added as volatile. This is fail-closed behavior, not a claim that every future provider uses the same metadata model.

## Other mutable Source state

This slice does **not** freeze the entire Source record.

The following remain governed mutable state:

- license state / declared expression / handling policy;
- acquisition depth (`metadata-only` → `selected-files` through the existing acquisition gates);
- repository-adapter freshness fields already represented by the volatile origin allowlist.

Verified Acquisition Commit continues to update acquisition depth without changing Source identity.

## Enforcement

### PostgreSQL

Migration `0023_source_identity_integrity.sql` normalizes the Source identity payload and rejects updates that change it.

Direct SQL and repository-mediated updates therefore share the same final boundary.

### MemoryRepository

`MemoryRepository` computes the same normalized identity payload before replacement and rejects changes to stable Source identity while allowing volatile metadata, license, and acquisition updates.

## Non-goals

This slice does not:

- assign quality or relevance from stars/forks;
- make discovery metadata immutable;
- make license/acquisition state immutable;
- infer that two Sources are the same object;
- automatically migrate a bad Source ID to a corrected one.

Corrections that change Source identity require a new Source ID and normal provenance linkage.