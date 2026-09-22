# Twilight Forest — Access Transformer Portability Matrix

Source: `src/main/resources/META-INF/accesstransformer.cfg`

| Track | AT entries | Target classes |
|---|---:|---:|
| ANCHOR 1.20.1 / Forge | 79 | 50 |
| FRONTIER 26.1.2 / NeoForge | 124 | 81 |

Class-level overlap:

- common target classes: **33**
- ANCHOR-only classes: **17**
- FRONTIER-only classes: **48**

## What this means

The FRONTIER AT file is not a drop-in upgrade for 1.20.1. The internal boundaries have moved.

A clear worldgen example:

```text
ANCHOR
NoiseBasedChunkGenerator
BlendedNoise
Heightmap
ChunkGenerator

        ↓ API/internal evolution

FRONTIER
Beardifier
ChunkStatus
Structure
SinglePoolElement
...
```

Likewise, FRONTIER opens newer client/render surfaces such as `EntityRenderDispatcher`, `HumanoidArmorLayer`, `ItemStackRenderState`, model-provider collectors and boss-event internals.

## Stable class anchors

Some semantic areas remain visible in both tracks:

- `GoalSelector`
- `MoveControl`
- `BaseSpawner`
- `Biome`
- `StructurePiece`
- `StructureStart`
- `MapItemSavedData`
- `LootTable`
- `LevelRenderer`

Even for these, member names/descriptors must be revalidated against 1.20.1 mappings.

## Backport rule

Never copy an AT line because the FRONTIER has it.

Use:

```text
semantic requirement
   ↓
equivalent 1.20.1 class/member
   ↓
is access actually insufficient?
   ↓
smallest ANCHOR AT
   ↓
regression evidence
```

This matrix is complementary to `ASM-PATCHES.md`: AT widens access, while FRONTIER ASM processors alter behavior at exact bytecode boundaries.

Machine-readable detail: `ACCESS-TRANSFORMER-PORTABILITY.json`.
