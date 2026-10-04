# Goofy Critters movement research — 2026-10-05

## 1. Research question

Why does Goofy Critters move so differently from ordinary Minecraft mobs, and what reusable
locomotion technology can KNEEKURA recover?

The central answer is Gestalt: its body is moved by **environment-anchored helper entities**, not a
normal walk/fly Navigation contract.

Evidence terms:

- **DIRECT_OBSERVATION** — visible in pinned source/diff.
- **AUTHOR_CLAIM** — public project/distribution text.
- **INFERENCE** — reusable engineering interpretation.
- **UNKNOWN** — not established from available evidence.

Two source tracks are kept separate:

- release-era source candidate: `9188e5175828154bdae309dd352e16e338dc8089`
- frontier source: `96d01a7b7ceaa18c51ae0cb1e7dfac0c3d467956`

The distributed CurseForge 1.0.0 binary is not asserted source-identical to either revision.

## 2. Gestalt deliberately opts out of normal mob locomotion

**DIRECT_OBSERVATION** in frontier `GestaltEntity`:

- `MOVEMENT_SPEED = 0`;
- `registerDefaultGoals()` is empty;
- constructor enables no-gravity;
- body tick runs `GestaltController.tick()`;
- fall distance is continually reset.

Locators:

- `entity/living/GestaltEntity.java#L42-L58`
- `entity/living/GestaltEntity.java#L60-L98`

The release-era source candidate already has the same architectural choice.

Gestalt therefore is not "a normal mob with a strange walk animation". Its motion source is outside
vanilla walking entirely.

## 3. Desired motion is represented as a target field, not a body command

The body does not receive `navigation.moveTo` for Gestalt locomotion.

Instead, `GestaltController` stores one desired target position.

The target comes from three contexts.

### Ridden

When an owner/player rides Gestalt and supplies strafe/forward input:

1. rider pitch/yaw and WASD-style inputs are converted to a world point;
2. left/right input and forward input are scaled by roughly 50 blocks;
3. Gestalt rotates toward rider view;
4. a small +0.01 Y impulse is added;
5. the calculated point is written to the controller as the desired target.

### Tamed follow

If owner distance is >=6, controller target becomes owner position.

### Untamed follow

The nearest valid player within 100 blocks is used when distance >=6.

**Technique:** input/AI chooses a **desired region**, while locomotion physics decides how the body
can move toward it.

This is radically different from:

`input -> body velocity`

and closer to:

`input -> actuator-placement bias -> force field -> body velocity`.

## 4. Environment sampling creates temporary actuators

`GestaltController.tick()` maintains a list of live hands.

While fewer than 16 hands exist:

- ray start = Gestalt body;
- when there is an active desired target:
  - random point is sampled around that target with radius ~5;
- without active target:
  - random point is sampled around the body with radius ~50;
- a block-collider ray is cast from body to sampled point;
- only a hit on a **full collision-shape block** becomes an anchor;
- one hand entity is launched to that hit point.

Locator:
- `misc/GestaltController.java#L33-L68`

**INFERENCE:** this converts surrounding static terrain into a temporary locomotor skeleton.

The creature does not pre-author legs for every terrain configuration. It asks the current world
where a usable support exists and instantiates an actuator there.

## 5. Hand lifecycle is a detached state machine

Each `GestaltHandEntity` stores/synchronizes:

- owner UUID;
- moving flag;
- discard-after-return flag;
- target world position.

### EXTENDING

A new hand:

- starts at body position;
- is oriented toward the chosen anchor;
- gets velocity directly toward that point at speed 1.5;
- moves itself with `MoverType.SELF`.

### ANCHORED

When:

- distance to target <=1 block, or
- horizontal/vertical collision occurs,

the hand stops and its velocity becomes zero.

### SUPPORT INVALIDATION

If the hand is no longer moving and the target block is no longer a full collision block, it
immediately retracts.

### RETRACTING

`retract(owner)`:

- sets moving=true;
- sets discard=true;
- changes target to owner position;
- sets velocity toward body at 1.5.

