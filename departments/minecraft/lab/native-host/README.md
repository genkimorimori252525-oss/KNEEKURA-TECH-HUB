# Persistent TechHub Tank host

TechHub owns the platform; the tested MOD is a profile input. This opt-in native host reuses the canonical Debug supervisor. It does not start the historical LAB, SimLab server or Web Viewer. Three existing pure motion/display/PNG libraries are included solely to close the canonical evidence modules' static imports; none starts a service or records anything.

Supported platform: Minecraft1.20.1, Forge47.4.10, JDK17, Gradle8.8 with official distribution checksum, ForgeGradle6.0.54 and official1.20.1 mappings. This is a development host: mapped development JARs load directly; Forge distribution JARs need explicit ForgeGradle dependency preparation. Other platforms/loaders and inferred artifact kinds are rejected. Actual MOD compatibility remains subject to Forge loading and native acceptance; profile-schema acceptance is not a compatibility result.

## One-time installation

From the matching TechHub LAB source, run:

```powershell
node native-host/tank.mjs install --java-home 'C:/Program Files/Java/jdk-17'
```

The result names `installed` and the installed CLI. Default storage is `%LOCALAPPDATA%/Kneekura/TechHub/Tank`. An immutable content-addressed bundle contains the host, wrapper, supervisor source closure, protocol helpers and observer source. Execution must use the installed CLI; development worktrees and artifact/temp folders are not runtime dependencies. Existing global Gradle caches are persistent user data; do not clean them during normal operation. Initial dependency preparation may download substantial assets and is not a warm-start measurement.

```text
node INSTALLED/native-host/tank.mjs warm --installation INSTALLED --online
node INSTALLED/native-host/tank.mjs doctor --installation INSTALLED
```

Only explicit `warm --online` enables online preparation. Normal warm, prepare and start run Gradle offline; missing cache entries fail with a retained log. No routine clean, dependency redownload or compiler bypass is used. Installation/doctor/import/warm never launches Minecraft. `doctor` verifies installation source hashes, dependency bytes and JDK version; it does not claim native READY. Keep failed installations/preparations for diagnosis; there is no automatic stale-lock stealing.

Successful warm publishes `%LOCALAPPDATA%/Kneekura/TechHub/Tank/active-host.json` and retains its versioned registration. Read this fixed entry to find `installed`; `nativeAcceptance: NOT_ESTABLISHED_BY_WARM` is deliberate. Existing trials retain their own exact installation. Dependencies use persistent Gradle storage and are hash-checked; removal requires explicit preparation, never a guessed historical classpath.

```powershell
$tankHome = Join-Path $env:LOCALAPPDATA 'Kneekura/TechHub/Tank'
$tankInstall = (Get-Content -LiteralPath (Join-Path $tankHome 'active-host.json') -Raw | ConvertFrom-Json).installed
node (Join-Path $tankInstall 'native-host/tank.mjs') doctor --installation $tankInstall
```

## Per-MOD profile and experiment

`profile.mjs` defines the exact JSON schema `kneekura.tank-profile/v1`. Fields: `id`, exact `runtime` (minecraft/forge/java), `mods` (id/absolute file/sha256/kind), `world` (absolute directory/inventorySha256), exact `playerUuid`/`subjectUuid`, target code `sourceRevision`, `mode`, `maxTicks`, `maxWallMs`, `maxEvents`. No executable command/environment/capability fields. MOD IDs are unique and dependencies are explicit entries. Modes are LIFECYCLE, MANUAL_OBSERVE or MANUAL_RALLY; mode names do not establish gameplay acceptance. Bounds:1..2400ticks,1..120000ms,1..512events, zero default images/input/mutation/motion grants.

[Profile example](profile.example.json) is a template, not runnable measured inputs. Replace every path/hash/actor with actual fixture/material facts before preparing.

For an explicit client mesh grid use `kneekura.tank-profile/v2`, the same fields plus `presentation: {"grid":true,"brightness":"NATIVE"}`. v1 retains its exact fields and gains no presentation authority. Preparation derives geometry from the actual hash-bound `kneekura-tank-owner.json`; request v2 seals renderer `tank-grid-v1`, recipe hash/bounds and separate `CLIENT_TANK_GRID_PRESENTATION`. Native startup verifies the actual matching world/recipe. This renders client lines only, with no camera, brightness override, effects, input, images, block changes or AI changes. Initial Player Night Vision belongs to a separately declared disposable fixture. The original finite window is consumed normally; STOP, expiry, world/disconnect or rendering failure clears the grid context. `grid-rendered.json` proves submitted geometry, not readable pixels; `presentation-result.json`/native result retains actual render count and cleared context. Existing four-direction cameras retain their separate contracts.

Manual events are discrete/change-only records using the existing `producerDeltaApplied` contract. After actual ACK/owned exit, `eventClosure` verifies every raw event's ID/content/contiguous writer sequence against canonical observations and the ACK's final sequence. Equal same-tick post-hurt events must not silently aggregate. Old installed bundles and finalized runs retain their original outcomes; do not rewrite them through this newer guard. Generic owner-change events also retain observed projectile velocity and Player body center for bounded aiming diagnosis; this is not full target-specific Rally telemetry.

Use a real40hex source commit when known. Binary-only profiles may use `sourceRevision: null`, sealed as `ARTIFACT_ONLY`; the MOD bytes remain mandatory SHA256 inputs, while source provenance/implementation acceptance stays unestablished. Do not invent a commit. TechHub source identity is still required. Natural's manual acceptance client additionally requires its actual source pin.

