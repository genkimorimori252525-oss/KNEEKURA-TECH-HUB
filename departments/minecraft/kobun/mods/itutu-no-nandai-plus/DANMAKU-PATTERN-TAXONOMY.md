# DANMAKU PATTERN TAXONOMY — 五つの難題MOD+ X1

Status: **derived from ORIGINAL_SOURCE / ORIGINAL_BINARY; runtime NOT_RUN**

This document classifies the active 35 spell cards by reusable danmaku mechanics. It does not claim that modern Minecraft should copy the 1.7.10 implementation literally.

## 1. Core grammar

The spell-card set is built from a small compositional grammar:

```text
spawn locus
  × geometry operator
  × temporal rhythm
  × trajectory operator
  × lifecycle transition
  × child-emission rule
```

The variety comes mostly from composing these dimensions instead of inventing a new projectile implementation per card.

### Spawn locus

1. **Caster-centered** — most rings/spheres.
2. **Target-centered** — Youryoku Spoiler.
3. **Moving mother/emitter** — Kappa Pororoca, Stardust Reverie, Red Magic, Kachoufuugetu, Meteor on Earth.
4. **Random spatial emitter** — Hikouchuu Nest.
5. **Predicted stop/explosion locus** — Fujiyama Volcano.

### Geometry operators

`THShotLib` supplies reusable primitives:

- single shot;
- circle;
- ring around an aim axis;
- random ring / cone;
- sphere composed from pole + ring slices;
- moving laser (`LaserA`);
- attached/setting laser (`LaserB` and related host relationships).

The spell code therefore owns composition/timing rather than rewriting low-level trigonometry per card.

## 2. Trajectory operators

### Constant / aimed
Representative cards: Meteonic Shower, Eternal Meek, Moses Miracle.

### Clamp-to-limit acceleration / deceleration
Representative cards: Kasho no Eimin, Miracle Fruit, Mishagujisama, Fujiyama Volcano.

`EntityTHShot.shotAcceleration()` applies positive acceleration only below its limit and negative acceleration only above its limit, then clamps. Speed change is used as a phase transition.

### Per-tick angular rotation
Representative cards: Kasho no Eimin, Red Magic, Saikou Ranbu.

### Bounded homing / re-aim
Representative cards: Musou Fuuin, Youryoku Spoiler.

Musou Fuuin turns toward the target with a bounded angular correction instead of snapping. Youryoku Spoiler changes semantic destination later and returns toward the caster.

### Hard turn / zigzag
Representative cards: Icicle Fall, Little Bug Storm, Gagouji Cyclone.

A projectile survives a phase boundary, changes heading by ±45/90/135 degrees, then resumes under new speed/gravity rules.

### Gravity-phase
Representative cards: Kerochan Fuuu ni Makezu, Icicle Fall.

Gravity is an explicit trajectory component and may be enabled only in a later phase.

### Ricochet
Representative cards: Kappa Pororoca child shots, Catadioptric.

The built-in BOUND family makes level geometry part of the pattern. BOUND04 supports continuing ricochet behavior rather than a single bounce.

### Knockback-as-pattern
Representative card: Yasaka no Kamikaze.

WIND01 changes victim motion and adds upward lift; danger is not just HP loss but modification of the next dodge state.

## 3. Temporal composition

### Periodic emission
Examples:
- Kasho no Eimin — 6-tick cadence;
- Kappa Pororoca — 10-tick mother cadence;
- Mishagujisama — 9-tick cadence;
- Houka Kenran — 3-tick weave + 20-tick dense accent.

### Phase reversal
Examples:
- Non-Directional Laser — opposite laser rotation in the second phase;
- Kachoufuugetu — handedness reverses after time 30;
- Meteor on Earth — second mother wave rotates oppositely;
- Red Magic — second phase reverses mother curvature.

### Delayed activation
Examples:
- Miracle Fruit;
- Red Magic;
- Perfect Freeze.

Delay creates telegraphed hazards whose dangerous motion begins after the object already exists.

## 4. Projectile-as-state-machine

The central reusable technique is that a projectile is not necessarily “spawn once, move once, die.”

`ISpecialShot` + `SpecialShotRegistry` lets one projectile change:

- form;
- color;
- size;
- damage;
- speed;
- acceleration;
- heading;
- gravity;
- lifetime;
- special behavior ID.

Strong examples:

- **Little Bug Storm** — turn → brake → change visual form → flash → turn again → large rice form → reaccelerate.
- **Icicle Fall** — outward spoke → brake → ±90° turn → gravity phase.
- **Perfect Freeze** — existing bullets are converted into stationary white freeze-state bullets and later relaunched.

This gives large behavior variety without a unique Entity class for every trajectory.

