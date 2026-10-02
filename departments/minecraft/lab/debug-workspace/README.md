> **CURRENT STATUS OVERRIDE (2026-10-02):** This README preserves the original G1/G2 milestone narrative. It is not the current implementation checklist. Arena/action control, owner lifetime/control, Cardinal capture/restoration, finalized evidence/export and Tank presentation are now implemented in this subtree. Read [`../../CURRENT-HANDOFF-2026-10-02.md`](../../CURRENT-HANDOFF-2026-10-02.md) first; sections below labeled “Not implemented yet” or “under implementation” are historical checkpoint text.\n\n# KNEEKURA Debug Workspace

This directory contains the G1 Debug Supervisor / Orchestrator.

It is intentionally independent from the old Web Viewer server.

## Current scope

Implemented:

- external Minecraft development workspace registration;
- dedicated runtime root;
- debugSessionId / runId / processEpoch;
- per-run handshake nonce;
- process launch and process-log capture;
- T0-T8 timeline recording;
- explicit Probe READY manifest validation;
- runtime attestation capture;
- current-state file;
- process-tree stop;
- fake-target self-test;
- real Forge/KNEEKURA G1 READY bootstrap;
- exact Debug World identity gate;
- source Git identity binding;
- one-command G1 smoke acceptance;
- persisted G1 acceptance manifest;
- immutable per-run RunSnapshot with startup source/observer drift fencing;
- exact UUID target control;
- G2 L0 client/server heartbeat lanes;
- G2 exact-target tracking and thresholded client ENTITY_STATE delta lane;
- server-authoritative exact-UUID lookup without world/entity full scan;
- server L1 lanes for SERVER_ENTITY_STATE / AI_TARGET / BRAIN_MEMORY / NAVIGATION / TLM_STATE / REIMU_STATE;
- bounded asynchronous Forge evidence writer with visible sequence-gap loss;
- incremental raw JSONL ingestion with persisted byte cursors;
- Evidence Broker compact status / exact-entity query / gap explanation;
- lane stale detection, rates, queue pressure and drop/error summaries;
- non-causal L2 watchpoints;
- Observation / Finding separation with snapshot provenance;
- run-bound Probe evidence shutdown request/ACK before process termination;
- immutable evidence finalization manifest with COMPLETE/PARTIAL truth.

Not implemented yet:

- Arena reset/action API and mutation fencing;
- deep TLM/AI/navigation lanes;
- network/Molang/YSM/render causal lanes;
- L3 snapshot and L4 burst/ring-buffer capture;
- G5 same-session restart orchestration.

## Local setup

On Windows, the preferred setup path is:

    npm run debug:setup

or double-click:

    debug-workspace/setup-local.cmd

The setup script:

1. finds a local `reimu-mod` checkout from common locations or `REIMU_MOD_WORKSPACE`;
2. verifies the checkout contains the current G1 Gradle integration markers;
3. writes `debug-workspace/config.local.json`;
4. verifies the dedicated Debug World exists;
5. runs `debug:doctor`.

To provide the workspace explicitly:

    powershell -NoProfile -ExecutionPolicy Bypass -File debug-workspace\setup-local.ps1 -ReimuWorkspace "C:\path\to\reimu-mod"

To setup and run the full G1 acceptance immediately:

    powershell -NoProfile -ExecutionPolicy Bypass -File debug-workspace\setup-local.ps1 -Smoke

Manual configuration is still supported by copying:

    debug-workspace/profiles/reimu-mod.example.json

to:

    debug-workspace/config.local.json

and setting the real Minecraft Mod development workspace plus the verification world name.

Do not point this at a normal personal Minecraft installation.

`worldName` identifies the singleplayer verification world used by the registered workspace.
The Supervisor also injects the canonical LAB Forge bridge source directory through
`KNEEKURA_DEBUG_FORGE_BRIDGE_SRC`; the executable workspace may include that source
only while debug mode is enabled.

The launch command is deliberately configurable because KNEEKURA-LAB no longer owns one canonical Forge Gradle wiring. The registered workspace is the executable real-Minecraft source tree.

