# ModernFix — Phase 1 source/repair audit (2026-10-11)

**Scope:** `embeddedt/ModernFix` branch `1.20` @ immutable `cf04b47d10ac5c6a748b177ce0348a3b1e4a9871`, observed Git index **390 blobs / 339 Java/Kotlin**. Minecraft 1.20.1 Forge branch per README. User requested **5.27.66** JAR; branch HEAD is not tied to this exact binary/version. Source repo license LGPL-3.0; binary not acquired. TRACK: ANCHOR-candidate source, release-equivalence UNKNOWN.

**This is not one optimization.** The source separates `common/mixin/perf/` from `bugfix/` and other feature systems; each option has distinct performance and correctness guards. Do not enable all and call behavior identical.

**Selected evidence backed:**
- `src/main/java/org/embeddedt/modernfix/common/mixin/perf/dynamic_dfu/DataFixersMixin.java`: installs **LazyDataFixer** so heavy DFU classloading can be postponed until needed. Static mechanism; *measured* startup cost NOT_RUN.
- `src/main/java/org/embeddedt/modernfix/common/mixin/perf/cache_strongholds/ConcentricRingsStructurePlacementMixin.java`: **BETA** modification uses analytically derived radial bounds and a conservatively enlarged uncertainty allowance to avoid expensive structure position checks for chunks provably outside radius. Fallback to original when inside bounds. Bounds account for rounding and biome-snapping offsets; correctness requires never rejecting a legitimate placement.
- Tree also includes `perf/compact_bit_storage`, `perf/deduplicate_wall_shapes`, `perf/dynamic_dfu`, `perf/dedicated_reload_executor`, `perf/chunk_meshing` and `bugfix/chunk_deadlock`. **Names are inventory leads only** until full callers and startup/side tests reviewed.

**Failure and repair:** [Issue #332](https://github.com/embeddedt/ModernFix/issues/332) reports empty Litematica `.schematic` with Dynamic DFU enabled, fixed when disabled. Maintainer linked [commit `ae8cfbaa3d880a20b70a418f4ae276312fa30981`](https://github.com/embeddedt/ModernFix/commit/ae8cfbaa3d880a20b70a418f4ae276312fa30981), parent `675c58a437f68b42f9daa7bfc4b143d0003f7dba`: **diff directly read** adds `disableIfModPresent("mixin.perf.dynamic_dfu","litematica")`. Reported causal lead: loading DFU lazily changes class initialization/order that Litematica's Mixin expected. Maintainer says should be fixed 5.12.0; **exact version compatibility and runtime fix NOT_VERIFIED**.

**Core lesson:** "lazy load" can change **other MODs' injection/class-initialization side effects**; exclude known integrations before applying the fast path. Stronghold cache's proof bounds are different from heuristic rendering culling.

**Correctness:** ID/mapping of legacy NBT and schematic conversions must remain valid, worldgen structure placement/chunk hashes must match, model reload/render correctness. Startup cold and warm load benchmarks on fixed modpacks + binary JAR identity, multiple runs.

**Facet:** path INVENTORIED; selected two mechanisms EVIDENCE_BACKED_STATIC; source patch FIX_COMMIT_READ; runtime, other 300+ files, exact 5.27.66 parity UNVERIFIED.

[DataFixersMixin](https://github.com/embeddedt/ModernFix/blob/cf04b47d10ac5c6a748b177ce0348a3b1e4a9871/src/main/java/org/embeddedt/modernfix/common/mixin/perf/dynamic_dfu/DataFixersMixin.java) / [Stronghold bounds](https://github.com/embeddedt/ModernFix/blob/cf04b47d10ac5c6a748b177ce0348a3b1e4a9871/src/main/java/org/embeddedt/modernfix/common/mixin/perf/cache_strongholds/ConcentricRingsStructurePlacementMixin.java).
