# Youkai's Homecoming — All Enemy Spell Card Pattern Atlas — 2026-10-05

## Scope

This is an exhaustive source-backed pass over the enemy Spell Card registrations in
`TouhouSpellCards` plus the Touhou Little Maid fairy registrations.

Pinned source:

- `Minecraft-LightLand/Youkai-Homecoming@6d5744269aa597370a265d5c20eeb69902629441`
- mod version: 2.7.0
- Minecraft: 1.20.1
- Forge source: 47.1.3

The registry surface is:

- **15 named Touhou character cards**
- **18 fairy registration IDs**
- **33 total registration IDs**
- **17 unique trajectory/pattern implementations**

The 18 fairy IDs reuse only two algorithms:

- `fairy:0..15` -> `SmallFairySpell`, color varies
- `fairy:16..17` -> `MediumFairySpell`, paired colors vary

Player-item spells and the editable custom-spell system are not counted as enemy Spell Cards here.
They are shared pattern infrastructure and were covered in the main danmaku architecture report.

Evidence labels:

- **DIRECT_OBSERVATION** — visible in pinned source.
- **INFERENCE** — pattern/readability/dodge interpretation.
- **UNKNOWN** — not established.

---

# 1. Pattern vocabulary

All cards can be described with six largely independent axes.

## 1.1 Topology

- ring
- fan
- cone
- curtain
- spiral
- moving orbit
- corridor
- border
- surround
- projectile tree
- delayed mine/marker

## 1.2 Emitter

- boss body
- fixed world point
- target-relative point
- moving mathematical point
- child `ShooterEntity`
- previous projectile endpoint

## 1.3 Time

- periodic volley
- finite sweep
- delayed start
- stop-and-go
- prepare/active/end laser
- expiry transform
- phase selection

## 1.4 Motion

- constant velocity
- constant acceleration
- deceleration to stop
- re-acceleration
- polar/orbital motion
- attached-to-owner motion
- staged retarget

## 1.5 Targeting

- forward snapshot
- live target position
- live target velocity
- predicted future position
- target-relative arena/border
- no target dependence after launch

## 1.6 Transformation

- projectile expires -> new projectile
- projectile expires -> laser
- stationary marker -> later aimed projectile
- child shooter -> repeated projectile stream

This is a more useful description than "red bullets" / "blue lasers" because the same visual bullet
type appears in radically different gameplay roles.

---

# 2. Registration map

| Registration ID / group | Pattern class | Main archetype |
|---|---|---|
| `touhou_little_maid:hakurei_reimu` | ReimuSpell | staged retarget rings / interception field |
| `touhou_little_maid:yukari_yakumo` | YukariSpell | teleport surround / orbit-transform / laser corridor |
| `touhou_little_maid:cirno` | CirnoSpell | decelerate-stop-split |
| `touhou_little_maid:kochiya_sanae` | SanaeSpell | rotating laser pair / explosive grains |
| `touhou_little_maid:komeiji_koishi` | KoishiSpell | parametric laser field / stop-retarget / arena border |
| `touhou_little_maid:kirisame_marisa` | MarisaSpell | adaptive Master Spark / Earth Light / Black Hole |
| `touhou_little_maid:mystia_lorelei` | MystiaSpell | stop-go sweeping curtain |
| `touhou_little_maid:sunny_milk` | SunnySpell | full radial rings |
| `touhou_little_maid:luna_child` | LunaSpell | striped radial lattice |
| `touhou_little_maid:star_sapphire` | StarSpell | moving comet emitter / transverse wake |
| `touhou_little_maid:doremy_sweet` | DoremiSpell | rotating laser maze / moving madness emitters |
| `touhou_little_maid:kisin_sagume` | KisinSpell | child-shooter swarms / delayed markers / laser wing |
| `touhou_little_maid:remilia_scarlet` | RemiliaSpell | rotating 3-speed curtain / laser trees / spear |
| `touhou_little_maid:eternity_larva` | LarvaSpell | mirrored nonlinear wings / straight bursts |
| `touhou_little_maid:clownpiece` | ClownSpell | rotating arc bullets -> laser transformation |
| `fairy:0..15` | SmallFairySpell | layered fan |
| `fairy:16..17` | MediumFairySpell | rotating sweep + layered fan |

---

# 3. Small Fairy — layered fan

Source:
`compat/touhoulittlemaid/spell/SmallFairySpell.java`

## Schedule

Every 20 ticks:

```text
step = tick / 20
fire when step % 5 < 3
```

So the macrocycle is:

```text
fire
fire
fire
rest
rest
repeat
```

## Geometry

Strength:
`n = smallFairyStrength`

Default config:
`n = 2`

Horizontal branches:

```text
i = -n .. +n
angle = i * 15 degrees
```

Speed layers:

```text
j = 0 .. n
speed = 0.5 + 0.2*j - 0.1*n
```

Bullets per active volley:

`(2n + 1) * (n + 1)`

Default n=2:

- 5 directions
- 3 speed layers
- **15 bullets per volley**

## Trajectory

Pure straight-line motion after launch.

## Design role — INFERENCE

Basic aimed fan with multiple speed shells.

The same angular lane arrives at multiple times, so the player cannot treat one gap crossing as
finished immediately.

---

