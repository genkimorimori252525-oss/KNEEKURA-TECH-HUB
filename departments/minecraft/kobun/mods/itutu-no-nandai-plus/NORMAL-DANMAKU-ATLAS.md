# NORMAL-DANMAKU ATLAS — 五つの難題MOD+ X1

Status: ORIGINAL_SOURCE / ORIGINAL_BINARY static analysis; runtime NOT_RUN

Scope: non-spell enemy danmaku, ordinary attack cycles, generic fairy pattern machinery, familiars and support entities in the supplied X1 distribution.

This document excludes active THSpellCard.spellcard_main timelines and complements SPELLCARD-ATLAS.md.

## Generic fairy pattern interpreter

EntityTHFairy is a data-driven attack interpreter. Its encoded danmakuPattern families map broadly as follows:

| Encoded range | High-level family |
|---:|---|
| 0–999 | multi-speed sphere / shell |
| 1000–1999 | wide fan / laser |
| 2000–2999 | multi-speed circle |
| 3000–3999 | random cone / random ring |
| 4000–4999 | ring pattern |
| 5000–5999 | 360-degree random fire |

The active path is DanmakuPatternRegistry -> EntityTHFairy interpreter -> THShotLib geometry -> EntityTHShot / EntityTHLaser.

## DanmakuPatternRegistry difficulty

The supplied X1 registry contains generic profile keys 000–007 plus laser-oriented 064 for each danmaku level.

Difficulty can alter projectile form, ways, interval, speed, span, laser use and secondary density. Ordinary-fairy difficulty is therefore topological, not merely a damage multiplier.

## Sunflower Fairy + Familiar

EntitySunFlowerFairy creates a mounted EntityFamiliar. The familiar inherits the generic fairy pattern engine, follows the riding creature's target and attributes shooting to the root living owner.

Reusable authority chain:

owner mob -> familiar emitter -> danmaku

The familiar is a mobile secondary firing origin, not decoration only.

## Cirno normal pattern 1 — layered crystal rings

After the opening wait, Cirno creates seven delayed AQUA crystal layers with ways increasing 2, 3, 4, 5, 6, 7, 8. Speed and angular span scale with difficulty.

The pattern progressively fills the angular gaps and functions as a compact progressive-density pattern.

## Cirno normal pattern 2 — circles into lasers

Early phase: dual circular bullet layers at roughly six-tick cadence.

Later phase: three separate 3-way white laser fans around counters 55, 65 and 75.

Threat grammar changes from bullet dodging to beam exclusion inside one normal attack cycle.

## Rumia normal danmaku

The sequence combines fast blue and red rings, strong deceleration, lateral caster movement and later low-speed tiny colored circles.

Fast bullets first occupy space, then remain as slow hazards while the emitter itself repositions.

## Sanae normal — five-point-star emitter

Across roughly 50 ticks the firing locus walks along subdivided edges of a five-pointed star. Each geometric point is transformed into a view-relative plane and becomes the origin of a tiny blue shot.

The projectile begins near zero speed and accelerates toward about 0.5.

Key technique: the geometric curve itself is the moving emitter path.

## Wriggle normal phase system

The first phase alternates positive/negative angular streams using the same special-shot state machinery later reused by Little Bug Storm. Higher difficulty adds interleaved offset streams.

A later phase emits decelerating five-way yellow fans.

### X1 control-flow defect

Movement branches around attack counters 24 and 67 are unreachable because earlier if/else-if ranges already consume those values. This is a source-level defect, not a runtime-reproduced bug.

## Toziko normal — stop, re-aim, relaunch

During the early part of an approximately 80-tick cycle, Toziko emits 1 + difficulty-level blue arrow shots from spread random positions.

The arrows decelerate toward zero.

At their dead-time transition, SPECIAL_TOZIKO01 reads the mob's current target, re-aims each stopped arrow, resets speed to about 0.01 and accelerates it toward a difficulty-scaled limit.

Pattern: place -> stop -> retarget -> relaunch.

## Danmaku Creeper / Hanabeeper

The Creeper-style fuse climax produces spherical danmaku rather than the normal destructive block explosion.

Three projectile shells are emitted: GREEN, RED and YELLOW. Difficulty way counts use 8, 12, 20, 32, 44.

Powered state doubles projectile damage and raises the fast green layer to about 1.2 speed.

Explosion sound remains; normal world/block explosion calls are commented out in X1.

The vanilla expectation of an explosion is converted into radial bullet space control.

## Reimu / Sakuya / Miko normal-attack boundaries

The supplied X1 classes do not provide active ordinary danmaku branches comparable to Cirno/Rumia/Sanae. Relevant branches are commented or empty.

Their item/spell mechanisms are kept separate and are not projected backward into nonexistent normal patterns.

## EntitySanaeWind

This projectile is coupled to the user's actual displacement/state instead of relying only on a fixed launch vector. Sneaking can force downward gravity behavior.

Together with WIND01, the projectile strongly displaces targets and can exploit airborne state.

## EntitySukima

EntitySukima has distinct uses.

- item portal: teleports and reorients existing EntityTHShot while preserving speed magnitude;
- Hikouchuu Nest route: color/state 17 is used as delayed laser infrastructure.

Utility portal behavior and spell-emitter behavior are not conflated.

## EntityDivineSpirit

Created by Miko Sword. Color represents target category, spawn point tracks the detected target, and the spirit can live about 300 ticks while orienting/moving toward a nearby player.

This is a visual information entity rather than ordinary damage danmaku.

## EntityMiracleCircle

Created during long Sanae-rod use. Roughly every 30 ticks a later pentagram stage can appear. The visible chain records ritual/charge progress used by the item to charge miracle cards.

This is a visible charge-state entity.

## Dormant/displaced effect classes

EntityTHHenyoriLaser and the older dedicated EntityMasterSpark remain in the tree, but active X1 registration/use is not established.

Current item Master Spark uses EntityMiniHakkero plus the generic laser system instead.

Named classes are historical clues; active registration and reachable call paths control gameplay claims.

# Normal-battle design lessons

1. Normal attacks teach mechanics later amplified by spell cards.
2. Moving firing loci can draw geometric figures in world space.
3. Vanilla events can be converted into danmaku, as Hanabeeper does with the Creeper climax.
4. Ordinary enemies can be data-driven consumers of a shared pattern registry.
5. Difficulty can change topology, not just count or damage.
6. Mobs, items and spell cards share one projectile language.
