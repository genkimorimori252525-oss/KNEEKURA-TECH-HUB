# Optimization A/B benchmark and semantic acceptance — NOT_RUN

Uses [lightweight genre BENCHMARK-SPEC](../../BENCHMARK-SPEC.md). All 58 provided items were Windows **paths**, not mounted JARs; no load, Java bytecode audit or runtime experiment performed.

## Paired comparisons only

A = Minecraft **1.20.1 Forge** baseline with exact pinned loader/dependencies/seed/config. B = same environment plus **one** optimization. C = same plus **one** possible competing optimization. Compare only same hardware/JVM/java/heap, driver, view/simulation distances, world, entities, warmup/cold-warm status and profiler identity. Measure repeated runs with recorded noise; no +X% based on static source.

| Workload ID | Candidate families | Metrics | Correctness/original behavior |
|---|---|---|---|
| `CLIENT_CHUNK_RENDER_STATIC` | Embeddium, BFRC, EntityCulling, CullLeaves, ImmediatelyFast, Bocchium, GPU Tape | frame median/p95/p99; CPU render, GPU time, VRAM, draw calls | all expected chunks/faces/entities visible, shaders/transparency/armor stands |
| `CLIENT_FAST_CAMERA_LOD` | Embeddium, BFRC, Distant Horizons | p99 frame, queue age, mesh rebuild count | no persistent occlusion holes or stale LOD |
| `CLIENT_PARTICLE_STRESS` | Particle Core, BadOptimizations | particles/s, GC allocation, frame p95/p99 | expected particle count, no off-thread RNG/palette crash |
| `WORLD_START_RELOAD` | ModernFix, FerriteCore, AllTheLeaks, MemoryLeakFix, SmoothBoot | launch/load, heap/RSS, allocation, GC, model bake | exact loaded models, correct schematic/NBT/DFU conversions, world cleanup |
| `SERVER_RAID_AI_MOBS` | ServerCore, Canary, AI Improvements, LetMeDespawn | MSPT median/p95/p99, entity tick counts, target reach | mobs still attack/route, wave counts; critical raid entity awake; no ghost despawn |
| `SERVER_CRAFT_MANY` | FastSuite, ModernFix | median/p95 recipe latency, pool contention | matching recipes, priority, NBT, resource reload |
| `SERVER_REDSTONE` | Alternate Current, Canary | block/neighbor update count, MSPT | same state machine & comparator/piston pulses; ordering-sensitive designs |
| `WORLDGEN_FIXED_SEED` | Noisium, Starlight, ModernFix | chunk throughput, MSPT/alloc | palette, lighting, biome/worldgen seed and save-reload parity |
| `SERVER_XP_ITEMS` | Clumps, GetItTogetherDrops | entity count, pickup latency/MSPT | conserved XP, Mending, save-load, item drops |
| `CLIENT_BACKGROUND` | Dynamic FPS | idle CPU/GPU, power, frame time | prompt foreground resume, network/audio stability |

**Critical combined tests:** render stack pairwise (Embeddium+ImmediatelyFast, BFRC+EntityCulling, CullLeaves+Bocchium, Distant Horizons); server workload AI overlays + ServerCore activation; FastSuite + custom recipes; FerriteCore+ModernFix+ModelGapFix/Chipped; redstone/lighting Noisium/Starlight/Alternate Current. No evidence of additive stacked improvements until measured.

**Correctness comes first:** no missing geometry, safe threads, equal XP/recipe outputs, matching tick state under promised equivalence, explicit notices for deliberately changed AI or visual LOD. Do not benchmark an all-on modpack and attribute gains to an individual MOD.

## Unfulfilled prerequisites

Exact JAR SHA-256 per user-supplied filename, dependency closure, mapped bytecode, mixin collision/priority profile, authorized isolated Minecraft lab world, target/modpack acceptance and cleanup receipts. **Current results: 0 tests / 0 benchmarks / all `PERFORMANCE_NOT_VERIFIED`.**
