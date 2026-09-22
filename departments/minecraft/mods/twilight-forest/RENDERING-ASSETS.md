# Twilight Forest — Rendering / Models / Assets

Status: **FRONTIER client rendering architecture mapped; full asset dependency graph in progress**

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

- generate complete entity → renderer → model layer → model → texture table;
- map block/item JSON model → texture references;
- map particle providers → textures;
- inspect shader/render pipeline code;
- compare ANCHOR model/render architecture;
- identify asset additions/removals by hash across tracks.
