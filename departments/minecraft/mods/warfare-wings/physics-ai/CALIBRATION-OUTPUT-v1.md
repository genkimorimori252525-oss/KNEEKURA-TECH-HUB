# Warfare Wings Physics AI — Calibration Output v1

The calibration layer is optimized for both machine inspection and quick human review.

For each exact-runtime scenario it emits:

- `calibration-diff.csv` — one row per tick; raw paired values plus scalar error measures;
- `calibration-summary.json` — compact metrics, checkpoints and phase-event deltas;
- `calibration-ai-view.json` — all ordered samples in a chart-ready JSON series;
- `calibration-summary.md` — concise human-readable report.

## Metrics

The first schema records:

- 3-D position error;
- 3-D velocity error;
- total and horizontal speed error;
- yaw, pitch and roll angular error;
- engine-target error;
- engine-power error;
- fuel-utilization error;
- smoothed X/Y/Z control error.

For every metric the summary keeps:

- RMSE;
- mean absolute error;
- maximum absolute error and the tick where it occurred;
- final absolute error;
- values at tick 20 / 100 / 200 / 400 when present.

## Phase events

The A6M throttle-step report also records:

- engine power reaching 50%;
- engine power reaching 90%;
- speed reaching 90% of each trace's own final speed;
- peak speed and peak tick.

These are useful for distinguishing a constant-value mismatch from a temporal/phase mismatch.

## No premature PASS threshold

Version 1 deliberately reports:

`CALIBRATION_ONLY_NO_ACCEPTANCE_THRESHOLD`

A tiny error is not automatically a PASS and a large error is not automatically a bug in the
microkernel. Acceptance thresholds should be chosen only after repeated same-artifact Minecraft
runs establish natural runtime variance and the binary/source relationship is better bounded.

## AI-readable view

`calibration-ai-view.json` retains every tick; it is not down-sampled.

This is the preferred first-read artifact for an AI agent because it combines:

- ordered time;
- runtime and microkernel speed;
- runtime and microkernel engine power;
- position and velocity drift;
- speed, yaw and pitch error.

An agent can chart only the suspicious series after reading the compact summary, rather than opening
raw Minecraft logs first.