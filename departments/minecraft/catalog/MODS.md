# Minecraft Technology Analysis Catalog

**Adaptation anchor:** Minecraft **1.20.1 + Forge**

**Discovery frontier:** latest useful upstream implementation, regardless of Forge / NeoForge / Fabric when technically relevant.

| Queue | Target | Kind | ANCHOR — 1.20.1 Forge | FRONTIER — latest useful upstream | Overall |
|---:|---|---|---|---|---|
| 1 | [The Twilight Forest](../mods/twilight-forest/README.md) | content/gameplay Mod | source candidate `a7dd8f13` pinned; distributed-JAR identity pending | `793c4d4c` pinned — MC 26.1.2 / NeoForge 26.1.2.102 | IN_PROGRESS |
| 2 | [Sinytra Connector](../mods/sinytra-connector/README.md) | loader compatibility / translation layer | `7f68ac0` beta.50 source; 141 files acquired; binary/runtime unresolved | `c84a96a` beta.6 / 26.1.2; 131 files acquired | IN_PROGRESS (source/recon/history) |
| 3 | [Immersive Aircraft](../mods/immersive-aircraft/README.md) | aircraft physics / vehicle runtime dependency | official 1.3.3 Forge release fixed by Modrinth `GsVmbbkj`; source tag `550b38d3…`; physics/runtime boundary mapped; compiled-JAR byte equivalence unresolved | live 1.20.1 branch is 29 commits beyond the ANCHOR and materially changes core vehicle classes | IN_PROGRESS (physics / Kneekura-bird bridge / history partial) |

## Rules

- One target may have multiple independently pinned version/loader tracks.
- ANCHOR evidence and FRONTIER evidence must never be silently mixed.
- Preserve native 1.20.1 Forge code when it exists.
- Preserve and analyze newer upstream code too.
- If no native 1.20.1 Forge implementation exists, create an explicit backport/adaptation analysis instead of discarding the target.
- NOT_PINNED means the exact immutable snapshot is not fixed enough for reproducible technical claims.
