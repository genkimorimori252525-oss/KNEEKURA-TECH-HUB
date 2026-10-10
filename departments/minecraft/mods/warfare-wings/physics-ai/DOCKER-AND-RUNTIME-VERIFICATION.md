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

If the runner is offline, the workflow can remain queued; do not mark runtime parity as PASS or call a queued job a measurement. The earlier registered-runner status was **offline** and the exact run remains `NOT_RUN` until verified execution evidence exists.

## 3. Evidence boundary

| Stage | Environment | Output and permitted conclusion |
|---|---|---|
| Docker headless | Java 17 + Python + Node, network disabled while running | `SOURCE_MICROKERNEL` deterministic verification only |
| Hosted Forge-source compile | Java 17, ForgeGradle 8.8, no target JARs | Probe source compiles; no real aircraft was spawned |
| Owner Windows real GameTest | Exact local Warfare Wings SHA-256 + Immersive Aircraft SHA-512 | `MEASURED` runtime trace after it actually completes |
| Calibration comparison | Real trace paired with the source trace | Drift/phase metrics; no parity acceptance threshold yet |

Never promote historical public-data predictions or source-only Atlas ranks into same-artifact runtime measurements.
