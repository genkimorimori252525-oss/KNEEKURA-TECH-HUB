# Danmaku Preview Implementation Plan

> **For agentic workers:** Use superpowers:executing-plans inline. Steps use checkbox syntax.

**Goal:** JavaFXで弾幕の下書きを即時調整し、JSONで保存できる最小ツール。
**Architecture:** 純Javaの時刻→弾位置計算、限定JSON codec、JavaFX表示を分離する。
**Tech Stack:** JDK17、OpenJFX21.0.9、PowerShell。Gradle/Minecraftは不要。
**Spec:** `docs/superpowers/specs/2026-10-06-danmaku-preview-design.md`

## Global Constraints

1block単位、20tick/秒、最大3,000同時弾・60秒。Windows x64。
正式world/Ver1.00/既存MODへの変更なし。Minecraft取り込み・物理再現は初版範囲外。

## Review Focus

- 無効な数値編集で現在の有効な設定を壊さない。
- 大量発射で上限を黙って切り捨てない。
- JSONの未知/重複項目・余剰文字・非有限値を拒否。
- 巻き戻しと期間端で発射/寿命の境界を維持。
- 停止/再開時に非表示期間の時刻を飛ばさない。

## Task 1: 時刻モデルとJSON

Files: `departments/minecraft/danmaku-preview/src/kneekura/danmaku/{Pattern,PatternJson}.java`
Test: `departments/minecraft/danmaku-preview/tests/kneekura/danmaku/PatternTest.java`
Interface: `Pattern.Config`、`Pattern.at(Config,double)`、`PatternJson.read/write`。

- [x] 手計算の扇/全周/回転、間隔/寿命、巻き戻し、入力上限、JSON異常テストを先に作成。
- [x] JDK17 javac/javaでRED確認後、等速直線計算と平坦JSONを実装してGREEN。

## Task 2: 起動可能な画面

Files: `src/kneekura/danmaku/PreviewApp.java`、`run.ps1`、`README.md`、`presets/fan.json`。
Interface: Task1のConfigを編集し、時刻をatへ渡す。JSONは同codecを使用。

- [x] pinned/hash照合OpenJFX取得と純Javaテスト専用の起動手順。
- [x] 3D格子/球/目印、視点、編集、再生操作、JSON保存読込。
- [x] 同じhandlersで有限smokeを実行し、JDK17実画面と保存読込を確認。

## Task 3: 引継ぎ

- [x] 独立レビュー、必要な修正と関連回帰を実行。
- [x] 実行例・限界・検証結果をREADMEへ記録。
- [ ] commit/push、新規Draft PR作成・添付、最終CIと起動手順を報告。

## Execution evidence

Task1: first-burst assertionのRED後、40assertions GREEN。追加境界確認後43assertions。
Task2: JDK17/OpenJFX21.0.9のgenuine compile/SCENE3D smokeとPNG目視確認。
Task3: 独立レビューで保存誤動作P2、整数丸めを検出。各再現のRED後に修正してGREEN。
Ruling: ユーザーが「さくっと」と承認済み短設計の実装を指示したため、追加の承認待ちは挟まず
設計/計画を記録してinline実装。Minecraftへの取り込みは明示的に次段階へ保持。
