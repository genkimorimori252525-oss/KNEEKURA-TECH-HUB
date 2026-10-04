# Olympus! Harpy flight AI research — 2026-10-04

## 1. Research question

What makes Olympus!'s Harpy feel like a capable flying combat creature, and which parts can be
reconstructed for KNEEKURA's Minecraft 1.20.1 + Forge work?

Pinned ANCHOR:
`Xylonity/Olympus@dcaccaa01abb4b84191c0173ba0996acd26c1f95`

Evidence language:

- **DIRECT_OBSERVATION** — present in pinned source or commit diff.
- **AUTHOR_CLAIM** — public project/release text.
- **INFERENCE** — reusable engineering conclusion.
- **UNKNOWN** — not established by this pass.

## 2. Harpy movement architecture

The movement stack is layered.

```text
Goal
  decides tactical intent / target point
        |
        v
HarpyFlyingNavigation
  clear line? -> direct target
  blocked?    -> FlyingPathNavigation
        |
        v
HarpyFlyingMoveControl
  wanted point -> smoothed velocity -> yaw
        |
        v
Entity physics
```

The special dash deliberately leaves this stack:

```text
normal navigation
   -> prepare
   -> stop navigation
   -> noPhysics scripted curve
   -> swept hit test
   -> restore collision
   -> escapeFromBlocks
   -> normal AI
```

This separation is the central reusable pattern.

## 3. Entity-level flight contract

**DIRECT_OBSERVATION** — `HarpyEntity`:

- installs `HarpyFlyingMoveControl`;
- returns `HarpyFlyingNavigation` from `createNavigation`;
- sets no-gravity in construction and again every tick;
- resets fall distance every tick;
- cannot take fall damage;
- while normal collision is active, every server tick checks whether its bounding box is embedded
  and attempts recovery.

Locators:

- `HarpyEntity.java#L99-L107`
- `HarpyEntity.java#L132-L161`
- `HarpyEntity.java#L172-L184`
- `HarpyEntity.java#L219-L263`

Harpy dimensions in the current 1.20.1 registry are 1.4 x 1.6 blocks.

**INFERENCE:** for a permanently aerial hostile, make "airborne" the entity's invariant instead of
continually fighting ground gravity from each Goal. Tactical Goals then only decide destinations.

## 4. Goal priority is the tactical scheduler

The Harpy registers:

| Priority | Goal | Purpose |
|---:|---|---|
| 0 | ProjectileDodge | emergency evasive movement |
| 1 | Melee | close attack |
| 2 | Projectile | ranged attack + strafe |
| 2 | Dash | special curved charge |
| 3 | Retreat | continuous combat orbit |
| 8 | Flight | idle hover/wander |

Target acquisition remains separate.

Because MOVE/LOOK flags are used on the tactical Goals, priority becomes a practical arbitration
mechanism: emergency dodge can take movement from retreat/orbit; special attacks can replace the
baseline combat movement; idle flight only owns movement when no target exists.

**INFERENCE:** a flying fighter can remain understandable if the default orbit is the "background"
behavior and every exceptional maneuver is a higher-priority temporary owner of movement.

## 5. Idle flight: terrain-relative hover band

`HarpyFlightGoal` runs only without a live target.

Constants:

- minimum height over ground: **3 blocks**
- horizontal wander range: **6 blocks**
- base hover time: **25 ticks**
- minimum travel commitment: **30 ticks**

### Destination generation

Up to eight attempts are made.

For each attempt:

1. choose X/Z within +/-6 blocks;
2. read `MOTION_BLOCKING_NO_LEAVES` ground height at that column;
3. choose desired Y from current Y +/-2;
4. clamp Y to **ground+3 .. ground+6**;
5. reject the destination if the translated Harpy bbox collides.

### Required lift

Before random wandering, if current Y is below ground+3 (within a 0.25 tolerance), it asks for a
vertical destination at the minimum safe height.

This is the closest thing Olympus has to "takeoff".

### Hover

