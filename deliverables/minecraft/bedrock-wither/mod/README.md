# KNEEKURA Bedrock Wither MOD

This is the actual product source tree for the Bedrock Wither deliverable.

Current stage: **source scaffold only — build/runtime not yet accepted**.

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

A Gradle source scaffold is tracked, but a complete wrapper/bootstrap and first real Forge compile are a separate acceptance step. Do not report this directory as buildable until STATUS/evidence records the run.
