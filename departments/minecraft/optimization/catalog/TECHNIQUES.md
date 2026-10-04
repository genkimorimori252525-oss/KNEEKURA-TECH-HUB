# Optimization Techniques Catalog

MOD単位ではなく、**再利用できる軽量化技術単位**の横断catalog。

| ID | Category | Technique | Source target | Track | Mechanism evidence | Benchmark state | Correctness boundary | Reuse status |
|---|---|---|---|---|---|---|---|---|
| — | — | — | — | — | — | — | — | EMPTY / READY |

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