## 5. Mother bullets and moving emitters

Representative cards: Kappa Pororoca, Stardust Reverie, Red Magic, Kachoufuugetu, Meteor on Earth.

A mother bullet provides a moving local coordinate frame. Children are emitted relative to its live position/orientation.

Reusable shapes:

1. **moving sprinkler** — Kappa Pororoca;
2. **helix/trail painter** — Stardust Reverie, Meteor on Earth;
3. **hazard history** — Red Magic leaves delayed children along a path;
4. **mobile laser flower** — Kachoufuugetu attaches multiple lasers to a moving mother.

## 6. Recursive / generational bullets

### Fujiyama Volcano

A decelerating carrier reaches its stop point and becomes a 44-way sphere. Each following generation splits two-way:

```text
carrier
  -> big
     -> 2 medium
        -> 2 small
           -> 2 tiny
```

The reusable idea is **lifecycle-triggered recursive emission**, not the literal counts.

## 7. Field manipulation

### Perfect Freeze

Instead of merely adding bullets, the card queries existing nearby `EntityTHShot` entities and converts eligible ones into a new state:

```text
existing field
    -> select
    -> transform
    -> delayed relaunch
```

### Satsujin Doll

The spell first constructs a knife field, invokes the time-stop system, then re-aims a selected subset during stopped time. The ordered mutation of world state is the spell.

## 8. Laser families

### Persistent central beam
- Master Spark.

### Radial rotating cage
- Non-Directional Laser;
- Moonlight Ray.

### Distributed / moving emitter lasers
- Hikouchuu Nest;
- Kachoufuugetu.

Laser difficulty is controlled by emitter position, spoke count, width/length, delay, angular velocity and whether the emitter itself moves.

## 9. Space-control classes across the active set

### Tracking / reactive pressure
IDs: **0, 3, 16, 24, 33**

### Ring / shell / lattice pressure
IDs: **2, 4, 5, 6, 14, 18, 20, 22, 23, 29, 30, 35, 40**

### Moving-emitter pressure
IDs: **11, 12, 23, 26, 35**

### Laser exclusion zones
IDs: **1, 10, 25, 26, 28**

### Trajectory phase-change pressure
IDs: **8, 9, 16, 19, 20, 23, 34, 40**

### Environment-interactive
IDs: **11, 21, 33**

### Random / chaos layer
IDs: **3, 13, 15, 30**

### Behavior-empty in this X1 build
IDs: **7, 27**

## 10. Difficulty scaling strategies

This MOD does not use one global “more bullets” rule. Cards instead may:

- raise shot count (Perfect Freeze, Icicle Fall);
- widen lasers (Moonlight Ray);
- add secondary rings/center shots (Meteor on Earth, Gagouji Cyclone);
- change mother-emitter count (Stardust Reverie, Meteor on Earth);
- activate Lunatic-only supplemental fire (Gagouji Cyclone).

Difficulty can change **topology**, not merely density.

## 11. Color and form as state communication

Visual properties correlate with behavior stage in several cards:

- Satsujin Doll — blue/red laid knives → selected green re-aimed knives;
- Perfect Freeze — arbitrary field → white frozen state;
- Little Bug Storm — form/color changes mark internal phase;
- Red Magic — purple mothers vs red delayed children.

Modern lesson: use visual state to telegraph trajectory-state changes.

## 12. Highest-value techniques for a modern danmaku battle system

1. **Trajectory state machines** — turn/brake/reaccelerate/transform without a unique projectile class.
2. **Mother-emitter coordinate frames** — moving local origins for trails, spirals and mobile lasers.
3. **Field transforms** — effects that consume the current bullet field as input.
4. **Phase reversal** — reuse geometry with opposite handedness as a second recognizable phase.
5. **Recursive lifecycle emission** — split/branch on timeout, stop or collision.
6. **Explicit projectile physics profiles** — first speed, limit speed, acceleration, gravity, angular rate.
7. **Geometry library** — ring/sphere/random-cone/laser from reusable vector operations.
8. **Visual state signalling** — form/color/size identify behavior phase.
9. **Difficulty by topology** — add layers or alter structure, not just count.
10. **Separate spell timeline from projectile behavior** — spell says when/where; projectile special says how the already-spawned object evolves.

## 13. Historical implementation boundary

Do not port literally:

- `Class.newInstance()` special behavior instantiation;
- global integer special IDs;
- numeric DataWatcher slots;
- mutable old-era shared data patterns;
- immediate GL11 rendering;
- 1.7.10 raytrace/entity/network assumptions.

A modern reconstruction should preserve the geometry/trajectory grammar and observable semantics while using namespaced typed registries, explicit codecs, bounded server-authoritative projectile simulation and modern rendering/batching.
