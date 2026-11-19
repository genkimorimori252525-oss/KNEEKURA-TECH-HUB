# Olympus! — Harpy flight AI research

## Scope

- Target: **Olympus!**
- Focus: Harpy / Elite Harpy flight AI, combat flight and 3D navigation
- TECH-HUB adaptation anchor: **Minecraft 1.20.1 + Forge 47.4.0**
- Research status: **TARGETED_FLIGHT_AI_MAPPED**
- Whole-target status: **IN_PROGRESS / NOT COMPLETE**
- Research date: 2026-10-04

This workspace records reusable engineering techniques. No Minecraft implementation code is changed.

## ANCHOR

Public distribution:

- CurseForge project: `1667111`
- Release: `Olympus! 1.0.8-1.20.1`
- File ID: `8962807`
- File: `olympusmythology-forge-1.20.1-1.0.8.jar`
- Loader: Forge
- Published: 2026-09-24

Pinned source:

- repository: `Xylonity/Olympus`
- branch: `v1.20.1`
- exact revision: `dcaccaa01abb4b84191c0173ba0996acd26c1f95`
- version: `1.0.8`
- Minecraft: `1.20.1`
- Forge: `47.4.0`
- Java: `17`
- source tree: 761 entries / 615 blobs / 121 Java files / 474 resource files
- Harpy-related Java surface: 16 files

This is an unusually strong ANCHOR because it matches the TECH-HUB Minecraft/loader line directly.

## FRONTIER

- source branch: `v1.21.1`
- revision: `31237b1e1e3abb29c7760c2a7596f320605ce75d`
- version: `1.0.9`
- Minecraft: `1.21.1`
- Java: `21`
- Forge: `52.0.28`
- NeoForge: `21.1.150`

The Harpy Flight/Dash/Retreat/Dodge/Projectile/Melee Goals and the custom MoveControl/Navigation
are source-equivalent between the pinned 1.20.1 and 1.21.1 tracks apart from loader-path relocation
and small surrounding entity/API adaptations. The flight design is therefore stable across these tracks.

## License boundary

The upstream repository states:

- source code: GPLv3 plus an additional attribution / same-terms clause
- assets: All Rights Reserved

TECH-HUB records algorithms, contracts, provenance and lessons. Direct source incorporation should
only happen deliberately under compatible licensing terms.

## Core result

Olympus does not implement one monolithic "flight AI". The Harpy is split into three movement layers:

1. **Goal layer** — chooses why/where to fly.
2. **Navigation layer** — chooses direct 3D flight or a real flying Path.
3. **MoveControl layer** — converts the current destination into smooth 3D velocity and rotation.

Special attacks may temporarily bypass that stack. The dash uses a scripted curved trajectory,
then explicitly returns to normal collision/navigation state.

The most reusable discoveries are:

- terrain-relative idle hover band;
- target-relative combat altitude;
- tangent orbit + radial correction steering;
- short steering commitments to suppress jitter;
- direct-flight fast path with pathfinding fallback;
- safe path-node shortcutting;
- distance-based slowdown + inertial velocity interpolation;
- combat-facing yaw decoupled from movement direction;
- relative-velocity projectile interception prediction;
- bounded lateral dodge search;
- quadratic-Bezier dash with approximate arc-length speed normalization;
- swept-volume hit detection for high-speed movement;
- bounded 3D free-position search and post-collision escape recovery.

Detailed report:
[FLIGHT-AI-RESEARCH-2026-10-04.md](FLIGHT-AI-RESEARCH-2026-10-04.md)

Bounded source-history review:
[FAILURE-REPAIR-HISTORY.md](FAILURE-REPAIR-HISTORY.md)

Pinned source inventory:
[SOURCE-INVENTORY-2026-10-04.json](SOURCE-INVENTORY-2026-10-04.json)

## Important non-findings

- Harpies do **not** have a takeoff/landing state machine.
- Gravity is disabled continuously; they are permanent aerial actors.
- No flock/cohesion/separation planner was found.
- No bank-angle or body-pitch steering was found; locomotion orientation is primarily yaw.
- Dash movement is not ordinary obstacle avoidance: it temporarily uses `noPhysics=true`.
- No runtime benchmark or automated test suite was found in the pinned source tree.
