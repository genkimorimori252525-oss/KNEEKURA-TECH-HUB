# 軽量化MOD全集 — Phase 0 / 1 technical cohort (2026-10-11)

**GitHub research checkpoint**: 2026-10-11. **58 user-named JAR basenames**, no binary upload for this cohort; source discovery through upstream GitHub and published product sources. This is a **staged investigation**, NOT analysis-complete status for 58 separate MODs.

## Scope and custody

- User's private Windows paths were normalized to **file basenames only** in [INPUT-MANIFEST.json](INPUT-MANIFEST.json); private paths not stored.
- NONE of these 58 JARs was received/opened this turn. JAR SHA256, deployed dependencies, classloader transforms, actual loaded Forge instance and per-binary source equivalence **NOT_ANALYZED**.
- Source branches and head commit IDs are **discovery/inspection snapshots**, not proof a requested JAR corresponds to that exact source tree. Every migration between Forge/Fabric/NeoForge needs its own track and release check.
- Whole-target methodology: [Minecraft Analysis Workflow](../../ANALYSIS-SPEC.md) (optimization-specific) and [parent standard](../../../ANALYSIS-WORKFLOW.md). Main performance rules: [BENCHMARK-SPEC](../../BENCHMARK-SPEC.md).
- `AI Improvements: Performance Tuning` was already researched in existing optimization lane. Do not analyze as `Improved Mobs`; [previous source audit](../../mods/ai-improvements/README.md).

## Gate results: 58 input names

| Scope gate | Count | Interpretation |
|---|---:|---|
| **OPTIMIZATION_CANDIDATE** | **27** | source/code search and, where possible, phase-one mechanism interpretation; may still need exact upstream/source proof |
| **RELATED_REVIEW** | **3** | indirect performance/world/network behaviour, not guaranteed optimization-first |
| **PROFILING_TOOL** | **3** | direct performance improvement is NOT implied; diagnostic/crash evidence capture tools |
| **OUT_OF_CORE_SCOPE** | **25** | UI/UX/gameplay/crafting/social convenience, separate from optimization mechanism audit |
| **TOTAL** | **58** | Every filename appears exactly once in input manifest |

### 27 optimization-first candidates

**Rendering / GPU / particles / LOD**:
- Brute Force Rendering Culling, Embeddium, Particle Core, Cull Leaves, BadOptimizations, ImmediatelyFast, Bocchium, Distant Horizons, EntityCulling, GPU Tape.
  
**Memory / allocation**:
- FerriteCore, AllTheLeaks, MemoryLeakFix, Saturn.
  
**Server ticks / entities / background activity**:
- AI Improvements, LetMeDespawn, Alternate Current, GetItTogetherDrops, Clumps, Canary, ServerCore, Dynamic FPS.

**Startup/resource/chunk/light/recipe**:
- Smooth Boot (Reloaded), ModernFix, FastSuite, Starlight, Noisium.

> These categories are **workload priorities**, not assertions that every listed MOD has a confirmed source match or performance benefit. Core implementation licensed code is never copied as-is into TECH-HUB.

### Other 31 entries

- **Related review (3):** PacketFixer (network correctness / packet sizing), LeavesBeGone (gameplay world update), RRLS (resource reload UI/experience). They may affect runtime or perceived delays, but do not presume measured optimization.
- **Diagnostic (3):** Observable, spark, NotEnoughCrashes (profiling / forensic crash evidence).
- **Utility-only out of optimization core (25):** caramelChat, ExtremeSoundMuffler, Essential, NotEnoughAnimations, TrashSlot, VisualWorkbench, Resourcify, StylishEffects, JourneyMap, Polymorph, PickUpNotifier, OverflowingBars, MouseTweaks, InvMove, Jade, BridgingMod, EMI, Freecam, Controlling, CWB, CherishedWorlds, BetterF3, CarryOn, BetterAdvancements, AppleSkin. Their code may still be relevant to other Minecraft technique shelves.

