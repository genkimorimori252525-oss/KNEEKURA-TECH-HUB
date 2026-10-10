# Bocchium — conservative world-limit face culling for Embeddium

Investigation 2026-10-11 Phase 3B. Source pinned [`MCTeamPotato/Bocchium@57a2e920273422253dde64f2c3d907bca8679afe`](https://github.com/MCTeamPotato/Bocchium/tree/57a2e920273422253dde64f2c3d907bca8679afe), branch `1201`. **19 Git blobs, 3 Java classes**; all three Java source bodies, Forge `mods.toml`, `build.gradle`, Mixin JSON and `gradle.properties` directly read. This is near complete **Java source code-body coverage for this pinned snapshot**, **not** JAR/source or loaded runtime proof.

`gradle.properties` says Minecraft **1.20.1**, Forge dev **47.1.3**, version **1.20.1-0.0.3**. User basename `bocchium-1.20.1-0.0.3.jar` agrees with project version string, but no user JAR bytes/hash or build equivalence. Source [LGPL-3.0](https://github.com/MCTeamPotato/Bocchium/blob/57a2e920273422253dde64f2c3d907bca8679afe/LICENSE). FRONTIER `1211` branch source of MC 1.21.1 separate `bd9934e...`; not ported to 1.20.1.

Categories `RENDERING_CHUNK`, `CULLING_LOD`, `MIXIN_BYTECODE`. Static mechanism confirmed, performance **NOT_RUN**.

## B-01 — face-of-boundary check before generating terrain side

[`BlockOcclusionCacheMixin.java`](https://github.com/MCTeamPotato/Bocchium/blob/57a2e920273422253dde64f2c3d907bca8679afe/src/main/java/com/teampotato/bocchium/mixin/BlockOcclusionCacheMixin.java) intercepts **Embeddium/Sodium `BlockOcclusionCache.shouldDrawSide`** at HEAD, `remap=false`, returns false when `Bocchium.shouldCull(facing,pos.getY())`.

[`Bocchium.java`](https://github.com/MCTeamPotato/Bocchium/blob/57a2e920273422253dde64f2c3d907bca8679afe/src/main/java/com/teampotato/bocchium/Bocchium.java) conditions:
- **Bottom**: `Direction.DOWN` at client dimension `getBottomY()`, if `shouldCullBottomBedrock=true`.
- **Top**: `Direction.UP` at `getTopY()-1` if dimension `hasCeiling()`, if `shouldCullTopBedrock=true`.
- Master switch `enableBocchium=true`; both per-side source defaults true.
- If player client world null, do not cull; other faces are normal vanilla/renderer path.

**Important nuance:** The hook directly checks **direction+height**, not the **block's identity**. Although named Bocchium/bedrock, the inspected method does **not** first assert `state.getBlock()==Blocks.BEDROCK`. At bottom/top height any face satisfying bounds may be suppressed. This is an **exact source fact**, and a correctness risk in custom dimensions or structures at world limits; not a witnessed rendering bug.

Dependencies: `build.gradle` contains compile-time `curse.maven:embeddium-908741:4792094` plus Forge 1.20.1. `mods.toml` in examined source does **not** declare Embeddium as mandatory; `bocchium.mixins.json` requires `BlockOcclusionCacheMixin` (Sodium/Embeddium package). Loaded-runtime if Embeddium absent or version API changed **NOT_RUN**, potential missing-class/injection mismatch.

## B-02 — undeployed-looking UI Mixin

A second [`SodiumGameOptionPagesMixin.java`](https://github.com/MCTeamPotato/Bocchium/blob/57a2e920273422253dde64f2c3d907bca8679afe/src/main/java/com/teampotato/bocchium/mixin/SodiumGameOptionPagesMixin.java) defines GUI toggles for enable/top/bottom, but selected [`bocchium.mixins.json`](https://github.com/MCTeamPotato/Bocchium/blob/57a2e920273422253dde64f2c3d907bca8679afe/src/main/resources/bocchium.mixins.json) has **only `BlockOcclusionCacheMixin` in its `client` list**. Therefore the GUI Mixin **is not registered through this config**. No other Mixin config is present in indexed tree, but bytecode/runtime before asserting final GUI absence remains UNKNOWN. This is a wiring **source observation**, not proof user sees no UI.

## Comparative path

Unlike CullLeaves, does not test leaf/neighbor transparency. Unlike BFRC/EntityCulling, does not do depth/ray cull. It is a **static geometric impossibility** at world bounds and should alter only unreachable external faces if conditions truly safe. Test world minY/topY dimensions with/without ceilings, non-bedrock blocks at limits, caves/void or spectator view, Embeddium/other render pipeline compatibility and chunk rebuild after config changes.

Upstream issue search `cull` returned **zero relevant cases** in this bounded window; no before/after repair diff claimed (see history). No Forge/JAR benchmarks run.
