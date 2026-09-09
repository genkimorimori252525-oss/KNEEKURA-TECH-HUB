# Canonical Selected-File Evidence Extraction v1

## Purpose

Verified Acquisition Commit v1 established the first canonical selected-file boundary:

```text
Discovery
  ↓
Human Selection
  ↓
Human Authorization
  ↓
Authorized Acquisition Execution
  ↓
Verified Acquisition Commit
  ↓
SourceSnapshot + Source(selected-files)
```

This slice begins semantic extraction, but deliberately stops before canonical knowledge claims:

```text
Committed SourceSnapshot
  ↓
re-verify exact stored bytes
  ↓
untrusted extraction proposal
  ↓
Hub-generated exact Evidence anchors
  ↓
NEW StagedObservations
  ↓
(no Claim / no Knowledge Entity promotion)
```

The core rule is:

> An extractor may propose meaning, but it may not propose provenance.

Paths, line ranges, summaries, and candidate names may come from an AI/tool. Evidence IDs, Observation IDs, byte hashes, Git blob hashes, Snapshot linkage, and manifest linkage are generated and verified by the Hub.

## Historical authority versus historical truth

Acquisition Authorization and committed Snapshot validity are intentionally separate.

An Authorization must be effective at execution and verified-commit time. After canonicalization, the Source becomes `selected-files`, which makes the old metadata-only Authorization historical/non-effective.

Evidence extraction therefore **does not** require that old Authorization to remain currently effective.

Instead it verifies the immutable historical chain:

```text
source_acquisition_commit
  ↓
SourceSnapshot
  ↓
source_acquisition_execution
  ↓
source_acquisition_authorization (historical record)
  ↓
exact selected-file store bytes
```

A later Source metadata update does not invalidate an old Snapshot. A mutation of the historical Authorization record does invalidate the chain because its execution-time fingerprint no longer matches.

## Accepted Snapshot contract

Extraction accepts only a SourceSnapshot that has exactly one `source_acquisition_commit`.

The following must agree:

- Snapshot Source ID
- commit Source ID
- commit Snapshot ID
- commit Execution ID
- Snapshot metadata Execution ID
- commit Authorization ID
- Snapshot metadata Authorization ID
- exact revision
- manifest SHA-256
- execution-time Source fingerprint
- execution-time Authorization fingerprint
- storage key
- exact selected-file result list

The historical Authorization record is re-fingerprinted. The current Source record is not required to equal its execution-time fingerprint because canonicalization itself changed `acquisition.level` from `metadata-only` to `selected-files` and current Source metadata may legitimately evolve.

The current Source must still represent at least the committed acquisition depth:

- `selected-files`, or
- `full-source`

## Byte re-verification

Before any extractor output is trusted, the Hub reuses the hardened execution-store checks and verifies:

- storage root exists and is not a symlink
- deterministic execution storage directory exists and is not a symlink
- no symlink entries
- regular files only
- exact file set
- no unexpected directories
- exact byte count per file
- exact SHA-256 per file
- independently recomputed Git blob SHA per file
- independently recomputed selected-files manifest SHA-256

The complete verified bytes are then held in memory for proposal validation.

The physical store is a material cache. It is not self-authenticating truth.

## Untrusted proposal format

The extractor does not submit Hub record IDs or hashes.

Example:

```json
{
  "proposal_version": "1.0",
  "snapshot_id": "ss:acq:...",
  "findings": [
    {
      "summary": "The implementation recomputes only changed inputs.",
      "candidate_names": ["changed-input recomputation"],
      "anchors": [
        {
          "path": "src/lib.rs",
          "line_start": 40,
          "line_end": 55
        }
      ]
    }
  ]
}
```

v1 operational bounds:

- at most 128 findings per proposal
- at most 8 anchors per finding
- at most 16 candidate names per finding
- summary length at most 4000 characters
- candidate name length at most 240 characters
- at most 400 lines per anchor
- at most 256 KiB exact bytes per anchor

These are operational anti-runaway limits, not epistemic quality thresholds.

## Text-only line anchors

`source_lines` Evidence requires a reproducible line range.

Therefore an anchored file must decode as strict UTF-8. Binary selected files may remain part of the committed Snapshot, but v1 will not invent line-oriented Evidence for them.

The extractor may simply omit binary files from its proposal.

## Hub-generated Evidence

For each proposed anchor, the Hub checks that:

1. the path is in the committed selected-file set;
2. the line range exists in the verified bytes;
3. the line range is within the v1 bounds.

