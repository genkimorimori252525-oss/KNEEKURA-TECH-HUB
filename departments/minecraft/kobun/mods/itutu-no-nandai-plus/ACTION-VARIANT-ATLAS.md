# ACTION-VARIANT ATLAS — 五つの難題MOD+ X1

Status: ORIGINAL_SOURCE / ORIGINAL_BINARY static analysis; runtime NOT_RUN

Scope: combat and combat-adjacent effects whose behavior changes according to player action/state rather than item identity alone.

This document answers a different question from the spell/non-spell atlases:

What changes when the player sneaks, holds use longer, moves, is grounded, changes item, aims at a world target, or changes contextual state?

## Quick map

| Item / system | Input | Normal result | Variant result |
|---|---|---|---|
| Homing Amulet | Sneak | 5-shot 100-degree fan | 2-shot 20-degree high-damage focus |
| Generic THShot | Sneak | configured spread | applicable cone/fan/ring widths halve |
| Generic THLaser | Sneak | configured spread | applicable laser spread widths halve |
| Dragon Neck Jewel | Sneak + pristine durability | one random-color jewel | five fixed-color jewels at -40..+40 degrees |
| Hourai Jeweled Branch | Sneak | forward nested rings | omnidirectional multi-speed circles |
| Yuyuko Fan | Sneak | mirrored forward butterfly fans | paired full-circle butterfly layers |
| Hakurouken | Sneak | moving-ground brake | bullet reflector plane |
| Death Scythe | Sneak | pull | push |
| Kinkakuji ceiling | Sneak | upward speed 0.7 | upward speed 1.0 |
| Laevateinn | Sneak | normal beam-blade frame | alternate / vertical beam-blade frame |
| Kappa Water Pistol | Sneak + source water | three-shot water attack | refill 2 durability, no attack |
| Sukima | Sneak | near / looked-block portal | long-range portal pair via ray |
| Sakuya Watch | Sneak | begin use in stored mode | toggle half-speed / full-stop mode |
| Yuuka Parasol | Sneak | prepare charged flower barrage | deploy parasol entity / cycle its modes |
| Miko Sword | Sneak | spawn spirits + chat report | spawn same spirits but suppress chat |
| Marisa Broom | Sneak | spawn and auto-mount | spawn without auto-mount |
| Tengu Fan | Hold duration | low-speed wind | progressively faster wind shot |
| Roukanken | Hold + grounded | weak dash | charge-scaled dash up to 6.0 |
| Miko Sword | Hold duration | small scan | radius grows to 50 |
| Yuyuko Fan / Hourai Branch | Hold duration | low density | way/density grows to cap |
| Nuclear Control Rod | Hold / item switch | growing held nuke | release + recoil / switch-away explosion |
| Hakurei Oharaibou | Hold | small held orb | orb grows to size3 before release |
| Sanae Oharaibou | Hold thresholds | wind attack | ritual/card charging after 30+ ticks |
| Aja Red Stone | Hold in environment | weak/no beam | accumulated block light grows final beam |
| ItemTHLaser | adjacent dye slot | default/random color | dye overrides laser color |

## 1. Homing Amulet — Shift focus mode

The red Homing Amulet explicitly labels the sneak branch as low-speed mode, but the projectile speed remains 0.7 in both branches.

### Normal

- 5 shots
- 100-degree total spread
- shot size 0.4
- damage 5
- HOMING01
- speed 0.7

### Sneak

- 2 shots
- 20-degree total spread
- shot size 1.0
- damage 8
- HOMING01
- speed 0.7

The real semantic change is therefore:

wide low-per-shot output -> narrow high-per-shot focus

This is very close to the Touhou focus-shot idea: Shift changes concentration and attack shape rather than simply making bullets slower.

The blue Diffusion Amulet is a separate item-damage variant and does not use the same sneak branch.

## 2. Generic THShot — Shift narrows only applicable shapes

ItemTHShot forwards player.isSneaking() into shootDanmaku as isSlowMode.

Sneak changes:

- random cone: 120 degrees -> 60 degrees
- forward n-way: width -> width x 0.5
- ring: 15 degrees -> 7.5 degrees

Sneak does not change:

- point
- full circle
- sphere

This is an important design rule: focus affects angularly ambiguous forward patterns, but not inherently 360-degree geometries.

## 3. Generic THLaser — same focus grammar

Shift halves applicable laser spread:

- random-ring: 30 degrees -> 15 degrees
- forward wide fan: width x 0.5
- ring: 15 degrees -> 7.5 degrees

Point, full-circle and sphere laser forms are unchanged.

### Adjacent-slot dye input

The hotbar slot immediately to the right of the selected laser item is inspected. If it contains dye, its metadata is mapped to the laser color.