When it returns/collides, it is discarded.

Locators:
- `entity/living/GestaltHandEntity.java#L39-L101`
- `#L103-L110`

**Technique:** temporary locomotion appendages can be real entities with a simple independent
lifecycle. The body then consumes their state as actuators.

## 6. The strange movement comes from a radial force shell

This is the core of the effect.

For each hand, current source computes hand/body separation.

### Hand at or beyond ~6 blocks

The body receives an impulse toward the hand.

Ignoring the undocumented precision gate and a ratio that is normally near one, the scale is
approximately **0.05**.

### Hand inside ~6 blocks

The body receives a smaller impulse away from the hand, approximately **0.01**.

Conceptually:

```text
d >= R:
    acceleration += toward(anchor) * pullGain

d < R:
    acceleration += away(anchor) * pushGain
```

where `R ~= 6`.

With N hands:

```text
deltaV = sum(force(hand_i, body))
```

No central solver decides exact body coordinates.

**INFERENCE:** the 6-block threshold behaves like a crude piecewise equilibrium shell. A cloud of
anchors around the entity stabilizes it, while a target-biased cloud creates asymmetric net force
and moves it.

This is why the creature can look organic/goofy without a procedural gait planner.

## 7. Movement direction emerges by moving the anchor distribution

When no target is active, new hands are sampled widely around the body.

When a target is active, new hands are sampled close to the target.

That means the controller does not need to compute:

`desired body acceleration = target - body`.

Instead it changes:

`P(next anchor | desired target)`.

As target-side anchors accumulate, their pull contribution biases the summed body impulse toward
the goal.

**Technique:** movement can be controlled indirectly by changing **where forces are allowed to
originate**.

This is a powerful pattern for:

- tentacled entities;
- slime/amoeba creatures;
- root/vine walkers;
- grappling bosses;
- wall-crawling horrors;
- magical multi-limb mounts.

## 8. Rolling contact replacement

When:

- there are more than eight hands;
- a movement target is active;

the controller looks at hands at least 40 ticks old and chooses the farthest from the body. That
hand is retracted, and the target field is reset.

New hand attempts continue later.

**INFERENCE:** this acts like contact turnover:

```text
old trailing anchor
      ↓ retract
free actuator budget
      ↓
future target-biased anchor
```

It resembles stepping without defining discrete legs or a footstep sequence.

## 9. One locomotion system serves AI and mount control

There is no separate "mount physics" path.

Player riding changes only the controller target. Owner-follow and wild-player-follow also change
only the controller target.

The same hand attachment and force accumulation runs afterward.

**Technique:** separate locomotion **control intent** from locomotion **actuation**. AI and player
control can feed the same actuator system.

This is a particularly clean model for exotic mounts.

## 10. Body rotation is intentionally decoupled from vanilla behavior

Gestalt overrides BodyRotationControl with an implementation whose client tick is empty.

Rider input explicitly rotates body/head toward rider orientation.

**INFERENCE:** vanilla Mob body/head correction would visually fight an entity whose movement
vector is not generated by forward walking. Exotic locomotion often needs explicit rotation
ownership.

## 11. Procedural arm rendering follows physical anchors

Gestalt's hand is a real entity, but the arm between body and hand is rendered procedurally.

`GestaltHandRenderer`:

1. takes interpolated body and hand positions;
2. computes the world-space span;
3. walks along that span in roughly one-block chunks;
4. applies a nonlinear angle transform to make the chain curve/bend;
5. orients each repeated arm model segment toward the next point;
6. samples world lighting along the generated chain.

Locator:
- `entity/renderer/GestaltHandRenderer.java#L38-L92`
- `#L95-L99`

The visual skeleton is therefore reconstructed from the physical actuator state.

**Technique:** physics and visuals can share only endpoints. A long deformable limb does not need
dozens of synchronized physics bones.

## 12. Visual/physics separation reduces simulation state

Physical simulation needs:

- body entity;
- one hand entity per anchor;
- hand target and phase.

