# Minecraft Technology Department

KNEEKURA TECH HUB の Minecraft MOD 開発専用部門。

## 互換性方針 — Anchor + Frontier

この部門は **Minecraft 1.20.1 + Forge に固定しない**。

原則として各対象を2本の独立トラックで保持する。

1. **ANCHOR — Minecraft 1.20.1 + Forge**
   - KNEEKURA が実際に利用・移植するときの基準環境。
   - upstream に 1.20.1 Forge 実装がある場合は、その実装を丸ごと分析する。
   - 存在しない場合でも、1.20.1 Forge を移植先仕様として残す。

2. **FRONTIER — Latest useful upstream**
   - upstream の最新版・現行主力版から最新技術を採取する。
   - Forge / NeoForge / Fabric / その他ローダーを理由に除外しない。
   - 最新版の仕組みを 1.20.1 に混ぜず、差分と移植条件を明示する。

ANCHOR と FRONTIER は必ず別 SourceSnapshot にする。別バージョン・別ローダーの証拠を同じ実装事実として混同しない。

これにより『1.20.1しか見ないため新技術を取り逃す』ことと、『最新版のコードが1.20.1でそのまま動くと思い込む』ことの両方を避ける。

## 標準の移植成果

FRONTIER で得た技術は VERSION-PORTABILITY.md で次へ分解する。

- concept: バージョン非依存の考え方
- implementation: upstream 固有実装
- platform dependency: Minecraft / Forge / NeoForge / Fabric API 依存部
- changed API surface: バージョン差で変わった API
- backport strategy: 1.20.1 Forge での再実装方針
- impossible / risky parts: そのまま移せない部分

## 目的

既存 Mod / loader bridge / library / framework を『遊び方』ではなく **実装技術の集合** として丸ごと分解し、KNEEKURA の Minecraft MOD 開発で再利用できる知識にする。

対象範囲:

- Mod 起動構造、entrypoint、registries、events、capabilities
- Entity / Mob / Boss AI
- Goal / Target Goal、Brain、Sensor、Memory、独自 state machine
- pathfinding / navigation / targeting / combat
- block / item / block entity / menu / screen
- packet / networking / client-server synchronization
- dimension / biome / chunk / structure / feature / world generation
- renderer / model / animation / pose / layer
- texture / atlas / UV / sprite / material
- particle / shader / post effect
- sound / music
- recipe / loot table / tag / advancement / language / config
- Mixin / Access Transformer / Access Widener / Class Tweaker / core patch / reflection
- mappings / remapping / classloading / bytecode transformation
- loader/API compatibility layers and translation
- dependencies / compatibility / optional integrations
- performance-sensitive paths / caches / tick cost / allocation
- test / debug / data generation / build tooling
- license / provenance / redistribution constraints
- cross-version / cross-loader portability

## 完全取得と保存原則

丸ごと分析するときは、対象 SourceSnapshot の **full upstream source tree をローカルに取得して全体を走査してよい**。数個の検索結果だけを見て whole analysis 完了とはみなさない。

Git に残すもの:
- exact source/release identity
- track (ANCHOR / FRONTIER / COMPARATIVE)
- file/path inventory
- SHA-256 / dimensions / formats / namespaces
- call graph / registry map / event map / feature map
- texture ↔ model ↔ renderer ↔ entity 対応表
- AI/state-machine の構造化分析
- bytecode/loader translation pipeline map
- version / loader delta
- 1.20.1 Forge backport notes
- evidence locator と派生分析

原則ローカルだけに置くもの:
- Mod JAR
- upstream full checkout の作業コピー
- 展開済み JAR 全体
- decompiled source tree
- third-party texture/model/sound の完全コピー
- 一時解析生成物

## 対象1個あたりの標準成果物

README.md / manifest.json / OVERVIEW.md / CODE-MAP.md / AI-BEHAVIOR.md / WORLDGEN.md / NETWORKING.md / RENDERING-ASSETS.md / DATA-ASSETS.md / PERFORMANCE.md / COMPATIBILITY.md / VERSION-PORTABILITY.md / LICENSE-PROVENANCE.md

## 分析キュー

1. **The Twilight Forest**
2. **Sinytra Connector**
3. 以降、Minecraft MOD 開発に再利用価値の高い対象

Sinytra Connector は 1.20.1 Forge 系と現行 NeoForge 系の両方を保持し、Fabric互換技術がどう進化したかを比較する重点対象とする。

対象横断の一覧は catalog/MODS.md。詳細手順は ANALYSIS-SPEC-v1.md。

## MOD制作AI環境の確定設計

[2026-09-28 確定設計](design/2026-09-28-mod-ai-environment/DESIGN.md)は、Source Intelligence、全classpath、source/bytecode、Connector研究、実装例・失敗例、GameTestと実機観測を既存部門へ接続する設計。4巡の敵対的設計監査、採否記録、受け入れ仕様、参考原典を同じディレクトリに保持する。

設計資料であり、新機能の実装・動作検証・既存解析キューの完了を意味しない。


## 成果物との境界

この部門はMinecraft技術の調査・根拠・移植知識を保持する。KNEEKURA自身が作るMODの製品ソースは [`deliverables/minecraft/`](../../deliverables/minecraft/README.md) に置く。

例: Bedrock Witherの仕様調査・先行MOD解析・受入根拠は本部門、実際のKNEEKURA Wither MODコード・製品Status・自開発の失敗修理史はdeliverable側。製品で得た教訓を一般技術へ戻す場合も、通常のEvidence/Review経路を通す。
