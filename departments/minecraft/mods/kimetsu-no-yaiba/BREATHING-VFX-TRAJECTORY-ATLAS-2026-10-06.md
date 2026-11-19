# Kimetsu no Yaiba ver3 — Breathing VFX / Trajectory Atlas — 2026-10-06

## 1. Scope

This atlas focuses on **combat presentation and spatial trajectory**, not merely damage values.

Pinned binary:

`KimetsunoYaiba-ver3-forge-1.20.1.jar`

SHA-256:

`b4af6e8a9d5926c5fea212a5e237e61f1e8095a5be23eca9b8294258a3b466b6`

No official source revision is pinned. Implementation evidence is therefore from JAR bytecode,
resources and renderer/model assets.

This pass asks, for each Breathing family:

- what physically moves?
- where is the damage sampled?
- what visual geometry is drawn?
- is the visual a particle, helper actor, projectile or body motion?
- does the visual path equal the hit path?
- how long does the afterimage persist?
- does the form destroy blocks / cut projectiles?
- which presentation primitives can be reused independently?

Evidence labels:

- **DIRECT_OBSERVATION** — bytecode/resource fact
- **INFERENCE** — visual/game-design interpretation
- **UNKNOWN** — not established

---

# 2. Main conclusion

The mod does **not** implement one universal "Breathing effect renderer".

It uses several very different presentation strategies:

```text
A. BODY_MOTION
   player/NPC body itself travels along the attack path

B. LOCAL_FIELD
   visual ring/area around actor = defensive/offensive field

C. SAMPLED_ARC_VOLUME
   Procedure computes several world positions and applies hits/particles there

D. INVISIBLE_HELPER_PROXY
   invisible Entity carries hit geometry/provenance

E. VISIBLE_HELPER_ACTOR
   modeled Entity carries a large creature/slash/weapon visual

F. DETACHED_WEAPON_RIG
   animated GeckoLib helper represents chain/weapon geometry

G. MOBILE_AOE_PROJECTILE
   projectile moves and runs area-damage logic every tick

H. PARTICLE_SHEET
   very large, short-life billboard particles describe slash planes

I. PERSISTENT_AFTERIMAGE
   small physics-enabled thematic particles remain after the cut

J. TECHNIQUE_SEQUENCE
   a higher-order form composes lower forms into one visual program
```

This is the most useful battle-presentation lesson from the target:

> **The style of an attack comes from choosing the right spatial representation, not just changing
> particle color.**

---

# 3. Full Breathing surface

Main form Procedure counts observed:

| Family | Procedure count | Main presentation tendencies |
|---|---:|---|
| Water | 12 | water trail, circular field, water-dragon helper |
| Thunder | 9 | charge/dash, lightning sheets, bright streaks |
| Flame | 7 | body slash + flame sheet + creature helper |
| Mist | 7 | discontinuous motion, ray-based space sampling, sparse visual layer |
| Wind | 9 | giant rotating wind sheets + claw helper |
| Beast | 5 | physical body trajectory, sweep sound, destruction |
| Serpent | 4 | invisible helper proxies + curved body/weapon path |
| Insect | 4 | thrust/lunge + poison |
| Moon | 12 | large crescent hierarchy + slash/projectile actors |
| Sun / Hinokami | 13 | mixed form primitives + large flame helper + sequence |
| Sound | 3 | spark/explosion bursts + destructive sweeps |
| Flower | 4 | persistent falling flower afterimage |
| Love | 6 | ribbon-like body/weapon sweeps |
| Stone | 5 | animated detached weapon rig |
| Bamboo | 12 | persistent bamboo motif + normal hit geometry |
| Cherry Blossom | 9 | falling petal afterimage + arc slashes |
| Senior / custom | 8 | mixed/joke/custom techniques; separated from canonical style analysis |

---

# 4. Particle implementation profiles

These are the **client particle objects themselves**, independent from where forms place them.

## 4.1 Water

`WaterParticle`

Observed constructor behavior:

- base dimensions: 0.7 x 0.7
- quad-size multiplier: x3
- lifetime: approximately 11–14 ticks
- gravity: 0
- collision physics: disabled
- input velocity multiplier: x0.3
- animated sprite sequence: 8 frames, advanced roughly every 2 particle ticks

