# Bounded Arena/action source slice

This implements an owner-only Java controller and real Forge 1.20.1 backend. It is source-tested and selected real-API compiled; it is **not live X2 acceptance**. Public execution remains BLOCKED. No Minecraft launch, network listener, command CLI, inbox poll or enabling environment flag is added.

## Ownership and installation

The existing Supervisor/run snapshot owns the run. `KneekuraDebugArenaOwnerGrant` carries exact session/run/snapshot/process/nonce, experiment generation/request hash, Arena baseline/bounds/epoch/revision, exact non-player UUIDs, dimension, disposable debug-world name, lease and budgets. Node's source-owned `buildOwnerGrantIntent` creates linkage only. Java parses strict exact keys; booleans or fields claiming authorization/attestation are rejected.

`KneekuraDebugArenaRuntime.installOwner` requires the concrete current server thread, server/level object, Config identity and a trusted source-owned `OwnerGate`. The gate must independently establish live mutation authorization and actual loaded-runtime attestation; `UNCONFIGURED` rejects both. Request JSON cannot provide a gate implementation. Matching disk hashes do not establish JVM-loaded bytes. A consumed grant cannot be reinstalled in the same JVM; restart/recovery requires a fresh owner-verified process identity and authority.

Owner submission, reset, snapshot and capture reservation/validation are server-thread APIs. No other runtime supervisor is introduced. `uninstallOwner` and controller revocation detach and journal pending UNKNOWN without world mutation even after authority/lease expiry; a wrong server thread still rejects cleanup.

## Implemented actions and limits

- `wait_ticks`: 1..1200 exact subsequent server ticks, asynchronous, at most one pending action. Tick gaps, expired/revoked authority or missing proof become OUTCOME_UNKNOWN
- `set_block`: exact default minecraft:air/stone/glass/barrier states, UPDATE_CLIENTS only, measured readback. Other blocks, fluids and block entities reject
- `teleport_subject`: pre-registered canonical UUID/type only, same loaded level, alive non-player, no passengers/vehicles. Both current and destination entity bounding boxes must fit the half-open Arena
- `use_item`: BACKEND_UNAVAILABLE; no approximation of use-item gameplay semantics

Mutation volume is at most 64 cells per edge and 4096 total cells. No chunk loading, force tickets, dimension transfer, arbitrary commands, player movement or spawning. Lease duration is at most120000ms, requested action budget0..32, capture budget0..16. An empty action set grants no action capability, including capture-only requests. Current authority/time is checked before every real backend write; lease is checked after mutation and durable observation before issuing VERIFIED. VERIFIED is action-postcondition proof, never gameplay PASS.

One separate explicit owner cleanup reset is reserved per installed lease, in addition to the requested action budget, within the same existing authority/deadline. It cannot grant new experiment actions or be retried under another key. An unsafe Arena may receive that explicit scoped cleanup attempt but remains unsafe for experiment reuse. No automatic reset/replay is introduced.

## Scoped reset fidelity

Capture and reset only already loaded bounded cells and exact registered subjects. Reset restores captured block states and subject position/rotation/velocity, then measures the same scoped fingerprint. Epoch/revision advance only after matching measurement plus durable receipts. Unsupported/entered players/entities/blocks, escaped/missing subjects, partial writes, disk errors or mismatch block reuse.

Reset classes are blocks RESETTABLE; entities/effects/target_state UNKNOWN; block_entities/scheduled_ticks/game_rules/time_weather/chunk_tickets EXTERNAL; probe_state PERSISTENT_BY_DESIGN. Subject pose is a measured subset, not a claim to restore entity/AI state. Health, inventory, effects, AI/tasks, entity creation/removal, scheduled ticks, global/neighbor state and third-party callbacks are not rolled back. A scoped match remains overall INCONCLUSIVE, never whole-world CLEAN.

## Journal and evidence

Java shares Node `control/actions/<sha256(key)>` request, exclusive `.writer-lock`, immutable numbered receipt chain and transitions. `canonical-action.json` preserves the exact Node payload bytes/digest, including exponent/float serialization. Java does not recanonicalize a Node action to derive its identity. Acceptance is fsynced before mutation; postcondition evidence is persisted before APPLIED/VERIFIED receipts. Previously seen accepted/applied interruption states are UNKNOWN and never dispatched again. Incomplete/torn/corrupt chains fail closed.

The existing Evidence Writer owns Arena observations. Ordinary lanes retain asynchronous behavior and epoch0. Arena observations explicitly carry the current/proposed Arena epoch; the same worker flushes and forces the raw row before completing its exact row SHA. Server action callers wait at most1s; camera/render callers use `recordArenaObservedAsync`. A missing/drop/disk/timeout acknowledgement cannot prove success. This explicit checkpoint introduces bounded waiting and disk-I/O perturbation. It does not make the other observer lanes an atomic snapshot or erase their delta caches.

## Source verification

`npm run test:ci` includes Node foundation/source-contract tests. Real Java behavior and Node/Java journal/grant interoperability are separate:

    JAVA_HOME=/path/to/jdk17 KNEEKURA_GSON_JAR=/absolute/path/to/gson-2.10.x.jar npm run test:bridge-runtime

`KNEEKURA_JAVA` and `KNEEKURA_JAVAC` can override the JDK executables. The entrypoint compiles Java17 into a temporary directory, runs real file-journal/durability/controller/grant tests and legacy READY tests, then verifies Node-produced receipts and grants through Java. It never instantiates Minecraft.

Selected Forge backend/runtime compilation uses genuine official-mapped Minecraft/Forge1.20.1 dependencies, not MC-shaped stubs. Whole pinned reimu-mod compilation, loaded-runtime proof and authorized live acceptance are separate owner checks. Source-contract string assertions verify wiring only; they are not runtime behavior evidence. No live G3/X2 readiness is claimed from them.

Selected actual API/writer check: provide `JAVA_HOME` and `KNEEKURA_FORGE_CLASSPATH` with genuine mappedForge1.20.1/Gson/LogUtils/SLF4J/annotation dependencies, then run `npm run test:bridge-runtime-api`. The test deterministically claims the actual writer row and verifies shutdown cannot falsely report clean or acknowledge an interrupted stream.

Git source preflight now drains subprocess pipes through the close event and defaults to5s/4MiB, with explicit UNKNOWN/failure on timeout, pipe error or output-limit truncation. This fixes an observed false source-drift race without weakening immutable source checks.
