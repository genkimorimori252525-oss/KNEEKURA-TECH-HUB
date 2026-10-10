# Alternate Current 1.7.0 — non-locational redstone wire propagation (Phase 6)

**2026-10-11 evidence checkpoint. Source ANCHOR:** [SpaceWalkerRS/alternate-current@`ab87061f1d04c44bfd42ba219ca567f8709c2acc`](https://github.com/SpaceWalkerRS/alternate-current/tree/ab87061f1d04c44bfd42ba219ca567f8709c2acc), branch `forge`. Git tree `8cc855648961cc14c99bea115c5e7b869cbff8a5`, **30 blobs / 16 Java source paths**, recursive tree not truncated; **selected source bodies read**, full source bytes/CAS not acquired. `gradle.properties` declares **Minecraft 1.20.1, Forge dev 47.1.0, mod 1.7.0**, Java 17 by Minecraft 1.20.1 dev context. This agrees with requested `alternate_current-mc1.20-1.7.0.jar` and official [CurseForge file 4721662](https://www.curseforge.com/minecraft/mc-mods/alternate-current/files/4721662) (Forge 1.20, 1.20.1 and 1.20.2 announced). **Actual user JAR not uploaded / SHA-256 or source-bytecode parity NOT_VERIFIED.** License [MIT](https://github.com/SpaceWalkerRS/alternate-current/blob/ab87061f1d04c44bfd42ba219ca567f8709c2acc/LICENSE).

Categories: `TICK_SIMULATION`, `CACHE_DATA_STRUCTURE`, `MIXIN_BYTECODE`; mechanism selected SOURCE-EVIDENCE_BACKED; **PERFORMANCE_NOT_VERIFIED**, runtime NOT_RUN.

## AC-NET-01 — collect sources, BFS, depower then power once

From [`WireHandler.java`](https://github.com/SpaceWalkerRS/alternate-current/blob/ab87061f1d04c44bfd42ba219ca567f8709c2acc/src/main/java/alternate/current/wire/WireHandler.java):
- **Baseline:** vanilla wire updates may recurse, repeatedly sample same non-wire power sources, set intermediate power states and issue redundant block/shape updates. Author documents 42 vanilla block updates (6 self, 12 duplicates) and up to 22 shape updates per power change in implementation comments. These are **author code explanatory values**, not independent KNEEKURA benchmarks.
- **Design:** a **per-ServerLevel WireHandler** provided via [`ServerLevelMixin`](https://github.com/SpaceWalkerRS/alternate-current/blob/ab87061f1d04c44bfd42ba219ca567f8709c2acc/src/main/java/alternate/current/mixin/ServerLevelMixin.java) holds `Long2ObjectMap<Node>`, simple BFS queue of wire nodes, priority queue for actual updates, reusable `Node[]` cache and `updating` recursion lock.
- **Phase 1:** `findRoot/discover/findExternalPower` groups connected wires, checks non-wire power at most once for matching node and tests desired `virtualPower`, using adjacency links and root BFS.
- **Phase 2:** `depowerNetwork` lets power decay virtually instead of committing every intermediate state to the world.
- **Phase 3:** `powerNetwork` propagates power from roots with deterministic direction-based ordering; commits `WireNode.setPower()` only when actually needed, and issues neighbor updates after final power transitions.
- **Cleanup/invalidation:** `tryUpdate` clears `nodes` and nodeCache index after nonreentrant work; when nested updates occur it calls `invalidate` and revalidates nodes before reuse. Exception guard resets `updating=false` to prevent permanent lockout. Cross-world shared/global cache is **not** claimed.
- **Source Mixin:** [`RedStoneWireBlockMixin`](https://github.com/SpaceWalkerRS/alternate-current/blob/ab87061f1d04c44bfd42ba219ca567f8709c2acc/src/main/java/alternate/current/mixin/RedStoneWireBlockMixin.java) cancels vanilla `updatePowerStrength` when enabled, forwards onPlace/onRemove to `WireHandler`, and handles `neighborChanged` with conditionally canceled vanilla callback. This intentionally changes the update pathway, not just helper-level math.

## AC-BLOCK-FASTPATH — specialized state mutation with required notifications

[`LevelHelper.setWireState`](https://github.com/SpaceWalkerRS/alternate-current/blob/ab87061f1d04c44bfd42ba219ca567f8709c2acc/src/main/java/alternate/current/wire/LevelHelper.java) accesses `ChunkAccess/LevelChunkSection`, sets only wire BlockState through `section.setBlockState`, then **`level.getChunkSource().blockChanged(pos)`** and **`chunk.setUnsaved(true)`**; emits shape updates only when needed for placement. Avoids generic Level.setBlock heightmap/light/BlockEntity side effects that should be unnecessary for wire signal level mutation. **The correctness contract depends on the state remaining a redstone wire and only its POWER changing**; copying this direct write technique for generic blocks or siege destruction would be unsound. Requires thread/world owner rules and interaction with other chunk/lighting mods.

## Intentional update-order difference from vanilla

[`WireHandler.forEachNeighbor`](https://github.com/SpaceWalkerRS/alternate-current/blob/ab87061f1d04c44bfd42ba219ca567f8709c2acc/src/main/java/alternate/current/wire/WireHandler.java) walks 6 direct + 12 diagonal + 6 Manhattan-distance-2 neighbors in direction derived from wire `flowIn`, then deterministic order. It **does not reproduce vanilla location-dependent update order**, even if final wire power levels match. Quasi-connectivity, observers, pistons, BUD circuits and redstone dupe farms need **behavior-level acceptance tests**.

Author [Issue #13 explanation](https://github.com/SpaceWalkerRS/alternate-current/issues/13#issuecomment-1015920585) admits circuits relying on vanilla order can behave differently. Later [Issue #55](https://github.com/SpaceWalkerRS/alternate-current/issues/55), **2026 version (not 1.7 Forge)**, describes a piston door behaving differently; maintainer and reporter tested update-order/locationality, not source proof of 1.7 specific bug.

**FRONTIER boundary:** official [Alternate Current releases](https://github.com/SpaceWalkerRS/alternate-current/releases) describe **1.8.0+** configurable update orders stored per world. The 1.7.0 Forge source uses a **fixed** priority/direction order and does **not** have the 1.8+ per-world update-order config. Newest published 1.9.x separate, not ported to 1.20.1.

## Verified failure and source repair

[Issue #27](https://github.com/SpaceWalkerRS/alternate-current/issues/27) describes 1.6.0 Forge **1.19.2** and Fabric 1.20.1 dropping 2 redstone when a support block breaks. [Actual commit `815fac14e103...`](https://github.com/SpaceWalkerRS/alternate-current/commit/815fac14e103ce5defcf98578acdd55da0b0cd63) shifts onPlace/onRemove Mixin injection from BEFORE to default placement and alters `onWireUpdated` to return true if still wire, letting neighbor callback be canceled; maintainer said **fixed in 1.7.0**. Selected source 1.7.0 contains amended neighbor cancel. This links **actual diff and author fix claim**, **runtime verification NOT_RUN**. See [history](FAILURE-REPAIR-HISTORY.md).

## Validation requirements before code reuse

World experiments same seed and block layout; compare vanilla and AC after settling, `blockstate POWER` values, exact emitted neighbor/shape notifications and update order, timed piston doors/observers, chunk border, breaks/placements during update, dripstone/fluids/other mods, 1/100/10000 dust networks. Measure MSPT p95/99 and number of Level.setBlock/shape calls; any altered behavior must be explicitly accepted rather than called exact parity. **No benchmark or game run performed.**
