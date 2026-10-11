# Flight Physics Twin — exact-original IA aerodynamics and offline research

**2026-10-11 research status:** implemented and measured the **recorded
free-air flight-control physical slice** of pinned Warfare Wings 1.1.4 and
Immersive Aircraft 1.3.3. This is a major increase in SOURCE replay fidelity,
**not** a Minecraft simulation replacement or full mission/weapon parity.
All measurements and claims below distinguish **(1) actual original-Forge
observations**, **(2) source replay of already observed commands**, and
**(3) synthetic counterfactual SOURCE experiments**.

## 1. Root cause: `AircraftEntity.getWindStrength()` includes SPEED

Exact-original pinned binary evidence:

- Owner Warfare Wings SHA-256:
  `dc3029597c88859744633b6f5e4a9f21d449294b1aaac90ea0c1749d7aa98a43`
- Immersive Aircraft 1.3.3 SHA-512:
  `7b74442e161bb74538e0d8da34a81616daeea56a0da62db86113a78b3bf3c2b3a6b0e12f12454fd7c96092762f6b212ba57cb87eb1af2b242a4d5df4eca03055`
- `AircraftEntity.getWindStrength()` explicitly includes the **current
  aircraft `getDeltaMovement().length()`** even when all weather wind
  configuration multipliers are zero, and multiplies by the aircraft's
  `VehicleStat.WIND`.
- `AircraftEntity.getWindEffect()` evaluates `Utils.cosNoise` at
  `entity.tickCount / (20 * mass)` for its pitch component and
  `entity.tickCount / (21 * mass)` for its yaw component.
- Original `Utils.cosNoise(double)` sums **five cosine harmonics**,
  multiplying the argument by **1.3** before each successive harmonic.
- `AircraftEntity.updateVelocity` applies this perturbation **after**
  `applyFriction`, with float semantics. The original additionally adds
  `0.005f * effect.x` and `0.005f * effect.z` to the respective delta
  velocity axes. `AirplaneEntity.updateController()` then applies actual
  IA flight controls and engine thrust.

This deterministic aircraft-speed contribution had been omitted from the
legacy `FlatWorld(0)` physics microkernel. **Zero WEATHER wind is not zero
AIRCRAFT aero forcing.** The omitted source term accumulated yaw/pitch drift,
which accumulated flight direction and position drift. It affected all 24
aircraft, especially slower and high-inertia bombers.

`PinnedIa133WindWorld.java` reconstructs the exact pinned formula in the
pure-Java source engine. `Ia133Microkernel.World.windAfterFriction` now
provides the already friction-adjusted velocity to an opt-in world callback.
**The existing `wind` method and every original Atlas v2/v3 golden remain
compatible and unchanged.** New flights opt in through
`PinnedIa133WindWorld.calmAirCalibration()`; `SCRIPTED_WIND` adds its
experimental overlay explicitly rather than silently changing this baseline.

## 2. Original-Forge flight receipts vs independent source predictions

The pinned-original Forge 1.20.1 / 47.4.20 server had already generated the
actual unmodified measurements. Java17 only source classes read those CSVs
and calculate the original-source physical step from *the actual observed
previous state*. For the stronger OPEN-LOOP test, they integrate **from only
the initial real state using the real prerecorded exogenous control stream**.
The current real airplane's new position and velocity never enter subsequent
open-loop steps.

| Original aircraft, same initial 0.7 blocks/tick +Z | 400tick old SOURCE open-loop deviation | New pinned aerodynamic source final deviation |
|---|---:|---:|
| A6M | 2.620935 blocks | <0.0002 blocks |
| P-47N | 4.165318 blocks | <0.0002 blocks |
| Spitfire | 6.277028 blocks | <0.0002 blocks |
| IL-2 | 6.429974 blocks | <0.0002 blocks |
| B-17 | 15.052741 blocks | <0.0002 blocks |

Five same-condition free-flight traces each used **401 actual physical
samples, 400 independent microkernel integration steps**. The previous
reported Source Atlas v3 neutral RMSE values are retained as accurate
historical **legacy-model** results, not silently rewritten.

### Cross-check extended to every original airframe

`RealTacticalPhysicsTwinReplayMain.java` also replays recorded original
GameTest pilot controls, respecting the confirmed **one-tick IA input-lag**.
Unlike a new autonomous decision experiment, the next command is read from
the pre-recorded **actual GameTest** control stream to isolate the physical
engine from policy differences. Actual game time, airframe, scenario,
position, velocity and missing-tick/frozen-chunk gates are independently
checked.

35 paired original-Forge receipts, all pass the **new separate scoped
`max_final_drift_blocks=0.01` threshold**:

| Recorded evidence group | Cases | Actual paired 20Hz physics updates | Result |
|---|---:|---:|---|
| All 24 aircraft sequential original Forge smoke | 24 | 960 (24×40) | Source replay PASS; max final drift 0.0000261 blocks |
| A6M/P-47N/Spitfire/IL-2/B-17 original neutral calibration | 5 | 2,000 (5×400) | Source replay PASS; each final drift <0.0002 blocks |
| Simultaneous original 2v2, B-17 escort and IL-2/B-17 long strike prerecorded controls | 6 | 2,920 | Source replay PASS, largest final drift 0.001775711 blocks |
| **TOTAL** | **35** | **5,880** | **24 airframe types, 35 real observation sequences, all paired** |

Largest independent **one-step position RMSE** of these 35 cases:
**0.000002388437 blocks**. Largest open-loop final deviation:
**0.001775711195 blocks** (B-17 long 840tick flight), median
**0.000015825348 blocks**. Real Forge still supplies actual observations;
the offline source handles the independent integration.

