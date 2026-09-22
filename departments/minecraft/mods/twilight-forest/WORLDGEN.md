# Twilight Forest — World Generation Map

Status: **FRONTIER architecture mapped / ANCHOR portability mapped**

## ANCHOR architecture

The 1.20.1 line is centered around a custom `ChunkGeneratorTwilight` family and terrain-warp implementation.

Key concepts in the ANCHOR tree include:

- custom chunk generator;
- chunk-generator wrapper;
- controlled-spawn cache;
- custom terrain warp/interpolation package;
- direct integration of landmarks, biome source and structures.

This is a comparatively self-contained generator architecture.

## FRONTIER architecture

The current tree no longer centers the dimension around the old custom chunk-generator class. Instead, terrain behavior is expressed through composable DensityFunctions and datapack-backed biome terrain data.

Important pieces:

- `TerrainDensityRouter`
- `NoiseDensityRouter`
- `BiomeDensitySource`
- custom density helper functions;
- registry `BIOME_TERRAIN_DATA`;
- custom biome stack/layer registries;
- structure-aware worldgen hooks.

### TerrainDensityRouter

Evidence:

- `src/main/java/twilightforest/world/components/chunkgenerators/TerrainDensityRouter.java`
- blob `38f2f97a72fc6d1f547c816dec829562c0db0d95`

It retrieves per-biome terrain information and converts it to density values.

During `mapAll`, it replaces itself with a chunk-scoped cached variant. That cache stores one terrain-column result for every X/Z position in a chunk:

```text
16 x 16 = 256 horizontal cache slots
```

The Y coordinate is intentionally not part of this cache key, so the source comments warn that the sampled biome-density calculation must not depend on vertical position.

### NoiseDensityRouter

Evidence:

- `src/main/java/twilightforest/world/components/chunkgenerators/NoiseDensityRouter.java`
- blob `11ffad75c9445efbc8586bf8f9de4f4c82dfc50c`

It uses the same per-biome source and the same 16×16 per-chunk cache concept for terrain scale/noise influence.

## Structure registry

Evidence:

- `src/main/java/twilightforest/init/TFStructures.java`
- blob `c9ab851b0118c1775c3b1d2362de4a9c5180530d`

The pinned FRONTIER snapshot declares **25** structure ResourceKeys, but declaration and active generation are kept separate:

- **21** keys are actually bootstrapped and have generated `worldgen/structure` JSON;
- **4** — `quest_island`, `druid_grove`, `floating_ruins`, and `world_tree` — are declaration-only in this snapshot and are not counted as active structures;
- **19** active structures/structure families have their own generated Structure Set;
- `mushroom_tower` is active/generated but has no own generated Structure Set file in this snapshot.

This avoids treating a future/historical registry key as evidence that content currently enters world generation.

## ASM integration with vanilla noise generation

The FRONTIER ASM module patches vanilla `NoiseBasedChunkGenerator.createNoiseChunk`.

Transformer:

- `InjectCustomTerrainBeardifierDuringCreateNoiseChunkTransformer`
- blob `f71b359808adfee97436d42f9304566143a1e8ae`

It inserts a call to Twilight Forest worldgen hooks around vanilla Beardifier creation. This lets Twilight Forest contribute custom structure-terrain density without replacing the entire noise generator.

## Chunk-surface hook

Transformer:

- `ChunkStatusTaskTransformer`
- blob `4a9227d016c0d8b50b86a4f19f0ef1512cdf3bf8`

It hooks the vanilla surface-generation task and invokes Twilight Forest chunk blanketing after `buildSurface`.

## Architectural evolution

```text
ANCHOR
custom ChunkGeneratorTwilight
        ↓
large amount of terrain responsibility owned by the Mod

FRONTIER
vanilla NoiseBasedChunkGenerator
        +
custom biome terrain data
        +
custom DensityFunctions
        +
small ASM insertion points
        ↓
Twilight-specific behavior layered into vanilla pipeline
```

## Backport strategy to 1.20.1 Forge

Do not attempt to copy the 26.1 DensityFunction/NeoForge implementation literally.

A safer migration path:

1. keep `ChunkGeneratorTwilight` initially;
2. extract hard-coded biome terrain parameters into independent data/codec objects;
3. introduce a small terrain-density abstraction;
4. cache X/Z biome terrain samples per chunk;
5. move structure-terrain coupling behind one hook/interface;
6. only then consider deeper vanilla-generator integration.

The reusable technology is **separation of terrain policy from the chunk generator**, not a particular modern API call.

## FRONTIER dimension pipeline

The generated dimension data proves the current dimension is layered on the vanilla noise generator:

```text
twilightforest:twilight_forest
        ↓
generator: minecraft:noise
        ↓
biome_source: twilightforest:twilight_biomes
        ↓
terrain_data: twilightforest:biome_grid
        ↓
settings: twilightforest:twilight_noise_gen
        ↓
final_density / preliminary_surface_level
        = twilightforest:forested_terrain
```

### Dimension properties observed

- dimension type height/logical height: **288**
- min Y: **-32**
- coordinate scale: **0.125**
- fixed time: enabled
- skylight: enabled
- custom NeoForge skybox: `twilightforest:renderer`
- custom weather: `twilightforest:weather`

### Noise settings observed

- noise height: **256**
- min Y: **-32**
- sea level: **0**
- aquifers: disabled
- ore veins: disabled
- final density: `twilightforest:forested_terrain`

`TFBiomeProvider` is a custom `BiomeSource` backed by datapack registry `BIOME_TERRAIN_DATA`, so biome selection and terrain-density policy are connected through data instead of living only inside one chunk-generator implementation.

Machine-readable copy: `WORLDGEN-PIPELINE.json`.

## Full FRONTIER structure catalog

See `STRUCTURES.md` and machine-readable `STRUCTURE-CATALOG.json`.

Two placement families are now explicitly mapped:

- **`twilightforest:landmark_grid`** for the landmark/progression lattice;
- **`twilightforest:avoid_landmark_grid`** for ambient structures such as camps, fallen trunks and hollow trees, with spacing/frequency/exclusion rules that keep them from interfering with landmarks.

Underground progression structures such as Labyrinth, Knight Stronghold and Troll Cave use `underground_structures` plus `bury`. Giant House uses `top_layer_modification`; most others use `surface_structures`.

This strengthens the portable design lesson: **gameplay-significant geography and ambient decoration should have separate placement policies even when both use Minecraft's Structure system.**
