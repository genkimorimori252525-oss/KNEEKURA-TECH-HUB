# Epic Mob Siege: Nightmare — exact 1.20.1 Forge binary anchor

Date: **2026-10-11**. This file adds **new first-party bytecode evidence** to the historical [research README](README.md). Do **not** rewrite the earlier `NOT_OBTAINED` receipt as though it had always been known; use this newer dated evidence instead.

## Exact artifact acquired

- User-uploaded file, independently read: `NESM-1.20.1-1.0.1.jar`
- **SHA-256**: `7b931b42b42e6f9b349d3eb4f7ad59904d3cfb82afbe8cbfee12448810b31de9`
- Size: **62,318 bytes**, ZIP/JAR **49 entries**, **39 .class files** (all class major **61 / Java 17**).
- Class packages: `com.esm.nightmare` (15 classes), `Base` (6), `MobBehavs` (17), `esmsounds` (1).
- `META-INF/MANIFEST.MF`: `Implementation-Version: 1.20.1-1.0.1`, implementors nuclearlavalamp, greenchiss, timestamp `2025-11-29T01:33:09-0500`.
- **Metadata conflict**: `META-INF/mods.toml` declares `modId=nightmareesm`, `version=1.0.0`, loader `javafml`, loader/Forge range `[47,)`, license `All Rights Reserved`. Filename/manifest version **1.0.1**, `mods.toml` **1.0.0**.
- No Mixin config, access transformer, custom audio/model asset or bundled external library found in exact archive. Forge event subscribers and direct world mutations appear instead.
- Full 39-class bytecode disassembled locally using `javap -p -c -l` (only local analysis; raw dumps *not* committed). Selected callers, constructors and bytecode control flow reviewed. **No Minecraft boot / real-world gameplay test** run.
- Reference distribution page: https://www.curseforge.com/minecraft/mc-mods/epic-mob-siege-nightmare/files/7273546 (same filename/1.0.1 metadata, but this SHA is the **uploaded file identity**, not a separately authenticated CDN download).

## Executable architecture — observed bytecode contracts

**Mod root** `com.esm.nightmare.NightmareMain`:
- `MobSpawnEvent.FinalizeSpawn` runs initial changes behind `isSiegeDay`: spawn-time target change, enhancements to zombie/creeper/skeleton/spider, mass mob duplication, special riders, aggression.
- `LivingEvent.LivingTickEvent` routes Mob actors into `LivingMobTick` (client-side excluded in its branch) and creeper-special processing.
- `LivingMobTick` makes `new MobTargetPlayer` on every server-side Mob tick, and for Zombie: checks world `mobGriefing` OR `ESMConfig.AllowZombieGriefing`, then time-gates excavation, up/down digging, building, optional TNT and ignition. Spider web and water-speed behavior elsewhere.
- The active logic is **event/constructor driven**, NOT the same persistent `GoalSelector` lifecycle as historical Epic Siege Mod (1.12), and NOT ANCHOR `Improved Mobs` pathnode Mixins.

**Excavation and construction**:
- `MobDig`, `MobDigDown`, `MobDigUp` do immediate conditional block checks and instantiate `MobDamageBlock`.
- `MobDamageBlock.<init>` calls vanilla `Level.destroyBlock(BlockPos, true)` directly, after a simplistic exclusion check. This **emits block drops** (for eligible vanilla blocks) and performs a real world modification.
- `MobBuildBridge` tests nearby forward gap and places a block under/in front of mob by instantiating `MobPlaceBlock`; `MobBuildUp` detects target above/near, checks overhead space, places support then moves mob upward to block center.
- `MobPlaceBlock.<init>` invokes `Level.setBlockAndUpdate(pos, block.defaultBlockState())` and plays placement sound.
- `CreeperBreachWalls` tests player distance, wall obstruction, time threshold and targets, then invokes `CreeperExplode`; TNT placement/fire and web emission have distinct classes.

**Default intervals** from `ESMConfig.<clinit>`: `entityDigDelay=5`, `entityBuildDelay=5` ticks; the `Clocker.IsAtTimeInterval(Entity,int)` bytecode checks **entity tickCount % interval == 0**. The other `Clocker` method `GetIndexFromTime(3)` chooses subroutine by **System.currentTimeMillis() % 3**; not a world-tick modulo, deterministic seeded selector or random source.

