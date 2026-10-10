# Improved Mobs — difficulty, equipment, item actions, server sides and compatibility

ANCHOR: source revision [029b8c20302a76bac1af9f5140e2abb6f73fea5c](https://github.com/Flemmli97/ImprovedMobs/tree/029b8c20302a76bac1af9f5140e2abb6f73fea5c) (Minecraft 1.20.1 Forge). Static analysis.

## Difficulty ownership and progression

`DifficultyData` extends `SavedData` and stores server-global difficulty/previous day time/pause state; `PlayerDifficulty` stores per-player state (Forge capability). Available modes in `Config`:
- `GLOBAL` (server-wide);
- `PLAYERMAX`, `PLAYERMEAN`, `PLAYERSUM` (aggregate nearby player difficulty);
- `DISTANCE` (configured center), `DISTANCESPAWN` (world spawn), with scalar or per-block progression zones;
- external systems optionally integrated (Scaling Health, PlayerEx, LevelZ, vanilla regional/clamped) via ON/OFF/ADD semantics for selected versions.

`EventCalls.tick` updates time progression in Overworld and can react to time skips; `EventCalls.onEntityLoad` obtains a difficulty value for that mob and initializes buffs, equipment, AI, target policies. Difficulty scaling is not by itself proof of runtime fairness.

Locations: [DifficultyData.java](https://github.com/Flemmli97/ImprovedMobs/blob/029b8c20302a76bac1af9f5140e2abb6f73fea5c/common/src/main/java/io/github/flemmli97/improvedmobs/difficulty/DifficultyData.java), [EventCalls.java](https://github.com/Flemmli97/ImprovedMobs/blob/029b8c20302a76bac1af9f5140e2abb6f73fea5c/common/src/main/java/io/github/flemmli97/improvedmobs/events/EventCalls.java), [Config.java](https://github.com/Flemmli97/ImprovedMobs/blob/029b8c20302a76bac1af9f5140e2abb6f73fea5c/common/src/main/java/io/github/flemmli97/improvedmobs/config/Config.java).

## Runtime-selected behavior attached to existing modded Mob

On `EntityJoinLevelEvent` (Forge `EventHandler.onEntityLoad`) the shared `EventCalls.onEntityLoad`:
1. excludes client-only execution and its own custom summon mounts; configurable spawner-exclusion check;
2. derives flag eligibility / configurable blacklist or whitelist for mob EntityType and tags;
3. assigns armor, held weapons, enchantments, attributes once using EntityFlags;
4. conditionally installs Goals: `ItemUseGoal` priority 1, `BlockBreakGoal` priority 1, ladder 4, steal 5, flying/water mount 6, target modifications through targetSelector;
5. checks `mobGriefing` for break-path enablement and stealing, preventing hardwired base-wide griefing in those code paths.

Strong reuse concept: *behavior overlays on multiple mobs* without copying one zombie class. But it also modifies target classes and path evaluator behavior via Mixins, so support for **all** third-party mobs is NOT proved. An ordinary ownerless/neutral custom mob could be changed unexpectedly: [issue #216](https://github.com/Flemmli97/ImprovedMobs/issues/216), historical 1.16.5 report.

## Item behavior

The source uses a strategy registry `ItemAI`, `ItemAIs` and `ItemUseGoal`. Verified named source handlers include bow, crossbow, trident, shield, thrown splash/lingering potion, enchanted book, TNT, snowball, ender pearl, flint and steel, lava bucket. Each has its own cooldown, hand rule and attack operation. `ItemAIs.TNT` is separate from the regular melee goal and can produce explosions; it must not share naive direct mined-block recovery assumptions.

`StealGoal` searches containers in local range and delegates opened/loot eligibility to a platform helper. The Forge path `ContainerCap` records whether an inventory was previously opened. This is a player-owned-resource policy risk for tower defense and must not be introduced merely because a Mob has an item-use overlay.

Locations: [ItemAIs.java](https://github.com/Flemmli97/ImprovedMobs/blob/029b8c20302a76bac1af9f5140e2abb6f73fea5c/common/src/main/java/io/github/flemmli97/improvedmobs/ai/util/ItemAIs.java), [ItemUseGoal.java](https://github.com/Flemmli97/ImprovedMobs/blob/029b8c20302a76bac1af9f5140e2abb6f73fea5c/common/src/main/java/io/github/flemmli97/improvedmobs/ai/ItemUseGoal.java), [StealGoal.java](https://github.com/Flemmli97/ImprovedMobs/blob/029b8c20302a76bac1af9f5140e2abb6f73fea5c/common/src/main/java/io/github/flemmli97/improvedmobs/ai/StealGoal.java).

## Client-server/network notes

The mod page claims most gameplay works server-side, client installation primarily adds difficulty display. ANCHOR Forge `PacketHandler` creates `SimpleChannel("improvedmobs:packets")`, sends two registered packets (`PacketDifficulty`, `PacketConfig`), checks negotiated channel presence per player and accepts peers without requiring the channel. This source detail is compatible with *server-mostly* gameplay, not evidence that all clients/every optional mod combination pass.

No direct customized mob models or attack animation assets are found in the source tree beyond UI difficulty meter and vanilla entity/mount appearance. Source lists an icon PNG and difficulty bar GUI; full visuals need live observation.

Forge-specific hooks: `LivingAttackEvent`, `LivingHurtEvent`, `EntityJoinLevelEvent`, `ProjectileImpactEvent`, `ExplosionEvent.Detonate`, `PlayerInteractEvent`; Fabric has different interceptors.

## Compatibility boundaries with user-researched mods

- **Raids: Enhanced**: adds `Raider` subtypes (Blimp/Golem/Zapper/Drill). Improved Mobs' broad `onEntityLoad` may attach Goals/modifiers to third-party mobs depending on class, configuration and exclusions; it does not know the raid boss encounter semantics by default.
- **Epic Mob Siege: Nightmare**: exact 1.20.1 JAR not examined; double block-break or pathing hooks may conflict, not proven either way.
- **Zombies Break & Build**: both can modify navigation and block-break behavior; simultaneous Goal insertion and duplicate terrain writes must be explicitly tested, never assumed composable.
- **Enhanced AI**: [upstream issue #304](https://github.com/Flemmli97/ImprovedMobs/issues/304) asked about compatibility; maintainer responded they did not know any incompatibilities, then closed. This is not a tested compatibility matrix.
- **Epic Fight**: a 1.20.1 Forge reported Drowned crash led to an actual scheduled mount transition fix, see failure history.
- **Lithium/Roadrunner**: earlier Mixin injection conflict, see failure history.
- **Protection claims**: source checks `mobGriefing`, but proving all claim plugins guard `destroyBlock`, TNT and direct item effects requires runtime.
