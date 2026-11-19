# Optimization Techniques Catalog

MOD単位ではなく、**再利用できる軽量化技術単位**の横断catalog。

| ID | Category | Technique | Source target | Track | Mechanism evidence | Benchmark state | Correctness boundary | Reuse status |
|---|---|---|---|---|---|---|---|---|
| `AI-GOAL-PRUNING` | `TICK_SIMULATION`, `ENTITY_BLOCKENTITY` | 対象Goalの任意削除で実行を省く | [AI Improvements](../mods/ai-improvements/OPTIMIZATIONS.md) | 1.20 Forge adjacent to ANCHOR | `ModifierLayer`, `FilteredRemove` | **PERFORMANCE_NOT_VERIFIED** | Mobの行動・演出自体が変化、既定では主な除去はfalse | CONCEPT_ONLY |
| `AI-TRIG-LOOKCONTROL` | `CACHE_DATA_STRUCTURE`, `ENTITY_BLOCKENTITY` | `atan2`を約256 KiBの表参照で近似 | [AI Improvements](../mods/ai-improvements/OPTIMIZATIONS.md) | 1.20 Forge adjacent to ANCHOR | `FastTrig`, `FixedLookControl` | **PERFORMANCE_NOT_VERIFIED** | 精度・狙い・カスタムLookControl互換性を再検証 | CONCEPT_ONLY |
| `AI-FILTER-HIT-ORDER` | `TICK_SIMULATION`, `CACHE_DATA_STRUCTURE` | 頻出フィルタを前に寄せる | [AI Improvements](../mods/ai-improvements/OPTIMIZATIONS.md) | 1.20 Forge adjacent to ANCHOR | `FilterLayer`, `ModifierLayer` | **PERFORMANCE_NOT_VERIFIED** | 順序変更・副作用・宣言だけの設定を確認 | EXPERIMENT_CANDIDATE |
| `AI-EVENT-HOOK-DEDUP` | `TICK_SIMULATION`, `ENTITY_BLOCKENTITY` | 重複スポーンイベント処理を削除 | [AI Improvements](../mods/ai-improvements/FAILURE-REPAIR-HISTORY.md) | historical 1.19/1.20 source ancestry | [diff 2e95e6e](https://github.com/BuiltBrokenModding/AI-Improvements/commit/2e95e6e62edeea7cfd86a06865d5cebaf190ab39) | **PERFORMANCE_NOT_VERIFIED** | エンティティ初期化が漏れないことを検証 | CONCEPT_ONLY |
| `AI-PATH-REPATH-THROTTLE` | `TICK_SIMULATION`, `ENTITY_BLOCKENTITY` | ターゲット距離・経路末端の精度で再探索を間引く | [旧Epic Siege Mod 1.12比較](https://github.com/da3dsoul/Epic-Siege-Mod/commit/a51465f74452f74e8b605625986b980d47fe1994) / [既存解析](https://github.com/genkimorimori252525-oss/KNEEKURA-TECH-HUB/blob/research/nesm-jar-and-ai-perf-2026-10-11/departments/minecraft/mods/epic-siege-mod/FAILURE-REPAIR-HISTORY.md) | **HISTORICAL 1.12**, not Forge 1.20.1 | `ESM_EntityAIAttackMelee/Ranged/Target` repair diff | **PERFORMANCE_NOT_VERIFIED** | 対象急変・遮蔽物変更時の遅延と反応を測る | COMPARATIVE_ONLY |
| `AI-PATH-TYPE-RAW-CACHE` | `CACHE_DATA_STRUCTURE`, `ENTITY_BLOCKENTITY`, `MIXIN_BYTECODE` | `WalkNodeEvaluator`で未加工path typeを短寿命にキャッシュ | [Improved Mobs 1.20.1ソース](https://github.com/Flemmli97/ImprovedMobs/blob/029b8c20302a76bac1af9f5140e2abb6f73fea5c/common/src/main/java/io/github/flemmli97/improvedmobs/mixin/pathfinding/performance/WalkNodeEvaluatorMixin.java) / [調査資料](https://github.com/genkimorimori252525-oss/KNEEKURA-TECH-HUB/blob/research/improved-mobs-2026-10-11/departments/minecraft/mods/improved-mobs/PATHFINDING-AND-SIEGE-AI.md) | **ANCHOR 1.20.1 Forge** source commit `029b8c20` | Mixins for `getBlockPathType`, clear cache in `done()` | **PERFORMANCE_NOT_VERIFIED** | 変更後のキャッシュ破棄、他の最適化Mixinとの競合 | COMPARATIVE_CONCEPT |

## Technique ID examples

- `RENDER-CHUNK-MESH-BATCHING`
- `MEMORY-STATE-INTERNING`
- `GC-TEMP-OBJECT-ELIMINATION`
- `TICK-SPATIAL-CULLING`
- `LIGHT-QUEUE-PACKING`
- `CHUNK-ASYNC-IO`
- `STARTUP-LAZY-INITIALIZATION`
- `CACHE-GENERATION-INVALIDATION`

IDは実際の研究で確定する。上記は命名例。

## Cross-lane linking

通常MODや古文MODから技術を発見した場合:

```text
Source target = 元解析へのlink
Technique row = optimization側の索引
```

として、解析本文をコピーしない。

## Comparison dimensions

同カテゴリ技術は可能なら以下で比較する。

- optimized operation
- asymptotic / constant-factor change
- memory tradeoff
- invalidation complexity
- thread-safety
- fallback
- compatibility risk
- observed workload
- benchmark metric
