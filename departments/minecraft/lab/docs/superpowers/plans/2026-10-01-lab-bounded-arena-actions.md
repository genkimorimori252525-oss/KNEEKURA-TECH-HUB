# LAB Bounded Arena Typed Actions Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [x]`) syntax for tracking.

**Goal:** Implement a real LAB-owned server-thread Minecraft backend for a deliberately small resettable Arena/action subset, retaining an inert public transport until owner authorization and live gates exist.

**Architecture:** Extend the existing Debug Workspace server-tick hook and Evidence Writer. A small Java controller owns an Arena epoch/revision, a bounded lease, and exact subject UUIDs. The Java journal shares Node's existing `control/actions` receipt lifecycle and lock, accepts durably before invoking the real Forge adapter, and never replays previously seen actions. No second supervisor, scheduler, evidence database or live endpoint.

**Tech Stack:** Java 17, Forge/Minecraft 1.20.1 existing APIs, current Gson; Node ESM built-ins and node:test. Existing cloud JDK17 and cached mapped Forge JAR can compile selected sources without starting Minecraft. Full pinned reimu-mod compile remains parent-owned exact-head CI.

**Spec:** Approved TECH design at https://github.com/genkimorimori252525-oss/KNEEKURA-TECH-HUB/blob/c7542e829cd9d6db80c7eec3c96d702d28498533/docs/superpowers/specs/2026-10-01-minecraft-mod-ai-experimental-runtime-bridge-design.md; LAB foundation `docs/superpowers/plans/2026-10-01-tech-hub-bridge-foundation.md`; TECH `experiment_contract.py` actual action schemas.

## Global Constraints

- Source only, in the new cloud `lab-arena-work` copy; controller established exact published baseline `c515d67b7005d15fec60f4ec1af2e961d21c0a68` before publication
- no new Evidence database; no caller-supplied executable path; no raw Minecraft commands
- no automatic retry after uncertain mutation; no production world
- no interpretation of action completion as gameplay PASS
- no Minecraft launch, runtime dispatch, user's computer, runner/settings/credential mutation, or publication
- Matching disk hashes are material linkage, never proof of JVM loaded bytes
- No external transport, CLI, inbox polling or config flag enabling typed actions; legacy runs remain unaffected. An explicit source-owner install/uninstall seam now requires a trusted gate and strict grant
- Preserve the immutable RunSnapshot and existing Node supervisor as sole run authority

## First supported scope and constraints

The Arena mutation volume is integer half-open, at most 64 blocks per edge and at most 4096 cells in this first backend. Capture/inspect only already loaded chunks. Supports `wait_ticks` (1..1200, asynchronous progression by server tick), `set_block` only exact default states of minecraft:air/stone/glass/barrier using UPDATE_CLIENTS only, and `teleport_subject` only pre-registered canonical UUIDs of non-player entities already in the same Arena and dimension. Subject bounding boxes must remain in bounds; teleport is an explicit perturbation. No spawn, arbitrary entity NBT, player movement, dimension transfer, effects, inventory, block entities, ticks, chunk force-loading or item-use semantics. `use_item` is rejected as BACKEND_UNAVAILABLE before acceptance/mutation.

Reset restores only the captured block palette and registered subject pose (position/rotation/velocity); it measures and hashes the same scoped state after restoration. It never rewinds world time, scheduled ticks, AI, health, effects, entity creation/removal, Forge callbacks, neighboring/global state or chunk tickets. Declare blocks RESETTABLE; block_entities EXTERNAL (must be absent); entities/effects/target_state/scheduled_ticks/game_rules/time_weather/chunk_tickets EXTERNAL or UNKNOWN as applicable; probe_state PERSISTENT_BY_DESIGN. A matching supported-scope baseline is SCOPED_BASELINE_MATCH and overall INCONCLUSIVE, never full-world CLEAN. Reject reset if captured subjects disappeared/escaped or unsupported blocks/entities entered rather than guessing rollback.