## Specific code-level hazards — must not adopt without redesign

1. **Config ownership is incomplete:** `ESMConfig.AllowZombieBuilding` is defined (`iszombiebuilding`, marked deprecated) but no behavior class reads it (the only bytecode references are the declaration/initializer). In the active `LivingMobTick` flow, **building is reached under mobGriefing OR legacy AllowZombieGriefing**, not an independent `AllowZombieBuilding` gate.
2. **Tool requirement likely ineffective:** when `EntitiesNeedPickaxesToBreakBlocks` is enabled, `ItemChecker.EntityHasPickaxe` stores boolean `isAllowedToGriefWithItemHeld` into local slot 7, but no subsequent `iload 7` condition is present in the method. Consequently, the computed result is **not used to gate** dig/build dispatch in this class. This is a bytecode-level finding, not a runtime reproduction.
3. **Dig branch fall-through:** switch `GetIndexFromTime(3)` has case 0 constructing `MobDig` then proceeding into `MobDigUp` and `MobDigDown`; case 1 proceeds into case 2, without jump breaks. Thus the route does **not** select exactly one dig behavior per event when zero or one is returned.
4. **Blacklist is display-text substring logic:** `MobDamageBlock.isExcludedBlock` compares `Block.getName().getString().toLowerCase()` against a static lowercased comma-separated `BlocksEntitiesCannotDigThrough` string using `String.contains`. This is not an exact registry ID/tag allow/deny contract and may have unintended substring matches.
5. **No reversible terrain ownership detected:** no local saved baseline BlockState/NBT class, expiration service, persisted per-position journal, or block recovery method identified in this JAR. `MobDamageBlock` destroys and `MobPlaceBlock` places directly. **The JAR does not itself supply the requested time-based exact restoration.**
6. **Work is repeated frequently:** the main server tick path allocates behavior objects and repeatedly evaluates world/player conditions. This suggests a horde scaling risk, but **no cost or TPS has been measured**.
7. **No central write coordination:** constructor wrappers issue direct world writes; there is no observed per-cell undo/lease/claim-safety adapter. A world protection system must be designed separately rather than assuming vanilla gamerules alone cover every path.

## Evidence limits

- Names like `MobDamageBlock` and `MobBuildBridge`, JVM instructions, parameters, public methods and control branches are recovered from uploaded exact bytecode.
- `m_46961_(BlockPos,Z)` and `m_46597_(BlockPos,BlockState)` are identified from Minecraft/Forge method context as destroy and setBlockAndUpdate. A formal Mojang+Forge mapping/classpath pass should still bind method IDs for portability.
- `Minecraft 1.20.1 + Forge` ANCHOR for this artifact, while 1.12 Epic Siege Mod is **COMPARATIVE** only; their classes are **not** claimed identical.
- No deduced crash count, multiplayer behavior, claims compatibility or measured performance is proven.
- Upstream code and media are ARR. No JAR or raw bytecode/decompiled source distributed from Tech Hub.

## Immediate next inspection/acceptance (staged)

1. Pin exact 1.0.0 release for bytecode diff and verify claimed change to mine/drop and the chunk-loader deadlock repair; current 1.0.1 release notes alone do not prove fix effectiveness.
2. Expand evidence to `CreeperBreachWalls`, `MobTargetPlayer`, `DuplicateMob`, `GetNearestTarget` full switch/branch matrix; inspect `ESMConfig` per-key runtime gates and side effects.
3. Forge 1.20.1 bounded LAB: one zombie vs walls/height gaps, gameRule `mobGriefing` false with AllowZombieGriefing toggles, pickaxe true/false, building config toggle, 1/10/50/100 actors, with reset receipts and chunk safety.
4. Separate independent restoration policy — prior [KNEEKURA reversible terrain design](../../design/kneekura-invasion-reversible-terrain-v1.md) remains DESIGN_ONLY.

No implementation or runtime tests were performed in this research.
