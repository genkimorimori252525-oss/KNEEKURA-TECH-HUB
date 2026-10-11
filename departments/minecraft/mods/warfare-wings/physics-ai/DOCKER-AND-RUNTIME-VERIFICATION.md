# Warfare Wings Physics AI — headless Docker and exact-runtime verification

## 1. Source-only Docker stage (any machine with Docker)

From the repository root, use the following commands in PowerShell with Docker running Linux containers (validated on `linux/amd64`):

```powershell
$wwPhysics = 'departments/minecraft/mods/warfare-wings/physics-ai'
docker build --pull --progress plain -f "$wwPhysics/Dockerfile" -t warfare-wings-physics-ai:source $wwPhysics
if ($LASTEXITCODE -ne 0) { throw 'Docker build failed' }
docker run --rm --network none --read-only --tmpfs '/tmp:rw,nosuid,nodev,size=256m,mode=1777' --security-opt no-new-privileges warfare-wings-physics-ai:source
if ($LASTEXITCODE -ne 0) { throw 'Headless physics verification failed' }
```

The Docker image contains a Java 17 JDK, Node 22, Python 3, source files, derived aircraft data and reference reports. The Dockerfile copies a positive allowlist of files from `physics-ai`; it does **not** copy `runtime-probe`, any local `.jar`, or the user's Minecraft installation. At verification time the container has no network, a read-only root filesystem, and temporary writable `/tmp` for compilation and regenerated report comparisons.

The image executes `tools/verify_headless.py`, which requires:

- the existing 18 Java invariants, deterministic 401-row throttle traces and golden report comparison;
- the source-side tactical AI self-test covering all 24 aircraft when present in the checked-out harness;
- comparator self-tests on matching and deliberately perturbed traces;
- strict Forge tactical runtime receipt-parser self-tests with intentionally
  corrupted synthetic CSVs (17 checks), without confusing fixtures with game telemetry;
- independent 24-airframe serial GameTest receipt-parser synthetic checks:
  reject missing, overlong or physically inconsistent per-plane control traces;
- synchronized multi-aircraft real-Forge receipt-parser synthetic checks:
  reject non-synchronized ticks, missing aircraft, nonfinite coordinates,
  unsafe sub-6-block body separation and intruders within an unchanged
  95-block B-17 protection corridor;
- 24-aircraft Atlas JSON semantic equality and normalized Markdown equality with committed reports.

Expected terminating markers:

```text
HEADLESS_SOURCE_PASS: Java 17 invariants, deterministic traces, comparator and 24-aircraft Atlas
REAL_MINECRAFT_PARITY: NOT_RUN
```

All checks use the checked-out source and report files. The Docker build pins the Node/Debian base image manifest by SHA-256 and installs distribution OpenJDK 17/Python 3 packages. The resulting image ID is recorded in GitHub-hosted CI logs. Debian package revisions can still change with `apt-get update`, so byte-identical full-image reconstruction would additionally require a frozen OS package snapshot; the test/report equality is deterministic with the current toolchain. Updating the pinned base image digest should be a deliberate reviewable change.

GitHub-hosted Actions runs this stage in the `docker-headless` job of `.github/workflows/warfare-wings-physics-ai-source.yml`, independent of the existing pure-Java and Forge-source compilation jobs. The Docker stage is not evidence of Minecraft runtime behavior or historical aircraft performance.

## 2. Exact Minecraft/Forge stage (owner-controlled Windows runner)

This stage uses `.github/workflows/warfare-wings-physics-ai-runtime.yml` and the registered Windows x64 self-hosted runner with labels `self-hosted`, `Windows`, `X64`, `tech-hub`, and `kneekura`. It cannot be performed by the GitHub-hosted Docker job because the target Warfare Wings binary is a locally supplied, owner-controlled artifact.

Before dispatch, confirm:

