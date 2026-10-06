# QB-MOD 1.6.4.082 — Mechanic timing / cadence / probability analysis

Date: 2026-10-07

Primary evidence:
- QB-MOD archive SHA-256 `52b1ba0774e098795dcf1ed9a489c66414ea725235978171f48a10db7287ba4e`
- Garnet-MOD archive SHA-256 `5f778c8949dcce95dcd56dacd9242f117bc17f03879bab48cb667ba2a3c82778`

All real-time conversions below use the vanilla nominal **20 ticks/second**. Runtime lag can make wall-clock time longer.

The shared short/middle/long goals decrement `actionTick` once per update before calling the character attack method, so a returned value of N is a nominal N-tick wait before that attack method can fire again while its Goal remains active.

---

## 1. Magical-girl form clocks

Source: `EntityMahoShojo.onLivingUpdate`.

### ordinary transformed form

When no target:
- `transformTime++`.

When target exists:
- Rebellion trigger is checked first;
- otherwise, if timer >0, `transformTime--`.

When `transformTime > 500`:
- reset timer;
- return to Normal.

Pure uninterrupted idle therefore ends after the counter crosses 500: nominally **501 ticks ≈25.05 s**.

This is not a simple timeout:
- idle accumulates debt;
- combat pays that debt down one tick at a time.

Technique:
**reversible idle budget**.

### Rebellion

No target:
- `transformTime++`.

Target present:
- timer does not decrement.

Exit:
- after Free mode is established and `transformTime >1000`;
- reset and return Normal.

Pure no-target lifetime: **1001 ticks ≈50.05 s**.

This is a **cumulative idle budget**, not a continuous “time since last target” timer.

### Ultimate Form

No target:
- timer increments.

Separately the branch order enforces:
1. fire immunity;
2. Follow mode;
3. cleanse Soul Gem by 1/tick until zero;
4. only then test `transformTime >1500`.

Pure no-target threshold: **1501 ticks ≈75.05 s**, but actual finish is also gated on fire/mode/corruption normalization.

If a target exists, the idle timer does not increase, but Soul Gem cleansing can still proceed once the earlier state gates are satisfied.

---

## 2. Core character burst cadence

### Madoka

#### short
One action:
- 5 arrows immediately;
- return 20.

Nominal: **5-projectile salvo every ~1.0 s** while conditions remain stable.

#### middle
`rapidFire < 7`:
- one projectile;
- return 3.

Final call:
- one projectile;
- reset;
- Soul Gem +1;
- return 10.

Result:
- **8 arrows**;
- nominal shot times: 0,3,6,9,12,15,18,21 ticks;
- burst span ≈**1.05 s**;
- then ≈0.5 s recovery.

#### long
Each call emits 4 Light Arrows.

`rapidFire2 <4` then final call:
- 5 volleys total;
- spacing 3 ticks;
- final recovery 15.

Result:
- **20 arrows**;
- nominal volley times 0,3,6,9,12;
- burst span ≈**0.60 s**;
- recovery ≈0.75 s.

### Madoka Ultimate

Dedicated AI:
- every 5 ticks fires 3 autonomous/search arrows;
- with a valid target, adds one targeted LightArrow3.

Rates:
- no target: 3 / 5 ticks = **12 arrows/s**;
- target present: 4 / 5 ticks = **16 arrows/s**.

This is before counting projectile lifetime/homing overlap, so simultaneous entity count can be much higher.

---

## 3. Homura burst cadence

### short handgun
- 8 shots total;
- 5-tick spacing;
- times 0..35 ticks;
- span ≈**1.75 s**;
- 20-tick recovery.

### middle Type 89
- `rapidFire2 <30` plus final shot = **31 shots**;
- 2-tick spacing;
- span 60 ticks = **3.0 s**;
- 20-tick recovery.

Nominal sustained burst rate during the firing window:
**10.33 shots/s**.

### Walpurgis-specific TNT/firework sequence
- `rapidFire3 <15` plus final attack = **16 iterations**;
- 1-tick spacing;
- span 15 ticks = **0.75 s**;
- then 100-tick = **5 s** recovery.

Each iteration:
- fuse-1 TNT;
- one firework tracer/cue.

This is a very high entity/event-density special case.

### Homura Rebellion
- one volley = 8 LightArrow2;
- action cooldown = 15 ticks.

Nominal average:
- **8 arrows / 0.75 s ≈10.67 arrows/s** when line of sight remains available.

