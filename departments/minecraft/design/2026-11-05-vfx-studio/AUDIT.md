# KNEEKURA VFX Studio v1.1 — 軽量・敵対監査記録

- 実施日: 2026-11-05 JST
- 対象: PLAN.md / 計画基準 main@4866d7d7bbfe42a668437ebf38f8a13d6a3d59e7
- 監査方式: 既存ソース・検証報告・公開 upstream の静的調査による設計監査。**独立レビューや新規実クライアントテストではない**。
- 総合判定: **DESIGN READY WITH GATES**。方針の重大な論理破綻は見つからなかったが、実装・実機・権利・互換性の合格は未確認。導入済み/動作済みとは記載しない。

## A. 現行の真偽区分

| 主張 | 確認した根拠 | 判定 |
| --- | --- | --- |
| 既存水槽は実 Minecraft を正本にしている | lab/docs/KNEEKURA_LAB_HISTORY.md / 現行統合ハンドオフ | CONFIRMED_DESIGN |
| registered UUID の XYZ, velocity, yaw/pitch, AABB | KneekuraDebugCardinalCapture.java の entityFact/serverFacts、KneekuraDebugServerObserver.java の SERVER_ENTITY_STATE | IMPLEMENTED; 各ランの鮮度は別途 |
| XZ の俯瞰地図と人/AIの画像資料 | lab/debug-workspace/evidence/visual-geometry.mjs, visual-compiler.mjs | IMPLEMENTED |
| Cardinal-4 が実画面を撮影し復元する | 同名 Java 実装、KNEEKURA_LIVE_ACCEPTANCE_REMAINDER_20261002.md | REAL_CLIENT_VERIFIED_FOR_PRIOR_SCOPE |
| 全モブリアルタイム地図 | 現行は明示 UUID と bounded subjects | NOT_ESTABLISHED |
| VFX の一時停止/巻き戻し/四方向同時瞬間 | Photon provider API と client time を含む実機テストなし | NOT_ESTABLISHED |
| 武器ボーン、FX emitter、画面全体シェーダーの空間記録 | 現行 raw subject snapshots の外 | NOT_IMPLEMENTED_IN_THIS_PLAN |
| AIによるVFX自動編集・リテイク | 現行 Blockbench 静的アイテム guard とは別 | NOT_IMPLEMENTED |
| Photon Forge 1.20.1 版 | https://modrinth.com/mod/photon-editor/version/mc1.20.1-1.1.17-forge および upstream 1.20.1 branch | RELEASE_EXISTS; RUNTIME_COMPATIBILITY_NOT_TESTED |

## B. 失敗を想定したレビュー

