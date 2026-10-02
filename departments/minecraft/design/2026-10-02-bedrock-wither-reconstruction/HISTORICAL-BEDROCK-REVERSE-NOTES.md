# Historical Bedrock Reverse-Engineering Notes — Wither

Reviewed: 2026-10-02  
Status: HISTORICAL / HYPOTHESIS SUPPORT ONLY

Source:
`PeratX/source` at `ea30a251dd8fd16a7bd2e568209797a9c7be970f`

The repository labels itself "Minecraft: Bedrock Source" and contains generated/decompiled C-like output. Its exact Bedrock game version is not established here. Therefore **no numeric constant from this source is current-authoritative**.

Current BDS structure remains authoritative over this file:
[BDS-STRUCTURE-2026-10-02.md](BDS-STRUCTURE-2026-10-02.md)

## Highest-damage target — strong historical corroboration

Historical `WitherTargetHighestDamage::getHighestDamageTarget()`:

- reads a Wither-owned "player party" collection;
- resolves each entry back to a Player;
- compares the stored damage value;
- chooses the Player with the greatest value that passes target validation;
- `canContinueToUse` stops when the highest-damage Player changes.

This matches the current BDS structural signature:

```
Player* getHighestDamageTarget()
```

Engineering consequence:
KNEEKURA's priority-1 highest-damage Goal currently selects Players, while the broader threat ledger can still retain non-player attackers for diagnostics and lower-priority retaliation logic.

Do not infer current damage-window duration, reset rules or party-entry lifetime from this historical build.

## Random attack-position goal — relationship evidence

Historical `WitherRandomAttackPosGoal`:

- is derived from `RandomStrollGoal`;
- only considers use when the Wither has a target;
- refuses the path while the Wither is in its powered/second-state condition;
- consults a Wither-owned wants-to-move flag;
- marks Wither pathing on start;
- clears wants-to-move/pathing on stop;
- modifies flight speed while active;
- assigns a shot delay when the movement goal stops.

Current BDS independently still exposes:
- `WitherRandomAttackPosGoal : RandomStrollGoal`;
- goal-local `mIsPathing`;
- Wither fields `mWantsMove`, `mIsPathing`, `mFramesTillMove`, `mMovementTime`;
- shot timing fields `mDelayShot`, `mTimeTillNextShot`, `mTimeSinceLastShot`.

This makes the **movement ↔ pathing ↔ firing-delay relationship** a high-priority current-runtime measurement target.

Rejected as current constants:
- historical flight-speed multiplier;
- historical stop-shot delay;
- historical random-position range values.

## Difficulty-health historical behavior

Historical `reloadHardcoded` visibly modifies health limits by difficulty and separately records a half-health threshold.

This supports the idea that the public JSON base health=600 is subsequently difficulty-adjusted in native code. It does **not** replace current runtime measurement for exact values, even though maintained current gameplay documentation reports 300/450/600.

## Phase transition historical relationship

Historical damage handling:
- processes accepted damage;
- tracks health interval values;
- compares health against a stored threshold;
- calls `changePhase` when threshold/phase conditions are met.

Current BDS still exposes:
- `mHealthThreshold`;
- `mPhase`;
- `mHealthIntervals`;
- `mLastHealthValue`;
- `mWantsToExplode`.

This is strong structural continuity but not proof of unchanged phase math.

## Projectile creation

Historical `_performRangedAttack(head, targetPos, dangerous)` selects between two projectile definitions based on the dangerous flag. Current Mojang behavior packs independently expose separate normal and dangerous skull entity definitions.

Accepted invariant:
normal/dangerous projectile identity is an explicit boss decision.

Not accepted from historical source:
- old head offsets;
- old exact firing cadence;
- old entity numeric IDs.

## Block destruction

Historical code had a `canDestroy` predicate excluding Bedrock, portal/portal-frame, command-block family and several education/barrier-like blocks.

Current BDS has evolved the interface into:

```
canDestroy(Block const&, WitherAttackType)
_destroyBlocks(..., range, WitherAttackType)
```

with distinct:
- Charge
- HurtExplosion
- Projectile

