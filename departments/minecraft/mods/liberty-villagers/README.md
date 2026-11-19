# Liberty's Villagers — villager AI / village habits research

## Scope

- Target: **Liberty's Villagers** + current **Liberty’s Villagers Revived** maintenance line
- Focus: villager Brain/POI/pathfinding/sleep/work/breeding/profession habits, plus golem/cat village behavior
- TECH-HUB adaptation anchor: **Minecraft 1.20.1 + Forge**
- Research status: **TARGETED_VILLAGER_AI_MAPPED**
- Whole-target status: **IN_PROGRESS / NOT COMPLETE**
- Research date: 2026-10-04

This workspace records reusable engineering techniques and repair history. No Minecraft
implementation code is changed.

## Lineage

### Original design baseline

- repository: `gitsh01/libertyvillagers`
- branch: `v2-1.20.1-architectury`
- revision: `e0bade76b49a40950d69ba4ce7e5d51799e4ea7f`
- mod version: `2.0.0`
- Minecraft: `1.20.1`
- Forge: `47.1.47`
- Java: `17`
- Architectury: `9.1.12`
- source license: **CC0 1.0**
- CurseForge project: `700485`

### Current 1.20.1 maintained line

- source repository: `Leclowndu93150/Liberty-Villagers`
- branch: `1.20.1-architectury`
- revision: `f2e25484049366fe13ec48f7c1e4d97c94809898`
- source version: `2.0.2`
- Minecraft: `1.20.1`
- Forge: `47.1.47`
- Fabric + Forge
- source tree: **153 entries / 109 blobs / 78 Java files**
- Java split: **46 mixins / 8 configs / 6 custom tasks / 7 commands / 1 custom Goal**

Distributed Forge pin:

- CurseForge project: `1334457`
- file: `libertyvillagers-2.0.1+forge+1.20.1.jar`
- file ID: `6930028`
- uploaded: 2025-08-26
- loader: Forge
- release note: fixes Mowzie's Mobs crash and disables villager teleporting

The source branch has one later 2.0.2 source commit fixing PANIC movement. A released 2.0.2 Forge
binary is not asserted here, so source↔binary equality is **NOT_ESTABLISHED**.

### FRONTIER

- branch: `1.21.11`
- revision: `40e1384183c074bcfc63ae15b231c9bcd31429ad`
- version: `1.0.1`
- Minecraft: `1.21.11`
- Java: `21`
- modern branch license declaration: MIT

## Core result

Liberty's Villagers is best understood as a **vanilla villager Brain repair/extension layer**.

It does not replace Villager Brain with a new planner. Instead it:

1. expands and regularizes Point Of Interest search/reach rules;
2. repairs path-node completion and stuck recovery;
3. modifies hazard costs and traversal permissions;
4. rewrites the WORK task bundle to add profession habits;
5. adds explicit life policies for sleep, breeding, food and aging;
6. extends village guardians/cats into the same settlement-radius model;
7. includes unusually useful Brain/POI observability tools.

Most reusable TECH-HUB concepts:

- **POI policy as one shared contract** rather than many unrelated hard-coded ranges;
- **semantic arrival distance** for beds/workstations instead of exact-block obsession;
- **staged stuck recovery**: detect -> fuzzy reroute -> optional bounded teleport;
- **emergency priority protection**: optimization guards must yield to PANIC;
- **occupation-specific task bundles** layered into the normal Brain schedule;
- **profession-aware inventory/resource flow**;
- **target/reference-aware village boundaries** anchored by bells;
- **path hazards as configurable node penalties/forbidden types**;
- **AI observability from Brain memory transitions and POI ownership**.

Detailed report:
[VILLAGER-AI-RESEARCH-2026-10-04.md](VILLAGER-AI-RESEARCH-2026-10-04.md)

Failure/repair history:
[FAILURE-REPAIR-HISTORY.md](FAILURE-REPAIR-HISTORY.md)

Source inventory:
[SOURCE-INVENTORY-2026-10-04.json](SOURCE-INVENTORY-2026-10-04.json)

## Important boundaries

- 46 mixins make this a broad patch surface; many target Yarn synthetic/lambda methods.
- `VillagerTaskListProvider.createWorkTasks` is replaced wholesale, which is powerful but
  compatibility-sensitive.
- current source couples `findPOIRange` to Villager/Iron Golem generic follow range.
- expanded search ranges can increase work; no runtime benchmark was performed.
- source contains no independent high-level "culture planner" or social norm engine.
- schedule timing itself is largely vanilla; the mod changes what tasks do and when some POI search
  is allowed.