# 4. Medium Fairy — rotating sweep + fan

Source:
`compat/touhoulittlemaid/spell/MediumFairySpell.java`

Uses the same configurable `smallFairyStrength`.

## Macrocycle

Every 10 ticks:

```text
step = tick / 10
round = (step / 2) % 7
```

The pattern alternates between:

- rotating single-stream sweeps
- layered fan bursts
- idle phases

## Round sweep

When:

- `step` even
- `round == 0 || round == 3`

create a `Round` Ticker.

```text
duration = 5 * (n + 2)
angular speed = +/- 180 / duration degrees per tick
speed = 0.3 + 0.1*n
```

One bullet is emitted per Ticker tick.

Default n=2:

- duration ≈20 ticks
- rotation ≈9°/tick
- speed 0.5

This draws a moving radial spoke rather than one instantaneous ring.

## Secondary fan

During rounds 1 and 4:

same basic fan topology as Small Fairy, but:

```text
speed = 0.5 + 0.3*j - 0.1*n
type = CIRCLE
color = secondary color
```

## Design role — INFERENCE

A stronger fairy alternates:

- continuous sweep pressure
- discrete aimed fan pressure

instead of simply increasing bullet count.

---

# 5. Sunny Milk — complete radial rings

Source:
`content/spell/game/SunnySpell.java#L16`

Every 10 ticks:

```text
color/speed index = (tick / 10) % 3
n = 40
angle_i = i * 360/40 + randomOffset
```

Speed/color sequence:

- yellow: 0.5
- orange: 0.7
- red: 0.9

All 40 bullets share one speed per volley.

## Geometry

A full 40-ray radial ring in the local orientation basis around `holder.forward()`.

## Density

- 40 bullets every 10 ticks
- source emission rate during continuous operation: **80 bullets/sec**

## Design role — INFERENCE

Readable classic ring pattern.

Difficulty comes from overlapping rings with different radial speeds rather than directional
targeting.

---

# 6. Luna Child — striped radial lattice

Source:
`content/spell/game/LunaSpell.java#L14`

Every 10 ticks, but only for four of each six slots.

The code enumerates 120 angular slots at 3° spacing:

```text
angle = (i + offset) * 3 degrees
```

Then suppresses alternating groups of four:

```text
if (i / 4) % 2 == 0:
    skip
```

Therefore:

- 120 possible slots
- 30 groups of four
- half suppressed
- **60 bullets per active volley**

Speed:
`0.8`

Lifetime:
40 ticks.

## Shape

Not a solid ring.

It is a ring with alternating filled and empty angular bands.

## Design role — INFERENCE

This creates deliberate macroscopic gaps.

Unlike Sunny's almost uniform radial pressure, Luna's player task is to identify and align with a
rotating/offset safe band.

---

# 7. Star Sapphire — shooting star + transverse wake

Source:
`content/spell/game/StarSpell.java`

Every 10 ticks for four of every six slots:

1. choose a direction near forward:
   - horizontal Gaussian sigma ≈20°
   - vertical Gaussian sigma ≈5°
2. create one `ShootingStar` Ticker.

## Main comet

At local tick 0:

- one red MENTOS
- speed 0.8
- lifetime 60

## Wake

From local tick >=2:

- compute a point moving along the original star axis:
  `p = origin + dir * (0.8*tick - 0.4)`
- emit **2 blue SPARK bullets per tick**
- emission directions lie around the transverse orientation of the star axis
- random 360° lateral angle
- small Gaussian vertical deviation
- speed 0.4
- lifetime 80

## Shape

```text
main red star ---->
       * * transverse blue wake
        * *
         * *
```

The emitter itself moves, so the pattern is a **trail field**, not a fixed-origin fan.

## Design role — INFERENCE

Introduces moving-source reasoning to the player.

Safe space changes because new bullets are written along a moving path through the arena.

---

# 8. Cirno — decelerate, stop, split toward target

Source:
`content/spell/game/CirnoSpell.java`

Every 10 ticks.

Special case:
if the current Mob target is a Frog, fire one simple light-blue forward CIRCLE and stop.

Normal pattern:

## Stage 1 — three outward ice bullets

Three MENTOS are arranged 120° apart.

Parameters:

- radius target `r0 = 12`
- time `t0 = 20`
- `acc = 2*r0 / t0^2 = 0.06`
- initial speed `acc*t0 = 1.2`
- acceleration = -0.06 along travel direction

Therefore each bullet analytically decelerates to rest around 12 blocks from origin.

## Stage 2 — expiry split

At expiry, each endpoint executes `IcePopsicle`.

For each of the 3 endpoints:

- re-aim at the **current** target position
- create 4 BALL bullets
- angular spacing: 20°
- speed: 1
- lifetime: 40..59 ticks

Total terminal bullets:
3 * 4 = **12**.

## Shape

```text
        stop point
         | /
boss ---- * ----> four target-facing shards
```

## Design role — INFERENCE

A delayed two-stage attack.

The initial bullet path is mostly setup. The actual danger is generated at remote stopping points,
forcing the player to remember where the first-stage bullets are going to transform.

---

# 9. Mystia — delayed stop/go sweeping curtain

Source:
`content/spell/game/MystiaSpell.java`

Every 40 ticks:

