# 軽量化 MOD Analysis Specification v1

## 1. Scope

この仕様は Minecraft の性能改善MODを解析するための追加規則。

通常の [Minecraft Whole-Target Analysis Specification](../ANALYSIS-SPEC-v1.md) の:

- ANCHOR / FRONTIER
- provenance
- full-tree acquisition
- failure/repair history
- evidence basis
- source/binary/runtime分離

を継承する。

軽量化lane固有の追加要件は:

1. optimization mechanism を特定する
2. baseline と比較対象を明示する
3. correctness を別評価する
4. performance claim を benchmark と結びつける

こと。

## 2. Target admission

主目的が性能改善なら `optimization/mods/` に置く。

例:

- renderer replacement
- chunk renderer
- memory optimization
- allocation/GC reduction
- lighting engine
- chunk/worldgen scheduler
- startup/classloading optimization
- network optimization
- simulation/tick culling
- cache/data structure optimization
- concurrency optimization

content MODに局所最適化があるだけなら、targetは通常 `mods/` に残し、
技術だけ `optimization/catalog/TECHNIQUES.md` から参照する。

歴史的な古い軽量化MODは ORIGINAL を `kobun/` に置く。

## 3. Tracks

通常laneと同じ。

### ANCHOR

Minecraft 1.20.1 + Forge を実際の利用/再構築基準とする。

### FRONTIER

最新版 upstream から最新の性能技術を回収する。

### COMPARATIVE

性能技術が特定versionで大きく変わった場合だけ追加。

各trackの性能結果は混ぜない。

## 4. Optimization Finding

最低限:

```text
Finding:
Category:
Evidence basis:
Track:
Baseline behavior:
Optimization target:
Mechanism:
Fast path:
Fallback:
Cache/invalidation:
Allocation effect:
Concurrency owner:
Correctness risk:
Compatibility surface:
Benchmark status:
Source/history locator:
```

## 5. Evidence classes

通常の:

- DIRECT_OBSERVATION
- AUTHOR_CLAIM
- INFERENCE
- UNKNOWN

に加えて、性能評価状態を別に持つ。

- `MECHANISM_ONLY`
- `BENCHMARKED_LOCAL`
- `BENCHMARKED_REPRODUCED`
- `PERFORMANCE_NOT_VERIFIED`
- `REGRESSION_FOUND`
- `INCONCLUSIVE`

Source diffだけで `BENCHMARKED_*` へ上げない。

## 6. Required optimization surfaces

各targetで必要に応じて確認する。

### Rendering / GPU
- render graph / render passes
- chunk mesh build
- buffer upload/reuse
- draw-call batching
- frustum/occlusion culling
- entity/block entity rendering
- transparency
- shader/material state changes
- GPU synchronization
- VRAM lifecycle

### CPU / simulation
- tick loops
- entity/block entity iteration
- neighbor updates
- scheduled ticks
- AI/pathfinding
- event dispatch
- collections/search
- repeated computation

### Memory / allocation
- object count
- collection type
- deduplication/interning
- packed storage
- temporary object elimination
- pooling
- cache size/lifetime
- heap retention/leak risk

### Chunks / world / IO
- chunk load/save
- worldgen
- serialization
- region-file access
- compression
- async IO
- work queues
- priority scheduling

### Lighting
- propagation algorithm
- invalidation/update region
- queue representation
- chunk boundary handling
- async/sync boundary

### Startup / resources
- classloading
- scanning
- datapack/resource loading
- model baking
- DFU/data conversion
- config discovery
- mod scanning

### Networking
- packet frequency
- payload size
- batching/coalescing
- state-delta encoding
- duplicate suppression
- client/server authority

### Concurrency
- thread ownership
- executor/pool
- dependency graph
- synchronization
- lock granularity
- race/deadlock safeguards
- main-thread handoff

## 7. Optimization contract

各最適化は「何を省くか」だけでなく「いつ省いてよいか」を記録する。

```text
expensive operation
      ↓
eligibility guard
      ↓
fast path
      ├─ valid → optimized result
      └─ invalid → fallback/original path
```

guard/fallbackが無い場合は correctness risk として明示する。

## 8. Cache contract

cacheを使う場合:

- key
- value
- owner
- maximum size
- lifetime
- invalidation trigger
- stale-data consequence
- thread safety
- save/reload boundary

を調べる。

「cacheした」だけでは技術解析完了にしない。

## 9. Correctness equivalence

軽量化前後で何を同じとみなすか明示する。

例:

- rendered block/entity set
- tick count / state transitions
- lighting result
- chunk serialization
- worldgen seed determinism
- packet-visible state
- collision/path result

完全一致が不要なLOD/cullingでは、許容差/visibility contractを定義する。

## 10. Failure / Repair History

軽量化MODでは特に:

- visual corruption
- missing chunks
- memory leak
- stale cache
- race
- deadlock
- server hang
- save corruption
- mod incompatibility
- shader conflict
- chunk desync
- startup crash

を重点的に追う。

最適化の失敗は、性能より correctness boundary を教えてくれることが多い。

## 11. Performance claims

性能値は必ず:

- track/version
- workload
- environment
- baseline
- metric
- sample method
- warm-up
- run count
- aggregation
- uncertainty/noise

と結ぶ。

`+30% FPS` のような値だけを技術catalogへ保存しない。

## 12. Compatibility

最適化MODは同じhot pathへMixin/core patchを当てることが多い。

各targetで:

- modified vanilla classes/methods
- replaced subsystems
- mixin priority
- optional integrations
- known incompatible mods
- fallback mode
- config toggles

を記録する。

## 13. Completion

targetの重要facetについて:

- mechanism evidence
- correctness boundary
- compatibility surface
- failure/repair coverage
- benchmark state

が記録されていること。

runtime benchmarkが無い場合でもmechanism researchは完了可能だが、
performance state は `PERFORMANCE_NOT_VERIFIED` のままにする。
