# Particle Core — guarded async particle ticking (slice 2B)

Date: 2026-10-11; candidate `particle_core-0.3.3+1.20.1+forge.jar` — **NOT_ACQUIRED**, no JAR SHA/parity proof.

Source pin: [`fzzyhmstrs/pc@8ae835f2abe100ff7a39f2e582e1cfa71ba6004a`](https://github.com/fzzyhmstrs/pc/tree/8ae835f2abe100ff7a39f2e582e1cfa71ba6004a), branch `forge/1.20.1`; path inventory 55 blobs, untruncated; selected Kotlin/Java files inspected. Source [MIT](https://github.com/fzzyhmstrs/pc/blob/8ae835f2abe100ff7a39f2e582e1cfa71ba6004a/LICENSE). FRONTIER source and binary not compared.

**Category:** `RENDERING_GPU`, `TICK_SIMULATION`, `THREADING_CONCURRENCY`, `CACHE_DATA_STRUCTURE`. Mechanism source EVIDENCE_BACKED_STATIC, performance correctness **NOT_RUN**.

## P-01 — conditional async particle updates

Selected [`ParticleManagerAsyncMixin.java`](https://github.com/fzzyhmstrs/pc/blob/8ae835f2abe100ff7a39f2e582e1cfa71ba6004a/src/main/java/me/fzzyhmstrs/particle_core/mixins/ParticleManagerAsyncMixin.java): wraps `ParticleManager.tick` and `addParticle`.

- **Guard 1**: if `getAsynchronousTicking()` disabled, call original `Map.forEach` tick path unchanged.
- **Guard 2**: per-sheet queue count must exceed **35% of configured max particles per sheet** to schedule `CompletableFuture.supplyAsync`; small queues tick synchronously. Need actual effective config to know whether active by default.
- **Mechanism**: run eligible sheet particle updates in `parallelStream`; keep per-particle `TickResult`. Wait for all futures, process results and removals on caller path.
- **Fallback for some failures**: if `CrashException` cause indicates LegacyRandomSource or thread-local random ownership violation, add particle class to concurrent `unsafeParticles` and re-tick those instances on synchronous caller. If more than 2/3 of a sheet fail, disables async. A broader exception also disables async and logs error.
- **Concurrency**: `ConcurrentHashMap.newKeySet` for unsafe classes; particle additions wrapped in a `synchronized` block; `this.particles` map synchronized while futures are joined. Thread safety of **all world reads, block palettes, chunk status and custom particle extension code is NOT proven**.
- **Risk**: exception-based fallbacks cannot prevent every possible off-thread world mutation or data race; position, lighting or visual state may be inconsistent. Do not call it universally safe.
- **Perf status**: unmeasured CPU/render-time overhead of futures and fallback retries.

## P-02 — render-distance rejection and particle cache

[`ParticleManagerRenderDistanceMixin`](https://github.com/fzzyhmstrs/pc/blob/8ae835f2abe100ff7a39f2e582e1cfa71ba6004a/src/main/java/me/fzzyhmstrs/particle_core/mixins/ParticleManagerRenderDistanceMixin.java) checks position relative to camera **before `Particle.buildGeometry`** and skips geometry for excluded distant particles. Config stores/uses squared distance. Additional `CachedLight`, `CachedPos`, `VertexContainer` resources are **inventoried**, not comprehensively proven. Separate surface from async ticking.

## Contradictory / cross-version reports

- [#39](https://github.com/fzzyhmstrs/pc/issues/39): **Forge 1.20.1** 0.3.0 visual/particle size glitches as user report; exact repair code not linked or verified. This is relevant but not proof 0.3.3 reproduces it.
- [#47](https://github.com/fzzyhmstrs/pc/issues/47): **Fabric Minecraft 1.21.11**, 0.3.2 crashes when `LegacyRandomSource` accessed on wrong thread. Comparable semantic hazard, **not ANCHOR runtime evidence**.
- [#65](https://github.com/fzzyhmstrs/pc/issues/65): current report of `MissingPaletteEntryException` from async world palette access. Need precise version and root-cause confirmation; no matching Forge 1.20.1 claim.
- See [history](FAILURE-REPAIR-HISTORY.md).

## Next proof requirements

Exact Forge 1.20.1 JAR SHA/source parity, branch dependency closure and Mixin signatures, full Kotlin config semantics, source class lifecycle, controlled particle counts 0/100/1000/10000, animated/transparent effects, FPS/frame median/p95/p99 and client thread profiler, `async` enabled/disabled and unsafe modded particles, world save/close and chunk-unload races. No experiments run.
