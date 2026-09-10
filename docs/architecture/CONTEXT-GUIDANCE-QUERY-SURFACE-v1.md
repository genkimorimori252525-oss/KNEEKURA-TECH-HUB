# Context Guidance Query Surface v1

## Status

Acceptance architecture for a read-only human/tool entry point into the already-governed contextual guidance path.

This surface does not create, rank, validate, challenge, supersede, or otherwise mutate knowledge. It only exposes existing trusted Claims and their exact provenance.

## Problem

KNEEKURA TECH HUB already had two proven internal capabilities:

1. `contextual_claims_for_entity(...)` selects VALIDATED entity Claims by exact applicability context without ranking or fallback.
2. `explain_contextual_guidance(...)` preserves that selection and reconstructs every candidate through Claim -> Evidence -> SourceSnapshot -> Source, failing closed on provenance damage or observed Claim drift.

Before this change there was no small user-facing query surface that preserved those semantics end to end.

The test-first acceptance head demonstrated the missing boundary as:

```text
ImportError: cannot import name 'guidance_cli'
```

## Surface

The dedicated command is:

```text
kneekura-guidance <knowledge-entity-id> [--context-json <json-object>] [--dsn <postgres-dsn>]
```

If `--dsn` is omitted, `KTHUB_DATABASE_URL` is used.

The command is intentionally separate from curation and acquisition CLIs. It has no write commands and no authority-bearing subcommand.

## Governed read path

```text
caller
  -> kneekura-guidance ENTITY --context-json {...}
  -> strict context JSON validation
  -> PostgresRepository
  -> explain_contextual_guidance(...)
  -> contextual_claims_for_entity(...)
  -> zero, one, or multiple VALIDATED Claim candidates
  -> explain_claim(...) for each candidate
  -> Evidence
  -> exact SourceSnapshot
  -> Source
  -> one complete JSON result
```

The CLI does not duplicate applicability matching. Selection semantics remain owned by `contextual_claims_for_entity(...)`.

The CLI does not duplicate provenance reconstruction. Explanation semantics remain owned by `explain_contextual_guidance(...)` and `explain_claim(...)`.

## Exact context input

Context is accepted as one JSON object rather than `key=value` strings. This preserves JSON types used by the existing exact comparator.

For example, integer `1` and boolean `true` remain different values.

```json
{"minimum_version": 1}
```

must not be treated as equivalent to:

```json
{"minimum_version": true}
```

### Ambiguous JSON is rejected before database access

Python's default JSON decoder accepts two forms that are unsafe for an exact-context boundary:

- duplicate object keys, where a later value silently replaces an earlier one;
- non-finite numeric constants such as `NaN`, `Infinity`, and `-Infinity`.

Adversarial acceptance reproduced both cases reaching the database-open boundary. The query surface therefore rejects them before opening PostgreSQL.

Duplicate keys are rejected at every JSON object level. Non-finite numbers are rejected wherever they occur.

Malformed JSON and non-object top-level JSON are also rejected before database access.

## Resolution preservation

The surface preserves the exact resolution returned by the context query.

### One match

A single exact candidate is returned and explained.

```text
ONE_MATCH
```

### Multiple matches

Multiple exact candidates remain multiple candidates.

```text
MULTIPLE_MATCHES
```

No winner is invented.

### Context omitted

If more than one VALIDATED Claim exists, the result remains:

```text
CONTEXT_REQUIRED
```

All candidates may be explained, but none becomes preferred merely because the caller omitted context.

### No match

An explicit context with no exact candidate remains:

```text
NO_MATCH
```

The CLI does not retry with weaker matching and does not fall back to unrelated or merely similar Claims.

### No validated claims

The underlying query's `NO_VALIDATED_CLAIMS` result is preserved unchanged.

## Provenance failure

A trusted-looking partial answer is more dangerous than an explicit failure.

If a candidate cannot be reconstructed through its complete provenance chain, the CLI returns an error and does not print the partial guidance JSON.

Examples include:

- missing Evidence;
- missing SourceSnapshot;
- missing Source;
- a SourceSnapshot belonging to a different Source;
- Claim drift detected between contextual selection and explanation.

This preserves the fail-closed behavior already established by Explainable Context Guidance v1.

## Read-only boundary

`kneekura-guidance` opens `PostgresRepository` directly and performs no migration application and no curation operation.

It does not call:

- Claim support or validation transitions;
- Claim disposition;
- source selection or acquisition authorization;
- acquisition execution or verified commit;
- observation triage;
- entity creation or mutation.

No table, schema, migration, decision record, or lifecycle state is created by the query surface.

## Authority boundary

The output is an explanation of already-governed knowledge, not a new authority layer.

The surface introduces none of the following:

- score;
- ranking;
- popularity weighting;
- repository-star weighting;
- recency winner selection;
- `winner`;
- `preferred_claim_id`;
- fuzzy matching;
- semantic embeddings;
- automatic conflict resolution;
- automatic promotion or validation;
- fallback recommendation.

If the underlying governed state is ambiguous, the surface remains ambiguous.

## Acceptance evidence

The primary CLI acceptance suite proves:

- exact JSON context types survive the CLI boundary;
- boolean and integer values are not coerced into equality;
- omitted context preserves `CONTEXT_REQUIRED`;
- malformed/non-object context fails before database open;
- broken provenance produces only an error, not partial trusted JSON;
- database configuration is explicit.

The adversarial JSON suite proves duplicate keys and non-finite numbers are rejected before database access.

The PostgreSQL integration test exercises the full CLI path against the real normalized repository and a governed VALIDATED Claim. It verifies the explanation reaches the pinned Go SourceSnapshot revision:

```text
5d12b248d5520ff5adafeb9be9acc2148399ca49
```

and preserves the exact Claim, Evidence, Snapshot, and Source identities.

## Non-goals

This v1 deliberately does not add:

- natural-language entity search;
- automatic context inference;
- context ontology expansion;
- recommendation scoring;
- conversational rendering;
- HTTP API/server;
- transaction-wide serializable snapshot guarantees beyond the already-proven Claim drift check;
- automatic database migration on query.

Those features require separate defect or product-need proof before they can change this boundary.

## Governing principle

> A query surface may expose governed knowledge, but it must not silently become a new decision-maker. Exact context stays exact, ambiguity stays visible, and every trusted answer remains traceable to immutable evidence provenance.