Prepare a target-specific fixture offline in a fresh copy before passing it to the platform. `inventory()` and `inventoryHash()` export the exact raw inventory format. Never open an original/finalized world with NBT/RegionFile tools. `prepare` copies and raw-verifies an already prepared fixture; it does not edit NBT, summon residents, alter AI or assume Reimu is needed. Copied input MODs and actual resolved/remapped artifacts are independently hashed before sealing and launch. Forge's actual loaded material hashes must match the sealed request.

```text
node INSTALLED/native-host/tank.mjs prepare --installation INSTALLED --profile PROFILE.json
node INSTALLED/native-host/tank.mjs start --trial TRIAL
node INSTALLED/native-host/tank.mjs status --trial TRIAL
node INSTALLED/native-host/tank.mjs stop --trial TRIAL
node INSTALLED/native-host/tank.mjs abort --trial TRIAL
node INSTALLED/native-host/tank.mjs evidence --trial TRIAL
```

`prepare` returns PREPARED_NOT_RUN and never starts a client. `start` is explicit and stays attached through the finite window and cleanup. It emits TANK_NATIVE_READY only after the actual native handshake; `startup.json` measures supervisor-start to READY, excluding preparation. Status/stop work from another process. The shared host has one exclusive build/run lock. Do not interrupt the start supervisor or remove a lock manually: an uncertain run must be reconciled against actual process identity. No second launch/retry, renewed window, automatic recording or scoped control authority is implied.

READY binds the real connected survival Player, declared living subject, private world, request/material hashes and actual process. The generic observer records selected vanilla Projectile ownership changes, actual AttackEntityEvent/LivingHurtEvent and post-hurt state. Event cancellation at LOWEST can still change at another listener of equal priority; removal does not establish impact, health differences may have multiple causes, ownership does not expose target-specific Rally counters/tells. A typed target observer and human testimony are separate acceptance inputs.

Before READY, an atomic native bootstrap claim binds the run/nonce/request/install/adapter hashes, PID/JVM start/executable and exact actual launch arguments. It grants cleanup only. `stop` before READY or explicit `abort` first requests graceful native shutdown, then revalidates actual identity immediately before any necessary exact-process termination. Both native and launcher exit must be verified before releasing that run's lock; absent/changed bootstrap identity remains UNKNOWN. The shared Gradle daemon is never adopted through ancestry. No READY, clean ACK or world acceptance is manufactured. Diagnostic-write failures cannot suppress a validated shutdown.

At most8 startup screen transitions record class/title and client-world/Player/server availability, with no clicks, captures or continuous history. A retained LoadingErrorScreen plus missing pack.mcmeta exposed a faulty test MOD; fixing its metadata in a new JAR resolved the actual swap failure. Keep failures and verify the actual cause; do not silently accept a warning screen or edit an unrelated world. Long internal Windows evidence paths are supported by Node/Java; Python callers need extended-length path handling rather than treating a plain-path FileNotFoundError as evidence absence.

STOP uses the unchanged canonical identity check. Actual ServerStopped/writer closure produces an ACK; the supervisor separately proves owned exit. An autonomous bounded expiry may exit before STOP; then only an actual matching retained native ACK plus separately VERIFIED_EXIT can close the run. This reconciliation does not change the canonical dispatcher/observer. Finalization completeness concerns retained evidence integrity, not complete gameplay coverage. Unexercised behavior stays NOT_RUN. Accepted product/world preservation and human/manual acceptance remain separate.

Recovery: preserve failed logs, run/session IDs and unknown cleanup. Do not kill unrelated Java/Gradle processes or release a lock by age/PID alone. Use the exact owned run's status/stop and inspect its actual ACK; an unclean or interrupted closure remains unaccepted. Previous installed bundles are retained. No source worktree or historical temporary host needs recreation.

Native platform acceptance: Natural mapped development JAR, an independent replacement MOD with Natural absent and explicit STOP, and Natural distribution-JAR preparation/remapping all have genuine READY/ACK/owned-exit/evidence receipts. Startup measurements are about25seconds versus a historical55second interval with different inputs. See [scoped results](../../../../docs/agent-decisions/2026-10-23-persistent-tank-results.md); this is not universal MOD compatibility, a controlled benchmark or manual Rally acceptance. Existing roster/fixed-camera/mob-eye features still require their original owners/contracts; this lane grants none automatically.


## Optional bounded motion diagnostics (v3)

Profile v3 retains explicit grid presentation and adds diagnostics from diagnosticDefaults() in diagnostics.mjs. Request v3 requires the distinct FINITE_MOTION_DIAGNOSTICS grant and fixed schema hash; v1/v2 reject diagnostic fields. A sublease of at most20seconds sits inside the original window, independently bounded to400server/400client/1200frame records,1MiB and64queued writes. No images, camera/input or gameplay mutations. Read actual server/client state on its owning thread; no FPS/MSPT inference from interaction counts.

Supplementary evidence/derived/manual-interaction/motion.jsonl and diagnostics-result.json remain separate from canonical MANUAL_INTERACTION events. Verify request/PID/subject/schema hash, file hash, written counts, flush, remaining queue, drops/errors/truncation and missing subjects before analysis. STOP/disconnect/original lease/sublease end collection; no renewal or background recording. Clean manual-event closure does not establish diagnostic success or a jitter cause. Tick-event elapsed time is not an independent whole-server profiler; frame samples are the selected world-render stage, not every possible screen frame.

Diagnostic schema v2 adds startTrigger: READY or SUBJECT_MOTION (default). Only actual consecutive server-END displacement>=0.02 triggers; velocity alone is insufficient. Seed the first sample, retain original deadline, report NOT_TRIGGERED when applicable and record triggeringDisplacement. Use matching installed diagnosticDefaults/schema hash. Rows include a generic Ghast charging cue to correlate movement with attack presentation. See AF0060 for the retained first stationary/PARTIAL native case.