Therefore old one-size block exclusions are **not** sufficient for current reconstruction. They are only a candidate baseline for per-attack-type runtime tests.

## Rules for use

Historical Bedrock reverse engineering may:
- explain a current field/function name;
- identify a relationship worth measuring;
- provide search terms for current symbols;
- suggest test scenarios.

It may not:
- set a current timer/speed/range;
- override current Mojang JSON;
- override current BDS generated headers;
- bypass direct Bedrock measurement where behavior remains hidden.


## Historical phase/volley body details now corroborated

The historical native body provides several relationships that now have independent current evidence.

### Native phase numbering

Historical constructor initializes `Phase=1`.

Historical `changePhase()`:
- decrements Phase;
- the half-health transition therefore changes 1 -> 0;
- disables the aerial-attack synced flag;
- raises an explode/wants-to-explode flag;
- clears wants-to-move;
- changes fire-rate related state.

Current BDS independently still exposes:
- `mPhase`
- `mHealthThreshold`
- `mWantsToExplode`
- movement/fire-rate fields.

Current gameplay documentation independently retains the same two-stage half-health transition.

KNEEKURA therefore uses native-like phase IDs:
- 1 = first/aerial phase
- 0 = second/powered phase

The high-level Java state enum remains separate from these IDs.

### Half-health threshold

Historical initialization stores `maxHealth / 2` as the phase health threshold.

Current Bedrock gameplay documentation consistently places the transition at half health.

KNEEKURA accepts half max health as the phase threshold.

### Transition skeleton count

Historical transition body spawns exactly three Wither Skeletons when difficulty is not Easy.

Current maintained Minecraft Wiki and Bedrock Wiki both report three on Normal/Hard and none on Easy.

KNEEKURA accepts:
- Easy: 0
- Normal: 3
- Hard: 3

Older/stale pages reporting four on Hard remain disagreement history and do not override the newer convergence.

### Transition explosion

Historical wants-to-explode body uses explosion power 7.0 with mob-griefing gating.

Current documentation describes a large half-health explosion; older Minecraft Wiki material describes it as equivalent to the spawn explosion, whose documented power is 7.

KNEEKURA currently records power 7.0 as **HISTORICAL_CORROBORATED**, not CURRENT_BINARY_CONFIRMED. It is isolated in `BedrockWitherPhaseController.PROVISIONAL_TRANSITION_EXPLOSION_POWER`.

### Main-head projectile cycle

Historical center-head ranged attack:
- increments a Wither-owned projectile counter;
- every fourth center-head projectile is dangerous/blue;
- first three are normal.

Current BDS still exposes:
- `mProjectileCounter`
- `mSecondVolley`
- `mMainHeadAttackCountdown`
- `mlastFiredHead`

Current Bedrock Wiki independently reports a firing cycle of three normal skulls followed by one dangerous skull.

KNEEKURA accepts the **projectile-type order** 3 normal + 1 dangerous. Exact inter-shot and inter-volley timers remain unresolved.

### Values deliberately not promoted

The historical body also contains timing/speed/range values. These are NOT current-authoritative merely because nearby structure survived.

Still unresolved:
- current `mFireRate` initialization and health update equation;
- current second-volley delay;
- current move cooldown;
- current charge preparation/duration/speed;
- current phase transition action tick ordering;
- exact current explosion power confirmation from BDS 1.26.51.1 binary body.


## Hurt-reaction and charge destruction geometry

Historical native server code calls the Wither block-destruction routine with different integer ranges:

- hurt reaction: `destroyBlocks(..., range=1)`
- active charge: `destroyBlocks(..., range=2)`

Current BDS independently changed the public native boundary into:
`_destroyBlocks(..., int range, WitherAttackType attackType)`,
with separate `HurtExplosion` and `Charge` attack types.

Using the current official Bedrock Wither collision box (width 1, height 3), the historical inclusive integer block iteration yields:

- AABB inflated by 1: 4 × 6 × 4 = 96 candidate block positions
- AABB inflated by 2: 6 × 8 × 6 = 288 candidate block positions

Current Bedrock Wiki runtime observation independently reports exactly:
- 4×6×4 for the delayed hurt break
- 6×8×6 per charge tick

