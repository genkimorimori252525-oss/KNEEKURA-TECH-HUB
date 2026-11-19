# Olympus! Harpy — bounded failure / repair history

## Scope

This is a source-history review focused only on flying behavior and collision.

It does not claim to be a complete issue history. The public repository exposes useful incremental
commits, but this pass did not reproduce the historical bugs in-game.

Evidence is therefore:

- source diff: **DIRECT_OBSERVATION**
- commit message: **AUTHOR_CLAIM**
- engineering lesson: **INFERENCE**

## 1. Dedicated aerial movement replaces generic movement

Commit:
`d9e1917638f4bd4e58ceac4ecbed790f7c27f875`
— "Updated flight logic for the harpy"

Observed change:

- no-gravity invariant added;
- FlyingMoveControl installed;
- FlyingPathNavigation installed;
- FLYING_SPEED increased;
- idle aerial Goal added;
- terrain-relative height band introduced.

Lesson:

A flying entity should not be a ground mob with occasional Y velocity. Establish an explicit
airborne locomotion contract first.

## 2. Custom navigator/control after baseline flight

Commit:
`d5cbe9d364de0126ca85d7397919e55030cb9d0a`
— "Enhanced flying navigator for teh harpy"

Observed change:

- new HarpyFlyingMoveControl;
- new HarpyFlyingNavigation;
- direct destination fast path;
- fallback to FlyingPathNavigation;
- bounded path-node shortcut;
- inertial velocity blending;
- target-facing yaw during combat;
- endpoint slowdown.

Lesson:

Once basic flight works, the next quality jump comes from reducing unnecessary A* and smoothing
the final steering rather than building a wholly new pathfinder.

## 3. Goal/navigation responsibility split

Commit:
`1661d88b071db8ff31628d8aac038f99c17e8088`
— "Adapted flight goal of the harpy to the new navigator"

Before:

- idle Flight Goal itself performed a ray/collision line-clear test;
- Goal directly drove MoveControl.

After:

- Goal validates candidate occupancy;
- Navigation owns line/path reachability;
- Goal starts and stops Navigation;
- direct flight and path fallback become transparent to Goal.

Lesson:

`Goal = what point is desirable`

`Navigation = how to reach it`

Duplicating path-clearance logic in the Goal makes later navigation upgrades harder.

## 4. Bounding box reduced

Commit:
`94591edf94243e2914f85e6f692a7199cee720e8`
— "Reduced harpy bbox"

Observed change:

- 2.0 x 2.0 -> 1.4 x 1.6.

Lesson:

A flying model's visual wing span should not automatically be its navigation collision footprint.
An oversized bbox can make otherwise valid air corridors look impossible and increases embedding
risk near terrain.

## 5. Embedded collision recovery added

Commit:
`c323fbc68b52bc479fb25ef279111ea1b1d55aa4`

Commit message explicitly states:
"enhanced collision detection to avoid staying inside blocks".

Observed change:

- combat free-position search;
- local escape search;
- per-tick embedded bbox check;
- navigation/motion cancellation before reposition;
- ordered vertical offsets and expanding horizontal rings.

Lesson:

Even a correct navigator cannot prevent every invalid position. Scripted movement, changing world
geometry or edge-case collision can strand a flying entity. Recovery must exist outside the
planner.

## 6. Combat altitude moved from terrain frame to target frame

Commit:
`2f9ec295d54218c4bbd6ecc89cb4962a007ab6cd`
— "Harpy logic now uses the target position to compute the altitude variation"

Observed changes:

- dash staging now uses `findFreeCombatPosition`;
- dash exit no longer clamps against terrain height;
- projectile strafe uses target-relative altitude;
- orbit altitude uses target eye height;
- all these paths share local free-space resolution;
- dash cleanup also invokes escape recovery.

Lesson:

The right coordinate reference depends on the behavior.

- idle cruising -> terrain-relative
- fighting -> target-relative
- formation -> group/leader-relative
- authored maneuver -> path/curve-relative

A single global altitude rule creates bad behavior when the reference object changes.

## 7. Dash phases through geometry

Current source observation:

- DASHING sets `noPhysics=true`;
- the Bezier path is not collision-traced each tick;
- collision is restored at the end;
- `escapeFromBlocks` repairs a bad final state.

This is not necessarily a historical bug: it is a current tradeoff.

Lesson:

There are two different classes of movement:

1. **navigational locomotion** — must respect world collision continuously;
2. **scripted attack locomotion** — may prioritize authored timing/shape and need explicit recovery.

Do not generalize the second into the first.

## 8. Attack tunneling handled separately from world collision

Current Dash uses a swept AABB expanded along movement for target damage.

Lesson:

World collision and hit registration are separate. Even if a special move intentionally phases
through blocks, high-speed hit registration still needs swept-volume logic or it can skip entities.

## 9. Source lineage / simplification

Olympus comments identify earlier Xylonity Companions code as inspiration.

Bounded comparison:

- Companions' FlyingNavigator includes custom voxel traversal, a pathability cache and a custom
  BonusPathFinder;
- Olympus retains direct-flight and shortcut concepts but uses vanilla `canMoveDirectly` and normal
  FlyingPathNavigation fallback.

Lesson:

Simplification is itself a repair strategy. Use vanilla primitives when they satisfy the contract;
add caches/custom pathfinders only after measured need.

## 10. Evidence gaps

Not established:

- exact player-visible symptom for each pre-release source revision;
- FPS/TPS/pathfinding benchmark before vs after;
- issue/PR discussion chain;
- automated regression tests;
- released JAR/source binary equality.

Status: **PARTIAL / SOURCE-HISTORY-BACKED**.
