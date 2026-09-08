# KNEEKURA TECH HUB

Private technology research infrastructure for discovering large amounts of engineering knowledge from OSS and other technical sources without confusing discovery with verified knowledge.

> **Discover broadly. Promote knowledge carefully.**

## Three roles

1. **OSS Technology Search Engine** — mass discovery and indexing.
2. **Evidence-backed Technology Encyclopedia** — curated claims with traceable evidence.
3. **Design Research Laboratory** — comparison, experiments, and KNEEKURA application hypotheses.

## Architecture

```text
Discovery Universe
      ↓
Discovery & Collection Layer
      ↓
Curation Gate
      ↓
Source → SourceSnapshot → Evidence → Claim → Knowledge Entity
                                  └→ Relation Claim
                                          ↓
                                  Relation Projection
                                          ↓
                         Problem-oriented Query Layer
                                          ↓
                                  Application & Research
```

`SourceSnapshot` is a first-class immutable evidence anchor. AI and scanners first produce `staged_observation` records; they cannot directly merge canonical entities or perform a `VALIDATED` promotion.

A staged observation must be backed by Evidence candidates that all resolve to exactly one SourceSnapshot. Those Observation ↔ Evidence links are persisted in PostgreSQL so the source-revision provenance survives reload.

Relationships between Knowledge Entities are also evidence-backed Claims. A Claim has exactly one subject: either one `entity_id`, or a `relation` consisting of source entity, relation type, and target entity. Direct non-empty `KnowledgeEntity.relations` writes remain rejected so an unproven taxonomy guess cannot become canonical graph truth.

`created_by` remains authorship provenance. An AI-created Candidate Claim can later be human-reviewed and promoted without rewriting its creator identity; the human transition is recorded separately in the curation-event trail.

Relation graph views are rebuilt from Claims. They are never stored as a second canonical graph. Projection preserves the asserted endpoint IDs and also resolves current canonical identities through human-approved entity-merge redirects.

Problem-oriented queries are deliberately conservative. They read only explicit evidence-backed relation claims such as `solves` and `requires`; they do not infer solutions from popularity, text similarity, `related_to`, or an AI guess made during query execution.

## Current implementation

### Phase 0 — Constitution & Schema

- Constitution v1.0
- machine-readable governance policy v1.0
- JSON Schema for core record types
- first-class immutable `source_snapshot` records
- PostgreSQL normalized persistence
- tracked ordered migrations with SHA-256 drift detection

### Phase 1 — Curation Engine

- policy-aware `CurationEngine`
- human-gated entity creation / merge
- governed claim maturity transitions
- human-only `VALIDATED` transition
- append-only curation events
- provenance checks for claims and staged observations
- CLI for DB initialization, ingest, get, list, claim transitions, and entity merges
- regression tests and real PostgreSQL integration tests in GitHub Actions

### Phase 2 — Curated Prototype

- curated prototype bundle format
- dependency-safe bundle preflight
- all-or-nothing PostgreSQL bundle ingestion
- mixed human/AI provenance without rewriting AI Candidate Claims as human-created
- first real OSS pilot using pinned Tree-sitter, Salsa, and rust-analyzer revisions
- 3 real Sources / 3 SourceSnapshots / 5 Evidence records / 3 Knowledge Entities / 4 AI-created Candidate Claims
- staged observations forced through Evidence to one immutable SourceSnapshot
- staged observation Evidence links persisted by migration `0002_staged_observation_evidence.sql`

### Relation Provenance v1

- entity-subject and relation-subject Claims share one lifecycle
- normalized PostgreSQL Relation Claim persistence via `0003_relation_claim_subject.sql`
- existing/distinct relation endpoint checks
- Evidence required for Relation Claims
- direct canonical relation writes quarantined
- Relation Claim PostgreSQL round-trip tests
- supersession requires the same subject, a distinct successor, and successor maturity of at least `SUPPORTED`
- additive real-OSS relation overlay: `pilots/incremental-computation-relations-v1.json`
- validated relations remain Claims rather than being copied into a duplicate canonical edge store

### Relation Projection v1

- rebuildable relation read model derived from Claim records
- `validated`, `research`, `challenged`, and `history` views
- one projected edge per Claim; competing assertions are not silently collapsed
- filters by entity, direction, and relation type
- merged entity IDs resolve to the current canonical survivor for querying
- asserted relation endpoints remain visible unchanged for provenance
- redirect-cycle and missing-entity corruption fails closed
- real PostgreSQL + real OSS pilot verification across Candidate → Supported → Validated
- read-only `kneekura-hub relations` CLI

### Problem Query v1

