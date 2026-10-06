# Warfare Wings — Explainable Aircraft Performance Model

## Purpose

Yes: aircraft-to-aircraft performance differences can be explained.

The important restriction is that an explanation must separate:

- **raw data differences**;
- **host-physics mechanisms**;
- **measured runtime behavior**;
- **engineering inference**.

A value appearing in aircraft JSON is not automatically an active performance control.

## 1. Explanation pipeline

For every base aircraft:

```text
Warfare Wings aircraft data
        ↓
effective host/runtime stats
        ↓
Immersive Aircraft state equations
        ↓
Minecraft movement / contact / projectile boundaries
        ↓
measured flight envelope
        ↓
aircraft performance explanation
```

Each performance card should contain:

```text
identity / role / doctrine
raw aircraft properties
effective physics properties
measured:
  top speed
  acceleration
  yaw response / turn time
  pitch response
  sustained-turn speed loss
  climb / descent
  glide
  stall / recovery
  braking / approach
combat:
  firing geometry
  projectile time of flight
  weapon count / mounts
survivability:
  durability
  damage state
explanation:
  source-backed causes
  uncertain / dead / unproven fields
```

## 2. Which fields actually explain what?

For the pinned Immersive Aircraft 1.3.3 source association:

| Input | Main effect | Explanation status |
|---|---|---|
| `engineSpeed` | forward thrust scale at engine power | SOURCE_DIRECT |
| `yawSpeed` | direct yaw change per tick from smoothed X | SOURCE_DIRECT |
| `pitchSpeed` | direct airborne pitch change per tick from smoothed Z | SOURCE_DIRECT |
| `lift` | bends velocity direction toward aircraft nose | SOURCE_DIRECT |
| `glideFactor` | converts descent into forward-direction velocity | SOURCE_DIRECT |
| `friction` | velocity decay; default 0.015 if absent | SOURCE_DIRECT |
| `horizontalDecay` | horizontal velocity decay | SOURCE_DIRECT |
| `verticalDecay` | vertical velocity decay | SOURCE_DIRECT |
| `stabilizer` | pulls pitch toward level | SOURCE_DIRECT |
| `acceleration` | changes engine response smoothing | SOURCE_DIRECT |
| `groundPitch` | ground attitude convergence | SOURCE_DIRECT |
| `pushSpeed` | low-power ground push/takeoff behavior | SOURCE_DIRECT |
| `durability` | scales incoming vehicle damage | SOURCE_DIRECT |
| `fuel` | fuel consumption multiplier | SOURCE_DIRECT |
| `wind` | wind perturbation amplitude | SOURCE_DIRECT |
| `mass` | changes wind-noise time scale in inspected 1.3.3 source | SOURCE_DIRECT but narrow |
| `rollFactor` | visual/control roll derived from lateral input | SOURCE_DIRECT; not primary turn force |
| `driftDrag` | present in JSON, not registered by inspected 1.3.3 VehicleStat loader | NOT_ACTIVE_IN_INSPECTED_SOURCE |

### Important interpretation traps

**Mass is not ordinary aircraft inertia in this host model.**
Do not explain a slow turn by saying "the aircraft is heavy" unless the runtime path actually makes
mass affect that result. In the inspected source, direct yaw response comes from `yawSpeed`, not
mass.

**Roll factor is not bank-to-turn authority.**
The host directly changes yaw. A larger visual bank does not by itself mean a tighter physical turn.

**Lift is not conventional aerodynamic lift.**
It is mainly velocity-vector alignment toward the nose.

These distinctions make the performance explanations more useful than merely repeating the JSON.

## 3. Concrete examples

All 24 base-aircraft raw values are now re-extracted directly from the supplied Warfare Wings ANCHOR
(SHA-256 `dc3029597c88859744633b6f5e4a9f21d449294b1aaac90ea0c1749d7aa98a43`) into the derived
`base-aircraft-anchor-v1` dataset. Runtime measurements still remain the final authority for
absolute performance.

### A6M Zero — turn-fighter bias

Selected values:

```text
engineSpeed  0.075
yawSpeed     3.8
pitchSpeed   3.5
lift         0.135
glideFactor  0.065
rollFactor   60
durability   2.5
mass         5.4
```

Interpretation:

