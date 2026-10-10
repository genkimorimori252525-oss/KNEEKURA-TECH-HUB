# 軽量化MOD全集 — Phase 3: 描画系6件のソース深掘り

**Date:** 2026-10-11. Phase 2 ended with 6 [mem/startup/server/particle/Embeddium dossiers](PHASE-2-CHECKPOINT.md). This phase adds **six distinct new renderer target dossiers**, leaving all earlier checkpoint documents intact. Main ledger [INPUT-MANIFEST.json](INPUT-MANIFEST.json) stays 58/58. Out of 27 optimization candidates, **12 have now received in-cohort deeper selected source reports**; other candidates may already have Phase-1 mechanism notes or an independent AI Improvements report, but this is **NOT a 12/27 completion rate** and no full-target analysis finished.

## Six individual source investigations

| Manifest ID | Target / pinned source | Specific mechanism and code evidence | Controlled failure/repair history | Binary and runtime state |
|---|---|---|---|---|
| **01** [BFRC](../../mods/brute-force-rendering-culling/README.md), Forge 1.20.1 [`58c55dcf`](https://github.com/RogoShum/BruteForceRenderingCulling/tree/58c55dcfe3d0a90c471c8a8b2bfedb1bf52685b3) | GPU 5-step depth pyramid; PBO result readback, indexed entity/section visibility, temporary visible grace, optional async rebuild. `CullingStateManager`, `EntityCullingMap`, `CullingMap`. | [Issue #27](https://github.com/RogoShum/BruteForceRenderingCulling/issues/27), **EXACT requested JAR version 0.5.12**, chunks appear late on rapid reveal; source 0.5.13 not exact binary, **no verified fix** | source only; no JAR hash, no frame test |
| **23** [EntityCulling](../../mods/entityculling/README.md), 1.20 [`dff7304b`](https://github.com/tr7zw/EntityCulling/tree/dff7304bcbb9186bada0a8c4617dc584fb2c3ea1) | CPU worker occlusion queries on AABBs, block entities, optional client-side Tick reduction, name tag exception; async iteration may race. `CullTask`, `ClientWorldMixin`. | Tick whitelist incorrectly added to render whitelist in old source; later [fix `5542327`](https://github.com/tr7zw/EntityCulling/commit/5542327d4a81c5fadfdad4c0d4c676862eea131b). 26.3 interpolation fix separate, not ANCHOR. | source metadata 1.6.2 vs requested 1.10.5 |
| **10** [ImmediatelyFast](../../mods/immediatelyfast/README.md), 1.20 dev [`b6688577`](https://github.com/RaphiMC/ImmediatelyFast/tree/b66885773494bfad58c83a8eee7b2f41424d4d9b) | RenderLayer batch HUD/text/item geometry, GL state restore, explicit flush barriers, temp memoization. `BatchingBuffers`, `BatchableBufferSource`, `BatchingRenderLayers`. | 1.20.1 Fabric glint ordering [fix `3f7d86f`](https://github.com/RaphiMC/ImmediatelyFast/commit/3f7d86fbdafb64fbb6e087e53bd3444bed4a717b), custom font text order [fix `f9fbf5d`](https://github.com/RaphiMC/ImmediatelyFast/commit/f9fbf5d83d6bd2bd73f403f833c419fff26a7368). | source 1.5.6-SNAPSHOT vs user 1.5.5; declared runtime 1.20-1.20.4 |
| **04** [CullLeaves](../../mods/cullleaves/README.md), multi-build [`a9ffb506`](https://github.com/TeamMidnightDust/CullLeaves/tree/a9ffb5061ae4ed49a55d5fe93679ee1d4bbe389e) | adjacency leaf/root `skipRendering`; optional fully surrounded leaves tesselation cancel; resourcepack reload flags and chunk rerender. | [Issue #69](https://github.com/TeamMidnightDust/CullLeaves/issues/69) SmartLeaves pack possibly reduces FPS; [#53](https://github.com/TeamMidnightDust/CullLeaves/issues/53) Embeddium collision is 1.19.2, not target. No before/after repair case supported. | source 4.1.2 vs user 4.1.1; code preprocessor needed |
| **08** [BadOptimizations](../../mods/badoptimizations/README.md), 1.20.1 [`f1540411`](https://github.com/imthosea/BadOptimizations/tree/f1540411b21e8458d6d143d00f53743e7a9bc893) | skip lightmap recalculation if lighting unchanged; uniform biome sky color cache, compatibility Dirty suppliers and mod-ID exclusions. | Polytone custom lightmap [fix `dd8c2c1`](https://github.com/imthosea/BadOptimizations/commit/dd8c2c1dc793a11c3c2e10e453a96001654b9023); 1.20.1 Darkness pulsing [fix `e6085b5`](https://github.com/imthosea/BadOptimizations/commit/e6085b58154adb90ca99db99741997e74ef27cd6). Source automatically excludes **Twilight Forest entity renderer caching** option. | source metadata 2.4.1 matches requested file version, bytes unverified |
| **18** [Bocchium](../../mods/bocchium/README.md), 1.20.1 [`57a2e920`](https://github.com/MCTeamPotato/Bocchium/tree/57a2e920273422253dde64f2c3d907bca8679afe) | inject `BlockOcclusionCache.shouldDrawSide` for top/down at dimension Y limits. **Does not check block is BEDROCK**. Single Mixin config only lists face cull, although GUI Mixin source exists. | Bounded issue search no supported failure/repair pair; no known fixed bug asserted. | source 0.0.3 name matches, no binary |

All six include `README.md`, `SOURCE-RECEIPT.json`, `FAILURE-REPAIR-HISTORY.md` and `FAILURE-REPAIR-HISTORY.json`, with standard six-facet evidence separation. The failure JSONs are **explicit research drafts, not history-adapter import-ready** pending actual CAS raw captures and their `index_snapshot_id`/`document_id`. Per-source **Git tree SHA is distinct from Git commit SHA** and present in source receipt.

## Cross-genre relevance

- **Twilight Forest**: BadOptimizations source built-in `twilightforest` entity-render cache exclusion; examine effect visual stability, not disable entire lightweight MOD.
- **Natural Ghast / complex boss attacks**: EntityCulling client ticking can affect custom animations and projectile visual state; BFRC can falsely hide large, shader-rendered/projectile geometry. Keep their draw/test data independent from server AI.
- **Kirby and particle FX**: CullLeaves and Bocchium act on chunk geometry, not particle rendering; Particle Core acts on a separate path but may overlap BadOptimizations' empty particle pass check.
- **Rendering stack**: [Detailed compatibility matrix](RENDER-STACK-CONFLICT-MATRIX.md) identifies cull order and source-specific Mixin targets. No architecture merging, no cross-MOD compatibility acceptance or benchmark.

## Important version boundaries

- **ImmediatelyFast 1.5.5+1.20.4** explicitly supports MC 1.20–1.20.4 on official Forge Modrinth listing; filename alone does not make it unsupported 1.20.1. Source branch 1.5.6 SNAPSHOT means JAR parity remains not proven.
- **BFRC** requested 0.5.12, inspected source gradle 0.5.13, issue #27 is specific to actual requested 0.5.12.
- **EntityCulling** code source 1.6.2 vs JAR 1.10.5; whitelists may have been repaired in newer JAR — cannot infer either way.
- **CullLeaves** source multiversion 4.1.2 vs JAR 4.1.1; requires preprocessing 1.20.1 Forge branch before bytecode conclusions.
- **BadOptimizations/Bocchium** dev source version string matches request, not actual byte parity.

## Next source batches

**Next renderer phase**: finish EntityCulling/Embeddium/BFRC source binary parity if original JARs become accessible; investigate GPU Tape and Distant Horizons GitLab. **Memory and worldgen remaining**: AllTheLeaks, MemoryLeakFix, Starlight, Noisium, Alternate Current, Clumps, Canary and Saturn source proof; then profiler tools spark/Observable. Keep priority by technical reusability, not attempt to present all 58 as fully analyzed.

**Run state:** 0 Forge runtime trials, 0 correct source-to-JAR matches, 0 FPS/MSPT benchmarks, 0 imported CAS whole-target snapshots, 0 canonical Claims promoted. Source mechanisms remain STATIC selected evidence.
