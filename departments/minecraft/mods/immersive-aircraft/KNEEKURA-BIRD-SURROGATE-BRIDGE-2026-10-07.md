# Kneekura-bird — Immersive Aircraft 1.3.3 Surrogate Bridge

## Decision

Build a **source-faithful Immersive Aircraft 1.3.3 microkernel** inside the Kneekura-bird fast
simulation layer, not a general Minecraft clone and not an unrelated aerodynamic simulator.

The three-layer validation model is:

```text
Layer A — fast IA 1.3.3 microkernel
  deterministic / batchable / cheap
  policy search, parameter sweeps, doctrine experiments
          ↓
Layer B — headless Forge parity oracle
  exact Modrinth IA GsVmbbkj
  exact Warfare Wings runtime entity
  real Minecraft Entity.move / blocks / projectile logic
          ↓
Layer C — normal client, only when necessary
  client-only crash damage path
  rendering/camera/player UX
```

Layer A accelerates discovery. Layer B decides whether a candidate transfers. Layer C is not the
ordinary AI-development loop.

## 1. Do not write a second AI

The production AI and fast simulator must share one decision core.

Preferred architecture:

```text
Combat/Mission Snapshot
        ↓
pure target + doctrine + guidance policy
        ↓
ControlProposal
        ↓
┌──────────────────────┬──────────────────────┐
│ IA 1.3.3 microkernel │ Minecraft adapter    │
│ fast state update    │ setInputs / engine   │
└──────────────────────┴──────────────────────┘
```

The current `ControlProposal` / `ControlAuthorityArbiter` refactor is therefore a useful
prerequisite, not unrelated cleanup.

Do not destabilize the active arbiter conversion merely to begin simulator work. Extract pure
records/functions around the accepted control boundary after the single-writer shape is stable.

## 2. Fast state contract

Recommended `Ia133AircraftState`:

```text
position xyz
velocity xyz

yaw
pitch
roll                        # derived/observer state where possible

rawInputX
rawInputY
rawInputZ

smoothInputX
smoothInputY
smoothInputZ

engineTarget
enginePowerSmooth
fuelUtilization

previousY                   # glide term
onGround
touchingWater
tick

health                      # when damage policy is under test
ammo / weapon state         # when weapon policy is under test
```

Do not reduce this to scalar speed + heading if dogfight energy transfer is the objective.

## 3. Aircraft model contract

Recommended `Ia133AircraftModel`:

```text
id
role
faction
doctrine

engineSpeed
yawSpeed
pitchSpeed
pushSpeed
acceleration
durability
fuel
friction
glideFactor
lift
rollFactor
groundPitch
stabilizer
wind
mass
groundFriction
waterFriction
rotationDecay
horizontalDecay
verticalDecay

collision approximation
weapon descriptors
```

The model is populated from **effective values**, not blindly copied JSON.

### Friction rule for the 1.3.3 ANCHOR

Unless an actual `friction` property is present through the runtime data path:

```text
friction = 0.015
```

Do not substitute JSON `driftDrag`.

This needs a regression test because old Kneekura-bird tooling did exactly that substitution.

## 4. One source-faithful fast tick

A minimal deterministic update should preserve this sequence:

```text
INPUT BOUNDARY
  policy chooses raw x/y/z + engineTarget

PRE-MOVE STATE
  use previous smoothed input values
  use previous smoothed engine power

VELOCITY PHASE
  compute forward vector
  apply descent->forward glide conversion
  bend velocity direction toward forward by lift
  apply alignment-sensitive friction magnitude
  apply horizontal/vertical decay + custom gravity
  optional deterministic wind
  optional ground-pitch treatment

CONTROL / THRUST PHASE
  yaw from smooth X
  pitch from smooth Z
  stabilizer
  negative raw Y -> target reduction + 0.95 brake
  compute thrust = enginePower^2 * engineSpeed
  add thrust along forward

MOVE PHASE
  integrate position
  query simplified terrain/contact/collision

POST-MOVE PHASE
  update smoothed raw X/Y/Z
  update engine-power smoothing
  update deterministic/continuous fuel approximation
```

For parity replay, keep 20 ticks/second.

## 5. Minecraft-independent policy snapshot