1. `Jolly-TechHub` shows **Online / Idle** in GitHub repository Settings → Actions → Runners, with the listed labels; the action's Windows account can read the locally owned target JAR.
2. Java 17 and Gradle 8.8 are available through the workflow's setup actions. The runner can reach Forge/Maven dependencies and the immutable Modrinth Immersive Aircraft version `GsVmbbkj`.
3. Place `warfare_wings-1.1.4-1.20.1-forge.jar` in an absolute local path that the runner account can access. Its SHA-256 must be exactly `dc3029597c88859744633b6f5e4a9f21d449294b1aaac90ea0c1749d7aa98a43`.

Dispatch **Warfare Wings Physics AI Runtime Trace** on the branch `jolly/research-warfare-wings-2026-10-07`; pass the absolute file path in the optional `warfare_wings_path` input. Alternatively, configure the `KNEEKURA_WW_ANCHOR_JAR` environment variable for the runner process. The workflow also checks the runner account's `Downloads` and `Documents` folders for the exact expected filename, but an explicit absolute path is more reliable when the runner runs as a service.

The run first hashes each local candidate, only copying a SHA-256 match into the isolated Gradle runtime directory. It then fetches Immersive Aircraft from the pinned Modrinth version and verifies SHA-512 `7b74442e161bb74538e0d8da34a81616daeea56a0da62db86113a78b3bf3c2b3a6b0e12f12454fd7c96092762f6b212ba57cb87eb1af2b242a4d5df4eca03055`. A missing/mismatched local Warfare Wings JAR is a hard failure; no public fallback occurs. The staged private JAR is not part of the uploaded trace artifact.

On successful runtime startup, the Forge 1.20.1 / 47.4.20 GameTest spawns the real A6M, captures header plus 401 tick records, regenerates the microkernel trace, and writes the detailed comparison beneath `runtime-probe/run-gametest/ww-physics-traces/`. The action uploads those traces, calibration summary, AI-view and logs with a 14-day retention. A successful workflow proves this concrete run executed, **not** that source physics equals the actual Minecraft implementation: the comparator deliberately uses `CALIBRATION_ONLY_NO_ACCEPTANCE_THRESHOLD` pending repeated exact-artifact calibration.

Five additional tactical GameTests must each produce a header and **181 CSV data samples**
(initial tick 0 plus 180 actual server ticks). The owner-runner CI checks all five
aircraft identities, movement, yaw, control bounds and tick continuity. A second,
independent Python validator (`tools/verify_tactical_runtime_receipts.py`) verifies
 the recorded per-airframe IA input-filter recurrence
 `smooth[N] = (1 - model.friction) * model.rotationDecay * 0.9 * smooth[N-1] + 0.1 * command[N]`
for X/Z, using the exact 24-aircraft ANCHOR source CSV, and writes
`tactical-runtime-receipts.json` only after all five traces pass. For the
current pinned airborne models, `(1-0.015)*0.97*0.9 = 0.859905`;
an unconditional factor of `0.9` would *falsely reject* the real aircraft
controller and is not the source Microkernel's formula.
Its synthetic corruption tests run in hosted and offline Docker CI via
`tools/test_tactical_runtime_receipts.py`. These tests confirm that invalid
receipts are rejected; they never manufacture game measurements. On
2026-10-11, the exact-user-JAR local GameTest produced all five 180-tick
traces and the corrected source-derived validator returned
`FIVE_RUNTIME_CONTROL_TRACES_VERIFIED`. This is controlled-flight evidence,
not a certification of all 24 aircraft physics or military doctrine.
The 13-test subsequent local Forge suite also produced 24 independent
`roster-<id>-forge-controls.csv` traces (40 real ticks each). The source-Atlas
validated all-24 receipt checker requires 41 samples per file, exact WW identity,
three or more steering ticks, >=0.25 degrees continued yaw and >=4 blocks
actual displacement: `ALL_24_SEQUENTIAL_RUNTIME_SMOKES_VERIFIED`. Every
roster aircraft is removed before the next is spawned, so these traces do
**not** establish 24-plane simultaneous combat/formation performance.