For the current `reimu-mod` adapter, use `debug-workspace/profiles/reimu-mod.example.json`.
It points at the existing Forge `run/client_a` development game directory and requires
`saves/<worldName>` to exist before launch. Missing world is reported by `debug:doctor`
instead of waiting for a READY timeout.

## Commands

    npm run debug:setup
    npm run debug:doctor
    npm run debug:start
    npm run debug:status
    npm run debug:timeline
    npm run debug:smoke
    npm run debug:g2-smoke -- <entity-uuid> [--require-reimu]
    npm run debug:stop
    npm run test:debug-workspace

A custom config path can be passed directly:

    node debug-workspace/cli.mjs doctor --config path/to/config.json

or through:

    KNEEKURA_DEBUG_CONFIG=path/to/config.json

## Environment passed to the debug target

The Supervisor passes:

- KNEEKURA_DEBUG_ENABLED=1
- KNEEKURA_DEBUG_SESSION_ID
- KNEEKURA_DEBUG_RUN_ID
- KNEEKURA_DEBUG_PROCESS_EPOCH
- KNEEKURA_DEBUG_RUN_SNAPSHOT_ID
- KNEEKURA_DEBUG_HANDSHAKE_NONCE
- KNEEKURA_DEBUG_READY_FILE
- KNEEKURA_DEBUG_BUILD_MARKER
- KNEEKURA_DEBUG_RUN_DIR
- KNEEKURA_DEBUG_RUNTIME_ROOT
- KNEEKURA_DEBUG_EVIDENCE_RAW_DIR
- KNEEKURA_DEBUG_TARGET_FILE
- KNEEKURA_DEBUG_SHUTDOWN_REQUEST_FILE
- KNEEKURA_DEBUG_SHUTDOWN_ACK_FILE
- KNEEKURA_DEBUG_FORGE_BRIDGE_SRC
- KNEEKURA_DEBUG_WORLD_NAME

The real Forge Probe should consume these values and write the READY manifest.

## READY contract

The Probe writes JSON to KNEEKURA_DEBUG_READY_FILE.

Minimum shape:

    {
      "protocolVersion": "KNEEKURA_DEBUG_READY_V1",
      "debugSessionId": "...",
      "runId": "...",
      "runSnapshotId": "...",
      "worldName": "KNEEKURA_DEBUG_WORLD",
      "processEpoch": 1,
      "handshakeNonce": "...",
      "status": "DEBUG_READY",
      "pid": 12345,
      "gates": {
        "probeHandshake": true,
        "debugWorldReady": true,
        "runtimeAttested": true
      },
      "milestones": {
        "jvmStartedAt": "...",
        "forgeInitializedAt": "...",
        "clientWorldAvailableAt": "...",
        "playerJoinedAt": "...",
        "probeReadyAt": "...",
        "debugWorldReadyAt": "..."
      },
      "runtime": {
        "minecraft": "1.20.1",
        "forge": "...",
        "java": "...",
        "probeBuild": "sha256:...",
        "processCommandHint": "java",
        "loadedMods": []
      }
    }

The Supervisor refuses READY if session/run/world/processEpoch/nonce do not match.

At G1, `debugWorldReady` means the expected singleplayer debug world is joined and stable.
It does **not** claim that the future G3 Arena baseline is clean or verified.

This prevents an old run's marker from making a newer process appear healthy.

## Runtime layout

    debug-runtime/
      current.json
      sessions/
        sess-.../
          session.json
          runs/
            run-.../
              run.json
              run-snapshot.json
              timeline.jsonl
              process.log
              ready.json
              control/
                target.json
                shutdown-request.json
                shutdown-ack.json
              evidence/
                raw/
                observations.jsonl
                findings.jsonl
                lane-health.jsonl
                ingest-state.json
                finalization.json

debug-runtime is local state and should not be committed.

## Important old-water-tank lesson

The old SimLab ran directly from mutable build/classes output. Running Gradle while Minecraft stayed alive could delete/rewrite classes that had not yet been loaded, causing later NoClassDefFoundError crashes.

The new Supervisor therefore does not treat "compile into the live classpath while Minecraft stays running" as Fast Restart.

