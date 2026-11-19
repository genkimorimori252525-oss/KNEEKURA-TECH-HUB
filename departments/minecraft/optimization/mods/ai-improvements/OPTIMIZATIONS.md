# AI Improvements — optimization finding ledger

Status: **MECHANISM_ONLY / PERFORMANCE_NOT_VERIFIED**. The findings below come from [historical source commit `89c89590d8160f332bd2740acd0a67c96f37f00d`](https://github.com/BuiltBrokenModding/AI-Improvements/tree/89c89590d8160f332bd2740acd0a67c96f37f00d), Minecraft **1.20 Forge**, not from a verified 1.20.1 distribution JAR.

## OPT-AI-01 — Goal pruning by entity type

- **Category**: `TICK_SIMULATION`, `ENTITY_BLOCKENTITY`
- **Evidence basis**: DIRECT_OBSERVATION of `ConfigMain`, `ModifierSystem`, `ModifierLayer`, `GenericRemove`, `FilteredRemove`.
- **Baseline**: each eligible Mob runs all its installed Goals; some do cosmetic looking or animal behaviors.
- **Optimization target**: remove specified idle looking, random looking, animal float/panic/breed/tempt/follow/stroll/selected fish/squid Goals from eligible instances.
- **Guard**: explicit config boolean and target EntityType filter, with special handling to inspect Goal class.
- **Fast path**: Goal removed from selector after initial list scan; its subsequent scheduled execution is avoided.
- **Fallback**: no config match → retain original Goal; removal disabled by default for most features.
- **Cache/invalidation**: no general time-changing cache demonstrated. A change in config after mob creation may not restore removed Goals; treat as re-creation/reapplication question.
- **Allocation**: `ModifierLayer` builds a temporary `HashSet` of removed Goals on application; repeated execution frequency, not per-tick allocation, is the primary candidate.
- **Concurrency**: entity injection event during server entity lifecycle; ownership of selector iteration and other mods' injected Goals needs real test.
- **Correctness risk**: intentional semantics change. No "invisible" equivalence; animations, steering, animal actions, aiming and modded custom Goal scheduling can differ.
- **Benchmark state**: `PERFORMANCE_NOT_VERIFIED`.
- **Source**: [ModifierLayer](https://github.com/BuiltBrokenModding/AI-Improvements/blob/89c89590d8160f332bd2740acd0a67c96f37f00d/src/main/java/com/builtbroken/ai/improvements/modifier/editor/ModifierLayer.java), [Config](https://github.com/BuiltBrokenModding/AI-Improvements/blob/89c89590d8160f332bd2740acd0a67c96f37f00d/src/main/java/com/builtbroken/ai/improvements/ConfigMain.java)

## OPT-AI-02 — Trigonometric lookup in vanilla LookControl

- **Category**: `CACHE_DATA_STRUCTURE`, `ENTITY_BLOCKENTITY`.
- **Evidence basis**: DIRECT_OBSERVATION of `FastTrig.init/atan2`, `FixedLookControl`, `ModifierSystem.replaceLookHelper`.
- **Baseline**: regular `LookControl` calculates pitch/yaw using trigonometric math.
- **Optimization target**: substitute look-direction `atan2` with 256×256 lookup table (`ATAN2_BITS=8`, `ATAN2_COUNT=65536`), initialized once.
- **Guard**: replace only exact vanilla `LookControl` class (or null) and configured/filtered entities. Custom `LookControl` subclasses remain untouched.
- **Fast path**: cached float lookup with quadrant arithmetic, no call to `Math.atan2` for each lookup.
- **Fallback**: original controller retained for excluded/custom types. After replacement, *no proven per-lookup accuracy fallback* for outlying input domains.
- **Cache**: key = quantized normalized 2D angle bins; value = `float` radians; owner = mod process-global static array; 65,536 slots ≈256 KiB base memory; lifetime = JVM process; initialization in common setup; no runtime invalidation needed for immutable contents.
- **Allocation**: preallocates table; no claim of GC or end-to-end CPU gain without benchmark.
- **Concurrency**: static read-only table after setup; initialization order and unusual inputs/NaN still require tests.
- **Correctness risk**: approximate math, discretization error, NPC head motion and ranged weapon aiming; threshold-specific rotation may shift. Config changes should not orphan prior look controllers.
- **Benchmark state**: `PERFORMANCE_NOT_VERIFIED`.
- **Source**: [FixedLookControl](https://github.com/BuiltBrokenModding/AI-Improvements/blob/89c89590d8160f332bd2740acd0a67c96f37f00d/src/main/java/com/builtbroken/ai/improvements/FixedLookControl.java), [FastTrig](https://github.com/BuiltBrokenModding/AI-Improvements/blob/89c89590d8160f332bd2740acd0a67c96f37f00d/src/main/java/com/builtbroken/ai/improvements/FastTrig.java)

## OPT-AI-03 — Move frequent successful filters forward

- **Category**: `TICK_SIMULATION`, `CACHE_DATA_STRUCTURE`.
- **Evidence basis**: DIRECT_OBSERVATION of `FilterLayer.handle`, `ModifierLayer.process/bubble`.
- **Baseline**: sequential type/Goal filter evaluation visits initial order for every mob that enters.
- **Optimization target**: reduce average lookup steps if some filters trigger often.
- **Mechanism**: count successful filters, swap with previous item when hits exceed, normalize counters to avoid overflow.
- **Fast path**: quicker match for heavy-hitting filter types on later entities *if* observed frequencies correlate.
- **Fallback**: no matched filter → ordinary scan; no guaranteed stable canonical evaluation order for side-effectful filters.
- **Cache**: hit counters and order form state, global to system; invalidation/normalization only on counter condition. `enableCallBubbling` setting is present in `ConfigMain`, but selected source code did **not** show it guarding swaps: verify before treating as effective toggle.
- **Correctness risk**: if filters have side effects or overlap, reordering may affect which editor wins. Needs priority/safe commutativity checks, especially for siege actor types.
- **Benchmark state**: `PERFORMANCE_NOT_VERIFIED`.
- **Source**: [FilterLayer](https://github.com/BuiltBrokenModding/AI-Improvements/blob/89c89590d8160f332bd2740acd0a67c96f37f00d/src/main/java/com/builtbroken/ai/improvements/modifier/filters/FilterLayer.java)

## OPT-AI-04 — Remove duplicated entity registration handlers

- **Category**: `TICK_SIMULATION`, `ENTITY_BLOCKENTITY`.
- **Evidence**: [Issue #31](https://github.com/BuiltBrokenModding/AI-Improvements/issues/31), [commit 2e95e6e](https://github.com/BuiltBrokenModding/AI-Improvements/commit/2e95e6e62edeea7cfd86a06865d5cebaf190ab39).
- **Baseline**: older version was subscribed to both `LivingSpawnEvent` (multiple subevents) and `EntityJoinLevelEvent`; modifier processing could be invoked more than needed.
- **Optimization**: removal of former listener, retaining the latter. Verifiable code diff: deleted an event subscriber, reducing opportunities for extra execution.
- **Guard/fallback**: relying on `EntityJoinLevelEvent` to cover needed entities; not a per-Mob toggle.
- **Correctness risk**: verify entities spawned by unusual third-party systems still receive required modifications exactly once, not zero times.
- **Benchmark state**: `PERFORMANCE_NOT_VERIFIED`. Maintainer reports the patch addresses server overload; no independent A/B collected.