It then computes an exact excerpt hash over the original UTF-8 bytes:

```text
content_hash = sha256(exact line bytes)
```

The generated Evidence locator contains:

- path
- line_start
- line_end
- exact line-byte SHA-256
- full-file SHA-256
- full-file Git blob SHA
- Snapshot manifest SHA-256

Evidence IDs are deterministic from:

```text
Snapshot ID
+ path
+ line_start
+ line_end
+ exact excerpt hash
```

The extractor cannot choose the ID.

Extraction-generated Evidence uses `roles: [SUPPORTS]` only in the narrow context of the generated StagedObservation. No Claim is created or attached here, so this role is not a Claim validation decision.

## Hub-generated StagedObservation

The proposal may supply:

- summary
- candidate names
- one or more exact anchors

The Hub supplies:

- deterministic Observation ID
- Source ID
- exact Evidence candidate IDs
- `status = NEW`
- `created_by` from the explicit caller actor

Observation identity includes the creator actor so two extractors can independently propose the same wording without rewriting provenance.

A duplicate exact proposal by the same actor is idempotent.

## Deterministic reuse and conflict handling

Evidence identity is content/provenance based, so the same exact Snapshot line anchor can be reused across multiple observations.

If the deterministic Evidence ID already exists:

- identical provenance is reused;
- conflicting content is rejected.

If the deterministic Observation ID already exists:

- the identical observation is reused;
- conflicting content is rejected.

No silent overwrite is allowed.

## Atomic PostgreSQL ingestion

`check` / preparation performs no writes.

`ingest` performs a complete conflict preflight before writing. For PostgreSQL it then opens one outer transaction and locks the historical provenance rows:

- SourceSnapshot
- source_acquisition_commit
- source_acquisition_execution
- source_acquisition_authorization

The Snapshot store is re-verified again while those DB provenance rows are locked.

Only then are new Evidence and StagedObservation records written through `CurationEngine`.

Nested repository writes remain inside the outer transaction. A failure while writing any later Observation rolls back:

- earlier Evidence
- earlier Observations
- generated curation events

The batch is all-or-nothing.

## What is deliberately not created

This slice does **not** create or change:

- Claim
- Claim maturity
- Knowledge Entity
- entity merge
- Human Review Decision
- Source acquisition depth
- SourceSnapshot
- Acquisition Authorization
- acquisition store contents

No AI proposal can become a `VALIDATED` Claim through this path.

## CLI

Re-verify a committed Snapshot without creating Evidence:

```bash
kneekura-selected-file-extract snapshot-check ss:acq:<id> \
  --storage-root ./var/acquisitions
```

Validate an untrusted proposal without writing:

```bash
kneekura-selected-file-extract check proposal.json \
  --storage-root ./var/acquisitions \
  --actor-type ai \
  --actor-id extractor-name \
  --actor-version model-or-tool-version
```

Ingest only after the same validation succeeds:

```bash
kneekura-selected-file-extract ingest proposal.json \
  --storage-root ./var/acquisitions \
  --actor-type ai \
  --actor-id extractor-name \
  --actor-version model-or-tool-version
```

The CLI itself does not call an AI model. Proposal generation remains a separate adapter so model output stays visibly outside the trust boundary.

## Acceptance cases

The test suite covers:

- exact committed Snapshot verification
- exact line-byte hashing
- multi-anchor observations
- no writes during preparation / `check`
- Evidence + NEW StagedObservation only
- no Claim or Knowledge Entity creation
- idempotent repeated ingest
- deterministic ID conflict rejection
- tampered store bytes
- uncommitted Snapshot
- unacquired path
- out-of-range line anchor
- binary/non-UTF-8 anchor
- current Source metadata evolution after commit
- historical Authorization mutation detection
- real PostgreSQL round-trip
- full PostgreSQL batch rollback on a mid-write failure

## Next pressure

The next safe slice is **Staged Observation Triage v1**.

It should turn the large lower-trust observation lake into an explicit review queue without yet promoting Claims automatically. Likely responsibilities:

- duplicate / near-duplicate candidate grouping
- same-Snapshot and cross-Snapshot observation clustering
- exact provenance display
- human/tool triage state transitions
- rejection / expiry without deletion
- bounded proposal of Claim Candidates
- no AI-only `SUPPORTED` or `VALIDATED` promotion

The Hub should remain able to collect broadly while making promotion progressively more expensive.