Visual presentation can synthesize all intermediate arm segments client-side.

That is much cheaper in state complexity than giving every arm segment collision/network identity.

**INFERENCE:** store mechanically significant endpoints; reconstruct continuous visual geometry
between them.

## 13. Eyes uses conventional 3D navigation

Eyes is useful as a contrast.

It uses the general aerial framework:

```text
random aerial Goal / owner-follow intent
        ↓
NoSpinFlyingPathNavigation
        ↓
AnimationFlyingMoveControl
        ↓
AIR travel physics
```

When tamed:

- random movement is suppressed;
- if owner is >=6 blocks away, Eyes navigates toward owner.

Unlike Gestalt, Eyes is still destination/path-driven.

## 14. Frontier flight control turns by yaw and pitch

`AnimationFlyingMoveControl`:

- computes vector to wanted position;
- yaws toward horizontal target;
- computes desired pitch from vertical/horizontal offset;
- clamps pitch with movement configuration;
- derives forward input from cos(pitch);
- derives vertical input from -sin(pitch).

Default frontier `MovementData.fly.turn`:

- pitch envelope: 85 degrees;
- yaw turn per update: 10 degrees.

This is a useful lightweight 3D steering contract, but it is conventional compared with Gestalt.

## 15. Frontier movement framework can swap locomotion modes

Post-release `AbstractAnimatableAnimal` classifies mobs as:

- LAND
- AIR
- WATER

For AIR/WATER creatures, `switchControl` can swap:

- MoveControl;
- LookControl;
- PathNavigation

when flight/swim state changes.

Example AIR transition:

```text
ground:
 AnimationMoveControl
 LookControl
 NoSpinGroundPathNavigation

flight:
 AnimationFlyingMoveControl
 FlyingLookControl
 NoSpinFlyingPathNavigation
```

**Technique:** locomotion mode should be a bundle of compatible movement components, not a single
boolean with one MoveControl trying to support every medium.

This is FRONTIER-only unless separately verified in the distributed JAR.

## 16. MovementData centralizes gait/mode tuning

Post-release `MovementData` holds:

- body turn limit;
- ground interval, yaw turn and random radius;
- flight interval, pitch/yaw turn and random radius;
- swim interval, pitch/yaw turn and random radius.

**Technique:** separate creature identity from locomotion tuning. Shared controls remain reusable
while individual mobs can change steering envelopes.

## 17. NoSpin navigation fixes body-volume path shortcuts

The frontier contains ground, flying and water NoSpin navigators.

They still use vanilla pathfinding/evaluators, but change path following.

### Patched node positions

A returned vanilla Path is wrapped. `getEntityPosAtNode` places the target point based on the
entity bounding width instead of blindly using a generic node position.

### Whole-body shortcut test

When skipping ahead, the navigator sweeps the entity's AABB along the proposed straight segment
through voxels.

The sweep checks:

- block pathfindability for the medium;
- path type/malus;
- fire/damage/lava hazards;
- ground support constraints where relevant.

Only if the complete body volume can move along the segment is the Path index advanced.

Source credit points to `andyhall/voxel-aabb-sweep` for the traversal concept.

**Technique:** line-of-sight of a point is not enough for a large entity. Shortcut validation should
sweep the entity volume.

## 18. Why "NoSpin" matters

The custom controls explicitly own yaw/pitch/body relationships rather than letting navigation
produce abrupt orientation corrections.

Historical commits repeatedly changed:

- flying node completion;
- ground node completion;
- body/head rotation behavior.

**INFERENCE:** the name and history reflect a design concern: path progress and visual facing should
not accidentally cause large instantaneous rotations.

Navigation chooses geometry. Control/rotation systems decide presentation.

## 19. Historical evolution: release movement vs frontier framework

### Release-era candidate

By 2026-01-31 the source already contains:

- Gestalt;
- Gestalt hand entities;
- GestaltController;
- rider target projection;
- owner/wild-player following through anchor targeting;
- procedural hand/arm rendering;
- early Eyes/flying systems.

