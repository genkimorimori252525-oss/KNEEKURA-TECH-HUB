# Twilight Forest — Structure Catalog

Status: **FRONTIER active structure catalog mapped**

Source snapshot: `TeamTwilight/twilightforest@793c4d4c7b0a2892f702cbb9a8d751fbe7218828`.

## Snapshot accounting

`TFStructures` declares **25** structure ResourceKeys.

- **21** are bootstrapped and have generated `worldgen/structure/*.json` in the pinned FRONTIER snapshot.
- **4** are declaration-only here: `quest_island`, `druid_grove`, `floating_ruins`, `world_tree`.
- **19** active structures/structure families have their own generated `structure_set` JSON.
- `mushroom_tower` is active and generated but has no own `structure_set` file in this snapshot.

Declaration is therefore not treated as evidence that a structure is currently placed.

## Placement architecture

Two placement families dominate.

### Landmark grid

Progression/landmark structures use `twilightforest:landmark_grid`. Examples include Naga Courtyard, Lich Tower, Labyrinth, Hydra Lair, Knight Stronghold, Dark Tower, Yeti Cave, Aurora Palace, Troll Cave, Final Castle and Giant House.

Several also pin a `structure_grid_lock`, including Naga Courtyard, Lich Tower, small/medium/large Hollow Hills and Hedge Maze.

**Reusable lesson:** progression geography is deterministic at a higher grid layer rather than each landmark independently rolling random spacing.

### Avoid-landmark random placement

Environmental structures use `twilightforest:avoid_landmark_grid`.

- `camp`: spacing 18 / separation 14, triangular spread, and explicit avoidance of fallen trunks/hollow trees.
- `fallen_trunk`: spacing 7 / separation 5, frequency 0.8, excludes the Hollow Tree set within one chunk.
- `hollow_tree`: spacing 7 / separation 5, frequency 0.5; one set contains normal and swamp hollow-tree variants.

**Reusable lesson:** ambient content can use ordinary randomized placement while explicitly respecting the gameplay landmark lattice.

## Generation steps / terrain adaptation

- `knight_stronghold`, `labyrinth`, `troll_cave`: `underground_structures` + `bury`.
- `giant_house`: `top_layer_modification`.
- Most others: `surface_structures`.
- `beard_thin` is used by Lich Tower, Naga Courtyard, Dark Tower and Quest Grove.
- `beard_box` is used by Camp, Hedge Maze and Final Castle.

This fits the broader FRONTIER design where structure terrain influence is fed into vanilla noise generation through custom Beardifier integration.

## Active structures

| ID | Type | Step | Placement |
|---|---|---|---|
| `aurora_palace` | `twilightforest:aurora_palace` | `surface_structures` | `landmark_grid` |
| `camp` | `twilightforest:camp` | `surface_structures` | `avoid_landmark_grid` |
| `dark_tower` | `twilightforest:dark_tower` | `surface_structures` | `landmark_grid` |
| `fallen_trunk` | `twilightforest:fallen_trunk` | `surface_structures` | `avoid_landmark_grid` |
| `final_castle` | `twilightforest:final_castle` | `surface_structures` | `landmark_grid` |
| `giant_house` | `twilightforest:giant_house` | `top_layer_modification` | `landmark_grid` |
| `hedge_maze` | `twilightforest:hedge_maze` | `surface_structures` | `landmark_grid` |
| `hollow_tree` | `twilightforest:hollow_tree` | `surface_structures` | `avoid_landmark_grid` |
| `hydra_lair` | `twilightforest:hydra_lair` | `surface_structures` | `landmark_grid` |
| `knight_stronghold` | `twilightforest:knight_stronghold` | `underground_structures` | `landmark_grid` |
| `labyrinth` | `twilightforest:labyrinth` | `underground_structures` | `landmark_grid` |
| `large_hollow_hill` | `twilightforest:hollow_hill` | `surface_structures` | `landmark_grid` |
| `lich_tower` | `twilightforest:lich_tower` | `surface_structures` | `landmark_grid` |
| `medium_hollow_hill` | `twilightforest:hollow_hill` | `surface_structures` | `landmark_grid` |
| `mushroom_tower` | `twilightforest:mushroom_tower` | `surface_structures` | no own set found |
| `naga_courtyard` | `twilightforest:naga_courtyard` | `surface_structures` | `landmark_grid` |
| `quest_grove` | `twilightforest:quest_grove` | `surface_structures` | `landmark_grid` |
| `small_hollow_hill` | `twilightforest:hollow_hill` | `surface_structures` | `landmark_grid` |
| `swamp_hollow_tree` | `twilightforest:hollow_tree` | `surface_structures` | `avoid_landmark_grid` |
| `troll_cave` | `twilightforest:troll_cave` | `underground_structures` | `landmark_grid` |
| `yeti_cave` | `twilightforest:yeti_cave` | `surface_structures` | `landmark_grid` |

## Declared-only keys

`quest_island`, `druid_grove`, `floating_ruins`, and `world_tree` remain useful historical/future signals, but are **not** counted as active generated structures in this pinned snapshot.

Machine-readable copy: `STRUCTURE-CATALOG.json`.
