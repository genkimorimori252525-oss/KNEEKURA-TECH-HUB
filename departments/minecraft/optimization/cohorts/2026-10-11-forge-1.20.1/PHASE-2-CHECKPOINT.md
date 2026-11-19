# Lightweight cohort — Phase 2 selected source deepening

**Date:** 2026-10-11. Base inventory: [58 user-named JAR basenames](INPUT-MANIFEST.json) (27 core performance candidates / 3 related / 3 diagnostic / 25 utility); no JARs actually provided to this cohort. [Phase 1](README.md) mapped 16 selected mechanisms. This Phase 2 reviewed **six existing targets further**, rather than duplicating analyses as separate MODs.

## Reassessed targets with primary source and history

| Manifest ID | Source/track | Selectively reviewed main mechanism | History/correctness caveat | State |
|---|---|---|---|---|
| **02** [Embeddium](../../mods/embeddium/README.md) | Forge 1.20.1 source `dee0ebde`, 552 Git blobs / 499 Java | chunk rebuild workers bounded by CPU/heap, queue budget 2 jobs per worker; cancellation/epoch | 2023 queue fix and 1.20.1 0.3.0 shader report; **not same as JAR 0.3.31** | STATIC_PARTIAL |
| **03** [Particle Core](../../mods/particle-core/README.md) | `forge/1.20.1@8ae835f2`, 55 Git blobs | optional async sheets above 35% threshold, unsafe class main-thread retry, render-distance geometry check | Forge 1.20.1 particle display report; 1.21.11 Fabric RNG issue **comparison only** | STATIC_PARTIAL |
| **05** [FerriteCore](../../mods/ferritecore/README.md) | 1.20.0 source `e47bcbbd`, 102 blobs / 67 Java | mixed-radix `FastMap`; canonicalize quad vertices/voxel data, reload clear | #129 quad hash collision, before/after `Arrays.hashCode`→Murmur fold | STATIC_PARTIAL |
| **06** [ModernFix](../../mods/modernfix/README.md) | 1.20 source `cf04b47d`, 390 blobs / 339 Java | `LazyDataFixer`, guard `version>=newVersion`; compact all-zero palettes | #332 Litematica early-classload side effect, auto-disable module | STATIC_PARTIAL |
| **11** [FastSuite](../../mods/fastsuite/README.md) | Forge 1.20 source `883aed9f`, 28 blobs / 9 Java | ≥100 recipe threshold, split safe-parallel and serial recipe classes; `ForkJoinPool` classloader | Timeout returns empty, not vanilla fallback; newer 1.21 `StackedContents` repair; #47 not confirmed FastSuite cause | STATIC_PARTIAL |
| **49** [ServerCore](../../mods/servercore/README.md) | 1.20.1 source `d1d0a02d`, 135 blobs / 105 Java | disabled-by-default activation range, wakeup immunity, optional 35 MSPT adaptive sim/spawn/view policies | 2024 later-branch activation tick fix **not present** at pinned 1.20.1 source; #118 is 1.21.1 | STATIC_PARTIAL |

For each there is `FAILURE-REPAIR-HISTORY.md` plus `FAILURE-REPAIR-HISTORY.json`. The JSON is explicitly `research-draft.v1`, not an import-ready formal TechHub history record: immutable raw Issue/diff source CAS and document/index IDs are still absent. Read exact revision, observe license boundaries, do not promote results to `VALIDATED`.

## Lessons shared across target boundaries

1. **Memory vs lookup time:** dedup often saves memory, but poor hash distribution can make loader performance worse (Ferrite #129).
2. **Laziness vs class lifecycle:** deferring library instantiation can bypass loading side effects that third-party Mixins rely upon (ModernFix #332).
3. **Concurrency vs complete result:** recipe matches use a certified class subset, but timeouts may return no recipe rather than safely recomputing on main thread (FastSuite).
4. **Tick reduction vs game semantics:** sophisticated immunities/exclusions still change entity schedules; source-level recent fixes are **not guaranteed to exist in older ANCHOR** (ServerCore).
5. **Exception fallback vs thread safety:** async particle task might still race with chunk palettes even if `LegacyRandomSource` error caught (Particle Core).
6. **Throughput vs backlog freshness:** GPU/CPU chunk meshing benefits from queue-size budget **and result epoch**, not only high thread count (Embeddium).

## External/secondary reconnaissance (no technical claim promotion)

- [2026-07 Forge 1.20.1 Reddit modpack discussion](https://www.reddit.com/r/feedthebeast/comments/1up9cz7/all_around_best_performance_mod_setup_for_forge/): asks whether entity culling overlaps with Embeddium; conflicting comments and no source proof. Treated only as a reason to compare their distinct render paths.
- [2024-01 Forge community recommendations](https://www.reddit.com/r/feedthebeast/comments/197a8ju/i_need_a_good_performance_mod_for_my_forge_1201/): names Embeddium/FerriteCore/ImmediatelyFast/ModernFix; **recommendation is not a benchmark**.
- [ModernFix author CurseForge project](https://www.curseforge.com/minecraft/mc-mods/modernfix) describes multi-subsystem performance features and current releases; its main page does **not** bind to requested 5.27.66 JAR.
- GitHub Issues are **AUTHOR_CLAIM/USER_REPORT** evidence until actual source diff; all referenced closed Issue states are not runtime verification.

## No release/JAR/binary proof or GameTest

The user supplied Windows file paths as identifiers, not mounted JARs. No source-to-release hash correspondence or Forge 1.20.1 compilation; no causal TPS/FPS numbers, no CAS source snapshots, no background tests. Preserve previous PHASE-1 receipts as historical.

## Next bounded source batches, no architecture mixing

**Rendering:** BFRC + EntityCulling + ImmediatelyFast + CullLeaves + BadOptimizations / Bocchium, then finish Embeddium workqueue/render GL and phase transitions, optionally Distant Horizons GitLab.

**Memory/lifecycle:** AllTheLeaks + MemoryLeakFix; then FerriteCore 6.0.1 actual bytecode and resource reload. Saturn source ownership unresolved.

**Server/simulation:** Alternate Current / Starlight / Noisium / Clumps, then ServerCore mixed raid AI and genuine Canary origin. Treat AI Improvements as prior static analysis, not a new universal AI-speed candidate.

**Profiling:** spark / Observable for A/B evidence; neither considered a performance booster.

**High-risk filename gates:** `ImmediatelyFast-Forge-1.5.5+1.20.4.jar` from 1.20.1 folder, and `BetterAdvancements-NeoForge-1.20.1-0.6.0.73.jar`. Filename alone does **not** prove working/failed compatibility; need actual metadata before any launch.
