# X0 LAB bridge readiness audit

Date: 2026-10-01 UTC. Scope: read-only source audit; no Minecraft launch, workflow dispatch, configuration change, code change, or test execution.

## Decision

**Offline TECH HUB X0 contracts and X1 import validation can proceed. A real bridge execution is BLOCKED on LAB-owned work.** LAB has substantive G1/G2 infrastructure to reuse, but neither its current source nor its checked-in acceptance status supports claiming resettable Arena, typed experiment mutations, exact artifact attestation, or Cardinal-4/dual-presentation capture readiness.

Exact fresh LAB main, confirmed twice with the GitHub branch API:

- `21959d439960d112d05c4c3ee44e54e353246d4e`
- [Commit: G2 manual real-Minecraft workflow hardening (#27)](https://github.com/genkimorimori252525-oss/KNEEKURA-LAB/commit/21959d439960d112d05c4c3ee44e54e353246d4e)
- This is the same commit reviewed by the approved TECH HUB bridge design; there is no newer implementation on main to assume.
- TECH HUB checkout audited against: `933bb9b0a6e8b1d501e148b4b76d5f1f8aeaa502`. Full approved 1,444-line bridge design read.

## Provenance and verification limits

The HTTPS clone could not authenticate (`could not read Username`). Authorized GitHub connector reads succeeded. The full recursive Git tree was retrieved and 44 relevant exact-commit text files were materialized for local inspection. All 44 local byte streams were verified against the Git blob SHA reported by GitHub; no source files were modified from those exact bytes. This is materialized exact source, not a Git checkout or configured runtime workspace.

The initial 44 primary source files were independently Git-blob verified. The remaining 180 upstream blobs were later materialized and verified as well, yielding the complete 224-blob source for offline testing. No runtime evidence was obtained by this audit.

The full tree contains no AGENTS.md or `.agents/skills` instructions. Relevant platform software-engineering guidance was read. No code-lab engine was needed or run. No tests, builds, or runtime acceptance were executed. The checked-in [G2 status, lines 9–18](https://github.com/genkimorimori252525-oss/KNEEKURA-LAB/blob/21959d439960d112d05c4c3ee44e54e353246d4e/docs/KNEEKURA_AUTONOMOUS_DEBUG_WORKSPACE_G2_STATUS_20260919.md#L9-L18) labels both G1/G2 implementation as CODE COMPLETE CANDIDATE and real-machine acceptance as PENDING. This audit did not obtain a newer real-machine acceptance artifact; it does not certify current machine readiness.

## Actual runtime and machine entrypoint

- Supervisor, evidence store, Broker and CLI: Node ESM `.mjs`, no Python runtime service.
- Probe: Java Forge instrumentation under `debug-workspace/forge-bridge/src/main/java/.../sim/debug/`.
- Current supplied profile: Forge 1.20.1 `reimu-mod` workspace, Windows `gradlew.bat runClient`, integrated server and one exact singleplayer debug-world name.
- Real Minecraft/Forge Gradle wiring is owned by the registered external MOD workspace. LAB injects its canonical debug source tree through `KNEEKURA_DEBUG_FORGE_BRIDGE_SRC` only for debug mode.
- Actual local entrypoint: `node debug-workspace/cli.mjs <command> --config <registered config>`.
- Existing commands: `doctor`, `start`, `status`, `timeline`, `smoke`, `g2-smoke`, `stop`, `target`, `target-clear`, `target-status`, `evidence-status`, `evidence-anomalies`, `evidence-entity`, `evidence-gap`, `evidence-capture`, `evidence-finalize`.
- There is **no ExperimentRequest execution command**. `evidence-capture` is structured pre-roll retention, not screenshot capture. The configurable `launch.command/args/env/shell` belongs to trusted registered configuration; never expose it as request-controlled data.

Sources: [CLI](https://github.com/genkimorimori252525-oss/KNEEKURA-LAB/blob/21959d439960d112d05c4c3ee44e54e353246d4e/debug-workspace/cli.mjs), [profile](https://github.com/genkimorimori252525-oss/KNEEKURA-LAB/blob/21959d439960d112d05c4c3ee44e54e353246d4e/debug-workspace/profiles/reimu-mod.example.json), [configuration validation, core.mjs 50–124](https://github.com/genkimorimori252525-oss/KNEEKURA-LAB/blob/21959d439960d112d05c4c3ee44e54e353246d4e/debug-workspace/core.mjs#L50-L124).

## Readiness by prerequisite

| Area | Actual implementation | Bridge readiness / smallest missing requirement |
|---|---|---|
| Run identity | Preallocated debugSessionId/runId/processEpoch/runSnapshotId; per-run nonce; READY checks exact run/world/nonce; PID/start-time/command ownership; startup source/observer drift rejection | Reuse. Add exact prelaunch TECH HUB binding and actual loaded target artifact/config/resource hash attestation in LAB |
| Runtime attestation | Minecraft/Forge/Java/topology, PID identity, sorted modId@version list, bootstrap-class probeBuild hash | Partial. Mod list contains no MOD hashes; one class hash is not complete Probe hash. Build marker validation is session/run/nonce + builtAt, not target JAR digest |
| Immutable RunSnapshot | Write-once `run-snapshot.json`, canonical object snapshotHash, source + observer before/ready fingerprint, runtime info | Reuse snapshot writer. Extend before its first write; never amend historical snapshots. Existing schema lacks TECH HUB identities and Arena/config/resource digest bindings |
| Arena/reset | G3 is explicitly unimplemented in primary debug workspace; old SimArena builds floor/blocks and deletes nearby non-player entities | Blocked. Legacy tank setup is not bounded reversible G3 reset or verified baseline |
| Typed world/entity actions | Only observation target-selection control exists, bound to run/snapshot/process epoch and revision | Blocked. Need bounded typed mutation envelope, lease/revision fencing, durable idempotency, postcondition receipts and UNKNOWN reconciliation |
| Evidence Broker | Compact status, UUID lookup, freshness/loss/gap reporting; cross-side/AI consistency; mixed-run/epoch rejection; per-writer sequence cut | Reuse. Evidence Cut is a query consistency result, not freeze/barrier. Strict bridge must allow only actually supported coherence modes |
| Raw retention | Raw JSONL CREATE_NEW producer, incremental byte cursors, identity validation, canonical observations/findings, hashes at finalization | Reuse for structured evidence. Extend artifact inventory for raw image/derived bundles without creating a second evidence DB |
| Ring/pre-roll | Bounded in-memory observation ring; explicit capture manifest references canonical observation prefix and IDs; finalizer replays capture proof | Reuse. Does not implement automatic trigger + post-roll or visual ring capture; those remain G4/X5 |
| Shutdown/finalization | Run-bound shutdown request/ACK, bounded writer drain, ownership-fenced process termination, write-once EVIDENCE_COMPLETE/PARTIAL, sealed store | Reuse with cleanup hardening: actual process exit must be reverified before bridge cleanup can be called complete |
| Dual presentation/capture barrier | Design concepts; old single-view YSM Golden capture has useful same-frame camera contracts | Blocked. No primary RunSnapshot/experiment-bound Cardinal-4 barrier, restoration receipt, raw scene vs human-composite boundary, or paired human/AI presentation records |

## Exact RunSnapshot wire facts

Authoritative constructor: [core.mjs 1143–1175](https://github.com/genkimorimori252525-oss/KNEEKURA-LAB/blob/21959d439960d112d05c4c3ee44e54e353246d4e/debug-workspace/core.mjs#L1143-L1175). File location: `<runtimeRoot>/sessions/<debugSessionId>/runs/<runId>/run-snapshot.json`.

Current object fields:

```text
schemaVersion: 1
snapshotId                    # NOT runSnapshotId in this object
createdAt
debugProfile
workspaceId
debugSessionId
runId
processEpoch
worldName
source: { before, ready, stableDuringStartup }
observer: { before, ready, stableDuringStartup,
            forgeBridgeSourceDir, observationSchemaVersion: 1 }
build: <original accepted build marker object>
runtime: { pid, startedAtEpochMs, ownership, attestation }
snapshotHash
```

The `before` and `ready` Git identities contain commit, branch, dirty, statusSha256, trackedDiffSha256, fingerprintSha256, untrackedContentComplete and per-untracked-file hashes. Startup compares fingerprints; untracked hashing is bounded to 256 files / 64 MiB, so incomplete identity remains visible. These are not built-runtime artifact hashes. [core.mjs 454–607](https://github.com/genkimorimori252525-oss/KNEEKURA-LAB/blob/21959d439960d112d05c4c3ee44e54e353246d4e/debug-workspace/core.mjs#L454-L607)

`snapshotHash` is `sha256:` plus SHA-256 of UTF-8 `JSON.stringify(recursively-key-sorted snapshot object)` **before adding snapshotHash**. Arrays retain order. The pretty-printed raw file's byte hash is a separate identity. Write uses `flag:'wx'`. [core.mjs 610–648](https://github.com/genkimorimori252525-oss/KNEEKURA-LAB/blob/21959d439960d112d05c4c3ee44e54e353246d4e/debug-workspace/core.mjs#L610-L648)

READY and raw rows instead use `runSnapshotId`, which equals snapshotId. READY exact-identity checks are at core.mjs 290–359. Build marker validation only checks debugSessionId, runId, handshakeNonce and builtAt at 363–374. Runtime Java attestation is [KneekuraDebugClientBootstrap.java 257–315](https://github.com/genkimorimori252525-oss/KNEEKURA-LAB/blob/21959d439960d112d05c4c3ee44e54e353246d4e/debug-workspace/forge-bridge/src/main/java/com/github/tartaricacid/touhoulittlemaid/sim/debug/KneekuraDebugClientBootstrap.java#L257-L315).

### Proposed successor extension, not current LAB capability

The parent TECH HUB offline plan proposes immutable snapshot `techHub` equal to experiment_binding(request):

```text
schema_version: 1
experiment_id
generation
request_hash
target: { profile_id, index_snapshot_id, build_artifact_hash,
          source_revision, dirty_hash, config_hash, resource_hash }
arena_id
arena_baseline_hash
assertions_hash
```

This is a sound detached linkage contract if clearly labeled proposed. LAB must validate and record it **before** writing the immutable snapshot, hash the entire new snapshot, and independently prove artifact/runtime correspondence. A matching caller-supplied object only proves reported consistency. TECH HUB's `provenance=IMPORTED_LAB_REPORT` and `runtime_attestation=NOT_ESTABLISHED` should remain until an authorized registered adapter establishes provenance. Exact raw-file CAS hash must remain distinct from LAB's internal canonical snapshotHash.

Existing LAB snapshots cannot honestly satisfy this extension. Do not add a `techHub` field to an old snapshot and call it a historical runtime fact.

## Arena/actions: concrete LAB owner boundary

The primary README explicitly marks Arena reset/action API and mutation fencing absent. [README 42–48](https://github.com/genkimorimori252525-oss/KNEEKURA-LAB/blob/21959d439960d112d05c4c3ee44e54e353246d4e/debug-workspace/README.md#L42-L48)

LAB's planned operation names are `world.inspectRegion/getBlock/setBlock/applyBlockBatch/fill/replace/clearRegion/restoreArena/buildShape`, `entity.inspect/spawn/remove/teleport/setTarget`, `scenario.reset/wait`, `capture.snapshot/screenshot`, `probe.configure/escalate/deescalate`. These are **design vocabulary, not callable APIs**. A TECH HUB enum such as wait_ticks/teleport_subject/set_block needs explicit future mapping. `use_item` has no existing supported action contract to reuse. [LAB plan 91–102](https://github.com/genkimorimori252525-oss/KNEEKURA-LAB/blob/21959d439960d112d05c4c3ee44e54e353246d4e/docs/KNEEKURA_AUTONOMOUS_DEBUG_WORKSPACE_V1_PLAN.md#L91-L102)

Smallest useful G3 slice in LAB:

1. One bounded Arena preset with arenaId/epoch/revision, baseline hash, bounds and allowedMutationBounds; explicitly classify resettable vs persistent/external/unknown state.
2. Only the actions required by the first experiment; run/snapshot/process/arena identity, actionId/idempotencyKey, exact subject UUID or region, expectedArenaRevision and preconditions.
3. One active experiment/writer lease; serialized queue; durable same-key/same-payload receipts and same-key/different-payload rejection.
4. REQUESTED → ACCEPTED → APPLIED → VERIFIED only after rereading postconditions. Preserve PARTIAL_APPLY/OUTCOME_UNKNOWN; never retry uncertain mutation blindly.
5. Reset baseline remeasurement and ARENA_NOT_CLEAN on mismatch; increment epochs and invalidate delta/forward-fill/ring interpretation across reset/resource/target boundaries.

These are already LAB design requirements at plan lines 408–494, 611–637 and 803–816. Current Java observations hardcode arenaEpoch and resourceEpoch to 0: [EvidenceWriter 313–327](https://github.com/genkimorimori252525-oss/KNEEKURA-LAB/blob/21959d439960d112d05c4c3ee44e54e353246d4e/debug-workspace/forge-bridge/src/main/java/com/github/tartaricacid/touhoulittlemaid/sim/debug/KneekuraDebugEvidenceWriter.java#L313-L327).

Do not adapt legacy SimArena as if G3 already exists: it chooses a broad AABB, directly places blocks, discards **all non-player entities** in that box, and may proceed after a chunk warmup timeout. There is no baseline restore/hash/receipt/lease interface. [SimArena 159–169, 280–323, 487–505](https://github.com/genkimorimori252525-oss/KNEEKURA-LAB/blob/21959d439960d112d05c4c3ee44e54e353246d4e/bridge/tlm-forge/src/main/java/com/github/tartaricacid/touhoulittlemaid/sim/SimArena.java#L280-L323)

## Evidence and capture semantics to preserve

- Actual EvidenceBroker supports compact status, entityCurrent, changes, anomalies and gap explanations. Mixed snapshot/process/arena/resource identity fails closed. LATEST_PER_LANE is non-simultaneous; BOUNDED_SKEW constrains timestamps; SAME_TICK_WHERE_AVAILABLE only checks available gameTime values. Per-writer sequence is authoritative; wall time is not causal proof. [broker.mjs 17–137, 523–687](https://github.com/genkimorimori252525-oss/KNEEKURA-LAB/blob/21959d439960d112d05c4c3ee44e54e353246d4e/debug-workspace/evidence/broker.mjs#L17-L137)
- The implementation accepts an arbitrary coherenceMode string but only branches for SAME_TICK_WHERE_AVAILABLE and BOUNDED_SKEW. An `ATOMIC_SNAPSHOT` label is therefore not proof of atomicity. Add a supported-mode allowlist when exposing this through the bridge; do not treat evidence query cuts as capture barriers.
- Raw JSONL is append-only during a run and retained alongside canonical observations. Ingestor rejects wrong session/run/snapshot/process identity. Finalization seals official write paths. This is API/write-once discipline, not a tamper-proof filesystem. Import should verify exact artifact bytes against inventory hashes. [ingest.mjs 18–75](https://github.com/genkimorimori252525-oss/KNEEKURA-LAB/blob/21959d439960d112d05c4c3ee44e54e353246d4e/debug-workspace/evidence/ingest.mjs#L18-L75), [store.mjs 296–305](https://github.com/genkimorimori252525-oss/KNEEKURA-LAB/blob/21959d439960d112d05c4c3ee44e54e353246d4e/debug-workspace/evidence/store.mjs#L296-L305)
- Pre-roll manifests are write-once and refer to canonical IDs/prefix hashes plus ring limits/filter/coverage; finalization replays the prefix and filter to reject altered coverage/content. No automatic trigger/post-roll integration exists in primary debug runtime. [capture.mjs 48–148](https://github.com/genkimorimori252525-oss/KNEEKURA-LAB/blob/21959d439960d112d05c4c3ee44e54e353246d4e/debug-workspace/evidence/capture.mjs#L48-L148), [finalize.mjs 184–303](https://github.com/genkimorimori252525-oss/KNEEKURA-LAB/blob/21959d439960d112d05c4c3ee44e54e353246d4e/debug-workspace/evidence/finalize.mjs#L184-L303)
- EVIDENCE_COMPLETE is clean writer shutdown + no trailing partial raw row/drop/error/remaining queue. It is not behavior PASS. Partial capture count is separately reported and does not participate in the global complete predicate, so assertions requiring that capture window must independently reject incomplete coverage. [finalize.mjs 434–518](https://github.com/genkimorimori252525-oss/KNEEKURA-LAB/blob/21959d439960d112d05c4c3ee44e54e353246d4e/debug-workspace/evidence/finalize.mjs#L434-L518)

## Shutdown prerequisite qualification

Reuse the identity-bound request/ACK protocol and sealed bounded writer. [core.mjs 1460–1533](https://github.com/genkimorimori252525-oss/KNEEKURA-LAB/blob/21959d439960d112d05c4c3ee44e54e353246d4e/debug-workspace/core.mjs#L1460-L1533), [Java coordinator 34–125](https://github.com/genkimorimori252525-oss/KNEEKURA-LAB/blob/21959d439960d112d05c4c3ee44e54e353246d4e/debug-workspace/forge-bridge/src/main/java/com/github/tartaricacid/touhoulittlemaid/sim/debug/KneekuraDebugShutdownCoordinator.java#L34-L125).

However, stopProcessTree ignores Windows taskkill failure status and catches Unix signal errors; stopCurrent marks STOPPED/live:false immediately after termination attempts without re-reading the processes. This is insufficient to prove bridge cleanup completion. Add a bounded process-exit reattestation and honest CLEANUP_UNKNOWN/FAILED result while preserving PID ownership checks. [core.mjs 777–800 and 1592–1615](https://github.com/genkimorimori252525-oss/KNEEKURA-LAB/blob/21959d439960d112d05c4c3ee44e54e353246d4e/debug-workspace/core.mjs#L1592-L1615)

## Dual presentation and visual barrier owner work

LAB contains reusable **legacy research**, not the bridge visual contract. `SimGoldenFramebufferCapture` captures one main-render-target background/after-entity pair around actual rendering with exact camera/frame identity; it intentionally excludes GUI/particles/weather and is scoped to isolated YSM/final-vertex comparison. It has no primary debug RunSnapshot/Experiment binding or canonical four-view protocol. Some outputs use overwrite flags; do not inherit those as immutable bridge image semantics. [Golden capture 35–59, 203–280](https://github.com/genkimorimori252525-oss/KNEEKURA-LAB/blob/21959d439960d112d05c4c3ee44e54e353246d4e/bridge/tlm-forge/src/main/java/com/github/tartaricacid/touhoulittlemaid/sim/client/SimGoldenFramebufferCapture.java#L203-L280)

Minimal LAB-owned X3/X4 prerequisite:

1. Capability-declared, bounded explicit capture on one authoritative client.
2. An actual controlled-state barrier with run/experiment generation/evidence cut/Arena epoch/exact subject identities. Sequential render frames must not be labeled same-frame.
3. Non-perturbing camera where feasible; otherwise exact pre-capture human camera state, bounded takeover, restoration receipt and recorded perturbation. Affected behavior assertions remain inconclusive or use a separate experiment.
4. Four independently hashed raw scene views with camera transform/FOV/viewport/time intervals; optional human composite is a different artifact.
5. Derived contact sheet, stable UUID labels and exact schematic refer back to raw observation/image hashes. Human UI actions are classified as presentation-only, observation-affecting or typed mutations.
6. Shared source identities for human/AI presentation records; Findings remain separate from Observations. Visual-check ambiguity remains unresolved.

No new renderer authority, evidence database, autonomous runtime loop or four-client camera farm is needed. Automatic trigger/post-roll (X5) and optional same-frame multipass (X8) are not prerequisites for the first explicit snapshot capture.

## Recommended implementation sequence

1. TECH HUB: finish inert strict X0 request/result validation and existing-CAS X1 import, with imported/unattested provenance and stale-target detection. No runnable adapter registration yet.
2. LAB: add immutable `techHub` binding, runtime artifact/config/resource attestation and stronger verified shutdown. Freeze supported capabilities with exact protocol/implementation identity.
3. LAB: implement the smallest G3 Arena/action subset and fixture tests proving stale fences, bounds, reset, partial apply, idempotency and UNKNOWN.
4. LAB: implement explicit capture barrier and dual-presentation raw/derived contracts, reusing evidence infrastructure.
5. Only with separate runtime authorization and registered environment: prove G1/G2 on the actual workspace, then bounded X2/X3; finish the required visual benchmark and one real repair cycle before X7 completion.

The existing code is valuable infrastructure. The safe boundary is to reuse its implemented G1/G2 contracts while leaving X2–X7 readiness blocked until each LAB-owned prerequisite and real-runtime proof exists.