G5 must use a safe build/runtime handoff or full process restart.

## Current completion boundary

The G1 supervisor path is implemented, and the G2 evidence foundation is now under implementation.

A real local-machine smoke acceptance against the actual Forge development workspace remains the required machine proof for G1:

    npm run debug:smoke

A successful smoke writes:

    <runDir>/g1-acceptance.json

The acceptance manifest binds the result to:

- the `reimu-mod` Git commit / dirty-state identity;
- the KNEEKURA-LAB Git identity;
- runtime attestation;
- the complete T0-T8 timeline;
- live process re-attestation;
- safe-stop result.

G2 infrastructure code may be developed in parallel, but G2 must not be declared accepted until the real-machine G1 acceptance passes and the G2 lanes are verified on the actual Forge runtime.

## Forge workspace integration rule

The executable Forge workspace remains the owner of Minecraft/Forge Gradle wiring.
KNEEKURA-LAB remains the owner of debug instrumentation.

A supported Forge workspace should conditionally add
`KNEEKURA_DEBUG_FORGE_BRIDGE_SRC` to its main Java sources only when
`KNEEKURA_DEBUG_ENABLED=1`.

Normal builds must not compile or package the LAB debug bridge.

This avoids copying Probe code between repositories while preserving the trusted boundary:
the LAB bridge is the single source of truth, and the target Mod remains usable without it.


## Runtime state reconciliation

`debug:status` does not blindly trust `current.json`.

It re-checks both:

- the Gradle/launcher process; and
- the actual runtime PID reported by the Minecraft Probe.

PID ownership is fenced by PID + process start time + command hint. The resulting state can become:

- `DEBUG_READY` with `live=true`
- `STALE_NOT_RUNNING`
- `OWNERSHIP_LOST`
- `STOP_REFUSED_UNVERIFIED`

`debug:stop` only kills processes whose ownership can be re-proven.

## Startup timing

`npm run debug:timeline` reads the current run's T0-T8 evidence and reports:

- each milestone timestamp;
- time from the previous milestone;
- time from T0;
- total startup time.

Current G1 milestones are:

- T0 restart requested
- T1 build complete
- T2 Minecraft JVM started
- T3 Forge client setup completed
- T4 client world available
- T5 player joined
- T6 Probe ready
- T7 exact Debug World ready
- T8 DEBUG_READY accepted by Supervisor

These names describe the evidence actually observed; T4 does not claim to see the internal beginning of world loading.


## Workspace compatibility preflight

The reimu-mod profile includes `workspaceChecks`.

`debug:doctor` verifies that the selected local checkout has:

- `gradlew.bat`;
- `KNEEKURA_DEBUG_FORGE_BRIDGE_SRC` integration;
- the dedicated `kneekuraDebugSourceSet`;
- Quick Play wiring;
- the run-bound build-complete marker.

A stale checkout is rejected before Minecraft launch.

## G1 acceptance evidence

A passing `debug:smoke` creates `g1-acceptance.json` in the run directory.

This is the canonical G1 completion artifact for that run. It records source identity, runtime identity, total startup time, timeline completeness, runtime liveness before stop, and safe-stop evidence.

## G2 evidence commands

    npm run debug:target -- <entity-uuid>
    npm run debug:target:status
    npm run debug:target:clear
    npm run debug:evidence:status
    npm run debug:evidence:entity -- <entity-uuid>
    npm run debug:evidence:anomalies
    npm run debug:evidence:gap -- <lane>
    npm run debug:evidence:capture -- --pre-roll-ms 5000 --entity <uuid> --lanes BEHAVIOR_TRANSITION,NAVIGATION
    npm run debug:evidence:finalize
    npm run test:g2-evidence

The exact target contract never auto-selects the "first Reimu". The target UUID is explicit,
run-bound, process-epoch-bound, revisioned, and stored under the active run directory.

debug:evidence:status is intentionally compact. It reports runtime liveness, per-lane
health/age/rate, worst lane, producer queue pressure and evidence loss without dumping raw
payloads first. Drill down only when needed.