- relatively high `yawSpeed` and `pitchSpeed` provide fast nose-direction changes;
- lower `engineSpeed` than the major US energy fighters limits thrust/top-speed potential;
- low durability makes prolonged exchanges less attractive;
- its "turn fighter" identity is therefore explainable primarily through control authority and the
  measured turn envelope, not through low mass.

Expected tactical consequence:

> stay engaged, convert nose authority into repeated firing opportunities, avoid long straight-line
> energy contests.

### P-47N Thunderbolt — high-energy / low-nose-authority bias

```text
engineSpeed  0.102
yawSpeed     2.5
pitchSpeed   2.4
lift         0.165
glideFactor  0.055
rollFactor   58
durability   5.0
mass         9.0
```

Relative to A6M:

- thrust scale is much higher;
- direct yaw and pitch authority are substantially lower;
- durability is twice the A6M value.

This naturally supports:

> build speed/separation, make an attack pass, extend, and re-enter rather than trying to remain in a
> close sustained nose-to-nose turning contest.

The explanation does **not** need to claim that mass=9 directly creates inertia; the inspected host
source does not use mass that way.

### P-51D Mustang — energy fighter with more control authority

```text
engineSpeed  0.100
yawSpeed     3.0
pitchSpeed   3.0
lift         0.150
glideFactor  0.060
rollFactor   80
durability   4.0
mass         6.5
```

Compared with P-47N:

- almost the same high thrust scale;
- higher yaw/pitch authority;
- lower durability;
- much higher visual roll factor.

So even if both are classified as energy fighters, they should not use identical tuning.

A plausible runtime policy distinction is:

- P-47N: larger separation / more conservative re-entry;
- P-51D: tolerate tighter pursuit and earlier nose commitment.

That policy distinction should be confirmed by measured energy-loss and firing-solution telemetry,
not only these raw values.

### Spitfire — fast-turning balanced fighter

```text
engineSpeed  0.095
yawSpeed     3.6
pitchSpeed   3.4
lift         0.148
glideFactor  0.064
durability   3.0
```

It combines near-energy-fighter thrust with control values close to the A6M.

That explains why a single `turn_fighter` template should still allow aircraft-specific tuning:
Spitfire can plausibly retain more speed while preserving strong nose authority.

### B-17 — heavy bomber behavior is explicit

```text
engineSpeed  0.045
yawSpeed     1.2
pitchSpeed   1.1
lift         0.280
glideFactor  0.080
rollFactor   15
durability   6.0
mass         18
```

The bomber's slow maneuver response does not need to be guessed from mass:

- `yawSpeed=1.2`;
- `pitchSpeed=1.1`;
- `engineSpeed=0.045`.

Those are already explicit.

Its very high `lift` should be interpreted in host-model terms: strong velocity alignment, not
large physical wing lift.

Tactical consequence:

> long-horizon guidance, gentle corrections, formation stability and pre-planned attack geometry are
> more appropriate than fighter-style reactive maneuvering.

### Ju 87 — deliberately slow attack-aircraft envelope

```text
engineSpeed  0.050
yawSpeed     1.8
pitchSpeed   1.8
lift         0.200
glideFactor  0.070
durability   4.5
```

Low thrust and low control rates make it unsuitable for generic fighter logic.

The useful explanation is mission-specific:

> attack geometry should be established before the dive; the AI should value safe pull-out timing
> over late high-rate corrections.

### IL-2 — an important counterexample

```text
engineSpeed  0.070
yawSpeed     4.0
pitchSpeed   3.5
lift         0.240
glideFactor  0.085
durability   5.0
mass         10.5
```

Despite being a heavy ground attacker by theme, it has **very high direct yaw/pitch settings**.

This demonstrates why historical-aircraft stereotypes must not replace runtime analysis.

In this MOD's host physics, the IL-2 can have strong nose authority while still having a lower
speed/mission envelope than fast fighters.

### G4M — medium/heavy mission aircraft

```text
engineSpeed  0.065
yawSpeed     2.9
pitchSpeed   2.7
lift         0.230
glideFactor  0.085
durability   4.0
mass         12
```

Its control rates are much higher than the B-17's, so grouping every bomber into one maneuver model
would erase real runtime differences.

A torpedo-attack AI can therefore allow more active heading correction for G4M than a B-17 level
bombing policy, while still respecting its slower engine envelope.

## 4. From explanation to AI tuning

The performance card should feed doctrine parameters rather than directly hard-code named aircraft.

Example derived features:

