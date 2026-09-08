# Architecture Baseline v1.0

## Mission
KNEEKURA TECH HUB has three faces:

1. **OSS Technology Search Engine** — broad discovery of techniques, designs, algorithms, failures, and migrations.
2. **Evidence-backed Technology Encyclopedia** — curated claims linked to reproducible evidence.
3. **Design Research Laboratory** — comparison, experimentation, and KNEEKURA application hypotheses.

## Separation of concerns

```text
Discovery Universe
      |
      v
Discovery & Collection Layer
  - source index
  - staged observations
  - technique candidates
      |
      v
Curation Gate
      |
      v
Curated Knowledge Core
  Source -> Evidence -> Claim -> Knowledge Entity
      |
      v
Application & Research
```

Mass discovery and canonical knowledge are intentionally different data planes. Large quantities are acceptable in discovery; canonical promotion is gated.

## Curated core

### Knowledge Entity
Identity only: immutable ID, canonical labels, aliases, kinds, abstraction level, relations, identity lifecycle.

### Claim
A typed assertion about an entity. Claims carry scope, applicability, maturity, time, and provenance references.

### Evidence
A precise anchor that supports, refutes, or qualifies a claim. Evidence is tied to a source snapshot or stable locator.

### Source
The original repository, paper, RFC, issue, benchmark, postmortem, or experiment artifact. AI interpretation is not an original source.

## Staging boundary
AI and scanners write `staged_observation` records first. They do not write validated knowledge directly.

## Claim types
- `DIRECT_OBSERVATION`
- `AUTHOR_CLAIM`
- `INFERENCE`
- `EXPERIMENT_RESULT`
- `JUDGMENT`

## Claim maturity
- `CANDIDATE`
- `SUPPORTED`
- `VALIDATED`
- `CHALLENGED`
- `SUPERSEDED`
- `REJECTED`

`ESTABLISHED` is deliberately absent from v1 to reduce authority drift.

## Source acquisition levels
- `metadata-only`
- `snapshot`
- `selected-files`
- `full-source`

Default: `metadata-only`.

## v1 non-goals
No automatic canonical merge, graph database, RDF/SHACL ontology, GitHub-wide crawler, automatic validated promotion, or global technology quality score.
