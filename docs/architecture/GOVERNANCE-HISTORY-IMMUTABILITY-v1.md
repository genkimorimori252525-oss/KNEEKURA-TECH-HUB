# Governance History Immutability v1

## Purpose

KNEEKURA TECH HUB already models several governance and audit records as append-only history. Application repositories and design documents require corrections to be represented by new decisions/events instead of rewriting prior history.

Older PostgreSQL tables did not consistently enforce that rule at the database boundary. A direct SQL `UPDATE` or `DELETE` could therefore alter who decided what, what was authorized or executed, or which curation event occurred after the fact.

This slice makes the database authority ceiling match the existing append-only contract.

## Protected history records

The following existing record types are append-only in v1:

- `curation_event`
- `review_decision`
- `source_selection_decision`
- `source_acquisition_authorization`
- `source_acquisition_execution`
- `source_acquisition_commit`
- `observation_triage_decision`

For each record, correction means adding a new successor/decision/event where the existing model provides one, not rewriting the historical row.

## PostgreSQL enforcement

Migration `0021_governance_history_immutability.sql` attaches one shared rejection function to `BEFORE UPDATE OR DELETE` triggers on all seven tables.

The database therefore rejects mutation whether it comes through a repository adapter or direct SQL.

Claim support, validation, and disposition decisions are not duplicated here; they already have dedicated append-only database enforcement.

## MemoryRepository parity

`MemoryRepository.put(..., replace=True)` rejects replacement of the same seven governance/audit record types.

The private in-memory dictionary may still be altered by tests that intentionally construct impossible/corrupted states. That is test-only corruption, not a supported repository mutation API.

## Deliberately mutable records

This slice does not freeze state-bearing records such as:

- `source`
- `staged_observation`
- `claim` lifecycle fields

Those records have legitimate governed transitions elsewhere in the system.

## Reset semantics

Test/database reset may continue to use `TRUNCATE`. It is not a canonical history-edit operation.

## Safety property

Once a governance/audit record is committed, its historical statement is stable:

```text
historical row identity + payload
        ↓
     immutable
```

Later corrections add history; they do not rewrite history.