Hovering:

- stops MoveControl;
- damps current velocity by **0.55**;
- sets animation/state back to idle.

**Technique:** represent idle aerial life as alternating:

`travel commitment -> damped hover -> travel commitment`

rather than randomizing the target every tick.

## 6. There is no landing system

**DIRECT_OBSERVATION:** no Harpy landing/takeoff Goal, grounded state, gravity restoration or
on-ground transition was found. `setNoGravity(true)` is reasserted every tick.

Therefore:

- "takeoff" = required lift when too close to terrain;
- "landing" = **not implemented**.

**INFERENCE:** this design is excellent for creatures that should always hover, but not sufficient
for birds/dragons that sleep, perch or land. A KNEEKURA reusable flight framework should keep
`AIRBORNE_PERMANENT` separate from `GROUND_AIR_TRANSITIONAL`.

## 7. Combat flight changes reference frame

Idle flight is ground-relative. Combat flight is **target-relative**.

`HarpyEntity.findFreeCombatPosition` clamps preferred Y between:

- target bounding-box minimum Y + 0.35;
- target eye Y + 3.0.

It then searches nearby vertical offsets and horizontal rings for a collision-free Harpy bbox.

**Why this matters:** a terrain heightmap can be a bad combat reference when the target is on a
ledge, staircase, floating structure or steep mountain. The combatant cares about the opponent's
body, not an unrelated terrain column.

This target-relative change is explicitly visible in upstream commit `2f9ec29`.

## 8. Bounded 3D free-position resolver

The Harpy has one shared local resolver used by combat maneuvers.

For combat:

- ordered vertical offsets from 0 through +/-2.5;
- up to **3 horizontal rings**;
- ring spacing: **0.75 block**;
- ring sampling count: `ring * 8`;
- Y is clamped to target-relative combat limits;
- first translated bounding box with `noCollision` wins.

For emergency escape:

- larger vertical offsets through +/-4;
- up to **5 horizontal rings**.

**Technique:** destination generation and pathfinding are different problems.

Before asking the navigator for an expensive route, first move an abstract desired point onto a
nearby collision-valid 3D point using a small deterministic search.

## 9. Orbit steering: tangent + radial correction

`HarpyRetreatGoal` is the normal combat movement.

Distance bands:

- inner: **4.5**
- nominal: **7.5**
- outer: **8.5**

Let `R` be the horizontal unit vector from target to Harpy.

The orbit tangent is a 90-degree rotation of R. Clockwise and counterclockwise variants are both
supported.

The flight vector is conceptually:

```text
flight = normalize(tangent + R * radialCorrection(distance))
```

Behavior:

- too close (<4.5): radial correction strongly points outward;
- too far (>8.5): correction points inward;
- near 7.5: mostly tangential with a small correction.

Movement speed also changes:

- too close: **1.8** modifier to escape pressure quickly;
- too far: **1.0**;
- normal orbit: **0.82**.

**INFERENCE:** this is a compact steering-controller version of "maintain combat radius" and is more
fluid than repeatedly choosing random points around a circle.

## 10. Orbit anti-jitter measures

The orbit logic deliberately does not recompute everything every tick.

- one destination is kept for **8..14 ticks** while navigation remains healthy;
- clockwise/counterclockwise choice is kept for **45..100 ticks**;
- failed destination attempts may flip orbit direction;
- three variants are tried:
  1. normal tangent + radial correction;
  2. weaker tangent;
  3. mostly radial fallback;
- if all fail, Harpy coasts and damps velocity by **0.96**.

**Technique:** short commitment windows produce natural-looking continuous arcs and reduce expensive
path churn.

## 11. Combat altitude bobbing is de-synchronized

Orbit altitude:

`targetEyeY + 1.25 + sin((tickCount + entityId*13) * 0.09) * 0.65`

Each Harpy receives a deterministic phase from entity ID.

**Technique:** use a stable per-entity phase offset for cosmetic/steering oscillations so groups do
not rise and fall in lockstep.

