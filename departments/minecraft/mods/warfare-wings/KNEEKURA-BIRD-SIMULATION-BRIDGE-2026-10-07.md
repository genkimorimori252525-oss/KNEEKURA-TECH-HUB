# Warfare Wings ↔ Kneekura-bird — Air-Combat Simulation Bridge (2026-10-07)

## Decision

**Adopt the user's idea, but do not build a second general-purpose Minecraft engine.**

Kneekura-bird already contains the correct validation ladder:

1. fast deterministic pure-Java simulation;
2. headless Forge GameTest using real Minecraft + Warfare Wings + Immersive Aircraft physics;
3. optional interactive client observation only when visual/manual evidence is needed.

The missing piece is a **fast mutually interacting air-combat dynamics layer** between today's
mission simulator and the exact headless runtime. This should be a calibrated surrogate/digital
twin, not a replacement source of truth.

## Why this is the efficient path

The existing fast simulator is intentionally lightweight and explicitly says it does not reproduce
Immersive Aircraft physics. Its integration state is roughly heading + scalar speed + altitude +
vertical speed + mission phase. That is excellent for route-state reachability, takeoff/landing
gates and parameter sanity, but it cannot answer the central dogfight questions:

- can two aircraft continuously maneuver against each other?
- does an energy fighter preserve enough speed/altitude to disengage and re-enter?
- can a turn fighter maintain a useful pursuit geometry without bleeding to stall?
- when does a lead solution enter the real fixed-gun firing cone?
- do collision/terrain/friendly-fire constraints prevent otherwise good attacks?
- which policy parameters remain stable across many initial positions and aircraft pairings?

Today those questions ultimately require the expensive headless Forge path. The proposed bridge
moves most parameter search into a cheap process while retaining the exact GameTest as an oracle.

## Existing Kneekura-bird state that must be preserved

Live repository inspection at the time of this design found:

- all 24 base aircraft have route/landing exact-physics qualification recorded in `docs/AI_HANDOFF.md`;
- `dogfight_mutual` has recorded repeated mutual-firing acceptance;
- combat awareness, target selection, offensive maneuvering, defensive maneuvering and real weapon
  firing already exist;
- role/doctrine mission depth is still incomplete;
- Issue #7's single-writer control architecture is still being converted;
- draft PR #101 is the remaining base-autonomy / terrain-safety proposal conversion.

Therefore a new simulator must **share policy logic** with the production AI. Forking a second
dogfight AI implementation would create two truths and invalidate the speed advantage.

## Target architecture

```text
                         shared pure decision core
                    ┌─────────────────────────────┐
                    │ mission / role / doctrine   │
                    │ tactical state machine      │
                    │ target scoring              │
                    │ guidance math               │
                    │ weapon-release decision     │
                    └──────────────┬──────────────┘
                                   │
                           ControlCommand
                                   │
              ┌────────────────────┴────────────────────┐
              │                                         │
      Fast combat surrogate                       Minecraft adapter
      (100s-1000s episodes)                       (exact behavior)
              │                                         │
      calibrated dynamics                  Warfare Wings Entity
      simplified terrain/LOS               Immersive Aircraft physics
      projectile/weapon model              Minecraft collision/raycast
              │                                         │
              └────────────── parity / drift ───────────┘
                              comparison
```

The same tactical policy should consume an immutable, Minecraft-independent snapshot on both paths.

## Proposed pure contracts

### `AirCombatState`

Minimum ownship state:

- position vector
- velocity vector
- forward/up/right basis or quaternion
- yaw/pitch/roll and whichever angular rates materially affect transfer
- engine power / target
- on-ground state and AGL
- health / damage state once AircraftDamageAuthority exists
- fuel if mission behavior reads it
- ammo and weapon cooldown

### `AircraftModel`

Static/calibrated aircraft data:

- role, faction, doctrine
- Warfare Wings coefficients: engine/yaw/pitch/push/glide/lift/friction/roll/wind/mass
- measured Kneekura-bird flight profile values
- simplified collision dimensions
- weapon mount / convergence metadata

Do not assume raw JSON coefficients alone produce an exact standalone flight model. The real
Minecraft/Immersive Aircraft run remains the calibration source.

### `CombatObservation`

Per-policy-step observation:

- ownship `AirCombatState`
- candidate targets with relative position/velocity/orientation
- line-of-sight
- closure
- angle-off-nose
- aspect
- altitude advantage
- normalized energy estimate
- terrain-clearance samples
- aircraft-separation threats
- mission/order context

This mirrors information already computed by Kneekura-bird's combat managers but removes direct
`Entity`, `Level` and Minecraft vector dependencies from the decision algorithm.

### `ControlCommand`

- lateral/yaw control X
- engine/brake control Y or normalized engine target
- pitch control Z
- fire request
- bomb/torpedo release request
- selected authority / reason for telemetry

The existing `ControlProposal` concept is the natural bridge. The pure contract should converge
with the single-writer arbiter rather than bypass it.

### `WorldQuery`

A deliberately tiny environment interface:

- terrain height / clearance
- segment raycast for line-of-sight
- collision query against aircraft / optional coarse obstacles
- optional wind sample
- scenario boundaries

No chunk loading, block registries, recipes, renderer, packet stack or general entity engine is
needed in the fast path.

## Dynamics strategy

### Do not begin with a hand-written "realistic flight simulator"

The objective is parity with Minecraft's actual Immersive Aircraft behavior, not aerodynamic truth
at all costs. A physically elegant 6-DOF model that disagrees with the mod is worse for policy
transfer than a simpler model calibrated to exact telemetry.

### Recommended first model

Use a compact vector-state integrator at 20 Hz with:

