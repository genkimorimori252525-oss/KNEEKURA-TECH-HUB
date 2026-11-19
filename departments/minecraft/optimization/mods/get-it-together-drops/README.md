# Get It Together, Drops! 1.3 — item merge radius / tag-based policy (historical source comparison)

Target supplied file **`getittogetherdrops-forge-1.20-1.3.jar`**. The [official Forge distribution](https://www.curseforge.com/minecraft/mc-mods/get-it-together-drops/files/4578649) uploaded 2023-06-10 is **declared compatible with Minecraft 1.20 and 1.20.1**; version 1.3. **This exact 1.20 Forge source commit was not found in official public GitHub history.** The author's [2023-11-10 NeoForge 1.20.2 update](https://github.com/bl4ckscor3/GetItTogetherDrops/commit/095d051034bbd8560f1bc5794a5ab1517ac822b5) explicitly says “forgot to commit and push 1.20”; therefore treating public `1.19` branch as the literal 1.20 Forge JAR source would be incorrect.

**Source COMPARATIVE only:** [bl4ckscor3/GetItTogetherDrops@`5adec7a58162d9762feeb1348eb11ce349638ae6`](https://github.com/bl4ckscor3/GetItTogetherDrops/tree/5adec7a58162d9762feeb1348eb11ce349638ae6) branch `1.19`, compiler Java17 Minecraft **1.19.2 Forge43.1.47**, version source `1.3`, git tree `75dcb0778d9a561b5151cbdd4f1d8134a73b4eb5`, **16 blobs/3 Java**, all three Java bodies read. Exact requested **JAR not uploaded**, no SHA256 / bytecode parity, effective 1.20.1 values UNKNOWN. Source license [MIT](https://github.com/bl4ckscor3/GetItTogetherDrops/blob/5adec7a58162d9762feeb1348eb11ce349638ae6/LICENSE). `FRONTIER` 26.3+ entirely different platform not analyzed.

## GITD-01 — ItemEntity neighborhood merger with explicit exemptions

In [`ItemEntityMixin.mergeWithNeighbours`](https://github.com/bl4ckscor3/GetItTogetherDrops/blob/5adec7a58162d9762feeb1348eb11ce349638ae6/src/main/java/bl4ckscor3/mod/getittogetherdrops/mixin/ItemEntityMixin.java), a `@Inject` before vanilla `isMergable()` runs on item entities:
- **IGNORED** tag: don't intercept; let vanilla merge behavior proceed.
- **DO_NOT_COMBINE** tag: cancel vanilla merge and don't combine item at all.
- Default: query nearby `ItemEntity` instances within `boundingBox.inflate(radius, checkY ? radius : 0, radius)`, then `tryToMerge` each still-valid neighbor until this item is removed. End by canceling vanilla handler.
- [`GetItTogetherDropsConfig`](https://github.com/bl4ckscor3/GetItTogetherDrops/blob/5adec7a58162d9762feeb1348eb11ce349638ae6/src/main/java/bl4ckscor3/mod/getittogetherdrops/GetItTogetherDropsConfig.java) declares comparative source defaults **radius 2.0** (vanilla 0.5), **checkY true**, maximum radius **500**. An optional expanded vertical search changes merging behavior; it is not free performance.
- Tags `getittogetherdrops:ignored` and `getittogetherdrops:do_not_combine` are defined on ItemTags; config registered as **Forge SERVER config**. Mod descriptor allows missing client (server optimization candidate).

**Baseline:** vanilla nearby same ItemStack merges only at narrow range; many matching drops can remain separately ticking. **Fast path:** larger spatial query may combine stacks sooner, potentially reduce entity count, but for extremely large `radius` scanning nearby candidates could raise `O(number of nearby entities)` overhead for *each* item; gains are workload-dependent. **Game semantics:** preserve item identity, NBT/custom cap, owner/pickup delay, stack max, item retention and exact combined amount; vanilla `tryToMerge` does much of the guarding but only for comparison source. No measured MSPT.

## Integration lesson from earlier Techhub research

**Distinct from Clumps:** [Clumps](../clumps/README.md) aggregates **ExperienceOrbs** and preserves XP per-value data for Mending. This mod acts on **ItemEntity** only. Combining them does not mean they patch the same entity or guarantee additive improvements.

**With Let Me Despawn:** [LMD comparative mechanism](../let-me-despawn/README.md) can return equipment as ItemEntity when a mob despawns. Item merger may then act on new drops; inventory conservation, player ownership, no double-drops are correctness sidecars. This is a plausible **cross-mod scenario**, not proof of an existing conflict.

## Failure/history window

Searched official issue terms `merge`, `radius`, `duplicate`, `do not combine`. [#9](https://github.com/bl4ckscor3/GetItTogetherDrops/issues/9) proposed radius below 0.5, **not evidence of a bug/fix**. [#10](https://github.com/bl4ckscor3/GetItTogetherDrops/issues/10) concerns **Minecraft1.21.9 Fabric** error, non-anchor. No matching source-level repair for Forge 1.20.1 1.3 was discovered; record bounded negative in [history](FAILURE-REPAIR-HISTORY.md).

## Acceptance planned only, NOT_RUN

In isolated Minecraft 1.20.1 Forge, measure 1/100/1000 ItemEntity instances, per-item same/different tags, NBT, stack count, max stacks, redstone hopper pulls, chunk unload/reload, configurable radius {0.5,2,8,500} (500 only tiny disposable world and cautious profiler), checkY, explosion drops, multiplayer ownership, MSPT p95/99. **No source-binary parity and no GameTest currently.** This is COMPARATIVE source finding, not the user's exact implementation.
