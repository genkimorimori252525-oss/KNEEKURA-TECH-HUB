# Twilight Forest — Custom Data Portability Map

Status: **ANCHOR ↔ FRONTIER custom-data architecture compared**

## Snapshots

- ANCHOR source candidate: `TeamTwilight/twilightforest@a7dd8f13c653e137f977f5ffaa870fcb20fc1625`
  - Minecraft 1.20.1
  - Forge line
  - strongest public-source candidate for distributed 4.3.2508, but binary identity is still unproven
- FRONTIER: `TeamTwilight/twilightforest@793c4d4c7b0a2892f702cbb9a8d751fbe7218828`
  - Minecraft 26.1.2
  - NeoForge
  - Mod line 4.9

This document answers one question: **which FRONTIER data-driven technologies can be reconstructed safely for the 1.20.1 Forge ANCHOR?**

## 1. Scale change

Under the canonical custom-data namespace:

`src/generated/resources/data/twilightforest/twilight/`

the ANCHOR has **21 records across 4 families**:

- biome_layer_stack: 2
- magic_paintings: 2
- restrictions: 9
- wood_palettes: 8

The FRONTIER has **290 records across 14 families**.

ANCHOR additionally has **12 old stalactite records** under the older top-level path:

`data/twilightforest/stalactites/`

so those are treated as an architectural predecessor rather than as a missing family.

## 2. Stable design kernels

### biome_layer_stack — DIRECTLY PORTABLE

Both tracks contain the exact same two record paths. The inspected `random_forest_biomes.json` has the **same Git blob SHA** in both snapshots.

The codec design is also structurally unchanged:

`layer_type -> registered BiomeLayerType codec -> nested BiomeLayerFactory tree`

The registry key moved under the consolidated `TFRegistries.Keys` surface, but the concept and serialized data survive.

**Backport action:** keep the ANCHOR implementation. Do not replace it with FRONTIER code merely because the package/registry organization changed.

### wood_palettes — DIRECTLY PORTABLE

All eight Twilight wood-palette JSON records are shared. The inspected `twilight_oak.json` has the **same Git blob SHA** in both snapshots.

The `WoodPalette.CODEC` fields are unchanged:

- planks
- stairs
- slab
- button
- fence
- gate
- plate
- banister

**Backport action:** treat this as a proven cross-version stable abstraction. New structure systems can reuse the ANCHOR palette codec and processor without importing modern loader APIs.

## 3. Stable concept with API/schema adaptation

### restrictions — PORTABLE AFTER SMALL ADAPTATION

All nine restriction record IDs exist in both tracks.

Core fields remain:

- `structure_key`
- `enforcement`
- `multiplier`
- `locked_biome_toast`
- `advancements`

The inspected `swamp.json` differs mainly because ANCHOR serializes an ItemStack with an explicit `Count: 1`, while FRONTIER uses `ItemStackTemplate` and only stores the item ID.

The Java codec likewise changed from ANCHOR `ItemStack.CODEC` to FRONTIER `ItemStackTemplate.CODEC`.

**Backport action:** preserve ANCHOR's `ItemStack.CODEC` representation. FRONTIER progression policy can be translated into the old schema without redesigning the whole restriction system.

### magic_paintings — CONCEPT PORTABLE, SCHEMA EXTENSION REQUIRED

The two ANCHOR painting IDs, `darkness` and `lucid_lands`, remain in FRONTIER, and FRONTIER adds three more variants.

The ANCHOR codec contains:

- width
- height
- layers
- layer path
- optional parallax
- optional opacity modifier
- fullbright

FRONTIER extends the same concept with:

- title
- author
- back_texture
- local_lighting
- opacity min/max
- optional from/to range
- item-trigger sets
- mob-effect-category triggers
- additional parallax/opacity behavior

This is not a loader-only migration: the **data model itself evolved**.

**Backport action:** extend the 1.20.1 codec incrementally. Keep old fields valid with defaults, then add only FRONTIER capabilities needed by KNEEKURA. Do not copy FRONTIER JSON before the ANCHOR codec understands those fields.

## 4. Stalactites / speleothems — REFACTOR PORTABLE, NOT FILE-COPY PORTABLE

ANCHOR uses an older reload-listener dataset under:

`data/twilightforest/stalactites/`

It has:

