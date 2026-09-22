# Twilight Forest Runtime Evidence Specification v1

Static architecture analysis is intentionally separate from runtime performance claims.

## Purpose

Measure the ANCHOR and FRONTIER systems under reproducible scenarios without turning code-reading hypotheses into unsupported “fast/slow” claims.

## Required environment record

Every run must capture:

- Minecraft version
- loader + exact loader version
- Twilight Forest artifact SHA-256 / source commit
- Java vendor/version
- JVM arguments
- CPU
- RAM
- GPU + driver for client rendering runs
- OS
- render distance / simulation distance
- allocated heap
- world seed
- installed Mods
- profiler/tool version

A result without this environment envelope is not comparable evidence.

## Scenario set

### R1 — startup

Measure:

- process start → Mod construction
- Mod construction → registry/load completion
- load completion → title screen / dedicated-server ready
- class transformation / ASM time when observable

### R2 — first Twilight dimension entry

Fixed seed and portal location.

Capture:

- portal transition latency
- first required chunk generation
- server tick spikes
- allocations
- generated structure activity

### R3 — steady chunk generation

Generate a fixed coordinate list twice:

1. cold/no generated chunks
2. warm/revisited

Record per-chunk timing distribution, not only average.

### R4 — structure-heavy generation

Use fixed coordinates intersecting representative structure families:

- Lich Tower
- Hydra Lair
- Dark Tower
- Aurora Palace
- Knight Stronghold
- Hollow Hill

Separate template processing from general terrain where instrumentation allows.

### R5 — boss server tick

One isolated encounter each:

- Naga
- Lich
- Hydra
- Ur-Ghast
- Snow Queen
- Alpha Yeti
- Knight Phantoms
- Minoshroom

Capture tick time and allocations through idle, active combat and death/loot phases.

### R6 — multipart stress

Hydra + Naga specifically.

Capture:

- multipart update cost
- collision/block-destruction cost
- dirty synchronized data
- packet count/bytes

### R7 — client rendering

Fixed camera, resolution and graphics settings.

Capture each boss separately plus a baseline empty scene:

- frame time
- render-thread CPU
- GPU frame time where available
- draw/submit hot spots
- allocation

### R8 — networking

Record packet rate/bytes during:

- Hydra fight
- Knight Phantom group fight
- Magic/Maze map synchronization
- particle-heavy event

Use the existing `PACKET-MAP.json` as the expected protocol surface.

### R9 — resource reload

Measure reload duration and allocation for:

- custom `twilight/*` data
- textures/models
- reload-listener datasets such as quests, stalactites and template definitions

## Acceptance discipline

Do not collapse the evidence into one “performance score”.

Store:

- distributions
- maxima/spikes
- scenario context
- profiler traces
- exact machine/environment
- observed regressions
- uncertainty

## Static hypotheses to test

Current code inspection suggests these candidates deserve measurement:

- 16×16 chunk-local terrain caches should reduce repeated horizontal terrain-policy work;
- Hydra multipart state/collision and block scans may dominate some encounter ticks;
- Knight Phantom group scans/formation coordination may scale with group activity;
- Ur-Ghast trap/location logic may create encounter-specific spikes;
- chunk blanketing and template-marker processing may add structure/worldgen costs;
- multipart synchronization and particle payloads may amplify network traffic.

These remain hypotheses until runtime evidence exists.

## Output contract

Each execution should produce:

```text
runtime/<track>/<run-id>/
  environment.json
  scenario.json
  metrics.json
  profiler/
  logs/
  evidence-summary.md
```

Raw large profiler captures should remain local/artifact storage. TECH HUB should commit compact manifests, hashes and derived evidence.
