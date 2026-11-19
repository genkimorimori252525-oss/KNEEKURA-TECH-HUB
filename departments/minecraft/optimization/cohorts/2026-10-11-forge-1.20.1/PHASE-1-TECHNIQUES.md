# Phase 1: source-backed mechanism map (selected targets)

**Method:** literal source reads and GitHub tree path indexes, original revisions pinned, on 2026-10-11. Nothing below is an in-game benchmark. For exact filename ↔ artifact correspondence see [manifest](INPUT-MANIFEST.json); binary hash still null.

| Optimization category | Target / source revision | Code-level finding | Semantic / compatibility boundary |
|---|---|---|---|
| RENDERING_GPU / THREADING | [Embeddium](../../mods/embeddium/PHASE-1-SOURCE-AUDIT.md) `dee0ebde` | per-worker chunk build context, queue budget 2 jobs/worker, memory-based cap | meshing is concurrent; old visible section must not disappear; Forge renderer callbacks and shader compat |
| RENDERING_GPU / CULLING_LOD | [Brute Force Rendering Culling](https://github.com/RogoShum/BruteForceRenderingCulling/blob/58c55dcfe3d0a90c471c8a8b2bfedb1bf52685b3/src/main/java/rogo/renderingculling/api/CullingStateManager.java) `58c55dcf` | depth texture targets, chunk & entity occlusion maps, view/frustum, historical-visibility grace | false negative = missing entities/chunks; resource lifecycle and shader depth state |
| RENDERING_GPU | [EntityCulling](https://github.com/tr7zw/EntityCulling/blob/dff7304bcbb9186bada0a8c4617dc584fb2c3ea1/Shared/src/main/java/dev/tr7zw/entityculling/CullTask.java) `dff7304b` | separate sleeping worker tests AABB occlusion and whitelists glowing/large/forced-visible actors | worker races with client chunk/entity collections; code catches CME/NPE, needs stale-result and visual regression |
| RENDERING_GPU | [CullLeaves](https://github.com/TeamMidnightDust/CullLeaves/blob/a9ffb5061ae4ed49a55d5fe93679ee1d4bbe389e/src/main/java/eu/midnightdust/cullleaves/mixin/MixinBlockModelRenderer.java) `a9ffb506` | cancellable leaf tesselation under hidden-leaf predicate | leaf alpha/fast/fancy graphics and multi-version preprocessor path (26.1 HEAD) |
| RENDERING_GPU / BUFFER_BATCH | [ImmediatelyFast](https://github.com/RaphiMC/ImmediatelyFast/blob/b66885773494bfad58c83a8eee7b2f41424d4d9b/common/src/main/java/net/raphimc/immediatelyfast/feature/batching/BatchingBuffer.java) `b6688577` | batching buffers per RenderLayer and guarded draw state | GL/RenderLayer ordering, GUI text/translucency and shaders |
| RENDERING_GPU / BLOCK_FACE | [Bocchium](https://github.com/MCTeamPotato/Bocchium/blob/57a2e920273422253dde64f2c3d907bca8679afe/src/main/java/com/teampotato/bocchium/mixin/BlockOcclusionCacheMixin.java) `57a2e920` | cancel Sodium `BlockOcclusionCache.shouldDrawSide` based on direction/elevation | modified visible face set, Embeddium/Sodium API exact mapping required |
| RENDERING_GPU / PARTICLES | [Particle Core](../../mods/particle-core/PHASE-1-SOURCE-AUDIT.md) `8ae835f2` | render-distance skip and configurable optional parallel particle simulation with detected unsafe-class fallback | RNG and chunk palette off-thread access; frontier issue reports |
| TICK / CACHE | [BadOptimizations](https://github.com/imthosea/BadOptimizations/blob/f1540411b21e8458d6d143d00f53743e7a9bc893/common/src/main/java/me/thosea/badoptimizations/hook/CacheHooks.java) `f1540411` | user-extensible lightmap/skycolor change predicates invalidate skipped updates | gamma/night vision/other mod overrides must call extra guards |
| MEMORY / DATA | [FerriteCore](../../mods/ferritecore/PHASE-1-SOURCE-AUDIT.md) `e47bcbbd` | compact blockstate `FastMap`, quad vertex/multipart deduplication, reload clears caches | memory and hashing vs loading time; resource reload mutation safety |
| STARTUP / DFU | [ModernFix](../../mods/modernfix/PHASE-1-SOURCE-AUDIT.md) `cf04b47d` | lazy DataFixerUpper, beta stronghold ring-bound early rejection | DFU class loading side effects, Litematica issue; structure generation exact positions |
| CRAFT / THREADING | [FastSuite](../../mods/fastsuite/PHASE-1-SOURCE-AUDIT.md) `883aed9f` | split recipe class by safety, cache lists, parallel-safe search, serial fallback, stack lock, timeout | thread-unsafe third-party recipes and match order; timeout may change no-match outcome |
| ENTITY | [Clumps](https://github.com/jaredlll08/Clumps/blob/d249b4d25478e6044b0951f01b729c17b5860456/common/src/main/java/com/blamejared/clumps/mixin/MixinExperienceOrb.java) `d249b4d2` | orb grouping and `Map<Integer,Integer>` retaining experience decomposition persisted in NBT | XP totals, pickup timing, Mending repairs, save/reload |
| ENTITY / ADAPTIVE LOAD | [ServerCore](../../mods/servercore/PHASE-1-SOURCE-AUDIT.md) `d1d0a02d` | entity activation guard, combat immunity, 20-tick MSPT ±5 adaptive view/sim/mobcap | can intentionally change mob behavior and spawning; raid battles must remain active |
| REDSTONE | [Alternate Current](https://github.com/SpaceWalkerRS/alternate-current/blob/ab87061f1d04c44bfd42ba219ca567f8709c2acc/src/main/java/alternate/current/wire/WireHandler.java) `ab87061f` | de-recursive wire propagation, fewer duplicate block/shape updates, deterministic queue and reusable nodes | ordering-dependent redstone contraptions require waveform equivalence |
| LIGHTING | [Starlight](https://github.com/PaperMC/Starlight/blob/c562a3a36e8f5ec0ad25a8fa530de0d9eadcc64a/src/main/java/ca/spottedleaf/starlight/common/light/SWMRNibbleArray.java) `c562a3a` | single-writer/multi-reader `SWMRNibbleArray`, `volatile` visibility, ThreadLocal byte pool | multi-chunk lighting consistency, skylight edges, cross-thread reads; archived |
| WORLDGEN / PALETTE | [Noisium](https://github.com/Steveplays28/noisium/blob/c640041c8c932b36753c0ccf43902ac8b0bd252d/common/src/main/java/io/github/steveplays28/noisium/mixin/NoiseChunkGeneratorMixin.java) `c640041c` | write generated noise `BlockState` directly into chunk palette storage, update nonempty/fluid/ticking counters manually | block palette correctness, worldgen seed/lighting invariants; archived |
| AI / GOALS | [AI Improvements](../../mods/ai-improvements/README.md) `89c89590` (historical source) | eligible Goal pruning and precomputed atan2 lookup in LookControl | **Gameplay changes** + accuracy; separate past study |

## Stage-1 path inventory only (not enough to assert mechanism)

- AllTheLeaks `pietro-lopes/AllTheLeaks@5f4157f5362ea6471601114f8695ae44b0a3e28e`: source folders contain `ClearLeakedLevelChunks`, `ResourceLocationDedupe`, `MemoryMonitor`, but callers and root causes not fully read.
- MemoryLeakFix `FxMorin/MemoryLeakFix@988f54c14db0d86e13dd5dcce284178b2278e581`: archived; mixin fixes indexed but mechanisms and release parity deferred.
- GPUTape `StarmanMine142/GpuTape@e57f961776195894ed23687f9c143fd6942b9d58`: FBO Mixin inventoried, exact GL state changes not yet analyzed.
- LetMeDespawn `frikinjay/let-me-despawn`: repository found but policy/loot writes not read deeply yet.
- Distant Horizons: code hosted on GitLab; source checkout and full LOD pipeline analysis pending.
- Canary and Saturn: published projects located, exact upstream source lineage not adequately pinned; do not substitute arbitrary fork.
- Smooth Boot Reloaded: official 1.20.1 0.0.4 JAR exists, public GitHub prior rewrite appears older (1.18.2), **source association unresolved**.

## Most important reusable lessons (no architecture adopted)

Cache only with **key, owner, upper memory bound, valid lifetime, invalidation trigger and fallback**.  
Concurrent optimization only with **confirmed safe data and correctness contract**.  
Culling only with **no false-negative visible objects** (or explicit/approved visual approximation).  
Adaptive tick suppression must preserve **combat/state transitions and documented semantic sacrifice**.  
Optimization alone never establishes full binary compatibility or measured gain.