- 9 ore/material entry files;
- 3 hollow-hill configuration files.

An ANCHOR hill config is a relatively small list of referenced stalactites.

FRONTIER splits the responsibility into two layers.

### Layer A — reloadable variety data

`twilight/stalactites/`

The current `large_hollow_hill` record separates:

- base_stalactites
- ore_stalactites
- stalagmites
- ore_chance
- stalactite_chance
- stalagmite_chance
- type
- replace

Individual stalactite entries also changed representation. For example, ANCHOR's diamond entry uses a `blocks` weighted list, while FRONTIER uses the more general `ores` field accepted by `Stalactite.CODEC`.

### Layer B — structure placement policy

`twilight/structure_speleothem_settings/`

FRONTIER adds a separate per-structure registry containing the triangular lattice placement parameters.

This is a meaningful architectural separation:

```text
material/variety selection
        ≠
structure placement lattice
```

**Backport action:** port the separation of concerns, not the modern API. The 1.20.1 reload listener can be extended to load variety data, while a second ANCHOR-compatible codec/config object owns lattice/placement settings.

## 5. FRONTIER-only data-driven systems

The following families have no equivalent records in the ANCHOR custom namespace.

| Family | Records | Portability class | 1.20.1 strategy |
|---|---:|---|---|
| biome_terrain_data | 1 | concept reusable / worldgen rewrite | Feed extracted terrain policy into `ChunkGeneratorTwilight` first; do not copy modern DensityFunction APIs. |
| chunk_blanket_processors | 2 | portable behind hook | Add an ANCHOR post-surface processor interface/hook, then decode processor configs. |
| dwarf_rabbit_variant | 3 | easy isolated backport | Add registry/reload-backed variant records and keep entity sync/persistence separate. |
| quests | 1 | easy reload-listener backport | Port `QuestingRamContext` codec + resource reload listener; sync resulting state explicitly. |
| template_definition | 205 | high-value structural backport | Port weighted template-definition loader and sampling independently of modern registry APIs. |
| template_marker_handler_list | 1 | portable with structure hook | Port marker-handler dispatch/list abstraction, then bind it to ANCHOR structure-template callbacks. |
| tiny_bird_variant | 4 | easy isolated backport | Same pattern as rabbit variants: data-selected texture/biome + synced registry identity. |
| travellers_modifiers | 24 | subsystem rewrite | Port the polymorphic modifier concept only after an ANCHOR gear/component storage boundary is defined. |

The stalactite/speleothem families are listed separately above because they have a clear ANCHOR predecessor.

## 6. Recommended backport order

The dependency-safe sequence for a 1.20.1 Forge implementation is:

1. **Keep stable existing systems**
   - biome_layer_stack
   - wood_palettes
   - restrictions
2. **Extend existing codecs**
   - magic paintings
3. **Backport isolated reload/variant systems**
   - quests
   - tiny bird variants
   - dwarf rabbit variants
4. **Refactor existing stalactite system**
   - variety selection
   - structure placement settings
5. **Backport structure authoring infrastructure**
   - template_definition
   - template marker handlers
6. **Introduce worldgen policy abstractions**
   - biome terrain data
   - chunk blanket processors
7. **Treat Traveller gear modifiers as a separate feature project**
   - it depends on a broader modern equipment/data-component architecture

## 7. Core lesson

The important technology is not “new JSON files”.

The FRONTIER repeatedly moves changeable policy out of imperative Java and into:

```text
typed Codec
   ↓
versioned data record
   ↓
registry / reload boundary
   ↓
small runtime consumer
```

For KNEEKURA's 1.20.1 Forge work, the safe strategy is therefore:

- preserve ANCHOR runtime contracts;
- reproduce the FRONTIER separation of policy from mechanism;
- write ANCHOR-compatible codecs/loaders;
- regenerate 1.20.1-compatible data;
- never assume a FRONTIER JSON schema is accepted by 1.20.1.

## Evidence companions

- `CUSTOM-DATA-GRAPH.json` — all 290 FRONTIER records → blob SHA / loading mode / codec / consumers.
- `CUSTOM-DATA-PORTABILITY.json` — machine-readable family comparison and backport classification.
- `DATA-ASSETS.md` — overall asset/data architecture.
- `WORLDGEN.md` — terrain/chunk-generation architecture delta.
