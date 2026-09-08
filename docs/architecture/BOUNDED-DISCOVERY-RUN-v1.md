# Bounded Discovery Run v1

## Purpose

GitHub Discovery Adapter v1 turns one GitHub repository-search page into a metadata-only Controlled Discovery batch.

Bounded Discovery Run v1 adds safe multi-query / multi-page orchestration without relaxing any downstream authority boundary.

```text
Query Set
  ↓
Bounded Discovery Run
  ↓
GitHub Discovery Adapter (one page at a time)
  ↓
One aggregate metadata-only Controlled Discovery batch
  ↓
optional discovery-check / discovery-ingest
```

The run orchestrator never writes PostgreSQL and never creates canonical knowledge.

## Hard bounds

v1 intentionally caps work before any request is made:

- maximum 32 queries per run;
- maximum 10 requested pages per query;
- maximum 100 planned requests per run;
- maximum 1000 unique Sources in aggregate;
- GitHub page size remains 1–100.

A spec exceeding any bound is rejected before fetching begins.

The run may choose a lower `max_unique_sources`. Once that cap is reached, remaining requests are not executed and the result records `truncated: true`.

## Run specification

Example:

```json
{
  "run_version": "1.0",
  "discovered_by": {
    "actor_type": "tool",
    "actor_id": "kneekura-discovery",
    "version": "1.0"
  },
  "discovered_at": "2026-09-09T06:30:00+09:00",
  "max_unique_sources": 500,
  "queries": [
    {
      "query_id": "query:incremental",
      "query": "incremental analysis",
      "page_count": 3,
      "per_page": 100
    },
    {
      "query_id": "query:parsing",
      "query": "incremental parsing",
      "page_count": 2,
      "per_page": 100,
      "sort": "updated",
      "order": "desc"
    }
  ]
}
```

`query_id` is a run-local provenance identity and must be unique.

The discovery timestamp must be timezone-aware and is normalized before downstream Adapter use.

## One Source, many discovery paths

The same repository can appear:

- on multiple pages;
- in multiple queries;
- under different search ordering parameters.

The run stores one deterministic Source record per logical GitHub repository, but it does not throw away repeated discovery context.

Each stored Source receives:

```text
origin.discovery_hits[]
```

Each hit records:

- query ID;
- exact query text;
- page;
- accepted position within the Adapter output page;
- API sort/order;
- page-batch ID;
- metadata fingerprint.

This means deduplication does not become provenance loss.

## Metadata changes are not silently reconciled

A repository may have different metadata when encountered through two query paths, for example a changed star count or description.

The run keeps the first accepted Source metadata as the record body and stores a SHA-256 metadata fingerprint on every discovery hit.

Different fingerprints therefore remain visible as a sign that search metadata differed across observations.

v1 does not interpret that difference, average counts, or declare one observation authoritative.

Search metadata is still not Evidence for a technical Claim.

## Ordering semantics

Two order concepts remain separate:

1. **Discovery order** — first accepted occurrence across query order, page order, and Adapter provider order. This determines aggregate Source order.
2. **Controlled Intake dependency order** — the order the downstream preflight may choose for safe ingestion.

Tests explicitly do not require these two orders to be identical.

This prevents an implementation detail in the ingest graph from rewriting discovery provenance.

## Empty pages

A requested page with an empty GitHub `items` array is treated as normal end-of-query pagination.

The run:

- records an empty page receipt;
- stops requesting further pages for that query;
- continues with later queries.

An empty page is therefore not treated as a fatal Adapter error.

If the entire run produces no public repository Sources, the run is rejected instead of emitting an empty Controlled Discovery batch.

## Aggregate output

The final output is one Controlled Discovery v1 batch containing only metadata-only GitHub Source records.

Aggregate scope records:

- query definitions;
- planned request count;
- executed request count;
- unique Source cap;
- unique Source count;
- duplicate-hit count;
- truncation state;
- per-page receipts;
- public-only / metadata-only contract.

The batch ID is deterministic over:

- normalized query specification;
- unique Source cap;
- ordered unique Source IDs.

The wall-clock discovery timestamp is not part of that content identity.

## CLI

Live mode:

```bash
kneekura-discovery-run \
  --spec query-set.json \
  --output discovery-run.json
```

`GITHUB_TOKEN` is used when present by the underlying GitHub Adapter and is never written into run output.

Offline/reproducible mode:

```bash
kneekura-discovery-run \
  --spec query-set.json \
  --responses github-pages.json \
  --output discovery-run.json
```

Offline response format:

```json
{
  "pages": [
    {
      "query": "incremental analysis",
      "page": 1,
      "payload": {
        "total_count": 2,
        "items": []
      }
    }
  ]
}
```

The offline mode allows deterministic CI without network or rate-limit dependency.

## Persistence remains separate

A run output is still only an intake artifact.

To persist it:

```bash
kneekura-hub discovery-check discovery-run.json

kneekura-hub discovery-ingest \
  discovery-run.json \
  --actor-type tool \
  --actor-id kneekura-discovery \
  --actor-version 1.0
```

The acting identity must continue to match `discovered_by` exactly.

The run orchestrator does not import `PostgresRepository` and has no DB write path.

## No popularity ranking

Bounded Discovery Run preserves query ordering and GitHub Adapter provider ordering.

It does not:

- rank by stars;
- vote across query hits;
- boost repositories appearing in many queries;
- turn duplicate-hit count into relevance;
- choose which repository deserves deeper acquisition.

A repository found ten times has ten discovery paths, not ten votes for truth or usefulness.

## Non-goals

v1 does not:

- resume a partially failed live run;
- retry HTTP failures automatically;
- implement rate-limit scheduling;
- persist a separate DiscoveryRun database record;
- automatically select repositories for deeper acquisition;
- verify licenses;
- fetch README/source files;
- produce Evidence or StagedObservations;
- create Claims or Knowledge Entities;
- rank repository quality.

## Next pressure

The next safety-critical layer should be **Metadata Review & Selection Gate v1**.

That gate can decide which metadata-only Sources are worth a separately authorized acquisition step, while keeping popularity, query frequency, and AI interest distinct from license approval and canonical knowledge promotion.