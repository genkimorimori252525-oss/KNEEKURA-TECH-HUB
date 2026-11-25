# One Dimension — scoped initial engineering research (2026-11-25)

Status: **PARTIAL / selected source analysis; runtime NOT_RUN; canonical promotion NONE**.
Follow [analysis specification](../../ANALYSIS-SPEC-v1.md) and [workflow](../../ANALYSIS-WORKFLOW.md). This is a research note, not a completed whole-target inventory or a runtime acceptance.

## Track identities and acquisition

| Track | Identity | Evidence status |
|---|---|---|
| ANCHOR | Minecraft 1.20.1 Forge, One Dimension 3.1.0, Modrinth ID IDoIWLlA; CodxLib >=1.3.6 | Release notes reviewed; JAR not acquired, binary hash and implementation UNKNOWN |
| FRONTIER source | Minecraft 26.3 Fabric, Codx-org/OneDimension commit 99285befab13cac3709a5661b8239fb277efba27, gradle.properties declares 4.0.1, Java 25, Fabric Loader 0.19.5 | Selected files fetched and blob hashes rechecked at exact commit; full tree/CAS/dependency closure not acquired |
| FRONTIER release | One Dimension 5.0.3, Minecraft 26.3 Fabric, CurseForge file 9101534, 2026-10-08; CustomChunks >=1.0.1 | Release notes only; source/binary equivalence NOT established; do not conflate with source snapshot |

Sources:
- https://modrinth.com/mod/one-dimension/version/IDoIWLlA
- https://modrinth.com/mod/one-dimension/version/3.0.0%2B1.21.10-forge (historical other-version behavior hint, not anchor code)
- https://modrinth.com/mod/one-dimension
- https://www.curseforge.com/minecraft/mc-mods/one-dimension/files/9101534
- https://www.curseforge.com/minecraft/mc-mods/customchunks
- https://github.com/Codx-org/OneDimension/tree/99285befab13cac3709a5661b8239fb277efba27

Local checkout/operating guides could not be accessed (companion tunnel disconnected). Container Maven download failed DNS. GitHub tracked AGENTS, AI-ENTRYPOINT, Minecraft README and analysis guides were read. No runtime launched, no existing worlds modified. No raw source/JAR committed. Modrinth lists CC-BY-NC-4.0, CurseForge CC-BY-NC-3.0, source metadata CC0-1.0; scope and exact artifact license need reconciliation before reuse; dependency licenses separate.

## ANCHOR — author claims, not implementation evidence

3.1.0 release notes describe Y bands with distinct generators and biome sources and a fixed Overworld anchor (-64..319). Standard example Nether -192..-65. 3.1.0 height modes reserve below/above the anchor respectively 256/960, 960/1712, 1968/1712 blocks, yielding total 1600/3056/4064 if simply summed with 384; note the older description says 1536, so exact dimension_type bounds require checking actual JAR/log (do not treat either as verified binary bounds). Config stacking.worldHeight, stacking.barrierThickness, blockBuildingAboveOverworld. Gap reduction before clipping terrain, warnings when a layout does not fit; fix band resolution for multiple lower bands, modded upper-band sky issue. Layout changes after generation risk incompatible existing chunks. Custom dimensions supported according to release documentation, not all mods tested.

## FRONTIER — selected direct static observations

The retrieved 4.0.1-declared source implements orchestration, not the low-level generator itself. Main build imports CustomChunks and Planeshift 1.0.0 as sibling Gradle composite builds; 5.0.3 release requires newer CustomChunks but has not been matched to this commit.

