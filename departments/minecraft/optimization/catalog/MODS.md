# 軽量化 MOD Catalog

**Adaptation anchor:** Minecraft **1.20.1 + Forge**

**Discovery frontier:** latest useful upstream implementation

**General modern MOD catalog:** [../../catalog/MODS.md](../../catalog/MODS.md)

| Queue | Target | Main categories | ANCHOR | FRONTIER | Performance state | Overall |
|---:|---|---|---|---|---|---|
| 1 | [AI Improvements: Performance Tuning](../mods/ai-improvements/README.md) | `TICK_SIMULATION` / `ENTITY_BLOCKENTITY` / `CACHE_DATA_STRUCTURE` | 1.20.1 Forge **target**; original adjacent source **1.20 Forge 46**, `0.5.2` @ [`89c89590`](https://github.com/BuiltBrokenModding/AI-Improvements/tree/89c89590d8160f332bd2740acd0a67c96f37f00d); binary parity pending | [`26.3`](https://github.com/BuiltBrokenModding/AI-Improvements/tree/a51cab76acf89099ea3c41393d858f9e061dbe4b) NeoForge, source inventory only | **PERFORMANCE_NOT_VERIFIED** | Selected static mechanism evidence; full analysis and runtime NOT_RUN |
| 2 | [Brute force Rendering Culling-forge-1.20.1-0.5.12.jar](../mods/brute-force-rendering-culling/README.md) | `RENDERING_GPU` | `forge-1.20.1` @ `58c55dcf`; **binary parity NOT_CHECKED** | NOT_ANALYZED | **PERFORMANCE_NOT_VERIFIED** | PHASE_3_RENDERING_STATIC_REVIEW |
| 3 | [embeddium-0.3.31+mc1.20.1.jar](../mods/embeddium/README.md) | `RENDERING_GPU` | `20.1/forge` @ `dee0ebde`; **binary parity NOT_CHECKED** | NOT_ANALYZED | **PERFORMANCE_NOT_VERIFIED** | PHASE_2_SELECTED_STATIC_REVIEW |
| 4 | [particle_core-0.3.3+1.20.1+forge.jar](../mods/particle-core/README.md) | `RENDERING_GPU` | `forge/1.20.1` @ `8ae835f2`; **binary parity NOT_CHECKED** | NOT_ANALYZED | **PERFORMANCE_NOT_VERIFIED** | PHASE_2_SELECTED_STATIC_REVIEW |
| 5 | [cullleaves-forge-4.1.1+1.20.1.jar](../mods/cullleaves/README.md) | `RENDERING_GPU` | `multiversion` @ `a9ffb506`; **binary parity NOT_CHECKED** | NOT_ANALYZED | **PERFORMANCE_NOT_VERIFIED** | PHASE_3_RENDERING_STATIC_REVIEW |
| 6 | [ferritecore-6.0.1-forge.jar](../mods/ferritecore/README.md) | `MEMORY` | `1.20.0` @ `e47bcbbd`; **binary parity NOT_CHECKED** | NOT_ANALYZED | **PERFORMANCE_NOT_VERIFIED** | PHASE_2_SELECTED_STATIC_REVIEW |
| 7 | [modernfix-forge-5.27.66+mc1.20.1.jar](../mods/modernfix/README.md) | `STARTUP_MEMORY_TICK` | `1.20` @ `cf04b47d`; **binary parity NOT_CHECKED** | NOT_ANALYZED | **PERFORMANCE_NOT_VERIFIED** | PHASE_2_SELECTED_STATIC_REVIEW |
| 8 | [smoothboot(reloaded)-mc1.20.1-0.0.4.jar](../cohorts/2026-10-11-forge-1.20.1/PHASE-7-SOURCE-IDENTITY-GATES.md) | `STARTUP_CLASSLOADING` | Forge 1.20.1 0.0.4 exact source NOT_FOUND; 1.19.2 historic COMPARATIVE | NOT_ANALYZED | **PERFORMANCE_NOT_VERIFIED** | SOURCE_IDENTITY_BLOCKED
| 9 | [BadOptimizations-2.4.1-1.20.1.jar](../mods/badoptimizations/README.md) | `TICK_SIMULATION_RENDERING` | `1.20.1` @ `f1540411`; **binary parity NOT_CHECKED** | NOT_ANALYZED | **PERFORMANCE_NOT_VERIFIED** | PHASE_3_RENDERING_STATIC_REVIEW |
| 10 | [ImmediatelyFast-Forge-1.5.5+1.20.4.jar](../mods/immediatelyfast/README.md) | `RENDERING_GPU` | `1.20` @ `b6688577`; **binary parity NOT_CHECKED** | NOT_ANALYZED | **PERFORMANCE_NOT_VERIFIED** | PHASE_3_RENDERING_STATIC_REVIEW |
| 11 | [FastSuite-1.20.1-5.1.2.jar](../mods/fastsuite/README.md) | `RESOURCE_DATA_THREADING` | `1.20` @ `883aed9f`; **binary parity NOT_CHECKED** | NOT_ANALYZED | **PERFORMANCE_NOT_VERIFIED** | PHASE_2_SELECTED_STATIC_REVIEW |
| 12 | [letmedespawn-1.20.x-forge-1.5.0.jar](../mods/let-me-despawn/README.md) | `ENTITY_BLOCKENTITY` | Forge 1.20.1 1.5.0 exact source NOT_FOUND; 1.18/1.21 COMPARATIVE | NOT_ANALYZED | **PERFORMANCE_NOT_VERIFIED** | PHASE_7_COMPARATIVE_SOURCE_ONLY
| 13 | [alternate_current-mc1.20-1.7.0.jar](../mods/alternate-current/README.md) | `TICK_SIMULATION` | `forge` @ `ab87061f`; **binary parity NOT_CHECKED** | NOT_ANALYZED | **PERFORMANCE_NOT_VERIFIED** | PHASE_6_SERVER_WORLD_STATIC_REVIEW |
| 14 | [getittogetherdrops-forge-1.20-1.3.jar](../mods/get-it-together-drops/README.md) | `ENTITY_BLOCKENTITY` | Forge 1.20 1.3 exact source not pushed; Forge 1.19.2 COMPARATIVE | NOT_ANALYZED | **PERFORMANCE_NOT_VERIFIED** | PHASE_7_COMPARATIVE_SOURCE_ONLY
| 15 | [Clumps-forge-1.20.1-12.0.0.4.jar](../mods/clumps/README.md) | `ENTITY_BLOCKENTITY` | 1.20.1 series @ `d249b4d2`, build .4 unverified; **binary parity NOT_CHECKED** | NOT_ANALYZED | **PERFORMANCE_NOT_VERIFIED** | PHASE_6_SERVER_WORLD_STATIC_REVIEW |
| 16 | [starlight-1.1.2+forge.1cda73c.jar](../mods/starlight/README.md) | `LIGHTING` | version 1.1.2 exact Git short SHA `1cda73c`; **binary parity NOT_CHECKED** | NOT_ANALYZED | **PERFORMANCE_NOT_VERIFIED** | PHASE_6_SERVER_WORLD_STATIC_REVIEW |
| 17 | [canary-mc1.20.1-0.3.3.jar](../cohorts/2026-10-11-forge-1.20.1/PHASE-7-SOURCE-IDENTITY-GATES.md) | `TICK_SIMULATION` | Canary 0.3.3 original source NOT_FOUND; Lithium 1.20.1 COMPARATIVE | NOT_ANALYZED | **PERFORMANCE_NOT_VERIFIED** | SOURCE_IDENTITY_BLOCKED
| 18 | [bocchium-1.20.1-0.0.3.jar](../mods/bocchium/README.md) | `RENDERING_GPU` | `1201` @ `57a2e920`; **binary parity NOT_CHECKED** | NOT_ANALYZED | **PERFORMANCE_NOT_VERIFIED** | PHASE_3_RENDERING_STATIC_REVIEW |
| 19 | [alltheleaks-1.1.1+1.20.1-forge.jar](../mods/alltheleaks/README.md) | `MEMORY` | `1.20.1` @ `5f4157f5`; **binary parity NOT_CHECKED** | NOT_ANALYZED | **PERFORMANCE_NOT_VERIFIED** | PHASE_4_5_STATIC_PARTIAL_DOSSIER |
| 20 | [DistantHorizons-3.2.0-b-1.20.1-fabric-forge.jar](../mods/distant-horizons/README.md) | `CULLING_LOD` | Exact release 3.2.0b Git main + Core gitlink pinned; **binary parity NOT_CHECKED** | NOT_ANALYZED | **PERFORMANCE_NOT_VERIFIED** | PHASE_4_5_STATIC_PARTIAL_DOSSIER |
| 21 | [dynamic-fps-3.11.4+minecraft-1.20.0-forge.jar](../mods/dynamic-fps/README.md) | `TICK_BACKGROUND_RENDER` | Forge 1.20-1.20.1 source 3.11.4 @ 499b5eed; binary parity NOT_VERIFIED | NOT_ANALYZED | **PERFORMANCE_NOT_VERIFIED** | PHASE_7_ANCHOR_SOURCE_STATIC_PARTIAL
| 22 | [servercore-forge-1.5.2+1.20.1.jar](../mods/servercore/README.md) | `TICK_SIMULATION` | `1.20.1` @ `d1d0a02d`; **binary parity NOT_CHECKED** | NOT_ANALYZED | **PERFORMANCE_NOT_VERIFIED** | PHASE_2_SELECTED_STATIC_REVIEW |
| 23 | [entityculling-forge-1.10.5-mc1.20.1.jar](../mods/entityculling/README.md) | `RENDERING_GPU` | `1.20` @ `dff7304b`; **binary parity NOT_CHECKED** | NOT_ANALYZED | **PERFORMANCE_NOT_VERIFIED** | PHASE_3_RENDERING_STATIC_REVIEW |
| 24 | [GPUTape-1.18x-1.21x-1.0.5.1.jar](../mods/gputape/README.md) | `RENDERING_GPU` | Exact 1.0.5.1 source UNKNOWN; 1.1.0 comparative `16bf18c`; **binary parity NOT_CHECKED** | NOT_ANALYZED | **PERFORMANCE_NOT_VERIFIED** | PHASE_4_5_STATIC_PARTIAL_DOSSIER |
| 25 | [memoryleakfix-forge-1.17+-1.1.5.jar](../mods/memoryleakfix/README.md) | `MEMORY` | 1.1.5 source dev 1.20.4 `988f54c1`; **binary parity NOT_CHECKED** | NOT_ANALYZED | **PERFORMANCE_NOT_VERIFIED** | PHASE_4_5_STATIC_PARTIAL_DOSSIER |
| 26 | [noisium-forge-2.3.0+mc1.20-1.20.1.jar](../mods/noisium/README.md) | `CHUNK_WORLDGEN_IO` | source 2.3.0 @ `8cf45180`; **binary parity NOT_CHECKED** | NOT_ANALYZED | **PERFORMANCE_NOT_VERIFIED** | PHASE_6_SERVER_WORLD_STATIC_REVIEW |
| 27 | [saturn-mc1.20.1-0.1.3.jar](../cohorts/2026-10-11-forge-1.20.1/PHASE-7-SOURCE-IDENTITY-GATES.md) | `MEMORY` | Saturn 0.1.3 Forge 1.20.1 source NOT_FOUND | NOT_ANALYZED | **PERFORMANCE_NOT_VERIFIED** | SOURCE_IDENTITY_BLOCKED

## 2026-10-11 input cohort — 58 files, 27 optimization candidates

All 58 names, source-identity states and excluded/diagnostic/related groups live at [full input manifest](../cohorts/2026-10-11-forge-1.20.1/INPUT-MANIFEST.json) and [phase-one analysis](../cohorts/2026-10-11-forge-1.20.1/README.md). The 27 rows above are **research candidates**, NOT fully analyzed, not recommended install combinations, and **NOT** claims that the pinned source revision equals the named release JAR. Forge/NeoForge/version drift and full access gaps are preserved.

## Rules

- 主目的がperformance optimizationのMODをここへ置く。
- content MODの局所最適化は target を重複登録せず TECHNIQUES catalogから参照する。
- ANCHOR / FRONTIER evidenceを混ぜない。
- source mechanism と benchmark result を混ぜない。
- performance未計測なら `PERFORMANCE_NOT_VERIFIED` と書く。
- correctness regressionを隠して性能値だけを掲載しない。
- 太古の軽量化MODの原版は `kobun/` で扱う。
