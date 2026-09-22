# Twilight Forest 描画グラフ — 実行状況と検証記録

記録更新: 2026-09-23 JST。状態: **FULL_CHECKOUT_RENDER_GRAPHS_GENERATED / STATIC GRAPH PHASE COMPLETE**。

## 完了した本番実行

GitHub Actions run `35767314089`（Twilight Forest Render Graph run #2）は、self-hosted Windows/x64 runner `Jolly-TechHub` 上で **success** となった。

固定した入力:

- TECH HUB event/input SHA: `1349626e24065b228b8ff2aa9576410affde0b71`
- FRONTIER: `TeamTwilight/twilightforest@793c4d4c7b0a2892f702cbb9a8d751fbe7218828`
- ANCHOR: `TeamTwilight/twilightforest@a7dd8f13c653e137f977f5ffaa870fcb20fc1625`
- extractor SHA-256: `3f54cceacde6e7e22560fa75347537d8974437a338be611da3308d7f3446cf87`
- comparator SHA-256: `d7b6d9354b46269bc05a373880f29c65dad6344fad412737160813b92550c684`

run は両 upstream checkout、snapshot 検証、抽出器テスト、FRONTIER graph、ANCHOR graph、cross-track comparison、証拠 receipt、成果物 commit まで全工程を成功させた。

## 生成結果

### FRONTIER

- blockstate: **528**
- model: **1,773**
- item definition: **663**
- atlas: **1**
- texture: **1,159**
- nodes: **4,124**
- dependency edges: **7,174**
- unresolved local refs: **17**
- duplicate logical paths: **0**
- parse errors: **0**
- model parent cycles: **0**
- graph SHA-256: `14492da8f1c329070f58e9a60676da2faa1794dc8e901a5efddcb86e618d2f78`

### ANCHOR

- blockstate: **453**
- model: **2,416**
- item definition: **0**
- atlas: **0**
- texture: **905**
- nodes: **3,774**
- dependency edges: **8,591**
- unresolved local refs: **15**
- duplicate logical paths: **0**
- parse errors: **0**
- model parent cycles: **0**
- graph SHA-256: `67ad0ead2c799a85ae8ebfa207783f8d13a98f861fa4f55d457009b89d92d1b7`

## ANCHOR ↔ FRONTIER portability

共有参照 edge は **2,131**、ANCHOR-only は **6,460**、FRONTIER-only は **5,043**。

主要 asset kind の差分:

| kind | ANCHOR | FRONTIER | shared | identical | changed | ANCHOR-only | FRONTIER-only |
|---|---:|---:|---:|---:|---:|---:|---:|
| atlas | 0 | 1 | 0 | 0 | 0 | 0 | 1 |
| blockstate | 453 | 528 | 451 | 0 | 451 | 2 | 77 |
| item_definition | 0 | 663 | 0 | 0 | 0 | 0 | 663 |
| model | 2,416 | 1,773 | 773 | 56 | 717 | 1,643 | 1,000 |
| texture | 905 | 1,159 | 599 | 563 | 36 | 306 | 560 |

未解決 local refs は shared 1 / ANCHOR-only 14 / FRONTIER-only 16。これらは黙って「解決済み」とせず、canonical JSON に診断として残している。

## 正本成果物

- `BLOCK-ITEM-RENDER-GRAPH.json` / `.md` — FRONTIER
- `ANCHOR-BLOCK-ITEM-RENDER-GRAPH.json` / `.md` — ANCHOR
- `BLOCK-ITEM-RENDER-COMPARISON.json` / `.md` — cross-track portability
- `RENDER-GRAPH-FULL-CHECKOUT-EVIDENCE.json` — 実行・ツール・source・hash receipt

生成成果物は derived evidence のみで、raw third-party assets は TECH HUB に保存していない。

## 境界

この完了は **静的なBlock/Item描画依存グラフ**についてのもの。

- Minecraft はこの run では起動していない。
- runtime performance はまだ測定していない。
- compiled class identity は証明していない。
- main へ merge していない。

したがって、次の正式フェーズは `RUNTIME-EVIDENCE-SPEC.md` に基づく **Runtime Evidence 実機計測**。静的解析結果と実測値を混同しない。
