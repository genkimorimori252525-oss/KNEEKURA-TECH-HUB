# 軽量化 MOD Catalog

**Adaptation anchor:** Minecraft **1.20.1 + Forge**

**Discovery frontier:** latest useful upstream implementation

**General modern MOD catalog:** [../../catalog/MODS.md](../../catalog/MODS.md)

| Queue | Target | Main categories | ANCHOR | FRONTIER | Performance state | Overall |
|---:|---|---|---|---|---|---|
| 1 | [AI Improvements: Performance Tuning](../mods/ai-improvements/README.md) | `TICK_SIMULATION` / `ENTITY_BLOCKENTITY` / `CACHE_DATA_STRUCTURE` | 1.20.1 Forge **target**; original adjacent source **1.20 Forge 46**, `0.5.2` @ [`89c89590`](https://github.com/BuiltBrokenModding/AI-Improvements/tree/89c89590d8160f332bd2740acd0a67c96f37f00d); binary parity pending | [`26.3`](https://github.com/BuiltBrokenModding/AI-Improvements/tree/a51cab76acf89099ea3c41393d858f9e061dbe4b) NeoForge, source inventory only | **PERFORMANCE_NOT_VERIFIED** | Selected static mechanism evidence; full analysis and runtime NOT_RUN |
| 2 | [Brute force Rendering Culling-forge-1.20.1-0.5.12.jar](https://github.com/RogoShum/BruteForceRenderingCulling/tree/58c55dcfe3d0a90c471c8a8b2bfedb1bf52685b3) | `RENDERING_GPU` | `forge-1.20.1` @ `58c55dcf`; **binary parity NOT_CHECKED** | NOT_ANALYZED | **PERFORMANCE_NOT_VERIFIED** | SELECTED_STATIC_EVIDENCE |
| 3 | [embeddium-0.3.31+mc1.20.1.jar](../mods/embeddium/README.md) | `RENDERING_GPU` | `20.1/forge` @ `dee0ebde`; **binary parity NOT_CHECKED** | NOT_ANALYZED | **PERFORMANCE_NOT_VERIFIED** | PHASE_2_SELECTED_STATIC_REVIEW |
| 4 | [particle_core-0.3.3+1.20.1+forge.jar](../mods/particle-core/README.md) | `RENDERING_GPU` | `forge/1.20.1` @ `8ae835f2`; **binary parity NOT_CHECKED** | NOT_ANALYZED | **PERFORMANCE_NOT_VERIFIED** | PHASE_2_SELECTED_STATIC_REVIEW |
| 5 | [cullleaves-forge-4.1.1+1.20.1.jar](https://github.com/TeamMidnightDust/CullLeaves/tree/a9ffb5061ae4ed49a55d5fe93679ee1d4bbe389e) | `RENDERING_GPU` | `multiversion` @ `a9ffb506`; **binary parity NOT_CHECKED** | NOT_ANALYZED | **PERFORMANCE_NOT_VERIFIED** | SELECTED_STATIC_EVIDENCE |
| 6 | [ferritecore-6.0.1-forge.jar](../mods/ferritecore/README.md) | `MEMORY` | `1.20.0` @ `e47bcbbd`; **binary parity NOT_CHECKED** | NOT_ANALYZED | **PERFORMANCE_NOT_VERIFIED** | PHASE_2_SELECTED_STATIC_REVIEW |
| 7 | [modernfix-forge-5.27.66+mc1.20.1.jar](../mods/modernfix/README.md) | `STARTUP_MEMORY_TICK` | `1.20` @ `cf04b47d`; **binary parity NOT_CHECKED** | NOT_ANALYZED | **PERFORMANCE_NOT_VERIFIED** | PHASE_2_SELECTED_STATIC_REVIEW |
| 8 | [smoothboot(reloaded)-mc1.20.1-0.0.4.jar](https://github.com/liangyaoyun209/SmoothBoot-Reloaded) | `STARTUP_CLASSLOADING` | `x1.18.2` repo lead; **binary parity NOT_CHECKED** | NOT_ANALYZED | **PERFORMANCE_NOT_VERIFIED** | SOURCE_DISCOVERY |
| 9 | [BadOptimizations-2.4.1-1.20.1.jar](https://github.com/imthosea/BadOptimizations/tree/f1540411b21e8458d6d143d00f53743e7a9bc893) | `TICK_SIMULATION_RENDERING` | `1.20.1` @ `f1540411`; **binary parity NOT_CHECKED** | NOT_ANALYZED | **PERFORMANCE_NOT_VERIFIED** | SELECTED_STATIC_EVIDENCE |
| 10 | [ImmediatelyFast-Forge-1.5.5+1.20.4.jar](https://github.com/RaphiMC/ImmediatelyFast/tree/b66885773494bfad58c83a8eee7b2f41424d4d9b) | `RENDERING_GPU` | `1.20` @ `b6688577`; **binary parity NOT_CHECKED** | NOT_ANALYZED | **PERFORMANCE_NOT_VERIFIED** | SELECTED_STATIC_EVIDENCE |
| 11 | [FastSuite-1.20.1-5.1.2.jar](../mods/fastsuite/README.md) | `RESOURCE_DATA_THREADING` | `1.20` @ `883aed9f`; **binary parity NOT_CHECKED** | NOT_ANALYZED | **PERFORMANCE_NOT_VERIFIED** | PHASE_2_SELECTED_STATIC_REVIEW |
| 12 | [letmedespawn-1.20.x-forge-1.5.0.jar](https://github.com/frikinjay/let-me-despawn) | `ENTITY_BLOCKENTITY` | `main` repo lead; **binary parity NOT_CHECKED** | NOT_ANALYZED | **PERFORMANCE_NOT_VERIFIED** | SOURCE_DISCOVERY |
| 13 | [alternate_current-mc1.20-1.7.0.jar](https://github.com/SpaceWalkerRS/alternate-current/tree/ab87061f1d04c44bfd42ba219ca567f8709c2acc) | `TICK_SIMULATION` | `forge` @ `ab87061f`; **binary parity NOT_CHECKED** | NOT_ANALYZED | **PERFORMANCE_NOT_VERIFIED** | SELECTED_STATIC_EVIDENCE |
| 14 | [getittogetherdrops-forge-1.20-1.3.jar](https://github.com/bl4ckscor3/GetItTogetherDrops) | `ENTITY_BLOCKENTITY` | `1.19` repo lead; **binary parity NOT_CHECKED** | NOT_ANALYZED | **PERFORMANCE_NOT_VERIFIED** | SOURCE_DISCOVERY |
| 15 | [Clumps-forge-1.20.1-12.0.0.4.jar](https://github.com/jaredlll08/Clumps/tree/d249b4d25478e6044b0951f01b729c17b5860456) | `ENTITY_BLOCKENTITY` | `1.20.1` @ `d249b4d2`; **binary parity NOT_CHECKED** | NOT_ANALYZED | **PERFORMANCE_NOT_VERIFIED** | SELECTED_STATIC_EVIDENCE |
| 16 | [starlight-1.1.2+forge.1cda73c.jar](https://github.com/PaperMC/Starlight/tree/c562a3a36e8f5ec0ad25a8fa530de0d9eadcc64a) | `LIGHTING` | `forge` @ `c562a3a3`; **binary parity NOT_CHECKED** | NOT_ANALYZED | **PERFORMANCE_NOT_VERIFIED** | SELECTED_STATIC_EVIDENCE |
| 17 | canary-mc1.20.1-0.3.3.jar | `TICK_SIMULATION` | SOURCE_MATCH_UNKNOWN; **binary parity NOT_CHECKED** | NOT_ANALYZED | **PERFORMANCE_NOT_VERIFIED** | NO_MATCHED_SOURCE |
| 18 | [bocchium-1.20.1-0.0.3.jar](https://github.com/MCTeamPotato/Bocchium/tree/57a2e920273422253dde64f2c3d907bca8679afe) | `RENDERING_GPU` | `1201` @ `57a2e920`; **binary parity NOT_CHECKED** | NOT_ANALYZED | **PERFORMANCE_NOT_VERIFIED** | SELECTED_STATIC_EVIDENCE |
| 19 | [alltheleaks-1.1.1+1.20.1-forge.jar](https://github.com/pietro-lopes/AllTheLeaks/tree/5f4157f5362ea6471601114f8695ae44b0a3e28e) | `MEMORY` | `1.20.1` @ `5f4157f5`; **binary parity NOT_CHECKED** | NOT_ANALYZED | **PERFORMANCE_NOT_VERIFIED** | SOURCE_PATH_INDEX |
| 20 | [DistantHorizons-3.2.0-b-1.20.1-fabric-forge.jar](https://gitlab.com/distant-horizons-team/distant-horizons) | `CULLING_LOD` | SOURCE_MATCH_UNKNOWN; **binary parity NOT_CHECKED** | NOT_ANALYZED | **PERFORMANCE_NOT_VERIFIED** | SOURCE_DISCOVERY |
| 21 | [dynamic-fps-3.11.4+minecraft-1.20.0-forge.jar](https://github.com/juliand665/Dynamic-FPS) | `TICK_BACKGROUND_RENDER` | `main` repo lead; **binary parity NOT_CHECKED** | NOT_ANALYZED | **PERFORMANCE_NOT_VERIFIED** | SOURCE_DISCOVERY |
| 22 | [servercore-forge-1.5.2+1.20.1.jar](../mods/servercore/README.md) | `TICK_SIMULATION` | `1.20.1` @ `d1d0a02d`; **binary parity NOT_CHECKED** | NOT_ANALYZED | **PERFORMANCE_NOT_VERIFIED** | PHASE_2_SELECTED_STATIC_REVIEW |
| 23 | [entityculling-forge-1.10.5-mc1.20.1.jar](https://github.com/tr7zw/EntityCulling/tree/dff7304bcbb9186bada0a8c4617dc584fb2c3ea1) | `RENDERING_GPU` | `1.20` @ `dff7304b`; **binary parity NOT_CHECKED** | NOT_ANALYZED | **PERFORMANCE_NOT_VERIFIED** | SELECTED_STATIC_EVIDENCE |
| 24 | [GPUTape-1.18x-1.21x-1.0.5.1.jar](https://github.com/StarmanMine142/GpuTape/tree/e57f961776195894ed23687f9c143fd6942b9d58) | `RENDERING_GPU` | `1.18x-1.21x` @ `e57f9617`; **binary parity NOT_CHECKED** | NOT_ANALYZED | **PERFORMANCE_NOT_VERIFIED** | SOURCE_PATH_INDEX |
| 25 | [memoryleakfix-forge-1.17+-1.1.5.jar](https://github.com/FxMorin/MemoryLeakFix/tree/988f54c14db0d86e13dd5dcce284178b2278e581) | `MEMORY` | `dev` @ `988f54c1`; **binary parity NOT_CHECKED** | NOT_ANALYZED | **PERFORMANCE_NOT_VERIFIED** | SOURCE_PATH_INDEX |
| 26 | [noisium-forge-2.3.0+mc1.20-1.20.1.jar](https://github.com/Steveplays28/noisium/tree/c640041c8c932b36753c0ccf43902ac8b0bd252d) | `CHUNK_WORLDGEN_IO` | `1.20-1.20.1` @ `c640041c`; **binary parity NOT_CHECKED** | NOT_ANALYZED | **PERFORMANCE_NOT_VERIFIED** | SELECTED_STATIC_EVIDENCE |
| 27 | saturn-mc1.20.1-0.1.3.jar | `MEMORY` | SOURCE_MATCH_UNKNOWN; **binary parity NOT_CHECKED** | NOT_ANALYZED | **PERFORMANCE_NOT_VERIFIED** | NO_MATCHED_SOURCE |

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