This is unusually strong cross-layer reconstruction evidence because the **geometry falls out of the native range parameter and official collision box**, rather than being copied from the Wiki as an arbitrary cuboid.

KNEEKURA therefore accepts these two destruction geometries.

## Hurt-reaction timer

Historical `_hurt` only arms the destruction countdown if it is not already active and assigns 20 ticks.

Current Bedrock Wiki independently reports that the phase-1 block-break reaction occurs 20 game ticks after the attack.

KNEEKURA accepts:
- delay = 20 ticks
- repeated accepted hits do not reset an already-active timer
- second phase does not run the ordinary hurt-break reaction

The current Wiki also reports one dangerous skull fired as part of the reaction. Exact current native aim/fallback selection is not exposed. KNEEKURA temporarily stores the triggering attacker and aims at it when still valid; that targeting policy remains an explicit adaptation target.

## Charge execution body

Historical native code shows the active charge loop:
- stores a charge direction;
- uses a dedicated charge frame/timer;
- performs range-2 block destruction while charging;
- applies 15 damage to nearby entities.

Current BDS still exposes:
- `mCharging`
- `mChargeDirection`
- `mChargeFrames`
- `mPreparingCharge`

Current Bedrock Wiki independently reports approximately 20 game ticks for active charge and range-2-derived 6×8×6 destruction every tick.

KNEEKURA accepts:
- active charge duration = 20 ticks
- charge destruction = range 2 every active tick
- charge entity damage = 15

Still measurement-gated:
- preparation duration / trigger
- exact current movement speed
- collision termination nuances
- repeated-hit semantics for an entity remaining inside the charge damage volume


## Center-head firing-rate reconstruction

This section intentionally separates confidence levels.

### Current-observation layer

Current Bedrock technical observation reports:
- a firing cycle of 3 normal skulls followed by 1 dangerous skull;
- firing speed depends on damage sustained;
- pathological healing/damage manipulation can drive the rate as fast as roughly one skull per game tick;
- after a firing cycle, a roughly 7-second intermediate period occurs before another cycle begins.

These observations are current behavior evidence, not native-body proof of the exact internal equation.

### Historical native-body layer

Historical Bedrock native code independently shows:

1. the center-head projectile counter increments for each shot;
2. every fourth projectile is marked dangerous;
3. the constructor initializes the firing-rate field to 20;
4. hardcoded reload stores:
   - the current max health;
   - a half-health phase threshold;
   - a health interval equal to maxHealth / 3;
   - a last-health cursor equal to maxHealth;
5. after accepted damage, when health crosses the next stored interval, the firing-rate field is replaced with approximately half its previous integer value and the health cursor advances to that interval.

Current BDS 1.26.51.1 independently still exposes:
- `mProjectileCounter`
- `mFireRate`
- `mHealthIntervals`
- `mLastHealthValue`
- `mDelayShot`
- `mTimeSinceLastShot`
- `mSecondVolley`
- `mMainHeadAttackCountdown`

This is strong structural continuity, but current binary bodies are not available in the retained source surface.

### KNEEKURA implementation labels

- **ACCEPTED order:** 3 normal + 1 dangerous.
- **OBSERVED_CURRENT:** inter-volley cooldown = about 7 seconds / 140 game ticks.
- **HISTORICAL_NATIVE_PROVISIONAL:** base fireRate = 20 ticks.
- **HISTORICAL_NATIVE_PROVISIONAL:** health interval = maxHealth / 3.
- **HISTORICAL_NATIVE_PROVISIONAL:** crossing the next health interval halves the current fireRate, bounded to at least 1 in the Java adaptation.

The provisional timing/equation lives only in `BedrockWitherVolleyController` so direct current-Bedrock measurement can replace it without touching projectile identity, targeting, phase or movement code.

### Not yet promoted

- exact current first-shot delay after target acquisition;
- exact current handling of large damage that crosses multiple health intervals in one hit;
- whether healing resets any current native health cursor;
- current phase-2 use of the same center-head volley controller;
- exact relation between `mSecondVolley`, `mDelayShot` and the observed 7-second pause;
- current passive dangerous-skull timer (~15 seconds in technical observation).
