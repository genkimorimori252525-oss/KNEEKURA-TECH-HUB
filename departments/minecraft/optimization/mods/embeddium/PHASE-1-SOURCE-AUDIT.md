# Embeddium — Phase 1 source audit (2026-10-11)

**Snapshot:** `FiniteReality/embeddium` (redirected from `embeddedt/embeddium`), [branch `20.1/forge` commit `dee0ebde6aea8b158613cd3b8ea5cdf0c1f6a9bf`](https://github.com/FiniteReality/embeddium/tree/dee0ebde6aea8b158613cd3b8ea5cdf0c1f6a9bf). Full recursive path inventory 552 blobs, 499 Java sources. This is an **ANCHOR Forge 1.20.1 source lineage**, NOT yet a verified match to user-specified `embeddium-0.3.31+mc1.20.1.jar` or JAR bytecode. Separate new NeoForge branch `21.4/neoforge` is later upstream.

**Important directly read mechanism:** `src/main/java/me/jellysquid/mods/sodium/client/render/chunk/compile/executor/ChunkBuilder.java`:

- Allocates per-worker `ChunkBuildContext`, runs background chunk mesh workers with bounded queue; **`TASK_QUEUE_LIMIT_PER_WORKER = 2`**, **`MBS_PER_CHUNK_BUILDER = 64`** source constants.
- Calculates worker count based on available processors & Java heap; guards 1..10 optimum by formula; avoids overcommitting memory/queue as camera moves.
- Shutdown joins threads, releases resources; tries main-thread task steal for urgent requests, worker thread local context to reduce synchronization.
- Does not claim chunk builder is safe for arbitrary MOD block models: rendering callbacks, shader pipeline, CPU↔GPU upload and Forge hooks still need inspection.

**Other source-indexed leads** (not fully read): `RenderSectionManager`, `ChunkRenderMatrices`, `ChunkModelBuilder`, `MultiDrawBatch`, `LightDataCache` and compatibility wrappers. Different features and dependencies must be scoped, including with ImmediatelyFast, BFRC, EntityCulling, CullLeaves, Bocchium.

**Optimization contract:** cap work under peak camera motion and memory pressure, prioritize urgent visible chunks; drop obsolete work carefully and rebuild stale sections exactly once. **Correctness:** exact visible chunk/block faces and lighting, no missing models, same resource reload status; measure CPU render-thread time, GPU render time, median and p95/p99 frames, bytes allocated, VRAM and queue age at 1/10/50k chunk mesh updates.

**Facet:** FULL SOURCE PATHS INVENTORIED only (not bytes acquired for all 499), worker mechanism EVIDENCE_BACKED_STATIC, visual and Mixin surfaces not yet deeply reviewed, runtime/benchmark NOT_RUN, release JAR parity UNVERIFIED. License file location and any bundled Sodium/Embeddium component licenses still require a full rights audit.

[ChunkBuilder.java](https://github.com/FiniteReality/embeddium/blob/dee0ebde6aea8b158613cd3b8ea5cdf0c1f6a9bf/src/main/java/me/jellysquid/mods/sodium/client/render/chunk/compile/executor/ChunkBuilder.java).
