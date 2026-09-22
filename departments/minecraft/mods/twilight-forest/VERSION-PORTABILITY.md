# Twilight Forest — Version Portability

## Core principle

FRONTIER code is evidence for newer techniques, not proof that the same source compiles on 1.20.1.

## High-value changes already identified

### 1. Bootstrap decomposition

ANCHOR puts config, listeners, registries, custom registries and packet setup largely inside `TwilightForestMod`.

FRONTIER splits lifecycle duties into dedicated component/event classes.

**Backportability:** high. This is mostly software structure and can be recreated on Forge 1.20.1 without needing NeoForge APIs to match exactly.

### 2. Networking direction/type discipline

ANCHOR: central numeric-ID `SimpleChannel` registry.

FRONTIER: typed payload registration with explicit direction.

**Backportability:** high at the design level. Keep Forge SimpleChannel but encode direction/ownership in wrapper registration and tests.

### 3. Biome-driven density architecture

ANCHOR: custom `ChunkGeneratorTwilight` plus terrain-warp package.

FRONTIER: composable DensityFunctions + biome terrain data + per-chunk horizontal cache.

**Backportability:** medium/high conceptually, low for direct copy. Recreate the separation and cache inside 1.20.1 APIs.

### 4. Boss infrastructure

FRONTIER adds `BaseTFBoss` and dedicated custom boss-bar classes.

**Backportability:** high. The abstraction is largely under mod control.

### 5. ASM patch module

FRONTIER contains 25 Java files under `src/asm/java` covering render, worldgen, entity movement/water behavior, multipart sync, map behavior and more.

**Backportability:** case-by-case and high risk. Every transform must be mapped against 1.20.1 bytecode/mappings independently.

### 6. Presentation stack modernization

FRONTIER has more renderer classes and newer custom model/pipeline/special-render systems while model-class count is lower than ANCHOR, indicating substantial API/architecture reshaping rather than simple accumulation.

**Backportability:** concept-by-concept. Do not copy modern renderer APIs into 1.20.1 blindly.

## Source-distribution warning

The public 1.20.1 source history and distributed 4.3.2508 must remain distinct evidence. Upstream issue #2345 includes a developer statement that a fix already existed but apparently had not been uploaded to CurseForge. Therefore later branch state cannot be assumed to equal the distributed JAR.
