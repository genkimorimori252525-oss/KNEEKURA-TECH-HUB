# 軽量化 MOD Catalog

**Adaptation anchor:** Minecraft **1.20.1 + Forge**

**Discovery frontier:** latest useful upstream implementation

**General modern MOD catalog:** [../../catalog/MODS.md](../../catalog/MODS.md)

| Queue | Target | Main categories | ANCHOR | FRONTIER | Performance state | Overall |
|---:|---|---|---|---|---|---|
| 1 | [AI Improvements: Performance Tuning](../mods/ai-improvements/README.md) | `TICK_SIMULATION` / `ENTITY_BLOCKENTITY` / `CACHE_DATA_STRUCTURE` | 1.20.1 Forge **target**; original adjacent source **1.20 Forge 46**, `0.5.2` @ [`89c89590`](https://github.com/BuiltBrokenModding/AI-Improvements/tree/89c89590d8160f332bd2740acd0a67c96f37f00d); binary parity pending | [`26.3`](https://github.com/BuiltBrokenModding/AI-Improvements/tree/a51cab76acf89099ea3c41393d858f9e061dbe4b) NeoForge, source inventory only | **PERFORMANCE_NOT_VERIFIED** | Selected static mechanism evidence; full analysis and runtime NOT_RUN |

## Rules

- 主目的がperformance optimizationのMODをここへ置く。
- content MODの局所最適化は target を重複登録せず TECHNIQUES catalogから参照する。
- ANCHOR / FRONTIER evidenceを混ぜない。
- source mechanism と benchmark result を混ぜない。
- performance未計測なら `PERFORMANCE_NOT_VERIFIED` と書く。
- correctness regressionを隠して性能値だけを掲載しない。
- 太古の軽量化MODの原版は `kobun/` で扱う。