- 3-D position and velocity;
- orientation;
- thrust / speed response;
- pitch/yaw authority as a function of profile and current speed;
- lift/velocity-direction coupling;
- drag/friction;
- glide/energy conversion;
- gravity/stall degradation;
- optional deterministic wind;
- collision ground plane / height field.

Fit or tune the response parameters from headless GameTest telemetry.

Today's measured profile already supplies useful gates. Add controlled excitation runs only when a
missing transfer function cannot be inferred: step throttle, fixed X input, fixed Z input,
energy-loss turn, dive/pullout and stall recovery.

### System-identification loop

```text
exact headless run
   -> per-tick telemetry dataset
   -> fit/update surrogate coefficients
   -> replay same command sequence in fast sim
   -> compare position / speed / attitude / energy envelopes
   -> retain error metrics
```

The surrogate is qualified per flight envelope, not by a single global "matches Minecraft" flag.

## Weapon model

### Fighter guns

The current production AI already reasons around a projectile speed of approximately 94 blocks/s.
The supplied Warfare Wings machine-gun bytecode independently supports the same value
(4.7 blocks/tick).

The fast model should reproduce:

- projectile time-of-flight;
- 80-block gun convergence as an aircraft/weapon property when relevant;
- current production fixed-gun cone and range gates;
- LOS;
- friendly-fire corridor;
- terrain interception;
- burst/cooldown/ammunition;
- hit volume and optional deterministic dispersion/damage.

During initial tuning, a "shot opportunity" metric can remain separate from stochastic damage. This
keeps tactics debuggable.

### Bombing / torpedo

Use separate weapon dynamics. Do not reuse fighter lead-fire code. Release-envelope tests should be
added only as their Issue #7 role/doctrine behavior is implemented.

## Rendering

The simple aircraft model the user proposed is useful, but it is an observer, not the simulator.

Recommended split:

```text
aircombat-core        no graphics, deterministic, fastest
aircombat-runner      scenario batches / sweeps / self-play
aircombat-viewer      optional simple 3-D aircraft/trajectory visualization
minecraft-adapter     real Forge/Entity integration
```

The viewer can begin with arrows/wireframe aircraft and trajectory trails. Its job is to reveal bad
geometry and tactical oscillation quickly; visual fidelity has no bearing on acceptance.

## AI tuning loop

### Phase A — deterministic policy parity

Before optimization, feed the same recorded snapshot into the extracted pure policy and the
Minecraft adapter. Require the same:

- selected target;
- tactical action;
- control proposal;
- fire/release decision;
- authority/reason.

This catches refactor drift before physics drift is even considered.

### Phase B — fast scenario matrix

Run hundreds/thousands of deterministic seeds over:

- A6M vs P-47N baseline;
- turn fighter vs turn fighter;
- energy fighter vs turn fighter;
- energy fighter vs energy fighter;
- altitude/speed advantage/disadvantage;
- crossing, head-on, tail chase and beam starts;
- terrain-clearance variants;
- 2v2 target-deconfliction cases.

Metrics should include:

- time to first firing solution;
- valid firing-solution time;
- reciprocal-shot count;
- minimum separation;
- terrain/ground violations;
- stall-risk duration;
- energy retention;
- time spent defensive/offensive/disengaged;
- target switching / oscillation;
- kill or damage proxy only after shot geometry is stable.

### Phase C — parameter search

Start with deterministic parameter sweeps / evolutionary search over doctrine constants. Reinforcement
learning is optional and should come later; the current policy is already interpretable and the main
bottleneck is simulation throughput, not lack of an AI formalism.

Use domain randomization around calibrated dynamics, weapon latency and sensor uncertainty so the
policy does not overfit the surrogate.

### Phase D — exact parity gate

A candidate parameter set is never promoted from fast simulation alone.

Gate:

1. unit / decision-parity tests;
2. fast combat surrogate matrix;
3. headless Forge GameTest with exact target aircraft pair and scenario;
4. telemetry comparison against surrogate;
5. only then optional visual client run if animation/appearance/player experience matters.

Failed exact runs become new calibration evidence rather than reasons to make the fast simulator
more permissive.

## What should be implemented first

Recommended bounded order:

1. **Do not disturb Issue #7's current arbiter conversion.**
2. Extract Minecraft-independent combat snapshot / vector math / tactical-decision records without
   changing behavior.
3. Add decision-parity tests against recorded/current snapshots.
4. Create a two-aircraft 3-D fast dynamics runner using measured `FlightProfile` plus Warfare Wings
   coefficients.
5. Replay exact GameTest control traces and quantify surrogate error.
6. Add fighter weapon opportunity / hit geometry.
7. Add scenario batch runner and optional viewer.
8. Only after parity is acceptable, use the fast environment for doctrine tuning.
9. Add bomber/attacker/torpedo weapon models when those production role policies exist.

## Acceptance criteria for the simulator itself

Do not call the fast environment "Minecraft-equivalent". Instead record per-aircraft / per-envelope
qualification such as:

- speed response error;
- turn-rate error;
- altitude/pitch response error;
- energy-loss error across sustained turns;
- stall/recovery envelope error;
- gun opportunity timing error;
- minimum-separation outcome;
- tactical state sequence agreement.

Thresholds should be selected from observed GameTest repeatability, not invented before baseline data
exists.

## Final recommendation

The user's proposed external/simple-model workflow is not merely reasonable; it is the natural next
step for Kneekura-bird.

The important correction is architectural:

> **Build a calibrated air-combat surrogate around a shared AI core, not a standalone Minecraft
> clone and not a second AI implementation.**

Kneekura-bird's headless Forge GameTest remains the truth oracle. The fast simulator exists to spend
CPU cheaply on search, variation and failure discovery before paying the Forge startup/runtime cost.