| ID / 優先度 | 不具合になり得る点 | 計画に反映した防止策 | 実装前/受入時のゲート |
| --- | --- | --- | --- |
| A01 / HIGH | Cardinal-4は4つの別render frame。粒子が動くのに「同一瞬間の4視点」と誤記する | 1視点 RECORD_REPLAY を先行。四方向は VFX clock freeze の証拠がなければ sequential time skew を表示 | 実 tick/render frame/FX clock 差が一致するかを実測 |
| A02 / HIGH | 既存 capture stage は AFTER_LEVEL_BEFORE_HAND_HUD で post-effect を拒否。画面の歪み・手元演出が撮れない | P6 で別 opt-in capture stage。既存ガードを緩めない | stage別 PNG と原画維持、カメラ/画面状態復元 |
| A03 / HIGH | XZ 地図が全モブ/全ブロック地図と誤解される | 対象UUID限定の地図を保持。必要範囲だけ bounded block query と Y elevation を追加 | 未登録 mob は描かない。欠損/未捕捉は明示 |
| A04 / HIGH | ボーンの client pose、server XYZ、VFX emitter の時間・座標系の違い | SOURCE_KIND と座標系、profile/model/bone layout hash、tick+partialTick を結び付ける | 既知の武器動作で位置誤差を独立検証 |
| A05 / HIGH | Photon の版/依存/API/ライセンスを想像で統合する | P0 で配布版、対応するLDLib、ライセンス条件を固定。コード移植・転載は保留 | upstream の適用条件確認、隔離環境実動作、第三者資産なし |
| A06 / HIGH | AI の操作が一般コマンド/任意 script を許し、ワールドやローカルファイルを破壊する | opt-in disposable world、既存owner/lease/CAS、schema限定操作、無断自動install無し | target mismatch / stale generation / unknown outcome / path traversal 負例 |
| A07 / MEDIUM | モブの映像と構造化座標を同じ瞬間として扱う | 観測時刻/発生源/鮮度を別々に保存。描画上の推測と直接数値を分離 | 不一致時は UNKNOWN / INCONCLUSIVE、見かけ上一致で PASSにしない |
| A08 / MEDIUM | GPU粒子やシェーダーの巻戻しを seed のみで保証する | RECORD_REPLAY で原フレームをコマ送り、CONTROLLED_SEEK は別の実証ゲート | 再実行時の差を測定。seek不可は UNAVAILABLE |
| A09 / MEDIUM | 常時全フレーム高解像度撮影でストレージ・描画負荷が増大 | 有限の ROI・秒数・fps・バイト数・対象数・書込キュー予算。通常時OFF | drop/queue/frame timeと停止後の回復を測定 |
| A10 / MEDIUM | 既存 LAB/Viewer/Score Mode と機能が重複、正本が分裂 | 統合LAB+既存EvidenceStore。Score Mode(PR#97)やMotion Traceの最新ソースと照合 | 新 DB/runner/standalone LAB を作っていないこと |
| A11 / MEDIUM | aestheticな好みを画像差分だけで PASSとする | 数値・視覚・ゲームプレイ・性能を分離。AI評価は根拠付きだが推論として残す | 実際に不自然な斬撃例と正常例を比較 |
| A12 / MEDIUM | cancel/世界再読込でクライアントに粒子/音/残像が残る | lifecycleに CANCEL/END/UNLOADを持たせ、有限寿命とidempotent stop | 早期キャンセル/死亡/アンロード/遅延packetの負例 |

## C. 実装を始める前の「止める条件」

1. 1.20.1 Forge / Photon / LDLib / 他必須依存の同居と出典が確認できない。
2. 該当 upstream ライセンスの条件が明らかでないまま、第三者コード/資産のコピーや未許可の移植が必要になる。
3. 使用する水槽が作業用ワールドではなく本番ワールドを指している、または owner/lease/RunSnapshot が不一致。
4. キャプチャ中に実ゲームのプレゼンテーション状態を復元できない。
5. 完了UNKNOWN後に同一の副作用命令を再送しないと先に進めない。
6. 現行受入記録・権限境界・別作業の成果を壊さないという証拠がない。

「止める条件」に遭遇したら、その phase の結果を BLOCKED/UNKNOWN と記録し、必要な **最小修正の提案**を出す。安全制約を外して通したことにはしない。

## D. あえて採用しなかったもの

- 新しい第二の水槽、Web側の独自 Minecraft レンダラー、独自Evidence DB、常駐AIエージェント。
- 最新 Photon 2.x の1.20.1への無許可直接移植、商用/配布条件を無視した upstream 統合。
- 任意スクリプト/GLSLのAIによる無制限実行。
- 全世界のモブ/ブロック/粒子を無制限にスキャンする「完全地図」。
- GeckoLib と EpicFight の同時必須化。
- 一次実証時点での動画編集、HDR/ポストエフェクト全面制作、フォトリアル演出の自動採点。
- 単にソース試験が通ったことを、実Minecraftや演出品質の合格へ昇格させること。

## E. 最終評価・次の条件

設計は軽量で、既存の verified Tank / 4方向 raw capture / 構造化位置 / XYZ / Evidence を維持しながら VFX の新しい責務だけ追加する方向に整っている。

**Plan = READY（対象範囲とゲートを確定） / Runtime = NOT_RUN / FX Provider Compatibility = NOT_RUN / AI VFX Editor = NOT_IMPLEMENTED / License Gate = OPEN.**

次の作業は PLAN.md の P0 から始める。P0の権利・API・実機確認結果により Photon との接続方式は修正できるが、ここに記載した根本原則、既存水槽の再利用、真偽と証拠の区分は変更しない。

レビューはこの branch に書類だけを提案する。merge/公開範囲/Actions/runner/設定/秘密の変更は行わない。
