# ServerCore — entity activation and adaptive MSPT budgets (slice 2B)

Date 2026-10-11. User-supplied path basename `servercore-forge-1.5.2+1.20.1.jar` (binary **NOT_ACQUIRED**, SHA-256 and release-source parity **UNKNOWN**).

ANCHOR source snapshot: [`Wesley1808/ServerCore@d1d0a02d39d0739441419e3a20f46fbc88d98ec5`](https://github.com/Wesley1808/ServerCore/tree/d1d0a02d39d0739441419e3a20f46fbc88d98ec5), branch `1.20.1`; full **path inventory** 135 blobs and 105 Java files, Git recursive tree not truncated; **only selected source files actually read**. FRONTIER separate latest branch not analyzed. Source `ActivationRange` notes code adapted from Paper/Spigot with GPL-3.0 source notice, **license audit needed** before implementation. No upstream code copied.

**Category:** `TICK_SIMULATION`, `ENTITY_BLOCKENTITY`, `CULLING_LOD`, `CACHE_DATA_STRUCTURE`. Mechanism evidence DIRECT_OBSERVATION source, **PERFORMANCE_NOT_VERIFIED / NOT_RUN**.

## S-01 — activation range by mob archetype

Vanilla baseline: all loaded eligible entities may receive regular ticks, including those far from players. [`ActivationRange.java`](https://github.com/Wesley1808/ServerCore/blob/d1d0a02d39d0739441419e3a20f46fbc88d98ec5/common/src/main/java/me/wesley1808/servercore/common/activation_range/ActivationRange.java) categorizes entities as raiders, villagers, zombies, flying, animals, water, neutral, monster, misc. During `activateEntities`, scans bounding regions near non-spectator players; entities in eligible range get activated for current tick + 19. Inactive entities receive throttled tick treatment, with special immunity checks for active targets, jumping, effects, portal activity, moving items/orbs, arrows, villagers in panic, bees, etc.

- **Guard:** `ActivationRangeConfig.ENABLED` is **false by default** in this pinned source. Disabling feature retains normal ticking; do **not** treat activation changes as automatically active upon install.
- **Further guard:** `isExcluded` exempts special classes including Wither, Ender Dragon, projectiles, TNT, lightning, player and configured `excluded_entity_types`. Exempt list defaults include `minecraft:ghast`, Warden and hopper minecart. Some customized bosses need their own exclusion regardless of base class.
- **Fallback:** eligible exceptions remain active; while inactive selected entities can be temporarily awakened by group counters and situations; not equivalent to full vanilla tick for all types.
- **Correctness:** attacks, mobfarms, breeding, navigation, villagers detecting danger, siege waves and timed explosions need behavioral assertions; scope activation exclusions around encounter/raids explicitly if adopted elsewhere.
- **Source config:** [`ActivationRangeConfig.java`](https://github.com/Wesley1808/ServerCore/blob/d1d0a02d39d0739441419e3a20f46fbc88d98ec5/common/src/main/java/me/wesley1808/servercore/common/config/tables/ActivationRangeConfig.java). `SKIP_NON_IMMUNE=false` also default; replacing it with "always skips a quarter" would be wrong.

## S-02 — adaptive server budget driven by MSPT

[`DynamicManager.java`](https://github.com/Wesley1808/ServerCore/blob/d1d0a02d39d0739441419e3a20f46fbc88d98ec5/common/src/main/java/me/wesley1808/servercore/common/dynamic/DynamicManager.java) obtains server average tick time once per 20 ticks, compares to configured target with approximately 5-ms deadband, changes **one** setting per eligible interval according to prioritized sequence. [`DynamicConfig.java`](https://github.com/Wesley1808/ServerCore/blob/d1d0a02d39d0739441419e3a20f46fbc88d98ec5/common/src/main/java/me/wesley1808/servercore/common/config/tables/DynamicConfig.java) declares:

- `ENABLED=false` by default, target `35 MSPT` if enabled;
- separate configurable view/simulation distance, random-tick chunk range, mobcap multiplier and update intervals;
- priority order `chunk_tick_distance` → `mobcap_multiplier` → `simulation_distance` → `view_distance`.

**Mechanism:** closed-loop quality/resource degradation under load. It changes the **amount of simulation**, not the speed/complexity of existing simulation code, so performance and gameplay contracts must be tested separately. `Mobcap` adjustment influences spawning/raid composition; `viewDistance` changes client chunk loading and can cause network spikes. No numeric improvement measured.

## Failure history

- [#118](https://github.com/Wesley1808/ServerCore/issues/118) reports a 1.21.1 iron farm affected by activation range, **NOT a 1.20.1 Forge runtime observation**. Author advised excluding villager and reloading chunk/area; reporter stated reload resolved the issue. This is operational/config outcome, not direct proof of source fix.
- Historic [commit `09ffb1b...`](https://github.com/Wesley1808/ServerCore/commit/09ffb1b7d1c958b4bb2723d4ef1f3ce09af59a4b) adds egg spawning to chicken **inactive tick**, demonstrating need for simulation-side effects even when expensive AI work is throttled. This is a historical 2022 code delta, not tested in current release.
- See [FAILURE-REPAIR-HISTORY.md](FAILURE-REPAIR-HISTORY.md).

## Follow-up

Compile exact 1.5.2 Forge JAR identity and bytecode feature flags, whole source/Mixin inventory, command config effects, special modded Goal/Brain lifecycle, 1/10/50/100 mob horde with and without exclusions, MSPT median/p95/p99 and exactly-once attacks/event timing. No GameTest or profiling executed.
