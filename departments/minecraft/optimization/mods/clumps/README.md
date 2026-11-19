# Clumps 12.0.0.4 — aggregate heterogeneous XP orbs with per-value accounting

Investigation: 2026-10-11. Source **1.20.1 Forge** anchored [`jaredlll08/Clumps@d249b4d25478e6044b0951f01b729c17b5860456`](https://github.com/jaredlll08/Clumps/tree/d249b4d25478e6044b0951f01b729c17b5860456), source git tree **`95093880f994660a6ddb6970243b49914a2907b6`**, 52 blobs / 21 Java + 4 Kotlin source paths, recursive complete-path index (not complete source-body acquisition). Selected Java full Mixin read. `buildSrc/.../Versions.kt`: Minecraft **1.20.1**, Forge dev **47.0.4**, Java 17, `MOD="12.0.0"` and actual build uses `GMUtils.updatingVersion` for suffixes. **Official [Modrinth Clumps 12.0.0.4](https://modrinth.com/mod/clumps/version/12.0.0.4)** references build correction #138. Requested `Clumps-forge-1.20.1-12.0.0.4.jar` binary bytes **NOT_UPLOADED**, SHA and source→JAR parity **NOT_VERIFIED** despite matching branch and version family. License [MIT](https://github.com/jaredlll08/Clumps/blob/d249b4d25478e6044b0951f01b729c17b5860456/LICENSE.md).

**Categories:** `ENTITY_BLOCKENTITY`, `TICK_SIMULATION`, `CACHE_DATA_STRUCTURE`; mechanism DIRECT SOURCE OBSERVATION, performance `PERFORMANCE_NOT_VERIFIED`, game tests NOT_RUN.

## CLUMPS-01 — replace many XP orb entities with aggregate multiset

[`MixinExperienceOrb.java`](https://github.com/jaredlll08/Clumps/blob/d249b4d25478e6044b0951f01b729c17b5860456/common/src/main/java/com/blamejared/clumps/mixin/MixinExperienceOrb.java) wraps `ExperienceOrb` at priority **1001**, overriding vanilla merging eligibility so any different live orb can combine (not only same value). `tryMergeToExisting(ServerLevel,Vec3,int)` performs a near-position AABB size **1×1×1** query, then accumulates values into a **Map<Integer,Integer> per *original orb value***, where key=XP value and count=multiplicity. The resultant orb's `value` is recalculated from sum `value * count` by `clumps$resolve`; merged orbs are discarded. `age` takes minimum so the group's lifespan does not spontaneously extend by merging older orb into younger without considering both. Source has nontrivial `count` update before map rewrite, so counts and first-merge mechanics require runtime assertion rather than assuming flawless invariance.

**Baseline:** many ExperienceOrb entities, each with position/tick/collision/pickup loop; vanilla only merges some equal-value orbs. **Fast path:** fewer entity instances, larger map per aggregate. **Guard:** live XP orb within AABB; no test of type-specific modded XP semantics, protection, or actual server performance. One huge aggregate may process very many `amount` loops at pickup, moving CPU cost from per-tick to pickup spike; not guaranteed lower total cost.

**Persistence:** `addAdditionalSaveData/readAdditionalSaveData` stores `clumpedMap` NBT as value→count integer entries. Legacy orb NBT without `clumpedMap` falls back to `value/count`; must test NBT old/new and cross-mod roundtrip. No client-only requirement for ≥1.17 per author README: server side sufficient, not proof every client renders identically.

## CLUMPS-02 — conserve vanilla Mending per XP *unit*, but changes event semantics

In `playerTouch(Player)` (server only):
1. Dispatch Forge `PlayerXpEvent.PickupXp` and honor cancellation; bypass vanilla `playerTouch` completely afterward.
2. Set `takeXpDelay=0` and gather XP map entries.
3. For each bucket of original orb value `value`, dispatch custom `ValueEvent`; for each count dispatch custom `RepairEvent` and then `repairPlayerItems` if not intercepted.
4. Accumulate remaining XP to `giveExperiencePoints`, remove the aggregate.

Exact source [`MixinExperienceOrb.java`](https://github.com/jaredlll08/Clumps/blob/d249b4d25478e6044b0951f01b729c17b5860456/common/src/main/java/com/blamejared/clumps/mixin/MixinExperienceOrb.java), [`ForgeEventHandler.java`](https://github.com/jaredlll08/Clumps/blob/d249b4d25478e6044b0951f01b729c17b5860456/forge/src/main/java/com/blamejared/clumps/platform/ForgeEventHandler.java). This deliberately processes original XP buckets to preserve Mending's per-orb behavior and custom reward events, even though only one Entity survives. Mending repair is not simply `giveExperiencePoints(totalXP)`, so a naive XP clumper would be semantically wrong.

**Crucial limitation with explicit author confirmation:** [Issue #144](https://github.com/jaredlll08/Clumps/issues/144) has **exact user-version 12.0.0.4 Minecraft 1.20.1 Forge 47.3.0** and Blood Magic 3.3.3-45. Blood Magic changes `value` during Forge PickupXp event, but Clumps' XP aggregate map remains independent of such changes. [Author's comment](https://github.com/jaredlll08/Clumps/issues/144#issuecomment-2208130840) explicitly states this event-value modification is **incompatible**, recommends supporting Clumps custom event API. This is **NOT** proven fixed, even if issue closed. Test event mutation and item XP storage; no exact compatibility assumptions.

## Repair and contradictory reports

- [Issue #124](https://github.com/jaredlll08/Clumps/issues/124) concerned **1.20 Fabric Clumps 11.0.0.1** SpawnEgg-initialized XP orbs with `value=0`. [Actual fix commit `ebb464852a132...`](https://github.com/jaredlll08/Clumps/commit/ebb464852a132188a023cf0f5698e8a4216b9476), parent `3b2b4ad169439b87c91f648b4415f688c7672619`: only write `clumpedMap` tag if map actually exists, avoiding serialization destroying spawn-egg-defined `value`. **Source 1.20.1 retains this guard**, GameTest NOT_RUN.
- [Issue #134](https://github.com/jaredlll08/Clumps/issues/134) user's Forge12.0.0.3 Mending failure in BetterMC4; maintainer reproduced normal Mending in controlled new flat world, **CONTRARY_EVIDENCE**, no accepted root or patch in inspected issue. Distinguish from #144 event mutation, for which author explicitly identifies incompatibility.
- [Issue #128](https://github.com/jaredlll08/Clumps/issues/128) one-off Forge12.0.0.3 XP Tome mending crash, not repeatable in reporter case, closed without source patch.
- [Issue #141](https://github.com/jaredlll08/Clumps/issues/141) initially alleged enormous XP; **comments establish Minecraft 1.12.2 Clumps 3.0.0**, NOT related to 12.0.0.4; its reuse as “known current XP dupe” would be false.
- [Issue #138](https://github.com/jaredlll08/Clumps/issues/138) fixed build infrastructure, not gameplay balancing.

## Correctness/performance gate

Benchmark many XP orbs (1/100/10000), normalize total XP and per-value distribution, Mending repair across armor+hand, custom XP Tome/BloodMagic events, enchanted repairs and cancelled pickups, NBT save/load, integer overflow when large map counts, server NPC kill farms and particles. Record entityCount/MSPT median/p95/p99, pickup spike time, XP+durability before vs after and cross-mod value/event semantics; **no actual run**. Concept reusable only with explicit event policy.