- create `SweepLarge`
- alternate sweep direction +1 / -1

## Sweep dimensions

- 15 angular steps
- step every 2 ticks
- 3 vertical layers
- 10 phase-offset bullets per vertical layer

Approximate bullets per Sweep:

`15 * 3 * 10 = 450`

## Sweep angle

```text
index = sign * (tick/2 - 7.25)
horizontal angle = index * 10 degrees
vertical angle = layer * 10 degrees
```

This moves a three-layer wall across the aim direction.

## Per-bullet motion

For phase index `j=0..9`:

1. `ZeroMover`: wait `j+1` ticks
2. `RectMover`: speed 1.6, decelerate to zero
3. `ZeroMover`: pause
4. `RectMover`: accelerate from rest in the same direction
5. append a static/coasting end phase

The precise deceleration duration decreases slightly with `j`.

## Design role — INFERENCE

This is not merely a moving wall.

Because bullets inside the same apparent curtain carry different internal delays, the wall
**breathes/staggers in time**.

The player must read future motion, not only current positions.

---

# 10. Eternity Larva — mirrored nonlinear wings

Source:
`content/spell/game/LarvaSpell.java`

Uses a 100-tick macrocycle based on:

`step = (tick / 10) % 10`

## Wing phase — steps 0..2

Each trigger creates two mirrored `Wings` Tickers.

Each Wing lasts about 20 ticks.

Direction angle:

`angle(t) = (1 - sqrt(t / duration)) * 180 * sign`

Consequences:

- begins around 180°
- rotates toward 0°
- angular movement is very rapid early and slows later

Each Wing tick emits:

- 6 BALL bullets
- common direction for that tick
- speed layers: 0.3, 0.4, 0.5, 0.6, 0.7, 0.8
- small random vertical jitter
- lifetime inversely scaled by speed

Two mirrored Wings produce a visual two-wing sweep.

### Target-state variation

Vertical orientation changes based on target state:

- grounded target -> nearly flat wing
- strongly rising target -> can use very large vertical spread
- otherwise randomized ±45°

## Straight phase — steps 5..8

Every active 10-tick slot emits:

- 5 lime BUBBLE bullets
- tightly around forward, approximately ±3°
- speed layers 0.65..1.05

## Design role — INFERENCE

Alternates a highly recognizable curved wing signature with simple forward pressure.

This improves pattern readability: the visually complex wing has a recovery/transition vocabulary
instead of running continuously.

---

# 11. Sanae — rotating laser stars / explosive grain rain

Source:
`content/spell/game/SanaeSpell.java`

Sanae selects between two pattern families based on:

- range
- how long the target has remained airborne

Despite the field name `groundTime`, source increments it while the target is **not** on ground.

## Near mode

Condition roughly:

- target within 35
- airborne counter <40

### Direct shot

Every 10 ticks:

- one red CIRCLE
- forward
- speed 0.6
- life 80

### Twin rotating laser emitters

Every 40 ticks:

- construct two emitter points
- radius 8 from the holder
- mirrored ±45°
- emitter Y aligned to target Y

Each Ticker lasts ~40 ticks and emits one PENCIL laser per tick.

Direction:

`9 degrees * localTick + phase`

The two sources begin 180° apart.

Laser has a short preparation/growth period and then physically moves using `setDelayedMover`.

**Shape:** rotating dual-spoke laser star.

## Far / airborne mode — ExplosiveGrains

Every 20 ticks create one `ExplosiveGrains`.

Within its first 10 ticks, on even ticks:

- five sub-bursts

Each sub-burst creates five emitter positions arranged on a radius-12 five-point ring.

From each emitter:

- 5 red CIRCLE projectiles at a 72° pattern
- each carries `ExplodeTrail(count=3)`
- plus one direct red CIRCLE aimed at target

Per sub-burst:

- 25 explosive bullets
- 5 direct bullets
- 30 initial projectiles

Five sub-bursts:
- 150 initial projectiles total

When the 125 explosive bullets expire:
- each becomes 3 randomly directed colored BALLs
- approximately **375 terminal fragments**

## Design role — INFERENCE

Near mode controls angular movement with rotating lasers.

Far mode fills volume through delayed fragmentation, preventing the player from solving the attack
only by outranging the boss.

---

# 12. Doremy Sweet — Maze / Madness

Source:
`content/spell/game/DoremiSpell.java`

Doremy selects pattern mode using target grounded/airborne history and internal cooldowns.

## Maze

Starts when the target has remained grounded long enough.

### Immediate laser cage

At target-relative center:

- two height layers: Y ±2
- 8 ring positions per layer
- radius 6
- 12 lasers from each position

Total initial laser count:

`2 * 8 * 12 = 192 lasers`

Laser direction includes random phase and each emitter index alternates rotation sign:

- +3°/tick
- -3°/tick

These are long-lived red rotating beams.

### Rotating bullet source

For roughly the first 80 ticks:

- source point circles target at radius 8
- angular speed: 9°/tick
- every tick emits 10 BALL bullets

The bullets:

1. move slowly for 40 ticks at speed 0.05
2. accelerate strongly for 20 ticks
3. continue/end via `addEnd`

Approximate source emission:
~800 bullets over the Maze's active rotating-emitter period.

### Vertical chase markers

