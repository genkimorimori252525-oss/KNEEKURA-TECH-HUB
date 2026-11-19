# A6M vs P-47N — IA 1.3.3 Microkernel Report

> Status: **SOURCE-MICROKERNEL ONLY / REAL-RUNTIME PARITY NOT YET RUN.**  
> Warfare Wings model values come from supplied ANCHOR SHA-256 `dc3029597c88859744633b6f5e4a9f21d449294b1aaac90ea0c1749d7aa98a43`.  
> Legacy measured values are historical references from a differently identified Warfare Wings runtime artifact.

| Aircraft | Source-predicted top speed | Yaw change (20t) | Pitch change (20t) | Turn exit retention | Durability |
|---|---:|---:|---:|---:|---:|
| warfare_wings:a6m | 33.67 b/s | 34.24 deg | 31.53 deg | 0.977 | 2.5 |
| warfare_wings:p47n | 45.79 b/s | 22.52 deg | 21.62 deg | 0.991 | 5.0 |

## Explainable differences

- **Speed tendency — SOURCE_DIRECT:** P-47N uses `engineSpeed=0.102` vs A6M `0.075`. IA 1.3.3 thrust is `enginePower^2 * engineSpeed`; this source microkernel predicts 45.79 b/s vs 33.67 b/s in the flat/wind-off envelope.
- **Nose authority — SOURCE_DIRECT:** A6M uses `yawSpeed=3.8` / `pitchSpeed=3.5`; P-47N uses `2.5` / `2.4`. The identical 20-tick yaw trace yields 34.24 vs 22.52 degrees.
- **Survivability input — SOURCE_DIRECT:** P-47N durability 5.0 is twice A6M 2.5; IA divides normalized vehicle damage by durability before health reduction.
- **Mass caution:** no turn-inertia claim is made from `mass`; the inspected 1.3.3 source does not use mass as ordinary yaw/pitch inertia.
- **driftDrag caution:** raw values differ (A6M 0.008, P-47N 0.013), but the pinned source loader registers runtime `friction`; both seed models therefore use default 0.015.

## Legacy reference — NOT a parity verdict

- warfare_wings:a6m legacy measured top speed: 43.63 b/s — legacy exact-runtime profile; older public Warfare Wings artifact; reference-only
- warfare_wings:p47n legacy measured top speed: 44.90 b/s — legacy exact-runtime profile; older public Warfare Wings artifact; reference-only

The A6M source prediction differs strongly from the legacy measurement. That mismatch is preserved as evidence, not tuned away: the old profile came from a differently identified Warfare Wings artifact, and IA source-tag ↔ distributed-binary equivalence is still not proven. The next gate is same-artifact Minecraft trace replay.
