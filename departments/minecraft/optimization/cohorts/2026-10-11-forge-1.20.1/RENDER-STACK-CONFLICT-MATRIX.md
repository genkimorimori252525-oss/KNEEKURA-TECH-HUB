# 描画MOD間の衝突面 — Layered renderer integration matrix

Date: 2026-10-11. **Status:** SOURCE-MAPPED, **NO combination was actually loaded or benchmarked**. Applies to user cohort of Minecraft 1.20.1 Forge named JARs only as a research candidate matrix; pinned source versions may differ from exact JARs.

## Stage ownership and overlaps

| Source | Where it intervenes | Work it avoids or rearranges | Direct overlap / testing risk |
|---|---|---|---|
| [BFRC](../../mods/brute-force-rendering-culling/README.md) | GPU depth hierarchy + PBO readback; Mixin `EntityRenderDispatcher.shouldRender` RETURN, `BlockEntityRenderDispatcher.render`, `OcclusionCuller.isSectionVisible` RETURN, `findVisible` HEAD | GPU depth/occlusion decides entity/block entity/chunk section visibility | EntityCulling render hooks can independently mark same entity hidden; Embeddium/Sodium OcclusionCuller exact mapped API; shaders can replace depth attachment |
| [EntityCulling](../../mods/entityculling/README.md) | `CullThread` CPU ray/AABB visibility; `LevelRenderer.renderEntity` HEAD, `BlockEntityRenderDispatcher.render` HEAD; **also `ClientLevel.tickNonPassenger` HEAD** | block hidden entity/BE draw, reduces **client only** entity ticks | same BlockEntity render dispatcher as BFRC, client tick policy may damage interpolation with custom animated entities, projectile rendering and boss overlays |
| [Embeddium](../../mods/embeddium/README.md) | chunk mesh builder worker queue / section renderer and GL buffer manager | avoid vanilla chunk mesh/render cost and schedule work within heap budget | BFRC uses `OcclusionCuller` class from Sodium namespace; CullLeaves/Bocchium source Mixins compile/load against specific Sodium/Embeddium ABI |
| [ImmediatelyFast](../../mods/immediatelyfast/README.md) | `BatchingBuffers` begin/end HUD/screen rendering, `RenderLayer` ordering, draw-state restores | reduce repeated draw/texture state switches, batch geometry | overlays, custom fonts, shader textures, enchant glint. Not the same optimization stage as BFRC/EntityCulling; interaction still possible through GPU state and GUI layers |
| [CullLeaves](../../mods/cullleaves/README.md) | `LeavesBlock.skipRendering`; optional `ModelBlockRenderer.tesselateBlock`; sodium `BlockRenderer.renderModel` loader path | skip adjoining leaf/root faces or whole enclosed leaf models | Bocchium also changes per-face mesh stage but different guard; every culling option needs chunk rebuilding; resourcepack SmartLeaves may increase geometry |
| [Bocchium](../../mods/bocchium/README.md) | Embeddium/Sodium `BlockOcclusionCache.shouldDrawSide` at HEAD, `remap=false` | drop boundary-facing top/bottom faces based on direction & Y | **does not check BEDROCK block type in inspected source**; world dimensions/custom geometry and fatal target class mismatch risk, if Embeddium API absent |
| [BadOptimizations](../../mods/badoptimizations/README.md) | `LightTexture.tick`, `ClientLevel.getSkyColor`, `LevelRenderer.renderSky`, particle-render empty early skip | cached client color/lightmap/time and redundant calls | shader/light/dynamic nightvision; **Twilight Forest disables only entity renderer cache option**, Polytone disables sky+lightmap caching via explicit mod-ID guards |
| [Particle Core](../../mods/particle-core/README.md) | particle manager `tick` optional async and `render` per-particle geometry distance guard | particle tick and geometry generation for distant particles | BadOptimizations also intercepts particle renderer; priority/transform order needs actual compiled Mixin evidence, and GPU offthread world reads can race |
| [BFRC + Embeddium + CullLeaves + Bocchium stack] | see all above | different-stage decisions are potentially complementary | **nothing guarantees additive FPS**, exact source+JAR version and GL state must be tested |

## Critical compatibility boundaries

1. **Exact-target mixins, not names**: compare (target class, target method descriptor, injector type, priority, `remap` mode, and loader). E.g. BFRC and EntityCulling both alter BlockEntityRenderDispatcher; BFRC also touches Sodium OcclusionCuller, Bocchium directly targets Embeddium's BlockOcclusionCache. The same Minecraft version is not enough to prove targets match.
2. **False negative → invisible essential objects**: force-render/tick for bosses, Ghasts, projectiles, lasers, shields, boss particles, decorative name tags, shaders and custom BlockEntity renderers. Test behind opaque vs transparent blocks and giant AABBs.
3. **Visible transition latency**: BFRC Issue #27 is exactly user-named 0.5.12; verify new visible chunks are generated/rendered promptly after rapid camera pans with limited FPS. Render pipeline should prefer temporarily drawing a suspect object over persistent holes.
4. **World unload and cache invalidation**: BFRC PBO/dynamic GL framebuffer state, EntityCulling `CullThread`, ImmediatelyFast HUD buffer flush and RenderLayer caches, CullLeaves resourcepack reload, BadOptimizations cached sky/lightmap and Polytone.
5. **Offscreen entities**: EntityCulling's reduced client tick can freeze client interpolation. This should never be extrapolated to skipping **server** AI logic. ServerCore activation is a separate server behavior-changing subsystem.
6. **Face-only vs whole-object culling**: leaf/Bocchium work at geometry generation; object culling occurs at later render submission; batching occurs at HUD/overlay draw operation; FPS gains from one may reduce work available to another.

## Explicit pending paired A/B test matrix (NOT_RUN)

Keep identical world seed, render/simulation distance, camera path, shaders, driver, resolution, JVM/heap, entity count & chunk contents across runs. Run stable warmup then 3+ replicated variants, metric frame median/p95/p99/GPU/render thread/VRAM/visible geometry and exceptions.

| Test ID | Enabled groups | Compare | Visual acceptance |
|---|---|---|---|
| `RENDER-BASE` | Embeddium as renderer baseline if supported | vanilla → Embeddium | expected chunks/models and blockstates unchanged |
| `RENDER-ENTITY` | EntityCulling alone; BFRC alone; both | A/B/C/D renderer costs and cull counts | boss projectiles, giant/animated mobs, nametag, glow; no missing sprites |
| `RENDER-FOLIAGE` | CullLeaves off/on + SmartLeaves pack off/on | leaf face count + frame p99 | correct leaf transparencies, rotations, missing faces and rebuilt chunks |
| `RENDER-WORLD-BOUND` | Bocchium off/on (Embeddium pinned version) | chunk vertex and mesh time | normal vs modded dimensions, boundary has non-bedrock blocks, only physically hidden faces |
| `RENDER-HUD` | ImmediatelyFast off/default + modern UI/font mods | GUI draw calls, GL state, frame p95 | title layering, XP level, armor glint, boss overlay preserved |
| `RENDER-DYNAMIC-LIGHT` | BadOptimizations caching off/on + Polytone/TF/GammaUtils | lightmap uploads, frame p95 | darkness pulse, sky hue, gamma/potion transitions and reloads match baseline |
| `RENDER-PARTICLE` | BadOptimizations + Particle Core combinations | particle tick/render cost | still visible near camera, no palette/thread RNG crash |

**Test lab authorization and exact user JAR source parity pending. NOT_RUN.**
