# FastSuite — Phase 1 source/repair audit (2026-10-11)

**SourceSnapshot:** [Shadows-of-Fire/FastSuite `1.20` @ `883aed9f39f6b83225cbf20ca9d59f1c98239278`](https://github.com/Shadows-of-Fire/FastSuite/tree/883aed9f39f6b83225cbf20ca9d59f1c98239278). Observed recursive source tree 28 blobs, 9 Java classes; selected implementation files read. User requested `FastSuite-1.20.1-5.1.2.jar`; code is a *Forge 1.20 branch candidate*, not yet proven distribution identical. `LICENSE`: MIT. Source artifact parity and runtime NOT_RUN.

**Mechanism (selected code, EVIDENCE_BACKED_STATIC)**:
1. `AuxRecipeManager.getRecipeFor/getRecipesFor` checks recipe count and allowlisted single-threaded recipe types; below threshold it delegates to Vanilla `RecipeManager`. Config has `unsafeMode` separate from safe split.
2. `CachedRecipeList` partitions recipes by type: known-safe vanilla recipe class and ingredient classes may be searched in parallel, unknown mod classes are **serialized**. Uses per-recipe-type cached list and cache of class eligibility.
3. `parallelStream().filter(...).findFirst()` for safe entries followed by **serial search**, with `lockAllStacks(inv,true)` before and cleanup `finally`.
4. `StreamUtils.executeUntil` has timeout path returning Optional.empty/list fallback (not guaranteed an equivalent exhaustive search). Unknown recipe custom sync interactions may still exist despite class package heuristic.

**Semantics/risks:**
- Some recipe authors use hidden mutable caches or tie-break matching order, even when class package passes known-safe heuristic. Multiple matches and output priority can change under parallel `findFirst` ordering. No equivalent result-set claim.
- Timeout can return no recipe even though one matches. `ItemStack` locking and memory visibility must be checked with Forge loader and other mods.
- Class/ingredient blacklist/invalidation of recipe cache on datapack reload/reload world remains to be verified end-to-end.
- Paired benchmark must measure recipe-type count, recipe lookup median/p95, parallel pool contention, multicore behavior and observable crafting output under reload.

**Issue triage (not a confirmed MOD bug):** [FastSuite #47](https://github.com/Shadows-of-Fire/FastSuite/issues/47) reported rare frozen server with ATM10. Maintainer explicitly states there are no FastSuite errors in logs and suspects **MiniHUD**; reporter later says removing one of MiniHUD/JEI/MEI affected reproduction. **Do not attribute this freeze to FastSuite**, and no actual fix diff is linked. History state: BOUNDED_REPORT_REVIEWED / NO_SUPPORTED_FASTSUITE_CAUSAL_CASE.

**Source:** [AuxRecipeManager.java](https://github.com/Shadows-of-Fire/FastSuite/blob/883aed9f39f6b83225cbf20ca9d59f1c98239278/src/main/java/dev/shadowsoffire/fastsuite/AuxRecipeManager.java), [CachedRecipeList.java](https://github.com/Shadows-of-Fire/FastSuite/blob/883aed9f39f6b83225cbf20ca9d59f1c98239278/src/main/java/dev/shadowsoffire/fastsuite/CachedRecipeList.java).

**Facet:** selected mechanism EVIDENCE_BACKED_STATIC, path INVENTORIED, history PARTIAL, runtime/benchmark/source-to-JAR UNVERIFIED. Category `RESOURCE_DATA`, `THREADING_CONCURRENCY`, `CACHE_DATA_STRUCTURE`.
