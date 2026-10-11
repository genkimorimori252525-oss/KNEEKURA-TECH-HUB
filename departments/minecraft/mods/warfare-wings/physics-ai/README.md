# Warfare Wings — Physics AI Laboratory

## Latest research milestone (2026-10-11)

**[FLIGHT-PHYSICS-TWIN-2026-10-11.md](FLIGHT-PHYSICS-TWIN-2026-10-11.md)**
documents the opt-in bytecode-reconstructed original IA 1.3.3 aerodynamic
speed-dependent wind, deterministic source physics, and strict **35 paired
real-Forge flight receipts / 24 original aircraft / 5,880 actual 20Hz steps**.
With the *pre-recorded actual aircraft command sequence and original airborne
initial state*, the 35 source replays reproduce their final positions to
**≤0.001776 blocks** under the tested free-air/no-voxel conditions. This is
**not** a certificate for autonomous policy, collisions, weapons, crashes,
landing, terrain or complete Minecraft parity.

**[FLIGHT-RESEARCH-LAB.md](FLIGHT-RESEARCH-LAB.md)** describes the Java 17
offline experiment engine: **12,288 seeded trials / 2,211,840 SOURCE physics
ticks**, 24 aircraft × 11 controlled experiments, and a new genuinely
simultaneous **24-distinct-aircraft, closed-loop SOURCE Flight Twin** with
per-observer enemy range/FOV/LOS/short-memory tracks, team radio, input control
and original pinned IA aerodynamic integration. Both research engines emit
offline self-contained HTML trajectory inspection and deterministic JSON/CSV;
run `tools/flight_lab_run.py --mode both`. Source closed-loop policies and
height-field sensor/collision assumptions are **not Forge validated**. Use
`tools/run_physics_twin.py` against original real Forge receipts for the
separate recorded-command physical-fidelity gate.

The **20 required exact-owner Forge GameTests still give 19 PASS, one true
FAILED**. The older #38119475729 run had **101/340** B-17 intrusions and
also froze the B-17 long strike at tick499. Following legitimate live B-17
enemy-team visibility and test-only chunk-liveness repairs, a later local
original-JAR run restores **841/841 IL-2 and B-17 strike/egress/RTB samples**
and 35/35 physically faithful recorded-command replays, but B-17 protection
still **FAILED (135/340, minimum 41.695 blocks)**. See the separate audited
run chronology in [FLIGHT-PHYSICS-TWIN-2026-10-11.md](FLIGHT-PHYSICS-TWIN-2026-10-11.md).
The **subsequent local original-JAR test with the 20-block-descending source
escort waypoint and an expanded two-chunk test-only load margin** completed
all original 340tick B-17 aircraft flight traces, and the 840tick strike still
passed. The independently measured protected B-17 intrusions fell further
to **49/340 ticks, nearest hostile 82.571b**, but still breach the unchanged
95-block corridor; additionally, the left escort's net displacement was
29.594b against the immutable 30b minimum. **Real Forge remains 19/20,
one FAILED**. See chronological detail in the Flight Physics Twin note.
No weapon is fired; original mounts, server launch/cooldown, ownership, muzzle
LOS and friendly-fire behavior remain evidence-gated. PR #102 stays **Draft**.

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

## Current implementation

The pure-Java microkernel, same-artifact calibration bridge, and 24-aircraft source Atlas now exist.

The first deterministic **tactical decision layer** now also exists:
[`TACTICAL-AI-IMPLEMENTATION-v1.md`](TACTICAL-AI-IMPLEMENTATION-v1.md)
describes the 24-aircraft role-aware controller, scenario replays, historically
sourced optional unit/year formation orders, and next Forge integration gates.
[`CONTROL-LOOP-INTEGRATION-v1.md`](CONTROL-LOOP-INTEGRATION-v1.md)
records the source-to-input autopilot, lookahead terrain/aircraft safety guards,
24-aircraft dynamic heading-acquisition tests and exact-game acceptance gates.
[`TACTICS-EVIDENCE-v1.md`](TACTICS-EVIDENCE-v1.md) documents the historical
source audit; these candidate tactics are not yet validated in Minecraft.

The later source- and Forge-side implementation added explicit-team live air
groups, finite-visibility/occlusion/contact memory, heading-rotated formation
stations, operator mission orders, 1v1/2v2 encounters and geometric strike
phases. See [`FORGE-INTEGRATION.md`](FORGE-INTEGRATION.md),
[`COMBAT-SIMULATION-v1.md`](COMBAT-SIMULATION-v1.md) and
[`RUNNER-READINESS-2026-10-11.md`](RUNNER-READINESS-2026-10-11.md).
The original exact owner JAR was subsequently recovered and SHA-verified.
The original **13/13** GameTest success was an earlier *baseline-only*
milestone including sequential 24-plane aircraft smokes and five
representative traces. The later real simultaneous combat GameTests extend
the suite to **19/20 PASS**; the B-17 95-block mission guard genuinely FAILED
(101/340 ticks in the previous owner CI, 135/340 in the subsequent local
Forge run), even though source replay and other live missions succeed.
The historical PowerShell UTF-8 BOM failure and later artifact endpoint
failure were independently resolved. An evidence fail is not a CI transport
failure and is never silently waived.
See [`ENGINE-REACTION-CALIBRATION-v1.md`](ENGINE-REACTION-CALIBRATION-v1.md)
for the new bytecode-verified 24-plane engine reaction catalog and the
completed, non-frozen 401-tick A6M source/runtime comparison.
No real Minecraft weapon effects, successful hostile escort defense or
generally accepted source/runtime physics parity is claimed.

