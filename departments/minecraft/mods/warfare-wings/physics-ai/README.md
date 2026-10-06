# Warfare Wings — Physics AI Laboratory

## Status

This is the canonical home for the **Warfare Wings physical-reproduction / autonomous-air-combat research**.

The goal is not to preserve or extend Kneekura-bird as a product. Kneekura-bird is historical evidence
only: its measured flight profiles and headless validation results may be reused when their exact
runtime provenance is still valid.

The active research unit lives here, under Warfare Wings.

## Purpose

Build a fast, explainable, source- and telemetry-calibrated environment that can:

1. reproduce the relevant Immersive Aircraft 1.3.3 fixed-wing behavior cheaply;
2. preserve Warfare Wings aircraft-to-aircraft performance differences;
3. run large numbers of autonomous-flight / dogfight experiments without launching a normal client;
4. explain **why** one aircraft behaves differently from another;
5. promote results only after parity checks against the real Minecraft runtime.

This is a laboratory and evidence system, not a second Minecraft implementation.

## Dependency boundary

Warfare Wings supplies:

- concrete aircraft entities;
- per-aircraft data / geometry / seats;
- weapon mounts and addon weapons;
- role / faction / doctrine metadata in the supplied ANCHOR artifact.

Immersive Aircraft supplies the important flight/runtime machinery:

- input smoothing;
- engine-power smoothing and fuel utilization;
- yaw / pitch control;
- velocity-vector alignment ("lift");
- glide conversion;
- friction / decay;
- custom gravity;
- thrust / braking;
- vehicle data and upgrades;
- Minecraft movement handoff;
- weapon base classes and network messages;
- additional projectile hit-box integration.

The Immersive Aircraft 1.3.3 source analysis is preserved separately as dependency evidence.
The canonical **AI / simulator plan**, however, belongs here.

## Planned structure

```text
warfare-wings/
  physics-ai/
    README.md
    AIRCRAFT-PERFORMANCE-MODEL.md
    physics-core/              # future pure deterministic implementation
    aircraft-profiles/         # future explainable per-aircraft derived profiles
    scenarios/                 # future dogfight / flight scenario definitions
    calibration/               # future real-runtime trace -> surrogate comparison
    reports/                   # future batch / parity / regression results
    viewer/                    # optional simple 3-D observer
```

Only the two documents exist in this research batch. The directories shown as future components are
a design, not an implementation claim.

## Core design

### Fast path

A compact 20 Hz physics microkernel should carry:

- 3-D position and velocity;
- yaw / pitch and observer roll;
- raw and smoothed control inputs;
- engine target and smoothed engine power;
- previous altitude sample for glide behavior;
- fuel utilization when relevant;
- terrain / contact state;
- weapon state when relevant.

The update order should follow the pinned Immersive Aircraft 1.3.3 behavior closely enough to retain
its temporal lag and energy-transfer behavior.

### Real-runtime oracle

The fast result is never final evidence by itself.

A promoted AI/physics change must pass a real-runtime parity gate using the exact target Minecraft /
Forge / Immersive Aircraft / Warfare Wings identities. A normal client is required only for behavior
that is genuinely client-owned or visual.

## Explainability contract

Every per-aircraft performance claim should answer four questions:

1. **What was observed?**
   - measured top speed, turn response, climb, glide, braking, firing geometry, etc.
2. **What input differs?**
   - engineSpeed, yawSpeed, pitchSpeed, lift, glideFactor, durability, weapon layout, etc.
3. **Through what mechanism can that input matter?**
   - exact source equation / state transition / weapon rule.
4. **How certain is the attribution?**
   - direct source relationship, measured correlation, inference, or unknown.

Do not explain a measured performance difference using a JSON field merely because the field has a
plausible name. The `driftDrag` case demonstrates why: a field can exist in data while the pinned
host runtime source does not consume it under that name.

## Evidence levels for performance explanations

Use these labels:

- `MEASURED` — exact runtime telemetry or repeatable benchmark result;
- `SOURCE_DIRECT` — the pinned runtime source directly uses the value in the relevant equation;
- `SOURCE_INDIRECT` — the source uses the value through upgrades/state/another derived value;
- `CORRELATED` — observed association across aircraft, but contribution is not isolated;
- `INFERENCE` — engineering interpretation consistent with evidence but not isolated;
- `UNKNOWN` — do not invent an explanation.

A high-quality performance card combines `MEASURED + SOURCE_DIRECT`.

## Initial calibration families

- throttle / acceleration response;
- stabilized maximum speed;
- fixed-X yaw response at multiple speeds;
- fixed-Z pitch response at multiple speeds;
- sustained-turn energy loss;
- engine-off glide;
- stall / recovery envelope;
- approach / braking;
- projectile time-of-flight and firing solution;
- aircraft-aircraft separation.

## What "realistic air combat" means here

Two independent axes must remain separate.

### Runtime fidelity

The AI correctly predicts and controls the actual Warfare Wings + Immersive Aircraft aircraft.

Mandatory.

### Tactical realism

The AI chooses plausible fighter behavior:

- lead / lag pursuit;
- break turns;
- vertical separation;
- energy preservation;
- disengagement / re-entry;
- boom-and-zoom behavior;
- mutual support / target deconfliction.

Desirable.

A tactically realistic AI can operate on arcade-like host physics. Replacing the host physics with
true aerodynamic bank-to-turn mechanics would be a separate MOD-physics project.

## Historical Kneekura-bird material

Kneekura-bird may be mined for:

- already-measured 24-aircraft flight profiles;
- exact Modrinth version identities used by old tests;
- useful telemetry formats;
- scenarios that exposed difficult AI behavior.

It is not the canonical architecture or project home.

When useful material is imported, record its original revision/runtime identity and preserve it as
legacy evidence rather than requiring future work to depend on that repository.

## Immediate next implementation milestone

Before tuning combat doctrine:

1. import or recreate a small authoritative measured-aircraft profile dataset in Tech Hub;
2. implement the source-faithful 1.3.3 physics microkernel;
3. create deterministic trace replay;
4. validate A6M and P-47N first because they strongly separate turn-fighter and energy-fighter
   behavior;
5. generate explainable per-aircraft performance reports;
6. expand to all 24 base aircraft;
7. only then use the environment for large-batch autonomous combat tuning.
