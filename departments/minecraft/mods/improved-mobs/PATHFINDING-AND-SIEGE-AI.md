# Improved Mobs — route planning through breakable blocks

ANCHOR: [source tree `029b8c20302a76bac1af9f5140e2abb6f73fea5c`](https://github.com/Flemmli97/ImprovedMobs/tree/029b8c20302a76bac1af9f5140e2abb6f73fea5c); Minecraft 1.20.1 Forge. **Static source-backed only**.

## Distinctive AI: plan through a removable obstacle

Unlike a reactive `stuck → break nearest wall` tactic, `GroundNodeMixin` changes `WalkNodeEvaluator` classification: blocks permitted by `BreakableBlocks` are assigned a walkable path type, while collision checking is specialized to ignore those breakable blocks for **planning**, with bounded in-search caches. `PathFindingUtils.notFloatingNodeModifier` adds a malus of **6** for a ground breakable route (flying/water path modifier cost **2**). These numbers are *implementation constants*, not recommended product balance.

The world block remains physically present during path calculation; the path is a **hypothetical future traversable corridor**. `NodeEvaluatorMixin` stores flags for ability to break/climb; `EventCalls.onEntityLoad` enables them for selected mobs, gated by gamerule `mobGriefing` for block breaking.

The separate `BlockBreakGoal` turns planned reachability into an actual edit. After a configurable cooldown, if the mob has not changed its block position and target remains beyond roughly 1 block, it scans `breakAOE` candidate positions oriented by the **next path node** (fallback: current facing), tests permitted block/collision/tool harvest, displays crack stages over ticks, breaks the chosen block and recomputes path. The scan advances one candidate index when no acceptable block found: don't assume an instantaneous exhaustive search.

Source locators:
- [GroundNodeMixin](https://github.com/Flemmli97/ImprovedMobs/blob/029b8c20302a76bac1af9f5140e2abb6f73fea5c/common/src/main/java/io/github/flemmli97/improvedmobs/mixin/pathfinding/GroundNodeMixin.java)
- [PathFindingUtils](https://github.com/Flemmli97/ImprovedMobs/blob/029b8c20302a76bac1af9f5140e2abb6f73fea5c/common/src/main/java/io/github/flemmli97/improvedmobs/utils/PathFindingUtils.java)
- [BlockBreakGoal](https://github.com/Flemmli97/ImprovedMobs/blob/029b8c20302a76bac1af9f5140e2abb6f73fea5c/common/src/main/java/io/github/flemmli97/improvedmobs/ai/BlockBreakGoal.java)
- [BreakableBlocks](https://github.com/Flemmli97/ImprovedMobs/blob/029b8c20302a76bac1af9f5140e2abb6f73fea5c/common/src/main/java/io/github/flemmli97/improvedmobs/config/BreakableBlocks.java)

## Exact default policy and gates

From the ANCHOR `Config.CommonConfig`:
- `breakerChance=0.3`, `breakerInitCooldown=120`, `breakerCooldown=20`, `difficultyBreak=0`;
- default breakables: `#forge:glass`, `#forge:glass_panes`, `#minecraft:fence_gates`, `#forge:fence_gates`, `#minecraft:wooden_doors`;
- `breakingAsBlacklist=false`; `breakTileEntities=true`; `idleBreak=false`; `restoreDelay=0`;
- `breakerSightIgnore=0.5`, `ignoreHarvestLevel=false`; excludes by configured entity flag and player/other mod policies.
- Harvest checks and collision checks still apply; **a mob does not automatically mine obsidian or any arbitrary protected wall**.

These are code defaults, not claims about edited config files or loaded JAR values.

## Ladder and flying alternate routes

- `PathFindingUtils.createLadderNodeFor` proposes vertical adjacency nodes if ladder present; `LadderClimbGoal` applies Y motion ±0.15 and restrains horizontal speed.
- `FlyRidingGoal.checkFlying` first checks ground navigation failure; constructs a separate hypothetical flying path, compares endpoint reachability/progress, summons a special mount if worthwhile; staged ride and slow-falling during dismount. The path is an **alternative route**, not a tactical block placement.
- `WaterRidingGoal` similarly uses a special aquatic mount; needs separate multiplayer and entity transition checks.
- `StealGoal` is a separate low-priority MoveToBlock task when there is no combat target; requires eligible opened container.
- No autonomous **pillar/bridge block placement** mechanism established in the ANCHOR source. Changelog/UI hints from 2018 mention building as only an idea; do not mislabel Improved Mobs as a builder.

## KNEEKURA comparative design vocabulary only

| Previously studied system | Core technical distinction |
|---|---|
| Epic Mob Siege: Nightmare | Product promises wall breaking / towering; exact release JAR implementation still UNKNOWN |
| Zombies Break & Build | Stuck/partial-path detection, distinct bridge, pillar and destroy actions plus persistent timed block restoration |
| Historical Invasion Mod | Explicit `DIG/BRIDGE/LADDER/SCAFFOLD` in planning node/action graph, engineer specialist |
| Improved Mobs | Global mixin-expanded navigation treats permitted blocks as traversable with cost; physical mining then follows path |
| Raids: Enhanced | Late-wave boss injection and special boss flight/weapon controllers, rather than global block-aware path planning |

Suggested future experiment only (not chosen architecture): obstacle dimensions (height/width), path cost while wall intact, time-to-breach, failed partial paths, incompatible protection mods, priority starvation and horde TPS. Keep the strategies distinct until comparative LAB data exists.
