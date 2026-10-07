# Minecraft Technology Analysis Catalog

**Adaptation anchor:** Minecraft **1.20.1 + Forge**

**Discovery frontier:** latest useful upstream implementation, regardless of Forge / NeoForge / Fabric when technically relevant.

| Queue | Target | Kind | ANCHOR — 1.20.1 Forge | FRONTIER — latest useful upstream | Overall |
|---:|---|---|---|---|---|
| 1 | [The Twilight Forest](../mods/twilight-forest/README.md) | content/gameplay Mod | source candidate `a7dd8f13` pinned; distributed-JAR identity pending | `793c4d4c` pinned — MC 26.1.2 / NeoForge 26.1.2.102 | IN_PROGRESS |
| 2 | [Sinytra Connector](../mods/sinytra-connector/README.md) | loader compatibility / translation layer | `7f68ac0` beta.50 source; 141 files acquired; binary/runtime unresolved | `c84a96a` beta.6 / 26.1.2; 131 files acquired | IN_PROGRESS (source/recon/history) |\n| 3 | [Wither: Reincarnated](../mods/wither-reincarnated/README.md) | content/gameplay Mod / vanilla Wither overhaul | exact user-supplied v1.0.5 JAR pinned (`00589726…ab80a`); 102 classes + Mixins/tags/AI/network mapped; runtime not run | not reviewed in this pass | STATIC_ANALYSIS_COMPLETE / RUNTIME_NOT_RUN |

## Rules

- One target may have multiple independently pinned version/loader tracks.
- ANCHOR evidence and FRONTIER evidence must never be silently mixed.
- Preserve native 1.20.1 Forge code when it exists.
- Preserve and analyze newer upstream code too.
- If no native 1.20.1 Forge implementation exists, create an explicit backport/adaptation analysis instead of discarding the target.
- NOT_PINNED means the exact immutable snapshot is not fixed enough for reproducible technical claims.
