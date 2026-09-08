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
      ↓
Application & Research
```

`SourceSnapshot` is a first-class immutable evidence anchor. AI and scanners first produce `staged_observation` records; they cannot directly merge canonical entities or promote claims to `VALIDATED`.

A staged observation must be backed by Evidence candidates that all resolve to exactly one SourceSnapshot. This keeps discovery observations pinned to the exact source revision that produced them.

## Current implementation

### Phase 0 — Constitution & Schema

- Constitution v1.0
- machine-readable governance policy v1.0
- JSON Schema for core record types
- first-class immutable `source_snapshot` records
- PostgreSQL normalized persistence and migration

### Phase 1 — Curation Engine

- policy-aware `CurationEngine`
- human-gated entity creation / merge
- governed claim maturity transitions
- append-only curation events
- provenance checks for claims and staged observations
- CLI for DB initialization, ingest, get, list, claim transitions, and entity merges
- regression tests and real PostgreSQL integration tests in GitHub Actions

### Phase 2 — Curated Prototype underway

- curated prototype bundle format
- dependency-safe bundle preflight
- all-or-nothing PostgreSQL bundle ingestion
- mixed human/AI provenance without rewriting AI Candidate Claims as human-created
- first real OSS pilot using pinned Tree-sitter, Salsa, and rust-analyzer revisions
- 3 real Sources / 3 SourceSnapshots / 5 Evidence records / 3 Knowledge Entities / 4 AI-created Candidate Claims
- staged observations forced through Evidence to one immutable SourceSnapshot

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

Atomically ingest the pilot with a human reviewer identity while preserving the AI creators recorded on Candidate Claims:

```bash
kneekura-hub ingest-bundle pilots/incremental-computation-v1.json --actor-id prototype-reviewer
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
kneekura-hub merge-entities ke:survivor ke:duplicate --reason 'same concept' --actor-id reviewer
```

## Documents

- `docs/architecture/BASELINE-v1.md`
- `docs/architecture/CURATION-ENGINE-v1.md`
- `docs/pilots/INCREMENTAL-COMPUTATION-v1.md`
- `governance/CONSTITUTION.md`
- `governance/policy-v1.json`
- `schemas/v1/hub.schema.json`

## Status

- Design baseline: **v1.0 confirmed**
- Phase 0: **implemented**
- Phase 1: **usable curation core implemented**
- Phase 2: **curated prototype active; first real OSS pilot passing PostgreSQL integration**
- Next design pressure: **relation provenance before canonical taxonomy scaling**
- Mass discovery: **not enabled yet**