---

## 4. Kyouko / Kirika / Yuri burst cadence

### Kyouko long-range spear
Each attack call spawns 4 Spears.

`rapidFire <5` plus final call:
- **6 volleys**;
- **24 Spears** total;
- 5-tick volley spacing;
- span 25 ticks = **1.25 s**;
- final 12-tick recovery.

### Kirika long-range claw
Each call spawns 3 Claws.

`rapidFire <5` plus final call:
- **6 volleys**;
- **18 Claws** total;
- 12-tick spacing;
- span 60 ticks = **3.0 s**;
- final 20-tick recovery.

The target can also receive Slowness II for 100 ticks = **5 s** if not already slowed.

### Yuri bullet burst
Middle/fallback-long:
- `rapidFire2 <12` plus final = **13 shots**;
- 6-tick spacing;
- span 72 ticks = **3.6 s**;
- final 20-tick recovery.

Long terrain attack, when it succeeds:
- immediately enters an 80-tick = **4 s** recovery instead of the gun sequence.

Summoning takes precedence and returns 20 ticks = **1 s** before ordinary attack selection resumes.

---

## 5. Mami staged-stock cadence

Mami has no long rapid-fire counter like Madoka/Homura.

Visible stock:
- middle deploy: **4 Muskets**;
- long deploy: **12 Muskets**.

A successful later stock consumption:
- removes one nearby Musket;
- fires one bullet;
- typically returns 3 ticks = **0.15 s** before next opportunity.

Long finisher:
- target HP <10 and maxHP >30;
- critical `Tiro Finale!`;
- 30 ticks = **1.5 s** recovery.

Normal low-HP direct Tiro:
- 5 ticks = **0.25 s**.

Thus much of Mami's rate limiting is encoded in:
**how many visible Muskets were staged**, not only a hidden burst counter.

---

## 6. Oktavia Wheel wave

Source: `EntityMajoAIOktavia`.

At range:
- one successful Wheel spawn increments `spawnTick`;
- first four successful Wheels schedule next try after 5 ticks;
- fifth successful Wheel sets recovery to 60 ticks and resets count.

Result:
- **5 Wheels** per complete wave;
- nominal successful launch times 0,5,10,15,20 ticks;
- wave span ≈**1.0 s**;
- then 60 ticks = **3 s** recovery.

Important:
- each Wheel creation can try up to **20 candidate spawn positions**;
- failed spawn attempts do not advance the wave counter.

Close melee:
- 20-tick = **1 s** cooldown.

---

## 7. Kriemhild absorption cycle

Source: `EntityKriemhildAIAbsorb`.

`timer++` every scheduler check; task executes when `timer %40 ==0`.

Nominal pulse sequence:
- tick 40 = drain/attack + heal;
- tick 80 = drain/attack + heal;
- tick 120 = drain/attack + heal;
- tick 160 = lightning presentation branch;
- timer resets to 0.

Therefore:
- ordinary absorb pulse period = **40 ticks =2 s**;
- macro-cycle = **160 ticks =8 s**;
- three drain/heal pulses then one lightning pulse.

Each pulse scans an AABB expanded:
- 64 X;
- 32 Y;
- 64 Z;
and processes until `targetCount >100`.

This timing is central to its static performance risk.

---

## 8. Walpurgis normal “Play” cadence — important modulo behavior

Source: `EntityMajoAIWalpurgisnachtPlay`.

Constructor initializes:
`attackTick = 500`.

`startExecuting()` does **not** reset it.

Each update:
1. pre-increment `attackTick`;
2. if >100:
   - set `attackTick=0`;
   - fire **5 Flame Lances**;
3. test `attackTick % attackTime1 ==0`;
4. test `attackTick % attackTime2 ==0`.

Because the counter was just set to zero:
- `0 % anyPositiveInteger == 0`.

Therefore the reset update also guarantees:
- +1 additional Flame Lance;
- +1 Prickle (source uses `nextInt(1)+1`, always 1).

### Immediate task-entry burst

Because constructor starts at 500, the **first Play update** increments to501 and immediately hits the reset path.

So task entry produces at least:
- **6 Flame Lances**
- **1 Prickle**
on that update.

### Recurring macro burst

After reset, the next reset occurs when the incremented counter exceeds100:
- after 101 updates;
- ≈**5.05 s** nominally.

