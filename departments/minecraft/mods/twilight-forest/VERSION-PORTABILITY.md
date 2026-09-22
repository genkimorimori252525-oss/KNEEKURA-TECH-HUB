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

## Custom data portability

The custom-data delta is now mapped in `CUSTOM-DATA-PORTABILITY.md` and `CUSTOM-DATA-PORTABILITY.json`.

Key result:

- ANCHOR canonical custom namespace: **21 records / 4 families**;
- FRONTIER: **290 records / 14 families**;
- ANCHOR also has **12 legacy stalactite records** outside the later `twilight/` namespace.

Portability classes:

- **directly portable:** biome layer stack, wood palettes;
- **small schema adaptation:** restrictions;
- **codec extension:** magic paintings;
- **architectural refactor:** stalactite/speleothem data;
- **new isolated data systems:** quests, bird/rabbit variants;
- **new structure authoring systems:** template definitions and marker handlers;
- **worldgen policy backport:** biome terrain data and chunk blanket processors;
- **subsystem rewrite:** Traveller gear modifiers.

The most important rule is that FRONTIER JSON is not itself the technology. The reusable technology is the split:

```text
typed codec → authored data → registry/reload boundary → small runtime consumer
```

For 1.20.1 Forge, preserve that separation while implementing ANCHOR-compatible codecs and hooks.
