# Bounded original-invocation Decision hooks

This slice targets the exact mapped Minecraft 1.20.1 / Forge 47.2.0 development ANCHOR described by `vanilla-ai/ANCHOR-BYTECODE-LEDGER-2026-10-03.json`. It is not a portable production/SRG hook or resident post-Mixin class attestation.

## Enablement and limits

Normal launches and debug launches default to `decisionHooks: false`. An explicit Gradle Debug Workspace configuration with `decisionHooks: true` adds the LAB-owned init script and separate debug source-set resources. Its required Mixin configuration uses a dedicated `decisionmixin` package, excluding ordinary bridge classes. Main MOD source/output is unchanged.

After startup, select one exact UUID with `target UUID --decision-burst`. Optional controls are `--decision-ticks`, `--decision-events`, `--decision-bytes`, `--decision-nodes`, and `--decision-channels goal,brain,path,control,malus,sensor`. Defaults are 100 ticks, 256 events, 262144 payload bytes and 32 cached nodes. Hard ceilings are 200 ticks, 256 events, 524288 payload bytes, 64 nodes and 32768 bytes per event. A request cannot enable launch hooks or authorize world actions. Every selection clears the old request; one revision can arm at most once. A missing target waits for exact UUID resolution before starting the bounded window.

Capture binds the actual Mob reference, dimension, session, run, snapshot, process epoch, Arena epoch and selection revision. Removal/replacement, changed boundaries, a reversed clock, exhausted limits or writer failure closes the session. Server stopping clears it. Terminal summary metadata preserves the captured context, including its original Arena epoch; it is not a new-state observation. Byte limits cover serialized event payloads, excluding raw envelopes, terminal summary, writer and Viewer. Cost counters cover event construction and the first encoding, excluding final encoding and writer work. They cannot establish total observer effect.

## Original calls only

- `WrappedGoal.canUse/canContinueToUse`: actual returned boolean; no replay or inferred rejection reason. Start/stop hooks run after the original delegated `Goal.start/stop` returns, excluding early no-op wrapper returns.
- `Brain.tick`, final `Behavior.tryStart/tickOrStop/doStop`, `Sensor.doTick`: actual selected-entity calls, with cached status or returned result where available. Sensor candidate populations and causal reasons remain unknown.
- `Mob.serverAiStep`: after its original virtual Move/Look/Jump control tick; cached base fields do not claim custom private controller fields.
- `Mob.getPathfindingMalus`: base-method return, explicitly not the final result of a custom overriding caller or a proven malus source.
- Outer `PathFinder.findPath`: search identity at entry, bounded cache after the original inner search returns and before `NodeEvaluator.done`, then the outer actual Path result. Cache roles distinguish closed/open/other cached entries. Allocated cache entries are not a complete evaluated-neighbor trace. Custom evaluators remain `NOT_EXPOSED`.

The existing `AI_DECISION` lane retains `kneekura.original-decision-event/v1` alongside optional sampled snapshots. The Decision adapter validates bounded kind-specific fields, uses source observation IDs and preserves run/process/Arena/selection fences. Original return facts and timeline events do not infer a complete candidate set, selection reason or causality between adjacent calls. Deep capture capabilities are `PARTIAL`, including a complete bounded cache at one return. Snapshot running-set changes still cite both samples and remain temporal association.

## Verification at this implementation checkpoint

- Motion/Decision Node suite: 44 passed, 0 skipped.
- Portable Java/source contracts: passed, including strict finite request parsing and eight budget identity fences.
- Actual mapped API contracts: passed, including Goal producer sentinels (no replay), unchanged bounded node cache, registered-world and writer contracts.
- All bridge and six Mixin classes: compiled against SHA-checked actual ANCHOR dependencies and pinned MOD output.
- Debug Workspace selftest: passed.

These checks do not establish applied Mixin/native hook acceptance. That requires a separate retained native run before this slice is called operationally verified. The earlier native-r6 component acceptance predates these hooks and cannot substitute for it. Complete terrain overlays, typed Mob SDK, TF runtime adapters, eight behavioral fixtures and controlled total observer-effect measurements remain later steps.
