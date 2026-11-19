# AllTheLeaks 1.1.1 for Forge 1.20.1 — per-issue memory retention and version-gated cleanup

Date: 2026-10-11. **Source `pietro-lopes/AllTheLeaks`, `1.20.1` branch pinned `5f4157f5362ea6471601114f8695ae44b0a3e28e`**, actual Git tree SHA `8d3fe6e1244e6bdd7cd80729fef70de8a254f6ea`, **373 blobs / 356 Java paths**, recursion not truncated; selected source bodies read, full body archive/CAS **not acquired**.

**ANCHOR** `gradle.properties`: Minecraft **1.20.1**, Forge dev **47.4.10**, mod version **`1.1.1+1.20.1-forge`**, exactly matches user basename `alltheleaks-1.1.1+1.20.1-forge.jar` at version/string level. **JAR itself NOT_UPLOADED, SHA-256 and source-binary class/mixin parity UNESTABLISHED**. **FRONTIER** 1.21.x [`a0e6f274`](https://github.com/pietro-lopes/AllTheLeaks/tree/a0e6f2749f367628043f9272cde2b7abaead539d) path-inventoried (306 blobs / 286 Java), **not source-body compared**. Source license **MIT** [`LICENSE.txt`](https://github.com/pietro-lopes/AllTheLeaks/blob/5f4157f5362ea6471601114f8695ae44b0a3e28e/LICENSE.txt). Static source mechanism evidence only, performance `PERFORMANCE_NOT_VERIFIED`.

## ATL-01 — per-MOD version and side-gated fixes, not blanket memory cleanup

[`IssueManager`](https://github.com/pietro-lopes/AllTheLeaks/blob/5f4157f5362ea6471601114f8695ae44b0a3e28e/src/main/java/dev/uncandango/alltheleaks/leaks/IssueManager.java) scans `@Issue` annotations in the load-time ModFileScanData and evaluates:
- Mod ID + mod version interval (using Forge/Apache version-range logic);
- required extra mods/versions, client or dedicated-server side, dev-only flags and user config;
- optional `modAbsent` and mixin cancel/allow lists;
- each matching fix is instantiated and its Mixins enabled, while nonmatching fix stays out.

This is a *feature capability matcher*, not proof every source class applies to 1.20.1 or is automatically enabled. Different from MemoryLeakFix's Minecraft-version-only gating; fundamentally its entrypoints are per **offending Mod+version**.

**Correctness:** a patch can become wrong once the original mod fixes its own bug. Precise version/side detection and disabling obsolete repairs is essential. Mixin cancellation creates compatibility touch points (e.g. ModernFix); don't reuse code blindly.

## ATL-02 — remove obsolete chunk holders by coordinating with server executor

[`ClearLeakedLevelChunks.execute()`](https://github.com/pietro-lopes/AllTheLeaks/blob/5f4157f5362ea6471601114f8695ae44b0a3e28e/src/main/java/dev/uncandango/alltheleaks/feature/common/mods/minecraft/ClearLeakedLevelChunks.java) obtains active server, calls `server.executeBlocking`, iterates dimensions and removes **null ticker wrappers for LevelChunks that are no longer `inLevel`** from blockEntityTickers. This targets references retaining unloaded chunks instead of clearing all ticking block entities.

- Guard: server exists; exact object is sentinel `LevelChunkAccessor.atl$getNullTicker()` and owner LevelChunk is not in level. Other tickers retained.
- Ownership: main server executor, avoids concurrent unsynchronized ticker edits.
- Cleanup: on invoked lifecycle path; **the source function alone is not proof when/how often it's actually called** (event caller remains a follow-up).
- Correctness risk: wrong sentinel or inLevel state could remove a live BlockEntityTicker; saved-world data, ticking continuity and unload/reload must be tested.

## ATL-03 — canonicalize recipes and identifiers with explicit memory tradeoff

[`IngredientDedupe`](https://github.com/pietro-lopes/AllTheLeaks/blob/5f4157f5362ea6471601114f8695ae44b0a3e28e/src/main/java/dev/uncandango/alltheleaks/feature/common/mods/minecraft/IngredientDedupe.java) uses `ObjectOpenCustomHashSet<Ingredient>` and exact Ingredient value comparisons to intern vanilla ingredients; **`@Issue(... config="ingredientDedupe", configActivated=false)` means this optimization is OFF by source default**, not part of any claimed default memory improvement. With ModernFix installed it adjusts equality semantics based on whether its own ingredient dedup Mixin is enabled. Interned objects are locked against modification (ItemStack/NBT related Mixins), a side-effect contract.

[`ResourceLocationDedupe`](https://github.com/pietro-lopes/AllTheLeaks/blob/5f4157f5362ea6471601114f8695ae44b0a3e28e/src/main/java/dev/uncandango/alltheleaks/feature/common/mods/minecraft/ResourceLocationDedupe.java) keeps synchronized strong `ObjectOpenCustomHashSet<String>` for namespaces and paths. Shared instances may cut repeated Strings; static unbounded strong caches **can trade temporary duplication for retained heap growth**, especially with many unique dynamic IDs. No arbitrary large memory reduction asserted.

## ATL-04 — tracking/heap dump and scoped Forge EventBus repair

[`MemoryMonitor`](https://github.com/pietro-lopes/AllTheLeaks/blob/5f4157f5362ea6471601114f8695ae44b0a3e28e/src/main/java/dev/uncandango/alltheleaks/feature/common/mods/minecraft/MemoryMonitor.java) collects stable memory summaries, leak-instance reports, event counts and can invoke `System.gc()` or diagnostic GC and heap dumps. Those are **measurement/diagnostics**, not proof leak repair; forced GC changes benchmark environment. Use paired heap snapshots and retained object reference paths.

[`leaks/common/mods/forge/Issue39.java`](https://github.com/pietro-lopes/AllTheLeaks/blob/5f4157f5362ea6471601114f8695ae44b0a3e28e/src/main/java/dev/uncandango/alltheleaks/leaks/common/mods/forge/Issue39.java) is annotated for Forge 47.2+ EventBus. For older EventBus, at `ServerStoppedEvent` it invokes listener cache reconstruction to clear stale unregistered listeners; first reads runtime EventBus Implementation-Version. **If EventBus >=6.2.26 it returns without installing workaround**. This check is actually present in source revision `5f4157f5362ea6471601114f8695ae44b0a3e28e` (2025-11). It is vital because Forge 47.4.16 uses EventBus 6.2.33 which already includes the upstream listener invalidation repair.

Source-backed external upstream [EventBus PR #65](https://github.com/MinecraftForge/EventBus/pull/65) merged 2025-01-22 replaces lazy stale listener array/invalidation with null-marking and reduces hot-path indirection. [ATL Issue #79](https://github.com/pietro-lopes/AllTheLeaks/issues/79) warns invoking workaround with new EventBus would itself eagerly create unused listeners; reporter later explicitly acknowledged **the constructor already had the check**. **Do not claim #79 caused a 2026 repair commit**, no such ATL diff inspected. Confirm needed versions at runtime.

## Relevant Twilight Forest subsystem and external evidence

[`UntrackedIssue001`](https://github.com/pietro-lopes/AllTheLeaks/blob/5f4157f5362ea6471601114f8695ae44b0a3e28e/src/main/java/dev/uncandango/alltheleaks/leaks/client/mods/twilightforest/UntrackedIssue001.java) has `@Issue(modId="twilightforest",versionRange="[4.3.2508,)",extraModDep="jei",extraModDepVersions="[15.8.2.24,)")`; on client render engines/level update, resets Hydra model state and clears the JEI Transformation Powder preview entity map via reflection. It is a **source-backed external compatibility memory-release concept** pertinent to KNEEKURA Techhub Twilight Forest study, NOT a universal known memory leak for every TF version.

**User reports with counterevidence:** [#70](https://github.com/pietro-lopes/AllTheLeaks/issues/70) exact mod 1.1.1 Forge 1.20.1 saw 80k retained chunks during Chunky pregeneration. Maintainer requested `spark heapsummary`; author/user traced possible **Fast Async World Save / Smooth Chunk Save** lack of world saves, *not shown to be a bug in AllTheLeaks*. [#99](https://github.com/pietro-lopes/AllTheLeaks/issues/99) further 1.20.1 memory growth, force refresh didn't clear; root unverified. Both are leads, not performance/causal proof.

## Quality gate

Full 356 source bodies incl per-mod issues not read, CAS not captured, exact binary bytecode not compared, and no Forge Minecraft world or heap/MSPT benchmarks. Test singleplayer/server session 30+ world loads, return to main menu, dimension transition, chunk pregen with controlled saving, heap retained dominated nodes, and GC under fixed flags; ensure server runs listeners/tickers as expected. No performance % or memory delta invented.
