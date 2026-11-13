# VFX Studio v1.1 — 実装状況（2026-11-14）

ブランチ `jolly/vfx-studio-impl-20261114`（基点 PR #114 の `3e107987`）。PLAN.md / AUDIT.md の本文は変更していない。

| 区分 | 状態 | 根拠 |
| --- | --- | --- |
| P0 技術・権利の机上確認 | DONE (SOURCE ONLY) | [P0-INVENTORY.md](P0-INVENTORY.md) |
| P0 隔離 Forge での Photon/LDLib/GeckoLib 同居 | NOT_RUN | 実機起動・mod 導入は別承認 |
| §4.1 Provider Adapter（provider 非依存の guard） | IMPLEMENTED (SOURCE) | `lab/debug-workspace/vfx/provider-adapter.mjs` |
| §4.1 Photon driver（Forge 側） | NOT_IMPLEMENTED | P0 同居確認待ち |
| §4.2 VFX Cue Contract v1 | IMPLEMENTED (SOURCE) | `vfx/cue-contract.mjs` |
| §4.3 Tank Frame Sequence v1 / RECORD_REPLAY / Viewer | IMPLEMENTED (SOURCE) | `vfx/frame-sequence.mjs`, `vfx/replay-viewer.mjs` |
| §4.3 CONTROLLED_SEEK | UNAVAILABLE | Photon 1.20.1 に時刻制御 API なし（P0） |
| §4.3 Forge 側 1 カメラ時系列 producer | NOT_IMPLEMENTED | |
| §4.4 Spatial & Timeline Inspector（Y 高度図・相関） | IMPLEMENTED (SOURCE) | `vfx/spatial-timeline.mjs` |
| §4.4 CLIENT_RENDER_POSE の Forge 観測 | NOT_IMPLEMENTED | P4 |
| §4.5 Repair 契約・P5 Evidence Packet | IMPLEMENTED (SOURCE) | `vfx/repair.mjs` |
| §10.3 Asset Method Manifest v1 | IMPLEMENTED (SOURCE) | `vfx/asset-manifest.mjs` |
| P1–P5 実クライアント受入 | NOT_RUN | 完了宣言は P5 実受入後のみ（PLAN §7） |

検証: `npm run test:vfx-studio` 32/32 PASS（Windows 11, Node 26.1.0）。既存 `test:visual-capture` 32/32、`test:result-export` 51/51、`test:visual-evidence` 62/63（失敗 1 件は本変更前から Windows の symlink 作成権限 EPERM で落ちる既存テスト）。CI（Linux）は未実行。

## 計画からの意図的な変更・追加（自己改善）

1. **prepare の例外を FAILED ではなく UNKNOWN 扱い**: 半端に生成された provider 状態がありうるため、同じ cue の再 prepare を盲目再試行として禁止（停止と観測は可）。
2. **stop は限定的な再試行を許可（3 回まで）**: 停止は復元方向の冪等操作なので、UNKNOWN 後の「盲目再試行禁止」の対象外とし、上限超過はエスカレーション。
3. **予算の整合検査を追加**: `spawnRate × lifetime` の定常粒子数見積りが `maxParticles` を、`intensity` が `maxCumulativeGlow` を超える cue を拒否（A09）。
4. **除外手法の検査を provider 名にも適用**: 許可された方式名の裏で Kimodo 等を provider として使う記録も拒否。
5. **Photon 1.21 既定ブランチの CC BY-NC-SA 4.0 化**を P0 で発見。AUDIT の権利ゲートへの追記を提案（P0-INVENTORY §3）。