The AI should consume a record similar to current `FlightSnapshot`, but without Minecraft classes:

```text
ownship:
  state above
  AGL
  horizontal and total speed
  movement heading
  effective flight profile

targets:
  relative position
  relative velocity
  target forward vector
  distance
  closure
  aspect
  angle off nose
  line of sight

safety:
  terrain samples
  predicted aircraft separation
  mission boundary
  protected-fire corridor

mission:
  order
  phase
  home/runway/route
  fuel/ammo/damage abort state
```

Adapters produce this snapshot from either Minecraft or the fast simulator.

## 6. WorldQuery boundary

Do not reproduce Minecraft's world engine.

Recommended interface:

```text
double groundHeight(x,z)
RayResult raycast(start,end)
CollisionResult aircraftCollision(stateA,stateB)
boolean insideScenarioBounds(position)
WindSample windAt(position,tick,seed)
```

Initial scenarios can use:

- flat world;
- deterministic height fields;
- a small obstacle set;
- coarse aircraft collision ellipsoids/AABBs.

Real voxel collision remains a parity test.

## 7. Weapon contract

### Fixed forward guns

The fast weapon descriptor should include:

- muzzle speed relative to aircraft;
- mount/convergence direction;
- firing cone;
- min/max policy range;
- shot cadence / burst state;
- ammunition;
- optional inaccuracy;
- hit volume approximation.

For Warfare Wings' fixed machine gun, previous binary analysis observed approximately 94 blocks/s
relative muzzle speed and 80-block convergence.

Because Immersive Aircraft adds aircraft sampled velocity to projectile velocity, the fast kernel can
either:

1. simulate world projectile velocity as `aircraftVelocity + muzzleVelocity`, or
2. solve in the shooter-relative frame with relative target velocity.

Kneekura-bird's current relative-motion intercept formulation is compatible with option 2.

### Bombs / torpedoes

Separate dynamics. Do not overload the fighter-gun solver.

## 8. Calibration program

The microkernel should begin from source equations, then use exact telemetry to account for Minecraft
boundaries and implementation details.

### C01 throttle step

Flat air start, X/Z zero, target 0 -> 1.

Compare:

- enginePower curve;
- speed curve;
- time to fixed speed fractions;
- steady top speed.

### C02 yaw step

At several stabilized speeds, apply X = ±1.

Compare:

- yaw response;
- smoothed X;
- speed/energy loss;
- position arc.

### C03 pitch step

At several stabilized speeds, apply Z = ±1.

Compare:

- pitch response;
- vertical velocity;
- total speed;
- altitude.

### C04 sustained turn

Hold a production-representative turn command.

Compare:

- 90/180/360-degree elapsed time;
- speed floor;
- altitude loss/gain;
- path radius.

### C05 glide / engine-off

Cut engine from cruise and use fixed pitch states.

Compare:

- descent;
- forward speed conversion;
- glide distance.

### C06 stall / recovery

Use the existing benchmark safety envelope.

Compare:

- onset of descent;
- minimum speed;
- altitude lost;
- recovery time.

### C07 brake / landing

Ground/approach samples.

Compare:

- 0.95 per-tick braking behavior when input is held;
- contact transition;
- stopping distance.

Do not expect the fast terrain contact model to reproduce exact Minecraft collision byte-for-byte.

### C08 projectile trace

Fixed-gun shot from known aircraft velocity.

Compare:

- projectile position over short horizons;
- inherited shooter velocity;
- hit timing against known geometry.

## 9. Error metrics

Do not declare one global "Minecraft accuracy" percentage.

Record per-aircraft, per-envelope metrics:

- position RMSE / maximum drift at 1s, 2s, 5s and scenario end;
- velocity-vector error;
- speed error;
- yaw error;
- pitch error;
- enginePower error;
- energy proxy error;
- turn-time error;
- stall/recovery event timing;
- stopping-distance error;
- shot-opportunity timing;
- exact policy action/state agreement.

Thresholds must come from repeated exact-run variance. If exact GameTest itself varies by X, a
surrogate threshold tighter than X has no engineering meaning.

## 10. Existing measured profiles remain authority

Kneekura-bird already has runtime-measured profiles for all 24 base Warfare Wings aircraft.

