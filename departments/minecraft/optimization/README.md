# 軽量化 — Minecraft Optimization Technology

KNEEKURA TECH HUB の **軽量化MOD専用解析区画**。

ここは「おすすめ軽量化MOD一覧」ではない。
描画、CPU/TPS、メモリ、GC、チャンク、Lighting、I/O、起動、同期、キャッシュ、
並列化などの **性能改善技術そのものを分解して再利用するための研究棚**。

## 位置づけ

```text
departments/minecraft/
├─ mods/           content/gameplay/loader等の通常MOD研究
├─ optimization/   軽量化・性能改善MOD研究
└─ kobun/          太古MODの歴史隔離研究
```

軽量化 lane は現代技術研究なので、基本は通常laneと同じ:

- **ANCHOR — Minecraft 1.20.1 + Forge**
- **FRONTIER — latest useful upstream**

を使う。

ただし太古の軽量化MODは、原版の実装事実を `kobun/` に置く。
`optimization/` 側には技術索引や比較だけを置き、古文の Temporal Firewall を壊さない。

## 目的

対象MODから以下を回収する。

- 何を重いと判断したか
- どのコードパスを減らした/置換したか
- fast path と fallback
- cache / invalidation の設計
- allocation削減
- batching / culling / LOD
- data structure の変更
- threading / work stealing / async
- chunk / lighting / IO pipeline
- renderer / GPU submission / buffer management
- classloading / startup / resource loading
- network圧縮・同期削減
- Mixin / bytecode最適化
- correctnessを守るためのguard
- incompatibility / regression / repair history
- 実測でどれだけ効いたか、どのworkloadだけで効くか

## 軽量化技術カテゴリ

- `RENDERING_GPU`
- `RENDERING_CHUNK`
- `MEMORY`
- `ALLOCATION_GC`
- `TICK_SIMULATION`
- `ENTITY_BLOCKENTITY`
- `CHUNK_WORLDGEN_IO`
- `LIGHTING`
- `STARTUP_CLASSLOADING`
- `RESOURCE_DATA`
- `NETWORK`
- `CACHE_DATA_STRUCTURE`
- `THREADING_CONCURRENCY`
- `CULLING_LOD`
- `MIXIN_BYTECODE`

一つのMODが複数カテゴリへまたがってよい。

## 性能主張は二段階

### Mechanism Evidence

Source / bytecode / history から、

> この処理を省く / キャッシュする / allocationを減らす / batchする

ことを確認できる。

これは **仕組みの証明**。

### Benchmark Evidence

実際の環境で、

- frame time
- MSPT
- heap
- allocation
- startup
- chunk throughput
- GPU time

などが改善したことを測る。

これは **効果の証明**。

```text
"速そうなコード"
      ≠
"実際に速い"
```

Mechanismだけなら `PERFORMANCE_NOT_VERIFIED` とする。

## 正しさも同時に測る

FPSが上がっても、

- chunkが描画されない
- mob tickを落としてしまう
- block entity更新が欠ける
- lightingが壊れる
- worldgen結果が変わる
- saveが壊れる

なら単純な成功ではない。

軽量化研究では常に、

```text
performance
+
semantic correctness
+
compatibility
```

を別々に評価する。

## 比較単位

MOD単位:
[軽量化MOD catalog](catalog/MODS.md)

技術単位:
[Optimization Techniques](catalog/TECHNIQUES.md)

技術catalogは、別ジャンルのMODから得た軽量化技術も参照できる。
target本体を重複コピーせず、元の解析へlinkする。

## 入口

- 分析規則: [ANALYSIS-SPEC.md](ANALYSIS-SPEC.md)
- benchmark規則: [BENCHMARK-SPEC.md](BENCHMARK-SPEC.md)
- target雛形: [TARGET-TEMPLATE.md](TARGET-TEMPLATE.md)
- MOD catalog: [catalog/MODS.md](catalog/MODS.md)
- 技術catalog: [catalog/TECHNIQUES.md](catalog/TECHNIQUES.md)
