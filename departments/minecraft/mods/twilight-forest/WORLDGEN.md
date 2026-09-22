# Twilight Forest — World Generation Map

## ANCHOR architecture

The 1.20.1 line registers a custom chunk-generator codec for `ChunkGeneratorTwilight`.

Core implementation is concentrated around:

- `ChunkGeneratorTwilight`;
- `ChunkGeneratorWrapper`;
- `ControlledSpawnsCache`;
- a custom `warp/` package containing blended noise, interpolators, sliders/modifiers and `TFTerrainWarp`.

The generator also integrates landmarks, structures, controlled spawning and biome sourcing.

This is a relatively self-contained custom-generator architecture.

## FRONTIER architecture

The latest tree removes the old `ChunkGeneratorTwilight` / terrain-warp package and instead introduces custom vanilla-compatible DensityFunctions and biome-driven density data.

Important pieces include:

- `TFDensityFunctions`;
- `TerrainDensityRouter`;
- `NoiseDensityRouter`;
- `FocusedDensityFunction`;
- `HollowHillFunction`;
- coordinate min/max functions;
- sqrt/tanh/box-style density helpers;
- `BiomeDensitySource`;
- datapack registry `BIOME_TERRAIN_DATA`.

`TerrainDensityRouter` and `NoiseDensityRouter` sample per-biome terrain data and convert it into density inputs. Both replace themselves during `mapAll` with chunk-scoped cached variants using a 16×16 horizontal cache.

This is a significant architectural improvement candidate: biome-specific terrain logic is moved into composable density functions and data instead of requiring the entire dimension to be controlled by one custom chunk-generator implementation.

## FRONTIER structure expansion

Structure Java grows from 222 to 291 files. Newer systems include:

- hollow-tree structures;
- fallen trunks;
- expanded/reworked Lich tower;
- template marker handlers;
- custom landmark placements;
- progression-wrapped structures;
- controlled spawning structures;
- structure density inputs.

## Backport hypothesis

The **concept** of separating biome terrain parameters from the core generator is highly portable to 1.20.1.

Direct source backport is not assumed because DensityFunction APIs, registries and NeoForge hooks differ. A 1.20.1 implementation could instead:

1. retain `ChunkGeneratorTwilight`;
2. lift biome terrain configuration into data/codec objects;
3. expose a small density-evaluation layer inside the old generator;
4. adopt per-chunk 16×16 horizontal caching;
5. progressively replace hard-coded warp behavior without requiring the 26.1 API wholesale.

This needs implementation-level validation before promotion from hypothesis.
