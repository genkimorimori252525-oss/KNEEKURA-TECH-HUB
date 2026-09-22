# Twilight Forest — Data / Asset Architecture

Status: **FRONTIER data architecture mapped; binary/source asset inventory complete**

Source snapshot: `TeamTwilight/twilightforest@793c4d4c7b0a2892f702cbb9a8d751fbe7218828`.

This report separates three things that are easy to confuse:

1. hand-authored runtime assets;
2. generated Minecraft data/assets committed to the repository;
3. custom Twilight Forest registry data consumed by Mod code.

The repository-wide file inventory remains in `DATA-ASSET-CATALOG.json` and `inventory/frontier-793c4d4c-files.json`.

## 1. Asset production model

The FRONTIER build defines a dedicated data source set and a `clientData` run that writes into:

`src/generated/resources/`

while using:

`src/main/resources/`

as existing input.

This means generated resources are first-class build inputs rather than disposable build-directory output. The repository records the generated result, allowing review of the exact data consumed by the game.

### Reusable pattern

For a large data-driven Mod:

```text
Java data generator
      ↓
versioned generated resources
      ↓
runtime registries / recipes / loot / models / tags
```

This makes code changes and their resulting data diff reviewable together.

## 2. Hand-authored client assets

Under `src/main/resources/assets/twilightforest/` the pinned FRONTIER contains at least:

| Category | Count |
|---|---:|
| textures | 1,241 |
| sounds (.ogg) | 229 |
| hand-authored model JSON | 155 |
| language files | 100 |
| shader files | 2 |

These are not interchangeable with generated model definitions. Textures and sounds remain source media, while much of the model/blockstate/item-description layer is generated.

## 3. Generated client assets

Under `src/generated/resources/assets/twilightforest/`:

| Category | Count |
|---|---:|
| models | 1,618 |
| item definitions | 663 |
| blockstates | 528 |
| tips | 82 |
| particles | 28 |
| equipment definitions | 9 |
| generated lang files | 2 |
| atlases | 1 |
| generated sounds.json | 1 |

### Architecture finding

The visual pipeline is split:

```text
hand-authored texture/media
        +
generated block/item/model metadata
        +
Java entity renderer/model/state code
        ↓
runtime presentation
```

This is why texture analysis alone cannot explain the visual system. The entity side is mapped separately in `ENTITY-RENDER-DEPENDENCIES.json`.

## 4. Generated gameplay data

The FRONTIER generated data tree contains:

| Data category | Count |
|---|---:|
| loot tables | 606 |
| advancements | 530 |
| recipes | 529 |
| worldgen | 306 |
| tags | 155 |
| damage types | 40 |
| banner patterns | 9 |
| jukebox songs | 9 |
| trim materials | 6 |
| data maps | 5 |
| enchantments | 4 |
| loot modifiers | 2 |
| dimension | 1 |
| dimension type | 1 |

There are also 13 hand-authored recipes under the main resource tree.

### Reusable lesson

Large content volume is handled primarily as **generated declarative data**, leaving Java to define algorithms, codecs, registration, and special behavior.

## 5. Structure templates

The main data tree contains **273 structure-template files** under:

`src/main/resources/data/twilightforest/structure/`

These are distinct from the generated structure/worldgen registry JSON.

This gives a two-layer structure system:

```text
worldgen / Structure registration and placement
                 ↓
template definitions / processors / marker handlers
                 ↓
binary NBT structure templates
```

The code/registry side is mapped in `WORLDGEN.md` and `STRUCTURES.md`.

## 6. Twilight Forest custom registry data

A particularly important FRONTIER design is the custom `twilight/` data namespace under:

`src/generated/resources/data/twilightforest/twilight/`

It contains **290 records** across:

| Custom data family | Count |
|---|---:|
| template_definition | 205 |
| travellers_modifiers | 24 |
| stalactites | 19 |
| restrictions | 9 |
| wood_palettes | 8 |
| structure_speleothem_settings | 6 |
| magic_paintings | 5 |
| tiny_bird_variant | 4 |
| dwarf_rabbit_variant | 3 |
| biome_layer_stack | 2 |
| chunk_blanket_processors | 2 |
| biome_terrain_data | 1 |
| quests | 1 |
| template_marker_handler_list | 1 |

These correspond directly to custom/datapack registries declared in `TFRegistries.java` and related initialization classes.

### Architecture finding

Twilight Forest treats many systems that could have been hard-coded Java enums as **data-selected behavior/configuration**.

Examples include:

- biome layer composition;
- terrain parameters;
- structure template definitions;
- structure marker behavior;
- progression restrictions;
- Traveller gear modifiers;
- visual/entity variants;
- wood palettes.

That is a high-value design for KNEEKURA because the same Java machinery can host many authored variants.

## 7. Other custom datasets

The tree also includes:

- `museumexhibits`: 67 records;
- main-resource functions: 6;
- Curios data: 1.

These are system-specific data surfaces and should remain separate from vanilla-standard data categories in tooling.

## 8. Consumer mapping

Current evidence supports the following major consumption paths:

```text
generated recipe JSON
  → recipe serializers/types
  → crafting / uncrafting / special gameplay

generated loot tables + modifiers
  → TFLoot registration
  → entities / blocks / structures / boss buffered loot

generated worldgen JSON
  → registries / density / biome / structures
  → Twilight dimension generation

generated twilight/* custom data
  → TFRegistries datapack registries
  → structure / terrain / restriction / variant systems

generated models/blockstates/items
  + main textures
  → client model baking / renderer layer
```

`CUSTOM-DATA-GRAPH.json` now connects **all 290 custom `twilight/*` records** to their family, immutable upstream blob SHA, loading mode, decoding codec(s), and primary runtime consumer class(es). It also distinguishes datapack registries from JSON reload-listener datasets, which is essential for backporting.

## 9. ANCHOR portability

The 1.20.1 ANCHOR also contains substantial generated resources, but registry APIs and data formats differ.

Backport rule:

- preserve the data-driven **concept**;
- map codecs/registry bootstrap onto 1.20.1 Forge;
- regenerate data using ANCHOR-compatible serializers;
- do not copy FRONTIER JSON blindly when Minecraft registry schemas changed.

## 10. Record-level graph status

`CUSTOM-DATA-GRAPH.json` covers 14 custom families / 290 records:

- 205 template definitions;
- 24 Traveller modifiers;
- 19 stalactite/speleothem records;
- 9 restrictions;
- 8 wood palettes;
- 6 structure speleothem settings;
- 5 magic paintings;
- 4 tiny-bird variants;
- 3 dwarf-rabbit variants;
- 2 biome-layer stacks;
- 2 chunk blanket processors;
- 1 biome terrain dataset;
- 1 quest dataset;
- 1 template-marker handler list.

Each record retains its source path and Git blob SHA. Family metadata records whether it is decoded through a datapack registry or a reload listener, the codec boundary, and primary consumer classes.

## 11. Remaining data work

For whole-target completion:

1. ANCHOR↔FRONTIER schema delta for important worldgen/custom data;
2. distributed 4.3.2508 JAR resource hash comparison.
