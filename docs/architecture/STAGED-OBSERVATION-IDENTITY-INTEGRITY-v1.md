# Staged Observation Identity Integrity v1

## Purpose

A StagedObservation is a low-trust extraction candidate, but its `obs:*` identity still has to mean one stable extracted payload.

Triage decisions are append-only governance history. If an existing Observation could later be rewritten under the same ID, an old triage decision could silently appear to have reviewed a different summary, candidate concept, creator, Source, or Evidence set.

This slice closes that substitution path without turning Observation lifecycle state into an immutable record.

## Stable Observation identity

After creation, the following meaning-bearing fields are immutable under one `obs:*` ID:

- `source_id`
- `summary`
- `candidate_names`
- `created_by`
- `evidence_candidate_ids`

A changed extraction proposal must use a new Observation ID.

The immutable identity deliberately excludes `status`.

## Governed lifecycle remains mutable

`status` continues to move only through the existing Staged Observation Triage boundary:

```text
NEW
  -> TRIAGED
  -> PROMOTED / REJECTED / EXPIRED
```

The existing `observation_triage_decision` transaction pairing remains the authority mechanism. Identity integrity does not invent a second lifecycle gate.

Re-extraction of the same deterministic Observation continues to reuse the existing record and preserve its current lifecycle state; it does not reset a reviewed Observation to `NEW`.

## PostgreSQL enforcement

Migration `0025_staged_observation_identity_integrity.sql` applies two complementary protections.

### Observation row payload

A `BEFORE UPDATE` trigger rejects changes to the stable payload while allowing `status` changes to continue through the existing triage gate.

Deletion of a StagedObservation is rejected. Rejection and expiry are lifecycle states, not physical deletion operations.

### Evidence-set identity

`evidence_candidate_ids` are normalized in `staged_observation_evidence`, so protecting only the parent row is insufficient.

The migration therefore stores the sorted committed Evidence-ID set in a private `staged_observation_evidence_anchor` row.

For existing observations the anchor is backfilled during migration. For new observations it is captured by a deferred creation trigger after the creation transaction has assembled the final Evidence links.

Later Evidence-link INSERT / UPDATE / DELETE operations are checked at transaction commit against that anchor.

This intentionally permits the current PostgreSQL adapter to delete and reinsert the *same* links during a normal status update while rejecting a different final Evidence set.

The anchor row itself is immutable.

## MemoryRepository parity

MemoryRepository compares the meaning-bearing StagedObservation fields before replacement.

A replacement that changes Source, summary, candidate names, creator, or Evidence IDs is rejected. A status-only replacement is not rejected by this identity guard; lifecycle authority remains a separate concern.

## Relationship to other integrity slices

The chain now preserves stable meaning at each boundary:

```text
Source identity
  -> immutable SourceSnapshot
  -> immutable Evidence
  -> immutable StagedObservation extraction payload
  -> governed triage decision
  -> Claim Candidate
```

A StagedObservation remains lower-trust than a Claim. Immutability here means only that historical review continues to refer to the same proposed extraction; it does not promote or validate the proposal.

## Deliberately not included

This slice does not add:

- semantic duplicate merging;
- automatic Claim creation;
- automatic support or validation;
- a scalar observation-quality score;
- a new Observation revision table;
- deletion as a lifecycle mechanism.
