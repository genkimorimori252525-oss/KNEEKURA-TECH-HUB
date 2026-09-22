# Twilight Forest — Rendering / Models / Assets

Status: **FRONTIER + ANCHOR client rendering architecture and global block/item asset graphs mapped**

Source snapshot: `TeamTwilight/twilightforest@793c4d4c7b0a2892f702cbb9a8d751fbe7218828`.

## Scale

FRONTIER whole-tree inventory contains:

- 1,160 PNG files;
- 1,241 paths under texture directories;
- 336 paths under client directories;
- 76 Java classes in the entity-renderer-heavy package group;
- 61 Java classes in the main entity-model package group;
- a separate `client/state/entity` render-state layer.

## Client registration hub

Evidence:

- `src/main/java/twilightforest/client/event/ClientRegistrationEvents.java`
- blob `41aa907d9c07bc9258aa91382443da87d6e66eb7`

This class wires most presentation systems:

- entity renderers;
- block-entity renderers;
- model layers;
- custom block-state models;
- item models;
- special model renderers;
- standalone models;
- texture atlases;
- particles;
- screens;
- client extensions;
- map decorators;
- item model properties;
- environment renderers;
- render-state modifiers;
- render pipelines;
- resource reload listeners;
- overlays and tooltip components.

This is a clean boundary between simulation/registry code and client presentation code.

## Render-state architecture

Modern FRONTIER renderers often follow:

```text
Entity simulation state
        ↓ extractRenderState(...)
RenderState snapshot
        ↓
Renderer
        ↓
Model / layers / RenderType
        ↓
Texture(s)
```

This is especially useful for backport design: the exact 26.1 renderer API is not portable to 1.20.1, but the separation between gameplay state and presentation snapshot is.

## Model layer registry

Evidence:

- `src/main/java/twilightforest/client/model/TFModelLayers.java`

The registry defines named model layers for bosses, normal mobs, multipart pieces, trophies, block entities, armor and special equipment.

Examples include:

- NAGA + NAGA_BODY
- HYDRA + HYDRA_HEAD + HYDRA_NECK + HYDRA_MORTAR
- LICH
- KNIGHT_PHANTOM
- MINOSHROOM
- SNOW_QUEEN
- UR_GHAST
- ALPHA_YETI

Multipart simulation therefore has matching multipart presentation assets instead of one flattened model.

## Boss rendering examples

### Naga

Evidence:

- Renderer: `client/renderer/entity/NagaRenderer.java`
- blob `6c9742bd26e6563848e5a6ad2b559366b52c0314`
- Model: `client/model/entity/NagaModel.java`
- Render state: `client/state/entity/NagaRenderState.java`

Textures selected by state:

- `textures/entity/nagahead.png`
- `textures/entity/nagahead_charging.png`
- `textures/entity/nagahead_dazed.png`

The renderer extracts dazed/charging/stunless progress from the entity and selects/tints presentation accordingly.

### Hydra

Evidence:

- Renderer: `client/renderer/entity/HydraRenderer.java`
- blob `d85966eae8c7b121b61d54cc80dcee994d1a0e37`
- Model: `client/model/entity/HydraModel.java`
- Render state: `client/state/entity/HydraRenderState.java`
- Texture: `textures/entity/hydra4.png`

Hydra disables normal culling assumptions and inflates its culling bounds because the multipart encounter extends far outside the body entity's ordinary visual footprint.

### Lich

Evidence:

- Renderer: `client/renderer/entity/LichRenderer.java`
- blob `755abde65b4c8530bb64e0544aef2c7417184647`
- Model: `client/model/entity/LichModel.java`
- Render state: `client/state/entity/LichRenderState.java`

Assets/layers include:

- `textures/entity/twilightlich64.png`
- `textures/entity/twilightlich64_eyes.png`
- shield layer;
- special shadow-clone RenderType/tint.

The clone distinction comes from simulation state but is materialized entirely in client rendering.

### Snow Queen

Evidence:

- Renderer: `client/renderer/entity/SnowQueenRenderer.java`
- blob `876cfe1e598cafbf4ed7cda4c26318f876bcfd58`
- Model: `client/model/entity/SnowQueenModel.java`
- Render state: `client/state/entity/SnowQueenRenderState.java`
- Texture: `textures/entity/snowqueen.png`

The render state carries breathing and boss phase, allowing the model/renderer to visualize server-driven encounter state.

## Resource reload and generated presentation

FRONTIER registers:

- a texture generator reload listener;
- an armor cache reload listener;
- a dedicated magic-painting atlas.

This means not all visual assets are static files used directly. Some presentation state/resources are generated or cached during resource reload.

## Custom model systems

The client registers custom model codecs for connected textures, force fields, giant blocks, noise-varying blocks and plant patches, plus custom item models and multiple special renderers.

Reusable lesson: Twilight Forest treats rendering as a programmable subsystem, not merely a directory of PNGs.

## Backport lesson for 1.20.1

High-value concept to preserve:

```text
authoritative simulation
    ↓
small immutable/interpolated presentation snapshot
    ↓
renderer/model/texture selection
```

On 1.20.1 Forge this should be recreated with the older renderer API rather than copying 26.1 classes.

## Remaining rendering work

