# Finalized LAB result export: source connection

This is a read-only X7 source connection from finalized LAB evidence to the existing TECH experiment-result/CAS importer. It does not launch, dispatch, replay, publish, issue an owner grant, or establish loaded runtime material equivalence.

## API

```js
import { exportFinalizedExperiment } from './debug-workspace/bridge/result-export.mjs';

const bundle = await exportFinalizedExperiment({
  runDir: registeredPrivateRunDirectory,
  requestBytes: registration.bytes.request,
  assertionsBytes: registration.bytes.assertions,
  actionKeys: [{ actionId: 'wait-1', idempotencyKey: 'registered-wait-key' }],
  observationIds: selectedCanonicalObservationIds,
  timelineObservationIds: selectedTimelineObservationIds,
  visualPacketHash: retainedAiPacketFileHashOrNull,
});
```

The request and assertion byte arrays are the original registered bytes. The exporter verifies their hashes against the exact immutable RunSnapshot TECH binding. It does not reproduce Python serialization in JavaScript.

`bundle` contains:

- `result`: the strict TECH ExperimentResult object
- `resultBytes`: its exact serialized bytes
- `manifest`: the hash-only private transport inventory below
- `blobs`: `{contentHash, bytes: Buffer, classification}` entries

```json
{
  "schema_version": 1,
  "kind": "lab_experiment_export",
  "request_hash": "<sha256>",
  "result_hash": "<sha256>",
  "run_snapshot_content_hash": "<sha256>",
  "contains_private_evidence": true,
  "provenance": "FINALIZED_LAB_EVIDENCE_REPORT",
  "runtime_attestation": "NOT_ESTABLISHED",
  "blobs": [
    {"content_hash": "<sha256>", "size_bytes": 123, "classification": "PRIVATE_RUN_SNAPSHOT"}
  ]
}
```

The caller writes those bytes only into its registered private local transport or existing TECH CAS. Public output contains only the manifest, hashes, counts, and explicit uncertainty. This module supplies no output-directory writer or upload operation, and must not be used for automatic publication.

The mandatory raw RunSnapshot remains byte-for-byte intact, including any pre-existing private source/runtime paths. It is classified `PRIVATE_RUN_SNAPSHOT`. Redaction would create a different snapshot and must not be disguised as the original identity. Other classifications are `PRIVATE_RETAINED_EVIDENCE`, `DERIVED_EVIDENCE_PROJECTION`, and `PRIVATE_EXPERIMENT_RESULT`.

## Verification and evidence shape

The exporter requires an existing evidence finalization and verifies the retained snapshot and canonical observations against its inventory. It checks the logical LAB snapshot hash independently of the raw file-content hash, proves the canonical prefix through the existing EvidenceStore, and preserves exact selected JSON row byte slices with source-file hash, byte offset, and length.

Optional selected rows containing absolute local paths are omitted from the outgoing bytes. Their derived selection entry retains the exact source hash and `PRIVATE_FIELDS_NOT_EXPORTED`, with an `UNAVAILABLE` gap. A truncated final producer row is skipped only when the sealed run explicitly records partial evidence and trailing-row loss; earlier verified byte slices remain available with PARTIAL/UNKNOWN gaps. Canonical rows, valid-but-invalid-schema JSON, and undeclared producer corruption remain strict failures. No arbitrary source facts are rewritten or reinterpreted. Process logs, complete raw producer files, and finalization-local path inventories are never exported.

Each action key must match a registered request action ID. The exporter verifies the existing journal chain, exact canonical action bytes, typed parameters, identities, and stable readback. Its receipt evidence capsule preserves the exact journal record bytes in base64 with their content hashes; the capsule itself is explicitly derived. The capsule is a transport artifact, not a new history database.

A journal `VERIFIED` becomes reported `APPLIED` only when every effect hash resolves to an exact retained producer row, that row matches canonical ingestion, and action/Arena identity and postcondition evidence match. Sparse producer completeness is normalized only for canonical comparison; outgoing producer bytes are untouched. Missing, corrupt, partial, accepted-but-unverified, or unsupported effect evidence stays `UNKNOWN`. Explicit pre-dispatch `NOT_RUN` and `[REQUESTED, FAILED]` rejection chains retain their narrower statuses.

A retained AI packet must validate its complete nested schema and artifact identities, match the exact sealed canonical capture and evidence prefix, and retain its source rows. Its derived image/JSON bytes and original PNGs are hash-verified. Selected timeline projections must exactly match their canonical source rows. Camera perturbations remain `PERTURBED` gaps; pixel availability is never visual acceptance.

Bounds: 32 structured and 32 timeline selections, 32 action-key mappings, 128 result evidence entries, 16 MiB per outgoing blob, 64 MiB total outgoing bytes, 1 MiB result JSON, 128 KiB transport manifest, 64 MiB canonical and producer-scan budgets. Exceeding a bound fails explicitly rather than silently dropping evidence. Missing optional selections are explicit gaps.

## Uncertainty remains separate

Evidence shutdown/finalization is not Arena cleanup. Cleanup remains `UNKNOWN` unless the experiment is explicitly `NOT_RUN`, in which case it is `NOT_RUN`. Assertions are always `INCONCLUSIVE` or `NOT_RUN` in this source connection. Disk/class-resource metadata cannot establish gameplay or visual PASS/FAIL. A reported `COMPLETED` means only all requested typed actions have backed reported application; it does not establish repair acceptance.

TECH retains these as `IMPORTED_LAB_REPORT` with `runtime_attestation=NOT_ESTABLISHED`. The existing resume view remains non-replayable and carries no execution authority.

## Finalization integration

`finalize.mjs` dispatches retained capture files by actual kind:

- `pre_roll_capture`: existing canonical prefix/ring replay checks remain
- `cardinal4_capture_manifest`: exact canonical observed source, complete outer observation identity, raw PNG hashes, per-view status and restoration
- `trigger_visual_window`: exact trigger/config/prefix/ring proof, slot-source identities and timing, raw image hashes, and partial/unknown coverage

No capture is relabeled as pre-roll. Unknown or unsupported kinds fail closed. The finalization inventory now includes referenced validated raw PNGs. Ingestion/shutdown completeness retains its established semantics; `captures.coverageStatus`, per-kind records, restoration, and limitations separately expose incomplete visual/trigger coverage.

## Source gates

Portable unit/integration gate:

```text
node --test debug-workspace/bridge/tests/result-export.test.mjs debug-workspace/evidence/tests/finalize-visual-captures.test.mjs
```

Add this as `test:result-export` and append `npm run test:result-export` to the parent-reconciled source CI script. The existing `npm run test:ci` must also pass.

Explicit cross-repository source gate: set `KNEEKURA_TECH_HUB_SOURCE` to the real TECH checkout (and optionally `KNEEKURA_PYTHON`), then run:

```text
node debug-workspace/bridge/tests/result-export-roundtrip.mjs
```

It creates a genuine captured TECH profile/index and prepared request, a source-only finalized LAB fixture, then imports Node-produced blobs through the actual TECH CAS/import/resume functions. It checks unchanged private snapshot bytes, completed reported actions, unknown cleanup, inconclusive assertions, absent runtime attestation, and disabled replay. All temporary source fixtures are removed. No Minecraft, browser, server, or public upload is used.

Still deferred: owner-authorized live execution, real loaded target/config/resource equivalence, restoration and observer-effect proof, Arena cleanup proof, a real repair comparison, and visual-format benchmark acceptance.
