# KNEEKURA Bedrock Wither MOD

This is the actual product source tree for the Bedrock Wither deliverable.

Current stage: **source-backed standalone boss implementation**. See [current status](../STATUS.md), [adopted policies](../ADOPTION.md) and [source-completion evidence](../evidence/source-completion-2026-10-03.json). Empirical Bedrock/Tank measurements are not part of the user-selected completion boundary; no measured-parity claim is made.

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

The source-completion generation passes build and 60 required GameTests, including ordinary phase 1 ascent/reposition/volleys, phase 2 firing/charge/recovery, target validity, real projectile impact/liquid/reflection, presentation math, save/load, Forge revival and ordinary reward events. The exact final verification is in the linked receipt and PR81. The project does not track a Gradle wrapper. A local pass is distinct from hosted CI and empirical Bedrock identity.


## Using the standalone entity

Build output is under `build/libs/`. In a compatible Forge 1.20.1 installation, the separate entity can be summoned with:

```mcfunction
/summon kneekura_bedrock_wither:bedrock_wither ~ ~ ~
```

The vanilla Wither summon/build route is not replaced. Use an expendable world for any later user-run gameplay: the boss intentionally destroys terrain. No interactive game or user desktop was run during this code-completion pass.

## Reconstruction policy

The implementation is functional with documented source-derived defaults. Public constants and controller boundaries isolate uncertain historical/Java choices; they no longer require a measured value to be supplied before ordinary combat can run. Source/version qualifications are retained in ADOPTION and STATUS. Java bundled textures and an explicit blue-tint substitute are used instead of redistributing Bedrock texture bytes.