```text
nose_authority
  <- measured yaw/pitch step response

speed_class
  <- measured stabilized speed / acceleration

energy_retention
  <- sustained turn / climb / extension traces

stall_margin
  <- measured stall and recovery traces

glide_efficiency
  <- engine-off descent traces

survivability
  <- durability + measured damage behavior

weapon_solution
  <- convergence / projectile speed / mount geometry
```

Then doctrine can use continuous values:

```text
if high nose_authority + moderate energy:
  tighter pursuit

if high speed + low nose_authority:
  larger extension and re-entry radius

if poor pull-out response:
  earlier dive-abort gate
```

This avoids creating 24 unrelated hard-coded AI personalities while preserving genuine aircraft
differences.

## 5. Required confidence output

Every generated statement should carry evidence tags.

Example:

```text
P-47N has lower raw yaw authority than A6M.
  SOURCE_DIRECT

P-47N reaches a higher measured maximum speed than A6M.
  MEASURED

The higher engineSpeed is a major contributor to that difference.
  SOURCE_DIRECT + CORRELATED

Exactly X% of the speed difference is caused by engineSpeed.
  UNKNOWN until isolated calibration
```

This prevents the explainability layer from pretending to have a causal decomposition that was
never measured.

## 6. All-aircraft Atlas implemented

The first all-aircraft layer now exists for all 24 base aircraft:

- [reports/base-aircraft-source-atlas.csv](reports/base-aircraft-source-atlas.csv) — compact source-microkernel feature table;
- [reports/aircraft-atlas-ai-view.json](reports/aircraft-atlas-ai-view.json) — machine-readable ranks, doctrine contrasts and query flags;
- [reports/AIRCRAFT-ATLAS.md](reports/AIRCRAFT-ATLAS.md) — human-readable extrema and interpretation warnings.

The Atlas deliberately avoids a composite "strongest" score. Atlas v2 ranks speed, yaw, pitch, same-input retention, equal-angle 90° turn time/retention/path distance, and durability independently.

Individual per-aircraft cards and pairwise combat recommendations can now be generated from this
shared representation as needed. Runtime mismatch warnings remain pending same-artifact calibration.

The useful end state is that a future AI can ask:

> "Why is this aircraft failing this maneuver?"

and receive a traceable answer such as:

> "The target maneuver demands faster nose closure than this aircraft's measured yaw/pitch response.
> Increasing turn aggressiveness would push it below its measured energy floor; use an extension /
> re-entry action instead."

That is the intended role of the Warfare Wings Physics AI Laboratory.


## 7. First executable performance card

The first executable/golden comparison is now:

- [reports/a6m-p47n-source-microkernel.md](reports/a6m-p47n-source-microkernel.md)
- [reports/a6m-p47n-source-microkernel.csv](reports/a6m-p47n-source-microkernel.csv)

The report is generated from the pure Java 1.3.3 source microkernel and checked for deterministic
byte-identical regeneration.

Current source-microkernel output:

| Aircraft | predicted top speed | yaw / 20t | pitch / 20t | turn-exit retention |
|---|---:|---:|---:|---:|
| A6M | 33.67 b/s | 34.24° | 31.53° | 0.977 |
| P-47N | 45.79 b/s | 22.52° | 21.62° | 0.991 |

These are **SOURCE-MICROKERNEL** results, not `MEASURED` runtime claims.

The large A6M difference from the isolated legacy measured profile is intentionally retained. It
must be resolved through same-artifact runtime trace replay, not by tuning constants until the
numbers look familiar.


## 8. Retention metric correction — implemented

The original field `turn_exit_speed_retention` remains the speed ratio after the **same 20-tick
full-yaw input**. It is now exposed in the AI view as `same_input_retention`.

Atlas v2 adds an explicit equal-angle experiment:

- `turn_90_ticks`;
- `equal_angle_90_speed_retention`;
- `distance_to_90_yaw_blocks`.

This lets the AI answer two different questions without conflating them:

> "How much speed survives the same control duration?"

and

> "How much speed survives after the same 90° heading change, and how long/far did that change take?"

For example, B-17 has excellent equal-angle retention (~0.9946) but needs 118 ticks to reach 90°,
whereas A6M reaches 90° in 42 ticks but retains ~0.9256. Neither single number is "turning quality";
the tactical policy needs both time-to-nose and energy cost.

The next evidence upgrade is to reproduce these equal-angle traces in the exact Minecraft runtime.