A controller needs exact Config session/run/snapshot/process/nonce + experiment, Arena ID/epoch/revision + lease ID/expiration/action count, fixed subject map, fixed dimension and debug disposable world identity. Lease check uses injected monotonic owner clock plus maximum duration 120000ms and maximum 32 actions, rechecked on every tick/mutation. Only the source-owned seam can construct the backend/controller; the production tick hook remains unconfigured/BLOCKED; an explicit source-owner installation seam requires independently verified live authority and loaded-runtime proof. Future authorization/attestation/ingress must be separately implemented before real use.

## Review Focus

- Crash after ACCEPTED or APPLIED, concurrent same-key submission, stale writer lock: UNKNOWN/no re-execution
- Wrong session/run/snapshot/nonce/process epoch or Arena lease/epoch/revision: reject before world mutation
- Half-open edge/bounding-box escape, unloaded chunks, players, unexpected block entities/palette: reject before mutation/reset
- Lease expiry/revocation while a wait is pending: unknown or NOT_RUN as appropriate, never a late mutation or fabricated elapsed ticks
- Evidence queue drops, disk receipt errors, reset mismatch: controller becomes unsafe/blocked and reports incomplete proof

## Files and interfaces

- NEW Java `KneekuraDebugArenaController.java`: pure typed records Identity, Bounds, Lease, Arena, Command and Backend; `submit(Command, long tick)`, `onTick(long tick)`, `reset(long tick)`; one pending wait at most, monotonic revision, fail-closed lease and dirty/unknown state
- NEW Java `KneekuraDebugActionJournal.java`: share Node journal directory/request/receipt format and writer lock; `accept(Command)`, `append(status, evidenceHashes)`, duplicate lookup; fsync exclusive receipts; read-back integrity
- NEW Java `KneekuraDebugForgeArenaBackend.java`: actual ServerLevel/Entity typed mutations and measured baseline/reset; assert MinecraftServer#isSameThread before every operation; no generic callback or command executor
- NEW Java `KneekuraDebugArenaRuntime.java`: default BLOCKED tick hook and trusted owner install/uninstall/capture-budget seam; no public installation, file polling, endpoint or CLI
- MODIFY Java `KneekuraDebugClientBootstrap.java`: call inert runtime tick before observations
- MODIFY Java `KneekuraDebugEvidenceWriter.java`: explicit Arena-epoch observation overload through existing writer; existing callers remain epoch 0; action/reset observations are OBSERVED only when measured, incomplete drops never receipts proving success
- MODIFY Node `debug-workspace/bridge/action-journal.mjs`: write canonical-action.json exact bytes (existing payloadHash) alongside request marker so Java need not invent JavaScript number serialization; retain same journal/lock/lifecycle
- NEW Java self-tests controller/journal/adapter API compile and NEW Node `tests/runtime-source.test.mjs`; NEW `debug-workspace/bridge/runtime-selftest.mjs` compile/run Java pure contract tests using explicit JDK/Gson paths
- MODIFY package scripts and README for executable source tests and truthful readiness/reset boundary; no workflow/settings edits in this slice

## Task 1: Shared durable Java journal

- [x] Add Node test: canonical-action.json SHA equals request payloadHash and parsed action; identity unchanged, old journal remains readable
- [x] Run node --test debug-workspace/bridge/tests/arena-journal.test.mjs and record missing-file RED
- [x] Implement sidecar write and rerun GREEN
- [x] Add Java self-test: shared REQUESTED -> ACCEPTED -> APPLIED -> VERIFIED readable by Node; existing acceptance returns UNKNOWN without replay, conflicting digest rejects, corrupt/missing/torn chain rejects, writer lock conflict fails closed
- [x] Compile/run Java self-test to record missing-class RED, implement bounded strict JSON receipt reader/writer and rerun GREEN; fixture has no runtime mutation

