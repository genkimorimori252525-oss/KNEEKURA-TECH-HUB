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
Source → Evidence → Claim → Knowledge Entity
      ↓
Application & Research
```

AI and scanners first produce `staged_observation` records. They cannot directly merge canonical entities or promote claims to `VALIDATED`.

## Current implementation

The first implementation slice covers **Phase 0 and the Phase 1 foundation**:

- Constitution v1.0
- machine-readable governance policy v1.0
- JSON Schema for core record types
- PostgreSQL foundation migration
- Python validation library and CLI
- regression tests for critical safety rules
- GitHub Actions test workflow

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
```

## Documents

- `docs/architecture/BASELINE-v1.md`
- `governance/CONSTITUTION.md`
- `governance/policy-v1.json`
- `schemas/v1/hub.schema.json`

## Status

- Design baseline: **v1.0 confirmed**
- Phase 0: **foundation implemented**
- Phase 1: **curation core foundation underway**
- Mass discovery: **not enabled yet**
