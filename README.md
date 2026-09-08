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

## Current implementation

The first implementation slice now covers **Phase 0 and the usable Phase 1 curation core**:

- Constitution v1.0
- machine-readable governance policy v1.0
- JSON Schema for core record types
- first-class immutable `source_snapshot` records
- PostgreSQL normalized persistence and migration
- policy-aware `CurationEngine`
- human-gated entity creation / merge
- governed claim maturity transitions
- append-only curation events
- CLI for DB initialization, ingest, get, list, claim transitions, and entity merges
- regression tests and real PostgreSQL integration tests in GitHub Actions

Mass crawling and automated knowledge promotion are intentionally not part of this slice.

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

Initialize PostgreSQL:

```bash
export KTHUB_DATABASE_URL='postgresql://user:pass@localhost:5432/kneekura'
kneekura-hub init-db
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
- `governance/CONSTITUTION.md`
- `governance/policy-v1.json`
- `schemas/v1/hub.schema.json`

## Status

- Design baseline: **v1.0 confirmed**
- Phase 0: **implemented**
- Phase 1: **usable curation core implemented**
- Phase 2: **curated prototype next**
- Mass discovery: **not enabled yet**