No mod is discarded from record; deferrals are explicit in the manifest.

## Already accomplished in this checkpoint

1. Full requested filename list captured and normalized, 58/58 traceable.
2. Upstream source repositories/branch candidates located for most items; 16 code-level key mechanisms **read directly** and 1 AI Improvements prior research reused, in addition to path/README inventory for others.
3. Separate source-audit reports for **FerriteCore, ModernFix, FastSuite, ServerCore, Particle Core, Embeddium** with pinned source locators, correctness boundaries and report/repair observations.
4. [PHASE-1-TECHNIQUES.md](PHASE-1-TECHNIQUES.md) maps selected other significant source reads (culling, lighting, redstone, Clumps, Noisium and more).
5. [FAILURE-REPAIR-TRIAGE.md](FAILURE-REPAIR-TRIAGE.md) prevents community blame being substituted for observed causal fixes.
6. [BENCHMARK-AND-ACCEPTANCE.md](BENCHMARK-AND-ACCEPTANCE.md) defines paired A/B workloads; **0 runtime scenarios actually run**.
7. [PHASE-2-BACKLOG.md](PHASE-2-BACKLOG.md) identifies next source/JAR/issue acceptance slices.

## Snapshot/inventory status caveats

Observed full recursive **source path inventories** include Embeddium 552 blobs, ModernFix 390, FerriteCore 102, ServerCore 135, AllTheLeaks 373, and many smaller repos. An API listing of all paths does **not** mean all bodies or binary bytes have been acquired/inspected. Every included target remains **IN_PROGRESS or INVENTORIED**, not COMPLETE.

- **Embeddium:** canonical GitHub source moved/redirected to `FiniteReality/embeddium`; branch `20.1/forge` vs 21.4/neoforge.
- **FerriteCore:** branch `1.20.0` is a comparative source for 1.20.1 release, not verified identical to 6.0.1.
- **ImmediatelyFast:** requested artifact filename ends `+1.20.4`, not automatic evidence that binary won't load in 1.20.1; source loader/minecraft metadata and release support require explicit check.
- **Particle Core:** branch `forge/1.20.1` source has namespace/mapping mix to audit before assuming recompilable.
- **Bocchium:** analyzed `1201` source is Minecraft 1.20.1-related but Sodium API compatibility and loader mapping unresolved.
- **Starlight/MemoryLeakFix/Noisium:** upstream GitHub repositories are archived, not evidence that their claimed features are available in newer loaders.
- **Distant Horizons:** primary upstream on **GitLab**, so GitHub code search is not authoritative; source tree acquisition pending.
- **Canary, Saturn, Smooth Boot Reloaded:** named distribution and nearby forks found, but exact matching public source revision unresolved. Source-only priority means defer deep claims until lineage verified.

## Non-goals for this phase

No unified "perfect optimization mod", no patch merging, no GPU/CUDA claims, no binary redistribution, no copying incompatible Mixins. These records collect independent techniques so products can choose modules based on real workload.

**Canonical MOD analysis completion status:** NOT_COMPLETE. **Benchmark status:** PERFORMANCE_NOT_VERIFIED. **Core knowledge claim promotion:** NONE. **Work resumed from existing lightweight genre PR #91**, not a new genre repository.

## Phase 2 source/repair continuation (2026-10-11)

Six target analyses extended beyond Phase 1: **[FerriteCore](../../mods/ferritecore/README.md)**, **[ModernFix](../../mods/modernfix/README.md)**, **[FastSuite](../../mods/fastsuite/README.md)**, **[ServerCore](../../mods/servercore/README.md)**, **[Particle Core](../../mods/particle-core/README.md)** and **[Embeddium](../../mods/embeddium/README.md)**. Each has a separate scoped human-readable history and machine-readable **research draft** (not import-ready until immutable CAS evidence is captured). See [Phase-2 checkpoint](PHASE-2-CHECKPOINT.md) and [Phase-2 receipt](PHASE-2-RECEIPT.json). All 58 initial manifest entries remain unchanged; **0 binary verifications and 0 runtime benchmarks**.

