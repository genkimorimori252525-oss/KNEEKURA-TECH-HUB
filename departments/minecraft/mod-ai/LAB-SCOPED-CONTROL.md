# Separately registered LAB scoped control

The legacy `kneekura.lab.local-bridge.v1` adapter remains registration/read-only.
Scoped control requires a separate registry with backend
`kneekura.lab.scoped-control.v1`. Neither registry starts Minecraft or grants a
permission through an ExperimentRequest. Source tests do not establish live
repair acceptance.

The new registry uses the same exact outer fields as the legacy adapter. Its
`module_hashes` keys are the 19 fixed repository-relative paths in
`experiment_control.MODULES`, including the owner entry point and every imported
bridge/evidence/PNG module. The executable, complete source closure, private owner
configuration, and owner envelope are hash-checked on every invocation. A declared
Git revision is metadata; the pinned bytes are the checked identities.

The private owner configuration is exactly:

```json
{
  "schemaVersion": 1,
  "runtimeRoot": "/operator-selected/runtime",
  "inputRoot": "/operator-selected/private-transport",
  "run": {
    "runDir": "/operator-selected/runtime/run",
    "identity": {
      "debugSessionId": "session-id",
      "runId": "run-id",
      "runSnapshotId": "snapshot-id",
      "processEpoch": 1,
      "experimentId": "experiment-id",
      "requestHash": "<request SHA-256>"
    },
    "ownerEnvelopeHash": "<owner-envelope SHA-256>"
  }
}
```

`runDir/control/owner-envelope.json` must match its pinned hash and the exact
run/request identity. The LAB source and run-specific Java gate independently
validate the prepared grant, material linkage, disposable world, owner lease,
order and replay fences. A reported owner is not live runtime attestation.

## Explicit commands

```text
kneekura-minecraft experiment inspect-control --registry CONTROL.json
kneekura-minecraft experiment inspect-owner --registry CONTROL.json --request-hash HASH
kneekura-minecraft experiment submit-action --registry CONTROL.json --request-hash HASH --action-id ID
kneekura-minecraft experiment request-capture --registry CONTROL.json --request-hash HASH --capture-index 0
kneekura-minecraft experiment inspect-action --registry CONTROL.json --request-hash HASH --action-id ID
kneekura-minecraft experiment request-cleanup --registry CONTROL.json --request-hash HASH
kneekura-minecraft experiment inspect-cleanup --registry CONTROL.json --request-hash HASH
kneekura-minecraft experiment export-result --registry CONTROL.json --request-hash HASH --observation-id ID
kneekura-minecraft experiment import-export --registry CONTROL.json --request-hash HASH --manifest-hash HASH
kneekura-minecraft experiment inspect-control-receipt --receipt-hash HASH
```

Actions select an existing action ID only; there is no action-payload or command
argument. Capture indices select Cardinal-4 slots, each consuming four captures
from the retained request budget. Export accepts up to 32 `--observation-id` and
32 `--timeline-observation-id` selections plus an optional `--visual-packet-hash`.

Submission responses are `REQUESTED`, `ALREADY_RECORDED`, or `OUTCOME_UNKNOWN`.
They never mean completion or gameplay/visual PASS. An uncertain immutable CAS
receipt is retained before invocation. Timeouts, output limits, invalid responses
and process failures preserve uncertainty with no automatic retry. Replay/order
authority remains LAB's existing journal, independent of the selected TECH Store.

`request-cleanup` explicitly selects the owner's existing one-reset allowance;
it takes no reset parameters and never automatically runs after an action or
failure. Its receipt points only to read-only `inspect-cleanup`. A published
cleanup marker without a native journal remains `OUTCOME_UNKNOWN`; absent marker
and journal report `NEVER_SEEN`. Duplicate requests report `ALREADY_RECORDED`.
None of these reports proves the reset was applied or Arena cleanup confirmed.
Even a `VERIFIED` cleanup journal only covers supported bounded reset classes;
an explicitly supplied cleanup receipt continues to recommend read-only
reconciliation and cannot clear uncertainty about earlier actions.

