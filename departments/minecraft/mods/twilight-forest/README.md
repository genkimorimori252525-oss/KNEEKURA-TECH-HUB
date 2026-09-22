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
- Exact distributed-JAR ↔ source identity: **not yet proven**

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
- data assets: mapped at family/system-consumer level
- compatibility/platform boundary: mapped (normal APIs / AT / ASM / Mod adapters)
- version portability: first-pass mapped
- performance: hot-path/caching hypotheses inventoried; runtime measurement pending
- full FRONTIER mob AI catalog: mapped for all 53 non-boss classes, including inherited/imperative semantics
- full FRONTIER structure catalog: mapped (25 declared keys / 21 active generated / 4 declared-only / 19 own Structure Sets)

See the sibling reports and `inventory/` manifests for evidence-backed progress.

## Remaining high-priority work

- prove/hash exact 4.3.2508 distributed JAR against ANCHOR source candidate
- map ANCHOR entity rendering/assets beyond inventory level
- record-level custom data codec/consumer graph
- runtime performance and compatibility measurements