If the runner is offline, the workflow can remain queued; do not mark
runtime parity as PASS or call a queued job a measurement. The owner runner
was confirmed **online** on 2026-10-11. A previous self-hosted run lacked
the original JAR; a subsequent exact-artifact run reached Forge startup,
but failed in its development Mixin refmap. The local ForgeGradle
SRG-to-official mapping fix allowed 12 actual GameTests to execute and pass;
the hosted CI and local test results must still be reported separately.

## 3. Evidence boundary

| Stage | Environment | Output and permitted conclusion |
|---|---|---|
| Docker headless | Java 17 + Python + Node, network disabled while running | `SOURCE_MICROKERNEL` deterministic verification only |
| Hosted Forge-source compile | Java 17, ForgeGradle 8.8, no target JARs | Probe source compiles; no real aircraft was spawned |
| Owner Windows real GameTest | Exact local Warfare Wings SHA-256 + Immersive Aircraft SHA-512 | `MEASURED` runtime trace after it actually completes |
| Calibration comparison | Real trace paired with the source trace | Drift/phase metrics; no parity acceptance threshold yet |

Never promote historical public-data predictions or source-only Atlas ranks into same-artifact runtime measurements.

## 4. Synchronized multi-aircraft geometric acceptance (not combat victory)

`tools/verify_live_aircombat_receipts.py` independently evaluates multiple
aircraft **on the same observed Forge server ticks**. Each CSV must use the
real `ww.physics.forge-tactical-pilot.v1` source/column schema with exactly
`ticks+1` consecutive recorded samples, at least 8 blocks of real position
change, explicit team membership and unique per-pilot trace filenames.
An absent flight, nonconsecutive clock or mismatched identity is fatal.

Supply a JSON manifest in the following structural form, using **only actual
GameTest-emitted CSV filenames** (these placeholder names are not measured
evidence):

```json
{
  "scenario": "game-test-case-id",
  "kind": "escort",
  "source": "minecraft_runtime_ia_next_tick_injection",
  "ticks": 190,
  "flights": [
    {"id": "bomber", "file": "measured-bomber.csv", "aircraft_id": "warfare_wings:b17", "scenario_id": "bomber-observed", "team": "blue"},
    {"id": "guard", "file": "measured-guard.csv", "aircraft_id": "warfare_wings:p47n", "scenario_id": "guard-observed", "team": "blue"},
    {"id": "intruder", "file": "measured-intruder.csv", "aircraft_id": "warfare_wings:a6m", "scenario_id": "intruder-observed", "team": "red"}
  ],
  "assets": ["bomber"],
  "escort_assignments": {"bomber": ["guard"]}
}
```

Run `python tools/verify_live_aircombat_receipts.py <manifest.json>
<actual-trace-directory> --summary <report.json>` from any working directory.
For `kind=aircombat`, omit `assets` and `escort_assignments`; the all-pair
6-block guard remains enforced. `kind=escort` additionally fails if an enemy
ever enters the 95-block defended distance to an explicitly named asset.
The CLI emits factual per-pair/asset distances and exit code 1 on operational
gating failure. A failure report is still written when `--summary` is used.
Synthetic verifier tests in source/Docker CI do **not** demonstrate success
of any live flight. Actual GameTest aircraft liveness and team/escort orders
must additionally be asserted inside the Forge probe; manifest metadata alone
does not prove those facts, nor do safe geometries prove any weapon hit/kill.

The pinned operational GameTests supply non-placeholder manifests at
`scenarios/forge-operational-2v2.json` (four simultaneous planes over
280 ticks) and `scenarios/forge-operational-b17-escort.json` (five simultaneous
planes over 340 ticks). They are checked only when real per-plane receipts
are available. The real Forge tests additionally require actual opposing
engagement and sustained ESCORT phases. The independent verifier cannot
replace those game-side mission assertions. A failed GameTest or missing
per-plane trace must never be reported as a passed combat mission.