Every 4 ticks, when target vertical separation is >2:

- place a very short-lived red bullet near target
- direction points toward the Maze center
- speed 0.1

## Madness

Creates 7 moving emitters around the **live target**.

For each emitter:

- radial distance: 16
- azimuth changes linearly with a random speed
- elevation oscillates sinusoidally
- parameters are randomized once per Madness instance

Every tick, every emitter fires 2 BALL bullets.

Those two directions rotate around the emitter's local axis.

Colors alternate blue/magenta.

Emission rate:
**14 bullets/tick** for about 100 ticks.

## Design role — INFERENCE

Maze = geometric area denial around a relatively grounded player.

Madness = moving target-centered pressure when fixed-ground geometry is less useful.

This is an unusually clear example of choosing topology from player mobility state.

---

# 13. Kisin Sagume — child shooter swarm

Source:
`content/spell/game/KisinSpell.java`

The card chooses among three attack families by distance.

## Near — SummonNear

Condition:
distance <10.

For ~40 ticks:

- every 2 ticks create a child `ShooterEntity`
- direction = target-facing plus random ±30° horizontal/vertical
- shooter speed = 0.5
- shooter life = 60

Each child carries `SubSpell`.

Every child tick while active:

- fire one CIRCLE forward at speed 0.8
- fire one CIRCLE backward at speed -0.3

Colors alternate yellow/orange by source creation phase.

**Shape:** a growing cloud of moving line emitters leaving two-direction streams.

## Far — SummonFar

Default/far case.

For roughly 40 ticks:

- create a ShooterEntity every tick
- source point:
  - target X/Z + Gaussian noise sigma≈20
  - target Y +20
- shooter falls straight down at speed 0.5
- life 40

Every shooter tick adds a `Delayed` Ticker to the root card at the shooter's current position.

Each Delayed marker:

1. at local tick 0:
   - spawn a stationary CIRCLE
2. at local tick ==40:
   - spawn a new CIRCLE from the same point
   - aim at the **current** target position
   - speed 1

**Shape:** falling emitter rain writes a 3D minefield, then all recorded positions become delayed
aimed fire points.

## Mid — Wing

Condition:
distance <40 and random branch.

One Ticker runs ~40 ticks.

Moving emitter point:

`p = start + sideDir * 0.7*t + Gaussian jitter`

Every tick:

- calculate current target direction from p
- random angular bias ±10°
- create 3 lasers at approximately -30°, 0°, +30°
- laser length 80

Approximate emission:
~3 lasers/tick.

## Design role — INFERENCE

Kisin demonstrates why child emitters are powerful.

The boss does not need to own thousands of per-pattern counters: geometry is delegated into
temporary actors that write future danger into world space.

---

# 14. Remilia Scarlet — rotating layered sweep / laser tree / spear

Source:
`content/spell/game/RemiliaSpell.java`

Runs a five-step macrocycle, one step every 20 ticks.

## Steps 0..2 — Sweep

Target distance controls base speed:

`v = max(1, distance / 20)`

Each Sweep lasts about 20 ticks.

Main rotation:

`baseAngle = 180 + 360/duration * localTick`

Random angular noise:

- horizontal ±15°
- vertical Gaussian
- vertical spread increases with target speed

Count:

`count = int(15 * v)`

For each sampled direction, emit **three projectiles**:

1. red BUBBLE: random speed in ~[0.8v, 1.2v]
2. red MENTOS: ~0.6..0.9 multiplier of the first speed
3. red BALL: ~0.3..0.6 multiplier

Lifetimes are scaled so shells cover roughly the configured range.

Source emission rate:
`3 * count` bullets per Sweep tick.

At longer range `v` and therefore `count` increase.

**Shape:** rotating curtain with three nested arrival-time shells.

## Step 3 — Lasers

Only when target speed >1.

Each local tick:

- choose 4 random 3D directions
- root laser length random 25..39
- at each root endpoint spawn 3 additional lasers
- children spread 120° around the endpoint axis with ~45° tilt
- child length 80

Per local tick:
- 4 root lasers
- 12 child lasers
- **16 lasers**

### Source anomaly

Inside the child loop, source calls `l0.setupTime(...)` again rather than `l1.setupTime(...)`.

DIRECT_OBSERVATION:
child lasers therefore retain their default timing while the root laser timing is repeatedly
modified.

Whether this is intended is **UNKNOWN**.

## Step 4 — Spear

Only if distance >=40.

Before spawning, Remilia moves/teleports roughly halfway toward target, respecting block clipping.

Then:

`n = max(100, distance * 5)`

For each sample i:

- `p = i/n`
- source position interpolates from boss toward 1.2x past target
- radial noise envelope is proportional to:
  `p * (1-p)`
- noise is largest near the middle, smallest at ends
- bullet direction = original target direction
- speed = 3
- type = red MENTOS
- life = 30

This is not a volley traveling from one origin.

It is a **pre-populated spatial lance**.

## Design role — INFERENCE

Remilia switches between:

- time-layered rotational pressure
- volumetric branching beams
- a direct spatial impalement line

The card attacks movement planning in very different ways within one repeating macrocycle.

---

# 15. Marisa — adaptive three-family spell selection

Source:
`content/spell/game/MarisaSpell.java`

Every 100 ticks, choose one family from:

