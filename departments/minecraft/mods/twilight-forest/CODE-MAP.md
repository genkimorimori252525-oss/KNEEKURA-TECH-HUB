# Twilight Forest — Code Map

## Bootstrap

### ANCHOR

`TwilightForestMod` owns much of setup directly:

- Forge config creation;
- client init dispatch;
- global Forge event listeners;
- DeferredRegister registration;
- datapack registries;
- biome source and custom chunk generator codec registration;
- packet initialization through `TFPacketHandler.init()`.

Evidence snapshot: `a7dd8f13…`, `src/main/java/twilightforest/TwilightForestMod.java`.

### FRONTIER

`TwilightForestMod` is narrower and primarily registers DeferredRegisters. Lifecycle wiring is split into component classes such as `RegistrationEvents` and `ClientRegistrationEvents`.

The current entrypoint registers a very broad set of registry domains, including items, blocks, entity types, features, structure types/pieces/processors/placements, particles, attributes, data attachments, density-function types, custom biome-layer types, template marker handlers, and others.

## Custom registries

`TFRegistries` in FRONTIER defines both normal registries and datapack registries, including:

- biome-layer type / stack;
- enforcement;
- chunk blanket types/processors;
- template marker handler types/data;
- travellers modifier types/data;
- biome terrain data;
- restrictions;
- magic paintings;
- wood palettes;
- passive-entity variants.

Several runtime registries are synchronized to clients.

## Entity registration

`TFEntities` uses NeoForge `DeferredRegister` and also maintains explicit attribute and spawn-predicate maps. Entity types encode tracking range, update interval, dimensions, fire immunity and peaceful-mode policy near the registration site.

## Server/common lifecycle

FRONTIER `RegistrationEvents` centralizes:

- setup;
- packet registration;
- capabilities;
- custom registries;
- datapack registries;
- spawn placement;
- entity attributes;
- commands;
- reload listeners;
- config synchronization.

## Client lifecycle

FRONTIER `ClientRegistrationEvents` centralizes:

- entity and block-entity renderers;
- model layers;
- custom block-state models;
- custom item models;
- special model renderers;
- texture atlases;
- particles;
- screens;
- key mappings;
- render pipelines;
- client reload listeners;
- environment renderers and overlays.

This separation is a portability lesson: registry definition, server/common lifecycle, and client presentation can be treated as explicit boundaries rather than one giant mod initializer.