**Presentation role — INFERENCE**

Large, soft, short-lived moving cards work well for a coherent water ribbon.
They disappear quickly enough that repeated samples can look like one continuous stream.

---

## 4.2 Thunder

`ParticleThunderParticle`

- base dimensions: 1 x 1
- quad multiplier: x3
- lifetime: ~9–14 ticks
- gravity: 0
- physics: disabled
- input velocity multiplier: x1.5

`ParticleThunder2Particle` / `ParticleThunder3Particle`

- dimensions: roughly 1 x 1.5
- quad multiplier: x5
- lifetime: ~9–14 ticks
- gravity: 0
- physics: disabled
- input velocity multiplier: x1.5
- full-bright render path

**Presentation role — INFERENCE**

Thunder intentionally trades persistence for size, brightness and speed.
This makes the VFX read as an instantaneous energy trace around a very fast body movement.

---

## 4.3 Wind

`ParticleWindParticle`

- dimensions: 8 x 8
- quad multiplier: x8
- lifetime: roughly 3–14 ticks
- gravity: 0
- physics: disabled
- input velocity multiplier: x0.5
- angular acceleration: 0.05

This is enormous compared with ordinary Minecraft particles.

**Presentation role — INFERENCE**

The particle is not "wind dust".
It is effectively a short-lived textured **slash sheet**.

---

## 4.4 Moon

Moon has a deliberate size hierarchy.

### `ParticleMoon1Particle`

- dimensions / quad scale: ~3
- lifetime: ~4–11 ticks
- no gravity / no physics
- velocity multiplier: 0.5
- angular acceleration: 0.2
- full-bright path

### `ParticleMoon2LarParticle`

- dimensions / quad scale: ~12
- lifetime: ~4–11 ticks
- no gravity / no physics
- velocity multiplier: 0.5
- angular acceleration: 0.2
- full-bright path

Additional:
- MOON_1_MED
- MOON_2
- MOON_2_MED
- MOON_PHASE

**Presentation role — INFERENCE**

Different crescent sizes are an authored visual vocabulary.
Forms can build a layered slash without scaling one texture ad hoc in every Procedure.

---

## 4.5 Flower

`ParticleFlowerParticle`

- scale: ~0.5
- lifetime: ~30–49 ticks
- gravity: 0.1
- collision physics: enabled
- input velocity: preserved
- angular acceleration: 0.05

The particle survives much longer than Water/Thunder/Moon.

**Presentation role**

Flower creates **aftermath**, not only impact.
Petals remain in the world after the actual hit volume has passed.

---

## 4.6 Cherry Blossom

`ParticleCherryBlossomParticle`

- dimensions: ~1 x 1
- lifetime: ~30–49 ticks
- gravity: 0.1
- collision physics: enabled
- input velocity: preserved

Again, the particle outlives the hit.

---

## 4.7 Bamboo

`ParticleBambooParticle`

- dimensions: ~1 x 1
- lifetime: ~20–39 ticks
- gravity: 0
- collision physics: enabled
- input velocity: preserved

This gives a floating/streaking motif rather than falling petals.

---

## 4.8 Sound / spark fire

`ParticleSparkFireParticle`

- quad multiplier: x4
- lifetime: ~7–12 ticks
- gravity: 0.1
- physics: disabled
- velocity multiplier: 0.5
- 14-frame animated sprite sequence

**Presentation role**

A short animated burst suits explosion timing much better than persistent decorative particles.

---

# 5. Shared geometric particle primitives

The JAR also contains general particle math Procedures.

## 5.1 `ParticleGeneratorCircleProcedure`

The Procedure constructs a local orientation basis from actor/world angles and produces positions
around a 3D circle/ring before forwarding them to the generic particle generator.

Stone forms use this for weapon-orbit/circle emphasis.

## 5.2 `ParticleGeneratorSweepingEffectProcedure`

The Procedure constructs a local slash plane from yaw/pitch-style basis vectors, applies randomized
angular offsets inside that plane and sends each calculated point/direction to
`ParticleGeneratorProcedure`.

This is a reusable "paint a blade sweep through 3D space" primitive.

