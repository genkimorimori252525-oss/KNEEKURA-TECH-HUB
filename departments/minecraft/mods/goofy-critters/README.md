# Goofy Critters — movement / locomotion research

## Scope

- Target: **Goofy Critters**
- Author: `min01`
- Focus: unusual locomotion, especially **Gestalt's multi-anchor hand movement**
- TECH-HUB adaptation anchor: Minecraft **1.20.1 + Forge**
- Research status: **TARGETED_MOVEMENT_ARCHITECTURE_MAPPED**
- Whole-target status: **IN_PROGRESS / NOT COMPLETE**
- Research date: 2026-10-05

This workspace records reusable movement techniques, provenance and failure/repair history.
It does **not** modify Minecraft implementation code.

## DISTRIBUTED ANCHOR

Public CurseForge distribution:

- CurseForge project: `1449738`
- file ID: `7553632`
- file: `goofycritters-1.0.0.jar`
- version: `1.0.0`
- Minecraft: `1.20.1`
- loader: Forge
- published: 2026-01-31
- license: GPLv3

Released-JAR SHA/source-byte equivalence is **NOT_ESTABLISHED**.

## RELEASE-ERA SOURCE CANDIDATE

- repository: `min2222/GoofyCritters`
- revision: `9188e5175828154bdae309dd352e16e338dc8089`
- date: 2026-01-31
- tree: 133 entries / 88 blobs / 58 Java files

This revision is from the release date and contains the core Gestalt hand-anchor locomotion, but it
is only a **SOURCE_CANDIDATE**. It is not asserted to be the exact source used to compile file
7553632.

## FRONTIER SOURCE

- repository: `min2222/GoofyCritters`
- branch: `main`
- revision: `96d01a7b7ceaa18c51ae0cb1e7dfac0c3d467956`
- source-declared version: `1.0.0`
- Minecraft: `1.20.1`
- Forge: `47.4.20`
- Java: `17`
- license: GPLv3
- tree: 142 entries / 97 blobs / 67 Java files
- repository state: archived/read-only

The FRONTIER is **22 commits ahead** of the release-era candidate and includes substantial
post-release movement-framework work. Those later systems must not be silently attributed to the
January distributed JAR.

## Entities

Source-backed:

- **Gestalt** — implemented
- **Gestalt Hand** — implemented helper/anchor entity
- **Eyes** — implemented

Public project plans mention **Masked**, but no `MaskedEntity` implementation was found in the
pinned source. Masked movement is therefore **NOT_ANALYZED / NOT_IMPLEMENTED_IN_PINNED_SOURCE**.

## Main result

Gestalt does not locomote like a normal Minecraft mob.

It has:

- `MOVEMENT_SPEED = 0`;
- no default movement Goals;
- no gravity;
- no path-following body movement.

Instead it creates up to sixteen independent hand entities, attaches them to full collision blocks,
and lets those anchors add impulses to the body.

Conceptually:

```text
desired direction / target
          |
          v
sample environment near target
          |
       raycast
          |
     world anchors
     /   |   |   \
 hand hand hand hand
    \    |    /
     force sum
          |
          v
   Gestalt deltaMovement
```

A hand farther than roughly six blocks pulls the body toward itself. A hand inside that radius
pushes the body away. The summed field produces the creature's unusual crawling / floating /
grappling motion.

The most important recovered technique is therefore:

> **Locomotion does not have to be a Path plus MoveControl. The environment itself can become a
> distributed set of temporary actuators.**

Detailed report:
[MOVEMENT-RESEARCH-2026-10-05.md](MOVEMENT-RESEARCH-2026-10-05.md)

Bounded source-history review:
[FAILURE-REPAIR-HISTORY.md](FAILURE-REPAIR-HISTORY.md)

Source inventory:
[SOURCE-INVENTORY-2026-10-05.json](SOURCE-INVENTORY-2026-10-05.json)

## Main reusable technologies

1. **Multi-anchor locomotion** — independent helper entities attach to world geometry.
2. **Target-biased anchor field** — desired travel direction changes where future anchors are
   sampled rather than directly setting body velocity.
3. **Piecewise anchor force** — far anchor pulls, near anchor pushes.
4. **Rolling anchor turnover** — old/far hands retract and are replaced.
5. **Detached actuator lifecycle** — extend -> anchor -> validate support -> retract/discard.
6. **Same actuator system for AI and player mount control**.
7. **Procedural limb reconstruction** between body and real world-space hand anchors.
8. **Whole-AABB voxel sweep path shortcutting** in the later general movement framework.
9. **Runtime movement-mode swapping** between ground/flying/swimming controls and navigators.
10. **Data-driven turn/radius/interval parameters** through `MovementData`.

## Important limits

- Gestalt has no strategic path planner.
- Anchors require full collision blocks in the pinned implementation.
- Open void / sparse-anchor environments have no formal reachability guarantee.
- Up to 16 helper entities exist per Gestalt.
- hand-owner resolution uses reflective entity lookup by UUID.
- the per-hand force path contains an undocumented nearly-equal `length > distanceTo` gate; do
  not copy it blindly.
- arm rendering cost grows with the total rendered hand/body span.
- no automated tests or runtime performance benchmark were found.
- later NoSpin/general movement work is FRONTIER evidence, not proven distributed-1.0.0 behavior.