- MasterSpark
- EarthLight
- BlackHole

Choice depends on:

- target distance
- target horizontal speed
- randomness

## BlackHole

Runs ~100 ticks.

Emission center:
- holder center
- raised 24 blocks
- if target is higher, center rises to target height first

There are:

- 5 color families
- 3 source offsets per family
- 5 direction spokes per source

Per tick:
`5 * 3 * 5 = 75 SPARK bullets`

### Moving source

Source point angle:
`7*tick + 72*i + 24*t`

Source radius:
`0.2*tick`

So emitters spiral outward over time.

### Bullet heading

Direction angle:
`-4*tick + 72*j + 24*t`

So source field and shot direction counter-rotate.

Speed varies by source layer and sinusoidally.

Every bullet receives world acceleration:

`(0, -0.05, 0)`

**Shape:** expanding counter-rotating overhead rain.

Static source emission:
**75 bullets/tick** during the Ticker.

## EarthLight

Runs ~100 ticks.

Every tick, create 2 lasers.

Source:

- around target X/Z with Gaussian sigma≈10
- height adjusted using MOTION_BLOCKING_NO_LEAVES
- if terrain is much lower, source may shift downward up to 20 blocks

Direction:

`normalize(gaussianX, 5, gaussianZ)`

So beams point mostly upward with random tilt.

- length 80
- life 60
- red or blue randomly

**Shape:** terrain-aware light pillars appearing around target.

## MasterSpark

At local tick 0:

- spawn one yellow length-80 laser
- attached to holder position
- prepare time 20

After tick >20:

- internal aim direction slowly lerps toward current target
- maximum directional adjustment step ≈0.02 per tick

Every tick afterward:

### White stars

- 20 bullets
- spawn at positions spaced along the current aim line
- direction within roughly ±15° horizontally/vertically
- speed 2..3

### Yellow sparks

- 10 bullets
- spawn at holder center
- direction within roughly ±60°
- speed 0.6..0.9

Total:
**30 bullets/tick** during the active secondary emission.

## Design role — INFERENCE

Marisa's card is an attack-family selector rather than one repeating geometry.

It reacts to player mobility/range and chooses:

- overhead area denial
- beam-aligned burst pressure
- terrain-localized pillars

---

# 16. Koishi — parametric laser field + delayed homing + hard border

Source:
`content/spell/game/KoishiSpell.java`

This card is active every tick.

## Parametric lasers

Every tick:
**10 lasers**

For each laser use a phase:

`t = 0.024 * cardTick + i * 17`

Position around holder:

```text
x = 32 * cos(1.47t) * cos(t)
z = 32 * cos(1.47t) * sin(t)
y = min(holderY - 15, targetY - 10)
```

Direction:

`normalize(cos(4t), 3, cos(4t))`

Thus the spawn locus and beam orientation have unrelated frequencies.

Laser:

- length 60
- prepare 10
- setup 4
- active 20
- end 4

**Shape:** a constantly rewritten parametric laser sculpture below/around the battle.

## Stop-and-retarget MENTOS

Every 4 ticks start a `StateChange`.

Stage 1:

- choose a horizontally rotating front vector from card tick
- launch one MENTOS
- analytically decelerate over 20 ticks
- stop about 4 blocks from origin

Stage 2 at tick 20:

- re-read current target
- fire a new red MENTOS from the stop point
- speed 1
- life 40..59

## 24-way rings

Every 10 ticks:

- 24 red BALL bullets
- random ring angular offset
- speed = max(0.6, distance/40)
- life 40

## Predictive border

When target distance >26:

- estimate `future = target + targetVelocity * 4`
- project an outward line from holder toward future position
- place 4 pink CIRCLE bullets at randomized distances along that line
- each receives slow transverse/downward motion

## Hard arena boundary

If the actual target becomes farther than 32:

- directly move target back to 32-block radius
- set target velocity inward
- mark player movement update when needed

This is not a projectile pattern; it is a combat-space rule.

## Design role — INFERENCE

Koishi combines:

- visual parametric hazard
- delayed direct threat
- conventional ring pressure
- explicit arena confinement

This is one of the strongest examples of **battlefield design being part of the Spell Card**, not
merely bullet spawning.

---

# 17. Yukari — teleport surround / butterfly orbit transform / laser corridor

Source:
`content/spell/game/YukariSpell.java`

Yukari chooses behavior by range and target speed.

## Long-distance teleport logic

When distance >40, every 5 ticks:

If target speed:

- <0.5
- or >1

Yukari attempts to teleport to a point 32 blocks beyond the target along the current boss->target
axis.

If target speed is in the middle band:

Yukari attempts a point 16 blocks on the near side.

Successful relocation triggers `hidden(...)`.

## Hidden surround sequence

`hidden` executes one burst immediately, then schedules six more burst sites around the target.

- six delayed sites
- each delayed by 10 ticks more than the previous
- sites lie around target at approximately the original boss-target radius

Thus the target is progressively attacked from a surrounding ring.

### Each hiddenImpl burst

At one site:

#### Lasers
- 6 magenta lasers
- 60° apart
- length 80
- prepare 2 / grow 8 / active 100 / end 10

#### Bubbles
- 6 purple BUBBLE bullets
- same six principal directions
- speed 2