| File at pinned commit | Git blob SHA | Mechanism |
|---|---|---|
| gradle.properties | add7e84544115d7687925820bb3ef23a0d244957 | 26.3/4.0.1 source version |
| build.gradle | 37fc3f9e99c2d6ed88822f5d9a498cd7a1ab10a8 | dependency boundaries, Java 25, selftest run config |
| src/main/java/codx/OneDimension.java | c11a0ba98f60900bee7708e57554570bf7c372fe | onInitialize initializes OneWorld, Column, OpenFloors; SERVER_STARTED builds loop |
| src/main/java/codx/onedimension/OneWorld.java | 6eb476c1597a8ed3abd90c39101480e9915e6b4f | Stacks.replace(Level.OVERWORLD, OneWorld::stackFor); obtains registry level stems and world choice before initial chunks, constructs StackDefinition with order, anchor, gaps, trim, separate skies, spawn and portal scaling |
| src/main/java/codx/onedimension/Column.java | 97e2b30b4c9f59f858ca282efdac498a181ed53f | creates paired infinite planes at minY/maxYExclusive in SAME Overworld through Planeshift; global provider; end-tick fallback checks nonremoved/nonpassenger entities beyond either end by >2 blocks and offsets Y by total stack height, preserving velocity and rotation; resync player crossing detector |
| src/main/java/codx/onedimension/OpenFloors.java | 9fcb75a5e37ee0b2eb4969b353271e794fe40a54 | CHUNK_LOAD, only enabled stacked level; skip air/no-bedrock palette sections, look up band at section Y, skip configured kept bands; replace all bedrock in qualifying sections directly, mark unsaved if changed |
| src/main/java/codx/onedimension/WorldChoice.java | 6cd8b34b8f0618b52af7b0e5ea0f370480f82701 | per-world one-dimension.json, persisted order/settings; pending integrated-server choice; dedicated default; existing world without file OFF; malformed read throws rather than guessing |
| src/client/java/codx/client/mixin/CreateWorldScreenMixin.java | 69bc3a092cc8dc2332b0f3371441a4e2799bae9e | intercept onCreate, gather datapack and selected LevelStem, show StackScreen once then reenter creation |
| src/main/java/codx/onedimension/LoopSelfTest.java | 4dca831c4d5193d7952ff49f1cedcd72685e7874 | headless pig beyond bottom, checks after 20 ticks, optional fake-player tick logging; source only, not executed |

All file links: https://github.com/Codx-org/OneDimension/blob/99285befab13cac3709a5661b8239fb277efba27/<path> . Git blob SHA is not JAR SHA-256.

### Architecture and implications

1. World layout is saved before generation. OneWorld replaces the Overworld with a stack definition, keeping the Overworld identity. CustomChunks owns actual stacked generation; do not assert the precise chunk/noise coordinate translation until dependency source is inspected.
2. Internal band boundaries are physically continuous; only the outermost wrap uses paired Planeshift planes and fallback teleport. Thus ordinary digging between internal bands is not the same mechanism as wrapping.
3. OpenFloors is post-generation modification on chunk load, not replacement of a noise generator. Its predicate is bedrock anywhere in a qualifying section, not only the mathematical border. Nonstandard replacement blocks may violate assumptions about opacity, heightmaps, ticks or neighbors; this is an inference, not a reproduced bug.
4. The fallback scans all entities each end tick in loop mode (linear in iterated entity count). No measured TPS cost. It skips passengers and resyncs player crossing history; behavior for vehicles and very large multi-wrap displacements requires tests. No proof of fluid flow/render implementation from these files; those depend on libraries and release-specific code.
5. The 5.0.3 release notes add portal return routing and Nether water settings; separate loop fluids/mob settings are reported in 5.0.1 notes. Not established in the pinned source.

## Portability / next checks

ANCHOR can be studied natively, not by blindly copying 26.3 source. Obtain exact Forge JAR + CodxLib, SHA-256, full inventory, mixins/registries and mappings; follow generator dispatch, band-local height conversion, biome/structure/feature phases, lighting/heightmap/skylight, portal routing, dragon fight and spawn rules. FRONTIER needs exact 5.0.3 JAR, dependency closure including CustomChunks and Planeshift where applicable, pinned library source or bytecode, verify release correspondence. Check height limits and packet/chunk serialization, coordinate-sensitive mod checks (dimension ID vs physical band), biome-specific spawns, cross-band structures, fluid flow and render. Use authorized disposable-world LAB with boundary coordinates, representative modded dimensions, portal and entity crossing, save/reload, worldgen/MSPT/memory vs baseline; never use production save. Source selftest exists but no PASS claimed.

Failure history reconnaissance: 3.1.0 notes report wrong biome/mob selection for deeper lower bands, End sky wrongly applied to upper modded bands, and prior gap clipping. Actual issues/repair diffs not examined; required FAILURE-REPAIR-HISTORY facet NOT_ANALYZED. Video search results located but not viewed; no video-based implementation claim.

Facet status: ANCHOR NOT_ANALYZED (behavior discovery only); FRONTIER selected orchestration MAPPED with direct code observations; low-level generator, network, rendering, full inventory and failure/repair NOT_ANALYZED; runtime NOT_RUN; no Core claim promotion.
