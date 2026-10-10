# Scape and Run: Parasites — reconnaissance / technology leads (2026-10-11)

Status: **STAGED RECONNAISSANCE — NOT COMPLETE / NOT CANONICALLY VALIDATED**  
Primary investigation: Minecraft **1.12.2 Forge**, original author Dhanantry.  
Research procedure: [ANALYSIS-WORKFLOW.md](../../ANALYSIS-WORKFLOW.md), [ANALYSIS-SPEC-v1.md](../../ANALYSIS-SPEC-v1.md).  
Purpose: isolate evidence-supported invasion, infection, evolution, colony AI, block destruction and terrain-reversion techniques for possible **independent** Minecraft 1.20.1 Forge reimplementation, without copying copyrighted game code or assets.

## Scope and track boundaries

| Track | Target | Origin | Capture/verification | Current facet state |
| --- | --- | --- | --- | --- |
| ANCHOR (adaptation destination) | Minecraft 1.20.1 Forge | No official target artifact established | No 1.20.1 original binary/source | NOT_ANALYZED |
| FRONTIER | SRP 1.10.9 Alpha, Minecraft 1.12.2 Forge, 2026-09-01 | [CurseForge file 8787918](https://www.curseforge.com/minecraft/mc-mods/scape-and-run-parasites/files/8787918) | Release metadata only; no binary/JAR SHA/inventory | INVENTORIED (release metadata only) |
| COMPARATIVE stable original | SRP 1.9.21 Beta, Minecraft 1.12.2 Forge, 2024-05-25 | [CurseForge file 5370258](https://www.curseforge.com/minecraft/mc-mods/scape-and-run-parasites/files/5370258) | Official descriptions/release notes + external addon API-symbol cross-references; **original binary NOT acquired** | INVENTORIED (release metadata); some independent addon surfaces MAPPED |
| COMPARATIVE addon (not original) | Nischhelm/SRPMixins v2.x for SRP **1.9.21** / Forge 1.12.2 | [Commit `b950ff30f7c4fa19d5d3d3290c7977c179a69554`](https://github.com/Nischhelm/SRPMixins/tree/b950ff30f7c4fa19d5d3d3290c7977c179a69554) | Selected **original addon Java** directly inspected, not complete whole-tree interpretation; Gradle explicitly pins `curse.maven:scape-and-run-parasites-348025:5370258` | MAPPED (selected addon source only) |

All user-facing behavior from wikis/Reddit is a **BehaviorHint**, not direct proof of actual Java control flow. Likewise, a Mixin target names an original SRP symbol, but an overwritten method body is **addon implementation**, not original SRP source. No proof exists here that SRPMixins runs with Alpha 1.10.9. Original SRP is All Rights Reserved; SRPMixins independently declares MIT. Do not merge or relicense the two.

SourceRef retrieval/review date: 2026-10-11 (Asia/Tokyo). Web/connector reads here were not stored as immutable raw HTTP snapshots with content SHA-256; preserve this outstanding provenance gap. No original JAR/bytecode hashes, class inventory, runtime traces, performance numbers or compatibility PASS are claimed.

## BehaviorHint → FeatureMap — early reconnaissance

| Facet | Finding/hint | Basis and locator | State |
| --- | --- | --- | --- |
| Evolution Phases / points | Evolution stages gate parasite strength/spawns/colony opportunities; point-producing behavior and dimension-scoped `SRPSaveData` references exist. Thresholds are version/config sensitive. | [Official description](https://www.curseforge.com/minecraft/mc-mods/scape-and-run-parasites); [SRPMixins CapabilityEvoPoints.java](https://github.com/Nischhelm/SRPMixins/blob/b950ff30f7c4fa19d5d3d3290c7977c179a69554/src/main/java/srpmixins/capability/chunkphases/CapabilityEvoPoints.java) | INVENTORIED original / MAPPED addon |
| Individual infection/assimilation | Hosts turn into infected/assimilated parasite species; COTH exists. Specific conversion code not acquired. | [Official description](https://www.curseforge.com/minecraft/mc-mods/scape-and-run-parasites); [community Evolution System](https://scape-and-run-parasites.fandom.com/wiki/Evolution_System) | INVENTORIED |
| Merging and evolution | Infected/moving-flesh organisms combine and upgrade under conditions. | [Official description](https://www.curseforge.com/minecraft/mc-mods/scape-and-run-parasites) | INVENTORIED |
| Global/colony adaptation | Official 1.9.2 notes describe colonies recording learned damage types, transmitting common adaptation to newly spawned parasites, and forgetting upon core destruction. This is **release author claim for 1.9.2**, not proof of unchanged 1.9.21/1.10.9 runtime. | [Official 1.9.2 changelog](https://www.curseforge.com/minecraft/mc-mods/scape-and-run-parasites/files/3728258) | INVENTORIED |
| Reinforcement / Beckons | Parasite deaths/residue can summon staged Beckons, which infest blocks and lead to stronger territory/hive growth. | [Official description](https://www.curseforge.com/minecraft/mc-mods/scape-and-run-parasites); [Community reinforcement wiki](https://scape-and-run-parasites.fandom.com/wiki/Reinforcement_System) | INVENTORIED |
| Beckon block infusion, stable range | SRP 1.9.21 changelog assigns configured Stage I/II/III infestation ranges **8/16/32**; actual radius shape and vertical reach not recovered. | [Official 1.9.21 release notes](https://www.curseforge.com/minecraft/mc-mods/scape-and-run-parasites/files/5370258) | INVENTORIED |
| Block destruction API lead | **Addon direct observation:** `BlockBreakBlacklist.java` wraps `EntityParasiteBase.skillBreakBlocks` → `blockException` and filters by block ID/metadata and parasite ID. This confirms selected addon interception contract, not original method body. | [Pinned addon class](https://github.com/Nischhelm/SRPMixins/blob/b950ff30f7c4fa19d5d3d3290c7977c179a69554/src/main/java/srpmixins/mixin/features/BlockBreakBlacklist.java) | MAPPED (addon) |
| Infestation AI class/API lead | **Addon direct observation:** `AIBlockInfestFix.java` targets `EntityAIBlockInfest.updateTask`. | [Pinned addon class](https://github.com/Nischhelm/SRPMixins/blob/b950ff30f7c4fa19d5d3d3290c7977c179a69554/src/main/java/srpmixins/mixin/deterrenttweaks/AIBlockInfestFix.java) | MAPPED (addon) |
| Biome/Beckon block conversion | **Addon direct observation:** `InfestationOverhaul.java` overwrites `ParasiteEventWorld.canInfestBlock`. **Addon** checks block material/hardness/blacklist and adjacent faces, sets `InfestedStain/Rubble/Trunk`, counts conversions and updates evolution points. The algorithm is NOT claimed as unmodified SRP implementation. | [Pinned addon class](https://github.com/Nischhelm/SRPMixins/blob/b950ff30f7c4fa19d5d3d3290c7977c179a69554/src/main/java/srpmixins/mixin/deterrenttweaks/InfestationOverhaul.java) | MAPPED (addon) |
| Dynamic infestation event | **Addon-defined** `BlockInfestationEvent` holds old/new block states, stage, generator flags and cancelability; comment explicitly states not fired on reversion. | [Pinned addon class](https://github.com/Nischhelm/SRPMixins/blob/b950ff30f7c4fa19d5d3d3290c7977c179a69554/src/main/java/srpmixins/event/BlockInfestationEvent.java) | MAPPED (addon) |
| Infestation revert vs faithful reconstruction | Official 1.9.13 says config `Reinforcement System Revert Block` default dirt → gravel. **Addon** `InfestationReversionToggle` intercepts `EntityPStationaryArchitect.freeDead` block-set/schedule calls. This is configured block reversion, **not proof of exact original player block reconstruction**. | [Official 1.9.13 changelog](https://www.curseforge.com/minecraft/mc-mods/scape-and-run-parasites/files/5062205); [Pinned addon reversion toggle](https://github.com/Nischhelm/SRPMixins/blob/b950ff30f7c4fa19d5d3d3290c7977c179a69554/src/main/java/srpmixins/mixin/deterrenttweaks/InfestationReversionToggle.java) | MAPPED addon / INVENTORIED original |
| Region-scale evolution | **Addon feature, disabled by default:** `ChunkPhaseConfig` permits chunk-region phases instead of dimension/global phases; `CapabilityEvoPoints.updateNearby` uses `getLoadedChunk` to avoid force loading unloaded chunks and buffers point changes. Not base-SRP behavior. | [Pinned addon config](https://github.com/Nischhelm/SRPMixins/blob/b950ff30f7c4fa19d5d3d3290c7977c179a69554/src/main/java/srpmixins/config/folders/ChunkPhaseConfig.java); [CapabilityEvoPoints](https://github.com/Nischhelm/SRPMixins/blob/b950ff30f7c4fa19d5d3d3290c7977c179a69554/src/main/java/srpmixins/capability/chunkphases/CapabilityEvoPoints.java) | MAPPED (addon) |
| Worldgen/packet performance | Addon `ParaBiomeConfig` comments report forced chunk loads from vines/bush generation and single-position biome packets, offering toggleable fixes. Profiling original SRP remains NOT_RUN. | [Pinned addon config](https://github.com/Nischhelm/SRPMixins/blob/b950ff30f7c4fa19d5d3d3290c7977c179a69554/src/main/java/srpmixins/config/folders/ParaBiomeConfig.java) | MAPPED addon claim; original NOT_ANALYZED |

## Scoped Failure / Repair leads (NOT yet formal imported Failure History)

History window: public issue tracker for Alpha v1.10.7–1.10.9 (2026) and official 1.9.13/1.9.21 release notes, focusing on `infestation`, `evolution`, `spawning`, `griefing`, `performance`. This was a bounded search and selected reading, **not all-Issues review**. Before/after exact original diff unavailable; no repair verification.

1. [Issue #33 — infestation reverting fails](https://github.com/Sereath/SRParasites-IssueTracker/issues/33): reporter on 1.10.8 says revert fails despite conditions. Symptom **REPORTED**; cause **UNKNOWN**; fix **NOT_VERIFIED**.
2. [Issue #18 — light-source setting affects broad griefing](https://github.com/Sereath/SRParasites-IssueTracker/issues/18): reporter describes a block-destruction configuration mismatch. Symptom **REPORTED**; cause **UNKNOWN**.
3. [Issue #1 — phase -2 spawning check still consumes server tick](https://github.com/Sereath/SRParasites-IssueTracker/issues/1): reporter 1.10.7 / Cleanroom traces `SRPWorldParasiteSpawner.tickSpawn` and calls for early short circuit. Symptom **REPORTED**; no local profiler/run.
4. [Issue #55 — GenLayer worldgen performance](https://github.com/Sereath/SRParasites-IssueTracker/issues/55): report for 1.10.9, with disputed/method-limited profiling significance. Keep counterevidence.
5. [Issue #12 — Node evolution points capped unexpectedly](https://github.com/Sereath/SRParasites-IssueTracker/issues/12) and [Issue #19 — unloaded-dimension cooldown](https://github.com/Sereath/SRParasites-IssueTracker/issues/19): alpha phase-accounting regression leads; cause/fix **UNKNOWN**.

Community leads only: [r/feedthebeast block-griefing config discussion](https://www.reddit.com/r/feedthebeast/comments/1ahrz4c), [invasion counterplay/cleanup](https://www.reddit.com/r/feedthebeast/comments/15ze6rs), [community phases wiki](https://scape-and-run-parasites.fandom.com/wiki/Evolution_Phases). Different guides/configs show divergent point threshold numbers; do **not** reuse numbers without version/config/bytecode anchoring.

## Candidate reusable techniques — independent implementation hypotheses

These are design proposals, NOT assertions about the original MOD internals.

- **ThreatDirector**: region- or dimension-scoped event-sourced invasion budget/phase with capped points, cooldown and state persistence; separate entity adaptation memory and colony/faction adaptation memory.
- **Territory/Nexus**: spawned Beckons/colony cores own bounded territory and finite tick budget, spawn budgets, structural conversion rules and destruction cleanup.
- **WorldMutationJournal**: when KNEEKURA mobs *temporarily* break, build or infect, record (dimension, position, original block state, optional BlockEntity NBT, owner/event/epoch, expected temporary state, expiry) and restore only if current block still matches MOD-owned mutation. Queue across chunk unloads; avoid force-loading all chunks, bound memory/I/O; specify conflicting player edits and multi-owner precedence. This achieves exact restoration unlike `Revert Block` default replacement.
- **Batch and lazy updates**: aggregate changes per loaded chunk/region, network deltas and capped processing per tick; do not perform redundant expensive disabled-dimension scans. Validate TPS and restoration fidelity under bounded LAB worlds.
- **Player counterplay**: lures/purifiers, defeat hives to suppress expansion, adaptation reset on core destruction, protected terrain whitelist and configurable damage cap. Not all protections are confirmed in each upstream version.

## Next evidence gates

1. Acquire immutable **original** stable SRP 1.9.21 JAR and Alpha 1.10.9 JAR from verified official releases; record exact size, SHA-256, mod metadata, dependency identity, JAR tree/class inventory and license. Check existing owned inputs first; do not commit raw JAR/decomp/assets.
2. Perform original stable bytecode/decomp mapping for `EntityParasiteBase.skillBreakBlocks`, `EntityAIBlockInfest.updateTask`, `EntityPStationaryArchitect.freeDead`, `ParasiteEventWorld.canInfestBlock`, `SRPSaveData`, adaptation, COTH/assimilation, colony cores, spawn and worldgen logic. Verify addon target method descriptors against **stable original JAR**, do not infer from Mixin alone.
3. Independently map Alpha 1.10.9 and compare behavioral semantics/changed configs to 1.9.21. Keep version tracks separate.
4. Capture Issue/PR/release source snapshots with provenance and before/after diffs where available, then author `FAILURE-REPAIR-HISTORY.md` and valid `FAILURE-REPAIR-HISTORY.json` following repo schema. Until then this section remains `PARTIAL` reconnaissance.
5. Test in bounded authorized LAB environment only with separately pinned runtime identities, pass/fail assertions (block restoration, chunk unload, player edits, TPS, per-type griefing controls, phase persistence) and cleanup evidence.
6. Write explicit Minecraft 1.20.1 Forge redesign/backport comparison, loader/API and mappings changes. No direct transplantation of copyrighted MOD code/assets.

**Unverified:** Original JAR class and bytecode semantics, final latest-Alpha precise algorithms, exact block restoration, all bosses/entities, animation/render/audio, full resources, multiplayer/runtime/lag and fixes. **Whole target completion: NOT CLAIMED.**