debug:evidence:entity returns the latest observation per requested lane from one run snapshot.
Because L1 lanes are delta/keyframe streams rather than simultaneous samples, the default
coherence mode is LATEST_PER_LANE and every lane includes freshness metadata. Use an explicit
BOUNDED_SKEW cut only when the question actually requires near-simultaneous evidence.

Every real Forge raw observation carries runSnapshotId. The Evidence Runtime rejects rows
whose snapshot identity does not match the active run. Findings remain separate from
Observations and inherit the same snapshot provenance.

## RunSnapshot

A successful DEBUG_READY run creates exactly one immutable-by-contract:

    <runDir>/run-snapshot.json

The Supervisor allocates runSnapshotId before launch and passes it into Minecraft.
The Probe echoes it in READY and raw Evidence. At DEBUG_READY the Supervisor re-inspects both
the target source workspace and KNEEKURA-LAB observer workspace. If either fingerprint changed
during startup, startup fails closed with SOURCE_CHANGED_DURING_START or
OBSERVER_CHANGED_DURING_START.

The snapshot binds source Git identity, observer identity, build marker, runtime process
attestation, loaded runtime information, debug profile, world identity and observation schema
identity. g1-acceptance.json records the snapshot ID and hash as part of its proof.

## Evidence shutdown and finalization

`debug:stop` no longer kills an owned Minecraft runtime immediately.
It first writes a run-bound shutdown request. The Forge Probe validates
debugSessionId/runId/runSnapshotId/processEpoch, seals the evidence writer,
drains its bounded queue, flushes/closes the raw JSONL, and writes a shutdown ACK.
Only then does the Supervisor terminate the owned process tree.

Finalization is immutable and fail-visible:

- `EVIDENCE_COMPLETE`: clean Probe flush ACK, zero remaining queue, zero known drops/errors, no trailing partial JSONL.
- `EVIDENCE_PARTIAL`: any missing ACK, drop, writer/store error, or incomplete raw row.

A clean flush is necessary but not sufficient for complete evidence. For example,
a run that dropped one row earlier remains `EVIDENCE_PARTIAL` even if shutdown itself is clean.


Finalization is also the write barrier for that run. Once
`evidence/finalization.json` exists, official EvidenceStore/Runtime write paths reject new
Observations, Findings, lane-health flushes, and pre-roll captures with
`EVIDENCE_FINALIZED_READ_ONLY`. Evidence queries may reopen the run in read-only mode, but
incremental raw ingestion is disabled. This prevents artifacts created after sealing from
appearing beside the finalized bundle without being covered by its hashes.

## Client/server authority split

The exact target is selected once by UUID and the same run-bound control file is consumed
by both client and integrated-server observers.

Client lanes answer what the real client currently has and renders:

- TARGET_TRACKED
- ENTITY_STATE

Server lanes answer runtime/AI authority directly from the integrated server:

- SERVER_TARGET_TRACKED
- SERVER_ENTITY_STATE
- AI_TARGET
- BRAIN_MEMORY
- RUNNING_BEHAVIORS
- BEHAVIOR_TRANSITION
- NAVIGATION
- TLM_STATE
- REIMU_STATE

The server observer resolves the selected UUID through ServerLevel#getEntity(UUID) across
loaded dimensions. It does not scan every entity. Current L1 server lanes sample every five
server ticks and emit only on change or a 100-tick keyframe.

REIMU_STATE currently uses public reimu-mod/TLM accessors only. It does not use reflection
or infer private AI intent. Published phase/mode/cooldown state is OBSERVED; causal
explanations still belong in Findings.

`BRAIN_MEMORY` exposes only registered/public Brain memories that are already part of the
TLM/vanilla AI contract: ATTACK_TARGET, WALK_TARGET, LOOK_TARGET, PATH,
CANT_REACH_WALK_TARGET_SINCE, ATTACK_COOLING_DOWN, and TLM TARGET_POS.
It records presence/identity/coordinates/path progress and does not infer why a Behavior
selected those memories.

`RUNNING_BEHAVIORS` records the ordered list returned by
`Brain#getRunningBehaviors()`. Behavior instances receive collision-free reference tokens
that are valid only inside the current JVM process and target revision. Duplicate class names
are preserved rather than deduplicated.