## 12. Hybrid navigation: direct flight first, pathfinding only when needed

`HarpyFlyingNavigation.moveTo` first calls the inherited direct-movement clearance check.

### Clear direct route

- stop any old Path;
- keep the exact Vec3 target and speed modifier;
- each navigation tick rechecks direct clearance;
- each tick reissues the target to the MoveControl;
- within squared distance **0.36**, clear the direct target.

### Route becomes blocked

If the line stops being directly traversable:

1. retain the desired target;
2. clear direct-target mode;
3. ask normal `FlyingPathNavigation` to create a Path to the same point;
4. continue through vanilla flying path logic.

**Technique:** for open-air creatures, pathfinding should be the fallback, not the default.

A large share of flying movement is unobstructed. Direct steering avoids paying A* cost where a
straight line is already valid.

## 13. 3D path shortcuts

When a real Path exists, Olympus tries to skip nodes.

- considers at most **6 nodes ahead**;
- farther node must be within squared distance **144** (12 blocks);
- every skipped/intermediate node must have pathfinding malus >=0 and <8;
- current position must have direct movement clearance to the candidate node.

Then the next Path index jumps forward.

**Technique:** a flying Path is often geometrically over-detailed after the creature has cleared an
obstacle. Visibility-based node skipping can recover smooth open-air flight while retaining A*
around obstructions.

## 14. MoveControl: velocity target, not position teleport

`HarpyFlyingMoveControl` converts desired position into desired velocity.

### Endpoint slowdown

Inside **1.5 blocks**, speed is scaled by `distance / 1.5`, clamped to 0.2..1.0.

### Inertial interpolation

```text
targetVelocity = normalized(offset) * speedModifier * FLYING_SPEED
velocity = lerp(currentVelocity, targetVelocity, acceleration)
```

Acceleration factor:

- normal: **0.12**
- inside slowdown distance: **0.20**

If movement would overshoot the remaining displacement, velocity is clamped to the remaining
distance.

At <0.1 block distance:

- WAIT;
- damp velocity by **0.82**.

**Technique:** steering toward a target velocity produces smoother flight than directly overwriting
velocity with a normalized direction every tick.

## 15. Facing is decoupled from movement in combat

Outside combat, yaw follows horizontal movement.

With a live target, yaw instead follows the target's horizontal direction.

Yaw changes through `rotLerp(0.15)`.

This lets the Harpy visibly face the opponent while moving tangentially around them.

**Technique:** movement heading and aim heading should be separate concepts for strafing aerial
combatants.

No body roll/bank or velocity-derived pitch is present.

## 16. Ranged attack strafe reuses the flight framework

During `HarpyProjectileGoal`:

- Harpy looks at the target;
- every ~8 ticks or when navigation completes, it chooses a lateral point;
- lateral direction is tangent to the target-Harpy radial line;
- desired Y is target eye + 1.25;
- `findFreeCombatPosition` moves that ideal point to a collision-valid nearby point;
- failed navigation flips clockwise/counterclockwise.

**Technique:** attack Goals should ask the shared flight positioning system for a legal tactical
point rather than implement their own collision search.

## 17. Projectile dodge predicts interception

Priority-zero `HarpyProjectileDodgeGoal` scans projectiles within a 30-block inflated bbox.

It uses relative motion:

```text
relativePosition = harpyCenter - projectileCenter
relativeVelocity = projectileVelocity - harpyVelocity

time = dot(relativePosition, relativeVelocity) / |relativeVelocity|^2
```

Candidates must have:

- meaningful relative speed;
- time > 0;
- time <= **30 ticks**;
- predicted closest separation within Harpy radius + projectile radius + 1 block.

The lowest time-to-impact wins.

Then:

- remember that projectile for **60 ticks** so it is not reconsidered repeatedly;
- react only with **40% probability**;
- build a horizontal lateral vector perpendicular to projectile travel;
- randomly choose one side, then try the opposite;
- dodge target is **8 blocks** away;
- both destination bbox and block ray must be clear.

