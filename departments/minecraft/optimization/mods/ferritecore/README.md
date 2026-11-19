# FerriteCore — Memory optimization source study (slice 2A)

Date 2026-10-11. User-named artifact: `ferritecore-6.0.1-forge.jar` — **NOT ACQUIRED** (Windows path, not uploaded). Source pin: [`malte0811/FerriteCore@e47bcbbde5b83805f927bad82bcc2b323e7169b8`](https://github.com/malte0811/FerriteCore/tree/e47bcbbde5b83805f927bad82bcc2b323e7169b8), historical branch `1.20.0`; official README, [summary](https://github.com/malte0811/FerriteCore/blob/e47bcbbde5b83805f927bad82bcc2b323e7169b8/summary.md), selected sources read. `1.20.0` is a **branch name**, not proof that this exact revision built the requested 1.20.1 Forge release.

## Track and admission

- **ANCHOR destination:** Minecraft 1.20.1 + Forge, requested 6.0.1 JAR; **exact released JAR SHA, build commit and bytecode PARITY UNKNOWN**.
- **ANCHOR-adjacent source:** fixed Git commit `e47bcbbde5b83805f927bad82bcc2b323e7169b8`; recursive source tree index 102 blobs, 67 Java files, `truncated=false`, **path inventory only**, not full byte acquisition.
- **FRONTIER:** separate newer source branch exists, unpinned/unread in this slice; **NOT_ANALYZED**.
- Primary categories: `MEMORY`, `CACHE_DATA_STRUCTURE`, `ALLOCATION_GC`; mechanism-only, **PERFORMANCE_NOT_VERIFIED**, correctness NOT_RUN.
- Source repository license [MIT](https://github.com/malte0811/FerriteCore/blob/e47bcbbde5b83805f927bad82bcc2b323e7169b8/LICENSE); no binary/source redistribution.

## Mechanism FERRITE-FASTMAP — packed BlockState property transitions

**Baseline:** vanilla BlockState neighbor lookup and per-state property bookkeeping can retain large maps. `FastMap<Value>` prebuilds one `valueMatrix` indexed by a mixed-radix composition of properties. `FastMapKey` maps each property choice into an index; `with(oldIndex, prop, value)` computes the replacement index and looks up the neighbor.

- **Source:** [`FastMap.java`](https://github.com/malte0811/FerriteCore/blob/e47bcbbde5b83805f927bad82bcc2b323e7169b8/Common/src/main/java/malte0811/ferritecore/fastmap/FastMap.java), `BinaryFastMapKey`, `CompactFastMapKey`.
- **Guard:** `with` returns null if property absent or new value invalid; caller-level Minecraft state semantics remain to be reviewed.
- **Allocation tradeoff:** preallocated indexed matrix instead of independently created adjacent-state maps; no memory gain magnitude stated as locally measured.
- **Compatibility risk:** mods extending/modifying `StateHolder` or expecting identity/layout assumptions; backport needs mappings check.
- **Persistence/cache:** immutable matrix for a given block/property set, initialized per structure; memory retention until owning maps/states die; invalidation on dynamic registry reload must be confirmed in live runtime.
- **Correctness:** `state.with(property, value)` result must equal expected neighbor across all valid combinations.

## Mechanism FERRITE-DEDUP-QUADS — canonical vertex arrays and cache reset

`Deduplicator.deduplicate(BakedQuad)` interns identical `int[]` vertex arrays using a custom hash-set with `Arrays.equals`, then installs the canonical array into the quad via access Mixin. `Deduplicator.registerReloadListener` clears and trims `BAKED_QUAD_CACHE`, multipart model and predicate/variant caches after model resource reload.

- Source [`Deduplicator.java`](https://github.com/malte0811/FerriteCore/blob/e47bcbbde5b83805f927bad82bcc2b323e7169b8/Common/src/main/java/malte0811/ferritecore/impl/Deduplicator.java); static collision/render cache dedup [`BlockStateCacheImpl`](https://github.com/malte081/FerriteCore/blob/e47bcbbde5b83805f927bad82bcc2b323e7169b8/Common/src/main/java/malte0811/ferritecore/impl/BlockStateCacheImpl.java).
- **Guard:** exact vertex content equality rather than pointer equality; hashing only chooses candidate buckets. Resource reloading invalidates **those specific dedup caches**, not proof every cache in FerriteCore is cleared.
- **Risk:** interning increases hash/search cost under pathological near-collision arrays and assumes treated arrays are immutable after canonicalization; user-reported tri-mod regression and actual hash repair reviewed below.
- Performance: **PERFORMANCE_NOT_VERIFIED**; upstream `summary.md` memory figures are author-context claims, not measurements in this project.

## Failure / repair: actual source diff, not only issue closure

[Issue #129](https://github.com/malte0811/FerriteCore/issues/129) reports loading slowdown with ModelGapFix + Chipped; workaround reported `bakedQuadDeduplication=false`.
[Fix commit `2aa56a0def18`](https://github.com/malte0811/FerriteCore/commit/2aa56a0def18a94574bc4c0f6e1aea00db1709a5), parent `5087367f63289248b778c183e53c7d6a303d675d`, changes quad hash from `Arrays::hashCode` to a per-int MurmurHash3-based fold. Compared **actual before/after source**. The fix is present in selected source. Exact startup speed-up not replicated; see [failure history](FAILURE-REPAIR-HISTORY.md).

## Follow-up required for whole-target claim

Capture source tree bytes and CAS index, Forge 1.20.1 6.0.1 exact binary hash, remapping and all Mixins, validate block-state transitions with custom property cardinalities, model reload memory retention, and A/B heap retained+GC+startup. Report exact world/modpack, no fabricated MB savings.
