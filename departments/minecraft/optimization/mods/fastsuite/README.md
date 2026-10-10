# FastSuite — recipe search concurrency (slice 2A)

User candidate: `FastSuite-1.20.1-5.1.2.jar`, not uploaded. Target ANCHOR: Minecraft **1.20.1 Forge**; selected source revision [`Shadows-of-Fire/FastSuite@883aed9f39f6b83225cbf20ca9d59f1c98239278`](https://github.com/Shadows-of-Fire/FastSuite/tree/883aed9f39f6b83225cbf20ca9d59f1c98239278) branch `1.20`, **28 blobs/9 Java** source path index (not truncated). JAR SHA and parity **UNESTABLISHED**. Source license [MIT](https://github.com/Shadows-of-Fire/FastSuite/blob/883aed9f39f6b83225cbf20ca9d59f1c98239278/LICENSE). Different 1.21.x repairs NOT automatically ANCHOR.

Categories: `THREADING_CONCURRENCY`, `RESOURCE_DATA`, `CACHE_DATA_STRUCTURE`, `TICK_SIMULATION`. Selected mechanism STATIC_EVIDENCE, **PERFORMANCE_NOT_VERIFIED**.

## FASTSUITE-RECIPE-GUARD — preclassified parallel / serial recipes

Source [`AuxRecipeManager`](https://github.com/Shadows-of-Fire/FastSuite/blob/883aed9f39f6b83225cbf20ca9d59f1c98239278/src/main/java/dev/shadowsoffire/fastsuite/AuxRecipeManager.java), [`CachedRecipeList`](https://github.com/Shadows-of-Fire/FastSuite/blob/883aed9f39f6b83225cbf20ca9d59f1c98239278/src/main/java/dev/shadowsoffire/fastsuite/CachedRecipeList.java), [`FastSuite`](https://github.com/Shadows-of-Fire/FastSuite/blob/883aed9f39f6b83225cbf20ca9d59f1c98239278/src/main/java/dev/shadowsoffire/fastsuite/FastSuite.java).

- Baseline: single-threaded recipe lookup.
- Eligibility guard: if recipe type has **fewer than 100** recipes, or is in `singleThreadedLookups`, delegates to original `RecipeManager`.
- Fast path: larger types use a lazily built `CachedRecipeList` separated by `isSafeRecipeClass/isSafeIngredient`; a parallel `parallelStream().findFirst()` evaluates allowlisted vanilla/Forge recipe classes first, and a **serial** loop processes unapproved recipes.
- Developer extension: explicitly register known thread-safe recipe and ingredient classes. `unsafeMode` bypasses validation but is **false by default**. `lockInputStacks` debug guard also **false by default**.
- Cache key: recipe type `RecipeType`, backing value = recipe partition. Lifecycle: `AuxRecipeManager` instance installed through `ServerResourcesMixin` and scoped to resource manager creation, with per-class thread-safety maps (synchronized identity maps).
- Concurrency owner: custom `ForkJoinPool` created in `StreamUtils.setup` with thread context classloader of caller. Worker count `max(4, availableProcessors-4)` in inspected source, not guaranteed performance-optimal on every CPU.
- Critical correctness: parallel search **order differs** from vanilla if multiple recipes match and results depend on registration order. `getRecipesFor` sorts output by item result description ID, but `getRecipeFor` first-match semantics and cache identity must be tested.
- Timeout behavior: [`StreamUtils.executeUntil`](https://github.com/Shadows-of-Fire/FastSuite/blob/883aed9f39f6b83225cbf20ca9d59f1c98239278/src/main/java/dev/shadowsoffire/fastsuite/StreamUtils.java) returns caller-provided **`Optional.empty()`** for recipe when exceeding timeout, not a verified automatic fallback to serial vanilla search. Thus timeout can change gameplay outcome in that call. This is a **source-based correctness risk**, not a measured outage. Worker cancellation behavior requires deeper source/runtime review.
- Exception: exceptions from the worker can propagate as runtime exception; thread dump available for diagnosis.
- Recipe cache invalidation on datapack reload: new `AuxRecipeManager` is created with new `ServerResources`, rather than universally clearing a global cache in-place; test resource reload version swaps and memory retention.

## Historical failures require track boundaries

A 2025 [commit `49971164e235...`](https://github.com/Shadows-of-Fire/FastSuite/commit/49971164e235bfc819a4cca896baa95575df9cf2) fixes `StackedContents` leaking/shared across threads for a **newer RecipeInput API**, by creating fresh `StackedContents` in `CraftingInputMixin`. This is FRONTIER/HISTORICAL comparative; not direct proof of 1.20.1 5.1.2 fix or vulnerability. [Issue #47](https://github.com/Shadows-of-Fire/FastSuite/issues/47) originally blamed FastSuite for thread freeze, but maintainer found no matching error and cited MiniHUD instead. **Do not record #47 as confirmed FastSuite bug.**

## Quality boundary

No custom TPS/speedup metrics were measured; build exact source parity, trust only proven-safe recipes for parallelism, test multiplayer/datapack reload/large 100+ recipes/ambiguous matching and thread race before any reuse. See [history](FAILURE-REPAIR-HISTORY.md).
