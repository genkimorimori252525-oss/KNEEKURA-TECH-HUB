# Optimization Techniques Catalog

MOD単位ではなく、**再利用できる軽量化技術単位**の横断catalog。

| ID | Category | Technique | Source target | Track | Mechanism evidence | Benchmark state | Correctness boundary | Reuse status |
|---|---|---|---|---|---|---|---|---|
| `AI-GOAL-PRUNING` | `TICK_SIMULATION`, `ENTITY_BLOCKENTITY` | 対象Goalの任意削除で実行を省く | [AI Improvements](../mods/ai-improvements/OPTIMIZATIONS.md) | 1.20 Forge adjacent to ANCHOR | `ModifierLayer`, `FilteredRemove` | **PERFORMANCE_NOT_VERIFIED** | Mobの行動・演出自体が変化、既定では主な除去はfalse | CONCEPT_ONLY |
| `AI-TRIG-LOOKCONTROL` | `CACHE_DATA_STRUCTURE`, `ENTITY_BLOCKENTITY` | `atan2`を約256 KiBの表参照で近似 | [AI Improvements](../mods/ai-improvements/OPTIMIZATIONS.md) | 1.20 Forge adjacent to ANCHOR | `FastTrig`, `FixedLookControl` | **PERFORMANCE_NOT_VERIFIED** | 精度・狙い・カスタムLookControl互換性を再検証 | CONCEPT_ONLY |
| `AI-FILTER-HIT-ORDER` | `TICK_SIMULATION`, `CACHE_DATA_STRUCTURE` | 頻出フィルタを前に寄せる | [AI Improvements](../mods/ai-improvements/OPTIMIZATIONS.md) | 1.20 Forge adjacent to ANCHOR | `FilterLayer`, `ModifierLayer` | **PERFORMANCE_NOT_VERIFIED** | 順序変更・副作用・宣言だけの設定を確認 | EXPERIMENT_CANDIDATE |
| `AI-EVENT-HOOK-DEDUP` | `TICK_SIMULATION`, `ENTITY_BLOCKENTITY` | 重複スポーンイベント処理を削除 | [AI Improvements](../mods/ai-improvements/FAILURE-REPAIR-HISTORY.md) | historical 1.19/1.20 source ancestry | [diff 2e95e6e](https://github.com/BuiltBrokenModding/AI-Improvements/commit/2e95e6e62edeea7cfd86a06865d5cebaf190ab39) | **PERFORMANCE_NOT_VERIFIED** | エンティティ初期化が漏れないことを検証 | CONCEPT_ONLY |
| `AI-PATH-REPATH-THROTTLE` | `TICK_SIMULATION`, `ENTITY_BLOCKENTITY` | ターゲット距離・経路末端の精度で再探索を間引く | [旧Epic Siege Mod 1.12比較](https://github.com/da3dsoul/Epic-Siege-Mod/commit/a51465f74452f74e8b605625986b980d47fe1994) / [既存解析](https://github.com/genkimorimori252525-oss/KNEEKURA-TECH-HUB/blob/research/nesm-jar-and-ai-perf-2026-10-11/departments/minecraft/mods/epic-siege-mod/FAILURE-REPAIR-HISTORY.md) | **HISTORICAL 1.12**, not Forge 1.20.1 | `ESM_EntityAIAttackMelee/Ranged/Target` repair diff | **PERFORMANCE_NOT_VERIFIED** | 対象急変・遮蔽物変更時の遅延と反応を測る | COMPARATIVE_ONLY |
| `AI-PATH-TYPE-RAW-CACHE` | `CACHE_DATA_STRUCTURE`, `ENTITY_BLOCKENTITY`, `MIXIN_BYTECODE` | `WalkNodeEvaluator`で未加工path typeを短寿命にキャッシュ | [Improved Mobs 1.20.1ソース](https://github.com/Flemmli97/ImprovedMobs/blob/029b8c20302a76bac1af9f5140e2abb6f73fea5c/common/src/main/java/io/github/flemmli97/improvedmobs/mixin/pathfinding/performance/WalkNodeEvaluatorMixin.java) / [調査資料](https://github.com/genkimorimori252525-oss/KNEEKURA-TECH-HUB/blob/research/improved-mobs-2026-10-11/departments/minecraft/mods/improved-mobs/PATHFINDING-AND-SIEGE-AI.md) | **ANCHOR 1.20.1 Forge** source commit `029b8c20` | Mixins for `getBlockPathType`, clear cache in `done()` | **PERFORMANCE_NOT_VERIFIED** | 変更後のキャッシュ破棄、他の最適化Mixinとの競合 | COMPARATIVE_CONCEPT |
| `RENDER-CHUNK-WORK-BUDGET` | `RENDERING_CHUNK, THREADING_CONCURRENCY` | Cap concurrent chunk mesh tasks per worker and heap | [embeddium](../cohorts/2026-10-11-forge-1.20.1/PHASE-1-TECHNIQUES.md) | ANCHOR-source Forge 1.20.1 | ChunkBuilder queue 2/worker, 64 MiB worker budget | **PERFORMANCE_NOT_VERIFIED** | Stale mesh, delayed updates | CONCEPT_ONLY |
| `RENDER-GPU-OCCLUSION-MAPS` | `CULLING_LOD, RENDERING_GPU` | Depth targets + entity/chunk visibility maps | [BruteForceRenderingCulling](../cohorts/2026-10-11-forge-1.20.1/PHASE-1-TECHNIQUES.md) | ANCHOR-source Forge 1.20.1 | CullingStateManager source+map lifetimes | **PERFORMANCE_NOT_VERIFIED** | False negative visible geometry, shaders | EXPERIMENT_CANDIDATE |
| `RENDER-ENTITY-AABB-CULLING` | `CULLING_LOD, THREADING_CONCURRENCY` | Threaded AABB occlusion with exceptions/whitelist | [EntityCulling](../cohorts/2026-10-11-forge-1.20.1/PHASE-1-TECHNIQUES.md) | 1.20 branch source | CullTask runnable and handled exceptions | **PERFORMANCE_NOT_VERIFIED** | Off-thread CME, stale result, missing boss | RISK_HEAVY |
| `RENDER-LEAVES-TESSELATION-SKIP` | `RENDERING_CHUNK` | Skip hidden leaves during model tesselation | [CullLeaves](../cohorts/2026-10-11-forge-1.20.1/PHASE-1-TECHNIQUES.md) | MULTIVERSION source | MixinBlockModelRenderer conditional cancel | **PERFORMANCE_NOT_VERIFIED** | Wrong foliage faces, transformed 1.20.1 target | CONCEPT_ONLY |
| `RENDER-LAYER-BATCHING` | `RENDERING_GPU` | Batch and reuse buffer by RenderLayer | [ImmediatelyFast](../cohorts/2026-10-11-forge-1.20.1/PHASE-1-TECHNIQUES.md) | 1.20 source branch | BatchingBuffer / source layer buffers | **PERFORMANCE_NOT_VERIFIED** | GL state order, transparency, text | CONCEPT_ONLY |
| `RENDER-OCCLUSION-SIDE-GUARD` | `RENDERING_CHUNK` | Side/direction culling of occlusion cache | [Bocchium](../cohorts/2026-10-11-forge-1.20.1/PHASE-1-TECHNIQUES.md) | 1.20.1 source candidate | BlockOcclusionCacheMixin.shouldDrawSide | **PERFORMANCE_NOT_VERIFIED** | False missing faces, Sodium/Embeddium API | CONCEPT_ONLY |
| `PARTICLE-SAFE-ASYNC-SPLIT` | `THREADING_CONCURRENCY` | Async busy particle sheets, sync error fallback | [particle-core](../cohorts/2026-10-11-forge-1.20.1/PHASE-1-TECHNIQUES.md) | 1.20.1 Forge source candidate | ParticleManagerAsyncMixin | **PERFORMANCE_NOT_VERIFIED** | Chunk palette and RNG races | RISK_HEAVY |
| `CACHE-COLOR-MOD-HOOKS` | `CACHE_DATA_STRUCTURE` | Allow other Mods to invalidate sky/lightmap caches | [BadOptimizations](../cohorts/2026-10-11-forge-1.20.1/PHASE-1-TECHNIQUES.md) | 1.20.1 source | CacheHooks common/lightmap/skycolor callbacks | **PERFORMANCE_NOT_VERIFIED** | Stale gamma, missing dynamic colors | CONCEPT_ONLY |
| `MEMORY-BLOCKSTATE-FASTMAP` | `MEMORY, CACHE_DATA_STRUCTURE` | Compact mixed-radix blockstate property map | [ferritecore](../cohorts/2026-10-11-forge-1.20.1/PHASE-1-TECHNIQUES.md) | 1.20 Forge adjacent | FastMap valueMatrix | **PERFORMANCE_NOT_VERIFIED** | Lost property transitions, memory overhead | CONCEPT_ONLY |
| `MEMORY-BAKED-QUAD-INTERN` | `MEMORY, ALLOCATION_GC` | Deduplicate vertex integer arrays | [ferritecore](../cohorts/2026-10-11-forge-1.20.1/PHASE-1-TECHNIQUES.md) | 1.20 Forge adjacent | Deduplicator + issue 129 fix 2aa56a | **PERFORMANCE_NOT_VERIFIED** | Hash collisions, model reload leaks | CONCEPT_ONLY |
| `STARTUP-LAZY-DFU` | `STARTUP_CLASSLOADING` | Defer DataFixerUpper class loading until required | [modernfix](../cohorts/2026-10-11-forge-1.20.1/PHASE-1-TECHNIQUES.md) | 1.20 source branch | DataFixersMixin + repair ae8cfbaa | **PERFORMANCE_NOT_VERIFIED** | Litematica classloading/Mixin side effects | GUARDED_CONCEPT |
| `CACHE-STRUCTURE-RADIUS-REJECT` | `CHUNK_WORLDGEN_IO` | Prove no stronghold ring possible outside safe bound | [modernfix](../cohorts/2026-10-11-forge-1.20.1/PHASE-1-TECHNIQUES.md) | 1.20 source branch | ConcentricRingsStructurePlacementMixin BETA | **PERFORMANCE_NOT_VERIFIED** | Incorrect worldgen positions if bounds too strict | EXPERIMENT_CANDIDATE |
| `RECIPE-SAFE-PARALLEL-PARTITION` | `THREADING_CONCURRENCY, RESOURCE_DATA` | Classify safe recipes for parallel find + serialized fallback | [fastsuite](../cohorts/2026-10-11-forge-1.20.1/PHASE-1-TECHNIQUES.md) | Forge 1.20 branch | AuxRecipeManager / CachedRecipeList | **PERFORMANCE_NOT_VERIFIED** | Non-thread-safe mod recipes, timeout changes result | RISK_HEAVY |
| `SERVER-ENTITY-ACTIVATION-GUARDS` | `TICK_SIMULATION, ENTITY_BLOCKENTITY` | Skip distant entity ticks with active combat exemptions | [servercore](../cohorts/2026-10-11-forge-1.20.1/PHASE-1-TECHNIQUES.md) | ANCHOR-source 1.20.1 | ActivationRange + fix commit 2238660 | **PERFORMANCE_NOT_VERIFIED** | Raid mob freezing, farm semantics | CONCEPT_ONLY |
| `SERVER-ADAPTIVE-MSPT-THRESHOLD` | `TICK_SIMULATION` | 20-tick adaptive view, simulation & mobcap control | [servercore](../cohorts/2026-10-11-forge-1.20.1/PHASE-1-TECHNIQUES.md) | ANCHOR-source 1.20.1 | DynamicManager target MSPT ±5 | **PERFORMANCE_NOT_VERIFIED** | Changed spawn and combat difficulty | BEHAVIOR_CHANGE |
| `REDSTONE-NONRECURSIVE-QUEUE` | `TICK_SIMULATION, CACHE_DATA_STRUCTURE` | Iterative deterministic redstone update queue | [alternate_current](../cohorts/2026-10-11-forge-1.20.1/PHASE-1-TECHNIQUES.md) | Forge branch source | WireHandler queue, dedupe, cached Node | **PERFORMANCE_NOT_VERIFIED** | Signal/order-dependent contraptions | CONCEPT_ONLY |
| `LIGHTING-SWMR-NIBBLES` | `LIGHTING, THREADING_CONCURRENCY` | Split updating/visible nibble arrays | [starlight](../cohorts/2026-10-11-forge-1.20.1/PHASE-1-TECHNIQUES.md) | Forge archived source | SWMRNibbleArray volatile visibility | **PERFORMANCE_NOT_VERIFIED** | Sky/block light chunk boundary races | CONCEPT_ONLY |
| `XP-ORB-CONSERVED-CLUMP` | `ENTITY_BLOCKENTITY` | Merge XP orbs and retain per-value counts in NBT | [clumps](../cohorts/2026-10-11-forge-1.20.1/PHASE-1-TECHNIQUES.md) | ANCHOR-source 1.20.1 | MixinExperienceOrb clumpedMap | **PERFORMANCE_NOT_VERIFIED** | Mending, pickup and save-load parity | CONCEPT_ONLY |
| `WORLDGEN-DIRECT-PALETTE` | `CHUNK_WORLDGEN_IO` | Direct palette writes with manual counters | [noisium](../cohorts/2026-10-11-forge-1.20.1/PHASE-1-TECHNIQUES.md) | 1.20.1 source archived | NoiseChunkGeneratorMixin | **PERFORMANCE_NOT_VERIFIED** | Palette/light/ticking counters invariants | EXPERIMENT_CANDIDATE |

## Technique ID examples

- `RENDER-CHUNK-MESH-BATCHING`
- `MEMORY-STATE-INTERNING`
- `GC-TEMP-OBJECT-ELIMINATION`
- `TICK-SPATIAL-CULLING`
- `LIGHT-QUEUE-PACKING`
- `CHUNK-ASYNC-IO`
- `STARTUP-LAZY-INITIALIZATION`
- `CACHE-GENERATION-INVALIDATION`

IDは実際の研究で確定する。上記は命名例。

## Cross-lane linking

通常MODや古文MODから技術を発見した場合:

```text
Source target = 元解析へのlink
Technique row = optimization側の索引
```

として、解析本文をコピーしない。

## Comparison dimensions

同カテゴリ技術は可能なら以下で比較する。

- optimized operation
- asymptotic / constant-factor change
- memory tradeoff
- invalidation complexity
- thread-safety
- fallback
- compatibility risk
- observed workload
- benchmark metric
