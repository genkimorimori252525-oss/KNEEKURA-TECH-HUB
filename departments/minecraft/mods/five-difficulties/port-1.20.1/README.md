# Five Difficulties X1 Preservation Port — Minecraft 1.20.1 Forge

Status: **P0 implementation started**.

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

## P0 source split

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

P0 deliberately does **not** yet contain:
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