## Task 2: Controller bounds/lease/typed execution

- [x] Add pure Java tests against a deterministic in-memory Backend: stale identity/nonce/epoch/revision/lease, budget exhausted, out-of-bounds, nonfinite positions, unsupported use_item, concurrent pending wait, tick discontinuity/interruption and evidence/receipt failure
- [x] Record RED with compilation/test failures for missing controller, then implement exact typed records and state machine
- [x] Assert durable ACCEPTED precedes backend invocation, postcondition precedes VERIFIED, same key never invokes backend twice; expiry stops pending wait
- [x] Assert reset increments epoch/revision only after scoped baseline measurement matches, stale old-epoch commands reject, reset failure blocks controller and cannot declare full-world clean
- [x] Rerun pure Java + Node journal tests GREEN

## Task 3: Real Forge backend and evidence/tick seam

- [x] Add API/source tests pinning actual server thread guard, setBlock/getBlockState, UUID resolution, teleportTo/pose readback, bounded loaded-cell reset, palette and player/block-entity rejection, default disabled runtime
- [x] Record RED, implement adapter against actual cached official mapped Forge 1.20.1 classes (no MC-shaped stubs)
- [x] Add writer overload routing current arenaEpoch explicitly, default epoch 0 untouched; evidence rows remain in existing raw writer
- [x] Wire default inert server-tick runtime; no endpoint/activation switch; test no transport/CLI additions and readiness remains BLOCKED
- [x] Compile the actual adapter and controller against real cached mapped Forge/Gson dependencies; if compile needs the full pinned mod workspace report exact gap rather than claim it passed

## Task 4: Verification, documentation, exact changed-file handoff

- [x] Run `node --test debug-workspace/bridge/tests/*.test.mjs` and Java source self-tests; run `npm run test:ci`, then full `npm test` and disclose any existing browser-only failure
- [x] Verify final actual Forge adapter compilation and save commands/logs/source hashes; do not conflate it with whole-mod compile or live acceptance
- [x] Document supported-scoped reset classes, unsupported states/actions, default BLOCKED transport, disk-vs-loaded artifact boundary, and owner prerequisite for next source slice
- [ ] Parent integration gate: independent source review is completed; exact-head publication and whole pinned Forge compilation remain parent-owned, with live verification deferred. No local synthetic commits or upstream-history claims

## Self-review

This completes a real owner backend slice, not X2 live acceptance. The controller, durable journal, Minecraft adapter and epoch-aware writer have executable source tests and real-API compilation. Public execution remains unavailable because loaded-runtime attestation, operator live authorization, disposable-world provisioning and transport authenticity have not yet been established. Block/entity state scope is explicit and does not assert whole-world rollback. No camera/visual or X3–X7 work is hidden in this plan.

## Final execution record

- Source baseline is the verified genuine c515d67b7005d15fec60f4ec1af2e961d21c0a68/tree cd3b414085675317e4ede5746a1e5af6db3ab8ab
- Parent technical review findings fixed by failing→passing tests: separate single cleanup reset allowance; expiry checks after apply/evidence; revoked/expired owner teardown; strict numeric journal fields and bounded race-resistant reads; atomic evidence dequeue/output claim
- Additional source-owned files: OwnerGrant, Durability, actual writer claim test, runtime-api-selftest; Node owner-grant builder copied from parent reviewed transport slice and validated through Java
- Existing Git preflight output race reproduced with unchanged real Git state; extracted process-output waits for close, defaults5s/4MiB and fails closed on timeout/output limit/retained descendant pipe; six tests green
- Java source tests and selected genuine Forge API/writer compilation pass; whole pinned mod compilation and live acceptance remain separate parent gates
- npm run test:ci passes; full npm test was run and stops at the existing Chrome/Edge-dependent palette-live-selftest because neither browser executable is installed here
- No source commit/publication, Minecraft launch or owner installation performed by this worker
