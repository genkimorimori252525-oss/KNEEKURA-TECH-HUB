# Twilight Forest — ASM / Runtime Patch Surface

Status: **FRONTIER transformer registry mapped**

Source snapshot: `TeamTwilight/twilightforest@793c4d4c7b0a2892f702cbb9a8d751fbe7218828`.

## Module

FRONTIER contains a dedicated ASM source set with **25 Java files**.

Registration root:

- `src/asm/java/twilightforest/asm/TFCoreMod.java`
- blob `20b6f8805b27376b5704e0f886ee7fb85b199e58`

`TFCoreMod` implements NeoForge `ClassProcessorProvider` and registers the transformations explicitly.

## Patch categories

### Rendering / equipment

- armor visibility rendering;
- hide player/head presentation under trophy-related rendering.

### World generation

- inject custom terrain Beardifier behavior into `NoiseBasedChunkGenerator.createNoiseChunk`;
- add chunk blanketing around surface-generation tasks;
- load conquered structure state.

### Entity physics / movement

- water walking;
- water collision;
- water sprint;
- pathfinder behavior when unrestricted by leash;
- movement speed/jump factor;
- stuck-state reset.

### Blocks / physics

- slime-block momentum;
- slime-block bounce;
- unrestricted friction;
- mushroom soil survivability;
- snowlogged/grass snowy behavior.

### Map / UI-supporting behavior

- nearest non-random-spread map structure resolution;
- map updates while using goggles.

### Multipart entity synchronization

- inject multipart dirty-data synchronization into vanilla `ServerEntity.sendDirtyEntityData`.

### Other

- foliage color resolver;
- rain-at checks;
- leash-knot survival;
- movement food exhaustion.

## Why this matters

These are **semantic extension points that normal events/APIs did not satisfy**.

The project does not replace Minecraft wholesale. It uses narrow processors targeted at exact classes/methods to bridge missing hooks.

## High-value example — worldgen

`InjectCustomTerrainBeardifierDuringCreateNoiseChunkTransformer` targets:

```text
NoiseBasedChunkGenerator.createNoiseChunk(...)
```

and inserts a call to Twilight Forest `WorldgenHooks.gatherCustomTerrain` around vanilla Beardifier creation.

This is a strong example of:

```text
preserve vanilla pipeline
+ intercept one semantic boundary
+ provide Mod-specific extension
```

## High-value example — multipart sync

`SendDirtyEntityDataTransformer` targets:

```text
ServerEntity.sendDirtyEntityData()
```

and routes the entity through a Twilight Forest multipart hook before vanilla synchronization continues.

## 1.20.1 portability warning

ASM is the least source-portable part of the project.

For every transformer, backport work must re-derive:

- target class;
- target method descriptor;
- mappings/names;
- insertion instruction;
- local-variable assumptions;
- vanilla semantics before/after insertion.

No FRONTIER transformer should be copied into 1.20.1 without bytecode-level revalidation.

## Reusable design rule

Treat runtime patches as explicit, named compatibility modules with:

- one semantic purpose;
- one bounded target;
- a plain-Java hook method containing most real logic;
- minimal bytecode manipulation;
- regression evidence.

That architecture is worth copying even when every concrete transform must be rewritten.