So the core Gestalt concept is not a later July invention.

### February movement work

Source history shows repeated tuning to:

- NoSpin flying node completion;
- Y tolerance;
- body/head rotation;
- ground completion radius;
- full voxel-AABB shortcut testing.

### July rework

`29545d7` and `96d01a7` substantially reorganize/generalize movement:

- one `AbstractAnimatableAnimal` framework;
- ground/air/water classifications;
- MovementData;
- separate controls;
- NoSpin navigators for each medium;
- generalized animation/movement ownership.

These are useful FRONTIER technologies, but not proven present in file 7553632.

## 20. Gestalt implementation quirk: nearly-equal distance gate

The per-hand force branches first calculate:

- a double vector length;
- `distanceTo(owner)`, returned/stored as float.

They then require `length > dist`.

These values represent essentially the same center-to-center distance at different precision.

The source gives no explanation.

Status: **UNKNOWN / IMPLEMENTATION QUIRK**.

Do not make this condition part of a generalized anchor-force contract without runtime study. The
meaningful reusable system is the force direction/radius behavior, not this gate.

## 21. Gestalt environment limitations

### Full-block anchors only

Controller only accepts a hit block whose collision shape is a full block.

Consequences:

- slabs/fences/complex shapes are not ordinary anchors;
- available locomotion contacts depend strongly on architecture.

### No reachability planner

There is no global A*/graph plan for Gestalt.

The system knows:

- desired target region;
- ray-hit anchors;
- local anchor forces.

It does not prove that the target is reachable.

### Sparse/open environments

If no suitable collision block is found along sampled rays, no new anchor is created.

No-gravity avoids falling, but there is no formal propulsion fallback in that state.

**Technique boundary:** emergent anchor locomotion trades deterministic reachability for physical
character.

## 22. Entity/network cost boundary

One Gestalt may maintain up to 16 hand entities.

Each hand:

- has synchronized data;
- resolves owner;
- ticks;
- can be saved;
- can be tracked/rendered.

Current registration gives GestaltHand a client tracking range of 100.

Hand rendering also sets no-culling/always-distance behavior.

**INFERENCE:** this is appropriate for a rare spectacle creature, but should be budgeted explicitly
before applying the same pattern to crowds.

## 23. Procedural arm render cost boundary

The renderer loops from body to hand in small segments.

Approximate render work is proportional to:

```text
sum(distance(body, hand_i)) / segment_length
```

not merely hand count.

A sixteen-hand Gestalt with long anchor spans can therefore emit many arm-model draws.

No profiling data is available, so the cost magnitude is **UNKNOWN**.

## 24. Owner resolution boundary

`GestaltHandEntity.getOwner()` resolves UUID through `GoofyUtil.getEntityByUUID`.

That helper reflectively accesses an obfuscated/private Level entity-getter method.

**INFERENCE:** detached actuator entities need a robust owner lookup, but reflective private API is
not the part to preserve. A TECH-HUB implementation should use stable loader/version-native entity
tracking or cached IDs/UUID resolution.

## 25. Model-part world position framework is separate

The frontier also contains:

- `ModelPartChains`;
- `ModelPartPositions`;
- client->server `UpdateModelPositionPacket`.

It can turn a rendered model-part chain into a world-space position and report it to server.

However, no active `addModelPos` consumer was found in the pinned source search.

Status: **FRAMEWORK SCAFFOLD / NOT PROVEN PART OF CURRENT LOCOMOTION**.

Do not confuse this with Gestalt's hand anchors, which are real server-visible entities.

## 26. Masked boundary

Public project material mentions Masked as future content, but pinned source contains no
`MaskedEntity`.

Therefore no Masked locomotion technology is claimed.

## 27. Reusable TECH-HUB abstractions

### AnchorFieldLocomotion

```text
desiredTarget
maxAnchors
anchorProbe(origin, desiredTarget)
anchorValidity(worldHit)
forceRadius
pullGain
pushGain
recyclePolicy
```