The actual dodge:

- immediately adds velocity along dodge direction (0.28);
- sends MoveControl toward the target at 1.5 modifier;
- lasts up to **9 ticks**;
- global next-dodge delay is **12 ticks**.

**Technique:** threat selection by time-to-impact is more useful than "nearest projectile", because
a close arrow moving away is not dangerous while a farther fast arrow may be.

## 18. Dash is a scripted cinematic locomotion mode

The dash has three phases:

1. PREPARING
2. DASHING
3. ENDING

It only starts for a visible target within squared distance 25..225 (5..15 blocks), outside the
shared special-attack chain delay.

### Preparation

Normal flying navigation stages Harpy roughly 4 blocks from the target at target-relative altitude.

### Curve

The dash path uses two quadratic Bezier segments:

```text
start -> inbound control -> target crossing
target crossing -> outbound control -> exit
```

The target crossing point is low near the target's body.

The exit point is approximately the same horizontal distance beyond the target as the initial
approach distance, at target eye + 1.75 adjusted by free-combat-position search.

Control handles are 2..5 blocks from the crossing point depending on approach length.

## 19. Dash speed is normalized against approximate curve length

The curve length is approximated with **24 samples**.

Each tick:

`progress += speed / approximateCurveLength`

This means a longer curve does not automatically finish in the same number of ticks as a short
curve. Progress is tied approximately to world-space speed.

Speed profile:

- first 18%: smoothstep acceleration 0.35 -> 1.1;
- middle: 1.1;
- final 22%: smoothstep deceleration 1.1 -> 0.12.

**Technique:** if a scripted curve is parameterized 0..1, approximate its arc length before using
"units per tick" speed. Otherwise the same progress increment produces wildly different world
speeds for curves of different sizes.

## 20. Dash hit detection uses swept volume

At high speed, checking overlap only at the new position can tunnel through the target.

Olympus expands the Harpy bounding box along the current movement vector and inflates it by 0.35.

If this swept region intersects the target bbox, damage is registered once.

A player shield can cancel the dash and start the ending phase immediately.

**Technique:** high-speed special movement needs swept collision/hit tests even when normal movement
does not.

## 21. Important dash constraint: noPhysics

During actual DASHING:

- navigation is stopped;
- MoveControl waits;
- ordinary collision flags are reset;
- `noPhysics = true`;
- delta movement follows the curve.

The curve itself is not continuously obstacle-checked.

Therefore this attack can phase through world collision. On completion or interruption:

- movement is stopped;
- `noPhysics=false`;
- `escapeFromBlocks()` is invoked.

**Boundary:** this is useful for a dramatic attack that must complete, but it is **not** a general
obstacle-avoidance solution. Do not use the dash locomotion contract as ordinary flight.

## 22. Embedded-entity recovery

`HarpyEntity.tick` calls `escapeFromBlocks` whenever normal collision is active.

If the slightly deflated current bbox collides:

1. search local free positions;
2. vertical offsets are tried in alternating +/- order through 4 blocks;
3. horizontal rings expand by 0.75 up to five rings;
4. first collision-free translated bbox wins;
5. stop navigation;
6. set MoveControl WAIT;
7. zero velocity;
8. set position to the free location.

**Technique:** flight systems need a recovery state independent of normal navigation. Teleports,
moving blocks, scripted attacks and desync can create invalid states no planner can smoothly solve.

## 23. Attack-state separation

The synchronized attack state controls animations and which movement Goals consider themselves
legal.

States include idle, fly, shot, dash preparing, dashing and dash ending.

There is also a shared special-attack delay of **60 ticks** after a successful projectile/dash
action, preventing specials from chaining immediately even though their individual Goal cooldowns
are separate.

**Technique:** combine:

- per-ability cooldown;
- shared category cooldown;
- explicit locomotion/animation phase state.

This prevents conflicting special maneuvers from composing accidentally.

