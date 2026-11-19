# Minecraft Technology Analysis Catalog

**Adaptation anchor:** Minecraft **1.20.1 + Forge**

**Discovery frontier:** latest useful upstream implementation, regardless of Forge / NeoForge / Fabric when technically relevant.

| Queue | Target | Kind | ANCHOR — 1.20.1 Forge | FRONTIER — latest useful upstream | Overall |
|---:|---|---|---|---|---|
| 1 | [The Twilight Forest](../mods/twilight-forest/README.md) | content/gameplay Mod | source candidate `a7dd8f13` pinned; distributed-JAR identity pending | `793c4d4c` pinned — MC 26.1.2 / NeoForge 26.1.2.102 | IN_PROGRESS |
| 2 | [Sinytra Connector](../mods/sinytra-connector/README.md) | loader compatibility / translation layer | `7f68ac0` beta.50 source; 141 files acquired; binary/runtime unresolved | `c84a96a` beta.6 / 26.1.2; 131 files acquired | IN_PROGRESS (source/recon/history) |
| 3 | [Jujutsu Craft](../mods/jujutsu-craft/README.md) | content/gameplay / combat Mod | exact distributed JAR ver50.1 pinned — MC 1.20.1 / Forge 47+ / SHA-256 094247a3… | latest public distribution is same ver50.1; public source not found | IN_PROGRESS (static evidence-backed; runtime NOT_RUN) |
| 4 | [Jujutsu Kaisen (Jujutsu Verse)](../mods/jujutsu-verse/README.md) | content/gameplay / combat + VFX reference Mod | V8.1 pinned `d0f2f4e4…` (historical); [V9.0 selected static audit](../mods/jujutsu-verse/versions/9.0/README.md) pinned `fdf1f8a6…` — both MC 1.20.1 / Forge 47+ | latest reviewed public V9.0; separate artifact, no original source version-diff verified | V8.1 historical static; V9.0 PARTIAL_STATIC_ANALYSIS (runtime NOT_RUN; history NOT_ANALYZED) |

## Rules

- One target may have multiple independently pinned version/loader tracks.
- ANCHOR evidence and FRONTIER evidence must never be silently mixed.
- Preserve native 1.20.1 Forge code when it exists.
- Preserve and analyze newer upstream code too.
- If no native 1.20.1 Forge implementation exists, create an explicit backport/adaptation analysis instead of discarding the target.
- NOT_PINNED means the exact immutable snapshot is not fixed enough for reproducible technical claims.