**Recommended extraction**

```text
ParticleArc {
  localBasis
  radius
  startAngle
  endAngle
  verticalTilt
  sampleCount
  jitter
  particleProfile
}
```

rather than hand-writing sin/cos in every form.

---

# 6. Water Breathing

Representative classes:

- `BreathesMizuProcedure`
- `BreathesMizu2..10Procedure`
- `BreathesNagiProcedure`
- `BreathesMizu10hitProcedure`

## 6.1 General Water presentation

Most forms reference the custom `WATER` particle.

The short-lived large animated Water particle means repeated samples visually merge into:

- blade-following ribbons
- arcs
- wake trails
- local circular currents

without the world accumulating long-lived debris.

## 6.2 Nagi — Local defensive ring

`BreathesNagiProcedure`

For the early active window (`cnt1 < 9`), bytecode constructs:

```text
radius0 = (cnt1 - 0.5) * 2
radius1 = radius0 + 1
```

For each radius:

- 72 angular samples
- 5° per sample
- point:
  - x = centerX + cos(angle)*radius
  - y = centerY
  - z = centerZ + sin(angle)*radius
- two particles emitted per point

So one active frame can generate:

```text
2 rings
* 72 points
* 2 particles
= 288 particle instances
```

The visual is spatially aligned with the combat field:

- Range = 7
- knockback = 0.7
- projectile_type = 1
- DoDamage2

projectile_type=1 lets the common kernel discard nearby non-strong projectiles.

**Reusable technique**

The defense field is not a collisionless visual shell.
The ring radius and combat radius are authored from the same conceptual space.

## 6.3 Tenth Form — Constant Flux

`BreathesMizu10Procedure`

Creates:

- `CONSTANT_FLUX` helper entity
- owner/provenance copy
- Water particles
- repeated DoDamage2
- substantial forward ray/clip sampling

Renderer texture:

`textures/entities/seiseiruten.png`

The helper actor is the large visible "creature/flux" silhouette while the owner's Procedure remains
responsible for combat state.

**Primitive: VISIBLE_HELPER_ACTOR**

---

# 7. Thunder Breathing

Representative:

- `BreathesHekirekiIssenProcedure`
- `BreathesHekirekiShinsokuProcedure`
- `BreathesHekireki6renProcedure`
- `BreathesHekireki8renProcedure`
- `BreathesKaminari2..6Procedure`

## 7.1 Thunderclap-and-Flash

The trajectory is body-driven.

Phases include:

1. setup / movement suppression
2. breathing + animation signal
3. particle/lightning telegraph
4. calculate or reuse `x_power/y_power/z_power`
5. set body delta movement at burst magnitude
6. DoDamage2 sampling during the dash
7. exit/reset

Representative movement write:

```text
deltaMovement ≈ directionPower * 2
```

Representative hit context:

- Damage around 23 before/with Strength scaling logic
- Range 3
- effect 4

VFX layers include:

- PARTICLE_LIGHTNING
- PARTICLE_THUNDER_2
- lightning impact sound
- electric_shock sound
- sword_putin / sword_sweep
- thunder1

**Presentation rule**

For extremely fast moves, the body trajectory should remain simple.
Complexity belongs in the trail/flash layer.

## 7.2 Forms 2–6

These forms use:

- PARTICLE_THUNDER
- PARTICLE_THUNDER_2
- PARTICLE_THUNDER_3
- trigonometric placement in several forms
- block destruction in forms 2/6
- fast body movement

The multiple particle scales create inner/outer electric layers without requiring a separate
modeled lightning entity.

## 7.3 Sixfold / Eightfold

The higher forms are orchestration Procedures around repeated first-form-style movement rather than
a completely separate movement engine.

**Primitive: TECHNIQUE_SEQUENCE / repeated dash**

---

# 8. Flame Breathing

Representative:

- `BreathesHonoProcedure`
- `BreathesShiranuiProcedure`
- `BreathesHono2..5Procedure`
- `BreathesHonoikadutiProcedure`

## 8.1 Direct forms

Use:

- body movement
- PARTICLE_FLAME
- slash/blaze/gateway sounds
- DoDamage2
- occasional block destruction

These are flame-wrapped weapon/body trajectories.

