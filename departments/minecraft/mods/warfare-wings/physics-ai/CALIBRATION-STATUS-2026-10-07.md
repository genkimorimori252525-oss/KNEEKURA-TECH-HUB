# Warfare Wings Physics AI — Calibration Status (2026-10-07)

## Current state

**Infrastructure: READY. Same-artifact Minecraft trace: NOT_RUN because the registered self-hosted runner is offline.**

This is a capability boundary, not a physics PASS/FAIL result.

## Green layers

### Pure Java microkernel

- Java 17 source microkernel compiles and runs.
- 18 source-invariant checks pass.
- A6M/P-47N deterministic performance reports reproduce byte-for-byte.
- A6M throttle-step trace emits 401 ordered samples (tick 0..400).
- repeated microkernel trace generation is byte-identical.

### Comparator

The standard-library comparator is implemented and self-tested.

Outputs:

- `calibration-diff.csv`
- `calibration-summary.json`
- `calibration-ai-view.json`
- `calibration-summary.md`

It reports per-tick drift plus RMSE/max/final/checkpoint metrics and phase-event deltas without
inventing an acceptance threshold.

The AI-view keeps every sample, so the preferred inspection order is:

```text
calibration-summary.json
        ↓
calibration-ai-view.json
        ↓
calibration-diff.csv at suspicious ticks
        ↓
raw Minecraft log only if needed
```

### Forge runtime probe source

The isolated Forge 1.20.1 / Forge 47.4.20 probe compiles on GitHub-hosted Linux under Java 17.

The probe:

1. spawns real `warfare_wings:a6m`;
2. mounts an ArmorStand pilot so IA keeps the aircraft active;
3. disables wind/fuel-consumption/collision-damage noise for this calibration scenario;
4. seeds position `(0,200,0)`, velocity `(0,0,0.7)`, engine target `1`;
5. records the shared trace schema for 400 physics ticks.

## Exact runtime identity gate

The runtime workflow **must not** silently download the public Warfare Wings 1.1.4 artifact.

It requires a locally owned JAR with:

`SHA-256 dc3029597c88859744633b6f5e4a9f21d449294b1aaac90ea0c1749d7aa98a43`

If no matching local JAR is found, the run fails.

Immersive Aircraft is fetched by immutable Modrinth version:

`GsVmbbkj`

and checked against the retained SHA-512:

`7b74442e161bb74538e0d8da34a81616daeea56a0da62db86113a78b3bf3c2b3a6b0e12f12454fd7c96092762f6b212ba57cb87eb1af2b242a4d5df4eca03055`

No raw mod JAR is committed.

## Current external blocker

GitHub Actions runner API at the final check reported:

```text
name: Jolly-TechHub
os: Windows
status: offline
busy: false
labels: self-hosted, Windows, X64, tech-hub, kneekura
```

Therefore the exact Minecraft trace is **NOT_RUN**.

## Next executable boundary

When `Jolly-TechHub` is online:

1. update/push `.github/warfare-wings-physics-ai-runtime-request.txt` on the research branch;
2. the branch-scoped runtime workflow starts on the self-hosted Windows runner;
3. it searches only explicit/local candidate locations for the supplied Warfare Wings JAR;
4. it verifies exact SHA-256 and refuses public fallback;
5. it runs the A6M throttle GameTest;
6. it generates the matching microkernel trace;
7. it runs `compare_traces.py`;
8. it uploads raw trace, calibration summary, AI-view and logs as one bounded artifact.

The request file is intentionally **not** created while the runner is offline, so no indefinitely
queued runtime job is being presented as active evidence.

## Promotion rule

A successful GameTest does not by itself make the microkernel "Minecraft-equivalent".

The first runtime trace will be used to identify:

- engine-power phase agreement;
- speed-response agreement;
- accumulated position drift;
- source-vs-binary/runtime discrepancies.

Only after repeat runs establish same-artifact variance will numerical acceptance thresholds be set.
