# EntityCulling — CPU occlusion rays, entity skip and client tick suppression

**Investigation:** 2026-10-11 rendering Phase 3A. [`tr7zw/EntityCulling@dff7304bcbb9186bada0a8c4617dc584fb2c3ea1`](https://github.com/tr7zw/EntityCulling/tree/dff7304bcbb9186bada0a8c4617dc584fb2c3ea1) branch `1.20`, Git tree **42 blobs / 17 Java files**, full path inventory, selected sources read. Target JAR `entityculling-forge-1.10.5-mc1.20.1.jar` **not uploaded or hashed**. `EntityCulling-Forge/.../mods.toml` in pinned source declares **1.6.2**: **not source/binary parity for 1.10.5**, and branch name alone does not establish version equivalence. FRONTIER latest branch `main` SHA `7e62c6ebd6a014b047330727d46faa1159a22406` discovered, but methods only reviewed via selected downstream repair diff, not a full comparison.

**License:** [`tr7zw Protective License`](https://github.com/tr7zw/EntityCulling/blob/dff7304bcbb9186bada0a8c4617dc584fb2c3ea1/LICENSE-EntityCulling); upstream README says redistribution of source/derivative binaries needs authorization, and license has noncommercial restrictions. Do not copy target source or redistribute.

## CPU-OCCLUSION-RAY: asynchronous occlusion of object AABBs

[`CullTask.run`](https://github.com/tr7zw/EntityCulling/blob/dff7304bcbb9186bada0a8c4617dc584fb2c3ea1/Shared/src/main/java/dev/tr7zw/entityculling/CullTask.java) is a persistent client worker `CullThread` started in [`EntityCullingModBase.clientTick`](https://github.com/tr7zw/EntityCulling/blob/dff7304bcbb9186bada0a8c4617dc584fb2c3ea1/Shared/src/main/java/dev/tr7zw/entityculling/EntityCullingModBase.java). It sleeps between passes (selected `Config.sleepDelay=10` ms), then checks camera moved or request flag, resets `OcclusionCullingInstance` cache, and evaluates entity/block entity **AABB visibility** by ray queries.

- Source defaults: `tracingDistance=128`, `hitboxLimit=50`, `renderNametagsThroughWalls=true`, `tickCulling=true`, `skipMarkerArmorStands=true`; `skipEntityCulling=false` and `skipBlockEntityCulling=false`.
- Guard: spectator, glowing, forced-visible, special marker armor stand, too-large AABBs, beyond tracing distance, entity/block-entity allowlists → remain visible. Specialized `shouldRenderOffScreen` block entity renderers skip automatic cull.
- `CullTask` iterates client render entities and scans a **17×17 area of chunks** for block entities (x,z = -8..8). Cross-thread `ConcurrentModificationException` / `NullPointerException` during iteration is caught and the current scan **breaks**. This is a pragmatic avoidance of crashes, **not a guarantee of consistent visibility state** or a fully race-free iteration.
- Per-candidate cached visibility flag `Cullable.setCulled` is consumed by [`WorldRendererMixin.renderEntity`](https://github.com/tr7zw/EntityCulling/blob/dff7304bcbb9186bada0a8c4617dc584fb2c3ea1/Shared/src/main/java/dev/tr7zw/entityculling/mixin/WorldRendererMixin.java) and [`BlockEntityRenderDispatcherMixin.render`](https://github.com/tr7zw/EntityCulling/blob/dff7304bcbb9186bada0a8c4617dc584fb2c3ea1/Shared/src/main/java/dev/tr7zw/entityculling/mixin/BlockEntityRenderDispatcherMixin.java); entity nametag may still be manually rendered for culled mob if configuration allows.
- Cache: `OcclusionCullingInstance.resetCache()` on moving/requested camera; thread lifetime is Minecraft client run. Culling flags have no observed world epoch fencing in selected source: chunk/despawn/change/camera can race worker. That is a **risk inference**, not reproduced defect.

## Tick culling is not render-only

[`ClientWorldMixin.tickNonPassenger`](https://github.com/tr7zw/EntityCulling/blob/dff7304bcbb9186bada0a8c4617dc584fb2c3ea1/Shared/src/main/java/dev/tr7zw/entityculling/mixin/ClientWorldMixin.java) cancels ordinary **client-side** entity tick for culled/out-of-camera mobs when `tickCulling=true`; calls reduced `basicTick` to update old positions, tick count and certain living/sound states. It does **not** cancel server-side AI/gameplay ticks. However client interpolation, animations and particle/visual state can diverge; do not claim semantic transparency.

## Exact source flaw + later repair (not JAR parity)

In selected `1.20` source, tick-culling whitelist IDs are inserted into `entityWhistelist`, not `tickCullWhistelist`; client tick check tests only `entityWhistelist`. This can make a tick-only exclusion alter rendering exclusions, conflating two configuration policies. Compared [repair commit `5542327d4a81...`](https://github.com/tr7zw/EntityCulling/commit/5542327d4a81c5fadfdad4c0d4c676862eea131b) from 2025-06-20 in **newer reorganized source**: stores tick exclusions separately and tests both sets for client ticking. Actual requested 1.10.5 release may contain the fix; **NOT_CHECKED**.

[Issue #204](https://github.com/tr7zw/EntityCulling/issues/204), **Fabric 1.21.4** display-entity teleport problem, led to default display entity tick whitelisting and diagnosis that the tick whitelist was ineffective. This supports developer repair motivation, **not** Forge 1.20.1 runtime.

Far newer [2026-09 interpolation fix `984ae74...`](https://github.com/tr7zw/EntityCulling/commit/984ae74b7fe191922e8bdc044e9be009e83f4091) adds `entity.getInterpolation().interpolate()` in reduced tick specifically for **Minecraft 26.3**. It is FRONTIER code for changed interpolation API; not a 1.20.1 procedure or evidence of same bug.

## Distinction from other render optimizers

- **BFRC**: GPU depth hierarchy plus readback; also culls **chunks** and may use PBO; direct overlap in entity/block entity **outcome**, but different algorithms and injection sites.
- **EntityCulling**: CPU background AABB occlusion plus optional client tick suppression and manual nametag handling. Tests must verify **culled state** with BFRC on/off, not assume savings stack.
- **Embeddium**: chunk-mesh generation and section visibility; README comments on weaker visible-chunk-based culling, but exact installed Embeddium render feature policy needs versioned source/JAR proof.
- **ImmediatelyFast**: buffer batching, not object visibility culling.

**Categories:** `RENDERING_GPU`, `CULLING_LOD`, `TICK_SIMULATION`, `THREADING_CONCURRENCY`. **PERFORMANCE_NOT_VERIFIED**, **RUNTIME_NOT_RUN**.

Recommended future test: 1/100/1000 moving actors including ghasts/armor stands/summons and giant AABBs; opaque vs translucent wall, nametag+glow, moving camera, world reload and entity despawn, frame p95/p99, culled/ticked ratio, motion interpolation. Need exact JAR bytes + dependencies before any source/binary parity or runtime confidence.