## 24. Evolution / repairs

The source history is unusually informative.

### `d9e1917` — dedicated flight introduced

Moved Harpy from ordinary ground-style entity behavior to:

- no-gravity;
- higher flying speed;
- FlyingMoveControl/FlyingPathNavigation;
- terrain-relative idle flight Goal.

### `d5cbe9d` — custom navigation/control

Introduced the current:

- direct-flight fast path;
- FlyingPathNavigation fallback;
- safe node shortcut;
- inertial MoveControl;
- endpoint slowdown;
- combat-facing yaw.

The source comments attribute the design lineage to Xylonity's Companions project and vanilla Vex
movement ideas.

### `1661d88` — responsibilities moved into Navigation

The Flight Goal stopped doing its own line ray test and delegated movement/path clearance to the new
navigator. It also began stopping Navigation explicitly when travel ended.

**Lesson:** Goal chooses destination; Navigation proves/tracks reachability.

### `94591ed` — smaller Harpy bbox

2.0 x 2.0 -> **1.4 x 1.6**.

**Lesson:** entity dimensions are part of navigation design. A visually large flying model can need
a smaller gameplay collision envelope to navigate plausible gaps.

### `c323fbc` — embedded collision recovery

Commit message explicitly mentions enhanced collision detection to avoid staying inside blocks.
Added free combat point search and escape recovery.

### `2f9ec29` — combat altitude moved to target frame

Dash preparation, dash exit, ranged strafe and orbit stopped relying on local terrain height for
combat altitude and began using target-relative collision-valid positions.

**Lesson:** navigation reference frames should match the tactical relation being controlled.

## 25. Provenance lineage: Companions

Current source comments explicitly say:

- `HarpyFlyingMoveControl` is based on vanilla Vex movement and Companions' `GoldenAllayMoveControl`;
- `HarpyFlyingNavigation` is a simplified version of Companions' `FlyingNavigator`.

A bounded read of the linked Companions 1.20.1 files shows Olympus deliberately simplified the
older navigator:

- Companions has a custom voxel traversal cache and `BonusPathFinder`;
- Olympus uses vanilla `canMoveDirectly` plus normal `PathFinder`;
- Olympus keeps the high-value direct-flight and path-shortcut concepts while reducing custom
  infrastructure.

**INFERENCE:** this is a useful simplification pattern: retain the strategy that eliminates
unnecessary pathfinding, but prefer vanilla collision/path primitives until profiling proves a
custom voxel cache is necessary.

## 26. Performance characteristics visible in source

No runtime benchmark was performed, but the design contains explicit bounds:

- idle destination attempts: 8;
- combat local search: 3 horizontal rings;
- escape local search: 5 rings;
- navigation shortcut lookahead: 6 nodes / 12 blocks;
- projectile threat scan radius: 30 blocks;
- projectile prediction horizon: 30 ticks;
- one projectile ignored for 60 ticks after consideration;
- dodge duration: 9 ticks;
- orbit steering commitment: 8..14 ticks;
- orbit side commitment: 45..100 ticks;
- dash curve length approximation: 24 samples;
- dash hard movement guard: 80 ticks.

The architecture also avoids 3D A* whenever a direct route is available.

## 27. Direct applicability to TECH-HUB 1.20.1

This target is already native to the anchor:

- Minecraft 1.20.1
- Forge 47.4.0
- Java 17

Therefore API archaeology/backport is minimal compared with newer-only targets.

Reusable contracts can be reconstructed against the same vanilla classes:

- `FlyingPathNavigation`
- `FlyNodeEvaluator`
- `MoveControl`
- `Goal`
- `Vec3`
- `AABB`
- `ClipContext`
- `Heightmap.Types.MOTION_BLOCKING_NO_LEAVES`

KnightLib is not fundamental to the flight math. It mainly surrounds animation/state presentation.

## 28. Suggested reusable KNEEKURA abstractions

Without copying upstream code, the recovered design can be represented as:

### FlightIntent

