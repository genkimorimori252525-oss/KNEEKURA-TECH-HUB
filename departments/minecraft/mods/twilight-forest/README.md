# The Twilight Forest — Analysis Workspace

## Queue

- Priority: **1**
- Target: The Twilight Forest
- Kind: content/gameplay Mod
- Status: **QUEUED**

## Required tracks

### ANCHOR
- Minecraft: **1.20.1**
- Loader: **Forge**
- Source Snapshot: **NOT_PINNED**

### FRONTIER
- Target: latest useful upstream release/branch at analysis time
- Minecraft / Loader: **NOT_PINNED**
- Source Snapshot: **NOT_PINNED**

Both tracks must remain separate. VERSION-PORTABILITY.md will explain which newer implementation ideas can be reconstructed safely for 1.20.1 Forge.

## Planned full analysis

- bootstrap / loader registration / lifecycle
- entity and boss AI
- navigation / targeting / state machines
- progression systems
- dimensions / biomes / structures / world generation
- blocks / items / block entities
- networking and synchronization
- rendering / models / animation
- textures, atlases, sprites, UV references
- particles / shaders / special render paths
- sounds / music
- recipes / loot / tags / advancements / language
- compatibility / integrations / patch surfaces
- performance-sensitive code
- cross-version portability
- license and provenance

Exact ANCHOR and FRONTIER SourceSnapshots must be pinned separately before reproducible implementation claims are accepted.
