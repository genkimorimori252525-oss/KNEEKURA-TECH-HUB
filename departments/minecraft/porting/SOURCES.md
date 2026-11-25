# 原典台帳（2026-11-25）
## S1: ModPorter
[固定ソース](https://github.com/CrabMods/modporter/tree/da08fa920f733f572a45329b25b78a712de47452) — 0.4.0、2026-11-16、Apache-2.0（LICENSE blob 261eeb9e9f8b2b4b0d119366dda99c6fd7d35c64）。第三者fixture/元MODの権利は別。実行・vendor・自動化なし。
- [strict benchmark](https://github.com/CrabMods/modporter/blob/da08fa920f733f572a45329b25b78a712de47452/docs/strict-0.4.0.json) blob 7e0aeefa5ab439da956c6b0379e85e6554b8d76d: upstream報告11/11 targets、274 required GameTests（Create 60）。独立再現していない。ソースプロジェクトの検証範囲に限る。個々のゲーム機能や配布JARの保証ではない。WorldEditは準備済みForge-only入力。
- [BENCHMARKING](https://github.com/CrabMods/modporter/blob/da08fa920f733f572a45329b25b78a712de47452/docs/BENCHMARKING.md) blob efb57267fd4ed5babe330a1733455f8096979d3b: 入力版・準備・再現条件。
- 規則入口: [structural transforms](https://github.com/CrabMods/modporter/tree/da08fa920f733f572a45329b25b78a712de47452/src/main/kotlin/com/modporter/core/transforms/structural), [mappings](https://github.com/CrabMods/modporter/tree/da08fa920f733f572a45329b25b78a712de47452/src/main/resources/mappings/forge2neo), [tests](https://github.com/CrabMods/modporter/tree/da08fa920f733f572a45329b25b78a712de47452/src/test).
- 実例の探索対象: Create, Twilight Forest, Aether, WorldEdit 等。上記実例を一律移植済み製品として扱わない。
## S2: NeoForge Primers
[公式目次](https://docs.neoforged.net/primer/docs/) (2026-11-25閲覧、動的Web資料)。非網羅的な概説。1.20.1→1.20.4に相当する全差分が目次にあるとは限らない。元先の実APIで穴を埋める。著者 ChampionAsh5357 の対象Primer は CC BY 4.0。派生要約のみ。
- [1.20.4→1.20.5](https://docs.neoforged.net/primer/docs/1.20.5/) Java21、Data Components、StreamCodec 等の vanilla差。
- [同 Neo changes](https://docs.neoforged.net/primer/docs/1.20.5/neo/)
- [1.20.5→1.20.6](https://docs.neoforged.net/primer/docs/1.20.6/)
- [1.20.6→1.21](https://docs.neoforged.net/primer/docs/1.21/) / [Neo changes](https://docs.neoforged.net/primer/docs/1.21/neo/)
- [1.21.1公式 registries](https://docs.neoforged.net/docs/1.21.1/concepts/registries/), [attachments](https://docs.neoforged.net/docs/1.21.1/datastorage/attachments/), [components](https://docs.neoforged.net/docs/1.21.1/items/datacomponents/).
- [Forge 1.20.1 docs](https://docs.minecraftforge.net/en/1.20.1/), [NeoForge user guide](https://docs.neoforged.net/user/docs/)（1.20.1はForge推奨）。
## S3: NeoForge MDKs
[公式一覧](https://github.com/NeoForgeMDKs)
- [NeoForge 1.21.1 ModDevGradle](https://github.com/NeoForgeMDKs/MDK-1.21.1-ModDevGradle/tree/d69737d705926b200c23769f0a674ff6379badb4) build.gradle blob ffe340d624445ead45c030305be1ecb68f8d83e8: moddev 2.0.148, Java21, neoForge DSL, client/server/gameTestServer/data。
- [Forge 1.20.1 legacy ModDevGradle](https://github.com/NeoForgeMDKs/MDK-Forge-1.20.1-ModDevGradle/tree/cba0981a47ce9756f4cbbc932484ff9f9dffe140) build.gradle blob 3fce4bee10e5e93208bb9692ad3f8a5a1d2944ab: legacyforge 2.0.91, Java17, legacyForge DSL、同種run。Forge向けでありNeoForge 1.20.1ではない。
- バージョンを固定して参照。新規開発環境の骨格に使うが既存製品のbuild構成を無条件で置換しない。ローカルでのclone/build未実施。権利・mapping利用条件は取得時に原典で確認。
