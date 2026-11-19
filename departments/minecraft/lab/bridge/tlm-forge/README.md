# TLM Forge bridge

このディレクトリは Minecraft Forge / TouhouLittleMaid 側で SimLab を実行し、
`simlab/schema.json` の JSONL と pose/palette/network companion を生成するための接続層です。

## Dependency boundary

ここから TLM の `EntityReimu`、`EntityMaid`、`ReimuAiDebug`、Forge の
`ServerLevel` などを参照します。AI・弾幕の実装本体は TLM リポジトリに残し、
この層にはシナリオ実行、イベント収集、モデル観測、トレース出力だけを置きます。

このディレクトリは TLM の Gradle 開発クラスパスへ組み込んでビルドする前提です。
単体の Node.js Viewer/解析機能はリポジトリルートから利用できます。


## Runtime network companion

Forge 1.20.1 の SimpleChannel runtime send/receive は arena JSONL へ直接混ぜず、
process-local `.net.jsonl` へ出します。server/client の両 JVM に同じ
`tlm.sim.scenario` と `tlm.sim.run` を渡すと、main trace の `meta.run` と
network companion の `net_meta.run` を hard identity として照合できます。
