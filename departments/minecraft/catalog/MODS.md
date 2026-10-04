# Minecraft Technology Analysis Catalog

**Adaptation anchor:** Minecraft **1.20.1 + Forge**

**Discovery frontier:** latest useful upstream implementation, regardless of Forge / NeoForge / Fabric when technically relevant.

| Queue | Target | Kind | ANCHOR — 1.20.1 Forge | FRONTIER — latest useful upstream | Overall |
|---:|---|---|---|---|---|
| 1 | [The Twilight Forest](../mods/twilight-forest/README.md) | content/gameplay Mod | source candidate `a7dd8f13` pinned; distributed-JAR identity pending | `793c4d4c` pinned — MC 26.1.2 / NeoForge 26.1.2.102 | IN_PROGRESS |
| 2 | [Sinytra Connector](../mods/sinytra-connector/README.md) | loader compatibility / translation layer | `7f68ac0` beta.50 source; 141 files acquired; binary/runtime unresolved | `c84a96a` beta.6 / 26.1.2; 131 files acquired | IN_PROGRESS (source/recon/history) |
| 7 | [Goofy Critters](../mods/goofy-critters/README.md) | exotic locomotion / multi-anchor movement | 1.0.0 Forge 1.20.1 file 7553632; release-era source candidate `9188e51`; exact binary/source identity unresolved | `96d01a7` archived frontier; Gestalt anchor locomotion + post-release NoSpin movement framework | IN_PROGRESS (targeted movement study complete) |

## Rules

- One target may have multiple independently pinned version/loader tracks.
- ANCHOR evidence and FRONTIER evidence must never be silently mixed.
- Preserve native 1.20.1 Forge code when it exists.
- Preserve and analyze newer upstream code too.
- If no native 1.20.1 Forge implementation exists, create an explicit backport/adaptation analysis instead of discarding the target.
- NOT_PINNED means the exact immutable snapshot is not fixed enough for reproducible technical claims.
