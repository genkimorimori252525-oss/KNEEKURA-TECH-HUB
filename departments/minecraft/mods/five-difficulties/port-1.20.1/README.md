# Five Difficulties X1 Preservation Port — Minecraft 1.20.1 Forge

Status: **P4 complete — canonical X1 Sakuya Watch / StopWatch are player-usable and their controller presentation compiles on Forge 1.20.1**.

Target:
- Minecraft 1.20.1
- Forge 47.4.6
- Java 17
- private preservation/research use

Fidelity oracle:
- 五つの難題MOD+ ver2.90.1.X1-1.7.10
- Roundabout is only a donor/reference for modern time-stop machinery.

## Build boundary

This directory intentionally keeps the implementation source tree but does not vendor the Forge MDK or Gradle wrapper binaries.

CI/validation overlays:

`port-1.20.1/src`

onto the exact official Forge 1.20.1-47.4.6 MDK used elsewhere by KNEEKURA-TECH-HUB.

This follows the existing Hub validation convention and keeps third-party/build artifacts out of Git history.

## Source split

`src/main/java/dev/kneekura/fivedifficulties/core/**`

Pure Java:
- no Minecraft or Forge imports;
- deterministic legacy shot/laser/pattern contracts;
- Sakuya time-stop policy/state;
- runnable with plain Java 17 regression tests.

`src/main/java/dev/kneekura/fivedifficulties/forge/**`

Forge 1.20.1 boundary:
- @Mod bootstrap;
- DeferredRegister boundary;
- network channel boundary;
- Minecraft Entity/ServerLevel adapters for the pure time-stop core.

Current port still deliberately defers broad content expansion: the 35 spell cards, Master Spark, generalized THShot/laser runtime, most X1 recipes/mobs/items, and all bullet batching remain later gates.

## Validation order

1. compile/run pure Java core regression;
2. compile/package source against exact Forge MDK;
3. only then add real X1 oracle-backed content.

No Minecraft runtime claim is made by a compile-only pass.


## P1 evidence contracts

P1 adds a strict evidence bridge to the earlier exact X1 analysis (PR #93):

- canonical core artifact SHA-256 `6307789d5f2f43b762bcc7d5aa03d67207eaa237fb124447e7ea951aa856e634`;
- red Homing Amulet normal/focus behavior contract;
- Sakuya Watch/StopWatch mode/range/duration contract;
- explicit unresolved fields/categories so missing raw/runtime evidence is never guessed.

These contracts are pure Java and do not yet make the original textures/items/renderers available in-game.


## P2 live preservation path

Canonical X1 was reacquired byte-for-byte and the first live 1.20.1 preservation path is now implemented:

- red Homing Amulet item;
- exact normal/focus fan geometry;
- exact static homing contract;
- X1-style logical collision sweep;
- live EntityType/projectile;
- two-pass legacy-style renderer;
- private SHA-verified original texture overlay.

See:
- `P2-CANONICAL-X1-REACQUISITION.md`
- `P2-HOMING-AMULET-EXACT.md`
- `IMPLEMENTATION-CHECKPOINT-P2.md`

Latest validated Forge compile: GitHub Actions run `37521984099` — SUCCESS.

Next preservation gate is Sakuya time-stop parity, not mass content expansion.


## P3 Sakuya time-domain machinery

Canonical X1 Watch/StopWatch source was re-read directly.

P3 now provides:
- exact X1 40-block AABB field policy;
- source/item-frame/painting/mount exclusions;
- two-tick new-entity grace;
- FULL_STOP and deterministic HALF_SPEED modes;
- synced transient controller entity;
- per-Level controller index;
- ServerLevel entity/passenger tick interception;
- ServerPlayer simulation/input/movement interception;
- ClientLevel tick cancellation;
- same-owner movable-spell callback boundary;
- Mixin packaging checks in exact Forge 47.4.6 CI.

X1 does **not** freeze blocks, fluids, BlockEntities, particles, animated textures, chunks or world day time, so those Roundabout capabilities stay disabled.

Latest validated P3 run: `37527522708` — SUCCESS.

See:
- `P3-SAKUYA-TIMESTOP-EXACT.md`
- `IMPLEMENTATION-CHECKPOINT-P3.md`

Next gate: usable Sakuya Watch/StopWatch items plus bounded Minecraft runtime verification.


## P4 usable Sakuya Watch / StopWatch

P4 connects the P3 time-domain machinery to real player items.

Implemented:
- mode-0 HALF / mode-1 FULL Sakuya Watch state;
- X1 20/48-tick charge behavior;
- creative immediate persistent activation;
- survival limited activation and item consumption;
- fresh mode-0 Watch return after limited Watch finishes;
- immediate disposable StopWatch;
- exact four-part Watch controller model;
- X1 +7°/tick controller spin;
- expanding dark-field mesh and legacy blend contract;
- SHA-verified private asset overlay for Watch / StopWatch item and controller textures.

Latest validated P4 compile/package: GitHub Actions run `37531317629` — SUCCESS.

See:
- `P4-SAKUYA-WATCH-VISUAL-ITEM-EXACT.md`
- `IMPLEMENTATION-CHECKPOINT-P4.md`

Next gate is bounded **runtime** verification of the current Homing + Sakuya vertical slice before broader content expansion.