## 8.2 Fifth-form helper

`BreathesHono5Procedure`

Spawns:
- `ENKO`

and copies ranged provenance.

The associated large-flame renderer path uses a modeled helper rather than trying to describe an
animal silhouette with hundreds of particles.

## 8.3 Flame creature asset

`FlameDragonRenderer` uses:

`textures/entities/flame_tiger.png`

This reinforces a general target pattern:

> when the attack silhouette has recognizable anatomy, use a helper actor/model rather than a
> particle cloud.

## 8.4 Honoikaduchi

Uses:

- HONOIKADUCHI helper
- PARTICLE_LIGHTNING
- PARTICLE_THUNDER_2
- electric/thunder sound vocabulary

This is a cross-element style composition:
flame technique identity + thunder-like presentation grammar.

---

# 9. Mist Breathing

Representative:

- `BreathesKasumiProcedure`
- `BreathesKasumi1/3/5/6Procedure`
- `BreathesKasumi7AttackProcedure`
- `BreathesKasumi7particleProcedure`

Mist does not rely on one obvious dedicated `PARTICLE_MIST` registry entry.

Instead its presentation comes from:

- animation
- body displacement
- ray/clip sampling
- separate particle Procedure
- swing helper
- teleport-like sound

## 9.1 Seventh Form separation

Two Procedures:

- presentation/particle layer
- attack layer

`BreathesKasumi7AttackProcedure` calls:
- SwingKasumi
- PlayAnimation
- DoDamage2
- many ray/clip paths

**Reusable technique**

For deceptive/discontinuous styles, decouple:

```text
VisualObscurationProgram
DamageTrajectoryProgram
```

They do not need to be represented by the same object.

---

# 10. Wind Breathing

Representative:

- `BreathesKazeProcedure`
- `BreathesKaze2..9Procedure`

## 10.1 Wind sheets

Forms 4/6/8/9 use the giant `PARTICLE_WIND`.

Because the particle itself is 8x8 with rotation, a sparse number of samples can read as a broad
air blade.

**Primitive: PARTICLE_SHEET**

## 10.2 Second form — visible claw helper

`BreathesKaze2Procedure`

Creates:

- `CLAWS_PURIFYING_WIND`
- owner/provenance copy
- body movement
- DoDamage2
- block destruction

Renderer:

`textures/entities/clawspurifyingwind.png`

The helper gives the attack an authored claw silhouette while common attack logic remains on the
owner.

## 10.3 High forms

Kaze9 combines:

- body motion
- trigonometric geometry
- large Wind particles
- spatial hit volume
- block destruction

This creates an expanding/curved slash zone without an actual projectile.

---

# 11. Beast Breathing

Representative:

- `BreathesKedamonoProcedure`
- `BreathesKedamono1/3/4/5Procedure`

No dedicated Beast particle family is used by these forms.

The style instead emphasizes:

- body trajectory
- animation
- sweep sounds
- DoDamage2
- BlockDestroy2
- ray/trigonometric spatial sampling in higher form

**Presentation identity**

Physical aggression is created by moving the actor/hit volume, not by elemental overlays.

This is useful as a contrast:
not every style needs a particle namespace.

---

# 12. Serpent Breathing

Representative:

- `BreathesHebi1..4Procedure`

Creates:

- `SNEAK`
- `SNEAK_2`

These helpers use:

`textures/entities/clear.png`

They are therefore **invisible geometric proxies**.

Forms copy attack provenance into the helpers and combine them with player/body animation.

## Why this is useful

A serpentine attack path can be represented by an Entity trajectory without rendering that Entity.

```text
hidden helper path = combat geometry
owner/sword animation = visible story
```

This lets hit geometry bend independently from a straight body dash.

**Primitive: INVISIBLE_HELPER_PROXY**

---

# 13. Insect Breathing

Representative:

- `BreathesMushiProcedure`
- `BreathesMushi2..4Procedure`

The visual identity is not built from a large dedicated custom particle family.

Instead:

- fast lunges
- multiple setDeltaMovement phases
- small-range hit volumes
- poison effect

All four observed form families write:

`effect = 3`

The shared `Effect3Procedure` applies:

`WISTERIAPOISON`

