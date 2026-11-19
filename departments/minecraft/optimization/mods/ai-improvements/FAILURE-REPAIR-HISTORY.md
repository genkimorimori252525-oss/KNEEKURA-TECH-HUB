# AI Improvements — failure/repair selection

**History status:** PARTIAL, source diff reviewed, runtime NOT_RUN. Research window: selected Issues **#31**, **#10** and related fixes in versions preceding Forge 1.20 source 0.5.2. No all-Issues crawl claimed.

## #31 — unnecessary multiple event dispatches

The [issue](https://github.com/BuiltBrokenModding/AI-Improvements/issues/31) reports an overloaded server and links a spark profile. The maintainer's [commit `2e95e6e62e...`](https://github.com/BuiltBrokenModding/AI-Improvements/commit/2e95e6e62edeea7cfd86a06865d5cebaf190ab39) says one old `LivingSpawnEvent` listener had multiple subevents and duplicated calls also covered by `EntityJoinLevelEvent`; the observed repair deletes the former subscriber from `ModifierSystem`.

- **Before:** `onSpawn(LivingSpawnEvent)` and `onEntityJoinWorld(EntityJoinLevelEvent)` each called `editor.handle`.
- **After:** only the latter remains in the selected source path.
- **Observed evidence:** actual commit diff; **claimed symptom** is reporter/maintainer-supplied; original spark data and runtime improvement were not rebenchmarked.
- **Lesson:** measure listener invocation counts and enforce once-only setup before micro-optimizing each Goal.

## #10 — behavior changes require per-Mob filtering

The [issue](https://github.com/BuiltBrokenModding/AI-Improvements/issues/10) asks to keep some mobs' idle/head-looking behavior while disabling others'. The [commit `4f89b9f867...`](https://github.com/BuiltBrokenModding/AI-Improvements/commit/4f89b9f86729c4967670b7e5fc7e5fb4190f25a1) adds `FilteredConfigValue` and filtered look-goal/controller logic.

- **Before:** broad look-goal removal/config.
- **After:** list-controlled eligible EntityType IDs; existing custom LookControl guard retained.
- **Lesson:** optimization toggles must protect behavior and rendering intent by mob role.

No independent 1.20.1 Forge/TPS/compatibility test performed. Historical source experiment records and capture hashes remain pending; this note is not a history-adapter imported proof.
