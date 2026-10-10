# Raids: Enhanced — evidence-backed MOD research

**Research date:** 2026-10-11  
**State:** SOURCE STATIC ANALYSIS / RELEASE JAR NOT VERIFIED / RUNTIME NOT RUN  
**ANCHOR:** Minecraft 1.20.1 + Forge, official upstream `1.20.1` branch at [`6354ebf97faaeba79affaf7e71d01ed5ae651e85`](https://github.com/FINDERFEED/raidsenhanced/tree/6354ebf97faaeba79affaf7e71d01ed5ae651e85).  
**COMPARATIVE:** Minecraft 1.21.1 + NeoForge, `master` at [`a1a6ded47abc1504a5319a68716cf17a5838e0e6`](https://github.com/FINDERFEED/raidsenhanced/tree/a1a6ded47abc1504a5319a68716cf17a5838e0e6).  
**Mod/version:** `raidsenhanced` / `1.0.2`; author FINDERFEED; **All Rights Reserved**.

## Why this matters

A compact four-mini-boss raid expansion with unusually useful engineering patterns:
- existing vanilla `Raid` wave insertion without replacing all wave logic;
- six independently aimed side cannons plus a downward bomb attack on an airborne mini-boss;
- special flight navigation and player-piloted craft controls;
- burrow/reappear state choreography without continuous subterranean pathfinding;
- combat Goals combining artillery, melee area attack, ball lightning, radial lightning and a sustained beam;
- Bedrock-model FDLib animation and effect synchronization.

## Verified source scope

The pinned 1.20.1 Git tree contains **66 Java source files** and **113 resource files** (38 JSON / 58 PNG / 15 OGG / 1 TOML / 1 MCMETA). Source architecture and selected logic were read directly; these counts are *source-tree inventory*, **not** an inventory of the distribution JAR. The 1.21.1 comparative branch has 65 Java files in its observed Git tree. The branches **diverge**: do not infer that 1.21.1 implements identical 1.20.1 behavior.

- [Source repository](https://github.com/FINDERFEED/raidsenhanced)
- [1.20.1 ANCHOR tree](https://github.com/FINDERFEED/raidsenhanced/tree/6354ebf97faaeba79affaf7e71d01ed5ae651e85)
- [1.21.1 COMPARATIVE tree](https://github.com/FINDERFEED/raidsenhanced/tree/a1a6ded47abc1504a5319a68716cf17a5838e0e6)
- [External issue tracker](https://github.com/FINDERFEED/raidsenhanced/issues)
- [Current Minecraft research entry](../../CURRENT-HANDOFF-2026-10-02.md)

## Evidence products

- [ANALYSIS-RECEIPT-2026-10-11.json](ANALYSIS-RECEIPT-2026-10-11.json): immutable source identities, inspection scope and unresolved evidence gates
- [CODE-MAP.md](CODE-MAP.md): raid injection, classes, hooks, attributes, registries, client code
- [AI-BEHAVIOR.md](AI-BEHAVIOR.md): behavior and attack/state mechanics for all four raid bosses
- [NETWORKING-RENDERING-PERFORMANCE.md](NETWORKING-RENDERING-PERFORMANCE.md): network boundary, model/render flow, performance hypotheses and external defect reports
- [VERSION-COMPATIBILITY.md](VERSION-COMPATIBILITY.md): 1.20.1 Forge vs 1.21.1 NeoForge and issue matrix
- [TECHNIQUE-HARVEST.md](TECHNIQUE-HARVEST.md): portable abstractions and LAB validation tests
- [LICENSE-PROVENANCE.md](LICENSE-PROVENANCE.md): permission and copied-content exclusion

## Scope and epistemic boundary

- **DIRECT SOURCE:** source file declarations, formulas, control branches, enum/class references, resource paths, upstream license and build metadata.
- **REPORTED ONLY:** CurseForge/Modrinth feature descriptions and user-reported GitHub issues; not equivalent to observation.
- **NOT ESTABLISHED:** distributed 1.0.2 JAR SHA-256, source-to-binary match, Java/Forge runtime startup, multiplayer interoperability, performance or visual parity.
- **CANDIDATE engineering concept:** lessons in technique notes may inform independent work but do not automatically promote claims to canonical `VALIDATED` knowledge.

No source bodies, JAR binaries, decompiled trees, textures, models, animations or sounds are redistributed here.
