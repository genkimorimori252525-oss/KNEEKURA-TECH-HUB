# Warfare Wings Physics AI — Implementation Status (2026-10-07)

## Implemented

A pure-Java Java 17 source microkernel now exists under `physics-ai/src/`.

Implemented source-faithful 1.3.3 behaviors:

- 20 Hz tick contract;
- raw X/Y/Z control + explicit engine target;
- 10-tick input exponential smoothing;
- rotation-decay interaction with smoothed X/Z before controller use;
- 20-tick engine-power smoothing adjusted by acceleration;
- one-tick phase separation between current raw input and the physics that consumes prior smoothed input;
- one-tick phase separation between engine target and the thrust using prior smoothed engine power;
- direct yaw/pitch control;
- pitch stabilizer;
- velocity-vector bending by `lift`;
- `friction`, horizontal/vertical decay and speed-dependent custom gravity;
- glide conversion from descent into forward velocity;
- exact 1.3.3 hard-coded brake multiplier 0.95;
- thrust `enginePower^2 * engineSpeed`;
- simple deterministic height-field movement/contact boundary;
- baseline wind disabled through a pluggable `World` interface.

Not implemented as exact behavior:

- Minecraft `Entity.move` voxel collision;
- fluids/chunks;
- exact IA cosine-noise wind;
- network ownership/synchronization;
- client-originated crash damage;
- real projectile entities / additional-shape hit callbacks;
- fuel inventory stochastic consumption;
- Forge/Warfare Wings same-artifact runtime parity.

## A6M / P-47N seed models

The raw aircraft values were re-read directly from the user-supplied ANCHOR:

`warfare_wings-1.1.4-1.20.1-forge.jar`

SHA-256:

`dc3029597c88859744633b6f5e4a9f21d449294b1aaac90ea0c1749d7aa98a43`

The current model CSV is separate from the legacy measured-profile CSV.

This separation is intentional because the historical exact-runtime measurements came from a differently identified Warfare Wings artifact.

## Pure Java verification

Local source verification performed in the current execution environment:

```text
javac --release 17 ...
java ... Ia133MicrokernelSelfTest
java ... PerformanceReportMain
node check-microkernel.mjs --java-home <JDK>
```

Observed:

```text
Ia133MicrokernelSelfTest passed: 18 checks
Warfare Wings Physics AI microkernel checks passed; real Minecraft parity NOT_RUN
```

The Node harness compiles the Java 17 source, runs the self-test, regenerates both A6M/P-47N reports,
and requires byte-identical equality with the committed golden CSV/Markdown.

## Current source-microkernel result

| Aircraft | predicted top speed | yaw change / 20t | pitch change / 20t | turn-exit speed retention |
|---|---:|---:|---:|---:|
| A6M | 33.67 b/s | 34.24° | 31.53° | 0.977 |
| P-47N | 45.79 b/s | 22.52° | 21.62° | 0.991 |

Interpretation:

- P-47N wins the source-microkernel flat speed tendency because `engineSpeed` is 0.102 vs 0.075;
- A6M wins identical-command nose authority because `yawSpeed/pitchSpeed` are 3.8/3.5 vs 2.5/2.4;
- P-47N has durability 5.0 vs A6M 2.5;
- no turn-inertia explanation is attributed to `mass`;
- raw `driftDrag` is not substituted for runtime `friction`.

## Important mismatch retained

The legacy exact-runtime A6M top-speed reference is about 43.63 b/s, while the source microkernel predicts about 33.67 b/s.

This batch does **not** tune the microkernel to erase that mismatch.

Possible evidence boundaries already known:

1. the legacy measurement used a different Warfare Wings artifact identity;
2. source-tag ↔ distributed Immersive Aircraft 1.3.3 binary equivalence is still unproven;
3. Minecraft/runtime details outside the current microkernel may contribute.

The correct next step is a **same-artifact trace replay**, not hand-adjusting constants until the numbers match.

## Next parity milestone

For the supplied Warfare Wings ANCHOR plus the exact target Immersive Aircraft runtime:

1. record per-tick throttle-step telemetry;
2. replay the identical command sequence in the microkernel;
3. compare engine power, speed and position;
4. then repeat yaw-step, pitch-step, sustained turn, glide and braking traces;
5. only after those transfer functions are bounded, use the microkernel for large-batch air-combat AI tuning.


## Trace-calibration layer

Added after the initial microkernel milestone:

