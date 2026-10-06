# FatePhantasms — Analysis Workspace

## Queue

- Upstream: `Terry0333/FatePhantasms`
- Kind: content/combat/VFX Mod
- Research emphasis: **skill presentation, summon/chant/charge/release choreography, beam/trail/custom geometry/screen-space/camera composition**
- Status: **STATIC VFX DEEP-DIVE COMPLETE — r205/r224/r284 binaries pinned and compared; r284 major skill presentation architecture is evidence-backed. Runtime performance and failure/repair history remain separate work.**

## Tracks

### ANCHOR — Minecraft 1.20.1 + Forge

- Current distributed target: `FatePhantasms-1.0.0-r284.jar`
- GitHub release tag: `8`
- Published: `2026-10-06T11:45:11Z`
- Size: `4,445,896` bytes
- SHA-256: `68158d03ae033577def23d51c4e238c8f9aa082243c8da16fbe0e4f9a3fcc88c`
- Declared platform: Minecraft `1.20.1` + Forge
- Direct r284 VFX dependency metadata: Photon `[1.1.17,)`, `mandatory=false`, `ordering=AFTER`
- The author's r224 release note described Photon + LDLib as prerequisites; the JAR itself directly declares Photon, which provides the LDLib-facing VFX stack.
- Source availability: upstream default branch exposes README/release binaries, not the full Mod source tree.
- Distribution bytecode/resource inventory: **EVIDENCE_BACKED** through version-pinned JAR inspection.
- License: `All Rights Reserved` in `META-INF/mods.toml`; do not treat this research as permission to copy code/assets.

### Historical comparison binaries

- r205 SHA-256: `1372be839df53214b53481dfce989486025c5d8b9273b0e3aa51450660ede9d1`
- r224 SHA-256: `6842008cea5107c13fa806bf433224841f3147c9c832be9d894837f0bf677d36`

The r205 → r224 transition is the key VFX architecture boundary:
- classes: **46 → 55**
- resources: **29 → 29**
- Photon/LDLib caller candidates: **0 → 9**
- new resource entries: **0**
- result: the enhancement is predominantly **procedural Java-side Photon composition**, not a new VFX resource pack.

### FRONTIER

No separate newer Minecraft/loader implementation was found in this pass. The current r284 1.20.1 Forge distribution is therefore also the newest observed upstream release.

## Current analysis coverage

- target identity / exact JAR hashes: **EVIDENCE_BACKED**
- release chronology: **EVIDENCE_BACKED**
- r205 → r224 Photon migration: **EVIDENCE_BACKED**
- Photon integration style (reflection/procedural emitter construction): **EVIDENCE_BACKED**
- Ea default cast timeline / server state / client timing packet: **EVIDENCE_BACKED**
- Ea Photon named layer graph: **EVIDENCE_BACKED**
- Ea custom beam geometry: **EVIDENCE_BACKED**
- Ea summon world renderer + Photon layer + full-screen finale + camera shake: **EVIDENCE_BACKED**
- Gate of Babylon deterministic layout, four volley presets, custom renderer, projectile trail, Photon enhancement: **EVIDENCE_BACKED**
- Enkidu 12-chain phased bind/release state machine and custom renderer: **EVIDENCE_BACKED**
- r284 custom sound-event inventory and phase-aware sound helpers: **EVIDENCE_BACKED**
- raw runtime performance / shader-pack behavior: **NOT_ANALYZED**
- live multiplayer latency/desync behavior: **NOT_ANALYZED**
- showcase-video visual timing confirmation: **DISCOVERED_NOT_REVIEWED**
- failure/repair history: **NOT_ANALYZED**

## Research documents

- [VFX-RESEARCH-2026-10-06.md](VFX-RESEARCH-2026-10-06.md) — initial upstream/dependency reconnaissance and design hypotheses
- [BINARY-VFX-DEEP-DIVE-2026-10-06.md](BINARY-VFX-DEEP-DIVE-2026-10-06.md) — authoritative binary-backed r205/r224/r284 deep dive
- [BINARY-VFX-EVIDENCE-2026-10-06.json](BINARY-VFX-EVIDENCE-2026-10-06.json) — machine-readable derived evidence summary

## Most reusable architecture finding

FatePhantasms r284 is not “a Photon effect Mod” in the simple sense. Its high-end presentation is a layered pipeline:

```text
server-authoritative skill state
→ compact timing / seed / phase packets
→ client animation state
→ deterministic layout reconstruction
→ custom vertex geometry for critical silhouettes
→ optional procedural Photon atmosphere/energy
→ GUI-space cinematic overlays
→ synchronized camera shake
→ phase-aware sound
```

The most useful KNEEKURA lesson is to build a shared cinematic-skill framework with these layers kept separable, rather than implementing every skill as one bespoke particle routine.

## Rights / evidence boundary

Do not commit upstream JARs, audio, textures, models, mesh payloads or decompiled source.
Retain only version identities, hashes, derived inventories, symbol/call relationships,
minimized numerical facts and independently written engineering conclusions.
