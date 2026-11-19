# BWR-0006 — volley GameTest assumed an untouched AI state

Date: 2026-10-02  
Origin: OWN_DEVELOPMENT  
State: VERIFIED_FIXED

## Symptom

Forge GameTest run `36992149823` ran 14 tests and failed only:

`centervolleyusesfireratethensevensecondcooldown failed! Target acquisition did not enter PHASE1_BURST`

## Root cause

Basis: DIRECT_OBSERVATION + test-fixture inspection.

The test created a combat-ready boss, then waited two server ticks before manually exercising `BedrockWitherVolleyController`.

During those two ticks the normal entity AI/controllers were free to consume or alter the same high-level combat state. The test then assumed the state was still exactly `PHASE1_REPOSITION`.

That made a controller-unit assertion depend on ambient server AI scheduling.

This is a **test-isolation defect**, not evidence that Bedrock firing semantics are wrong.

## Repair

Immediately before the manual volley-controller step, establish the exact precondition owned by the test:
- native phase = first phase;
- spawn state completed;
- high-level state = `PHASE1_REPOSITION`;
- target assigned.

Then call the controller and assert its transition/cadence deterministically.

The broader fixture was also corrected: all Wither GameTests are assigned distinct batches so bosses with 70-block targeting, explosions and projectiles do not execute concurrently in the same default batch. Controller-test targets may additionally be invulnerable where their survival is a test precondition.

## Verification

Dedicated Forge workflow run `36993986762` (source `c230bd372ca2ee96bc0396e424071d2f4c06cb3a`) completed successfully. The GameTest server ran 14 required tests in isolated batches and reported `All 14 required tests passed :)`.

The log shows every Wither test running in its own named batch, including `bwr_centervolleyusesfireratethensevensecondcooldown`. The previously failing volley controller test passed under isolated state/target conditions.

Workflow: https://github.com/genkimorimori252525-oss/KNEEKURA-TECH-HUB/actions/runs/36993986762

## Lesson

When GameTests manually drive a controller, they must own every state precondition that controller reads. Do not mix ambient entity AI progression with synchronous controller-unit timing unless the purpose is explicitly an integration test.