`BEHAVIOR_TRANSITION` is an L2 sampled transition lane derived only from consecutive
`getRunningBehaviors()` samples. The first sample establishes a baseline and emits no
synthetic START events. Later rows report instance tokens added/removed between samples,
with `exactTransitionTickKnown=false` and `reasonKnown=false`; they do not claim the exact
start/stop tick or infer why the Brain changed state.

## Bounded pre-roll capture

`debug:evidence:capture` persists a run-bound immutable capture manifest under:

    <runDir>/evidence/captures/<captureId>.json

The manifest references canonical Observation IDs instead of duplicating raw evidence. It
records the requested pre-roll window, the actually available ring-buffer window,
dropped/late-start coverage facts, lane counts, writer sequence ranges, and whether the
buffer could cover the requested time window. A full buffer window does not claim that an
event-style lane must contain rows; zero matching rows can be a valid observation result.

Capture manifests explicitly separate `bufferWindowCompleteness` from
`selectedEvidencePresence`; they never claim continuous evidence merely because a filter
matched some rows.

A partial pre-roll capture does not by itself make the whole run `EVIDENCE_PARTIAL`.
Run completeness still describes canonical evidence loss/finalization. Capture completeness
describes whether that particular requested historical window was fully available.

Finalization does not trust the capture manifest blindly. At capture time the manifest stores
the canonical observation-prefix count, terminal Observation ID, SHA-256 of both the ID list
and stable canonical row contents, plus the ring-buffer limits. During finalization that exact
canonical prefix is reconstructed, the ring buffer is replayed, and the requested filter/window
is recomputed. Observation IDs, coverage fields, lane counts, writer sequence ranges, and
capture semantics must match exactly or finalization fails closed. Capture manifests are also
included in the final artifact hash list.

This is G2 bounded evidence retention. Automatic anomaly-triggered L4 burst capture,
post-roll recording, and subsystem escalation remain G4 responsibilities.

## Server-authoritative target lanes

The exact target UUID is observed independently on both client and integrated-server sides.

Client-side lanes:

- `TARGET_TRACKED`
- `ENTITY_STATE`

Server-authoritative lanes:

- `SERVER_TARGET_TRACKED`
- `SERVER_ENTITY_STATE`
- `AI_TARGET`
- `BRAIN_MEMORY`
- `RUNNING_BEHAVIORS`
- `BEHAVIOR_TRANSITION`
- `NAVIGATION`
- `TLM_STATE`
- `REIMU_STATE`

The server observer never scans all entities. It resolves the selected UUID with
`ServerLevel#getEntity(UUID)` across loaded dimensions, samples at a bounded cadence,
and emits only changes plus periodic keyframes.

`AI_TARGET`, `BRAIN_MEMORY`, `RUNNING_BEHAVIORS`, `BEHAVIOR_TRANSITION`,
`NAVIGATION`, `TLM_STATE`, and `REIMU_STATE` are direct or explicitly sampled-delta
observations from the integrated-server runtime. The Broker must not infer them from client movement or rendering.

`debug:evidence:entity -- <uuid>` includes both client and server lanes so cross-side
disagreement is visible instead of silently reconciled.

## G2 real-machine acceptance

G2 is accepted only by a real Minecraft debug run. The one-command gate is:

    npm run debug:g2-smoke -- <entity-uuid>

For the current Reimu-focused acceptance, use:

    npm run debug:g2-smoke -- <entity-uuid> --require-reimu

The command performs:

1. `debug:doctor` preflight;
2. real Forge/Minecraft launch through the G1 Supervisor;
3. DEBUG_READY and T0-T8 validation;
4. exact UUID target control bound to the active RunSnapshot;
5. wait for fresh, complete, OBSERVED client/server authority lanes;
6. bounded 1-second pre-roll capture from canonical evidence;
7. Probe clean evidence shutdown ACK;
8. safe process stop and immutable evidence finalization;
9. `g1-acceptance.json` plus `g2-acceptance.json`.

Required G2 authority lanes are:

- L0 CLIENT health: `CLIENT_TICK`
- L0 SERVER health: `SERVER_TICK`
- L1 CLIENT target state: `TARGET_TRACKED`, `ENTITY_STATE`
- L1 SERVER target state: `SERVER_TARGET_TRACKED`, `SERVER_ENTITY_STATE`, `AI_TARGET`,
  `BRAIN_MEMORY`, `RUNNING_BEHAVIORS`, `NAVIGATION`, `TLM_STATE`
- optional strict Reimu gate: `REIMU_STATE`

`BEHAVIOR_TRANSITION` is not mandatory for acceptance because a correct runtime may
remain behaviorally stable during the smoke window. Its producer/contract remains
covered by CI and it is included in the pre-roll filter when present.

The gate fails closed on wrong L0/L1 level, wrong client/server source authority, stale rows,
incomplete observations, snapshot/process identity mismatch, lane drop/error evidence, truncated
pre-roll, unclean shutdown, or non-COMPLETE finalization.

## TECH HUB bridge source foundation (runtime unavailable)

`debug-workspace/bridge/` contains internal Node APIs for exact-byte request registration,
registered material-file integrity, detached Arena/action/reset validation and a durable
unknown-safe action receipt journal. These APIs do not execute Minecraft actions.

- `registerBridgeRequest` receives trusted root-relative input paths separately from the
  experiment. It validates exact request/binding/assertions byte hashes and disk files
  (build ≤64 MiB, config ≤1 MiB, resource bundle ≤16 MiB)
- `loadBridgeRegistration` is read-only and rejects absent, incomplete, altered or conflicting
  registrations. A registry is local run/control metadata, not an Evidence database
- An internal `launchDebugRun` bridgeRequestHash option rechecks a previously registered input,
  clean exact source revision and disk material identity before launch/READY. The initial
  immutable snapshot includes techHub binding and explicitly disk-only bridge metadata
- Disk hashes do not prove JVM-loaded artifact identity. All bridge runtime attestation remains
  NOT_ESTABLISHED, and execution/Arena/capture readiness remains BLOCKED
- Action envelopes validate the declared identity, revision, typed args and half-open bounds.
  The journal never dispatches a mutation. Reported receipts remain CONTRACT_ONLY;
  accepted/applied unfinished receipts return OUTCOME_UNKNOWN, never-seen keys remain distinct
- Source-owned Java Arena lease, scoped reset and typed backends now have a separate
  bounded source slice; loaded-artifact attestation and live acceptance remain unestablished
- Stop now requires bounded process-exit verification after the existing flush/termination
  protocol. Inspection error, PID ownership change or timeout cannot be reported as safe stop
- Evidence Cut accepts only implemented non-atomic modes; ATOMIC_SNAPSHOT is not a supported
  capture barrier

Run the source tests with `npm run test:bridge-foundation`. The same suite is included in
`npm test` and `npm run test:ci`. Fake-target Supervisor tests do not establish real-Minecraft
acceptance. No new execution CLI or network service is introduced.

## Bounded Java Arena/action source

The real Forge backend and strict owner-only install/uninstall seam are documented in
[bounded Arena source slice](../docs/KNEEKURA_BOUNDED_ARENA_SOURCE_SLICE.md).
Public execution remains BLOCKED without independently verified live authority and loaded-runtime
attestation. The reset restores bounded blocks/subject pose only and remains overall INCONCLUSIVE.

Run Java17/Gson source behavior and cross-language tests with `npm run test:bridge-runtime`;
provide `JAVA_HOME` and an absolute `KNEEKURA_GSON_JAR`. Selected real-API compilation and full
pinned mod/live checks are distinct. No game process is launched by this source suite.


## Explicit scoped owner connection (source capability)

The Probe's existing server tick can install bounded diagnostic control only from the paired
`KNEEKURA_DEBUG_OWNER_ENVELOPE_FILE` / `KNEEKURA_DEBUG_OWNER_ENVELOPE_SHA256` private Supervisor
configuration. Unconfigured launches remain inert. The envelope closes over the exact sealed
ExperimentRequest, immutable grant/material/world registration and canonical initial RunSnapshot
body; the native parser requires its actual JVM PID and private integrated-server topology.

