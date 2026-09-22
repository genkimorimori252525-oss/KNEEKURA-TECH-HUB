# Minecraft Technology Department

KNEEKURA TECH HUB の Minecraft MOD 開発専用部門。

## 固定対象環境

**この部門の標準・正本対象は Minecraft 1.20.1 + Minecraft Forge。**

- Minecraft: `1.20.1`
- Mod Loader: `Forge`
- Fabric / NeoForge / 他バージョン: 比較資料として参照は可能。ただし 1.20.1 Forge の正本分析へ混在させない。
- 解析結果には必ず対象 Mod の release / tag / commit / JAR SHA-256 など、再現可能な Source Snapshot を付ける。

## 目的

既存 Mod を「遊び方」ではなく **実装技術の集合** として丸ごと分解し、KNEEKURA の Minecraft MOD 開発で再利用できる知識にする。

対象範囲は原則として以下をすべて含む。

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
- Mixin / Access Transformer / core patch / reflection
- dependencies / compatibility / optional integrations
- performance-sensitive paths / caches / tick cost / allocation
- test / debug / data generation / build tooling
- license / provenance / redistribution constraints

## 保存原則

このリポジトリは private でも、第三者 Mod の原物置き場にはしない。

**Git に残すもの**

- exact source/release identity
- file/path inventory
- SHA-256 / dimensions / formats / namespaces
- call graph / registry map / event map / feature map
- texture ↔ model ↔ renderer ↔ entity 対応表
- AI/state-machine の構造化分析
- 設計パターン、制約、注意点
- evidence locator と派生分析

**原則ローカルだけに置くもの**

- Mod JAR
- 展開済み JAR 全体
- decompiled source tree
- third-party texture/model/sound の完全コピー
- 一時解析生成物

ローカル生成物は `departments/minecraft/local-artifacts/` 配下を想定し、Git 追跡対象外とする。

## Mod 1個あたりの標準成果物

```text
mods/<mod-slug>/
  README.md
  manifest.json
  OVERVIEW.md
  CODE-MAP.md
  AI-BEHAVIOR.md
  WORLDGEN.md
  NETWORKING.md
  RENDERING-ASSETS.md
  DATA-ASSETS.md
  PERFORMANCE.md
  COMPATIBILITY.md
  LICENSE-PROVENANCE.md
```

すべてのファイルを毎回無理に埋めるのではなく、存在しない領域は `NOT_APPLICABLE`、未調査は `NOT_ANALYZED` と明記する。

## 一覧

Mod 横断の一覧は `catalog/MODS.md` に置く。

最初の正式ターゲットは **The Twilight Forest**。詳細分析は対象 1.20.1 Forge リリースと Source Snapshot を固定してから開始する。

## 分析手順

詳細は `ANALYSIS-SPEC-v1.md` を参照。
