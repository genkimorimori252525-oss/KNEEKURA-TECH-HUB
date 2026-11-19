# FerriteCore — Phase 1 source/repair audit (2026-10-11)

**Scope:** `malte0811/FerriteCore` source **1.20.0 branch** immutable revision `e47bcbbde5b83805f927bad82bcc2b323e7169b8`, **102 Git blobs / 67 Java/Kotlin source files path-inventoried**. User requested `ferritecore-6.0.1-forge.jar` for Forge 1.20.1. The snapshot is a **Forge-adjacent comparative source**, **NOT matched** to exact release JAR. The JAR and SHA-256 are **not acquired**. Repo code license **MIT** (read `LICENSE`).

**Feature map from reviewed source:**

- `Common/src/main/java/malte0811/ferritecore/fastmap/FastMap.java`: transforms block-state property/value assignments into compact mixed-radix table indices; direct `with(oldIndex,property,value)` neighbor lookup avoids repeated map allocations and property object storage. Exact property uniqueness/state transitions must match vanilla.
- `Common/src/main/java/malte0811/ferritecore/impl/Deduplicator.java`: **interns/shared references** for model variants, multipart models, Boolean predicate combinations and `BakedQuad` vertex `int[]`. `ConcurrentHashMap` for some shared model keys and synchronized `ObjectOpenCustomHashSet<int[]>` for vertex arrays.
- Registers a reload listener that **clears and trims** deduplication caches when resource/model reload completes. Shared instances must not escape cleanup or get mutated after deduplication.

**Optimization evidence:** DIRECT_OBSERVATION of selected code paths only. Categories `MEMORY`, `CACHE_DATA_STRUCTURE`, `ALLOCATION_GC`. Expected decrease in duplicate heap objects; **measured heap/FPS/loading improvements NONE**, `PERFORMANCE_NOT_VERIFIED`.

**Failure/repair trace (actual diff + issue):**

- [Issue #129](https://github.com/malte0811/FerriteCore/issues/129) documents a reporter's Minecraft **1.20.1** ModelGapFix + Chipped combination: approximately **23 seconds** load without FerriteCore vs **70 seconds** with it, and user workaround `bakedQuadDeduplication=false`. These times are **reported, not KNEEKURA benchmark**.
- [Commit `2aa56a0def18a94574bc4c0f6e1aea00db1709a5`](https://github.com/malte0811/FerriteCore/commit/2aa56a0def18a94574bc4c0f6e1aea00db1709a5), parent `5087367f63289248b778c183e53c7d6a303d675d`, **diff read**. Changed hash of `BakedQuad` vertex integer array from `Arrays.hashCode` to stronger per-element MurmurHash3 combination while retaining exact `Arrays.equals`. Maintainer message explicitly associates it with #129. **Mechanism**: collision-resistant hash for near-equal quad arrays reduces expensive equality checks; **not** proof of measured fix success. Checked present pinned source's `betterIntArrayHash`.

**Correctness contract:** equivalent `BlockState.getValue/setValue` outcomes, equivalent model vertex indices and render geometry, reference lifetime safe through resource reload; no stale data. Measure live/retained heap, allocation/GC, model bake time, resource reload correctness and p95 frame time. For tests use Chipped+ModelGapFix with exactly pinned versions and no unrelated differences. Do not copy resource/source JAR into Git.

**Facet status:** source tree path INVENTORIED; selected data structures EVIDENCE_BACKED; failure repair diff EVIDENCE_BACKED_STATIC; binary/compile/run/benchmark NOT_ANALYZED; whole-target **IN_PROGRESS**.

**Locators:** [FastMap](https://github.com/malte0811/FerriteCore/blob/e47bcbbde5b83805f927bad82bcc2b323e7169b8/Common/src/main/java/malte0811/ferritecore/fastmap/FastMap.java), [Deduplicator](https://github.com/malte0811/FerriteCore/blob/e47bcbbde5b83805f927bad82bcc2b323e7169b8/Common/src/main/java/malte0811/ferritecore/impl/Deduplicator.java).
