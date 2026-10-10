# ModernFix — lazy loading, memory and cross-mod gate (slice 2A)

Date: 2026-10-11. Listed JAR `modernfix-forge-5.27.66+mc1.20.1.jar` **NOT uploaded**, SHA-256 and source/binary parity **UNESTABLISHED**.

**Source ANCHOR-candidate:** [`embeddedt/ModernFix@cf04b47d10ac5c6a748b177ce0348a3b1e4a9871`](https://github.com/embeddedt/ModernFix/tree/cf04b47d10ac5c6a748b177ce0348a3b1e4a9871), branch `1.20`. Recursive path index 390 blobs / 339 Java files (`truncated=false`). **Only selected source bodies read**. Branch revisions may change after published JAR 5.27.66; pin is source evidence, not proof of that binary. **FRONTIER** older/newer loader not reviewed in this slice.

Category `STARTUP_CLASSLOADING`, `RESOURCE_DATA`, `MEMORY`, `CACHE_DATA_STRUCTURE`, `MIXIN_BYTECODE`, `CHUNK_WORLDGEN_IO`. Source license [LGPL-3.0-or-later](https://github.com/embeddedt/ModernFix/blob/cf04b47d10ac5c6a748b177ce0348a3b1e4a9871/LICENSE), original media/notebook hashes not imported. **Performance NOT_RUN**.

## MODERNFIX-LAZY-DFU — defer expensive DataFixerUpper initialization

**Sources:** [`DataFixersMixin`](https://github.com/embeddedt/ModernFix/blob/cf04b47d10ac5c6a748b177ce0348a3b1e4a9871/src/main/java/org/embeddedt/modernfix/common/mixin/perf/dynamic_dfu/DataFixersMixin.java), [`LazyDataFixer`](https://github.com/embeddedt/ModernFix/blob/cf04b47d10ac5c6a748b177ce0348a3b1e4a9871/src/main/java/org/embeddedt/modernfix/dfu/LazyDataFixer.java).

- **Baseline:** create Mojang DataFixerUpper during initialization even for sessions that do not require old-format NBT upgrade.
- **Mechanism:** return a `LazyDataFixer` implementing `DataFixer` initially; on `update(type,input,version,newVersion)` if `version >= newVersion`, return input unchanged; otherwise load actual backing DFU on demand. `getSchema` always initializes backing DFU. Backing creation synchronized on wrapper.
- **Fast path:** no data conversion required → skip building DFU.
- **Fallback:** actual Mojang DFU when upgrade/schema requested, preserving delegate behavior.
- **Cache/owner:** one lazy wrapper and one synchronized backing instance; lifecycle tied to static host datafix registration.
- **Correctness risk:** **early side effects and Mixins that depend on the eager loading of classes are not preserved** even though DataFixer API results may match.
- **Observed upstream repair:** [Issue #332](https://github.com/embeddedt/ModernFix/issues/332) shows Litematica old schematic conversion regression; [commit `ae8cfbaa3d88...`](https://github.com/embeddedt/ModernFix/commit/ae8cfbaa3d880a20b70a418f4ae276312fa30981) adds `disableIfModPresent("mixin.perf.dynamic_dfu","litematica")` to early config; same gate exists at selected source [ModernFixEarlyConfig.java](https://github.com/embeddedt/ModernFix/blob/cf04b47d10ac5c6a748b177ce0348a3b1e4a9871/src/main/java/org/embeddedt/modernfix/core/config/ModernFixEarlyConfig.java).
- **Not implied:** that all DataFixers are skipped, all old world loads improve, or KNEEKURA has benchmarked startup gains.

## MODERNFIX-COMPACT-PALETTE — reduce oversized empty chunk palette

Source [`PalettedContainerMixin`](https://github.com/embeddedt/ModernFix/blob/cf04b47d10ac5c6a748b177ce0348a3b1e4a9871/src/main/java/org/embeddedt/modernfix/common/mixin/perf/compact_bit_storage/PalettedContainerMixin.java).

After packet buffer `PalettedContainer.read`, if palette bit width `i>1` while storage raw longs are **all zero** and length >0, code attempts to read palette index 0 and rebuilds data with a minimal width, retaining that value.

- **Guard**: only all-zero storage; `valueFor(0)` failure caught/returns with old representation left.
- **Fast path**: replace excessively wide palette backing with compact data when all positions share one state.
- **Correctness concern**: needs exact compare of all chunk cells, lighting, serialization/reload, and known malformed palettes; **runtime NOT_RUN**.
- Does not establish all packet/chunk palette optimizations throughout the repository.

## Cross-mod gate matters

Early config explicitly disables certain separate fixes when conflicting mods are present: e.g. dynamic DFU vs Litematica, chunk deadlock fix vs C2ME/DimThread, compressed biome container vs some world editors/mods, some optimized code vs OptiFine. Gates are source-backed compatibility policy; **not a promise of global compatibility**.

Author project [CurseForge](https://www.curseforge.com/minecraft/mc-mods/modernfix) documents different game-version support; its default current-release page does not prove 5.27.66 behavior. Community co-install recommendations are reconnaissance only.

## Remaining review

Complete source tree/mixin inventory and CAS capture, exact requested release SHA and built-config parity; analyze startup/memory profiles before/after, DFU schema fidelity, packet/chunk tests, per-feature disable flags, regressions, client/server and mixin incompatibilities. `README` and [history](FAILURE-REPAIR-HISTORY.md) only cover selected source feature slices.
