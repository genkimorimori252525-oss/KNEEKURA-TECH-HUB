# Improved Mobs — Forge 1.20.1 evidence-backed technical research

Date: 2026-10-11. **Scope: mod research, not a new KNEEKURA Invasion product design.** Follow-up planning is deliberately deferred until the user chooses to reopen that step.

## Exact tracks and sources

- **ANCHOR**: Minecraft **1.20.1 Forge**; upstream [Flemmli97/ImprovedMobs at 029b8c20302a76bac1af9f5140e2abb6f73fea5c](https://github.com/Flemmli97/ImprovedMobs/tree/029b8c20302a76bac1af9f5140e2abb6f73fea5c); source `gradle.properties` says **mod 1.13.7**, Forge development version 47.1.3, Java 17, TenshiLib 1.20.1-1.7.2. Official [CurseForge release 8282565](https://www.curseforge.com/minecraft/mc-mods/improved-mobs/files/8282565) lists `improvedmobs-1.20.1-1.13.7-forge.jar` (2026-06-19).
- **FRONTIER**: Minecraft **1.21.1 NeoForge**; upstream [d495a4d617d38b841f275b174f7137e0644de13c](https://github.com/Flemmli97/ImprovedMobs/tree/d495a4d617d38b841f275b174f7137e0644de13c); `gradle.properties` says **mod 1.16.0.b**, NeoForge 21.1.233, Java 21, TenshiLib 1.21.1-2.3.0. Official [Forge/NeoForge page](https://www.curseforge.com/minecraft/mc-mods/improved-mobs) lists the 1.21.1 release (2026-08-22).
- ANCHOR branch's complete **Git tree index** was retrieved: 134 blobs, including 106 Java sources; FRONTIER: 167 blobs, including 136 Java sources. Tree APIs returned `truncated=false`. **This is full-tree PATH inventory, not byte acquisition of every blob**: selected sources and changes were read; uninspected files remain INVENTORIED.
- Source license/official distribution declaration: **All Rights Reserved** ([Forge `mods.toml`](https://github.com/Flemmli97/ImprovedMobs/blob/029b8c20302a76bac1af9f5140e2abb6f73fea5c/forge/src/main/resources/META-INF/mods.toml), CurseForge). Do not copy code/assets.
- **No release JAR SHA-256 or bytecode equivalence** established; no runtime or TPS measured. Forge+Fabric ANCHOR source layout vs NeoForge+Fabric FRONTIER kept separate.

## Player-visible feature map to source

| Feature / hint | ANCHOR evidence | State |
|---|---|---|
| Mob mines blocks in the way | `BlockBreakGoal`, `BreakableBlocks`, `PathFindingUtils`, ground/fly/swim node Mixins | EVIDENCE_BACKED_STATIC |
| Block planned as passable path node | `GroundNodeMixin` and `PathFindingUtils.notFloatingNodeModifier` | EVIDENCE_BACKED_STATIC |
| 1.20.1 restoring broken blocks | `BlockRestorationData`, `EventCalls.tick`, `Config.restoreDelay` | EVIDENCE_BACKED_STATIC; limited fidelity |
| Active ladder ascent | `LadderClimbGoal` + `createLadderNodeFor` | EVIDENCE_BACKED_STATIC |
| Flying/water mounts | `FlyRidingGoal`, `WaterRidingGoal`, summoned mounts | EVIDENCE_BACKED_STATIC |
| Equipped item use | `ItemUseGoal`, `ItemAIs` (TNT, potions, pearls, bow, trident etc.) | MAPPED_STATIC |
| Loot opened containers | `StealGoal`, Forge ContainerCap | EVIDENCE_BACKED_STATIC |
| Difficulty, equipment and buffs | `DifficultyData`, `EventCalls`, `Utils`, configs | EVIDENCE_BACKED_STATIC |
| Modded mob compatibility | entity-type/tag flags and event-based injection | EVIDENCE_BACKED_STATIC, runtime compatibility UNKNOWN |
| Newer 1.21.1 datapack overrides | `EntityOverridesManager`, JSON feature/attribute/breakable block overrides | EVIDENCE_BACKED_FRONTIER; no direct 1.20.1 parity |
| Models/worldgen | only UI difficulty bar and server-only entities; no ordinary structures/dimensions generation identified in inventoried tree | INVENTORIED, comprehensive verification incomplete |

## Reports and derived material

- [SOURCE-AND-FACETS.md](SOURCE-AND-FACETS.md): profile inventory, dependencies, evidence boundary and facet checklist.
- [PATHFINDING-AND-SIEGE-AI.md](PATHFINDING-AND-SIEGE-AI.md): breakable nodes, mining phases, ladders, mounts and action geometry.
- [RESTORATION-AND-WORLD-INTERACTION.md](RESTORATION-AND-WORLD-INTERACTION.md): exact SavedData behavior, default-disabled restore, conflicts and duplicate-loot risks.
- [DIFFICULTY-AND-INTEROPERABILITY.md](DIFFICULTY-AND-INTEROPERABILITY.md): equipment, target goals, third-party entities and networking.
- [VERSION-PORTABILITY.md](VERSION-PORTABILITY.md): 1.20.1 Forge vs 1.21.1 NeoForge.
- [FAILURE-REPAIR-HISTORY.md](FAILURE-REPAIR-HISTORY.md), [FAILURE-REPAIR-HISTORY.json](FAILURE-REPAIR-HISTORY.json): bounded upstream cases with before/after commits and unresolved concerns.
- [TECHNIQUE-HARVEST.md](TECHNIQUE-HARVEST.md): extracted, non-authorized-copy lessons.
- [ANALYSIS-RECEIPT-2026-10-11.json](ANALYSIS-RECEIPT-2026-10-11.json): machine-readable scope and status.

## Comparison with previous research (without committing to architecture)

Prior KNEEKURA research:
- [Raids:Enhanced, PR #107](https://github.com/genkimorimori252525-oss/KNEEKURA-TECH-HUB/pull/107): raid registration and specialized boss/multi-cannon attacks.
- [Epic Mob Siege + Zombies Break & Build + Invasion Mod, PR #108](https://github.com/genkimorimori252525-oss/KNEEKURA-TECH-HUB/pull/108): siege/tower tactics and stricter restoration candidate.
- **Improved Mobs** differs by **modifying path cost/types for breakable terrain directly**, dynamically augmenting existing Mob goals, exploiting ladders and vehicle paths, using item-based combat and persistent broken-block recovery. Its 1.20.1 restore feature is **not sufficient** for full protected-world reconstruction.

This PR does not modify existing research history, CODE/TECH data models, runtime experiments, MOD source or future KNEEKURA Invasion design.
