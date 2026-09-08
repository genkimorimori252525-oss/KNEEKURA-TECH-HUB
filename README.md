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
                               Evidence Explanation
                                          ↓
                                  Application & Research
```

`SourceSnapshot` is a first-class immutable evidence anchor. AI and scanners first produce `staged_observation` records; they cannot directly merge canonical entities or perform a `VALIDATED` promotion.

A staged observation must be backed by Evidence candidates that all resolve to exactly one SourceSnapshot. Those Observation ↔ Evidence links are persisted in PostgreSQL so the source-revision provenance survives reload.

Relationships between Knowledge Entities are also evidence-backed Claims. A Claim has exactly one subject: either one `entity_id`, or a `relation` consisting of source entity, relation type, and target entity. Direct non-empty `KnowledgeEntity.relations` writes remain rejected so an unproven taxonomy guess cannot become canonical graph truth.

`created_by` remains authorship provenance. An AI-created Candidate Claim can later be human-reviewed and promoted without rewriting its creator identity; the human transition is recorded separately in the curation-event trail.

Relation graph views are rebuilt from Claims. They are never stored as a second canonical graph. Projection preserves the asserted endpoint IDs and also resolves current canonical identities through human-approved entity-merge redirects.

Problem-oriented queries are deliberately conservative. They read only explicit evidence-backed relation claims such as `solves` and `requires`; they do not infer solutions from popularity, text similarity, `related_to`, or an AI guess made during query execution.

Evidence Explanation reconstructs `Claim → Evidence → SourceSnapshot → Source` directly from canonical records. It does not generate a new justification, promote the Claim, or silently repair broken provenance.

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
- staged observations forced through Evidence to one immutable SourceSnapshot
- staged observation Evidence links persisted by migration `0002_staged_observation_evidence.sql`

### Relation Provenance v1

- entity-subject and relation-subject Claims share one lifecycle
- normalized PostgreSQL Relation Claim persistence via `0003_relation_claim_subject.sql`
- Evidence required for Relation Claims
- direct canonical relation writes quarantined
- supersession requires the same subject, a distinct successor, and successor maturity of at least `SUPPORTED`
- additive real-OSS relation overlay: `pilots/incremental-computation-relations-v1.json`

### Relation Projection v1

- rebuildable relation read model derived from Claim records
- `validated`, `research`, `challenged`, and `history` views
- one projected edge per Claim; competing assertions are not silently collapsed
- filters by entity, direction, and relation type
- merged entity IDs resolve to the current canonical survivor for querying
- asserted relation endpoints remain visible unchanged for provenance
- real PostgreSQL + real OSS pilot verification
- read-only `kneekura-hub relations` CLI

### Problem Query v1

- first-class Problem Knowledge Entities using `kinds: ["problem"]`
- explicit semantic contract: `solution --solves→ problem`
- `solves` creation and query-time interpretation fail closed when the target is not a Problem entity
- `solutions_for_problem`, `problems_solved_by`, and `requirements_for` read APIs
- no query-time invention from `related_to`, text similarity, tags, or repository popularity
- additive real-Salsa problem overlay: `pilots/incremental-computation-problems-v1.json`
- Candidate results remain research-only until human `VALIDATED` transition
- read-only `solutions`, `solved-problems`, and `requirements` CLI commands

### Evidence Explanation v1

- rebuilds the exact `Claim → Evidence → SourceSnapshot → Source` chain
- preserves `Claim.evidence_ids` order
- returns full underlying records rather than a lossy summary
- projected/problem-query results can be explained by their immutable `relation_claim.claim_id`
- missing or wrong-type provenance records fail closed
- SourceSnapshot/Source mismatch fails closed
- explanation is read-only and does not alter Claim maturity
- real Salsa Problem Query result resolves to the pinned `e021c01d4939408c89c9325ad2426660117a8b32` revision
- read-only `kneekura-hub explain-claim` CLI

Mass crawling and automated knowledge promotion are intentionally not enabled yet.

## Quick start

```bash
python -m venv .venv
# activate the virtualenv
pip install -e '.[dev]'
pytest
```

Initialize PostgreSQL and ingest the pilot overlays:

```bash
export KTHUB_DATABASE_URL='postgresql://user:pass@localhost:5432/kneekura'
kneekura-hub init-db
kneekura-hub ingest-bundle pilots/incremental-computation-v1.json --actor-id prototype-reviewer
kneekura-hub ingest-bundle pilots/incremental-computation-relations-v1.json --actor-id prototype-reviewer
kneekura-hub ingest-bundle pilots/incremental-computation-problems-v1.json --actor-id prototype-reviewer
```

Query explicit problem/solution knowledge:

```bash
kneekura-hub solutions \
  ke:problem:repeated-recomputation-after-input-change \
  --view research

kneekura-hub requirements \
  ke:query-based-incremental-computation \
  --view research
```

Explain exactly why one returned Claim exists:

```bash
kneekura-hub explain-claim \
  cl:salsa:query-incremental:solves:repeated-recomputation:e021c01d
```

The output includes the Claim, each referenced Evidence record, its immutable SourceSnapshot, and the Source.

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
- `docs/architecture/EVIDENCE-EXPLANATION-v1.md`
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
- Problem Query v1: **implemented and merged**
- Evidence Explanation v1: **implemented; verification in progress**
- Next pressure: **derived evidence-strength / review view without mutating Claims**
- Mass discovery: **not enabled yet**
