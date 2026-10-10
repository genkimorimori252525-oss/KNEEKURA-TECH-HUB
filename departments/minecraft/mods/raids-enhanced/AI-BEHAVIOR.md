# Raids: Enhanced — four-mini-boss AI and attack map

**Basis:** the original author's [Minecraft 1.20.1 Forge source at `6354ebf97faaeba79affaf7e71d01ed5ae651e85`](https://github.com/FINDERFEED/raidsenhanced/tree/6354ebf97faaeba79affaf7e71d01ed5ae651e85). **No JAR/runtime observation in this pass**.

## 1. Raid-wide actor selection

`RaidMixin` calls `REMixinHandler.raidMixin` inside the final spawn group only. Bad Omen 2 → Drill, 3 → Golem, 4 → Zapper, 5+ → Blimp. 1.20.1 `Raid` wave bookkeeping is reused; Blimp has distinct placement and registration due to flight altitude. Thus source explicitly selects **one** special boss archetype rather than accumulating them.

Primary locator: [REMixinHandler.java](https://github.com/FINDERFEED/raidsenhanced/blob/6354ebf97faaeba79affaf7e71d01ed5ae651e85/src/main/java/com/finderfeed/raids_enhanced/REMixinHandler.java) and [mixin/RaidMixin.java](https://github.com/FINDERFEED/raidsenhanced/blob/6354ebf97faaeba79affaf7e71d01ed5ae651e85/src/main/java/com/finderfeed/raids_enhanced/mixin/RaidMixin.java).

## 2. Raid Blimp — airborne approach and six independent guns

- The mob extends `FDRaider`, whose animation attachment layer is driven by FDLib; `registerGoals()` is empty and operational behavior is in `tick()`.
- On spawn the special raid branch positions the airship at terrain height +25. Movement is split between moving toward raid center, responding to nearby players/attackers and gradually descending if no target exists.
- `RaidBlimpMoveControl` extends `FlyingMoveControl`; it uses facing-direction velocity, a 6-block arrival band, velocity damping of 0.95 near targets. `RaidBlimpPathNavigation` skips/path-selects nodes with block ray tests, recalculation cooldown 10 ticks.
- `RaidBlimpCannonsController` owns six cannon controllers (three on each flank), sees living targets inside a 35-radius, 100-high cylinder, and attempts to avoid assigning the same living target to different cannons. Each cannon enforces range 40 and ray obstruction tests; firing cooldown default in controller: 30 ticks.
- A **separate seventh attack path** checks targets directly beneath at most ~40 blocks downward and 5 blocks in horizontal radius, and animates bomb release. It is not one of six side cannons.
- Combat target policy explicitly admits villagers, survival players and iron golems.
- Tactical note: a multi-gun system should separate **shared target census → weapon-specific FOV/LOS → assignment → cadence → per-cannon bone pose and projectile**.

Locators: [content/entities/raid_blimp/RaidBlimp.java](https://github.com/FINDERFEED/raidsenhanced/blob/6354ebf97faaeba79affaf7e71d01ed5ae651e85/src/main/java/com/finderfeed/raids_enhanced/content/entities/raid_blimp/RaidBlimp.java), [content/entities/raid_blimp/navigation/RaidBlimpMoveControl.java](https://github.com/FINDERFEED/raidsenhanced/blob/6354ebf97faaeba79affaf7e71d01ed5ae651e85/src/main/java/com/finderfeed/raids_enhanced/content/entities/raid_blimp/navigation/RaidBlimpMoveControl.java), [content/entities/raid_blimp/navigation/RaidBlimpPathNavigation.java](https://github.com/FINDERFEED/raidsenhanced/blob/6354ebf97faaeba79affaf7e71d01ed5ae651e85/src/main/java/com/finderfeed/raids_enhanced/content/entities/raid_blimp/navigation/RaidBlimpPathNavigation.java), [content/entities/raid_blimp/cannons/RaidBlimpCannonsController.java](https://github.com/FINDERFEED/raidsenhanced/blob/6354ebf97faaeba79affaf7e71d01ed5ae651e85/src/main/java/com/finderfeed/raids_enhanced/content/entities/raid_blimp/cannons/RaidBlimpCannonsController.java), [content/entities/raid_blimp/cannons/RaidBlimpCannon.java](https://github.com/FINDERFEED/raidsenhanced/blob/6354ebf97faaeba79affaf7e71d01ed5ae651e85/src/main/java/com/finderfeed/raids_enhanced/content/entities/raid_blimp/cannons/RaidBlimpCannon.java), [content/entities/raid_blimp/cannons/RaidBlimpCannonBonesController.java](https://github.com/FINDERFEED/raidsenhanced/blob/6354ebf97faaeba79affaf7e71d01ed5ae651e85/src/main/java/com/finderfeed/raids_enhanced/content/entities/raid_blimp/cannons/RaidBlimpCannonBonesController.java).

## 3. Raider Drill — choreographed transit rather than real tunnel routing

- The actor maintains `reDigTicker`, `raidersSpawningTicker`, `raidersToSpawn`, `idleTicker` and re-burrow count.
- Burrow animation → temporarily invisible → candidate generation and teleport → unburrow animation → raider emission. **Actual terrain excavation/tunnel pathfinding is not proven**: the verified code teleports between validated surfaces during the burrow state.
- Surface search uses X/Z candidate offsets in a -25..25 square around the origin, skipping inner square and using directional preference, heightmap, fluid check, solid ground and two free body-height blocks before selecting a random valid site.
- A Pillager or Vindicator is emitted every 60 ticks while scheduled; default count = 2–3 per emerge sequence.
- Defaults in `REConfig`: automatic re-burrow idle threshold 200 ticks (10 s), automatic re-burrow allowance **3**. The distribution-page narrative references **5**; unresolved until distributed artifact and/or runtime compared.
- Damage path implements hit-count logic and scripted relocation rather than standard health-per-swing. The registered max health is 5 but `hurt()` alters hits and effective applied damage, so DO NOT interpret health 5 as five normal damaging hits.

Source: [content/entities/raid_drill/RaidDrill.java](https://github.com/FINDERFEED/raidsenhanced/blob/6354ebf97faaeba79affaf7e71d01ed5ae651e85/src/main/java/com/finderfeed/raids_enhanced/content/entities/raid_drill/RaidDrill.java), [REConfig.java](https://github.com/FINDERFEED/raidsenhanced/blob/6354ebf97faaeba79affaf7e71d01ed5ae651e85/src/main/java/com/finderfeed/raids_enhanced/REConfig.java).

## 4. Golem of Last Resort — mixed melee + mortar and terrain interaction

- Separate `Goal` classes: `GolemBombsAttack` and `GolemMeleeAttackGoal`, plus vanilla style stroll/look/target goals.
- The melee controller chooses standard strike, heavy strike or whirlwind, with different animation tick windows and hit geometry. The heavy strike uses a forward arc and spawns animated debris; whirlwind uses a cylinder-area scan and can disable a player's shield.
- Mortar style launches projectiles toward player/target positions using a computed projectile velocity and a time-of-flight parameter. Animation, particles/sounds and camera shake are coordinated against explicit ticks.
- Block destruction route is gated on Forge mob-griefing, block destruction predicate, vanilla Wither destruction predicate, and `onEntityDestroyBlock`. It is **not** evidence that every claim/protection mod is respected.
- Area loops in several attacks exclude the Golem entity itself; verify ally/faction filtering under actual `doHurtTarget` call and damage events before treating friendly fire as resolved.

Source: [content/entities/golem_of_last_resort/GolemOfLastResort.java](https://github.com/FINDERFEED/raidsenhanced/blob/6354ebf97faaeba79affaf7e71d01ed5ae651e85/src/main/java/com/finderfeed/raids_enhanced/content/entities/golem_of_last_resort/GolemOfLastResort.java).

## 5. Zapper — ranged orb, radial lightning and beam as independent Goals

- AI registers `BallLightningRangedAttack`, `LightningsAttack` and `LaserAttackGoal`.
- Radial lightning triggers in expanding concentric rings: radii **4, 8, 12, 16** with counts **4, 8, 12, 16** across attack ticks **20, 25, 30, 35**; ring orientation alternates.
- Laser follows prepare/charge/active/recover phases; beam can persist up to ~100 ticks within the controlling goal. Attack ray endpoint is recalculated via look direction and block clip up to 30 units, and living entity intersections checked every other tick in the active band.
- Server-synced beam/target pose state and FDLib animations separate gameplay attack from client rendering, though FDLib carries much of this infrastructure.
- This is useful as **attack-phase choreography**, not a certified runtime timeline or benchmark.

Source: [content/entities/engineer/ZapperIllager.java](https://github.com/FINDERFEED/raidsenhanced/blob/6354ebf97faaeba79affaf7e71d01ed5ae651e85/src/main/java/com/finderfeed/raids_enhanced/content/entities/engineer/ZapperIllager.java), [content/entities/ball_lightning/BallLightningEntity.java](https://github.com/FINDERFEED/raidsenhanced/blob/6354ebf97faaeba79affaf7e71d01ed5ae651e85/src/main/java/com/finderfeed/raids_enhanced/content/entities/ball_lightning/BallLightningEntity.java), [content/entities/vertical_lightning_strike/VerticalLightningStrikeAttack.java](https://github.com/FINDERFEED/raidsenhanced/blob/6354ebf97faaeba79affaf7e71d01ed5ae651e85/src/main/java/com/finderfeed/raids_enhanced/content/entities/vertical_lightning_strike/VerticalLightningStrikeAttack.java).

## 6. Player-piloted airship (bonus non-boss actor)

- `PlayerBlimpEntity` allows at most two passengers; controls forward/backward, ascent/descent and left/right rotation with accumulated/limited rotational speed and damping.
- Local input is read through `LocalPlayerMixin`; steering packet uses entity ID and rotation direction. Vehicle movement should be tested server-side for rider authority, latency and input divergence.
- Unlike Blimp's AI move controller, this is a distinct **vehicle flight / acceleration** model and merits separate WarWareWing research.

Source: [content/entities/player_blimp/PlayerBlimpEntity.java](https://github.com/FINDERFEED/raidsenhanced/blob/6354ebf97faaeba79affaf7e71d01ed5ae651e85/src/main/java/com/finderfeed/raids_enhanced/content/entities/player_blimp/PlayerBlimpEntity.java), [content/entities/player_blimp/PlayerBlimpRotatingPacket.java](https://github.com/FINDERFEED/raidsenhanced/blob/6354ebf97faaeba79affaf7e71d01ed5ae651e85/src/main/java/com/finderfeed/raids_enhanced/content/entities/player_blimp/PlayerBlimpRotatingPacket.java).

## Status

All details: **SOURCE-CONFIRMED at pinned ANCHOR**, never `RUNTIME-CONFIRMED`. Values may diverge in the packaged JAR or after configuration changes.
