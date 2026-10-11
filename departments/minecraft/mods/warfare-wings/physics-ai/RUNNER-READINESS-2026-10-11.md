# Warfare Wings — owner runner readiness and exact-artifact gate (2026-10-11)

Observed runner: `Jolly-TechHub`, labels
`self-hosted, Windows, X64, tech-hub, kneekura`. At the
2026-10-11 validation it was **online and idle**, and successfully accepted
owner Windows workflow [#38109783517](https://github.com/genkimorimori252525-oss/KNEEKURA-TECH-HUB/actions/runs/38109783517).

Early GitHub Actions evidence from run #38109783517:

1. Checkout, Temurin Java 17, and Gradle setup: **PASS**.
2. `Stage exact runtime jars`: **FAILED** with
   `Exact user-owned Warfare Wings ANCHOR not found`.
3. All real Minecraft GameTests at this **early run**: **NOT_RUN**.

### October 11 recovery (after that first blocked run)

- Three owner-supplied exact original WW 1.1.4 JARs were located inside
  top-level `Downloads` subdirectories, each with **identical exact SHA-256**
  `dc3029597c88859744633b6f5e4a9f21d449294b1aaac90ea0c1749d7aa98a43`.
  The original is available. Do not use the byte-different public build.
- Explicit-path self-hosted run
  [#38110700138](https://github.com/genkimorimori252525-oss/KNEEKURA-TECH-HUB/actions/runs/38110700138)
  passed both pinned JAR hash checks and Java/Gradle setup, then **FAILED
  during Forge UserDev boot**: the unmodified Immersive Aircraft Mixin
  refmap referenced SRG `Player.m_36342_()`, but the ForgeGradle
  official-mapped class had a readable method name.
- In the shared workspace, the ForgeGradle-generated
  `build/createSrgToMcp/output.srg` mapping confirmed the exact translation.
  The userdev GameTest JVM now supplies `mixin.env.remapRefMap=true`
  and the corresponding `mixin.env.refMapRemappingFile` pointing at that
  mapping; **neither game binary was patched**.
- The subsequent exact-artifact **local Forge 1.20.1 GameTest passed all
  12 required tests** after removing cross-batch spawned-aircraft
  interference. A **subsequent 13-test local exact-artifact run** also
  passed the new `AllAircraftRosterGameTests`, which serially instantiates
  all 24 derived aircraft for 40 actual entity ticks each with physical
  displacement, yaw and raw input assertions. Exact
  `run-gametest/logs/latest.log` terminator:
  `All 13 required tests passed :)`. Five aircraft also recorded complete
  180-tick steering/movement traces: A6M, P-47N, IL-2, B-17 and G4M.
  This is local actual Minecraft measurement, not a replayed source simulation.
- The strict receipt verifier derived the correct airborne IA input
  recurrence `0.859905 * previousSmooth + 0.1 * rawCommand` from the
  exact Atlas input friction and rotation decay, and independently passed
  all five local control traces. This is **controller telemetry agreement**,
  not full physics parity, weapon firing or practical escort victory.
- The companion `verify_all_aircraft_runtime_receipts.py` independently
  checked 24 actual 40-tick CSVs (`roster-<plane>-forge-controls.csv`)
  against their exact Atlas-derived model retention and fixed minimum
  physical motion: `ALL_24_SEQUENTIAL_RUNTIME_SMOKES_VERIFIED`. This is a
  **single-aircraft serial smoke**, not a 24-on-24 simultaneous dogfight.

### Source-model physics parity is **not** established

A genuine owner-JAR A6M 401-sample throttle trace is now available locally
(`runtime-probe/run-gametest/ww-physics-traces/a6m-throttle-step-v1-runtime.csv`)
alongside regenerated Microkernel traces and the threshold-free
`tools/compare_traces.py` report. One **earlier invalid capture** repeated
the same actual aircraft position and engine state between ticks 223 and
400 because the airplane left the loaded chunk. Its apparent peak
25.0815 blocks/s, speed RMSE 11.9768 and engine RMSE 0.26584
**must not be treated as complete 400-tick physical observations**.
`RuntimeTraceManager` now forces and releases its own test corridor,
checks actual entity tickCount continuity, and fails rather than recording
a non-ticking aircraft.

The subsequent completed **400 actually moving ticks** produced:

| Same-artifact comparison | Legacy source (reaction20) | Exact bytecode source (reaction100) | Real Minecraft |
|---|---:|---:|---:|
| Maximum A6M speed in 400-tick throttle trace | 33.6700 b/s | 32.1310 b/s | 31.7603 b/s |
| First engine power 0.5 tick | 14 | 69 | 69 |
| Engine power RMSE | 0.2589 | 0.00000019 | reference |
| Speed RMSE | 10.9859 b/s | 0.1554 b/s | reference |
| Final speed absolute error | 1.9097 b/s | 0.3707 b/s | reference |

The new `WarfareWingsEngineReaction` opt-in 24-model catalog was checked
against each exact-JAR `getEngineReactionSpeed()` override. The A6M's
observed engine discrepancy was primarily the old generic20 versus actual100
reaction time. The corrected source has **2.621 blocks final origin-aligned**
position drift and a small residual speed difference; no general physics
parity verdict or tolerance is assigned yet.

This is still `CALIBRATION_ONLY_NO_ACCEPTANCE_THRESHOLD`, **not**
`SOURCE_RUNTIME_PARITY_PASS`. The source model is no longer blindly
retuned based on an incomplete trace. Repeat equal-envelope calibration
for A6M, P-47N, IL-2 and B-17 before promoting the derived Atlas.

The original researched Warfare Wings SHA-256 is
`dc3029597c88859744633b6f5e4a9f21d449294b1aaac90ea0c1749d7aa98a43`.
A byte-for-byte check of a publicly hosted Warfare Wings 1.1.4 Forge JAR
(29,568,717 bytes) gave SHA-256
`3b6b245e703862517fe7aae6acd95ccafc865e1e81ba7a26e2b9abcfe1120187`,
which **does not match** the previously supplied research artifact. The
comparison download was removed from the ignored local cache. Do not use
this public JAR as evidence of the user's same-artifact physics.

The pinned Immersive Aircraft 1.3.3 runtime SHA-512 is
`7b74442e161bb74538e0d8da34a81616daeea56a0da62db86113a78b3bf3c2b3a6b0e12f12454fd7c96092762f6b212ba57cb87eb1af2b242a4d5df4eca03055`.
The owner workflow automatically downloads that particular pinned Modrinth
version **only after** locating the exact user-supplied Warfare Wings JAR,
and then independently hashes it.

## Reproducible runtime command and remaining gate

The original Warfare Wings ANCHOR JAR now exists in the owner's Downloads
collections. Select an existing exact-hash matching copy on the Windows
Jolly-TechHub machine at a path readable by the runner account. Do not
commit or upload the JAR to this Git repository. Verify it with:

```powershell
$wwAnchor = 'C:\ABSOLUTE\PATH\TO\warfare_wings-1.1.4-1.20.1-forge.jar'
(Get-FileHash -LiteralPath $wwAnchor -Algorithm SHA256).Hash.ToLowerInvariant()
```

The digest must equal the exact SHA-256 shown above. Set the optional
`warfare_wings_path` input to this absolute path when dispatching
`warfare-wings-physics-ai-runtime.yml` for branch
`jolly/research-warfare-wings-2026-10-07`, or configure the runner process
environment variable `KNEEKURA_WW_ANCHOR_JAR`. The workflow also checks
the runner account's top-level `Downloads` and `Documents` folders for
the exact canonical filename.

The gate was demonstrated PASS in the above exact-artifact local and
self-hosted attempts. For automated acceptance on the latest PR commit,
dispatch the owner runner **again after the source-side refmap fix is
committed**. It must then pass the entire GameTest suite and trace receipts
as one exact-ref reproducible GitHub workflow. The earlier self-hosted job's
FAILURE is retained as historical evidence and is not relabeled.

## Evidence to accept afterward

The workflow must pass old A6M header + 401 records, five independent
single-aircraft control CSVs (header + 181 records), live team-pair and
same-team CSVs, server-side FOV/occlusion GameTests, and strict
`verify_tactical_runtime_receipts.py` checks. Review elapsed tick order,
real yaw and displacement, IA X/Z smoothing, terrain hazard decisions,
equipment API availability and physical parity separately. The comparator
currently operates as a **calibration investigation with no acceptance
tolerance**; GameTest success alone cannot promote all 24 aircraft's
source-model performance rankings to real Minecraft parity.
