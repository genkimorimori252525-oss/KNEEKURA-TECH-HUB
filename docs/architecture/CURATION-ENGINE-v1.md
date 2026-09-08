# Curation Engine v1

## Purpose

The Phase 1 curation engine is the guarded write path into canonical KNEEKURA TECH HUB knowledge. Discovery may be broad and noisy; curated records must satisfy schema, provenance, reference, and governance checks.

## Record path

```text
Source
  ↓
SourceSnapshot
  ↓
Evidence
  ↓
Claim
  ↓
Knowledge Entity
```

`staged_observation` stays outside this curated chain until triage.

## SourceSnapshot invariant

Evidence must point to a first-class `source_snapshot` record. A snapshot belongs to exactly one Source and must have at least one immutable anchor such as revision, tree/content hash, or SWHID.

The service rejects Evidence when its snapshot belongs to a different Source.

## Claim lifecycle

```text
CANDIDATE → SUPPORTED → VALIDATED
    │            │          │
    └→ REJECTED  ├→ CHALLENGED
                 └→ REJECTED

CHALLENGED → SUPPORTED / VALIDATED / SUPERSEDED / REJECTED
VALIDATED  → CHALLENGED / SUPERSEDED
```

`VALIDATED` requires a human actor. `ESTABLISHED` does not exist in v1.

## Entity governance

Canonical entity creation and entity merge require a human actor. Merge does not hard-delete the losing identity; it changes that entity to `MERGED` and preserves a `redirect_to` pointer to the survivor. A reversible `ENTITY_MERGE` curation event is appended.

## Persistence

`PostgresRepository` maps the logical records onto normalized PostgreSQL tables from `migrations/0001_foundation.sql`.

Production/CLI connections use autocommit for reads while every `put()` is wrapped in an explicit transaction. This avoids long-lived implicit read transactions while preserving atomic writes.

## CLI surface

```text
kneekura-hub validate <record.json>
kneekura-hub init-db
kneekura-hub ingest <record.json>
kneekura-hub get <immutable-id>
kneekura-hub list [--type TYPE]
kneekura-hub transition-claim <claim-id> <target> --reason ...
kneekura-hub merge-entities <survivor> <duplicate> --reason ...
```

The database DSN is supplied with `--dsn` or `KTHUB_DATABASE_URL`.

## Explicit non-goals of Phase 1

- no mass crawler
- no automatic canonical merge
- no automatic `VALIDATED` promotion
- no graph database
- no vector-search requirement
- no automatic evidence-independence inference

These belong to later phases only after the curated core remains stable under adversarial prototype data.
