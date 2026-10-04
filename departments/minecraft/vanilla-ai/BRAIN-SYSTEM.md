# Brain system — Minecraft 1.20.1 ANCHOR

Evidence: `Brain`, `Sensor`, `Behavior`, `BehaviorControl`, and `ExpirableValue` in [the exact bytecode ledger](ANCHOR-BYTECODE-LEDGER-2026-10-03.json).

## Registered memories and expiry

Brain stores registered `MemoryModuleType` keys with optional `ExpirableValue` values. Registered-but-empty and unregistered are different states.

`getMemory(type)` throws `IllegalStateException` for an unregistered key. A generic adapter must inspect the registered map or use a verified registration-aware read; it must not issue an arbitrary list of memory getters against every Mob.

`getMemories()` returns the underlying map in the captured development class. Treat it as read-only and snapshot bounded entries. Each present `ExpirableValue` exposes `getValue()`, `getTimeToLive()` and `canExpire()`; reading must not call its `tick()`.

`forgetOutdatedMemories()` checks whether the retained TTL has expired and erases that memory, then ticks the expirable object. `ExpirableValue.hasExpired()` checks TTL <= 0. The observer records the actual retained TTL and whether it can expire; it does not recompute a guessed expiry from wall time.

Unknown/custom memory values must use a declared bounded representation. Do not call arbitrary object `toString()`, traverse arbitrary object graphs, or describe an unsupported custom value as empty. Entity references, block positions, known Walk/Look targets and known Path values need typed encoders with exact identity.

## Sensor and activity cadence

`Sensor.tick()` decrements its counter, resets it to the configured scan rate when due, and calls the original sensor's `doTick()`. Counter/readable-memory state is not the sensor's full candidate population. Never call the sensor again to produce an observation.

`Brain.tick()` orders memory expiry, sensors, behavior starts and running behavior ticks. Activity requirements use registered memory status and configured behavior/activity structures.

`updateActivityFromSchedule(dayTime, gameTime)` returns while `gameTime - lastScheduleUpdate <= 20`; when due, it records the update time, queries the schedule at `dayTime % 24000`, and attempts an activity change if needed. This method's cadence is distinct from every Brain tick.

Public snapshot surfaces include active activities, active non-core activity and running behaviors. Core/default activity and Sensor instances are private in the captured class and need separately declared access capability. No adapter infers an unexposed core/default activity from its absence in the non-core getter.

## Behavior state

BehaviorControl is the scheduler interface; Behavior implements a status/start/end-time lifecycle and memory requirements. A snapshot may record running class/reference identity. A sampled set difference is a derived transition interval, not an exact lifecycle callback or explanation of why a behavior ran.

Vanilla Villager's inspected `customServerAiStep()` explicitly calls Brain.tick. Other entities require their own call-site evidence; inherited Brain existence alone does not establish a Brain-driven Mob.

Keep key memories, active/running state, navigation and resulting motion as separate facts. WalkTarget, LookTarget, AttackTarget and PATH can be linked spatially where typed values are exposed; temporal proximity is not automatically causal.