```text
destination
referenceFrame = TERRAIN | TARGET | ABSOLUTE
speedModifier
commitUntil
facingMode = VELOCITY | TARGET
```

### FlightNavigation

```text
if directClear:
    directSteering
else:
    flyingPathfinder

while pathing:
    try bounded safe shortcut
```

### FlightSteering

```text
desiredVelocity
endpointSlowdown
accelerationBlend
overshootClamp
facingController
```

### TacticalOrbit

```text
tangent(target)
+ radialCorrection(targetDistance)
+ targetRelativeAltitude
+ stable side / short steering commitment
```

### FreeSpaceResolver

```text
ideal point
-> bounded vertical/ring offsets
-> translated bbox collision check
-> first valid nearby point
```

### PredictiveDodge

```text
relative-motion interception estimate
-> lowest time-to-impact
-> bounded lateral free-space search
-> short evasive ownership of movement
```

### ScriptedManeuver

```text
PREPARE -> EXECUTE_CURVE -> RECOVER
curve length normalization
swept hit volume
hard timeout
post-maneuver collision recovery
```

## 29. Where this is most useful

The recovered techniques are especially useful for:

- flying hostile mobs;
- dragons/wyverns;
- fairies/allays with combat behavior;
- aerial bosses;
- projectile-aware enemies;
- high-speed charge attacks;
- camera-observed autonomous entities where visual smoothness matters.

For a creature that lands/perches, add a separate ground/air transition planner rather than
forcing that behavior into this permanent-hover architecture.

## 30. Non-findings and limits

- No real aerodynamics, lift/drag or bank physics.
- No landing, perching or takeoff animation state.
- No flock formation/cohesion/separation.
- No predictive target-leading movement for the Harpy body itself; projectile dodge is predictive.
- No body pitch/bank orientation tied to vertical velocity.
- Dash obstacle avoidance is intentionally weak because `noPhysics` is enabled.
- No automated tests were found in the pinned tree.
- No runtime profiling was performed.
- Released JAR SHA/source-byte equivalence was not established in this pass.

## 31. Primary source locators

Pinned ANCHOR root:
https://github.com/Xylonity/Olympus/tree/dcaccaa01abb4b84191c0173ba0996acd26c1f95

Core files:

- `forge/src/main/java/dev/xylonity/olympus/common/entity/HarpyEntity.java`
- `forge/src/main/java/dev/xylonity/olympus/common/entity/ai/harpy/AbstractHarpyGoal.java`
- `forge/src/main/java/dev/xylonity/olympus/common/entity/ai/harpy/internal/HarpyFlightGoal.java`
- `forge/src/main/java/dev/xylonity/olympus/common/entity/ai/harpy/internal/HarpyRetreatGoal.java`
- `forge/src/main/java/dev/xylonity/olympus/common/entity/ai/harpy/internal/HarpyProjectileGoal.java`
- `forge/src/main/java/dev/xylonity/olympus/common/entity/ai/harpy/internal/HarpyProjectileDodgeGoal.java`
- `forge/src/main/java/dev/xylonity/olympus/common/entity/ai/harpy/internal/HarpyDashGoal.java`
- `forge/src/main/java/dev/xylonity/olympus/common/entity/ai/navigation/HarpyFlyingMoveControl.java`
- `forge/src/main/java/dev/xylonity/olympus/common/entity/ai/navigation/HarpyFlyingNavigation.java`
- `forge/src/main/java/dev/xylonity/olympus/registry/OlympusEntities.java`

History commits:

- `d9e1917638f4bd4e58ceac4ecbed790f7c27f875`
- `d5cbe9d364de0126ca85d7397919e55030cb9d0a`
- `1661d88b071db8ff31628d8aac038f99c17e8088`
- `94591edf94243e2914f85e6f692a7199cee720e8`
- `c323fbc68b52bc479fb25ef279111ea1b1d55aa4`
- `2f9ec295d54218c4bbd6ecc89cb4962a007ab6cd`
