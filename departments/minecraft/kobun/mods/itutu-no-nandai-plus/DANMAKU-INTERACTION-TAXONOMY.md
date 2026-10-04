# DANMAKU INTERACTION TAXONOMY — 五つの難題MOD+ X1

Status: MODERN-EXTRACTION derived from ORIGINAL_SOURCE / ORIGINAL_BINARY

This document focuses on what can be done to an existing bullet field, not only how bullets are spawned.

## One shared combat language

Spell cards, player items and normal mobs reuse the same broad substrate:

ShotData / LaserData -> THShotLib geometry -> EntityTHShot / EntityTHLaser -> SpecialShotRegistry behavior.

The main difference is who drives the timeline: scripted spell, player input, mob attack counter, or persistent controller entity.

## CUT

Historical example: Roukanken.

Semantics: hostile bullet -> blade sweep -> consume original -> emit small visual fragments.

This makes bullet destruction an active spatial action instead of passive invulnerability. Lasers are explicitly excluded.

Modern reusable verb: CUT(projectile, cutter, contact).

## REFLECT

Historical example: Hakurouken.

Semantics: hostile projectile -> reflect plane -> consume -> create a player-owned normalized countershot.

Reflection changes both defense and ownership/offense.

## PURGE

Historical example: Spiritual Strike Talisman.

An expanding radial field clears nearby EntityTHShot through shotFinishBonus while hostile living entities are knocked outward/upward.

This resets both projectile density and local enemy positioning.

## REDIRECT

Historical example: Sukima.

A shot entering portal A exits portal B with position transformed, heading recomputed from portal orientation relation and speed magnitude preserved.

The projectile remains conceptually the same attack while its trajectory changes.

## TIME / FREEZE

Historical examples: Sakuya Watch, StopWatch, Perfect Freeze and Satsujin Doll.

World/entity time manipulation and projectile frozen-state manipulation are related but distinct.

A modern design should model:
- world time-domain policy;
- projectile trajectory state = FROZEN;
as separate concepts.

Do not reproduce the broad 1.7.10 rollback tables literally.

## Input-coupled attack controllers

Non-spell attacks use player input/state heavily:

- Roukanken: charge -> player dash velocity;
- Onmyoudama: hold -> size, release -> projectile;
- NuclearShot: hold -> size/damage, release -> recoil;
- SanaeWind: player displacement/sneak -> projectile behavior;
- Yuuka Parasol: deployed state -> movement stance;
- Hakurouken: crouch -> reflector, normal use -> brake.

Reusable split: input controller -> effect state -> physical projectile/beam/movement action.

## Environment-to-attack conversion

Examples:
- Aja Red Stone: ambient block light -> beam power/geometry;
- Kinkakuji: downward speed -> crush damage;
- Sukima: portal orientation -> outgoing shot heading;
- NuclearShot: held charge -> size/damage/recoil.

World and motion state become attack parameters.

## Controller + effect entity

Repeated architecture:

| Controller/input owner | World effect |
|---|---|
| Mini Hakkero | persistent Master Spark LaserB |
| Nuclear Control Rod | EntityNuclearShot |
| Aja Red Stone effect | released LaserA |
| Sakuya Watch item | time-control entity |
| Yuuka Parasol item | deployed parasol |
| Sanae ritual | EntityMiracleCircle stages |

The controller owns input/lifetime/charge. The effect entity owns trajectory/collision/world presence.

## Item-hosted pseudo-spells

ID7 全人類の緋想天 and ID27 Spear the Gungnir are important X1 boundaries.

Their active registered spell-card classes lack spellcard_main, yet the visible techniques exist through items/special entities.

- Hisou item -> EntityHisou main sword + seven afterimages -> repeating KISHITU shots.
- Gungnir item -> GUNGNIR LaserA + secondary-ring behavior.

Declaration/permission and effect implementation are separate subsystems.

## Physical projectile vs lightweight danmaku

EntityTHShot is suitable for large lightweight fields with shared trajectory logic.

SilverKnife, Kinkakuji and NuclearShot are bespoke physical world projectiles with sticking, collision persistence, large-object or held-charge semantics.

A modern system should preserve this distinction.

## Visible charge telegraph entities

MiracleCircle, AjaRedStoneEffect, NuclearShot and Onmyoudama expose stored power visibly in the world before release.

Reusable pattern: charge source -> visible telegraph state -> release transform -> final attack.

## Normal attacks as mechanic onboarding

Examples:
- Wriggle normal -> state-machine vocabulary later amplified by Little Bug Storm;
- Toziko normal -> stop/re-aim/relaunch;
- generic fairies -> ring/sphere/fan/laser grammar;
- Cirno normal -> bullets then lasers;
- Sanae normal -> moving geometric emitter.

Normal attack teaches the verb; spell card recombines or amplifies it.

## Difficulty as topology

Across mobs/items/spells, difficulty can modify ways, emitter count, projectile form, interval, speed, laser presence/width and supplemental layers.

A modern difficulty model should alter a pattern graph, not merely multiply bullet count.

## Visual state as combat information

Examples:
- DivineSpirit color = detected target category;
- Remorse Rod glow = usable state;
- MiracleCircle stages = ritual progress;
- Onmyoudama/NuclearShot size = stored power;
- Perfect Freeze white = frozen projectile;
- Satsujin Doll green = re-aimed knife;
- Little Bug Storm form/color = internal trajectory phase.

Visuals communicate combat state.

## Recommended modern interaction vocabulary

A typed modern API could expose:

CUT, REFLECT, PURGE, REDIRECT, FREEZE, RELEASE, SPLIT and BOUNCE.

Each operation should define ownership transition, identity survival, position/heading transform, speed transform, damage transform, visual-state transition, allowed projectile classes and server authority.

## Historical implementation boundary

Do not literal-port:
- global integer special-shot IDs;
- Class.newInstance;
- numeric DataWatcher slots;
- direct SRG method names as stable APIs;
- immediate GL11 rendering;
- large unbudgeted per-tick AABB scans;
- old Java packet/object assumptions;
- time stop as broad state rollback.

Preserve observable verbs and trajectory semantics, not the 1.7.10 mechanism.

## Dead-code reachability rule

Houtou's commented attack, old EntityMasterSpark and EntityTHHenyoriLaser show that combat-looking classes can survive after the live path moved elsewhere.

An effect is ACTIVE only when the supplied X1 artifact has a reachable registration/call path.
