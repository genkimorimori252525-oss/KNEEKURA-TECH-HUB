# The Twilight Forest — Analysis Workspace

## Queue

- Priority: **1**
- Upstream: `TeamTwilight/twilightforest`
- Kind: content/gameplay Mod
- Status: **IN_PROGRESS**

## Tracks

### ANCHOR — Minecraft 1.20.1 + Forge

- Distributed target: `4.3.2508`
- Public-source candidate pinned: `a7dd8f13c653e137f977f5ffaa870fcb20fc1625`
- Full public-source tree inventory: **complete**
- Distributed JAR SHA-256: `0bdc89263616d1b35c32ef82c5e9c14cbd20368e2fe8b468c72a28320be7a778`
- Resource correspondence to `a7dd8f13…`: **6,156 / 6,156 exact Git-blob matches; 0 mismatches; 0 missing**
- Identity conclusion: **RESOURCE_CORRESPONDENCE_STRONG**
- Compiled-class identity: **not asserted**; compilation/remap/reobf remains a separate proof boundary

### FRONTIER — Minecraft 26.1.2 + NeoForge

- Commit pinned: `793c4d4c7b0a2892f702cbb9a8d751fbe7218828`
- Full tree inventory: **complete**

## Current analysis coverage

- bootstrap / registries: mapped
- major boss architecture + explicit transition matrix: mapped
- networking: mapped, including exact 29-payload FRONTIER direction map
- worldgen architecture: mapped, including dimension/noise pipeline
- rendering/model/client architecture: mapped
- all 8 principal boss renderer/model/texture dependencies: mapped
- texture/model files: fully inventoried; all 81 EntityType renderer/model/layer/asset-selection dependencies mapped
- data assets: mapped to record level; all 290 custom `twilight/*` records linked to blob SHA + loader mode + codec + consumer
- custom-data portability: ANCHOR↔FRONTIER family/schema delta and 1.20.1 backport order mapped
- compatibility/platform boundary: mapped (normal APIs / AT / ASM / Mod adapters)
- version portability: first-pass mapped
- performance: hot-path/caching hypotheses inventoried; reproducible runtime evidence spec prepared, measurements pending
- full FRONTIER mob AI catalog: mapped for all 53 non-boss classes, including inherited/imperative semantics\n- ANCHOR↔FRONTIER AI portability: mapped for 132 AI/entity Java paths; principal boss refactors classified\n- compatibility feature evolution: mapped for Curios/Jade/JEI/TOP/EMI/REI with ACTIVE vs DISABLED state
- full FRONTIER structure catalog: mapped (25 declared keys / 21 active generated / 4 declared-only / 19 own Structure Sets)\n- global block/item render graph: extractor implemented for 528 blockstates + 1,773 models + 663 item definitions + texture/atlas resolution; LAB full-checkout execution requested

See the sibling reports and `inventory/` manifests for evidence-backed progress.

## Remaining high-priority work

- materialize and integrate the full block/item render graph from the LAB run
- runtime performance and compatibility measurements
- optional class-level reproducible-build comparison if compiled-code identity is ever required