Thus Play has a strong macro rhythm:
**every ~5.05 s, 5-Lance burst + guaranteed modulo-triggered Lance + Prickle**.

### Random “attackTime” variables are divisors, not countdowns

Initial:
- attackTime1 = 15..29;
- attackTime2 = 50..99.

When a modulo event fires, a new divisor is sampled.

This does **not** mean “wait 15–29 ticks”.
It means:
`current attackTick % sampledDivisor == 0`.

The next event depends on the current counter phase relative to the new divisor.

This is a significant implementation detail for any faithful reconstruction.

---

## 9. Walpurgis low-health Attack cadence

Source: `EntityMajoAIWalpurgisnachtAttack`.

Constructor also starts:
`attackTick = 500`.

First update:
- increments to501;
- immediately attempts `attackDestroy()`.

If terrain-to-TNT conversion succeeds:
- counter becomes0;
- same update then also satisfies both modulo tests;
- launches **1–3 Flame Lances** and **1–3 Prickles**.

If destruction fails:
- target receives a large random velocity impulse;
- counter is set to400;
- next terrain attempt becomes possible after it crosses500 again.

Post-trigger divisors:
- Flame Lance divisor sampled 10..29;
- Prickle divisor sampled 50..99.

Again, these are modulo divisors rather than countdown intervals.

### Phase-entry consequence

Entering the low-HP goal can cause an **immediate high-impact terrain attack + projectile wave**, rather than a delayed wind-up.

For ANCHOR readability, consider an explicit phase-transition/charge telegraph before reproducing the damage timing.

---

## 10. Walpurgis anti-air timing

Both Play/Attack variants use the same broad clock:

While target is:
- not on ground;
- not in water;

`floatTime++`.

At `floatTime >=100`:
- set `cannotFloat=true`;
- reset timer.

Nominal pre-punishment grace:
**100 ticks =5 s** airborne.

During punishment:
- target motionY is reduced by 10 each update;
- landing causes strength-3 explosion and reset;
- if still airborne for another100 punishment ticks, strength-6 explosion fires and the legacy self-poison anomaly executes.

Thus the theoretical second-stage ceiling is another **5 s**, though the forced vertical acceleration should usually ground the target much earlier.

---

## 11. Grief Seed incubation distribution

Formula:
`countdown = 500 + nextInt(1000) - damage*5`.

The countdown only progresses while a player is within 16 blocks.

Possible initial countdowns:

| Grief Seed damage | min ticks | max ticks | mean ticks | nominal mean |
| ---: | ---: | ---: | ---: | ---: |
| 0 | 500 | 1499 | 999.5 | 49.975 s |
| 16 | 420 | 1419 | 919.5 | 45.975 s |
| 32 | 340 | 1339 | 839.5 | 41.975 s |
| 48 | 260 | 1259 | 759.5 | 37.975 s |
| 63 | 185 | 1184 | 684.5 | 34.225 s |

At maximum damage, the random range remains very wide:
**9.25–59.2 s** of active nearby-player countdown.

Corruption therefore shifts the distribution earlier but does not make hatch time deterministic.

---

## 12. Grief Seed VFX thresholds as timing zones

While a nearby player exists:
- <1000: red-dust pulse every 5 ticks;
- <500: additional red-dust every tick;
- <100: another randomized-velocity red-dust every tick.

At nominal 20 TPS:
- first warning layer: up to 4 pulses/s;
- second layer adds 20/s;
- final layer adds another 20/s with agitation.

Since the starting countdown may already be below1000 for sufficiently high corruption/random roll, some seeds can enter a stronger visual warning zone immediately.

---

## 13. Witch/familiar maturation clock

Common:
- age +1 each living update;
- each kill adds **+100 age**, equivalent to about **5 nominal seconds** of natural age.

Pure no-kill maturation thresholds use `age > threshold`, so replacement begins on the first tick past the threshold.

Approximate baselines:

| Chain | threshold | no-kill time |
| --- | ---: | ---: |
| Lilia → Luiselotte | 1500 | ~75.05 s |
| Lotte → Luiselotte | 1500 | ~75.05 s |
| Anthony → Adelbert | 1800 | ~90.05 s |
| Court Lady → guide | 1800 | ~90.05 s |
| Maid → Candeloro | 2000 | ~100.05 s |
| Luiselotte → Clara | 2000 | ~100.05 s |
| Adelbert → Gertrud | 2400 | ~120.05 s |
| Pyotr → Charlotte | 3000 | ~150.05 s |
| guide Court Lady → Ophelia | 3000 | ~150.05 s |
| Liese → Clara | 3000 | ~150.05 s |

