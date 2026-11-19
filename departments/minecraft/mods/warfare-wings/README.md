# Warfare Wings — Analysis Workspace

## Current entry point

**ANCHOR static first pass complete; supplied-binary runtime remains UNKNOWN.**

This workspace records the 2026-10-07 analysis of the user-supplied
`warfare_wings-1.1.4-1.20.1-forge.jar` and is also the canonical home for future
Warfare Wings autonomous-flight, physical-reproduction and air-combat AI research.

Historical Kneekura-bird material may be used as evidence when its runtime identity is preserved,
but future work does not depend on that repository.

Start with:

- [ANCHOR-JAR-EVIDENCE.json](ANCHOR-JAR-EVIDENCE.json) — immutable identity and finite JAR inventory
- [TECHNICAL-ANALYSIS-2026-10-07.md](TECHNICAL-ANALYSIS-2026-10-07.md) — flight/weapon/data/client architecture
- [physics-ai/README.md](physics-ai/README.md) — **canonical physical-reproduction / autonomous-air-combat laboratory**
- [physics-ai/AIRCRAFT-PERFORMANCE-MODEL.md](physics-ai/AIRCRAFT-PERFORMANCE-MODEL.md) — explainable aircraft-to-aircraft performance differences
- [KNEEKURA-BIRD-SIMULATION-BRIDGE-2026-10-07.md](KNEEKURA-BIRD-SIMULATION-BRIDGE-2026-10-07.md) — historical design input retained for provenance
- [FAILURE-REPAIR-HISTORY.md](FAILURE-REPAIR-HISTORY.md) — bounded release-history review

The shared workflow remains [ANALYSIS-WORKFLOW.md](../../ANALYSIS-WORKFLOW.md) and
[ANALYSIS-SPEC-v1.md](../../ANALYSIS-SPEC-v1.md).

## ANCHOR — Minecraft 1.20.1 + Forge

User-supplied artifact:

- file name: `warfare_wings-1.1.4-1.20.1-forge.jar`
- size: `29,564,937` bytes
- SHA-1: `2f11c29973a563457bdc734ccc94fa6e17afbc68`
- SHA-256: `dc3029597c88859744633b6f5e4a9f21d449294b1aaac90ea0c1749d7aa98a43`
- embedded MOD version: `1.1.4`
- loader declaration: JavaFML `[47,)`
- mandatory dependency: `immersive_aircraft [1.1.0,)`, BOTH

This exact artifact is the ANCHOR for this research batch.

### Important identity warning

The supplied binary must **not** be treated as byte-identical to the public CurseForge 1.1.4 file.
CurseForge identifies the public Forge 1.20.1 release as file ID `7778796`; an independent
CurseForge-manifest index records SHA-1
`d0186bde4d69087d2317e692211447128a1d5314`, which differs from the supplied artifact.
The supplied JAR also contains `ai { role, faction, doctrine }` metadata in all 90 aircraft JSON
files, while the existing Kneekura-bird runtime-gap note records 0/90 AI blocks for the previously
used public runtime artifact.

Therefore older Kneekura-bird runtime qualifications are useful architectural evidence, but are not
silently transferred as runtime PASS evidence for this supplied JAR.

## Static coverage snapshot

- 220 Warfare Wings classes
- 90 aircraft data JSON files
- 24 base aircraft plus 66 livery/scheme entities
- all 90 aircraft JSON files contain an `ai` block in this supplied binary
- 12 weapon classes
- 12 bullet/bomb classes
- 101 client classes, dominated by aircraft / projectile renderers
- 106 item model JSON files
- 91 entity textures
- 104 recipes
- no active Warfare Wings mixins in the two shipped mixin configs
- no Warfare Wings-local packet/network class family found
- no Warfare Wings `sounds.json` or local sound class family found

## Current technical conclusion

Warfare Wings is primarily an **Immersive Aircraft addon** rather than an independent flight engine.
Its aircraft entities extend Immersive Aircraft airplane classes; its data supplies aircraft-specific
flight coefficients, geometry, seats and weapon mounts; its weapon classes extend Immersive Aircraft
weapon abstractions.

For future autonomous combat work, the reusable physics authority is therefore the exact
Immersive Aircraft 1.20.1 runtime behavior plus Warfare Wings' per-aircraft parameters and weapons.

## License / redistribution caution

There is conflicting metadata:

- the supplied JAR's `META-INF/mods.toml` says `GPL-3.0-only`;
- the public CurseForge and Modrinth project pages label the project All Rights Reserved, and the
  CurseForge description prohibits re-release.

This analysis does not resolve that contradiction. Raw JAR/assets are not committed here. Until the
rights conflict is independently resolved, preserve only hashes, locators, derived summaries and
small engineering facts needed for research.

## Status by facet

| Facet | State | Note |
|---|---|---|
| artifact identity | EVIDENCE_BACKED | supplied JAR hash and metadata pinned |
| loader / dependency boundary | EVIDENCE_BACKED | static JAR metadata |
| aircraft data / role metadata | EVIDENCE_BACKED | all 90 JSON inspected programmatically |
| flight physics ownership | MAPPED | Warfare Wings -> Immersive Aircraft; exact runtime dependency binary not acquired in this batch |
| weapons / projectiles | EVIDENCE_BACKED (static) | bytecode signatures and selected constants inspected |
| networking | MAPPED | delegated to Immersive Aircraft paths; no local packet family found |
| rendering/assets | INVENTORIED | renderer and asset families counted; full render behavior not deeply interpreted |
| runtime compatibility | NOT_ANALYZED | this supplied binary was not launched |
| performance | NOT_ANALYZED | no runtime measurements in this batch |
| failure/repair history | PARTIAL | bounded public release-note review; source repair diffs unavailable |
| ANCHOR↔FRONTIER portability | NOT_ANALYZED | current focus is 1.20.1 Forge |

## Physics AI laboratory

Future physical-reproduction and autonomous-air-combat development lives under
[`physics-ai/`](physics-ai/README.md), as part of the Warfare Wings analysis domain.

The core rule is unchanged: do not build a general Minecraft clone. Reproduce only the relevant
Immersive Aircraft fixed-wing state/update contract, preserve Warfare Wings aircraft-specific
parameters and weapons, and use exact Minecraft runtime tests as the parity oracle.

Historical Kneekura-bird measurements can be imported as legacy evidence, but the Tech Hub
Warfare Wings workspace is now the canonical project home.
