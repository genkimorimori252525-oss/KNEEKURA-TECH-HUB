# QB-MOD 1.6.4.082 — Projectile / trajectory catalog

Primary evidence:
- QB-MOD archive SHA-256 `52b1ba0774e098795dcf1ed9a489c66414ea725235978171f48a10db7287ba4e`
- Garnet-MOD archive SHA-256 `5f778c8949dcce95dcd56dacd9242f117bc17f03879bab48cb667ba2a3c82778`

This document separates projectile mechanics from character identity so future KNEEKURA systems can reuse trajectories without copying an entire NPC design.

## Garnet projectile foundations

### EntityGarnetArrow

A custom arrow-like physical projectile:
- normalizes the requested direction;
- applies Gaussian spread scaled by inaccuracy;
- sets velocity directly from speed;
- rotates model to velocity vector;
- ray-traces blocks and entities;
- ignores its shooter for the first 5 air ticks;
- persists embedded in blocks up to 1200 ticks;
- applies drag and gravity;
- computes impact damage from projectile speed × configured damage;
- carries critical, fire and knockback state.

Targeted constructor computes aim vector using target position/eye height and adds a range-dependent upward term before `setThrowableHeading`.

This is a conventional ballistic base.

### EntityGarnetThrowable

A lighter EntityThrowable-derived base:
- targeted constructor computes target direction directly;
- damage scales from current motion magnitude;
- supports fire and knockback;
- attempts to attribute damage to player/owner correctly for tameable entities.

This is the base for LightArrow, Claw, FireLance, Spear2 and Garnet bullets.

### Shared multi-hit contract — reset vanilla hurt-resistant time

Both Garnet projectile foundations deliberately clear the struck entity's vanilla post-hit immunity timer immediately before applying damage:

- `EntityGarnetArrow`: `entityHit.hurtResistantTime = 0` before `attackEntityFrom`;
- `EntityGarnetThrowable`: same reset before its thrown-damage attempt.

The distributed class bytecode contains the corresponding write to obfuscated `Entity.field_70172_ad` in both implementations.

This is a major combat-system invariant. Dense patterns such as:
- Madoka 8/20-arrow bursts;
- Homura 31-shot rifle burst;
- Kyouko 24-Spear burst;
- Mami rapid staged-Musket shots;

are not merely visually dense: the projectile substrate is designed so successive impacts are not mostly swallowed by Minecraft's ordinary hurt-resistance window.

Technique:
**projectile-layer multi-hit authorization by explicitly resetting target i-frames**.

ANCHOR caution:
do not blindly assign modern `invulnerableTime = 0` everywhere. That can bypass compatibility expectations, armor/damage-event pacing and other mods' combat rules. Prefer an explicit multi-hit policy with:
- per-attack / per-source hit cadence;
- target hit budget;
- DamageType/event compatibility;
- boss immunity rules;
- telemetry for simultaneous projectile bursts.

### Shared burning-projectile block ignition

Both Garnet projectile foundations also contain a common incendiary block-impact rule.

When the projectile is burning and hits a block:
1. the hit side is converted into the adjacent cell;
2. if that adjacent cell is air;
3. the projectile places vanilla Fire there.

This behavior exists in:
- `EntityGarnetArrow`;
- `EntityGarnetThrowable`.

So Fire Aspect / burning state can affect more than entity damage: it can **ignite world geometry at the collision face**.

This matters for character/item attacks that propagate fire enchantment into projectiles.

Technique:
**projectile elemental state → local world interaction at impact face**.

ANCHOR should route this through:
- server-side mob-griefing/config policy;
- block protection hooks;
- encounter/world-edit policy where appropriate.

### Throwable critical mode — impact becomes an explosion

`EntityGarnetThrowable` treats its synchronized critical bit as an explosive modifier:

- critical entity impact → creates explosion strength **6.0**, block damage enabled, then clears target hurt-resistant time and applies projectile damage;
- critical block impact → creates explosion strength **4.0**, block damage enabled;
- burning block impact can ignite an adjacent air block;
- impacting TNT currently removes the TNT block; a commented TODO shows an abandoned explicit TNT-explosion interaction.

`EntityGarnetBullet` extends `EntityGarnetThrowable`, so any bullet marked critical inherits this explosion behavior.

This makes `critical` semantically much stronger than vanilla arrow critical particles/damage: it is a **projectile-mode switch into explosive impact**.

---

## Light Arrow family

### EntityLightArrow

Mostly GarnetThrowable behavior plus full-bright rendering behavior.

Technique: **projectile identity can be primarily visual while sharing physical damage logic**.

### EntityLightArrow2 — expanding-search homing

Key state:
- `tickSearch` increases to max 200;
- existing target is cleared if dead.

After the first 3 ticks, if no target:
- searches `EntityLivingBase` in an AABB expanding by `tickSearch * 0.25` on each axis;
- sorts candidates by distance;
- filters thrower, owner, allied tameables/servants and optionally broad friendly/entity classes;
- selects the first eligible target.

With a target:
- every server update recomputes direction to target;
- calls `setThrowableHeading(..., 1.2F, 0.5F)`;
- this is hard steering rather than proportional navigation.

Impact behavior:
- if it currently has a target, collisions with anything except the selected target are ignored;
- without target it uses normal impact behavior.

Damage behavior:
- after search begins, bonus grows with search age: approximately `ceil(tickSearch/5)*0.3 - 1`, capped at +5;
- the first 3 ticks report zero dynamic damage through this override.