#### Butterfly volume fan
- horizontal index -3..3 -> 7 lanes
- vertical index -2..2 -> 5 lanes
- three speed layers: 1.4, 1.6, 1.8

Total butterfly bullets:
`7 * 5 * 3 = 105`

Total projectiles/lasers per burst site:
`6 + 6 + 105 = 117`

One immediate + six delayed sites:
up to **819 spawned danger objects** across the surround sequence.

## Close range — Butterfly program

When distance <20:

launch two mirrored sets:

- cyan, direction sign +1
- magenta, direction sign -1

Each set has:
**100 bullets**

Initial directions cover a full ring around forward with random vertical deviation up to about
±45°.

Each bullet receives a five-stage `CompositeMover`.

### Phase A — outward deceleration

Duration 40.

Target radius randomly:
4..20 blocks.

Initial radial speed chosen so constant deceleration brings the bullet to rest at that radius.

### Phase B — rotate in place

Duration 10.

`ZeroMover` changes orientation without translation.

### Phase C — angular acceleration orbit

Duration 10.

`PolarMover`:
- constant radius
- angular acceleration

### Phase D — constant orbit

Duration 30.

Carry forward the resulting angular velocity but clear acceleration.

### Phase E — tangent escape

Duration 40.

Convert the final orbit state to a straight `RectMover`.

**Shape:**

```text
explode outward
 -> stop
 -> turn
 -> begin orbit
 -> orbit
 -> leave tangentially
```

Two mirrored sets yield **200 bullets**.

This is one of the clearest demonstrations of the mover DSL.

## Default / mid distance — LaserAdder

Runs about 120 ticks.

Every tick:

- spawn one red laser from a point moving outward along -45° line
- spawn one blue laser from a point moving outward along +45° line

Source distance:
`1 + 0.5*tick`

Each laser points perpendicular to that travel line, with randomized rotation around the line.

Approximate:
**2 lasers/tick**

At local tick 20:
- add red group

At local tick 40:
- add blue group

Each group:

- 5 BUBBLE bullets
- 50 MENTOS bullets
- directions form a noisy forward cone
- speed gradually decreases by index
- life 60..79

## Design role — INFERENCE

Yukari's identity comes from **changing the origin topology**, not simply changing bullet heading.

The player's current relative position is repeatedly invalidated by teleporting or surrounding
emitters.

---

# 18. Reimu — staged retarget rings / velocity interception / reactive border

Source:
`content/spell/game/ReimuSpell.java`

Reimu works on a 10-tick scheduler.

`step = (tick/10) % 5`

For steps 0..2:
normal staged ring.

For long-distance targets, steps 3/4 can run `intercept`.

If Reimu is in abyssal state and the target has stayed airborne, additional sequence behavior can
run.

Taking damage can permanently enable `border` until reset.

## Normal StateChange

Every normal trigger builds one `StateChange`.

Distance changes the parameters.

For target distance 16..40+, interpolate:

- radius from ~6 to 20
- first/second phase duration from 20 down to 10
- terminal speed from 1 up to 3

Default branch count:
**20**

### Phase 1 — radial outward stop

For each branch:

```text
acc = 2*r0 / t0^2
initialSpeed = acc*t0
acceleration = -acc
```

So each projectile analytically stops at radius `r0`.

Color:
light gray.

### Phase 2 — expiry retarget

At expiry:

- read **current target position**
- spawn a purple projectile aimed at target
- start speed = `acc*t1`
- decelerate to 0 over t1

### Phase 3 — expiry retarget again

At second expiry:

- read current target again
- spawn final colored projectile
- constant terminal speed
- randomized lifetime

Thus one conceptual branch re-aims twice.

This is not continuous homing.

It is **discrete homing at transformation events**.

## Long-range Intercept

When distance >40, Reimu uses target velocity.

It first teleports relative to the target's movement vector:

```text
distanceAhead = max(24, targetSpeed*20)
destination = target + normalizedVelocity * distanceAhead
```

If speed >=0.5, start `Intercept`.

### Intercept field

Duration:
~80 ticks.

Maintain a smoothed target center:

`center = 0.95*old + 0.05*currentTarget`

Build 8 emitter points in a radius-32 ring around the movement axis.

Each emitter produces 8 bullets every tick.

Per tick:
`8 * 8 = 64 yellow BUBBLE bullets`

Bullet velocity:

- rotating tangential component, speed 2
- plus inward component (-off)

Angular rotation:
about 18°/tick.

**Shape:** a moving toroidal/cylindrical interception field around the target trajectory.

Static emission rate:
**64 bullets/tick**.

## Reactive border

After Reimu is hurt by an entity, `border=true`.

Then every card tick:

- emit 8 yellow BALL bullets
- radial ring around current forward orientation
- speed = clamp(distance/30, 1.5, 3)
- life 40

This becomes persistent background pressure.

## Hurt-triggered sequences

Damage can also create additional delayed `StateChange` families.

Non-abyss:
- one multi-step oriented BUBBLE sequence

Abyss:
- three oriented sequence families
- additional blue/abyssal behavior

## Important source anomaly

`TargetTracker.vel()` currently returns:

`t2.subtract(t2).scale(0.1)`

which is always zero.

The main `shoot()` path contains a branch requiring `vel.length() > 0.2`.