## Phase 3: renderer deepening (2026-10-11)

Six **different** culling/batching/cache MODs further reviewed: [BFRC](../../mods/brute-force-rendering-culling/README.md), [EntityCulling](../../mods/entityculling/README.md), [ImmediatelyFast](../../mods/immediatelyfast/README.md), [CullLeaves](../../mods/cullleaves/README.md), [BadOptimizations](../../mods/badoptimizations/README.md), [Bocchium](../../mods/bocchium/README.md). Combined with Phase 2, **12/27 subjects have scoped in-cohort deep dossiers**; these are **NOT whole-target COMPLETE** and are not validated benchmark outcomes. Start at [Phase 3 checkpoint](PHASE-3-RENDERING-CHECKPOINT.md), [render stack comparison](RENDER-STACK-CONFLICT-MATRIX.md), and [Phase 3 receipt](PHASE-3-RECEIPT.json). Original 58 filenames preserved; no binaries or runtime tests acquired.

## Phase 4/5: LOD renderer and memory leak research (2026-10-11)

Four more staged deepening filesets: [GPU Tape](../../mods/gputape/README.md), [Distant Horizons 3.2.0-b](../../mods/distant-horizons/README.md), [AllTheLeaks](../../mods/alltheleaks/README.md), [MemoryLeakFix](../../mods/memoryleakfix/README.md). Includes exact release Git tags/gitlink for DH, source version gates and eventbus fix gating, 1.0.5.1 GPU Tape source mismatch, cross-source compatibility matrix. See [checkpoint](PHASE-4-5-CHECKPOINT.md), [machine receipt](PHASE-4-5-RECEIPT.json) and [LOD/Memory interop](LOD-MEMORY-INTEROP-MATRIX.md). **16 of 27** core candidates have an individually scoped static source dossier, **none whole-target complete**, and JARs, CAS profiles, runtime and benchmarks all NOT_RUN.

## Phase 6: server/world processing (2026-10-11)

New [source/repair checkpoint](PHASE-6-CHECKPOINT.md) and [machine receipt](PHASE-6-RECEIPT.json): [Alternate Current](../../mods/alternate-current/README.md), [Starlight](../../mods/starlight/README.md), [Noisium](../../mods/noisium/README.md), [Clumps](../../mods/clumps/README.md) — selected source snapshots, three actual repair diffs, exact-version user-reported compatibility constraints and an [interop matrix](SERVER-WORLD-INTEROP-MATRIX.md). **20/27** core optimization candidate subjects have bounded selected-source deep dossiers; **0 whole-target COMPLETE, binary parity, runtime and benchmark results**. Total **50** catalog techniques. Starlight's old 1.1.3 and Noisium 2.7 branch-head locators were superseded in catalog by exact version-matching source commits; raw past checkpoints kept historical.

## Phase 7: source-backed remainder and unavailable original sources (2026-10-11)

[Checkpoint](PHASE-7-CHECKPOINT.md) / [machine receipt](PHASE-7-RECEIPT.json): [Dynamic FPS 3.11.4](../../mods/dynamic-fps/README.md) with correct 1.20.0–1.20.1 versioned source; [Get It Together Drops](../../mods/get-it-together-drops/README.md) and [Let Me Despawn](../../mods/let-me-despawn/README.md) with **other-version comparative source only**. [Canary/Saturn/SmoothBoot source-identity gates](PHASE-7-SOURCE-IDENTITY-GATES.md) document why their exact original Forge1.20.1 code is not yet analyzed. [Client/ItemEntity/despawn matrix](CLIENT-IDLE-DESPAWN-DROPS-MATRIX.md) preserves cross-mod correctness contracts. **23/27 partial in-cohort dossiers + 1 parent AI Improvements dossier**, **55 concept techniques**, 0 whole-target completion or performance benchmarks.
