# VFX Studio v1.1 — P0 机上棚卸し（2026-11-14）

- 実施: 2026-11-14 JST、実装ブランチ `jolly/vfx-studio-impl-20261114`（基点 `jolly/vfx-studio-tank-spatial-plan-20261105@3e107987`、その基点は main@4866d7d7）
- 方式: GitHub API による upstream の**読み取りのみ**（ソース・LICENSE・gradle.properties）。JAR のダウンロード、Forge 起動、mod 導入は**していない**。
- 判定: **P0 SOURCE INVENTORY DONE / P0 RUNTIME CO-EXISTENCE NOT_RUN / LICENSE GATE PARTIALLY RESOLVED**

## 1. 並行作業との照合

| 対象 | 確認結果 | 判定 |
| --- | --- | --- |
| main の Motion Trace / VFX / frame sequence 実装 | `departments/` 配下の `.mjs/.js/.py/.java` に該当シンボルなし | 重複なし。新規 `lab/debug-workspace/vfx/` に置く |
| PR #114（本計画の DRAFT） | 設計書のみ | 実装は本ブランチで別に積む |
| PR #115（mcbuild 建築） | 建築ジャンル。VFX/Tank に触れない | 衝突なし |
| PR #97（JavaFX 弾幕 draft tool） | 独立ツール。Viewer 時間軸 API は main に無い | 共通抽象は作らない（計画 §1 の通り） |
| Cardinal-4 の capture stage | `visual-capture.mjs` が `AFTER_LEVEL_BEFORE_HAND_HUD` 以外を拒否 | v1 Frame Sequence も同 stage に固定。P6 まで緩めない |

## 2. upstream 権利・API（ソース静的確認）

| upstream | 固定点 | ライセンス | 判定 |
| --- | --- | --- | --- |
| Low-Drag-MC/Photon `1.20.1` | commit `507499fbe5a3fc72bb90993e059848cbb31f13ca`（2026-01-21）, `mod_version = 1.1.17` | LICENSE 本文 GPL-3.0、`mod_license = GPL-3.0 license` | ANCHOR 候補。**第三者コードは取り込まない**（外部配布物の opt-in 利用＋自作の薄い接続のみ） |
| Low-Drag-MC/Photon 既定ブランチ `1.21` | — | **CC BY-NC-SA 4.0（非商用・継承）** | **新規発見のリスク**。FRONTIER 参考でもコード・資産の転載不可。1.20.1 版と取り違えない |
| Low-Drag-MC/LDLib-MultiLoader | 既定 `1.20.1` | GPL-3.0 | Photon 1.20.1 が要求する正確な LDLib 版は gradle.properties から読めず **UNVERIFIED** |
| LodestarMC/Lodestone | 既定 `1.21` | LGPL-3.0 | 代替候補のまま。採用時に 1.20.1 系の版を別途固定 |

Photon 1.20.1 の公開 API（`client/fx/IFXEffect.java`, `FXRuntime.java` のシグネチャのみ確認）:

| 計画上の操作 | 対応しそうな upstream | 状態 |
| --- | --- | --- |
| prepare（offset/rotation/scale/delay） | `IFXEffect.setOffset/setRotation/setScale/setDelay` | SOURCE_PRESENT / RUNTIME NOT_RUN |
| play | `IFXEffect.start()` | SOURCE_PRESENT / RUNTIME NOT_RUN |
| stop | `FXRuntime.destroy(boolean force)`, `IFXEffect.setForcedDeath` | SOURCE_PRESENT / 残留しないかは NOT_RUN |
| observe（生存） | `FXRuntime.isAlive()` | SOURCE_PRESENT / RUNTIME NOT_RUN |
| 粒子全位置 | 公開 API で確認できず | NOT_EXPOSED 扱い |
| 時刻シーク・時間スケール・一時停止 | `IFXEffect`/`FXRuntime` に該当メソッドなし | **CONTROLLED_SEEK = UNAVAILABLE**（RECORD_REPLAY を正本とする計画 §4.3 と整合） |
| コマンド経路 | `command/EffectCommand` 等が存在 | AI に汎用コマンドとして渡さない（§4.1） |

この表は `lab/debug-workspace/vfx/providers/photon-1.20.1.capabilities.json` に機械可読で保存し、アダプターはこの申告を超える操作を拒否する。

## 3. 計画への提案（plan delta）

1. **Photon 1.21 の CC BY-NC-SA 化を AUDIT の権利ゲートに追記**すべき。FRONTIER 研究でも 1.21 系のコード・プリセット資産を TECH HUB に入れない。
2. 1.20.1 に時刻制御 API が無いため、**CONTROLLED_SEEK は Photon では原則 UNAVAILABLE** と先に確定し、P2 の RECORD_REPLAY を恒久の正本として扱う。CONTROLLED_SEEK は別 provider が出たときのみ再審査。
3. 斬撃の残光は Photon のトレイルではなく自作の薄いクライアント描画でも P1–P5 を通せる。provider を差し替え可能にするため、契約側（Cue / Frame Sequence / Repair）は provider 非依存で実装した。

## 4. 未実施（NOT_RUN）

- isolated Forge 1.20.1 profile での Photon 1.1.17 + LDLib + GeckoLib 同居確認
- 配布 JAR のハッシュ固定（Modrinth 配布物は未取得）
- 実クライアントでの再生・停止・残留確認（P1 ゲート）
