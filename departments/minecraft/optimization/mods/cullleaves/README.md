# CullLeaves — leaf faces, whole hidden leaf blocks and config-driven rebuild

**Investigation date:** 2026-10-11, rendering Phase 3B. Source pinned [`TeamMidnightDust/CullLeaves@a9ffb5061ae4ed49a55d5fe93679ee1d4bbe389e`](https://github.com/TeamMidnightDust/CullLeaves/tree/a9ffb5061ae4ed49a55d5fe93679ee1d4bbe389e), branch `multiversion`; recursive tree **81 blobs / 9 Java + 1 Kotlin** source paths, not truncated. Selected classes, configs and Mixin configs read; full generated Forge 1.20.1 artifacts NOT_ACQUIRED.

**ANCHOR build target:** `versions/1.20.1-forge/gradle.properties` confirms **Minecraft 1.20/1.20.1, Forge loader dev 47.3.0**. [Official CullLeaves Forge 1.20.1 file 7324169](https://www.curseforge.com/minecraft/mc-mods/cull-leaves/files/7324169) declares exact requested `cullleaves-forge-4.1.1+1.20.1.jar` (2025-12-12) and requires MidnightLib. However current pinned top-level source declares **`mod.version=4.1.2`**; **source/JAR 4.1.1 equivalence UNKNOWN**. Multi-version Java includes Stonecutter/preprocessor `//? if` branches; **unprocessed current source cannot be treated as literal Forge 1.20.1 bytecode**. FRONTIER source 26.2+ shares tree but changed methods; no full version diff. Source [MIT](https://github.com/TeamMidnightDust/CullLeaves/blob/a9ffb5061ae4ed49a55d5fe93679ee1d4bbe389e/LICENSE).

**Categories:** `RENDERING_CHUNK`, `CULLING_LOD`, `MIXIN_BYTECODE`. Performance `MECHANISM_ONLY/PERFORMANCE_NOT_VERIFIED`.

## CL-01 — skip leaf-vs-leaf faces

[`MixinLeavesBlock`](https://github.com/TeamMidnightDust/CullLeaves/blob/a9ffb5061ae4ed49a55d5fe93679ee1d4bbe389e/src/main/java/eu/midnightdust/cullleaves/mixin/MixinLeavesBlock.java) overrides `LeavesBlock.skipRendering` to call `CullLeavesClient.isLeafSideInvisible(neighborState)`. With `CullLeavesConfig.enabled=true` (selected source default), adjacent **LeavesBlock** surfaces are reported as unnecessary for rendering; no complete leaf-volume scan is needed for this optimization. A separate `MixinMangroveRootsBlock` handles adjacent mangrove roots when `cullRoots=true`.

- **Baseline:** face generation unless vanilla/other render pipeline decides to omit it.
- **Fast path:** avoid emitting a face that would be behind another same-category leaf/root block.
- **Guard:** feature toggle + neighbor block class/type; no GPU occlusion query, no Entity/BlockEntity culling.
- **Correctness:** transparency, resource-pack models, fast/fancy leaf settings and mismatched neighbor mesh; check leaf/roots with mixed species, foliage decay, transparent layer shaders, leaf animation and different lighting.
- **Invalidation:** changing config requires renderer/chunk rebuild; `CullLeavesConfig.writeChanges()` requests full render section update on selected preprocessing branch; avoid stale geometry from change without rebuild.

## CL-02 — optional hide fully surrounded leaf blocks

[`CullLeavesClient.shouldHideBlock(world,pos)`](https://github.com/TeamMidnightDust/CullLeaves/blob/a9ffb5061ae4ed49a55d5fe93679ee1d4bbe389e/src/main/java/eu/midnightdust/cullleaves/CullLeavesClient.java) checks **all six neighboring directions** and says the leaf can be hidden only when each neighbor is another `LeavesBlock` or a full enough sturdy face. `MixinBlockModelRenderer` can **cancel complete tesselation** when `forceHideInnerLeaves` is active. The separate `sodium.MixinBlockRenderer` path exists for other loaders/versions but its exact Forge 1.20.1 inclusion and Embeddium class matching need generated JAR evidence. This is a more aggressive policy than merely skipping adjoining faces.

**Resource pack trigger:** `CullLeavesClient.ReloadListener` resets `forceLeafCulling` / `forceHideInnerLeaves` and loads `options/*cullleaves*options.json` on resource reload. Resource pack changes culling conditions, which means A/B tests must include **pack enabled/disabled** and fresh chunk rebuild.

## Field report: "SmartLeaves" pack can be slower, not a verified benchmark

[Issue #69](https://github.com/TeamMidnightDust/CullLeaves/issues/69) says SmartLeaves resource pack enabled by default in user's setup worsened FPS compared with pack disabled. This is a **user-reported workload**; selected source confirms the pack can affect culling mode, but no paired actual pack model/geometry trace was captured. Do not call SmartLeaves categorically slower or faster.

[Issue #53](https://github.com/TeamMidnightDust/CullLeaves/issues/53) reports jungle crash with Embeddium on **Forge 1.19.2** / CullLeaves 3.0.0; **not** target Forge 1.20.1 4.1.1, and no inspected repair diff.

## Comparison / tests

Distinct from BFRC and EntityCulling because CullLeaves acts **at block/mesh construction**, not object draw submission or occlusion-map visibility. Combining with Bocchium may target different faces but needs full rebuilt mesh and correct boundary. Test all three leaf cull modes (leaf adjacency on/off; inner leaf pack on/off), shaders, 10k+ leaf blocks, camera paths, exact geometry visibility, mesh time/frame p95/vertex count. No JAR/benchmark/cross-mod runtime.
