# KNEEKURA Bedrock Wither MOD

This is the actual product source tree for the Bedrock Wither deliverable.

Current stage: **standalone prototype with bounded Forge build/GameTest verification**. See [current status](../STATUS.md) and [source-bound evidence](../evidence/gametest-cancellation-2026-10-03.json); direct Bedrock parity and client/Tank acceptance remain open.

Target:
- Minecraft 1.20.1
- Forge 47.2.0 baseline
- Java 17
- mod id: `kneekura_bedrock_wither`

The Forge baseline matches the current KNEEKURA 1.20.1 development profile used by existing MOD work. A later exact-version change must be recorded in product history and verified; do not silently follow "latest".

## Source policy

- no dependency on BEStyleWither;
- no Mixin into vanilla `WitherBoss` in M1;
- vanilla `minecraft:wither` remains untouched;
- Bedrock uncertainty stays parameterized/documented;
- client-only code must remain isolated from dedicated-server classloading.

## Build state

Use Java 17 and Gradle 8.1.1, matching the dedicated workflow:

```sh
gradle build runGameTestServer --no-daemon
```

The current 2026-10-03 isolated cloud run passed build and 23 required GameTests, including healthy/dead save-load, spawn entity-data synchronization and positive-health Forge revival regressions. The project does not track a Gradle wrapper. A local pass is distinct from hosted CI and from current Bedrock behavioral equivalence.