Therefore:

- zero velocity result: **DIRECT_OBSERVATION**
- intended result likely target-delta velocity: **INFERENCE**
- runtime symptom: **NOT_REPRODUCED**

The separate `intercept()` uses `holder.targetVelocity()`, so that long-range path is not
disabled by this particular helper.

---

# 19. Clownpiece — rotating arc -> expiry laser conversion

Source:
`content/spell/game/ClownSpell.java`

Base macro duration:
60 ticks.

If Clownpiece is Lunatic:
30 ticks.

Pattern alternates red/blue major modes.

## Major Laser Tickers

Despite the class name `Laser`, these Tickers first emit MENTOS bullets.

### Mode 0

At major phase start:

- choose rotation sign
- build three vertical offsets
- create mirrored ± families
- six Tickers total
- additional families are delayed by -10 / -20 ticks

### Mode 1

- use a random vertical range ±60°
- create one mirrored pair

### Arc formula

For local Ticker progress:

```text
angle = (45 + (tick/dur)*180) * sign
forwardAngle = (-45 + (tick/dur)*90) * sign
vertical = (-15 + (tick/dur)*30) * sign
```

Every active tick:

- emit one MENTOS at speed 0.5
- lifetime increases with local tick

## Expiry transform — blue mode

Blue MENTOS expiry:

- create one blue length-60 laser
- fixed direction derived from the source arc
- prepare 10 / grow 10 / active 60 / end 10
- create one stationary blue MENTOS marker

## Expiry transform — red mode

Red MENTOS expiry:

- re-read **current target**
- laser points from expiry point toward target
- create one stationary red MENTOS marker

So blue is geometrically predetermined; red retargets on expiry.

## Concurrent Spread curtain

Every 10 ticks during the active portion of the macrocycle:

start a `Spread` job.

Each Spread tick:

- 3 sub-time offsets
- 5 vertical lanes (-30,-15,0,+15,+30 approximately)
- total 15 bullets per tick
- horizontal angle sweeps with `w = +/-9`
- speed 0.8
- color/type follows the current red/blue mode

Duration:
10 ticks.

Approximate output:
~150 bullets per Spread job.

## Design role — INFERENCE

Clownpiece creates two time scales:

1. continuous swept projectile curtains;
2. apparently harmless/temporary arc bullets that later become large laser hazards.

The player has to remember where old bullets are going to transform.

---

# 20. Cross-card density map

These are **source emission rates/counts**, not runtime-performance measurements.

| Pattern | Static source density observation |
|---|---:|
| Marisa BlackHole | 75 bullets/tick |
| Reimu Intercept | 64 bullets/tick |
| Doremi Madness | 14 bullets/tick |
| Koishi parametric field | 10 lasers/tick + auxiliary bullets |
| Yukari LaserAdder | ~2 lasers/tick for ~120 ticks |
| Sunny | 40 bullets / 10 ticks |
| Luna | 60 bullets / active 10-tick volley |
| Mystia Sweep | ~450 bullets per sweep |
| Sanae ExplosiveGrains | ~150 initial + ~375 expiry fragments/event |
| Yukari Hidden | 117 danger objects/site, up to 7 sites |
| Remilia Spear | >=100 bullets spawned spatially at once |
| Remilia Sweep | 3*count bullets/tick; count increases with range |
| Clown Spread | 15 bullets/tick for ~10 ticks per job |

The total live-object count can be much larger than the creation rate because projectile lifetimes
overlap.

---

# 21. Avoidance-pressure classification

This section is **INFERENCE**, based on geometry/time structure.

## Route-reading pressure

Cards where stable gaps are the main problem:

- Small Fairy
- Medium Fairy
- Sunny
- Luna

Player task:
identify angular lanes and move to a safe route.

## Timing / memory pressure

Cards where old bullets change behavior later:

- Cirno
- Mystia
- Reimu
- Clownpiece
- Kisin Far

Player task:
remember future state, not only current position.

## Field-tracking pressure

Moving emitters rewrite danger continuously:

- Star
- Doremi Madness
- Marisa BlackHole
- Koishi
- Yukari LaserAdder
- Kisin shooter swarms

Player task:
track the source field itself.

## Area-denial pressure

Persistent/large geometry restricts legal movement:

- Doremi Maze
- Koishi parametric lasers
- Marisa EarthLight
- Yukari hidden surround
- Kisin Wing
- Remilia laser tree

## Interception pressure

Patterns that use target state to punish predictable escape:

- Reimu Intercept
- Koishi future-position border
- Marisa attack-family selection
- Sanae near/far-air selection
- Yukari teleport placement
- Remilia speed/range branch

## Arena-control pressure

Directly limits battle geography:

- Koishi hard 32-block boundary
- Yukari teleports/re-surrounds
- Remilia closes distance before spear

---

# 22. Trajectory families worth extracting

## 22.1 Decelerate-to-radius

Used by:
- Cirno
- Reimu
- Koishi staged bullet
- Yukari butterfly phase A

Contract:

```text
given desired travel radius R and duration T:
a = 2R/T^2
v0 = aT
accel = -a
```

The projectile reaches approximately R while ending at zero speed.

This is extremely reusable for readable bullet staging.

## 22.2 Expiry retarget

