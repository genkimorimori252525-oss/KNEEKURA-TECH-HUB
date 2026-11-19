# BWR-0004 — zero spawn frames skipped Bedrock spawn sequence

Date: 2026-10-02  
Origin: OWN_DEVELOPMENT  
State: VERIFIED_FIXED

## Symptom

Forge GameTest run `36991331495` compiled successfully but failed:

`officialentitysurface failed! Expected initial reconstruction state SPAWN_SEQUENCE`

The state machine had been changed so `SPAWN_SEQUENCE` ends whenever `mSpawningFrames <= 0`, but no modern Bedrock spawn controller initialized `mSpawningFrames`.

Result: the boss entered `PHASE1_REPOSITION` immediately after its first server AI tick.

## Root cause

Basis: DIRECT_OBSERVATION + evidence gap.

The runtime-shaped field existed, but the product intentionally left the spawn duration unresolved. Later, the state machine consumed that unresolved field as if zero were an accepted runtime value.

This conflated:
- "unknown/uninitialized"
with
- "spawn sequence complete".

## New evidence

Current gameplay documentation states that a newly summoned Wither is invulnerable for about **11 seconds**, i.e. 220 game ticks, then creates its spawn explosion.

Historical Bedrock native code used 200 spawn/invulnerability ticks.

Current BDS 1.26.51.1 still exposes `mSpawningFrames` and pre-AI gating.

## Repair plan

Add a dedicated spawn controller that:
- initializes modern target duration to 220 ticks;
- keeps `SPAWN_SEQUENCE` active while the counter is positive;
- blocks normal combat damage/AI during the sequence;
- performs the accepted spawn explosion at completion;
- enters `PHASE1_REPOSITION` exactly once;
- isolates 220 as a modern-observation value rather than rewriting historical evidence.

## Verification

Dedicated Forge workflow run `36993986762` (source `c230bd372ca2ee96bc0396e424071d2f4c06cb3a`) completed successfully. The GameTest server ran 14 required tests in isolated batches and reported `All 14 required tests passed :)`.

The isolated `spawnSequenceUsesModern220TickContract` batch passed, including:
- new entity starts in the modern 220-tick spawn countdown;
- ordinary damage is rejected during spawn;
- the sequence remains active through tick 219;
- tick 220 exits to `PHASE1_REPOSITION`.

Workflow: https://github.com/genkimorimori252525-oss/KNEEKURA-TECH-HUB/actions/runs/36993986762

## Lesson

A structurally mirrored native field must not default to a gameplay-significant zero when zero has semantic meaning. Unknown values need either an explicit unresolved sentinel or a controller that initializes them before the first consuming tick.
