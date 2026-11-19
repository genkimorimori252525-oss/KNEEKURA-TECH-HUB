# Minecraft Technology Analysis Catalog

**Adaptation anchor:** Minecraft **1.20.1 + Forge**

**Discovery frontier:** latest useful upstream implementation, regardless of Forge / NeoForge / Fabric when technically relevant.

| Queue | Target | Kind | ANCHOR — 1.20.1 Forge | FRONTIER — latest useful upstream | Overall |
|---:|---|---|---|---|---|
| 1 | [The Twilight Forest](../mods/twilight-forest/README.md) | content/gameplay Mod | source candidate `a7dd8f13` pinned; distributed-JAR identity pending | `793c4d4c` pinned — MC 26.1.2 / NeoForge 26.1.2.102 | IN_PROGRESS |
| 2 | [Sinytra Connector](../mods/sinytra-connector/README.md) | loader compatibility / translation layer | `7f68ac0` beta.50 source; 141 files acquired; binary/runtime unresolved | `c84a96a` beta.6 / 26.1.2; 131 files acquired | IN_PROGRESS (source/recon/history) |
| 3 | [Wither: Reincarnated](../mods/wither-reincarnated/README.md) | content/gameplay Mod / vanilla Wither overhaul | exact user-supplied v1.0.5 JAR pinned (`00589726…ab80a`); 102 classes + Mixins/tags/AI/network mapped; runtime not run | not reviewed in this pass | STATIC_ANALYSIS_COMPLETE / RUNTIME_NOT_RUN |
| 4 | [Fungal Infection: Spore](../mods/fungal-infection-spore/README.md) | Infection/ecology + Hivemind AI | 2.2.0j user-provided SHA-256 `d20c4be6…1489`; selected Proto, Womb, Mound, group targeting and combat bytecode MAPPED; runtime NOT_RUN | 1.21.1 NeoForge metadata only / no binary reviewed | IN_PROGRESS (selected STATIC); NOT COMPLETE |
| 5 | [Chronoclones](../mods/chronoclones/README.md) | recorded-player automation / clone replay | 1.1 / Forge 1.20.1 file `8986915` metadata pinned; targeted clone-replay behavior mapped; JAR/source not acquired | 1.1 / NeoForge 26.2 file `8986919` metadata pinned | IN_PROGRESS (targeted clone study complete; whole-target incomplete) |
| 6 | [Ages of Dominion](../mods/ages-of-dominion/README.md) | Minecraft-native RTS / unit-worker command system | no native 1.20.1 Forge source; explicit backport boundary mapped | `c1e71a0` / v4.2.0 / MC 26.1.2 NeoForge; 166 Java files inventoried | IN_PROGRESS (targeted RTS architecture mapped) |
| 7 | [Olympus!](../mods/olympus/README.md) | flying combat mob / 3D navigation | `dcaccaa` / v1.0.8 / Forge 1.20.1 native; targeted Harpy flight AI mapped | `31237b1` / v1.0.9 / MC 1.21.1; core Harpy flight logic source-equivalent | IN_PROGRESS (targeted flight study complete) |
| 8 | [Liberty's Villagers](../mods/liberty-villagers/README.md) | villager Brain / POI / village habits | Revived source `f2e2548` / MC 1.20.1 Forge line; distributed Forge 2.0.1 file 6930028; 78 Java / 46 mixins | `40e1384` / Revived MC 1.21.11 | IN_PROGRESS (targeted villager AI study complete) |
| 9 | [Goofy Critters](../mods/goofy-critters/README.md) | exotic locomotion / multi-anchor movement | 1.0.0 Forge 1.20.1 file 7553632; release-era source candidate `9188e51`; exact binary/source identity unresolved | `96d01a7` archived frontier; Gestalt anchor locomotion + post-release NoSpin movement framework | IN_PROGRESS (targeted movement study complete) |
| 10 | [Youkai's Homecoming](../mods/youkai-homecoming/README.md) | danmaku / spell-card / virtual projectile system | `6d57442` / v2.7.0 / MC 1.20.1 Forge 47.1.3; targeted danmaku architecture mapped | current upstream remains same 2.7.0 / 1.20.1 source line | IN_PROGRESS (targeted danmaku study complete) |
| 11 | [Kimetsu no Yaiba ver3](../mods/kimetsu-no-yaiba/README.md) | content/combat/worldgen Mod | uploaded JAR SHA `b4af6e8a…` / v3 / MC 1.20.1 Forge; 3,713 classes; bytecode whole-target map | no official public source/frontier pinned; current public 1.20.1 release is same ver3 line | IN_PROGRESS (static whole-target architecture mapped) |

## Rules

- One target may have multiple independently pinned version/loader tracks.
- ANCHOR evidence and FRONTIER evidence must never be silently mixed.
- Preserve native 1.20.1 Forge code when it exists.
- Preserve and analyze newer upstream code too.
- If no native 1.20.1 Forge implementation exists, create an explicit backport/adaptation analysis instead of discarding the target.
- NOT_PINNED means the exact immutable snapshot is not fixed enough for reproducible technical claims.
