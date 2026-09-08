# Controlled Discovery Intake v1

## Purpose

KNEEKURA TECH HUB now has a safety spine for evidence-backed knowledge:

```text
Source → SourceSnapshot → Evidence → Claim
                              ↓
                       Evidence Review
                              ↓
                       Claim Comparison
                              ↓
                    Human Review Decision
```

The next risk is scale.

A crawler or AI can discover thousands of repositories much faster than a human can review them. If the discovery path can directly create Knowledge Entities, Claims, Relations, or Review Decisions, one noisy search pass can contaminate canonical knowledge at scale.

Controlled Discovery Intake v1 creates a deliberately narrower entrance:

```text
Untrusted GitHub discovery output
              ↓
      Controlled Intake Gate
              ↓
   Source / SourceSnapshot
          /       \
     Evidence   StagedObservation
              ↓
         Curation Gate
              ↓
     Canonical Knowledge
```

Discovery can collect provenance and propose candidate names. It cannot promote its own interpretation into canonical knowledge.

## v1 scope

The first slice is intentionally limited to **GitHub repository discovery**.

Accepted batch records are only:

- `source`
- `source_snapshot`
- `evidence`
- `staged_observation`

The intake envelope rejects all other record types.

In particular, discovery cannot submit:

- `knowledge_entity`
- `claim`
- relation Claims
- `review_decision`
- `curation_event`

Service-generated `SOURCE_ACQUIRE` curation events are still created by the existing CurationEngine. The untrusted batch itself cannot author events.

## Separate from curated prototype bundles

`ingest-bundle` is a human-reviewed curation path. It is allowed to create canonical Knowledge Entities and Candidate Claims.

`discovery-ingest` is an untrusted/high-volume staging path. It is not a convenience alias for `ingest-bundle` and it does not call the bundle ingestion path.

This separation is intentional:

```text
prototype bundle = reviewed curation input
controlled discovery = untrusted staging input
```

A future crawler must use the discovery path.

## Intake envelope

`schemas/v1/discovery-intake.schema.json` defines a transport envelope with:

- `intake_version: 1.0`
- `batch_id`
- `discovered_by`
- timezone-aware `discovered_at`
- GitHub discovery scope metadata
- `records`

The envelope allows at most 1000 records per transaction in v1. Larger crawls must be partitioned into bounded batches rather than creating an unbounded write transaction.

The batch metadata is transport/audit context, not evidence that a technology is good or even relevant.

## Actor binding

The actor executing `discovery-ingest` must exactly equal the envelope's `discovered_by` identity.

For every StagedObservation:

```text
observation.created_by == batch.discovered_by == acting identity
```

This prevents a crawler or AI from writing observations under another actor's provenance.

Human, AI, tool, and system actors may perform discovery. None of them gains canonical Knowledge privileges through this path.

## Deterministic GitHub Source identity

GitHub repositories use one deterministic Source ID:

```text
owner/name
   ↓ lowercase identity normalization
src:github:owner:name
```

Example:

```text
Salsa-RS/Salsa
→ src:github:salsa-rs:salsa
```

A discovery batch that tries to register the same logical repository under a different Source ID fails closed.

The intake also checks already-stored GitHub Sources for duplicate logical identities.

This prevents repeated search queries from creating parallel Source identities for the same repository.

## SourceSnapshot namespace

A SourceSnapshot ID must be namespaced by its Source:

```text
src:github:salsa-rs:salsa
→ ss:github:salsa-rs:salsa:<revision-anchor>
```

The existing core schema still requires an immutable anchor such as revision, tree hash, content hash, or SWHID.

## Acquisition and license boundary

The existing governance policy already limits `UNKNOWN` license Sources to `metadata-only` acquisition.

Controlled Discovery adds a second gate:

A `metadata-only` Source cannot be used to create:

- SourceSnapshot
- Evidence
- StagedObservation

Therefore:

```text
UNKNOWN license
      ↓
metadata-only Source
      ↓
no code/document snapshot through discovery v1
```

A metadata-only repository can still be remembered as a discovery candidate, but discovery cannot silently deepen acquisition beyond its declared level.

This guard is repeated when referencing an **existing** Source. Historical inconsistent data cannot be used as a loophole to add new discovery observations.

v1 does not implement acquisition-level upgrades. Upgrading a metadata-only Source is a separate future governance problem rather than an implicit crawler action.

## Observation boundary

Discovery-created StagedObservations must:

- enter with `status: NEW`;
- have at least one `candidate_name`;
- have Evidence candidates;
- use Evidence belonging to the same Source;
- resolve all Evidence to exactly one SourceSnapshot;
- have `created_by` exactly matching the discovery actor.

Discovery therefore produces a statement of the form:

```text
"This pinned material may be relevant to candidate X."
```

It does **not** produce:

```text
"X is canonical knowledge."
```

Candidate names are discovery hypotheses, not canonical entity identity.

## Dependency-safe preflight

Crawler output does not need to be ordered.

`preflight_discovery_intake` validates the complete batch before any write and then constructs a dependency-safe order:

```text
Source
  ↓
SourceSnapshot
  ↓
Evidence
  ↓
StagedObservation
```

References may resolve either:

- inside the same batch; or
- to compatible records already stored in the repository.

Existing IDs may be referenced but cannot be redefined.

The preflight rejects:

- missing dependencies;
- wrong record types under referenced IDs;
- duplicate batch IDs;
- attempted redefinition of existing IDs;
- duplicate GitHub Source identities;
- non-deterministic Source IDs;
- SourceSnapshot/Source namespace mismatch;
- Evidence/SourceSnapshot source mismatch;
- Observation/Evidence source mismatch;
- multi-snapshot Observation evidence;
- metadata-only deep acquisition;
- non-NEW observations;
- missing candidate names;
- actor provenance mismatch;
- blocked canonical record types.

## Atomic PostgreSQL write

`discovery-ingest` wraps the full intake in one PostgreSQL transaction.

If any governed write fails after earlier records were inserted, the transaction rolls back all discovery writes, including Source acquisition events.

The integration test deliberately injects an Evidence write failure after earlier Source/Snapshot work and verifies that the database returns to an empty state.

This prevents partial states such as:

```text
Source stored
Snapshot stored
Evidence failed
Observation missing
```

from surviving a failed batch.

## Receipt

Successful ingestion returns a receipt containing:

- batch ID;
- discovery actor;
- discovery timestamp;
- stored IDs;
- count by allowed record type;
- the fixed discovery allowlist;
- `canonical_knowledge_writes: 0`.

The receipt is an operation result, not a new canonical knowledge record.

## CLI

Offline/self-contained preflight:

```bash
kneekura-hub discovery-check pilots/controlled-discovery-intake-v1.json
```

Atomic PostgreSQL intake:

```bash
kneekura-hub discovery-ingest \
  pilots/controlled-discovery-intake-v1.json \
  --actor-type ai \
  --actor-id jolly \
  --actor-version gpt-5.6-sol
```

The actor arguments must match `discovered_by` in the batch exactly.

## Real OSS acceptance pilot

`pilots/controlled-discovery-intake-v1.json` reuses pinned evidence anchors from the existing real-OSS research set:

- `tree-sitter/tree-sitter` at revision `8351896bea2e3359ed2fd893ffb051e9f9ebc69b`
- `salsa-rs/salsa` at revision `e021c01d4939408c89c9325ad2426660117a8b32`

The batch is intentionally scrambled rather than dependency ordered.

It contains:

- 2 Sources
- 2 SourceSnapshots
- 2 Evidence records
- 2 NEW StagedObservations
- 0 Knowledge Entities
- 0 Claims
- 0 Review Decisions

Candidate names include:

- `Incremental Parsing`
- `Query-based Incremental Computation`

Those names remain discovery hypotheses. The intake does not reuse the canonical Knowledge Entities from the older curated pilot.

## Security posture

Controlled Discovery v1 never executes discovered repository code.

The intake consumes already-produced metadata/snapshot/evidence records. Source execution, build execution, dependency installation, and benchmark execution remain outside this boundary and require a separately sandboxed design.

## Non-goals

v1 does not:

- crawl GitHub by itself;
- automatically choose repositories by stars or popularity;
- execute cloned code;
- install dependencies;
- create Knowledge Entities;
- create Claims or Relations;
- create Review Decisions;
- promote StagedObservations;
- upgrade metadata-only acquisition;
- infer license compatibility;
- deduplicate arbitrary non-GitHub sources;
- rank candidate technologies;
- infer that a candidate is good because it was discovered often.

## Next pressure

After this intake gate is merged, the next safe slice is **GitHub Discovery Adapter v1**.

That adapter can turn GitHub search results into bounded Controlled Discovery batches, initially preferring metadata-only collection and explicit license handling. Any selected-file acquisition must still pass this intake gate, and the adapter must remain unable to emit canonical Knowledge/Claim/Decision records.
