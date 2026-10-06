# FatePhantasms — Analysis Workspace

## Queue

- Upstream: `Terry0333/FatePhantasms`
- Kind: content/combat/VFX Mod
- Research emphasis: **skill presentation, summon/chant/charge/release choreography, beam/trail/post-processing composition**
- Status: **IN_PROGRESS — VFX reconnaissance and dependency-source analysis complete; target JAR internals not yet acquired through the current connector path**

## Tracks

### ANCHOR — Minecraft 1.20.1 + Forge

- Current distributed target: `FatePhantasms-1.0.0-r284.jar`
- GitHub release tag: `8`
- Published: `2026-10-06T11:45:11Z`
- Size: `4,445,896` bytes
- SHA-256 published by GitHub: `68158d03ae033577def23d51c4e238c8f9aa082243c8da16fbe0e4f9a3fcc88c`
- Declared platform: Minecraft `1.20.1` + Forge
- Declared VFX prerequisites since the enhanced-effects release: **Photon + LDLib**
- Source availability: the upstream default branch currently exposes the README, not the Mod source tree
- Distribution bytecode/resource inventory: **NOT_ANALYZED** in this pass because the binary release could not be materialized through the current GitHub connector
- License locator: CurseForge project metadata reports **All Rights Reserved**; do not treat this research as permission to copy code/assets

### FRONTIER

No separate newer Minecraft/loader implementation was found in this pass. The current r284 1.20.1 Forge distribution is therefore also the newest observed upstream release, but ANCHOR claims are kept separate from any future branch/version.

## Current analysis coverage

- target identity and release chronology: **EVIDENCE_BACKED**
- Photon/LDLib dependency transition: **EVIDENCE_BACKED** as an upstream release claim
- summon / chant / charge presentation evolution: **EVIDENCE_BACKED** as upstream release-history claims
- Photon 1.20.1 entity-bound FX runtime: **EVIDENCE_BACKED for dependency capability**
- Photon 1.20.1 beam / trail / bloom facilities: **EVIDENCE_BACKED for dependency capability**
- exact FatePhantasms use of each Photon facility: **MAPPED as inference only; target JAR proof pending**
- Gate of Babylon / Enkidu spatial choreography: **SECONDARY_BEHAVIOR_HINT only** where derived from an independent recreation that explicitly cites FatePhantasms as inspiration
- exact target FX resource inventory, shader/material definitions, sound hooks, camera shake, post-processing graph, skill-to-effect binding and server/client packets: **NOT_ANALYZED**
- showcase videos: **DISCOVERED_NOT_REVIEWED** in this pass; no fabricated timestamps or visual claims
- failure/repair history: **NOT_ANALYZED**

See [VFX-RESEARCH-2026-10-06.md](VFX-RESEARCH-2026-10-06.md).

## High-value next acquisition

The most informative next static pass is not another broad web search. It is a versioned binary differential:

1. acquire r284 and verify the published SHA-256 above;
2. inventory `META-INF/mods.toml`, classes, `assets/`, sounds, models/textures and Photon project/FX resources;
3. search bytecode/decompiled source for Photon entrypoints such as entity/block effects, FX runtime creation, beam/trail emitters and effect-resource locators;
4. acquire r205 and r224 if available and compare them, because r224 is the declared enhanced-effects transition where Photon + LDLib became prerequisites and chant/charge effects were heavily reworked;
5. only after the static map exists, use the showcase videos or bounded live observation to confirm timing, camera-facing behavior, multiplayer synchronization and impact/afterglow phases.

Do not commit upstream JARs, extracted assets or other licensed raw material to normal TECH HUB Git history. Commit only derived inventories, hashes, locators and minimized engineering findings.