- [TRACE-SCHEMA-v1.md](TRACE-SCHEMA-v1.md) — shared runtime/microkernel tick schema;
- [scenarios/a6m-throttle-step-v1.json](scenarios/a6m-throttle-step-v1.json) — exact 400-tick control scenario;
- `TraceCsv.java` / `TraceScenarioMain.java` — deterministic microkernel trace generation;
- `runtime-probe/` — isolated Forge GameTest source for the exact real-aircraft trace;
- `tools/compare_traces.py` — per-tick drift and phase comparator;
- [CALIBRATION-OUTPUT-v1.md](CALIBRATION-OUTPUT-v1.md) — machine/human output contract;
- [CALIBRATION-STATUS-2026-10-07.md](CALIBRATION-STATUS-2026-10-07.md) — exact current execution boundary.

Hosted verification now establishes:

- pure-Java microkernel/trace checks: GREEN;
- comparator self-test: GREEN;
- Forge runtime-probe source compile: GREEN;
- same-artifact real Minecraft trace: **NOT_RUN**.

The exact real trace is not blocked by missing implementation. The registered Windows runner
`Jolly-TechHub` was queried through GitHub Actions and reported `offline`.

The branch runtime workflow is designed to use only the user-owned Warfare Wings ANCHOR matching
SHA-256 `dc3029597c88859744633b6f5e4a9f21d449294b1aaac90ea0c1749d7aa98a43`; no public artifact
fallback is allowed.


## 24-aircraft Aircraft Atlas

The exact supplied Warfare Wings ANCHOR is now represented as a derived all-base-aircraft dataset:

- `data/base-aircraft-anchor-v1.csv`
- `data/base-aircraft-anchor-v1.json`

The extractor requires the exact supplied JAR SHA-256 and verifies all 24 canonical base IDs. Raw
Warfare Wings values and effective IA 1.3.3 values/defaults are kept separate. In particular,
`raw_driftDrag` remains provenance while `effective_friction=0.015` follows the inspected 1.3.3
source loader contract.

`AircraftAtlasMain` then runs all 24 aircraft through one deterministic source-microkernel feature
suite and produces:

- `reports/base-aircraft-source-atlas.csv` — 24 source feature vectors;
- `reports/aircraft-atlas-ai-view.json` — per-axis ranks, doctrine ranks, query flags and statistical inspection data;
- `reports/AIRCRAFT-ATLAS.md` — human-readable extrema and doctrine contrasts.

Current source-Atlas extrema:

| Axis | Highest | Lowest |
|---|---|---|
| source-predicted speed | P-47N | B-17 |
| 20-tick yaw response | IL-2 | B-17 |
| 20-tick pitch response | A6M / IL-2 tie | B-17 |
| identical-input 20-tick speed retention | B-17 | A6M |
| durability | B-29 | A6M |

The fixed-duration retention axis remains intentionally labeled **identical-input retention**. Atlas v2 now also adds an **equal-angle 90°** experiment, so the two questions no longer have to be conflated.

The Atlas computes no composite "best aircraft" score. Ranking stays per-axis so tactical consumers
can choose the relevant dimensions without hiding trade-offs.

High-value contrasts already visible in source space include:

- P-47N: fastest source tendency but lowest yaw/pitch response inside `energy_fighter`;
- Ki-84: near-top speed while leading `energy_fighter` yaw/pitch response;
- IL-2: highest yaw response across all 24 despite attacker role;
- Ju 87 vs IL-2: same attacker doctrine, strongly different speed/control envelope;
- G10N1/G10N2: identical wind-off Atlas features despite mass 22 vs 17, consistent with mass not
  acting as ordinary yaw/pitch inertia in the inspected source path.

These remain `SOURCE_MICROKERNEL` facts until same-artifact runtime calibration promotes them.
## Atlas v2 equal-angle extension

The source Atlas schema is now `ww.physics.aircraft-atlas.v2`.

New fields:

- `ticks_to_90_yaw`;
- `equal_angle_90_speed_retention`;
- `distance_to_90_yaw_blocks`.

The AI-readable view is `ww.physics.aircraft-atlas-ai.v2`. It ranks `turn_90_ticks` and
`distance_90` with **lower values first**, while speed/yaw/pitch/retention/durability continue to
rank higher values first.

The two retention dimensions are deliberately separate:

1. **same-input retention** — same 20-tick control duration;
2. **equal-angle retention** — same achieved 90° yaw change.

All 24 aircraft reach 90° within the bounded source scenario. Observed turn time spans **41 ticks
(IL-2) to 118 ticks (B-17)**.

This materially changes interpretation without erasing the old measurement:

- A6M: 42 ticks / 0.925567 — very fast nose change, highest speed cost among the 24;
- P-47N: 60 / 0.964626 — slower heading change, better equal-angle retention;
- B-17: 118 / 0.994638 — very low speed loss but very high time cost;
- IL-2: 41 / 0.951955 — fastest source 90° result despite attacker role.

The distance-to-90 value is path distance under this scenario, **not** asserted to be an aerodynamic
turn radius.