- **DONE (v1):** all 81 registered entity renderers are resolved in `ENTITY-RENDER-DEPENDENCIES.json`; 66 Twilight Forest renderer classes were inspected in four evidence batches and renderer inheritance is followed.
- **DONE:** map global block/item JSON model → parent/model/texture/atlas references for pinned FRONTIER and ANCHOR snapshots;
- map particle providers → textures;
- inspect shader/render pipeline code;
- compare ANCHOR model/render architecture;
- identify asset additions/removals by hash across tracks.

## Major-boss render dependency table

All eight principal progression bosses now have direct FRONTIER renderer/model-layer/texture mappings.

| Boss | Renderer | Model / layer | Primary texture(s) |
|---|---|---|---|
| Naga | `NagaRenderer` | `NagaModel` / `TFModelLayers.NAGA` | `nagahead.png`, `nagahead_charging.png`, `nagahead_dazed.png` |
| Lich | `LichRenderer` | `LichModel` / `LICH` | `twilightlich64.png`, eye layer `twilightlich64_eyes.png` |
| Hydra | `HydraRenderer` | `HydraModel` / `HYDRA` | `hydra4.png` |
| Ur-Ghast | `UrGhastRenderer` | `UrGhastModel` / `UR_GHAST` | `towerboss.png`, `towerboss_openeyes.png`, `towerboss_fire.png` |
| Snow Queen | `SnowQueenRenderer` | `SnowQueenModel` / `SNOW_QUEEN` | `snowqueen.png` |
| Alpha Yeti | `AlphaYetiRenderer` | `AlphaYetiModel` / `ALPHA_YETI` | `yetialpha.png` |
| Knight Phantom | `KnightPhantomRenderer` | `KnightPhantomModel` / `KNIGHT_PHANTOM` | `phantomskeleton.png` + armor layer |
| Minoshroom | `MinoshroomRenderer` | `MinoshroomModel` / `MINOSHROOM` | `minoshroomtaur.png` + dynamic brown-mushroom block-model layer |

Machine-readable copy: `BOSS-RENDER-MAP.json`.

This reinforces a recurring pattern: authoritative encounter state is projected into render state and then into model/texture choice; presentation does not drive combat state.

## Complete EntityType → Renderer registration surface

The pinned FRONTIER client registers **81** entity renderers. Every registration is captured in `ENTITY-RENDER-REGISTRY.json`.

This first registry pass is exhaustive for registration wiring. Inline registrations already expose model/layer/texture arguments; class-reference renderers are being resolved separately to model layers and texture dependencies.

## Complete 81-entity dependency map

The full FRONTIER registration surface is now resolved in `ENTITY-RENDER-DEPENDENCIES.json`.

- 81 EntityType registrations classified;
- 66 distinct Twilight Forest renderer source classes inspected;
- 74 registrations resolve through Twilight Forest renderer source (shared classes included);
- 1 registration is inline-only;
- 6 registrations use Minecraft generic renderers;
- 62 registrations expose literal/direct-or-inherited texture references during the source extraction pass;
- the remaining 19 have all been semantically classified rather than left unknown.

Those 19 use one of these mechanisms:

- vanilla WolfVariant assets;
- datapack-driven Tiny Bird / Dwarf Rabbit variants;
- a custom RenderType texture (Protection Box);
- the dedicated Magic Painting texture atlas;
- runtime player skins (Giants);
- Minecraft NoopRenderer;
- item-model rendering;
- BlockState/moving-block rendering;
- inherited vanilla Zombie rendering.

Evidence batches:

- `inventory/renderers-batch-01.json`
- `inventory/renderers-batch-02.json`
- `inventory/renderers-batch-03.json`
- `inventory/renderers-batch-04.json`

This closes the first-pass **Entity → Renderer → Model/Layer → asset-selection strategy** map. The separate global block/item JSON-model graph is now also materialized for both pinned tracks.


## Global block/item graph extractor

The remaining data-driven render graph now has an implemented extractor:

- `tools/build_render_asset_graph.py`
- specification: `RENDER-ASSET-GRAPH-SPEC.md`

The pinned FRONTIER inventory contains:

- 528 blockstate JSON files;
- 1,773 model JSON files;
- 663 modern item-definition JSON files;
- 1 Twilight Forest atlas JSON;
- 1,159 texture PNG files.

The extractor walks:

```text
blockstate / item definition
        ↓
model
        ↓
parent model
        ↓
texture / atlas resource
```

and records SHA-256, local reference resolution, unresolved Twilight Forest references, duplicate logical assets, parse failures and model-parent cycles.

Full-checkout execution completed on GitHub Actions run `35767314089` using self-hosted Windows/x64 runner `Jolly-TechHub`. FRONTIER produced 4,124 nodes / 7,174 edges with 17 unresolved local refs; ANCHOR produced 3,774 nodes / 8,591 edges with 15 unresolved local refs. Both have 0 duplicate logical paths, 0 parse errors, and 0 model-parent cycles. Cross-track results are stored in `BLOCK-ITEM-RENDER-COMPARISON.json` / `.md`, and the exact run/tool/source identities are recorded in `RENDER-GRAPH-FULL-CHECKOUT-EVIDENCE.json`.
