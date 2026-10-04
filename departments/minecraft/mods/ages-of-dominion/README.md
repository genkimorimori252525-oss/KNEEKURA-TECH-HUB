# Ages of Dominion — RTS technology research

## Scope

- Kind: Minecraft-native RTS / civilization / worker-and-army command system
- Research status: **TARGETED_RTS_ARCHITECTURE_MAPPED**
- Whole-target status: **IN_PROGRESS / NOT COMPLETE**
- TECH-HUB adaptation anchor: Minecraft **1.20.1 + Forge**
- Native upstream track: Minecraft **26.1.2 + NeoForge**
- Research date: 2026-10-04

This workspace records reusable engineering techniques from Ages of Dominion.
It does **not** copy upstream implementation code into KNEEKURA and does not change
Minecraft implementation code in this repository.

## FRONTIER source pin

- Upstream repository: `NssIs/Ages-of-Dominion-ModJam-2026`
- Exact revision: `c1e71a021ba88a053a378292c6011cb89828fd36`
- Upstream version: `4.2.0`
- Minecraft: `26.1.2`
- NeoForge: `26.1.2.87`
- Java: `25`
- Upstream license: **All Rights Reserved** for original code/art/assets
- Bundled music: separate CC0 material; see upstream `CREDITS.md`
- Source-distribution compiled identity: **not asserted**

Public distribution discovery:

- CurseForge project: `1676810`
- Release: `Forgotten Realms RTS v4.2.0 Bug Patch`
- File ID: `8845160`
- File: `forgotten_realms_rts-4.2.0.jar`
- Published: 2026-09-09
- Loader/version: NeoForge / Minecraft 26.1.2

## Source inventory

The exact recursive Git tree at the pinned revision was fully returned and was not truncated:

- tree entries: **473**
- blobs: **396**
- Java files: **166**
- resource files under `src/main/resources`: **217**
- Java top-level split under the mod package:
  - root RTS domain: **34**
  - client: **69**
  - network: **43**
  - entity: **12**
  - mixin: **4**
  - command: **1**
  - particle: **2**
  - sound: **1**

No ordinary `src/test` suite was present in the pinned tree. Source inspection is therefore
not promoted to runtime verification.

## Main result

Ages of Dominion is not built around one giant "RTS AI". It composes several deliberately
different layers:

1. **client selection / order intent**
2. **server validation and typed command routing**
3. **runtime tactical orders** for MOVE / ATTACK / HOLD
4. **persistent worker job state machines** for gathering, mining, farming, construction and repair
5. **low-frequency town/defense directors**
6. **vanilla navigation and combat Goals used as local executors**
7. **persistent realm/world state** separated by ownership domain
8. **night invasion / siege orchestration**
9. **Minecraft-aware placement, terrain and natural-tree classifiers**

The most useful finding is the priority structure:

`explicit player order > specialist work > temporary defense response > autonomous patrol`.

The full evidence map and 1.20.1 portability notes are in
[RTS-ARCHITECTURE-RESEARCH-2026-10-04.md](RTS-ARCHITECTURE-RESEARCH-2026-10-04.md).

The bounded repair-history review is in
[FAILURE-REPAIR-HISTORY.md](FAILURE-REPAIR-HISTORY.md).

## Important limits

- The upstream implementation is NeoForge 26.1.2, not native Forge 1.20.1.
- Upstream states multiplayer is not supported yet. Do not reuse current authority assumptions
  as a multiplayer security model.
- No formation-offset planner was found. Group movement currently sends one strategic destination
  to multiple individually pathfinding units.
- No runtime benchmark or distributed-JAR/source equivalence was established.
- All Rights Reserved means KNEEKURA should recover **concepts/contracts**, not transplant source.
