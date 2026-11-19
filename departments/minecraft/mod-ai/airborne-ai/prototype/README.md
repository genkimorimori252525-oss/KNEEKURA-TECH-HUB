# Airborne AI Foundation offline prototype

Status: **OFFLINE_CONTRACT_PROTOTYPE / MINECRAFT_RUNTIME_NOT_RUN**.

This directory turns the cross-MOD Airborne AI research into executable, deterministic contracts without touching the active LAB/native observer implementation.

## Why it is separate from LAB

PR #80 is actively changing `departments/minecraft/lab/debug-workspace` and `departments/minecraft/vanilla-ai`. This prototype intentionally lives under `mod-ai/airborne-ai/prototype` so the research can be tested without merging or mutating the native observer line.

## Modules

- `contracts.mjs` — common finite-vector, intent, route-generation, landing-reservation and target-memory contracts.
- `tier-a.mjs` — Hero/large-flyer simulator: direct-first routing, path fallback, stale async-route rejection, validated landing, contact completion, bounded recovery, LOS memory.
- `tier-b.mjs` — Common hostile flyer: cheap direct steering, collision probe, CHASE/CHARGE, bounded recovery.
- `tests/contracts.test.mjs` — shared contract tests.
- `tests/tier-a.test.mjs` — Tier A behavior tests.
- `tests/tier-b.test.mjs` — Tier B behavior tests.
- `tests/failure-regressions.test.mjs` — named regressions derived from Saint's Dragons, Cosy/Fowl, Ice and Fire/Dragon Fix, Book of Dragons and the synthesis invariants.

## Run

From this directory:

```bash
node --test tests/*.test.mjs
```

The prototype uses only Node.js ESM built-ins and `node:test`.

## What this proves

The offline suite can prove deterministic contract behavior for:

- rejection of NaN/Infinity movement inputs;
- self-target rejection;
- altitude clamping before route/steering commands;
- direct route preference and path fallback;
- stale route-generation rejection;
- landing support validation, revalidation, TTL and contact-required completion;
- bounded recovery/retry;
- bounded LOS SEARCH/reacquire memory;
- Tier B cheap collision-probe recovery;
- zero-length vectors remaining finite.

## What this does not prove

It does **not** prove Minecraft/Forge integration, real `AABB`/voxel collision correctness, real `FlyingPathNavigation`, async executor behavior, actual entity synchronization, TPS cost, animation, multiplayer behavior, or real landing contact.

Those belong to a later LAB adapter/runtime acceptance. The intended next integration maps prototype fields to native evidence rather than replacing PR #80:

- `airState` / `combatState` -> decision state;
- `routeGeneration` / `routeMode` -> path/decision evidence;
- `lastReason` -> bounded reason code;
- `landingId` -> landing candidate/reservation observation;
- `targetVisible` / target memory status -> perception/LOS evidence;
- `recoveryAttempts` -> movement recovery diagnostics.
