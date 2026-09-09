# Staged Observation Triage v1 — Acceptance Invariants

This file is a compact acceptance record for the v1 triage slice.

## Authority

- New StagedObservations start at `NEW` only.
- AI cannot mutate Observation lifecycle state.
- Tool/system actors are limited to `MARK_TRIAGED` and `EXPIRE`.
- `REJECT` and `PROMOTE_TO_CLAIM_CANDIDATE` require a human actor.
- Promotion creates only a `CANDIDATE` Claim.

## Provenance

- Promotion inherits Evidence IDs from the Observation.
- Promotion input cannot supply or replace Evidence IDs.
- Promotion input cannot supply maturity, creator, policy version, or verification state.
- Triage context rejects cross-Source or multi-Snapshot Evidence corruption.

## Lifecycle audit

- Triage decisions are append-only.
- PostgreSQL rejects initial Observation status other than `NEW`.
- PostgreSQL rejects status mutation without a matching triage decision.
- PostgreSQL rejects a triage decision whose target status was not applied.
- One `(observation_id, from_status)` may produce only one decision.

## Atomicity

A failed promotion must leave all of these unchanged:

- Claim set
- Claim curation events
- Observation lifecycle status
- Triage decision history

## Deduplication

- Exact-content grouping is read-only.
- Shared-Evidence grouping is read-only.
- Creator and lifecycle status do not cause exact-content records to be merged.
- Semantic similarity never causes automatic merge in v1.

## Migration safety

The migration lexer must split only on top-level semicolons and preserve semicolons inside:

- quoted strings
- quoted identifiers
- line comments
- nested block comments
- PostgreSQL dollar-quoted function bodies

Migration drift remains checksum-enforced.

## Acceptance result

Branch acceptance requires the complete repository pytest workflow, including a real PostgreSQL 16 service, to pass before PR merge.
