# Source acquisition and multi-stage continuation

This is a **todo ledger, NOT an ongoing background job**. Current research checkpoint 2026-10-11; user asked to proceed in stages.

## Phase 0 — cohort intake: DONE

- [x] All **58** original JAR basenames captured exactly in [INPUT-MANIFEST.json](INPUT-MANIFEST.json); Windows private paths omitted.
- [x] 27 optimization candidates / 3 related / 3 diagnostic / 25 utility-only screened.
- [x] Current source repositories identified for many targets, exact source commit pinned when read; unresolved sources left explicitly UNKNOWN.
- [ ] All actual release JARs acquired: **NOT_RUN**, user supplied paths only.

## Phase 1 — selected code and incident research: PARTIAL

- [x] Selected code mechanisms mapped for **16** candidate MODs, prior AI Improvements study reused.
- [x] Six focused audits: FerriteCore, ModernFix, FastSuite, ServerCore, Particle Core and Embeddium; bounded issue/repair staging companions.
- [x] FerriteCore hash regression repair, ModernFix DFU-Litematica opt-out, ServerCore activation repair read as actual before/after source.
- [ ] Full source bodies, all required facets, complete history and source binary parity for each: NOT_COMPLETE.

## Phase 2 — in-depth batches: SELECTED_6_SOURCE_SLICES_DONE / WHOLE_TARGET_IN_PROGRESS

**Phase 2 checkpoint (2026-10-11):** FerriteCore, ModernFix, FastSuite, ServerCore, Particle Core and Embeddium have bounded new source review + history drafts. Details: [PHASE-2-CHECKPOINT.md](PHASE-2-CHECKPOINT.md). **No JAR parity, CAS import, FULL_SOURCE, benchmarks or full-target COMPLETE.** All other candidates are still Phase 1 only.

1. **Rendering**: Embeddium + ImmediatelyFast + EntityCulling first, then BFRC + CullLeaves + Bocchium, then GPU Tape + Distant Horizons; profile GL state, GPU occlusion, false missing visibility, resource reload and Mixin compatibility.
2. **Memory/cache**: FerriteCore, ModernFix, AllTheLeaks, MemoryLeakFix, Saturn. Obtain original source for Saturn first; pin at release + source. Study lifetimes/heap leakage, duplicate shared state, DFU and model caches.
3. **Server/AI and entity**: ServerCore, Canary, AI Improvements, LetMeDespawn, Clumps, GetItTogetherDrops. Find genuine Canary source lineage, not arbitrary forks; evaluate spawn/lifetime/targeting and pathfinding conflict.
4. **Chunks/worldgen/redstone/lighting/crafting**: Noisium, Starlight, Alternate Current, FastSuite, SmoothBoot Reloaded. Resolve SmoothBoot current original revision and actual backend; test worldgen/light/redstone invariants.
5. **Profilers not boosters**: spark, Observable, NotEnoughCrashes supply evidence and failure investigations, not FPS claims.
6. **Related/utility only when justified**: PacketFixer, LeavesBeGone, RRLS and UI/audio features remain tracked in manifest, without deep optimization claims.

For **each full target**: obtain full upstream source tree locally + hashes, select exact ANCHOR 1.20.1 Forge and independent FRONTIER (with COMPARATIVE for historical version), map entrypoints, resources/config, networking, lifecycle, Mixins, memory ownership, open Issues and verified before/after fixes, license and binding to distributed JAR. Publish `README`, `SOURCE-INVENTORY`, `OPTIMIZATIONS`, `CORRECTNESS`, `COMPATIBILITY`, `FAILURE-REPAIR-HISTORY.md/json`, `VERSION-PORTABILITY`, and source receipts.

## Phase 3 — renderer source slices: SIX NEW DOSSIERS DONE, remaining work OPEN

- [x] Added **BFRC / EntityCulling / ImmediatelyFast / CullLeaves / BadOptimizations / Bocchium** `README.md` + scoped `FAILURE-REPAIR-HISTORY.md/json` + exact commit/tree `SOURCE-RECEIPT.json`. See [PHASE-3-RENDERING-CHECKPOINT.md](PHASE-3-RENDERING-CHECKPOINT.md).
- [x] Added [RENDER-STACK-CONFLICT-MATRIX.md](RENDER-STACK-CONFLICT-MATRIX.md) for exact source Mixin target overlap and future A/B isolation. Existing MOD and TECHNIQUES catalogs now link to six dossiers; **29** technique entries.
- [x] Distinguish source revision vs user JAR distribution release (BFRC 0.5.13 vs 0.5.12; CullLeaves 4.1.2 vs 4.1.1; EntityCulling source 1.6.2 vs JAR 1.10.5; ImmediatelyFast dev 1.5.6 vs release 1.5.5).
- [ ] Full source-body acquisition, exact release JAR hash+parity, native 1.20.1 compiling/remap, CAS index capture, reloaded shader/world comparison: **NOT_RUN**.
- [ ] Next rendering: GPU Tape + Distant Horizons official GitLab, and source follow-up for EntityCulling/BFRC/Embeddium interoperability.

## Phase 4 — LAB and A/B: NOT_RUN

Use only an explicitly authorized disposable Forge 1.20.1 environment with source/binary identity, set observations/assertions/cleanup, record paired measurements. No production world. Do not reuse unrelated successful Water Tank tests as evidence.

## Known uncertainty

- Original source **Canary**, **Saturn**, exact **SmoothBoot 0.0.4** still needs matching source verification.
- **Distant Horizons** upstream lives on GitLab; GitHub copy is not authoritative.
- Embeddium repo was moved, use `FiniteReality/embeddium` exact branch. AI Improvements `1.20` latest is **NeoForge 1.20.2**; historical Forge 1.20 source separate.
- `ImmediatelyFast-...1.20.4` filename alone doesn't prove unsupported 1.20.1. `BetterAdvancements-NeoForge-1.20.1` in Forge directory must be verified as to actual loader.
- All source material collected so far is **selected evidence**, never proof that the *named release JAR* contains equivalent classes. No known +X% FPS/TPS measure.

## Phase 5 — knowledge promotion: NOT_DONE

These are reviewed source candidates and comparative source locators, NOT VALIDATED canonical knowledge. No new composite optimization MOD or source copying authorized.