Each kill subtracts about5 seconds from the remaining natural-age requirement by adding100 age immediately.

---

## 14. Natural-spawn random gates

These are **per `getCanSpawnHere` evaluation**, not per-tick world probabilities.

### QB
First local gate:
`nextInt(20) ==0`.

Probability:
**1/20 =5%** before Y/block/collision and registry-spawn conditions.

### Grief Seed
Default config:
`GSSpawning=20`.

Code passes first random gate when:
`nextInt(100) <=19`.

Probability:
**20%** before light/collision/liquid/difficulty constraints.

### Walpurgis calendar gate
Requires:
- world day index modulo8 ==0;
- time >12000 and <23200.

The time window spans roughly 11,199 integer tick values depending endpoint interpretation, about **9m20s** of nominal world time on each eligible eighth day.

This is an **admission window**, not a spawn probability: normal entity spawning and height checks must still succeed.

---

## 15. QB exchange probability geometry

Damaged QB exchange samples uniformly from:
`0..damage`.

At damage63 there are64 equiprobable outcomes.

Final distribution at damage63:

| Reward band | outcomes | probability |
| --- | ---: | ---: |
| Tea | 7 | 10.9375% |
| Leather | 8 | 12.5% |
| Golden Apple | 8 | 12.5% |
| Iron | 8 | 12.5% |
| Bone Meal | 8 | 12.5% |
| Wood | 8 | 12.5% |
| Enchanted Golden Apple | 8 | 12.5% |
| Gunpowder | 8 | 12.5% |
| Diamond | 1 | **1.5625%** |

Important boundary examples:
- damage7: Leather becomes reachable at 1/8 =12.5%;
- damage15: Golden Apple first appears at 1/16 =6.25%;
- damage47: Enchanted Apple first appears at 1/48 ≈2.083%;
- damage55: Gunpowder first appears at 1/56 ≈1.786%;
- damage63: Diamond appears at 1/64.

Unlocking a new tier initially gives it only one reachable roll; its probability expands as damage increases.

---

## 16. JB inverse probability geometry

JB samples:
`nextInt(64-damage)`.

At pristine damage0:
64 equiprobable outcomes 0..63:

| Reward | probability |
| --- | ---: |
| Tea | 1.5625% |
| Glowstone | 9.375% |
| Lapis | 12.5% |
| Redstone | 12.5% |
| Iron | 12.5% |
| Gold | 25% |
| Emerald | 12.5% |
| Quartz | 12.5% |
| Diamond | **1.5625%** |

At damage1:
- domain becomes0..62;
- Diamond is already impossible.

At damage63:
- `nextInt(1)` =0;
- Tea = **100%**.

So QB and JB use opposite domain geometry:
- QB damage expands the possible roll ceiling;
- JB damage contracts it.

---

## 17. Performance/readability implications of cadence

High-density static cases for LAB:

1. **Madoka UF**: 12–16 homing arrows/s before lifetime overlap.
2. **Homura Rebellion**: ~10.67 homing arrows/s.
3. **Homura Type89 NPC burst**: 31 bullets across3 s.
4. **Kyouko long**: 24 spear entities in1.25 s.
5. **Walpurgis Play macro reset**: at least7 projectiles/events on same update (6 Flame +1 Prickle) plus normal modulo shots.
6. **Walpurgis low-health entry**: terrain conversion plus up to6 projectiles on same update when conversion succeeds.
7. **Oktavia**: five kinetic Mob entities in1 s, each with up to20 position probes.
8. **Kriemhild**: large-area entity scan every2 s.
9. **Grief Seed final warning**: multiple particle emissions every tick.
10. **Nutcracker ecology**: short summon interval + large local population cap.

These should be tested with trajectory/entity-count telemetry, not only FPS screenshots.

---

## 18. Reconstruction rule

Do not interpret every legacy tick number as sacred.

For ANCHOR record separately:
- **semantic cadence**: burst, pause, escalation, periodic wave;
- **legacy exact tick values**;
- **modern tuned value**;
- **reason for any change**;
- **observed player readability**;
- **server cost at target concurrency**.

Faithfulness means preserving the combat rhythm and visible contract unless exact-tick parity is itself a requirement.
