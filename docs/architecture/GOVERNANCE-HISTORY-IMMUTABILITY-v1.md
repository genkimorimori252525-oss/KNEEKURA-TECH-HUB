# Governance History Immutability v1

## Purpose

Several Hub record families are already designed and exposed as append-only history. Their repository APIs create new decisions, authorizations, executions, commits, and triage decisions instead of rewriting prior history.

Older PostgreSQL tables did not consistently enforce that contract against direct SQL `UPDATE` or `DELETE`. That left a database-level path to rewrite who decided what, what was authorized or executed, or what triage decision occurred after the fact.

This slice closes that gap without changing the existing governance vocabulary or lifecycle semantics.

## Protected history records

The following existing record types become database-enforced append-only history:

- `review_decision`
- `source_selection_decision`
- `source_acquisition_authorization`
- `source_acquisition_execution`
- `source_acquisition_commit`
- `observation_triage_decision`

Corrections append a successor/new record where the model provides one. They do not rewrite the historical row.

## Existing protections not duplicated here

`curation_event` is already append-only through `0021_audit_trail_immutability.sql` and is deliberately not re-targeted by this slice.

Claim support, validation, and disposition decisions already have dedicated append-only database enforcement in their respective claim-governance migrations. Those record families are also deliberately not duplicated here.

## PostgreSQL enforcement

Migration `0024_governance_history_immutability.sql` attaches one shared rejection function to `BEFORE UPDATE OR DELETE` triggers on the six tables above.

This makes the database authority ceiling match the existing repository/domain contract: direct SQL cannot silently rewrite committed governance or acquisition history.

## MemoryRepository parity

`MemoryRepository.put(..., replace=True)` rejects replacement of the same six history record types.

This is intentionally the same semantic boundary as PostgreSQL. Tests may still manipulate private internals to manufacture impossible states, but that is not a supported repository mutation path.

## Deliberately mutable state

This slice does not freeze state-bearing records such as:

- `source` mutable license/acquisition/freshness state;
- `staged_observation` lifecycle state, which is governed by triage pairing;
- `claim` lifecycle state, which is governed by Support / Validation / Disposition gates.

It also does not change the meaning of `TRUNCATE` in isolated database tests. `TRUNCATE` remains a reset mechanism, not a canonical history-edit API.

## Safety property

Once one of these governance/history rows is committed, its stored historical statement is stable:

```text
historical row identity + payload
        ↓
     append-only
```

Later corrections add history. They do not rewrite history.
