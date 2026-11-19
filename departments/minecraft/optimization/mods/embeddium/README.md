# Embeddium — bounded chunk meshing scheduling and memory guard (slice 2B)

Date 2026-10-11. Listed `embeddium-0.3.31+mc1.20.1.jar` is **NOT_ACQUIRED**, SHA-256 and binary equivalence unknown.

Pinned ANCHOR-adjacent source: [`FiniteReality/embeddium@dee0ebde6aea8b158613cd3b8ea5cdf0c1f6a9bf`](https://github.com/FiniteReality/embeddium/tree/dee0ebde6aea8b158613cd3b8ea5cdf0c1f6a9bf), branch `20.1/forge`. Recursive source path index **552 blobs / 499 Java**, untruncated; selected `ChunkBuilder`, `ChunkJobQueue`, and historical diff reviewed. This is not full acquired source-body coverage nor proof exact 0.3.31 release. FRONTIER latest NeoForge separate, not yet reviewed.

Categories `RENDERING_CHUNK`, `RENDERING_GPU`, `THREADING_CONCURRENCY`, `MEMORY`, `CACHE_DATA_STRUCTURE`. Performance & visual compatibility: **NOT_RUN / PERFORMANCE_NOT_VERIFIED**.

## E-01 — chunk mesh build worker count bounded by heap

[`ChunkBuilder.java`](https://github.com/FiniteReality/embeddium/blob/dee0ebde6aea8b158613cd3b8ea5cdf0c1f6a9bf/src/main/java/me/jellysquid/mods/sodium/client/render/chunk/compile/executor/ChunkBuilder.java):
- `MBS_PER_CHUNK_BUILDER=64`; `getMaxThreadCount()` uses minimum of available CPU processors and `max(1, heapMiB/64)`.
- When configured worker count 0 (auto), `getOptimalThreadCount()` clamps a cores-derived heuristic within `[1,10]`. Nonzero user preference capped at memory+CPU-derived limit.
- Worker threads receive individual `ChunkBuildContext`; `WorkerRunnable` comments that thread-local context avoids synchronization overhead.
- Semantics: bounds potential temporary heap resource consumption and avoids overlarge parallel meshing; **not a throughput gain measurement**.

## E-02 — chunk job scheduling pressure and clean shutdown

[`ChunkBuilder.java`](https://github.com/FiniteReality/embeddium/blob/dee0ebde6aea8b158613cd3b8ea5cdf0c1f6a9bf/src/main/java/me/jellysquid/mods/sodium/client/render/chunk/compile/executor/ChunkBuilder.java) `TASK_QUEUE_LIMIT_PER_WORKER=2`; `getSchedulingBudget()` reports `max(0,workers*2 - queue.size)`. [`ChunkJobQueue.java`](https://github.com/FiniteReality/embeddium/blob/dee0ebde6aea8b158613cd3b8ea5cdf0c1f6a9bf/src/main/java/me/jellysquid/mods/sodium/client/render/chunk/compile/executor/ChunkJobQueue.java) manages priority jobs through semaphore and queue; shutdown stops accepting jobs, wakes blocked workers, then builder waits for thread termination.

- **Guard**: explicit scheduling budget and cancellation; **a caller must heed that budget**. It is not a hard-coded unbreakable queue-size maximum.
- **Fallback:** canceled/obsolete outputs should be dropped instead of uploaded after the target render section was modified/unloaded. Exact full render pipeline side effect audit incomplete.
- **Correctness**: changes to geometry/visibility must not lead to stale chunks, missing meshes, crashes after world unload or unbounded queue growth.
- **Memory**: thread-owned context and task backlog can retain heap until shutdown or queue drain. Test repeated world reopen/shader reload.
- Compatible GL backend/extensions and modded renderer integrations not established by the selected two files.

## Repair history and scope

Upstream [commit `5866c29da7b6...`](https://github.com/FiniteReality/embeddium/commit/5866c29da7b66b0acc2f194f9c9ef1fe3f733713), parent `5b643cd136d1579cb0b7c8dcc6ddbd6acc4e61d6` (2023-07-30), fixes chunk job cancellation/empty queue tasks; diff replaces section job references with cancel tokens, adds result queue, checks frame/submission time to avoid obsolete output being accepted. Different-era source has changed classes and method mappings; not a release-specific 0.3.31 verification.
[Issue #192](https://github.com/FiniteReality/embeddium/issues/192) reports Minecraft 1.20.1 Forge 47.2.20 / Embeddium 0.3.0 crash with TFC and Oculus. This is another version and modpack; no linked repair reviewed.

## Next proof

Full source and dependency closure, OpenGL shader/render pass + modded geometry classmaps, licensed origin audit, exact JAR pin, benchmark chunk build tasks, stalled queues under fast camera flight and repeated chunks, GPU upload sync, FPS p95/p99 and correctness screenshots for standard block entities, transparency/shaders. No launcher/runtime tests here.
