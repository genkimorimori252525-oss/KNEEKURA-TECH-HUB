# Audit Trail Immutability v1

## Purpose

A governance decision is only auditable if its audit event cannot be rewritten after the fact.

`curation_event` is therefore append-only from creation onward.

## Contract

Allowed:

- insert a new `curation_event`;
- read existing events;
- use `TRUNCATE` only for isolated test/database reset.

Forbidden:

- update an existing `curation_event`;
- delete an existing `curation_event`;
- reuse an existing event ID for different history.

Corrections append a new event or governed decision; they do not rewrite history.

## PostgreSQL enforcement

Migration `0021_audit_trail_immutability.sql` rejects direct SQL `UPDATE` and `DELETE` on `curation_event`.

`PostgresRepository` already treats curation events as append-only at its API boundary. The migration closes the direct-SQL bypass.

## MemoryRepository parity

`MemoryRepository.put(..., replace=True)` also rejects replacement of an existing `curation_event`.

## Scope

This slice does not change event vocabulary, introduce event signing, or claim that a database administrator cannot fabricate a new event. It establishes the narrower invariant needed by later governance gates: once an event exists, its stored history cannot be mutated through normal Hub persistence or SQL DML.