One attack can therefore depend simultaneously on:

- configured NBT pattern;
- current Shift/focus state;
- neighboring inventory slot.

## 4. Dragon Neck Jewel — normal shot vs five-color finisher

### Normal

Condition: not sneaking and durability damage <229.

- fires one jewel
- direction = current aim
- jewel color = random one of five
- durability cost =70

### Sneak

Condition: sneaking and item damage <1, effectively pristine state.

- fires five jewels
- angles = -40, -20, 0, +20, +40 degrees
- each jewel uses one of the five fixed colors
- durability cost =299

Each jewel retains the same impact bloom into colored lasers/light shots.

Shift is therefore not a mild focus change. It is an expensive multi-carrier finisher gated by weapon condition.

## 5. Hourai Jeweled Branch — forward formation vs omnidirectional shell

Charge first controls shotNum:

32 + heldTicks, capped72, then divided by3 for the local parameter.

### Normal

Three nested ring/cone layers around the current look axis:

- N ways / 15-degree span
- N/2 ways / 10-degree span
- N/3 ways / 5-degree span

All accelerate toward speed2.0.

### Sneak

The same charge resource is reinterpreted as repeated full-circle layers over multiple first speeds.

The semantic switch is:

forward stacked precision -> omnidirectional layered defense/offense

## 6. Yuyuko Fan — forward butterflies vs full circles

Charge controls shotNum from32 up to72, aligned to a multiple of3.

### Normal

Two mirrored forward butterfly fans:

- opposite rotation signs
- forward 90-degree spread
- accelerating bullets

### Sneak

Three speed tiers are emitted as paired circles with opposite rotation signs.

The same ammunition budget becomes a fundamentally different topology.

## 7. Hakurouken — brake vs reflector

### Normal, grounded and moving

Release applies a counter-impulse of about1.5 against current horizontal movement.

### Sneak

Release spawns EntityHakurouReflecter.

The reflector converts hostile non-laser THShots into normalized player-owned AQUA countershots.

### False charge affordance

The release function computes:

size = (72000 - usedTime) / 3, capped8

but size is never used afterward.

Holding longer therefore does not enlarge the reflector or strengthen the brake in the supplied X1 source.

## 8. Death Scythe — pull vs push

The same roughly16-block view-ray target selection is used in both modes.

- normal: subtract 0.6 x look vector -> attraction
- sneak: add 0.6 x look vector -> repulsion

This is a clean action-verb switch with identical targeting.

## 9. Kinkakuji — trajectory power switch

- normal upward launch power: 0.7
- sneak upward launch power: 1.0

Because impact damage later depends on falling vertical motion, Shift changes the physical trajectory and can indirectly change impact conditions.

## 10. Laevateinn — orientation switch

Both branches create the same FIRE LaserB combat profile:

- width0.6
- length20.8
- damage7
- lifetime30

The difference is the orientation frame.

Sneak computes a different move/rotation basis and explicitly sets AngleZ=90 degrees.

The result is an orientation/stance variant, not a damage variant.

## 11. Kappa Water Pistol — context override

When sneaking, the item first ray-tests for source water.

If a source-water block is found:

- restore2 durability
- swing
- return immediately
- do not fire

If no valid water source is found, execution falls through to the normal three-shot water barrage.

This is not a fixed alternate mode.

It is:

Shift + valid context -> utility action
Shift + invalid context -> normal attack

## 12. Sukima — local placement vs long warp pair

### Normal

Uses nearby/looked block-surface placement for a standard portal.

### Sneak

Casts a ray up to about128 blocks.

- rejects targets within about5 blocks
- clamps to first block hit
- can select the nearest intersected living entity
- creates one portal near the player and one at the distant target/hit
- includes a 15% item-loss roll

Shift changes the portal from local placement into long-distance paired transport.

## 13. Sakuya Watch — Shift changes persistent mode

Shift does not simply fire a different watch effect.

On initial right click, sneak toggles item damage 0/1 and returns.

Stored mode then changes the later use contract:

### Mode 0

- max use duration20 ticks
- creative effect: TIME_HALF
- survival full-charge effect: TIME_HALF_WITH_LIMIT

### Mode 1

- max use duration48 ticks
- creative effect: TIME_STOP
- survival full-charge effect: TIME_STOP_WITH_LIMIT

This is a persistent mode toggle whose result survives beyond the Shift press itself.

## 14. Yuuka Parasol — attack vs deploy, then repeated mode cycling

Normal use prepares the charged flower barrage.

Sneak use also creates EntityYuukaParasol, consuming the item stack if spawned.

The deployed entity starts at mode0.

Repeated sneak after more than10 ticks cycles:

mode0 -> mode1 -> mode2 -> finish/return

Mode0 includes easyFalling when ridden: negative motionY is multiplied by0.7.