```text
warfare-wings/
  physics-ai/
    README.md
    AIRCRAFT-PERFORMANCE-MODEL.md
    IMPLEMENTATION-STATUS-2026-10-07.md
    CALIBRATION-STATUS-2026-10-07.md
    TRACE-SCHEMA-v1.md
    CALIBRATION-OUTPUT-v1.md
    check-microkernel.mjs
    data/
      a6m-p47n-anchor-models.csv
      a6m-p47n-legacy-measured-reference.csv
      base-aircraft-anchor-v1.csv
      base-aircraft-anchor-v1.json
    src/main/java/.../
      Ia133Microkernel.java
      WarfareWingsAircraft.java
      PerformanceReportMain.java
      AircraftAtlasMain.java
    src/test/java/.../
      Ia133MicrokernelSelfTest.java
    tools/
      extract_anchor_aircraft.py
      build_aircraft_atlas.py
      compare_traces.py
    reports/
      a6m-p47n-source-microkernel.csv
      a6m-p47n-source-microkernel.md
      base-aircraft-source-atlas.csv
      aircraft-atlas-ai-view.json
      AIRCRAFT-ATLAS.md
```

Current verified scope:

- dependency-free Java 17;
- 20 Hz source-microkernel;
- exact supplied-ANCHOR derived data for all **24 base aircraft**;
- A6M and P-47N focused seed/reference models;
- 18 pure-Java invariant checks;
- deterministic 24-aircraft source-Atlas regeneration;
- AI-readable **Atlas v2** independent-axis ranks, doctrine contrasts and statistical inspection flags;
- fixed-duration and equal-angle 90° turn metrics kept as separate questions;
- deterministic 401-sample throttle trace generation;
- threshold-free trace comparator + AI-readable full-series output;
- Forge runtime-probe source compilation;
- real same-artifact Minecraft trace: **NOT_RUN — registered runner offline**.

See [IMPLEMENTATION-STATUS-2026-10-07.md](IMPLEMENTATION-STATUS-2026-10-07.md) and [CALIBRATION-STATUS-2026-10-07.md](CALIBRATION-STATUS-2026-10-07.md).

For the reproducible source-only Docker stage and the separately gated owner-controlled Windows GameTest, see [DOCKER-AND-RUNTIME-VERIFICATION.md](DOCKER-AND-RUNTIME-VERIFICATION.md). Docker performs headless Java 17 validation without target game binaries; it does not replace real Minecraft calibration.

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

## Next implementation milestone

The 24-aircraft source Atlas is now implemented. The next gate is **same-artifact runtime calibration**, prioritized by what the Atlas can falsify fastest:

1. run the existing A6M throttle-step trace on the exact supplied Warfare Wings ANCHOR;
2. add the same P-47N throttle trace to test the high-`engineSpeed` end of the source model;
3. add A6M/P-47N yaw and pitch steps to validate the two fighter-control extremes already used in tactical comparisons;
4. add IL-2 and B-17 yaw traces because the Atlas places them at the global high/low yaw extremes;
5. reproduce the implemented **90° equal-angle turn** scenario in Minecraft for representative fighters/attackers/bombers, comparing turn time, speed retention and path distance;
6. calibrate representative attacker/escort envelopes and promote trustworthy Atlas axes toward `MEASURED`;
7. only after those transfer functions are bounded, use the fast environment for large-batch autonomous combat tuning.

See [reports/AIRCRAFT-ATLAS.md](reports/AIRCRAFT-ATLAS.md) for the current 24-aircraft overview.
## Atlas v2 turn semantics

The source Atlas now carries both:

- `same_input_retention` — speed retained after the same 20-tick full-yaw input;
- `equal_angle_retention` — speed retained after each aircraft actually reaches 90° yaw.

It also records `turn_90_ticks` and `distance_90`. This prevents a slow-turning aircraft from
looking "efficient" solely because it changed little heading during the fixed 20-tick window.

Representative source results:

| Aircraft | 90° ticks | Equal-angle retention | Distance to 90° |
|---|---:|---:|---:|
| IL-2 | 41 | 0.951955 | 63.074 |
| A6M | 42 | 0.925567 | 68.547 |
| Spitfire | 44 | 0.935021 | 91.231 |
| Yak-3 | 46 | 0.939018 | 96.495 |
| Ki-84 | 48 | 0.941936 | 104.950 |
| P-47N | 60 | 0.964626 | 134.909 |
| B-17 | 118 | 0.994638 | 118.738 |

These remain `SOURCE_MICROKERNEL`, not same-artifact measurements.