## Private result import

The fixed private transport destination is
`inputRoot/exports/<requestHash>/manifests/<manifestHash>.json` with hash-named
files under the sibling `blobs/` directory. It stays outside the sealed run.
Import checks exact manifest fields, hash/size/classification for every file,
the complete result/snapshot/evidence inventory, and the original request linkage
before retaining new bytes in the existing CAS. It does not follow any path
inside report data. Limits are 128 KiB manifest, 1 MiB result, 2 MiB snapshot,
16 MiB per evidence blob and 64 MiB for the entire transport inventory.

Raw snapshot bytes remain private. The imported summary retains
`provenance: IMPORTED_LAB_REPORT`,
`export_provenance: FINALIZED_LAB_EVIDENCE_REPORT`, and
`runtime_attestation: NOT_ESTABLISHED`. A finalized evidence seal does not prove
Arena cleanup, loaded config/resources, or gameplay/visual acceptance.

## Inert planning

`task prepare` and `task capabilities` accept optional
`--experiment-control-registry` and `--experiment-control-receipt` inputs.
They only inspect local pinned bytes and retained receipts, without subprocesses
or writes. A pending or uncertain receipt suppresses every new side-effecting
recommendation and points to read-only inspection. Owner inspection alone cannot
resolve an uncertain capture; the retained capture/evidence needs reconciliation.

## Native owner activation and evidence limits

LAB's existing launch flow can opt in through its private `ownerControl` configuration, selecting the frozen request and a hash-pinned operator registration. The registration binds the canonical disposable integrated-world directory, dimension, fixed class-resource hashes and allowed diagnostic/capture permissions. The launch flow prepares an immutable run-local closure before process creation, removes inherited owner activation unless preparation succeeds, and records the initial intent in RunSnapshot. The runtime checks its own PID, exact canonical snapshot bytes, the already instantiated MOD container and class resources, and the actual server world before installing the bounded owner.

The two supported linkage modes are `PACKAGED_JAR_CODE_SOURCE_AND_CLASS_RESOURCE_LINKAGE` and `OBSERVED_CLASS_RESOURCE_AND_CONTAINER_LINKAGE`. Both describe observed correspondence only. Loaded config and resource equivalence, transformed class definitions and full target attestation remain `NOT_ESTABLISHED`; this registration grants only explicitly selected `BOUNDED_DIAGNOSTIC_CONTROL`. It cannot turn a structured or visual assertion into PASS.

Runtime installation is nonrenewable for a prepared envelope. The existing LAB journal owns action order and replay behavior; owner status is a recent hint, not another authority or database. FAILED summaries also require reconciliation because a failure can occur after application. Private exported evidence is finalized once, then validated and imported without replacing raw snapshot or evidence bytes.

## Deferred acceptance

The source phase does not close the saved design's real-runtime acceptance:

- Actual owner installation, world reset, typed mutation, interruption handling and cleanup
- Camera pause/barrier, four views, exact restoration and impact on the running experiment
- KNEEKURA-specific visual-format benchmark and matched real before/after repair cycle
- A second AI resuming the real evidence and recording the verified lesson
- Loaded target/config/resource/transformed-class equivalence
- Windows self-hosted build/Thin Viewer runtime gate

X4/X6 final independent review remains unperformed after its review continuation was blocked; author tests and source compilation are reported separately. X8 synchronized multipass remains `DEFERRED`: it may only be selected after a concrete defect shows the sequential rig is insufficient.

For the code-first publication, LAB commits use the standard `[skip ci]` marker to honor the instruction to defer real-device verification. Existing LAB workflows and runner settings are untouched. TECH's hosted source workflow checks out the exact published LAB commit and pinned MOD source, runs source contracts and paired fixtures, and compiles the real Forge source without launching Minecraft. Skipped Windows checks are not counted as successful checks.
