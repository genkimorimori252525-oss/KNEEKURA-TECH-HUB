# Phase 4/5 checkpoint — Distant Horizons/GPU Tape and memory leak defenses

Date: 2026-10-11. Previous phase: [Phase 3 renderer](PHASE-3-RENDERING-CHECKPOINT.md) with 12 bounded in-cohort target dossiers out of 27 performance candidates.

## Phase 4: GPU/LOD technology — selected code and history

| Target | Source / track | Evidence-backed technique | Important limit |
|---|---|---|---|
| **[Distant Horizons 3.2.0-b](../../mods/distant-horizons/README.md)** | Exact [official GitLab tag 3.2.0b](https://gitlab.com/distant-horizons-team/distant-horizons/-/tags), GitHub mirror main commit `eb6bf9ae`, **pinned Core submodule `a0d2dfe`** | FullData→LOD columns, greedy quad merging and per-thread buffers, adaptive CPU throttle, quadtree LOD render selection, delayed async save, shader-compatible fallbacks; selected source + fixes verified | **424 main + 666 Core Git blobs indexed**, not all source bodies. 3.2.0-b release JAR SHA unverified, no GameTest. LOD lossiness intended. |
| **[GPU Tape 1.0.5.1](../../mods/gputape/README.md)** | **Exact 1.0.5.1 source NOT PINNED**; earlier `StarmanMine142/GpuTape` 1.20.2 Fabric 1.0.0; related developer historical `ITsMrToad/GPUBooster` pinned 1.21.1 Fabric 1.1.0 | **Comparative only**: queue deferred framebuffer/texture/FBO cleanup on client tick max 20 per tick | Client Forge/NeoForge source and binary evidence missing; contradictory project version support metadata, no direct 1.0.5.1 code inference. |

**Distant Horizons recorded source repairs:**
- viewport GL leak fix [1a7d3a4e...](https://github.com/DecoderCoder/Distant-Horizons/commit/1a7d3a4e87f84044b2222998db6ef80e4540a602) explicit destroy old depth/color textures before resizing;
- Iris [20f1cc43...](https://github.com/DecoderCoder/Distant-Horizons/commit/20f1cc438cbbb656342ea34720cdff5be170cc48) shader textured LOD fallback;
- **26.2 Blaze ByteBuffer pool separate** from Forge 1.20.1 OpenGL pipeline, not merged into ANCHOR.
- GPU Tape [Issue #5](https://github.com/ITsMrToad/GPUBooster/issues/5) maintainer claims 1.0.5.1 fixed crash in Forge 1.20.1, actual patch unknown.

## Phase 5: memory retention and cleanup

| Target | Exact source | Evidence-backed selected mechanisms | Critical limitations |
|---|---|---|---|
| **[AllTheLeaks](../../mods/alltheleaks/README.md)** | `1.20.1@5f4157f5`, Forge dev 47.4.10, **1.1.1+1.20.1-forge** source version agrees with user | `@Issue` per-mod/version/side gate, main-server stale BlockEntity ticker release, optional vanilla Ingredient interning, ResourceLocation string canonicalization, MemoryMonitor, old EventBus listener cache workaround gated by version; TF/JEI Hydra preview cleanup | **373 blob/356 Java paths indexed**, not all bodies; IngredientDedupe **off by default**; no binary equivalence/heap tests |
| **[MemoryLeakFix](../../mods/memoryleakfix/README.md)** | `dev@988f54c1`, 1.1.5 **dev MC1.20.4** Forge 49, not actual 1.20.1 release | version-gated Mixin plugin, shared static per-thread Biome temp cache, client hitResult clearing, huge screenshot error memory cleanup | **57 blob/28 Java paths indexed**. Brain memory cleanup only <=1.19.3, Drowned leak only <=1.16.5, TagKey fix only 1.18.2. Must not label active 1.20.1 |

**Important failure provenance:** upstream EventBus [PR #65](https://github.com/MinecraftForge/EventBus/pull/65) (merged Jan2025) eagerly invalidates old listeners; ATL [Issue #79](https://github.com/pietro-lopes/AllTheLeaks/issues/79) reporter in Jan2026 raised “old workaround may create new leak in EventBus 6.2.26+”, **but pinned ATL source from Nov2025 already has the proper gate**, and reporter acknowledged it. Not a confirmed new ATL fix. [ATL #70](https://github.com/pietro-lopes/AllTheLeaks/issues/70) chunk pregen memory issue points at other World Save mods per comments, not proved ATL leak. [MLF #115](https://github.com/FxMorin/MemoryLeakFix/issues/115) co-install conflict with Saturn is **1.18.2**, not 1.20.1.

## Reusable techniques promoted only as concepts

Catalog contains **40 research entries** (previous 29, +11). Sources and conditions are linked per row; no JARs, source blobs or proprietary assets committed; no implementation or code copying. Compare [LOD/memory interop matrix](LOD-MEMORY-INTEROP-MATRIX.md).

## Verified scope and next work

Cohort still **58 user file names** / **27 performance-first candidates** (not all matched to public original source). Cumulative **16/27** have *individual selected source research dossiers*, **NOT 16 whole-target completions**; **11 core candidates** remain without in-cohort deep dossier. No target release binary acquired, exact class/mixin parity, CAS source profile, reproducible profiler A/B or runtime Forge 1.20.1 world checks. `PERFORMANCE_NOT_VERIFIED` is unchanged across catalog.

Next suitable staged group:
1. **Server/AI:** Alternate Current, Clumps, Starlight, Noisium, then Canary genuine source search and Saturn;
2. **Rendering or performance tools:** inspect GPU Tape exact file loader tag/version and Distant Horizons official release JAR, profiler spark/Observable;
3. **Leak/interop:** MLF/Saturn exact 1.20.1 Class Mixins, ATL/ModernFix/JEI data reload/world-unload tests.
Do not conduct accidental all-on modpack performance tests or claim a % improvement without controlled local execution.
