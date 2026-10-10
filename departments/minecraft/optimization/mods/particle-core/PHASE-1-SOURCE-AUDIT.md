# Particle Core — Phase 1 source/risk audit (2026-10-11)

**Snapshot:** `fzzyhmstrs/pc`, [`forge/1.20.1` commit `8ae835f2abe100ff7a39f2e582e1cfa71ba6004a`](https://github.com/fzzyhmstrs/pc/tree/8ae835f2abe100ff7a39f2e582e1cfa71ba6004a). 55 indexed blobs; selected 1.20.1 Forge implementation read. User filename `particle_core-0.3.3+1.20.1+forge.jar` exact binary not acquired, branch version parity not claimed. LICENSE MIT.

**Core mechanisms:**
- `ParticleManagerRenderDistanceMixin`: sets view-distance from config at `ParticleManager.render` and wraps `Particle.buildGeometry` to SKIP geometry when particle location lies out of range. `RENDERING_GPU` / `CULLING_LOD`. Correctness: acceptable particle appearance radius/fog boundaries and precision under different camera coords.
- `ParticleManagerAsyncMixin`: optional parallel particle sheet updates, threshold at **35% of configured max particle count per sheet** in selected code, asynchronously processes busy sheets with `CompletableFuture` and joins before finalizing. Other sheets run synchronously. Maintains a concurrent `unsafeParticles` class set and per-particle fallback to main/sync tick when detecting thread-unsafe RNG errors.
- On async catch/threshold of widespread error, attempts to disable async config. **None of these guards alone prove safety** from unsafe off-thread world/chunk palette reads. Async flag may default off depending on config profile not read: don't claim default on.

**Crucial version-aware upstream reports:** [Issue #47](https://github.com/fzzyhmstrs/pc/issues/47) reports **Fabric 1.21.11** `LegacyRandomSource` concurrent access in 0.3.2, not Forge 1.20.1. [Issue #65](https://github.com/fzzyhmstrs/pc/issues/65) currently open in 2026-09 reports chunk palette access `MissingPaletteEntryException` on async particles. These are **FRONTIER user reports / hypothesis**, not direct 1.20.1 runtime facts.

**Correctness:** exact particle count and visual results where expected; particles requiring RNG/chunks must not run off-thread unless safe; no missing crash/false-migration; dependency Mixin target 1.20.1 Forge must match loader implementation. Benchmark frames median/p95/p99, particles/s, allocations, async task count, main thread stalls, GC, with/without particle-heavy modpacks.

**Facet:** EVIDENCE_BACKED_STATIC for selected Mixins; paths INVENTORIED, failure history DISCOVERY_BOUND; runtime and benchmark NOT_RUN.

[Async Mixin](https://github.com/fzzyhmstrs/pc/blob/8ae835f2abe100ff7a39f2e582e1cfa71ba6004a/src/main/java/me/fzzyhmstrs/particle_core/mixins/ParticleManagerAsyncMixin.java) / [Render distance](https://github.com/fzzyhmstrs/pc/blob/8ae835f2abe100ff7a39f2e582e1cfa71ba6004a/src/main/java/me/fzzyhmstrs/particle_core/mixins/ParticleManagerRenderDistanceMixin.java).
