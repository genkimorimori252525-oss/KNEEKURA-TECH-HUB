# Fresh LAB bridge prerequisite audit

Audited 2026-10-01. TECH HUB base: `933bb9b0a6e8b1d501e148b4b76d5f1f8aeaa502`.
LAB main was independently rechecked at
[`21959d439960d112d05c4c3ee44e54e353246d4e`](https://github.com/genkimorimori252525-oss/KNEEKURA-LAB/commit/21959d439960d112d05c4c3ee44e54e353246d4e).
This is a read-only source audit, not real runtime acceptance.

## Reuse

- Node ESM supervisor and actual `debug-workspace/cli.mjs` machine entrypoint
- Forge Java run/session/nonce/PID/start-time identity checks and startup source/observer drift detection
- Initial write-once RunSnapshot with separate canonical `snapshotHash`
- Compact Evidence Broker and coherent query cuts
- Raw/canonical observation retention, bounded ring/pre-roll capture manifests and finalization
- Exact-UUID observation-target control

## Missing or qualified prerequisites

| Requirement | Current source finding | Owning next change |
|---|---|---|
| Exact TECH HUB build/profile/index/request binding | Not in current immutable snapshot | LAB prelaunch registration and initial snapshot extension |
| Loaded material hashes | Loaded mods are ID/version strings; one bootstrap class hash is not whole Probe/MOD/resource/config attestation | LAB exact material/loaded-runtime inventory |
| Resettable bounded Arena | G3 explicitly unimplemented; legacy arena construction is not reversible reset | LAB Arena baseline/reset backend |
| Typed experiment mutation | Observation target selection exists; generic world/action control does not | LAB typed actions, revision/epoch fencing, durable idempotency and postcondition receipts |
| Atomic four-view capture | Broker evidence cut is query consistency, not a world/camera barrier | LAB explicit capture barrier, canonical cameras and exact restoration |
| Verified cleanup | Current stop attempts termination then records STOPPED without a new bounded PID-exit verification | LAB bounded exit/ownership verification |
| Honest coherence labels | Unknown labels can bypass the existing named-mode checks | LAB supported-mode allowlist |
| Visual evidence/dual presentation | Present in design, not in primary experiment runtime | LAB raw/derived lineage and separate human/AI presentation |

## Identity details that must not be conflated

The RunSnapshot constructor uses `snapshotId`; READY/evidence use
`runSnapshotId`. These refer to the same identity. Its pretty-printed file byte
hash differs from its recursively key-sorted logical `snapshotHash`.

Current build-marker validation binds session/run/nonce and build time. It does
not establish the target JAR digest. `loadedMods` contains `modId@version`, and
`probeBuild` hashes one bootstrap class. Exact new target digests cannot be
injected into an old snapshot and called observed.

Arena/resource epochs currently remain zero in raw observation production.
`EVIDENCE_COMPLETE` concerns transport/store completeness; per-assertion coverage
and raw-row completeness remain independent. Same-tick/cross-writer queries do
not prove an atomic renderer/world barrier.

## Source references

- [Supervisor, snapshot construction and shutdown](https://github.com/genkimorimori252525-oss/KNEEKURA-LAB/blob/21959d439960d112d05c4c3ee44e54e353246d4e/debug-workspace/core.mjs)
- [Workspace capability boundary](https://github.com/genkimorimori252525-oss/KNEEKURA-LAB/blob/21959d439960d112d05c4c3ee44e54e353246d4e/debug-workspace/README.md)
- [Evidence Broker](https://github.com/genkimorimori252525-oss/KNEEKURA-LAB/blob/21959d439960d112d05c4c3ee44e54e353246d4e/debug-workspace/evidence/broker.mjs)
- [Raw/evidence finalization](https://github.com/genkimorimori252525-oss/KNEEKURA-LAB/blob/21959d439960d112d05c4c3ee44e54e353246d4e/debug-workspace/evidence/finalize.mjs)
- [Runtime attestation producer](https://github.com/genkimorimori252525-oss/KNEEKURA-LAB/blob/21959d439960d112d05c4c3ee44e54e353246d4e/debug-workspace/forge-bridge/src/main/java/com/github/tartaricacid/touhoulittlemaid/sim/debug/KneekuraDebugClientBootstrap.java)

## Decision

Proceed with offline X0/X1 and implement missing prerequisites only in LAB.
Reuse both repositories' existing stores and run identities. Do not advertise
real experiment execution, camera readiness or a completed successor plan from
source tests. A separate bounded real-run contract remains necessary after the
owner implementation and compile gates.