Technique: **delayed target acquisition + expanding search radius + target-lock collision filtering + age-scaled damage**.

### EntityLightArrow3 — percentage-health homing strike

Extends LightArrow2.

If it hits its selected target:
- target current HP is first replaced by `floor(max(currentHP * 0.95, 1))`;
- Enderman receives direct `setDead`;
- then base impact processing continues.

If it has no target and search age reaches 100:
- block impact can resolve normally;
- hitting another entity instead destroys the projectile.

Technique: **homing projectile with pre-impact health transform and late no-target cleanup behavior**.

High-risk ANCHOR portability: direct health mutation can bypass armor, invulnerability, modded damage hooks and boss rules.

---

## Spear family

### EntitySpear

GarnetArrow-derived thrown spear.

Targeted constructors intentionally add randomized lateral offsets around the target before setting heading. Against the normal character combat loop, multiple Spears are emitted in one burst, creating a loose spread around the target volume.

Technique: **world-space target-volume scatter rather than only angular inaccuracy**.

### EntitySpear2 — impact fan-out

EntitySpear2 is a Throwable that acts as a carrier.

On impact:
- if it hits a living entity, spawns 6 EntitySpear projectiles aimed around that entity;
- if it hits terrain, spawns 6 EntitySpear projectiles using the impact/carry projectile as spatial reference;
- propagates damage, knockback and fire state to children;
- then resolves its own base impact.

Technique: **parent projectile → collision-triggered radial/secondary projectile fan-out**.

---

## Cutlass and Musket world props

`EntityCutlass` and `EntityMusket` are thin `EntityGarnetArrow` specializations.

Their special behavior is not in the projectile class but in the character AI:
- spawned at coordinates with effectively no initial targeted velocity;
- remain as world entities / props;
- later character logic searches nearby instances, kills one, and converts that staged prop into a real attack.

Technique: **world projectile entity reused as a visible attack token / ammo reservoir**.

This is valuable because presentation and combat state are represented by the same entity instead of a separate invisible counter.

---

## Fire Lance

`EntityFireLance` customizes aim and impact.

On impact:
- Walpurgisnacht is explicitly exempted from normal impact handling;
- terrain impact removes the struck block if it is not bedrock or Kyouko Shield.

Technique: **projectile as localized block-cutting attack**.

ANCHOR rewrite should route block damage through a permission/budget policy rather than direct `setBlock(..., 0)`.

---

## Prickle

`EntityPrickle` is an Arrow that becomes a delayed summon anchor.

Behavior:
- after embedding in terrain for >20 ticks;
- spawns an `EntityShadowPuellaMagi` at the embedded position;
- if shooter was Walpurgisnacht, the Shadow receives a reference back to Walpurgis;
- emits explosion particles and removes the projectile.

Impact against Walpurgis itself is specially suppressed.

Technique: **projectile → persistent embedded seed → delayed minion spawn**.

This is a high-value boss pattern because the shot changes role over time: damage projectile first, spawn anchor after landing.

---

## Shadow Puella Magi

Prickle-spawned `EntityShadowPuellaMagi`:
- randomly chooses one of 7 magical-girl visual/weapon types;
- attacks players/ageable/Garnet entities;
- can report kills back to its parent Walpurgis reference.

Technique: **projectile-spawned minion retaining encounter-owner callback**.

ANCHOR should store an encounter UUID/id rather than raw entity reference where persistence matters.

---

## Wheel

Oktavia's `EntityWheel` is not a conventional projectile, but acts as a kinetic hazard:
- 1 HP;
- movement speed 0.6 and 3 attack;
- spawned at random positions in a 10×10×10-ish volume around Oktavia;
- initial motion is set directly toward target;
- cannot be damaged by non-living/environmental sources.

Technique: **disposable mob projectile / kinetic hazard**.

It combines entity AI and initial ballistic motion, useful when a projectile should remain targetable after launch.

---

## Homura / Yuri TNT as trajectory systems

Primed TNT is used as a combat projectile in two forms.

### Homura
- spawns TNT in target space after teleport;
- TNT inherits target motion vector;
- fuse shortened;
- Walpurgis special branch uses fuse 1.

This is **motion-matched explosive planting**.

### Yuri / Walpurgis-style terrain conversion
- connected-block search chooses terrain cells;
- each selected block position becomes stationary primed TNT;
- hazard is encoded into the terrain topology rather than fired through the air.

This is **terrain-to-projectile/hazard conversion**.

---

## Trajectory taxonomy recovered from this MOD

1. ballistic with Gaussian spread — GarnetArrow;
2. direct throwable — GarnetThrowable/Bullet;
3. target-volume randomized scatter — Spear;
4. multi-shot volley — Madoka/Kyouko patterns;
5. delayed acquire-and-home — LightArrow2;
6. launch-upward then home — Madoka Ultimate;
7. collision-locked homing — LightArrow2/3;
8. parent-on-impact fan-out — Spear2;
9. staged stationary world prop → later shot — Cutlass/Musket;
10. embedded projectile → delayed summon — Prickle;
11. disposable mob used as kinetic projectile — Wheel;
12. target-motion-matched explosive — Homura TNT;
13. terrain cell → stationary explosive hazard — Yuri/Walpurgis family;
14. block-cutting projectile — FireLance.

These should be preserved as independent trajectory primitives for the future LAB motion/trajectory viewer.