Modes also alter the parasol's position/orientation presentation.

Shift is therefore both an initial deploy command and a repeated state-machine command.

## 15. Miko Sword — output-channel variant

Charge selects scan radius up to50 and the nearest ten living targets are still marked by DivineSpirits in both modes.

Sneak changes only information output:

- normal: spawn spirits + print direction/range text
- sneak: spawn spirits, suppress chat report

This is useful because not every action variant needs to change damage or geometry.

## 16. Marisa Broom — attachment variant

Right use always spawns the broom.

- normal, if not already riding: automatically mount
- sneak: spawn without automatic mount

The modifier changes immediate control ownership/attachment.

## 17. Charge scalar family

### Roukanken

heldTicks capped20, then x0.3 -> dash power up to6.0.

Requires the player to be on the ground at release.

### Tengu Fan

speed = heldTicks / 7, max duration24 -> about3.43 maximum speed.

### Miko Sword

scan radius = heldTicks, capped50.

### Yuyuko Fan / Hourai Branch

heldTicks increase shot density from a base32 toward cap72.

### Yuuka Parasol

shotPower2 = (10 + heldTicks) / 10.

If shotPower2 exceeds4.0, source sets it directly to5.0, producing a discontinuous jump once that threshold is crossed.

## 18. Embodied charge — Hakurei Onmyoudama

The item itself does not need to own a numeric charge meter.

It spawns EntityOnmyoudama immediately.

While the player remains in item-use state:

- the orb follows current aim/position
- size grows by0.06 per tick
- cap size =3.0
- damage continuously equals size x6

When item use ends:

- speed becomes about0.5
- the same entity transitions into its fired state

Charge is physically represented by the world projectile itself.

## 19. Embodied charge — Nuclear Control Rod

The rod creates EntityNuclearShot immediately.

While held:

- projectile follows player aim
- size grows by0.06/tick
- cap size =6.0
- damage = size x8

On normal release:

- shot becomes free
- acceleration becomes0.2
- recoil = min(heldTicks,100)/25
- max recoil magnitude =4

If the player switches the selected item away from Nuclear Control Rod while still charging, the held projectile explodes at its current position with size-dependent explosion radius.

This gives charge a real interruption risk.

## 20. Sanae Oharaibou — threshold ladder

Release before30 ticks:

- create EntitySanaeWind normal attack

At30+ ticks:

- no wind attack
- ritual/card charging branch

Threshold ladder:

| Hold | Level | Card charged |
|---:|---:|---|
| 30+ | 20+ | Miracle Fruit |
| 60+ | 25+ | Fafurotskies |
| 90+ | 30+ | Youryoku Spoiler |
| 120+ | 35+ | Moses Miracle |
| 150+ | 40+ | Yasaka no Kamikaze |

Longer hold changes the action category entirely rather than scaling one projectile.

## 21. Aja Red Stone — environment-weighted charge

EntityAjaRedStoneEffect follows in front of the player while use is held.

Each tick:

- read block-light value at current effect position
- add it to accumulated lightLevel

When use ends:

damage = floor(lightLevel / 40), capped30

Then:

- laser width = damage x0.01
- laser length = damage x0.3
- laser damage = damage

The result depends on:

- hold duration
- local brightness
- player movement/aim path through the environment

This is richer than a pure timer.

## 22. Ground / motion / airborne gates

Examples:

- Roukanken dash only executes on ground.
- Hakurouken brake requires ground + nonzero horizontal motion.
- WIND01 doubles damage when the victim is airborne.
- Yuuka Parasol mode0 only modifies descent when motionY is negative.

Physical state is part of combat input.

## 23. Weapon condition and inventory context

### Dragon Neck Jewel

Durability state decides whether the five-jewel Shift finisher is even legal.

### ItemTHLaser

The immediately adjacent hotbar slot can override laser color with dye metadata.

### Sakuya Watch

Persistent mode is encoded in item damage.

These are examples of item/inventory state being part of the action resolver.

## 24. Context fallthrough must be documented

Kappa Water Pistol shows an important source behavior:

Shift tries refill first, but if refill preconditions fail, it falls through and fires normally.

A modern input resolver should make this priority explicit instead of relying on control-flow fallthrough.

## 25. False affordances / dead input paths

### Hakurouken

Charge-derived size is unused.

### Bloodthirsty Onmyoudama

The item enters a long use state, but release behavior does not read usedTime. Hold duration does not strengthen the live teleport effect.

### Onmyoudama armor

An isSneaking branch exists, but its intended motionY effect is commented out. Horizontal motion amplification is unconditional.

### Houtou

Historical focus/attack code exists only as commented/dead code and is not active X1 behavior.

Input syntax alone is not proof of a meaningful action variant.