- first-class Problem Knowledge Entities using `kinds: ["problem"]`
- explicit semantic contract: `solution --solves→ problem`
- `solves` relation creation fails closed when the target is not a Problem entity
- read-time semantic validation repeats the same invariant to catch corrupted or legacy data
- `solutions_for_problem`, `problems_solved_by`, and `requirements_for` read APIs
- `validated`, `research`, `challenged`, and `history` maturity views reused from Relation Projection
- no query-time invention from `related_to`, text similarity, tags, or repository popularity
- additive real-Salsa problem overlay: `pilots/incremental-computation-problems-v1.json`
- Candidate results remain research-only until the normal human `VALIDATED` transition
- read-only `solutions`, `solved-problems`, and `requirements` CLI commands
- real PostgreSQL + real OSS pilot verification

Mass crawling and automated knowledge promotion are intentionally not enabled yet.

## Quick start

```bash
python -m venv .venv
# activate the virtualenv
pip install -e '.[dev]'
pytest
```

Validate a JSON record:

```bash
kneekura-hub-validate path/to/record.json
# or
kneekura-hub validate path/to/record.json
```

Preflight the real curated pilot bundle without writing anything:

```bash
kneekura-hub bundle-check pilots/incremental-computation-v1.json
```

Initialize PostgreSQL:

```bash
export KTHUB_DATABASE_URL='postgresql://user:pass@localhost:5432/kneekura'
kneekura-hub init-db
```

Atomically ingest the base pilot with a human reviewer identity while preserving the AI creators recorded on Candidate Claims:

```bash
kneekura-hub ingest-bundle pilots/incremental-computation-v1.json --actor-id prototype-reviewer
```

Then add the Relation Claim and Problem Query overlays without rewriting the base pilot:

```bash
kneekura-hub ingest-bundle pilots/incremental-computation-relations-v1.json --actor-id prototype-reviewer
kneekura-hub ingest-bundle pilots/incremental-computation-problems-v1.json --actor-id prototype-reviewer
```

Query projected relations without writing a graph copy:

```bash
# trusted relationships only
kneekura-hub relations --view validated

# include Candidate, Supported, Validated, and Challenged research assertions
kneekura-hub relations --view research

# outgoing research relations for one entity
kneekura-hub relations \
  --view research \
  --entity-id ke:incremental-computation \
  --direction out

# full audit history of one relation type
kneekura-hub relations \
  --view history \
  --relation-type narrower_than
```

Query explicit problem/solution knowledge:

```bash
# trusted solutions only
kneekura-hub solutions \
  ke:problem:repeated-recomputation-after-input-change \
  --view validated

# include research candidates
kneekura-hub solutions \
  ke:problem:repeated-recomputation-after-input-change \
  --view research

# Problems one entity explicitly claims to solve
kneekura-hub solved-problems \
  ke:query-based-incremental-computation \
  --view research

# explicit requirements / prerequisites
kneekura-hub requirements \
  ke:query-based-incremental-computation \
  --view research
```

Store and retrieve records:

```bash
kneekura-hub ingest path/to/source.json --actor-id reviewer
kneekura-hub ingest path/to/snapshot.json --actor-id reviewer
kneekura-hub get src:example
kneekura-hub list --type claim
```

Govern a claim or merge canonical identities:

```bash
kneekura-hub transition-claim cl:example SUPPORTED --reason 'evidence reviewed' --actor-id reviewer
kneekura-hub transition-claim cl:example VALIDATED --reason 'human verification complete' --actor-id reviewer
kneekura-hub merge-entities ke:survivor ke:duplicate --reason 'same concept' --actor-id reviewer
```

## Documents

- `docs/architecture/BASELINE-v1.md`
- `docs/architecture/CURATION-ENGINE-v1.md`
- `docs/architecture/RELATION-PROVENANCE-v1.md`
- `docs/architecture/RELATION-PROJECTION-v1.md`
- `docs/architecture/PROBLEM-QUERY-v1.md`
- `docs/pilots/INCREMENTAL-COMPUTATION-v1.md`
- `governance/CONSTITUTION.md`
- `governance/policy-v1.json`
- `schemas/v1/hub.schema.json`

## Status

- Design baseline: **v1.0 confirmed**
- Phase 0: **implemented**
- Phase 1: **usable curation core implemented**
- Phase 2: **first real OSS curated pilot implemented**
- Relation Provenance v1: **implemented and merged**
- Relation Projection v1: **implemented and merged**
- Problem Query v1: **implemented; real-pilot verification passing**
- Next pressure: **Evidence Explanation — Claim → Evidence → SourceSnapshot → Source provenance walk**
- Mass discovery: **not enabled yet**