Used by:
- Cirno
- Reimu
- Clownpiece
- Sanae fragmentation

Contract:

```text
projectile lifetime ends
 -> sample live target / stored direction
 -> spawn next stage at exact endpoint
```

Cheaper and more visually legible than continuous homing.

## 22.3 Moving emitter

Used by:
- Star
- Doremi
- Kisin
- Marisa
- Koishi
- Yukari

The bullet formula itself can remain simple because complexity comes from changing the source
position.

## 22.4 Polar/orbital transition

Strongest example:
Yukari Butterfly.

The useful abstraction is:

```text
rectilinear approach
 -> stop/rotate
 -> angular acceleration
 -> stable orbit
 -> tangent conversion
```

## 22.5 Delayed marker

Strongest example:
Kisin Far.

```text
record world point now
display stationary marker
wait T
sample live target
fire from old point
```

Excellent for memory-based bullet hell.

## 22.6 Parametric world-space hazard

Strongest examples:
- Koishi laser locus
- Marisa BlackHole emitters
- Doremi Madness emitters

The emitter itself is a mathematical function of time.

No pathfinding or steering is necessary.

---

# 23. Pattern readability lessons

INFERENCE.

The strongest cards rarely increase difficulty only by increasing count.

They combine readable dimensions:

- color identifies family/state
- laser growth provides telegraph
- ZeroMover creates visible waiting
- slow bullets mark future danger
- transformation occurs at predictable lifetime
- repeated macrocycle teaches the pattern
- randomness perturbs a known structure rather than replacing it completely

This is a valuable design principle:

> **Use deterministic topology for learnability, then add bounded randomness for replay variation.**

Examples:

- Sunny: deterministic ring + random phase
- Remilia Sweep: deterministic rotation + bounded random spread
- Doremi Madness: fixed seven-emitter structure + randomized emitter parameters
- Star: fixed moving-wake grammar + randomized initial heading
- Sanae grains: fixed five-point emitter geometry + random terminal fragments

---

# 24. Pattern construction layers

A reusable KNEEKURA spell architecture can preserve these as separate layers.

## PatternTopology

```text
RING
FAN
CONE
CURTAIN
SPIRAL
ORBIT
CORRIDOR
SURROUND
BORDER
TREE
MARKER_FIELD
```

## EmitterMotion

```text
STATIC
ATTACHED
LINEAR
POLAR
PARAMETRIC
CHILD_ENTITY
TARGET_RELATIVE
```

## ProjectileMotion

```text
CONSTANT
ACCELERATED
DECELERATE_TO_STOP
STOP_GO
ORBIT
STAGED_RETARGET
```

## TemporalProgram

```text
PERIODIC
BURST
SWEEP
DELAY
TRANSFORM_ON_EXPIRY
PHASE_SELECT
```

## TargetPolicy

```text
SNAPSHOT_AIM
LIVE_RETARGET
VELOCITY_PREDICT
DISTANCE_SELECT
AIR_GROUND_SELECT
ARENA_BOUNDARY
```

This preserves the individuality of each card while allowing new patterns to be assembled from
shared concepts.

---

# 25. Source anomalies / boundaries

## Reimu TargetTracker

`TargetTracker.vel()` returns zero due to `t2.subtract(t2)`.

See main danmaku failure-history report.

## Remilia laser child timing

In `RemiliaSpell.Lasers`, the child-laser loop calls:

`l0.setupTime(...)`

rather than calling it on `l1`.

DIRECT_OBSERVATION:
root timing is changed; child timing remains default.

Intent:
**UNKNOWN**.

## No difficulty measurement

This atlas describes source geometry.

It does not claim:

- which card is hardest
- player success rate
- actual FPS/MSPT
- exact maximum simultaneous projectile count in real combat
- multiplayer subjective fairness

Those require runtime instrumentation.

---

# 26. Suggested LAB instrumentation for danmaku study

For future runtime research, the most useful per-card telemetry would be:

```text
live projectile count
spawn count/tick
erase count/tick
laser count
virtual vs Level-managed count
collision candidate count
narrowphase sample count
client render instance count/type
packet bytes/tick
frame time
server MSPT contribution
minimum player-to-projectile distance
graze events/tick
hit events
safe-space estimate
```

Trajectory capture should distinguish:

- emitter trajectory
- projectile trajectory
- target trajectory
- transformation point
- telegraph-active-damage windows

This would integrate directly with the existing TECH-HUB trajectory-observation direction.

---

# 27. Bottom line

The 17 unique enemy Spell Card algorithms are not variations of one radial generator.

They cover at least these distinct design families:

1. layered fan
2. rotating radial sweep
3. full ring
4. striped ring
5. moving comet emitter
6. stop-and-split
7. delayed stop/go curtain
8. nonlinear mirrored wings
9. rotating laser sources
10. fragmentation field
11. target-centered moving emitter maze
12. child-shooter swarm
13. layered rotational speed curtain
14. spatial spear
15. adaptive attack-family selection
16. parametric laser field + arena border
17. teleport surround + orbit-transform
18. discrete multi-stage homing
19. arc-to-laser transformation

The core reusable lesson is:

> **Good bullet-hell variety comes from changing topology, emitter motion, timing and retarget rules —
> not from creating more projectile classes.**
