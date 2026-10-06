# Five Difficulties X1 Preservation Port — Minecraft 1.20.1 Forge

Status: **P1 evidence-backed behavior-contract implementation in progress**.

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

## P1 source split

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

P1 deliberately does **not** yet contain:
- original X1 textures/assets;
- the 35 spell cards;
- Master Spark;
- real projectile entities/renderers;
- Mixin tick cancellation;
- X1 recipes/mobs/items;
- any optimization/virtual-bullet backend.

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