The 0.01-block position gate is a new **recorded-control physical-slice**
requirement only. It is NOT a weaker/alternative definition of successful
combat, 95-block bomber protection or 6-block flight safety. The real B-17
escort acceptance **STILL FAILS**: enemy inside 95 blocks for **101/340
Minecraft ticks**, minimum ~**66.029 blocks**. The exact real original
Forge suite remains **20 GameTests = 19 PASS and 1 FAILED**.

## 3. Independent original-Forge provenance and AI-inspectable evidence

Run from `departments/minecraft/mods/warfare-wings/physics-ai` using
**Java17 + Python standard library only**, against your own existing
original-JAR GameTest receipt directory:

```powershell
$root = 'runtime-probe/run-gametest/ww-physics-traces'
python tools/run_physics_twin.py --real-traces $root `
  --output "$root/physics-twin-full" `
  --java-home 'C:\Program Files\Java\jdk-17' `
  --max-final-drift 0.01
```

This **does not start Minecraft**. It compiles the pinned source-only Java
replay engine, demands all **24+5+6** real receipts, produces 35 independently
calculated per-tick CSVs and then verifies *every position, velocity,
scenario, Entity tick, real Minecraft clock, finite value, aircraft
identity, position discrepancy and air-clearance assumption* against the
raw original receipts. Missing/modified game samples fail closed. The
independent verifier also has synthetic failure-injection tests proving
bad provenance, missing airframes, broken clocks, unrealistically low
error thresholds, and fabricated roll readings are not counted.

The local output tree contains:

```text
physics-twin-full/
  paired/                            35 per-tick original/source comparisons
  report/
    physics-twin-evidence.json        AI-readable per-scenario summary + limits
    physics-twin-evidence.csv         35-row metric table
    physics-twin-explorer.html        Offline interactive error curves
  classes/                            temporary Java17 compilation output
```

The HTML explorer works directly from a local file: select 35 physical
recordings and graph one-step/open-loop position, yaw and speed residuals.
No web API, fonts, external scripts or network access. Exact aircraft IDs,
scenario names and hard failure limits are included.

Do **not** commit original JAR bodies, GameTest CSV recordings, or the raw
local binary. The GitHub self-hosted workflow reuses its existing exact-
original-JAR hash gate, actual Forge GameTests, and then executes this new
35-receipt validator. Its unconditional terminal gate still fails honestly
when the B-17 remains unprotected, even if physical replay succeeds.

## 4. Fully offline tactical research batches

**[FLIGHT-RESEARCH-LAB.md](FLIGHT-RESEARCH-LAB.md)** documents
`FlightResearchBatchMain.java` and its independent `flight_lab_run.py`
runner, `flight_lab_report.py` renderer, and seed/rupture unit tests.

```powershell
$output = Join-Path $env:TEMP 'ww-flight-research-lab-20261011'
python tools/flight_lab_run.py --output $output `
  --seed 20261011 --trials-per-aircraft 512 --ticks 180 `
  --java-home 'C:\Program Files\Java\jdk-17'
Start-Process (Join-Path $output 'flight-lab.html')
```

Independent Windows Java17 verification achieved **12,288 deterministic
SOURCE trials (24 aircraft × 512), 11 conditions**, and **2,211,840
Source-only physical ticks**. There are **264 representative full-flight
tracks sampled to 5,016 time-slice rows** and **809 analytical synthetic
ridge contacts**. The source loop internally reported about **1.794
seconds**, around **1.23 million SOURCE steps/second**, with approximately
**3.488 seconds** for Java17 compile, simulation and standalone HTML.
These numbers depend on the local hardware and **are NOT Forge or real game
simulation throughput**.

Identical seeds gave byte-equal summary JSON, every trial CSV, sample
trajectory CSV, and self-contained offline HTML in two independently
executed full-size runs. Changing the seed changes the generated physical
trajectories. The experimental controller draws on existing
`FlightControlLoop`, `TacticalAirAI`, per-airframe Atlas v3 parameters, and
the newly pinned original aerodynamic forcing. It is **not** a complete
multi-aircraft physical battle: synthetic enemy observations are kinematic,
terrain uses an analytical ridge rather than block collision, and no
projectile damage/hits/kill are invented.

## 5. Scope contract: what is actually solved and what is NOT_RUN

**MEASURED and VERIFIED under the stated original-JAR/free-air conditions:**
20Hz input interpolation phase, original per-plane 100–200tick engine
reaction, baseline constant/accelerated pitch/yaw/forward, friction, glide,
gravity, float wind harmonics and mass-specific aerodynamic response,
original 35 recorded source-control flights. No player needs to repeatedly
launch Minecraft for those already measured conditions.

**SOURCE-only useful laboratory experiments, NOT independently verified
parity:** new speed/altitude/control/heading profiles, SOURCE autopilot
counterfactual policy decisions, scripted hostile contacts and formation,
analytic terrain/ridge and deterministic additional weather stress.

**FAILED / NOT_ESTABLISHED / NOT_RUN:** B-17 fixed original rear escort
59/190 source corridor ticks, actual B-17 original 101/340 inside95;
Minecraft voxel collision solver, vehicle dimensions and loaded-chunk
feedback, fluids, ground handling and actual touchdown, damage and crash,
all mounted weapons and projectile/kill attribution, friendly muzzle and
line-of-sight fire safety, 24-aircraft *simultaneously moving* large combat,
and independent NEW-policy-to-real-Forge closed-loop outcome equality.
Those remain necessary before claiming a complete Minecraft-compatible
autonomous warflight simulator. All weapons stay **fail-closed**.