## Mushi4

Contains multiple movement writes, including strong forward phases around 1.75 multipliers and later
velocity changes.

Representative active hit:

- Damage around 12 before Strength scaling path
- Range 3
- effect 3

**Presentation rule**

Insect is an example where **motion cadence + status identity** can carry the style without covering
the screen in elemental VFX.

---

# 14. Flower Breathing

Representative:

- `BreathesHana2/4/5/6Procedure`

Forms 5/6 use:

- PARTICLE_FLOWER
- DoDamage2
- block destruction
- animation

Flower particles remain after the actual cut because of their long life and gravity.

**Primitive: PERSISTENT_FALLING_AFTERIMAGE**

The hit is brief; the visual signature is the lingering aftermath.

---

# 15. Love Breathing

Representative:

- `BreathesKoi1/2/3/5/6Procedure`
- `BreathesKoiSwingProcedure`

The style contains:

- body velocity
- trigonometric sweep paths
- repeated DoDamage2
- repeated BlockDestroy2
- SwingKoi
- animation

It has little dedicated particle infrastructure.

**Presentation interpretation**

The "ribbon" feeling comes from repeated, curved spatial samples of the weapon/body trajectory rather
than an elemental billboard.

This is a useful technique for flexible/whip weapons:
draw the path with animation and hit samples, not a generic projectile.

---

# 16. Sound Breathing

Representative:

- `BreathesOto1/4/5Procedure`

Forms 4/5 use:

- PARTICLE_SPARK_FIRE
- firework explosion sound
- attack sweep sound
- body movement
- DoDamage2
- BlockDestroy2

SparkFire's short animated 14-frame burst makes the impact timing read as an explosion.

**Primitive: IMPACT_BURST**

The visual does not need to persist because the combat identity is rhythmic detonation.

---

# 17. Moon Breathing

Representative:

- `BreathesTsuki1/2/3/5/6/7/8/9/10/14/16Procedure`
- `BreathesTsukiTransformProcedure`

This style uses the richest particle vocabulary.

## 17.1 Crescent hierarchy

- MOON_1
- MOON_1_MED
- MOON_2
- MOON_2_MED
- MOON_2_LAR
- MOON_PHASE

Different physical sizes are separate particle types.

This gives authored form code direct semantic choices:

```text
small crescent
medium crescent
large crescent
phase marker
```

rather than arbitrary per-call scaling.

## 17.2 Forms 14 / 16

Use medium + large Moon2 particles at sampled positions.

Form 16 representative attack context:

- Damage around 21 * Strength scaling
- Range 5
- knockback 1
- projectile_type 1
- DoDamage2
- BlockDestroy2

The huge 12-scale short-lived crescent makes each sampled attack volume visible as a distinct slash
plane.

## 17.3 Form 10

Spawns:

- `SLASHING_MOON`

Renderer texture:

`textures/entities/slashing_moon10.png`

The helper has its own AI/provenance relationship and emits Moon particles.

## 17.4 Moving moon projectile

`BULLET_SLASHING_MOON_PROJECTILE`

uses a while-flying Procedure that repeatedly calls the attack kernel.

**Primitive: MOBILE_AOE_PROJECTILE**

The visual projectile and attack volume travel together.

---

# 18. Sun / Hinokami Kagura

Representative:

- `BreathesHi1..12Procedure`
- `BreathesHi13Procedure`

Unlike Moon, there is no one giant dedicated particle palette for every form.

Presentation is composed from:

- body animation
- movement
- sampled hit volumes
- Flame particle in selected form(s)
- creature helper in Hi6
- higher-order sequence in Hi13

## 18.1 Sixth Form helper

`BreathesHi6Procedure`

Spawns:
- `FLAME_DRAGON`

and moves the user at roughly 0.8 of stored forward power during an observed phase.

The helper provides the large fire-creature silhouette.

## 18.2 Thirteenth Form

No unique projectile/particle grammar.

It sequences forms 1–12.

Therefore its VFX is a **composed montage**:

```text
form1 visual
 -> form2 visual
 -> ...
 -> form12 visual
```

**Primitive: TECHNIQUE_SEQUENCE**

This avoids creating one monolithic 13th-form renderer.

