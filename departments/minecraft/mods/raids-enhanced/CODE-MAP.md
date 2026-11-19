# Raids: Enhanced — 1.20.1 source architecture and code map

ANCHOR commit: [`6354ebf97faaeba79affaf7e71d01ed5ae651e85`](https://github.com/FINDERFEED/raidsenhanced/tree/6354ebf97faaeba79affaf7e71d01ed5ae651e85); these are **source-tree claims**, not JAR claims.

## Entry and raid wave insertion

- [RaidsEnhanced.java](https://github.com/FINDERFEED/raidsenhanced/blob/6354ebf97faaeba79affaf7e71d01ed5ae651e85/src/main/java/com/finderfeed/raids_enhanced/RaidsEnhanced.java): `@Mod(raidsenhanced)` plus deferred registration for animation, particles, entities, config, models, sounds and items.
- [mixin/RaidMixin.java](https://github.com/FINDERFEED/raidsenhanced/blob/6354ebf97faaeba79affaf7e71d01ed5ae651e85/src/main/java/com/finderfeed/raids_enhanced/mixin/RaidMixin.java): `@Mixin(Raid.class)` injects at a specific `Optional.empty()` invocation inside `Raid.spawnGroup`; forwards `groupsSpawned + 1`, `numGroups` and spawn position.
- [REMixinHandler.java](https://github.com/FINDERFEED/raidsenhanced/blob/6354ebf97faaeba79affaf7e71d01ed5ae651e85/src/main/java/com/finderfeed/raids_enhanced/REMixinHandler.java): act only when `currentGroup == numGroups`, add exactly one extra boss family selected by raid Bad Omen level: 2 Drill, 3 Golem, 4 Zapper, >=5 Blimp. Levels 2–4 call `Raid.joinRaid`; Blimp is positioned at motion-blocking height +25 and registered through fresh entity spawn + `addWaveMob`.
- A level-5 raid **does not** accumulate all four mini-boss types through this branch. The exact Mixin injection point is a compatibility-sensitive seam, not a general Forge event.

## Entity and combat packages

| Source owner | Main entities / systems | Role |
|---|---|---|
| `content/entities/FDRaider.java` | `FDRaider extends Raider`, implements `AnimatedObject` | shared FDLib entity model/attachment sync and NBT persistence |
| `content/entities/raid_blimp/` | `RaidBlimp`, `RaiderBomb` | airship tactical tick, bombing, death parts |
| `content/entities/raid_blimp/navigation/` | `RaidBlimpMoveControl`, `RaidBlimpPathNavigation` | flight motion and node advancement |
| `content/entities/raid_blimp/cannons/` | `RaidBlimpCannonsController`, `RaidBlimpCannon`, projectile, bone controller | independent turret targeting, firing, pose |
| `content/entities/raid_drill/RaidDrill.java` | `RaidDrill` | burrow cycles, spawn positions, spawning raiders |
| `content/entities/golem_of_last_resort/GolemOfLastResort.java` | `GolemBombsAttack`, `GolemMeleeAttackGoal` | bombing, melee, destructible terrain |
| `content/entities/engineer/ZapperIllager.java` | `BallLightningRangedAttack`, `LightningsAttack`, `LaserAttackGoal` | ranged, radial and sustained beam attacks |
| `content/entities/player_blimp/` | `PlayerBlimpEntity`, `FDVehicle`, rotating packet | 2-seat piloted vehicle |

All relative locations above are under `src/main/java/com/finderfeed/raids_enhanced/`. See [source at pinned commit](https://github.com/FINDERFEED/raidsenhanced/tree/6354ebf97faaeba79affaf7e71d01ed5ae651e85/src/main/java/com/finderfeed/raids_enhanced/content/entities).

## Attributes set in registration source

The initial `REEntities.registerAttributes` builder includes:

| Entity | Max health | Armor | Other attributes |
|---|---:|---:|---|
| `RaidBlimp` | 200 | inherited/default | attack 7, follow 40, flying speed 0.3 |
| `GolemOfLastResort` | 200 | 8 | follow 30, movement speed 0.3 |
| `ZapperIllager` | 100 | 8 | attack 7, knockback resistance 0.8 |
| `RaidDrill` | 5 | 8 | knockback resistance 1.0 |

See [REEntities.java](https://github.com/FINDERFEED/raidsenhanced/blob/6354ebf97faaeba79affaf7e71d01ed5ae651e85/src/main/java/com/finderfeed/raids_enhanced/init/REEntities.java). Values describe registration source, not effective runtime after other modifiers.

## Mixin and functional seams

The `raidsenhanced.mixins.json` explicitly registers:
- common: `RaidMixin`, `PlayerMixin`, `EntityMixin`;
- client: `ClientPacketListenerMixin`, `LocalPlayerMixin`.

`PlayerMixin` and `EntityMixin` modify rider pose/crouching; `LocalPlayerMixin` feeds vehicle input; `ClientPacketListenerMixin` hooks passenger packet/narration logic. This is a broader compatibility surface than a fully self-contained boss.

## Supporting registries

- `init/REModels.java` uses FDLib `FDModelInfo` for Bedrock geometry/model IDs.
- `init/REAnimations.java` registers ship, golem, Zapper, drill, and piloted-airship animations.
- `REClientEvents.java` wires client renderers.
- `init/REParticles.java`, `init/RESounds.java`, `init/REItems.java` back combat FX and items.
- The source resource tree has 9 Bedrock `.geo.json` model files, 5 main Bedrock animation JSON files, additional particle JSON and sprite textures, and 15 audio OGG files. Do not copy their contents.

## Primary observations and review boundary

`Raid.spawnGroup` Mixin ordering should be tested against other raid-rewriter mods; player vehicle packet actions need authorization checks; FDLib attachment/network behavior needs its own source review. These are *static review items*, not proven bugs or runtime failures.