Those profiles contain, among other fields:

- stall guard speed;
- cruise speed;
- climb target speed;
- turn speed floor;
- brake lead / lower-bound distance;
- measured top speed.

Use them as:

- policy envelope authority;
- calibration targets;
- guardrails for source-microkernel outputs.

Never replace them with `parse_aircraft_stats.py` theoretical values.

## 11. Legacy parser correction

Current `tools/parse_aircraft_stats.py` has a historical theoretical model that:

- extracts `driftDrag`;
- labels 0.015 as default friction;
- nevertheless uses the per-aircraft `driftDrag` value in speed/energy calculations;
- approximates turn-energy retention with additional invented coefficients.

That output can remain as historical exploratory material, but it should be relabeled or repaired
before being used by new AI work.

Recommended future change, separate from the current arbiter PR:

1. rename theoretical output as legacy/non-authoritative;
2. resolve effective `friction` exactly as IA 1.3.3 does;
3. replace scalar equations with the shared microkernel;
4. regression-check selected aircraft against measured profiles.

Do not mix this cleanup into unrelated combat-control commits.

## 12. Headless parity gate

Candidate doctrine/tuning flow:

```text
pure policy unit tests
  ↓
recorded-snapshot decision parity
  ↓
fast IA microkernel:
  hundreds/thousands of scenario seeds
  ↓
shortlist candidate parameters
  ↓
exact headless Forge:
  same aircraft / initial condition / mission
  ↓
compare telemetry + acceptance invariants
  ↓
optional normal client only when client-only behavior matters
```

No candidate becomes production evidence from the fast simulator alone.

## 13. Scenario matrix for fighter AI

Start with the existing A6M / P-47N mutual dogfight because exact evidence already exists.

Then add:

```text
turn vs turn
  A6M / Spitfire / Yak-3

energy vs turn
  P-47N vs A6M
  Bf 109 vs Spitfire
  Ki-84 vs P-51D

energy vs energy
  P-47N vs P-51D
  Fw 190 vs Ki-84
```

Vary:

- distance;
- closure;
- aspect;
- starting speed;
- altitude advantage;
- crossing angle;
- initial offensive/defensive state;
- terrain clearance.

Metrics:

- time to first valid firing solution;
- reciprocal firing;
- firing-solution occupancy;
- min/max separation;
- ground-contact frames;
- stall-risk duration;
- energy retention;
- action transition oscillation;
- disengage/re-entry duration.

Only after 1v1 transfers reliably should 2v2 target deconfliction become a fast-sim optimization
target.

## 14. Realism policy

Immersive Aircraft's fixed-wing physics directly yaws/pitches the aircraft and uses a velocity-vector
alignment model. It is not a realistic banked-turn flight simulator.

Therefore separate two goals:

### Runtime parity

"AI understands and exploits the actual Minecraft aircraft."

This is mandatory.

### Tactical realism

"AI chooses maneuvers resembling real fighter doctrine: energy management, separation, defensive
breaks, re-entry, lead pursuit, mutual support."

This is desirable and can be developed on top of the arcade dynamics.

If the project later wants genuinely realistic bank-to-turn aerodynamics, that is a **physics-mod
change**, not just better AI. Keep it out of the first surrogate milestone or the simulator will no
longer predict the game being controlled.

## 15. Suggested implementation order

1. Finish/stabilize Kneekura-bird's current single-writer `ControlAuthorityArbiter` conversion.
2. Add a documented correction for the `driftDrag` theoretical-parser assumption.
3. Extract Minecraft-independent vectors/snapshots/control records around the existing policy.
4. Implement the IA 1.3.3 state and per-tick microkernel with flat-world contact only.
5. Replay C01–C06 exact command traces and build drift reports.
6. Add terrain/query abstraction.
7. Add fixed-gun projectile opportunity simulation.
8. Add A6M vs P-47N batch runner.
9. Add optional lightweight 3-D viewer/trajectory visualizer.
10. Use parameter sweeps/evolutionary search only after parity is measured.
11. Extend role-specific weapon models when bomber/attacker/torpedo production policy exists.

The fast simulator is a laboratory. Headless Forge remains the runtime truth oracle.
