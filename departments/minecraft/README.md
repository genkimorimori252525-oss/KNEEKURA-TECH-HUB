# Minecraft Technology Department

KNEEKURA TECH HUB の Minecraft MOD 開発専用部門。

## 独立AI部門との連携（2026-10-11）

[AI専門研究部門](../ai/README.md) は指揮階層・群体知能・学習・AI評価の一般化を担当し、Minecraft部門はMob実装、Forge API、JAR/Bytecode、LAB/GameTestでの検証を担当する。`mod-ai/`（MOD制作AI基盤）を改名・移動しない。

- [階層型指揮・群体知能 v0](../ai/multi-agent/HIERARCHICAL-COMMAND-AI-v0.md) — **独立した将来設計候補**
- [Scape and Run: Parasites 1.9.21 Bytecode解析](mods/scape-and-run-parasites/COMBAT-AI-BYTECODE-2026-10-11.md) — **実物の旧版JARの限定的な静的証拠**

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

## 再利用技術ライブラリ

対象MOD固有の解析から、複数製品へ安全に移植できる設計契約は `techniques/` に分離する。

最初の正式Toolkit:
- [Boss Combat Toolkit v1](techniques/boss-combat-toolkit/README.md) — Attack Lifecycle / Beam / Projectile Deflection / Temporary Faction / Client FX Budget / Boss Presentation を、製品固有の数値を持たない再利用契約と検証シナリオとして定義する。

Toolkitは共通ランタイム実装を強制しない。各製品は必要なmoduleだけを採用し、実装・数値・受け入れ根拠を自身で所有する。

## Minecraft 1.20.1 Vanilla Foundation Map

[Vanilla Foundation Map](vanilla-foundation/README.md)は、既存Source Intelligenceの exact ANCHOR `IndexSnapshot` から `net/minecraft/**` のクラス・package・subsystem・継承/implements・JVM class-reference候補・由来を content-addressed な小型地図へ変換する。巨大なMinecraft source/JARをGitへ複製せず、実装AIが外部検索より先に1.20.1内部を発見できる入口として使う。

Vanilla AIの意味解析は [vanilla-ai](vanilla-ai/README.md)、実機での意思決定可視化は LAB の Entity Decision Observatory が担当し、Foundation Map自体は静的な発見・由来層に留める。

## MOD制作AI環境の確定設計

[2026-09-28 確定設計](design/2026-09-28-mod-ai-environment/DESIGN.md)は、Source Intelligence、全classpath、source/bytecode、Connector研究、実装例・失敗例、GameTestと実機観測を既存部門へ接続する設計。4巡の敵対的設計監査、採否記録、受け入れ仕様、参考原典を同じディレクトリに保持する。

設計資料であり、新機能の実装・動作検証・既存解析キューの完了を意味しない。

## KNEEKURA-made product MODs (2026-10-09)

- [Product workspaces](projects/README.md) — `projects/kirby-mod/` contains the canonical Kirby source import from the former `Kirby_mod` repository. The old repo remains a read-only historical backup; Reimu and Natural Ghast have not been migrated in this Kirby change.
- [Shared MOD debugging roadmap](design/2026-10-09-shared-mod-debug-roadmap.md) — plan to replace incomplete per-MOD diagnostics with optional adapters to the existing LAB / MOD-AI system; no shared debug runtime claimed yet.


### 新しい感染・指揮AI原作研究

[Spore 2.2.0j](mods/fungal-infection-spore/README.md) はユーザー提供Minecraft 1.20.1 Forge JARを固定し、Protoの4×4部隊選択/報酬更新、Womb/Moundの資源回収・感染、上位個体の標的共有を選定Bytecodeから調査中。AI部門での一般化は [別研究](../ai/multi-agent/PROTO-HIVEMIND-CASE-STUDY-2026-10-11.md)。実機検証とwhole-target completeは未実施。

