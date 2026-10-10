# Phase 7 — source identity gates for Canary, Saturn, Smooth Boot (Reloaded)

Created 2026-10-11. **Purpose:** distinguish exact Forge 1.20.1 distribution releases from a source tree that can actually be pinned and whose code is relevant. User explicitly limits research to MODs with source; **do not fabricate full source analysis from a name/author description or transcribe unrelated fork code as the 1.20.1 release**.

| Input row | User JAR + official origin | Original source result | Only defensible next step | Result |
|---|---|---|---|---|
| **21** | `canary-mc1.20.1-0.3.3.jar`, [CurseForge file 5089991](https://www.curseforge.com/minecraft/mc-mods/canary/files/5089991), Feb 8 2024, Forge, author AbdElAziz333, LGPLv3 | Author's plausible GitHub path `AbdElAziz333/Canary` **unavailable / cannot fetch**. No public official 0.3.3 Forge source commit pinned. | Actual release JAR and bytecode/version/config if available, or verifiable tagged source mirror; otherwise limit to **Lithium original conceptual comparison** | **SOURCE_ORIGINAL_UNAVAILABLE; NO_CODE_ANALYSIS for 0.3.3** |
| **27** | `saturn-mc1.20.1-0.1.3.jar`, [CurseForge Saturn 1.20.1 releases](https://www.curseforge.com/minecraft/mc-mods/saturn/files/all?page=1&version=1.20.1), Feb 9 2024, Forge, author AbdElAziz333 | Plausible `AbdElAziz333/Saturn` endpoint not accessible; no original 0.1.3 Forge source revision or bytecode | Need release source mirror with identity proof or actual JAR. MemoryLeakFix/Saturn overlap [issue #115](https://github.com/FxMorin/MemoryLeakFix/issues/115) is **1.18.2**, cannot assume 1.20.1 bug or redundant modules. | **SOURCE_ORIGINAL_UNAVAILABLE; NO_CODE_ANALYSIS for 0.1.3** |
| **07** | `smoothboot(reloaded)-mc1.20.1-0.0.4.jar`, [CurseForge file 5016280](https://www.curseforge.com/minecraft/mc-mods/smooth-boot-reloaded/files/5016280) Jan 8 2024 Forge, author AbdElAziz333, MIT | `AbdElAziz333/Smooth-Boot-Reloaded` unavailable. Two historic alternative public trees: [liangyaoyun209/SmoothBoot-Reloaded](https://github.com/liangyaoyun209/SmoothBoot-Reloaded/tree/8b1ba501f69bcefb37fb7fa1afd3a33b15ef2f89) source **1.18.2 Forge 1.0.1**; [FITFC/SmoothBoot-Reloaded](https://github.com/FITFC/SmoothBoot-Reloaded/tree/387c8a5cb14e6537bf604887a2c55261ed0cc9e5) source **1.19.2 Forge 0.0.2** (different owner). No exact 1.20.1 0.0.4 source identity or equivalence. | Keep old thread scheduling mechanism **HISTORICAL COMPARATIVE only**, release says main worker **config count** replacing raw core count, [Issue #19](https://github.com/AbdElAziz333/Smooth-Boot-Reloaded/issues/19) old endpoint inaccessible. Need exact 0.0.4 code/JAR before declaring defaults/behavior. | **SOURCE_ORIGINAL_UNAVAILABLE; HISTORICAL_SOURCE_ADJACENT only** |

## Honest upstream concept comparison for Canary, not an assertion about Canary code

Canary’s [CurseForge project description](https://www.curseforge.com/minecraft/mc-mods/canary) explicitly labels it an **unofficial Forge fork of Lithium**. The original [`CaffeineMC/lithium@1316ab1aafd888bf9881e924f29928f653ad2308` MC1.20.1 branch](https://github.com/CaffeineMC/lithium/tree/1316ab1aafd888bf9881e924f29928f653ad2308) has **524 Git blobs / 470 Java source paths**; this is **COMPARATIVE Fabric Lithium technology only**, NOT proof the Canary 0.3.3 JAR contains exactly those classes, Mixin switches or correctness repairs.

Lithium source path inventory includes `common/ai/pathing/PathNodeCache`, `common/block/BlockCountingSection`, `entity/movement_tracker`, `block/entity/inventory_change_tracking` and others. No body-level independent investigation was performed on this frontier in Phase 7, therefore don't add individual Lithium optimizations to the Canary catalog as proven. Separate [Noisium 2.3.0](../../mods/noisium/README.md) source specifically checks mod ID `canary` for **Lithium-related direct palette counter rebuild** — this is a source-backed **Noisium** compatibility decision, not Canary's own internal code inspection.

The [Canary 0.3.3 release change notes for MC1.18.2](https://www.curseforge.com/minecraft/mc-mods/canary/files/5089967) mention `ai.replace_streams.storage`, `ai.nearby_entity_tracking` and disabling overlapping Saturn changes; **same version label, different Minecraft-target file**. Even that changelog is AUTHOR_CLAIM, not proof of flags/behavior in user's **MC1.20.1** released JAR.

## Smooth Boot historic source concept: thread scheduling / priority, not proven 0.0.4 code

At comparative [FITFC 1.19.2 source `387c8a5cb14e6537bf604887a2c55261ed0cc9e5`](https://github.com/FITFC/SmoothBoot-Reloaded/tree/387c8a5cb14e6537bf604887a2c55261ed0cc9e5) `UtilMixin` substitutes Bootstrap and Background ForkJoinPools, and separate IO executor:
- Creates named worker threads with configured priorities, uses `ForkJoinPool` for bootstrap/background and `Executors.newCachedThreadPool` for IO.
- Source config default `bootstrapThreads=1`, `mainThreads=max(availableProcessors/2,1)` and thread priorities, version 0.0.2 only. `SmoothBootConfig.validate` appears to accidentally use `bootstrapPriority` in calculation of `bootstrapThreads` — **comparative source suspicion**, no testing or assertion that newer release still contains this.
- Replacing `Util.bootstrapExecutor/backgroundExecutor/ioPool` must respect Java 17 ForkJoin thread count, CPU oversubscription, async I/O and mod loading/classloader deadlock. Such technology could improve **startup responsiveness** but not automatically reduce total boot duration or server TPS.

Exact target [0.0.4 changelog](https://www.curseforge.com/minecraft/mc-mods/smooth-boot-reloaded/files/5016280) says **“uses a specific amount of main worker threads you can change ... old updates used number of available threads, resulting in worse performance”**. This is a **publisher description** of an important change vs old versions; do **not** reuse comparative source's `availableProcessors()/2` formula as verified target default. No runtime benchmarks.

## Provenance and scope controls

- Only related developer repos confirmed by GitHub read: legacy `liangyaoyun209/SmoothBoot-Reloaded`, `FITFC/SmoothBoot-Reloaded`, genuine `CaffeineMC/lithium`.
- Requests for likely author repositories `AbdElAziz333/Canary`, `AbdElAziz333/Saturn`, `AbdElAziz333/Smooth-Boot-Reloaded` produced **404 / NOT_FOUND** in this session. This might mean removed, renamed, made private, or a never-existing URL; **do not claim account deletion or conclusively no source exists anywhere**.
- CurseForge descriptions, community recommendations and version strings are discovery hints; no author claims promoted to code certainty.
- No third-party code/JAR copied. Original user local Windows path is not a mounted artifact. **No JAR SHA, GameTest, performance benchmark or canonical Core import**.

## Decision

Three source-gated targets remain **UNRESOLVED / SOURCE_NOT_ANALYZED**, not a claim that optimization cohort can be declared fully studied. When exact original source becomes available, prioritize a version-pinned tree plus Mixin and failure history; otherwise they remain deferred under user's explicit source-only rule. Count only separate source-backed modules (including comparative-only where clearly flagged) in progress.
