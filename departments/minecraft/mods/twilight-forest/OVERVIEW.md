# The Twilight Forest — Overview

Status: **IN_PROGRESS**

## Pinned research tracks

### ANCHOR — Minecraft 1.20.1 + Forge

- Upstream: `TeamTwilight/twilightforest`
- Distributed version of interest: `4.3.2508`
- Public-source candidate: `a7dd8f13c653e137f977f5ffaa870fcb20fc1625`
- Minecraft: `1.20.1`
- Forge line in build config: `47.1.70`
- Java: 17
- Full tree inventory: 7,467 files / 1,265 Java / 4,986 JSON / 906 PNG / 137 OGG / 65 NBT

The distributed CurseForge/CurseMaven JAR is now pinned at SHA-256 `0bdc89263616d1b35c32ef82c5e9c14cbd20368e2fe8b468c72a28320be7a778` (23,332,091 bytes). Its manifest reports implementation version `4.3.2508` and build timestamp `2024-06-24T18:00:24+0000`. Against public-source candidate `a7dd8f13…`, **all 6,156 comparable resource paths match exact Git blob bytes**, with zero mismatches and zero source-resource omissions. This establishes strong resource/metadata correspondence; it does not independently prove compiled `.class` identity after compilation, mapping and reobfuscation.

### FRONTIER — Minecraft 26.1.2 + NeoForge

- Commit: `793c4d4c7b0a2892f702cbb9a8d751fbe7218828`
- Minecraft: `26.1.2`
- NeoForge: `26.1.2.102`
- Mod line: `4.9`
- Java: 25
- Full tree inventory: 9,592 files / 1,735 Java / 6,047 JSON / 1,160 PNG / 229 OGG / 273 NBT

## Architectural character

Twilight Forest is not one subsystem. It is a large content platform combining:

- a custom dimension and biome source;
- extensive structure/world-generation logic;
- progression and structure restrictions;
- many entities plus custom boss AI;
- custom packet synchronization;
- a large rendering/model/texture stack;
- data-driven registries and reload listeners;
- compatibility integrations;
- in FRONTIER, a separate ASM transformation module.

The entrypoint remains registry-heavy in both generations, but the latest code moves substantial lifecycle work into componentized event classes and Beanification-managed components.

## Major growth from ANCHOR to FRONTIER

| Surface | ANCHOR | FRONTIER |
|---|---:|---:|
| Java files | 1,265 | 1,735 |
| boss package Java | 19 | 23 |
| custom AI goals | 41 | 44 |
| network Java | 20 | 30 |
| structure Java | 222 | 291 |
| renderers | 94 | 124 |
| ASM transformer Java | 0 | 25 |

This makes the FRONTIER track valuable even when the deployment target stays on 1.20.1 Forge.
