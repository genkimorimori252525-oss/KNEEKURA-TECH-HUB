# Chronoclones — targeted clone/replay research

## Scope

- Kind: recorded-player automation / clone replay MOD
- Current status: **TARGETED_CLONE_REPLAY_MAPPED**
- Whole-target status: **IN_PROGRESS / NOT COMPLETE**
- Adaptation anchor: Minecraft **1.20.1 + Forge**
- Research date: 2026-10-04

This workspace records the Chronoclones clone mechanism as a reusable technology study.
It does **not** add or modify Minecraft implementation code.

## Tracks

### ANCHOR — Minecraft 1.20.1 + Forge

- Project: Chronoclones
- Author: ballaler
- Release: **1.1**
- CurseForge project ID: `1625743`
- CurseForge file ID: `8986915`
- File name: `chronoclones-1.20.1-forge-1.1.0.jar`
- Published: 2026-09-27
- Distribution size reported by CurseForge: 535.7 KB
- CurseMaven coordinate: `curse.maven:chronoclones-1625743:8986915`
- Environment: client + server
- License advertised by CurseForge/Modrinth: MIT
- Distributed JAR SHA-256: **UNKNOWN / not acquired in this pass**
- Public source repository: **not found in the official project links or bounded web/GitHub search performed for this pass**

### FRONTIER — Minecraft 26.2 + NeoForge

- Release: **1.1**
- CurseForge file ID: `8986919`
- File name: `chronoclones-26.2-neoforge-1.1.0.jar`
- Published: 2026-09-27
- CurseMaven coordinate: `curse.maven:chronoclones-1625743:8986919`
- Source/binary equivalence with ANCHOR: **not asserted**

## Current result

The clone is best modeled as a **recorded-player routine executor**, not as a normal autonomous
Mob Goal/Brain AI. A player records movement and interactions, an Anchor replays the routine,
and one or more stateful clones perform the recorded work repeatedly.

The detailed evidence map, confidence labels, transferable techniques, and unresolved class-level
questions are in [CLONE-REPLAY-RESEARCH-2026-10-04.md](CLONE-REPLAY-RESEARCH-2026-10-04.md).

The bounded repair-history reconnaissance is in
[FAILURE-REPAIR-HISTORY.md](FAILURE-REPAIR-HISTORY.md).

## Evidence boundary

This pass uses author-maintained CurseForge/Modrinth project documentation, exact release metadata,
and release notes. The distributed 1.20.1 JAR was identified but could not be acquired into the
current analysis environment, so this pass does **not** claim:

- exact package/class names;
- Forge `FakePlayer` usage;
- exact NBT/Codec/data-component schema;
- exact packet/channel definitions;
- exact save location or entity implementation;
- source↔binary equivalence;
- runtime performance or compatibility.

Those remain explicit follow-up questions rather than inferred facts.
