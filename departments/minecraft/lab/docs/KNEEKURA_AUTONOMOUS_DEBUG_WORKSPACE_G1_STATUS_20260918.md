# KNEEKURA Autonomous Debug Workspace v1 — G1 Status

Date: 2026-09-18 JST

Primary plan:
- docs/KNEEKURA_AUTONOMOUS_DEBUG_WORKSPACE_V1_PLAN.md
- docs/KNEEKURA_AUTONOMOUS_DEBUG_WORKSPACE_G0_INVENTORY.md

## Status

- G0 Asset Inventory: COMPLETE
- G1 Debug Launch implementation: CODE COMPLETE CANDIDATE
- G1 real-machine acceptance: PENDING

Do not call G1 fully complete until the real Minecraft development workspace passes the local smoke acceptance.

## Implemented G1 boundary

The new path is independent from the legacy Web Viewer launcher:

    KNEEKURA-LAB/debug-workspace
        -> registered real Forge development workspace
        -> runClient
        -> dedicated Debug World
        -> LAB-owned Forge bridge
        -> READY manifest
        -> Supervisor acceptance

The live Viewer is not part of G1.

## Supervisor

Implemented:

- external workspace registration
- dedicated runtime root
- debugSessionId
- runId
- processEpoch
- per-run handshake nonce
- planned runSnapshotId and immutable RunSnapshot
- startup source/observer fingerprint drift fencing
- process log isolation
- current.json durable state
- launcher PID tracking
- actual runtime PID tracking
- process ownership fencing by PID + start time + command hint
- stale PID / PID reuse rejection
- double-start refusal
- safe stop
- status reconciliation
- restart after clean stop

Possible reconciled states include:

- DEBUG_READY
- STALE_NOT_RUNNING
- OWNERSHIP_LOST
- STOP_REFUSED_UNVERIFIED
- STOPPED

## READY acceptance

The Supervisor requires:

- protocolVersion = KNEEKURA_DEBUG_READY_V1
- matching debugSessionId
- matching runId
- matching Debug World name
- matching processEpoch
- matching handshake nonce
- positive runtime PID
- probeHandshake = true
- debugWorldReady = true
- runtimeAttested = true
- valid ordered startup milestones
- runtime process command hint
- OS-level PID/start-time/command re-attestation

A stale READY file cannot make a newer run look healthy.

## Runtime attestation

The Forge bridge currently reports:

- Minecraft version
- Forge version
- Java version
- topology
- loaded mods
- Probe class SHA-256
- runtime process command hint
- runtime PID
- actual JVM start time

The Probe class hash is calculated from the loaded class bytes rather than only from a source path.

## Debug World gate

G1 proves only:

- expected singleplayer Debug World was joined
- integrated server exists
- client player exists
- world identity matches the configured world name
- the state remains stable for a short gate
- runtime identity was attested

G1 does NOT claim that the future Arena baseline is clean.

Arena geometry, mutation bounds, reset completeness and baseline fingerprint belong to G3.

## T0-T8 startup timeline

Measured contract:

- T0_RESTART_REQUESTED
- T1_BUILD_COMPLETE
- T2_JVM_STARTED
- T3_FORGE_INITIALIZED
- T4_CLIENT_WORLD_AVAILABLE
- T5_PLAYER_JOINED
- T6_PROBE_READY
- T7_DEBUG_WORLD_READY
- T8_DEBUG_READY

T1 is emitted by the real Forge Gradle workspace immediately before runClient begins, after its dependencies have completed.

T2 comes from the actual JVM runtime start time.

T3 comes from FMLClientSetupEvent.

T4 is deliberately named CLIENT_WORLD_AVAILABLE because that is what is directly observed.

Use:

    npm run debug:timeline

to obtain per-stage and total startup timing.

## One-command acceptance

Use:

    npm run debug:smoke

The smoke command performs:

1. doctor
2. launch
3. DEBUG_READY wait
4. T0-T8 completeness check
5. live status re-attestation
6. Probe evidence flush/ACK
7. safe stop
8. evidence finalization

The smoke must exit 0 before G1 is marked complete.

## reimu-mod integration

The current executable target is:

    genkimorimori252525-oss/reimu-mod

Its normal Forge runClient remains the real Minecraft execution path.

Debug-only integration is conditional on KNEEKURA_DEBUG_ENABLED.

The LAB Forge bridge is placed in a dedicated kneekuraDebug source set so debug classes do not leak into normal main output or a later normal jar.

The debug launch also uses Quick Play to enter the configured singleplayer Debug World directly.

## Existing-world preflight

For the current reimu-mod profile:

    gameDir = run/client_a
    saves/<worldName> must exist

debug:doctor checks the world before launch.

This avoids spending minutes on a READY timeout when the configured Debug World does not exist.

First-time automatic world creation is intentionally not mixed into the G1 launch contract yet.

## CI validation status on 2026-09-18

GitHub Actions is now producing usable step and log evidence on the self-hosted Windows KNEEKURA runner.

A previously hidden Windows process-attestation bug was exposed by CI: the generated PowerShell script joined object-literal lines with semicolons and produced invalid `[pscustomobject]@{; ... }` syntax. Run `35349158716` reached the autonomous debug workspace test and failed specifically on this parser error while the Java READY contract, packet snapshot tests, and YSM probe tests had already passed.

The process inspection script was corrected to use real newlines. On later run `35349932054`, the `Test autonomous debug workspace supervisor` step passed, proving the portable Supervisor/fake-target lifecycle through runtime PID attestation.

That workflow still concluded failure for a separate legacy SimLab reason: three renderpack symlink-security tests could not create Windows symbolic links and failed with `EPERM`. This is runner privilege/capability noise, not evidence of a Debug Workspace failure.

Therefore GitHub CI is now useful validation evidence for the portable contracts, but it is still not a substitute for the required real Forge/Minecraft smoke acceptance.
## Remaining G1 acceptance

Required on the actual Windows development machine:

1. create/copy debug-workspace/config.local.json from the reimu-mod profile
2. set workspaceDir to the local reimu-mod checkout
3. ensure run/client_a/saves/KNEEKURA_DEBUG_WORLD exists
4. run npm run debug:doctor
5. run npm run debug:smoke
6. record debug:timeline result
7. verify normal non-debug runClient/build still excludes the LAB debug source set

After those pass, G1 can be marked COMPLETE. G2 infrastructure implementation has already begun in parallel, but G2 acceptance still requires real Forge/Minecraft evidence.