---

# 19. Stone Breathing

Representative:

- `BreathesIwa1..5Procedure`

Every form uses:

- `HIMEJIMA_WEAPONS`
- SetRangedAmmo
- DoDamage2
- BlockDestroy2
- animation

The helper has:

- `geo/himejima_weapons.geo.json`
- `animations/himejima_weapons.animation.json`

and dynamic texture/model behavior.

## 19.1 Iwa1

Additionally:

- trigonometric geometry
- ParticleGeneratorCircle
- multiple DoDamage2 passes
- multiple block-destroy passes
- explode sound
- sweep sound

## 19.2 Iwa5

Uses multiple body-velocity changes and a detached weapon actor.

## Architecture

```text
Owner
  - state / damage authority
  - animation opcode
  - attack kernel

HimejimaWeapons
  - chain/ball/axe visual geometry
  - form-specific animation
  - owner-linked lifetime
```

**Primitive: DETACHED_WEAPON_RIG**

This is the strongest reference in the JAR for chain weapons or visually separated melee weapons.

---

# 20. Bamboo Breathing

Representative:
`BreathesTake1..12Procedure`

Many forms use `PARTICLE_BAMBOO`.

The particle:

- has physical collision
- does not fall under gravity
- persists ~20–39 ticks

This allows shards/leaves to remain spatially coherent around the attack rather than immediately
dropping.

The style also mixes:

- normal DoDamage2
- block destruction
- helper/provenance paths in selected forms
- authored novelty effects (e.g. Take10 contains a `panda_face` summon command)

For reuse, treat the novelty actor separately from the core bamboo particle/trajectory grammar.

---

# 21. Cherry Blossom Breathing

Representative:
`BreathesSakura1..6,8..10Procedure`

Nearly all forms reference:

- PARTICLE_CHERRY_BLOSSOM

Many also combine:

- trigonometric arc geometry
- sword_sweep / sword_putin sounds
- body movement
- DoDamage2
- BlockDestroy2

Because petals:

- last ~30–49 ticks
- use gravity
- have collision physics

the slash leaves a persistent falling spatial record.

**Presentation rule**

The attack path should be fast.
The style identity can remain in the environment after the hitbox is gone.

---

# 22. Senior/custom bucket

`PlayerBreathSeniorProcedure` dispatches nonstandard techniques:

- BreathesDicesteak1..4
- BreathesHikkondero
- BreathesOraa
- BreathesSyusse
- BreathesTyodoiikurainoonigairuzyaneka

DiceSteak uses Lightning particle vocabulary and ordinary damage/block kernels.
Others use direct power/effect logic.

These are recorded separately so they do not distort the main style taxonomy.

---

# 23. Visual geometry vs hit geometry

One of the most important findings is that the target uses several relationships.

## 23.1 Coincident

Visual and damage occupy roughly the same space.

Example:
- Nagi ring / local Range field

## 23.2 Visual actor, owner damage

Visual helper moves, but owner Procedure owns damage.

Examples:
- Constant Flux
- Flame creature
- Himejima weapons

## 23.3 Invisible actor geometry

Helper has no meaningful texture but carries trajectory/provenance.

Example:
- Serpent SNEAK/SNEAK_2

## 23.4 Projectile owns moving AoE

Visual projectile and damage emitter are the same moving actor.

Example:
- Bullet Slashing Moon

## 23.5 VFX aftermath only

Particle remains after damage already ended.

Examples:
- Flower
- Cherry Blossom

This distinction should be explicit in any KNEEKURA combat-effect framework.

---

# 24. Reusable VFX / trajectory primitives

Recommended independent primitives:

## BodyDash

```text
chargeTicks
direction
speedProfile
hitSampleInterval
trailProfile
exitPolicy
```

Best references:
- Thunderclap and Flash
- Flame dash forms
- Insect thrusts

## LocalField

```text
center
radius
visualRing
damagePolicy
projectilePolicy
duration
```

Best reference:
- Nagi

## SampledArc

```text
basis
angleRange
radius/forward distance
sampleCount
visualProfile
attackContext
```

Best references:
- Wind
- Love
- Moon
- Cherry

## VisualHelperActor

