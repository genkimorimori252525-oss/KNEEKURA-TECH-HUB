# Brute Force Rendering Culling (BFRC) — depth-based occlusion and temporal validity

**Investigation:** 2026-10-11, rendering Phase 3A. **Source snapshot:** [`RogoShum/BruteForceRenderingCulling@58c55dcfe3d0a90c471c8a8b2bfedb1bf52685b3`](https://github.com/RogoShum/BruteForceRenderingCulling/tree/58c55dcfe3d0a90c471c8a8b2bfedb1bf52685b3), branch `forge-1.20.1`; Git recursive tree **91 blobs / 55 Java sources**, `truncated=false`. Only selected files retrieved/read; entire source bytes/CAS not acquired.

**Exact association boundary:** the user's named binary is `Brute force Rendering Culling-forge-1.20.1-0.5.12.jar`, **NOT uploaded / NOT hashed**. Pinned source `gradle.properties` declares **Minecraft 1.20.1, Forge dev 47.2.23, mod 0.5.13**. The source is **one version newer than the requested 0.5.12 release**, and is **NOT proven equal**. This repo is archived; FRONTIER beyond this snapshot NOT_ANALYZED. Source [LGPL-3.0](https://github.com/RogoShum/BruteForceRenderingCulling/blob/58c55dcfe3d0a90c471c8a8b2bfedb1bf52685b3/LICENSE).

## GPU-HiZ-01: depth hierarchy → entity, block-entity and section visibility

**Direct source:** [`CullingStateManager`](https://github.com/RogoShum/BruteForceRenderingCulling/blob/58c55dcfe3d0a90c471c8a8b2bfedb1bf52685b3/src/main/java/rogo/renderingculling/api/CullingStateManager.java), [`CullingMap`](https://github.com/RogoShum/BruteForceRenderingCulling/blob/58c55dcfe3d0a90c471c8a8b2bfedb1bf52685b3/src/main/java/rogo/renderingculling/api/data/CullingMap.java), [`EntityCullingMap`](https://github.com/RogoShum/BruteForceRenderingCulling/blob/58c55dcfe3d0a90c471c8a8b2bfedb1bf52685b3/src/main/java/rogo/renderingculling/api/data/EntityCullingMap.java), [`ChunkCullingMap`](https://github.com/RogoShum/BruteForceRenderingCulling/blob/58c55dcfe3d0a90c471c8a8b2bfedb1bf52685b3/src/main/java/rogo/renderingculling/api/data/ChunkCullingMap.java).

**Baseline:** vanilla frustum culling excludes out-of-camera geometry but not geometry fully hidden behind existing rendered surfaces.

**Mechanism:** allocate **5 depth hierarchy `TextureTarget` levels** (`DEPTH_SIZE=5`), plus entity/chunk map render targets; derive and downsample main-frame depth through shaders, read occlusion result via **OpenGL pixel buffer object** (`GL_PIXEL_PACK_BUFFER`) and an indexed byte-buffer map. The GPU performs a depth-informed visibility test; culling decisions are consumed by render dispatcher/section visibility hooks on the CPU side.

**Specific guards / fail open:**
- `Config.getCullEntity/getCullBlockEntity` returns **false** when not initialized or GL 3.3 unavailable, regardless of config.
- `EntityCullingMap.isObjectVisible(o)` defaults **visible** if its object does not map to a valid result index; records it as temporary pending.
- `CullingStateManager.visibleEntity/visibleBlock` life timers temporarily retain visibility to reduce popping (separate `EntityMap.tempObjectTimer.tick(tick, 3)`).
- Section query applies downstream of vanilla/Sodium `isSectionVisible` true. `Config.shouldCullChunk()` checks map readiness (`isDone`) first.
- `getAsyncChunkRebuild` has config guards, optional shader-driven disable and chunk rebuild pause logic; **do not treat async as unconditional**.

**Defaults in selected `Config.java`:** entity, block entity, chunk culling **true**; depth update delay **1 frame**; entity/block entity ignore lists configured. Actual user's edited config UNKNOWN.

**Lifecycle/cache:** maps have PBO allocated and `cleanup` deletes GL PBO; `CullingStateManager.onWorldUnload/checkShader` reset maps/timers/shader bookkeeping. GL resource/state lifecycle requires real render-context and world reload tests. Transfer/readback cadence adds frame/tick latency.

**Mixin surfaces** [`mixins.bfrc.json`](https://github.com/RogoShum/BruteForceRenderingCulling/blob/58c55dcfe3d0a90c471c8a8b2bfedb1bf52685b3/src/main/resources/mixins.bfrc.json): `EntityRenderDispatcher.shouldRender` RETURN, `BlockEntityRenderDispatcher.render`, `LevelRenderer.applyFrustum/setupRender`, Sodium/`OcclusionCuller.isSectionVisible` RETURN and `findVisible` HEAD, shader/window hooks. These are collision-sensitive with Embeddium/EntityCulling/shader loaders.

**Correctness risk:** newly visible chunks may remain hidden while GPU result/buffer/culling state is updated; shader depth target changes and inaccurate section index/range can cause missing geometry; false-negative cull never acceptable for player-critical combat. Detection of unsupported GL alone does not establish visual correctness.

## Upstream report matching the owner's **exact requested version**

[Issue #27](https://github.com/RogoShum/BruteForceRenderingCulling/issues/27) reports **0.5.12**, Minecraft **1.20.1 Forge** (also Fabric), missing newly revealed chunks for a short period when turning quickly or coming out from behind tree; reporter distinguishes async rebuild vs occlusion and says disabling chunk culling eliminates the latter. This is **REPORTER evidence**, issue **OPEN**, with **NO verified repair commit** found in inspected history. Never say 0.5.13 fixed it.

[Issue #10](https://github.com/RogoShum/BruteForceRenderingCulling/issues/10) concerns **Fabric 1.20.1 BFRC 0.5.8** + Iris shader crash, not the user's version.

## Reuse decision boundary / A-B test

Mechanism classification `RENDERING_GPU`, `CULLING_LOD`, `CACHE_DATA_STRUCTURE`, `MIXIN_BYTECODE`. **PERFORMANCE_NOT_VERIFIED, RUNTIME_NOT_RUN**. If compared with EntityCulling use same camera/geometry and check visible entity/section sets, frame median/p95/p99, GPU/PBO readback latency and number of culled false negatives. Test shader on/off, turning fast behind sparse terrain, low FPS and resizes. No original BFRC code committed or integrated.