The source owner observes an already instantiated Forge mod object, fixed loaded anchors and the
operator-registered canonical disposable world. Explicit direct-JAR linkage and observed
class-resource/container linkage are separate supported tiers. Opaque config/resources are only
verified on disk; transformed class definitions and full target attestation stay unestablished.
This capability does not authorize gameplay/visual PASS.

Fixed action markers select retained actions in order with one deterministic identity/key; the
existing journal durably accepts before world mutation. Independent declared capture slots are
finite and consumed once. Capture completion must prove restored API presentation and an actually
released, unexpired barrier before another action; unknown restoration permanently fences the owner.
Explicit cleanup uses the existing separate one-reset allowance, never automatic retry or whole-world
rollback. Shutdown waits for the existing owner-thread detach before evidence sealing.

Installation keeps private native material/world details. Exportable action rows retain exact
installation/envelope/material/world hash references and incomplete certainty fields without paths.
All files, scans, queues, image slots, regions, actions and leases have fixed bounds.

See `docs/superpowers/plans/2026-10-01-owner-runtime-connection.md` for source ownership, schemas,
verification scope and remaining deferred live acceptance. Portable JVM and genuine selected API
checks do not instantiate Minecraft; full pinned-mod compilation is a separate verification step.

## Selected event capture (X5 source capability)

The scoped owner can now bind the single implemented `ARENA_EXIT` source to bounded
cardinal capture windows. This supplements the historical G2 retention status above;
it does not enable generic anomaly bursts or continuous image recording. Native source
observes the declared subject's point moving from inside to outside the half-open Arena
bounds. First-seen outside, missing/unloaded subjects, and log text are not exit evidence.

Preparation is explicit: the private operator registration accepted by
`prepareOwnerControl` may include `triggerCapture`, for example:

```json
{
  "enabled": true,
  "triggerKinds": ["ARENA_EXIT"],
  "offsetsMs": [-1000, 0, 1000],
  "toleranceMs": 200,
  "cooldownMs": 1000,
  "maxWindows": 1,
  "captureBudget": 2,
  "timeoutMs": 3000,
  "captureIndices": [1, 2]
}
```

This example requires the request's cardinal rig, operator camera/pause permission,
at least 12 image slots, and at least 3000 ms in the sealed owner lease. The selected
capture indices reserve native four-image slots for triggers; index 0 remains available
for explicit capture. A config cannot add image budget or a callback/executable. The
immutable `control/owner-trigger-config.json` is hash-bound by the optional
`triggerConfigHash` in the prepared owner envelope. Omitting the config keeps this
source and watcher off.

After the explicitly authorized owner is installed, use `evidence-trigger-watch` with
the existing private debug config, or the registered owner control operation
`watch_triggers` (TECH command `experiment watch-triggers`). This is a bounded foreground
invocation using one existing EvidenceRuntime refresh/store/ring. It ends on the original
installation lease deadline, owner closure, or all configured windows finishing. Ordinary
evidence/status reads remain inert. A persisted reservation prevents concurrent watchers
or a restart from re-arming this run. Stop/rejection remains reported evidence, not proof
that a capture or gameplay assertion succeeded.

Negative slots reference only images already retained strictly before the trigger at
millisecond resolution; same-millisecond ordering is ambiguous and stays MISSING.
Precise canonical timestamp strings are retained verbatim. Missing pre-roll stays MISSING. Dispatched slots match the exact acknowledged native capture ID
within the declared request/deadline interval. Each matched slot records its canonical
manifest `observedAt`, signed `offsetFromRequestedMs`, and match basis. That timestamp is
manifest observation/completion time, not a claim that all four views were rendered at
the nominal T+offset. Event and per-frame Arena revisions remain explicit. Camera/pause
perturbation still makes behavior evidence INCONCLUSIVE, and exact native restoration,
closed-owner, cleanup, finite capture budget, and teardown fences still apply.

Source scope and deferred real-game acceptance are tracked in
[the experiment source-scope record](../docs/KNEEKURA_EXPERIMENT_SOURCE_SCOPE_20261001.md).
