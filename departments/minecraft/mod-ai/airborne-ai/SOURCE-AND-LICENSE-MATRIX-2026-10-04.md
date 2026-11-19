# Source and license matrix — Airborne AI research

This is a provenance map for the bounded cross-MOD study. It is not a binary-equivalence report.

## Olympus

- Repository/source provenance: existing TECH HUB Olympus capture.
- ANCHOR: v1.0.8, Minecraft 1.20.1, Forge 47.4.0, upstream source revision `dcaccaa01abb4b84191c0173ba0996acd26c1f95`.
- Primary document: `departments/minecraft/mods/olympus/FLIGHT-AI-RESEARCH-2026-10-04.md`.
- Use here: baseline Goal → Navigation → MoveControl separation, direct-flight/path fallback, orbit, dodge, dash, recovery.

## Saint's Dragons

- Repository: https://github.com/LilRicefield/saints-dragons
- Branch studied: `1.20.1`.
- Searched head during this study: `fe3b5605bf5228111c3f705437794291733333c4`.
- `gradle.properties`: Minecraft 1.20.1, Forge 47.4.10, mod 0.9.85.
- License boundary: root `LICENSE.md` is dual-license:
  - source code/build/config/documentation: MIT;
  - art/audio assets: All Rights Reserved.
- Do not summarize this as "the whole MOD is MIT".
- Entry points:
  - `DragonLandingSites`
  - `AsyncFlightController`
  - `AsyncFlightPathResolver`
  - `AsyncFlightMovementExecutor`
  - `DragonFlightSpace`
  - `DragonCombatFlightState`
  - `AirCombatMovementBehaviour`
  - `AirToGroundTransitionBehaviour`
  - `DragonFlightMovementRecoveryBehaviour`
  - `NulljawPackCombatCoordinator`
  - `DraconianSwarmCoordinator`

## Alex's Mobs

- Repository: https://github.com/AlexModGuy/AlexsMobs
- Branch studied: `1.20`.
- Searched revision during this study: `09755dade2cfbdf14839e026d3af446f9d3ff843`.
- Source metadata observed: MOD version 1.22.9, Forge >=47.1.0.
- License: LGPL-family declaration in repository metadata.
- Primary specimen:
  - `EntityCrimsonMosquito`
    - `FlyTowardsTarget`
    - `FlyAwayFromTarget`
    - `RandomFlyGoal`
    - nested MoveControl
  - generic `FlightMoveController`
- Scope: technique extraction, not an exhaustive Alex's Mobs flying-entity census.

## Fowl Play

- Repository: https://github.com/aqariio/Fowl-Play
- Branch studied: `1.20.1`.
- License: MIT.
- 1.20.1 Forge release line observed separately; branch-to-distributed-binary identity was not proven.
- Exact fetched blobs used as anchors:
  - `BirdMoveControl.java`: `4410dc311fbbfae8fb5d1e373a468ec46ee7c5c4`
  - `GuidedFlocking.java`: `129da73c599352964d8324294414c270facb7a87`
  - `LeaderlessFlocking.java`: `1be8e42f3558c6078ce2184d60689b348bcfaaf4`
- Other entry points:
  - `ExtendedSchedule`, `FPSchedules`
  - `BirdEntity`, `FlyingBirdEntity`
  - `FlightNavigation`, `BirdRandomPos`
  - `SetRandomFlightTarget`, `SetPerchWalkTarget`
  - `FlightBehaviours`, `CompositeBehaviours`

## Cosy Critters & Creepy Crawlies

- Repository: https://github.com/PigCart/cosy-critters
- Tree observed: current multi-version `main`, revision `1403312ea3092f1583668b954c00e621afae9dba`.
- License: MIT.
- Main entry points:
  - `src/main/java/pigcart/cosycritters/particle/BirdParticle.java`
  - `ConfigData.BirdOptions`
- Important evidence boundary:
  - current source tree demonstrates the algorithm;
  - 1.20.1 release history corroborates that the bird-flying/Boids/landing behavior existed on the 1.20.1 line;
  - this study does not claim byte-for-byte identity between current main and an old 1.20.1 artifact.
- The bird is a **client particle**, not an authoritative server Mob.

## Ice and Fire

- Repository: https://github.com/AlexModGuy/Ice_and_Fire
- Branch studied: `1.20`.
- License: LGPL-3.0 in repository LICENSE.
- Primary entry points:
  - `IafDragonFlightManager`
  - `EntityDragonBase`
  - `DragonAIReturnToRoost`
  - `DragonAIEscort`
  - `EntityHippogryph`
- This study does not assert that the branch is binary-identical to one particular distributed 1.20.1 JAR.

### Ice and Fire: Dragon Fix

- Separate compatibility/repair addon used only as repair-history evidence in this synthesis.
- Exact full source closure is not claimed here.
- Its published fixes are treated as author/release-history evidence, not as proof that every defect exists in every Ice and Fire build.

## Hostile Mobs and Girls

- Repository: https://github.com/Mechalopa/Hostile-Mobs-and-Girls
- Branch studied: `1.20.1`.
- Observed revision: `e39abcfb4648c89632b80afa74b1d082ef20ace8`.
- Metadata: Minecraft 1.20.1, Forge 47.4.2, mod 9.0.38.
- License: LGPL-3.0.
- Entry points:
  - `AbstractFlyingMonsterEntity`
    - `FlyingMonsterMoveControl`
    - `ChargeAttackGoal`
    - `MoveRandomGoal`
  - `GhastlySeekerEntity`
  - `DyssomniaEntity`
  - `MonolithEntity`
  - consumers include Banshee/Ghost/Hornet.
- Release 9.0.33 reports crashes in AI shared by several flying entities, but the inspected version-bump commit `fd26f67e1c2a6b7cfc7cc5fb6177e438259e93d2` contains only version metadata. The exact repair diff is therefore UNKNOWN in this study.

## Book of Dragons

- Player-facing 1.20.1 Forge project.
- License boundary: All Rights Reserved.
- Treatment here: **observation/changelog only**.
- No code or asset reuse is authorized or implied by this research.
- Only the public behavior history (flight strafe fixes, target-loss/LOS-search semantics) is used as a design hint.
