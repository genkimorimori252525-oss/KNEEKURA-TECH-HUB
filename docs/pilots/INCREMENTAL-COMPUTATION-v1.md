# Incremental Computation Curated Pilot v1

## Purpose

This is the first real-data exercise of the KNEEKURA TECH HUB curated core.
It intentionally uses a very small corpus so schema, provenance, and curation
failures appear before discovery is scaled to dozens or thousands of sources.

Pilot bundle:

- `pilots/incremental-computation-v1.json`

## Pinned sources

| Source | Pinned revision | Role in this pilot |
| --- | --- | --- |
| `tree-sitter/tree-sitter` | `8351896bea2e3359ed2fd893ffb051e9f9ebc69b` | author description of incremental parsing |
| `salsa-rs/salsa` | `e021c01d4939408c89c9325ad2426660117a8b32` | author description of incrementalized/query-based computation |
| `rust-lang/rust-analyzer` | `33a84d20e5fe310a43bae1dab7ad41121a7214fc` | direct code evidence that a HIR type-inference database uses Salsa |

The Hub stores metadata and immutable revision/tree anchors only. It does not
vendor these repositories in this pilot.

## Knowledge entities introduced

- `ke:incremental-computation`
- `ke:query-based-incremental-computation`
- `ke:incremental-parsing`

The pilot deliberately leaves their canonical relation graph empty. The current
entity-relation representation does not yet carry first-class provenance or
claim maturity, so encoding taxonomy edges here would make a curator judgment
look more authoritative than the underlying evidence warrants.

## Claims introduced

Four claims are added, all at `CANDIDATE` maturity and all preserving
`created_by.actor_type = ai`:

1. Salsa self-describes as a framework for on-demand incrementalized computation.
2. Salsa describes a query model with memoized results that may be reused or recomputed after input changes.
3. Tree-sitter self-describes as an incremental parsing library that updates a concrete syntax tree as source changes.
4. At the pinned rust-analyzer revision, `HirDatabase` is documented as a Salsa database for type-inference queries and is annotated with `#[salsa::db]`.

No claim is inserted as `SUPPORTED` or `VALIDATED`. Human review must use the
normal claim lifecycle to promote any of them.

## Explicit non-conclusions

This pilot does **not** establish that:

- Tree-sitter, Salsa, or rust-analyzer is globally better than alternatives;
- any claimed performance target is achieved in our environment;
- query-based incremental computation is appropriate for every KNEEKURA project;
- incremental parsing and query-based incremental computation should already be linked by a canonical taxonomy edge;
- project popularity, stars, or adoption count is evidence of correctness.

Those require comparison, experiment, or explicit curator judgment records.

## What this pilot is testing

- real GitHub source identities with immutable snapshots;
- source-line Evidence with blob hashes;
- separation of `AUTHOR_CLAIM` from `DIRECT_OBSERVATION`;
- AI-created Candidate Claims without human-provenance rewriting;
- dependency-safe bundle ingestion;
- all-or-nothing PostgreSQL transaction behavior;
- ability to discover data-model weaknesses before mass collection.

## Known design pressure exposed by the pilot

Two areas should be exercised next rather than guessed at now:

1. **Relation provenance** — Knowledge Entity relation edges currently do not have the same evidence/maturity model as Claims.
2. **Staged observation snapshot pinning** — discovery observations should ultimately be tied to the exact SourceSnapshot from which they were extracted.

Neither issue should be hidden by adding unsupported relation edges or by mass-ingesting data before the model is tested further.