```text
owner
trajectory
model
animation
lifetime
visualOnly / combatAware
```

Best references:
- Constant Flux
- Flame creature
- Wind claws

## HiddenTrajectoryProxy

Same as helper actor but without visible renderer.

Best reference:
- Serpent

## DetachedWeaponRig

```text
owner
weapon animation
chain/endpoint geometry
attack sampling
block interaction
```

Best reference:
- Stone

## MobileAoEProjectile

```text
trajectory
lifetime
attackVolumeEveryTick
visual projectile
block interaction
```

Best reference:
- Moon projectile

## PersistentAfterimage

```text
particle
spawnPath
lifetime > attackLifetime
physics
gravity
angularDrift
```

Best references:
- Flower
- Cherry Blossom

## TechniqueSequence

```text
steps: List<TechniqueProgram>
transitionPolicy
counterResetPolicy
visual continuity
```

Best reference:
- Sun 13th Form

---

# 25. Recommended separation for a new combat system

Do not implement a technique as one giant Procedure.

Use:

```text
TechniqueProgram
 |
 +-- MovementTrack
 |
 +-- AttackTrack
 |
 +-- VfxTrack
 |
 +-- AnimationTrack
 |
 +-- SoundTrack
 |
 +-- WorldInteractionTrack
```

All tracks share one local timeline but can be independently authored.

Example — Nagi:

```text
MovementTrack:
  damp/hold actor

AttackTrack:
  Range 7 field, projectile cut

VfxTrack:
  2 concentric 72-point rings

AnimationTrack:
  defensive stance

SoundTrack:
  calm

WorldInteraction:
  none
```

Example — Thunderclap:

```text
MovementTrack:
  charge -> high-speed forward dash

AttackTrack:
  repeated sampled Range 3 volume

VfxTrack:
  lightning + thunder streaks

AnimationTrack:
  draw/iai -> dash

SoundTrack:
  breath / electric shock / sweep

WorldInteraction:
  selected forms may destroy blocks
```

This makes combat presentation reusable without copying whole techniques.

---

# 26. Performance implications

No benchmark was run.

Mechanism-level cost risks:

## Particle storms

Nagi can author hundreds of particle instances in a single active frame.

Large Moon/Wind cards are also expensive visually because of large transparent quads.

## Helper actors

Constant Flux, flame creatures, Wind claws, Stone weapon rig and Moon helpers are full Entities with
tracking/tick/render costs.

## Sampled AoE

Trigonometric slash procedures may call DoDamage2 at many spatial positions.

## Block destruction

Many high-tier forms call BlockDestroy/BlockDestroy2 during the attack.

## Combined load

The expensive case is not "many particles" alone.

It is:

```text
body movement
+ particles
+ helper entity
+ repeated AABB attack queries
+ block edits
+ sounds
+ animation sync
```

in the same tick window.

For reconstruction, budget these tracks independently.

---

# 27. Strongest battle-presentation lessons

1. **Use the body as the projectile** for very fast martial techniques.
2. **Use a visual helper actor** when the effect has recognizable anatomy or weapon geometry.
3. **Use invisible helpers** when combat geometry must bend independently from visuals.
4. **Use huge short-lived particles** for slash planes; do not simulate them as dozens of tiny dust
   particles.
5. **Use long-lived physical particles** only when the style benefits from aftermath.
6. **Make VFX scale hierarchy explicit** (Moon small/medium/large) instead of arbitrary ad-hoc scale.
7. **Align visual and hit geometry intentionally**, not accidentally.
8. **Separate attack timeline from VFX timeline** so lingering petals do not keep damaging.
9. **Compose complex forms from lower forms** when their identity is a sequence.
10. **Treat block interaction as its own track**, not an automatic side effect of every strong VFX.

---

# 28. Static boundaries

This atlas does not claim:

- exact runtime camera appearance
- exact frame-by-frame PlayerAnimator pose for every form
- FPS/TPS cost
- shader/OptiFine behavior
- every particle spawn count for all 100+ individual form procedures
- exact old-version trajectory differences

It does establish:

- the breathing-form surface
- major movement/attack/VFX architectures
- style-specific particle/helper resources
- representative exact trajectory math
- the reusable presentation primitives
