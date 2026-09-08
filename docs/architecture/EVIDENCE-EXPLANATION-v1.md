# Evidence Explanation v1

## Purpose

KNEEKURA TECH HUB must be able to answer not only:

> What does the Hub currently think?

but also:

> Why did this Claim or query result appear?

Evidence Explanation v1 reconstructs the provenance chain already stored by the curated core:

```text
Claim
  ↓ evidence_ids
Evidence
  ↓ source_snapshot_id
SourceSnapshot
  ↓ source_id
Source
```

It introduces no new knowledge store and performs no AI inference while explaining a result.

## Core query

`explain_claim(repository, claim_id)` returns the exact Claim plus one provenance chain for each referenced Evidence record.

Evidence chains preserve the order of `Claim.evidence_ids`.

Result shape:

```json
{
  "claim": {"id": "cl:..."},
  "evidence_count": 2,
  "evidence_chains": [
    {
      "evidence": {"id": "ev:..."},
      "source_snapshot": {"id": "ss:...", "revision": "..."},
      "source": {"id": "src:..."}
    }
  ]
}
```

The complete underlying records are returned rather than a lossy summary so callers can inspect locator, roles, revision, hashes, acquisition mode, license handling, and source metadata.

## Query-result explanation

Problem Query and Relation Projection results already carry a `relation_claim.claim_id`.

`explain_relation_result(repository, result)` extracts that immutable Claim ID and delegates to `explain_claim`.

The explanation therefore does not trust a rendered query result as the source of truth. It uses only the Claim ID to reload canonical provenance records.

## Fail-closed integrity

Evidence Explanation refuses to emit a partial chain when a referenced record is corrupt.

It rejects:

- missing Claim;
- non-Claim record under the requested ID;
- missing referenced Evidence;
- non-Evidence record under an Evidence ID;
- missing SourceSnapshot;
- missing Source;
- a SourceSnapshot whose `source_id` does not match the Evidence Source.

This is important because a partial explanation can look authoritative even when the provenance chain is broken.

## Read-only guarantee

Explanation functions never write, replace, promote, merge, or normalize records.

They return deep copies of the stored records. Calling an explanation query cannot change Claim maturity, Evidence, SourceSnapshot, Source, or curation history.

## Real Salsa acceptance

The existing Problem Query pilot contains the Candidate Relation Claim:

```text
Query-based Incremental Computation
  --solves→
Repeated recomputation after input changes
```

Its Claim ID is:

`cl:salsa:query-incremental:solves:repeated-recomputation:e021c01d`

Evidence Explanation reconstructs two supporting Salsa README Evidence anchors and verifies that both lead to:

- Source: `src:github:salsa-rs:salsa`
- SourceSnapshot: `ss:github:salsa-rs:salsa:e021c01d`
- pinned revision: `e021c01d4939408c89c9325ad2426660117a8b32`

The Claim remains `CANDIDATE`; explaining it does not imply validation.

## CLI

```bash
kneekura-hub explain-claim \
  cl:salsa:query-incremental:solves:repeated-recomputation:e021c01d
```

The command is read-only and returns the structured provenance chain as JSON.

## Non-goals

Evidence Explanation v1 does not:

- generate a persuasive natural-language justification;
- decide whether Evidence is sufficient;
- promote or demote Claims;
- rank sources by popularity;
- silently repair broken provenance;
- fetch a newer upstream revision;
- treat an explanation as proof that the Claim is correct.

Explanation answers **where this Claim came from**. Claim maturity and human validation answer **how much the Hub currently trusts it**.

## Next pressure

The next useful layer is an evidence-strength / review view that keeps explanation separate from judgment. It should summarize things such as:

- how many independent Sources support a Claim;
- whether Evidence is direct code observation, author documentation, experiment result, or inference support;
- whether all Evidence comes from one SourceSnapshot;
- whether contradictory/refuting Evidence exists;
- when the Claim was last verified.

That layer should remain a derived read model rather than mutating the underlying Claim.