### LocomotionAnchor

```text
owner
targetPosition
phase = EXTENDING | ANCHORED | RETRACTING
supportStillValid
```

### AnchorForce

```text
offset = anchor - body
distance = |offset|

if distance >= restRadius:
    +normalize(offset) * pullGain
else:
    -normalize(offset) * pushGain
```

The body integrates the sum of all anchor contributions.

### IntentAdapter

```text
AI follow target
rider input
scripted direction
        ↓
desired anchor-sampling region
```

### WholeVolumeShortcut

```text
candidate farther path node
        ↓
sweep mob AABB through voxels
        ↓
all traversed cells/path types safe?
        ↓
yes -> skip intermediate nodes
```

### MobilityModeBundle

```text
mode:
  MoveControl
  LookControl
  Navigation
  travel physics
  turn/radius parameters
```

## 28. Strongest technologies recovered

1. Environment-anchored locomotion instead of Path-driven body motion.
2. Force-field movement from many independent contacts.
3. Desired movement expressed as anchor-placement bias.
4. Pull/push equilibrium shell.
5. Rolling contact recycling.
6. Same actuator contract for AI and rider control.
7. Endpoint-only physical state with procedural limb reconstruction.
8. Whole-AABB path shortcut validation.
9. Runtime ground/air/water movement-component swapping.
10. Data-driven steering envelopes.

## 29. What to preserve vs what not to preserve

### Preserve as concepts

- anchor lifecycle;
- target-biased anchor acquisition;
- force accumulation;
- rolling contact replacement;
- procedural body-to-anchor visuals;
- whole-body sweep validation;
- movement-mode bundles.

### Do not blindly copy

- reflective owner lookup;
- unexplained `length > dist` gate;
- unconditional 16 helper-entity budget;
- full-block-only support rule unless aesthetically intended;
- always-render/no-culling settings;
- private post-release framework details without deciding GPL implications.

## 30. Primary source locators

FRONTIER root:
https://github.com/min2222/GoofyCritters/tree/96d01a7b7ceaa18c51ae0cb1e7dfac0c3d467956

Release-era candidate:
https://github.com/min2222/GoofyCritters/tree/9188e5175828154bdae309dd352e16e338dc8089

Key current files:

- `entity/living/GestaltEntity.java`
- `entity/living/GestaltHandEntity.java`
- `misc/GestaltController.java`
- `entity/renderer/GestaltHandRenderer.java`
- `entity/living/EyesEntity.java`
- `entity/AbstractAnimatableAnimal.java`
- `entity/AbstractAnimatableFlyingAnimal.java`
- `entity/ai/control/AnimationMoveControl.java`
- `entity/ai/control/AnimationFlyingMoveControl.java`
- `entity/ai/control/AnimationSwimmingMoveControl.java`
- `entity/ai/control/AnimationBodyRotationControl.java`
- `entity/ai/navigation/NoSpinGroundPathNavigation.java`
- `entity/ai/navigation/NoSpinFlyingPathNavigation.java`
- `entity/ai/navigation/NoSpinWaterBoundPathNavigation.java`
- `misc/MovementData.java`
- `entity/AbstractOwnableEntity.java`
- `util/GoofyUtil.java`

Important movement-history commits:

- `812091d343e13dd23c055adb179ae4846d39e7a7`
- `5225cd8e8fb781c1362929ffdb45b21fccd33a00`
- `6ab5a74c1212941030c98f6cec56327050654f67`
- `8a35e6d32676c93aa48717c1e834052bfe5e64e3`
- `d99e2cc508c9daa98959024d854440b4f53eacec`
- `4bf75aab01d64ff0c32d31dc1a12e5aa0bc0e568`
- `f68594eb3207c6a704b71255fd88868f114dc96a`
- `9f65e6dd63f83d281a18cb161bd3ad7a85f173bf`
- `29545d7e2dc3c31df53865b14f9bd4ee2aaf9b59`
- `96d01a7b7ceaa18c51ae0cb1e7dfac0c3d467956`
