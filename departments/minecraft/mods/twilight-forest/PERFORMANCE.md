# Twilight Forest — Performance / Hot-Path Notes

Status: **INVENTORIED / hypotheses only unless explicitly evidenced by code structure**

This document does not claim measured performance results yet. It identifies likely hot paths and optimization patterns that need profiling.

## Confirmed optimization pattern: per-chunk terrain cache

`TerrainDensityRouter` and `NoiseDensityRouter` replace configuration instances with chunk-scoped cached variants during noise generation.

Each keeps a 16×16 array of biome terrain samples.

Purpose visible from code structure:

- avoid recomputing the same X/Z terrain source repeatedly for many Y evaluations;
- keep the cache scoped to one noise chunk;
- avoid a global cache lifecycle.

This is a strong reusable pattern for expensive horizontally invariant worldgen functions.

## Areas requiring runtime measurement

### Worldgen

Potentially expensive:

- biome terrain sampling;
- structure density hooks;
- chunk blanketing;
- large structure/template processing;
- custom processors and markers.

### Bosses

Potentially expensive during encounters:

- Hydra multipart updates and collision checks;
- Hydra secondary-target scans;
- block-destruction scans around large multipart hitboxes;
- Naga multipart movement;
- group scans for Knight Phantoms;
- Ur-Ghast trap/location logic.

These are hypotheses from control flow and collection/spatial operations, not benchmark conclusions.

### Rendering

Potentially expensive:

- multipart bosses;
- custom culling bounds;
- special renderers;
- generated/reloaded textures;
- custom model/render pipeline logic.

### Networking

Potential load multipliers:

- multipart dirty-data synchronization;
- map synchronization;
- particle payloads;
- boss/group state.

## Existing cache/lifecycle signals

FRONTIER explicitly includes:

- chunk-local density caches;
- armor cache reload handling;
- texture generation reload handling;
- resource reload listeners.

This suggests the project already distinguishes data lifetime by subsystem rather than using one global cache.

## Measurement plan

When local runtime testing begins, capture separately:

1. startup + class transformation;
2. dimension first-generation latency;
3. steady chunk-generation time;
4. structure-heavy chunk generation;
5. each major boss encounter server tick cost;
6. client frame/render cost per boss;
7. packet rate/bytes during multipart fights;
8. resource reload duration;
9. heap allocation during worldgen and rendering.

Do not promote any “fast/slow” claim before measurements are attached to machine/environment evidence.

## Executable evidence contract

`RUNTIME-EVIDENCE-SPEC.md` now defines the fixed runtime scenarios, environment envelope, output layout, and proof boundary for future ANCHOR/FRONTIER measurements. Static hot-path notes remain hypotheses until those runs exist.
