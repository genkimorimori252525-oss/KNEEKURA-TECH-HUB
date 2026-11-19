# VFX Studio v1 — 契約・検証レイヤー

設計の正本: [`../../../design/2026-11-05-vfx-studio/PLAN.md`](../../../design/2026-11-05-vfx-studio/PLAN.md)（§4）／監査 [`AUDIT.md`](../../../design/2026-11-05-vfx-studio/AUDIT.md)／P0 棚卸し [`P0-INVENTORY.md`](../../../design/2026-11-05-vfx-studio/P0-INVENTORY.md)

**状態: SOURCE CONTRACTS IMPLEMENTED / REAL CLIENT NOT_RUN / PROVIDER INTEGRATION NOT_RUN**

ここにあるのは provider 非依存の純関数（I/O・時計・ネットワーク無し）だけ。既定で何も起動せず、何もインストールしない。既存の Evidence Store / 派生アーティファクト（`evidence/visual-artifacts.mjs`）・カメラ契約（`evidence/visual-capture.mjs` の `validateCamera`）・X/Z 図（`evidence/visual-geometry.mjs` の `topDownSvg`）を再利用し、第二の DB・runner・レンダラーは作っていない。

| ファイル | PLAN | 役割 |
| --- | --- | --- |
| `cue-contract.mjs` | §4.2 | VFX Cue v1（seal 付き）。演出は表示専用で `SERVER_AUTHORITATIVE_VFX_IS_PRESENTATION_ONLY` 固定。FX パラメータ表・予算上限・seed の決定論主張禁止。攻撃 1 件のライフサイクル検査（終端なしは OPEN）。bone emitter は layout hash に結合 |
| `provider-adapter.mjs` | §4.1 | capabilities/validate/prepare/play/stop/observe のみ。登録済み asset hash 以外拒否、UNVERIFIED 機能は明示 opt-in、UNKNOWN 後の盲目再試行禁止、stop は冪等・回数上限、`stopAll` は残留を UNKNOWN として報告 |
| `providers/photon-1.20.1.capabilities.json` | §2 | Photon 1.20.1（GPL-3.0, commit 507499fb）の機械可読申告。全 runtime 機能 UNVERIFIED、seek/pause UNAVAILABLE、粒子位置 NOT_EXPOSED、コード取込 FORBIDDEN |
| `frame-sequence.mjs` | §4.3 / P2 | Tank Frame Sequence v1（1 カメラ時系列、RECORD_REPLAY のみ、capture stage は Cardinal-4 と同じ）。偽 COMPLETE・復元不明の丸め・時計逆行・予算超過を拒否。replay index（drop/同一画像/skew を数値で）、カーソル、Cardinal-4 の時刻ラベル（SAME_VFX_INSTANT は直接観測の VFX 時刻が全一致のときだけ） |
| `replay-viewer.mjs` | §4.3 / P2 | 記録フレームのコマ送り・再生/停止・比較固定だけをする自己完結 HTML（派生アーティファクト）。再シミュレーションしない |
| `spatial-timeline.mjs` | §4.4 / P3 | 空間・時系列インスペクター。SOURCE_KIND ごとの検査、WORLD / ARENA_LOCAL 併記、run/epoch 混在拒否、未取得は UNKNOWN、ROI 限定のブロック標本、server/client イベントの ID 対応（因果は NOT_ESTABLISHED）。X/Y・Z/Y 高度図と既存 X/Z 図を 1 枚にまとめる |
| `repair.mjs` | §4.5 / P5 | 修復提案（FX パラメータのみ、expected old・asset hash・generation 固定）と適用（非対象不変を検証）。Evidence Packet は structure/visual/gameplay/performance/human_preference を独立列で保持し、合成証拠の runtime PASS・同一条件でない visual PASS・未回答の人間評価 PASS を拒否 |
| `asset-manifest.mjs` | §10.3 / §11.3 | Asset Method Manifest v1。方式の選択/切替履歴（切替前候補を保持）、LOSSY_CONVERSION、別 rig の clip/emitter 拒否、rig 変更時の無効化一覧、除外手法（Kimodo / video2mocap）拒否、外部送信は承認参照必須 |

## テスト

```bash
cd departments/minecraft/lab && npm run test:vfx-studio
```

`test` / `test:ci` にも組み込み済み。テスト用 fixture は全て `SYNTHETIC_FIXTURE` で、runtime 列を PASS にできないことも検査している。

## まだ無いもの（次の実装）

- Forge 側: 1 カメラ時系列撮影（Frame Sequence の producer）、武器ボーンの CLIENT_RENDER_POSE 観測、Photon driver。いずれも隔離 Forge profile での P0 同居確認が先。
- 実クライアントでの P1（再生・停止・残留なし）〜P5 受入。現時点では全て NOT_RUN。
