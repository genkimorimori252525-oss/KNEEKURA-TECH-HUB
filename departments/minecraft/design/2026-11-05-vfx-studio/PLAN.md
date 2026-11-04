# KNEEKURA VFX Studio v1.1 — 確定実装計画

- 確定日: 2026-11-05 JST
- 設計状態: DESIGN APPROVED / IMPLEMENTATION NOT STARTED
- 対象: KNEEKURA-TECH-HUB の既存 Minecraft 部門、MOD-AI、統合 LAB / Water Tank Studio
- 計画の基準: main@4866d7d7bbfe42a668437ebf38f8a13d6a3d59e7
- ANCHOR: Minecraft Java 1.20.1 + Forge + Java 17。Forge の正確なパッチ版は実験対象の captured profile に従う。
- FRONTIER: 最新版の描画・VFX研究を別トラックとして保持。別バージョン/ローダーのコードがそのまま動くとは見なさない。
- この文書は実装許可・プラグインの自動導入・実機起動許可・merge の許可ではない。

## 0. 最終目的と最初の実証

既存 Water Tank の実 Minecraft 描画を正本として、実装 AI が演出を「設計→限定的に生成/調整→実 Minecraft で再生→記録済みの動きをコマ送り→XYZ・骨格・エミッターの数値と照合→差分修正→再検証」できるようにする。

最初の縦断実証は **1体の登録済みモブが武器を振る、青白い斬撃の残光と命中衝撃波**。ゲームプレイの威力・命中判定は VFX に決定させない。最小実証に必要ない特効、3Dエディタの全面実装、動画編集、全モブ探索には進まない。

達成条件:
1. 同一の固定条件で実 Minecraft 上のエフェクトが一度再生でき、キャンセル後に残留しない。
2. 時間情報付きの実描画フレーム列を保存し、人と AI が一コマずつ確認できる。
3. 既存 XZ 地図と同じ空間真値に Y 高度図、対象モブ、武器ボーン、FX エミッターの位置を合わせる。取得していない値は UNKNOWN と表示する。
4. ある一つの視覚上/数値上の欠陥を根拠付きで特定し、許可されたパラメータだけ変え、修正前後を同条件で比較する。
5. 既存セッション/ワールドの復元・Evidence/CAS・正確なプロファイルを破壊しない。

## 1. 現行実装の根拠・再利用箇所

新規実装者は以下を現行 main と照合してから作業する。2026-10-02以前の「未実装」記述には後継の状態更新があり得るため、実ソースと最新ハンドオフを優先する。

| 領域 | 既存ソース・根拠 | 再利用するもの/制限 |
| --- | --- | --- |
| 現行統合の正本 | departments/minecraft/CURRENT-HANDOFF-2026-10-02.md | LAB は Tech Hub 内の departments/minecraft/lab。旧単独 KNEEKURA-LAB を新しい正本にしない |
| 実 Minecraft 正本 | departments/minecraft/lab/docs/KNEEKURA_LAB_HISTORY.md | Web は操作・観測・比較の表示。別の Web レンダラーを実画面の正解にしない |
| 水槽制御・所有権 | departments/minecraft/lab/debug-workspace/README.md | Supervisor、使い捨て Arena、RunSnapshot、READY、実機の owner/lease/fence、reset、Evidence |
| 四方向撮影 | departments/minecraft/lab/debug-workspace/forge-bridge/src/main/java/com/github/tartaricacid/touhoulittlemaid/sim/debug/KneekuraDebugCardinalCapture.java | 同一サーバー状態の North/East/South/West を順次別 render frame で撮る。sameFrame=false |
| 撮影契約 | departments/minecraft/lab/debug-workspace/evidence/visual-capture.mjs | 正本 PNG、カメラ行列、viewport、frame/tick、原画像ハッシュ、復元証拠 |
| XZ 地図・XYZ | departments/minecraft/lab/debug-workspace/evidence/visual-geometry.mjs | 登録対象の位置・速度・向き・AABB と topDownSvg。既存地図は地形ボクセル一覧ではない |
| AI 視覚報告 | departments/minecraft/lab/debug-workspace/evidence/visual-compiler.mjs | 四方向 contact sheet、構造化事実、XZ 地図、原画像リンク、限定的 drilldown |
| モブの数値観測 | departments/minecraft/lab/debug-workspace/forge-bridge/src/main/java/com/github/tartaricacid/touhoulittlemaid/sim/debug/KneekuraDebugServerObserver.java | UUID 指定の SERVER_ENTITY_STATE: x/y/z、vx/vy/vz、yaw/pitch、health、alive 等。全ワールド走査ではない |
| 画像比較の限界 | departments/minecraft/mod-ai/VISUAL-FORMAT-BENCHMARK-2026-10-02.md | XZ 地図は投影図。遮蔽、ピクセル所属、正確なメッシュ衝突の証明ではない |
| 過去の作業計画 | departments/minecraft/lab/docs/superpowers/plans/2026-10-02-on-demand-motion-trace.md | Motion Trace は予定の段階あり。進捗を最新ソースで再調査し、二重に履歴DBを実装しない |
| 戦闘表現の責務 | departments/minecraft/techniques/boss-combat-toolkit/README.md | BCT-A/B/X/P: 攻撃ライフサイクルとサーバー命中処理、クライアント描画・音・FX Budget を分離 |
| モデル制作 | departments/minecraft/mod-ai/ASSET-INTEGRATION.md | 既存 Blockbench guard/CAS・静的アイテム実証を維持。GeckoLib モブと骨格VFXは別受入 |
| 他作業との衝突 | Tech Hub PR #97（弾幕 Score Mode）など並行開発 | 既存の Score Mode、Viewer 時間軸、Motion Trace と API/用語を比較してから共通抽象を追加。勝手に統合/再実装しない |

**重要:** 現行 Cardinal-4 は VFX の内部時刻まで固定できるという証拠ではない。既存のキャプチャは AFTER_LEVEL_BEFORE_HAND_HUD であり、実装には currentEffect() のある画面を拒否するガードがある。この制約を壊して画面効果を撮影しない。

## 2. 外部 OSS の扱い

| 候補 | 使い方 | 条件/注意 |
| --- | --- | --- |
| Low-Drag-MC/Photon の 1.20.1 Forge 系（配布版 1.1.17） | 第一候補の独立 VFX 作成・実行 provider。実機サンプルを試してから薄いアダプター化 | 1.20.1 ブランチに FX/FXRuntime が存在。実 API、必要 LDLib 版、保存形式、停止・時間制御は実物で監査 |
| Low-Drag-MC/LDLib-MultiLoader | Photon の対応依存を検査 | 既存 modpack/Forge/GeckoLibとの競合も確認 |
| Low-Drag-MC/Photon-Arsenal | 1.20.1 技術例の静的参考 | upstream アーカイブ済み。古い依存をそのまま採用しない |
| 37250977/photon-or-epicfight | 戦闘アニメーションのボーン追従・プレビューの設計参考 | EpicFight を共通必須依存にしない。GeckoLib 用は独自アダプターで実証 |
| LodestarMC/Lodestone | 粒子/トレイル/シェーダーの代替・補完候補 | 必要時のみ採用。Photon との共存・描画負荷を検証 |
| Photon 2.x / Veil 等 | FRONTIER の参考のみ | ANCHOR への直移植や旧 API と混同しない。ライセンスと移植許可を別途確認 |

参照:
- https://github.com/Low-Drag-MC/Photon/tree/1.20.1
- https://modrinth.com/mod/photon-editor/version/mc1.20.1-1.1.17-forge
- https://github.com/Low-Drag-MC/Photon-Arsenal
- https://github.com/37250977/photon-or-epicfight
- https://github.com/LodestarMC/Lodestone

**権利ゲート:** Photon 1.20.1 のソース側 GPL-3.0 記載と、現行プロジェクト側の別ライセンス/移植制限の関係を対象版で再確認する。ライセンス確定までは第三者コードや素材を Tech Hub のソースへ取り込まず、外部配布物の opt-in 利用と自作の薄い接続で検証する。生成したエフェクト自体の権利と、MOD 本体の再配布権利も別に記録する。

## 3. 変更しないアーキテクチャ原則

- 既存 MOD-AI + 統合 LAB + Evidence Store/CAS を再利用。第二の scheduler、canonical DB、起動管理、汎用権限系、Web での Minecraft 全描画再実装は禁止。
- 実 Minecraft が描画真値。Web の地図/連続画像ビューア/AI Packet は観測・派生表示であり、実ゲームプレイ上の効果を勝手に確定しない。
- サーバーは攻撃 ID・状態・開始/終了/命中・当たり判定・ダメージを所有。クライアントは VFX 描画・補間・音・画面効果を所有。粒子1個ごとのネットワーク送信はしない。
- 全モブ/全ブロックを常時収集しない。run に明示登録した UUID と有限の FX インスタンス/検証範囲だけを扱う。追加対象には明示登録とコスト上限が必要。
- 原画像や原 Observation を書き換えない。ラベル付き地図・スロー表示・動画は derived artifact。
- 実験開始・編集・シナリオ再生は opt-in、明示所有された使い捨て world だけ。通常プレイの save を操作しない。所有権・lease・revision・capability を再検査する。
- UNKNOWN / PARTIAL / NOT_RUN / INCONCLUSIVE / BLOCKED を PASS に丸めない。未確認のライブラリ機能を前提に契約を確定しない。

## 4. 新規機能の責務と最小契約

### 4.1 VFX Provider Adapter（新規・薄い）

担当: VFX アセットの能力確認、リソース検証、指定パラメータによる最小作成、有限再生、停止。Photon など provider 固有の API とフォーマットは内部に閉じ込める。

実装候補の操作は capabilities / validate / prepare / play / stop / observe。操作名は設計上の候補であり、現行コードの実装済みコマンド名ではない。execute_script、任意 Java/JS/GLSL 実行、任意 URL/パスの読込を AI に渡さない。未知の終了後は blind retry 禁止。

### 4.2 VFX Cue Contract v1（新規）

最小情報:
- effectId / providerId / providerSourceRevision / runtimeAssetHash
- 固定 profile / build / resource / config hash
- attackInstanceId / cueId / event kind（TELEGRAPH / START / HIT / CANCEL / END 等）
- actor UUID、任意の target UUID、world/dimension、emitter attachment（WORLD / ENTITY / BONE）
- タイミング（server tick と client/render clock の対応）、上限を持つ duration、見た目のパラメータ/色・カーブ
- seed がある場合は記録。seed だけで GPU 描画が決定論的になるとは主張しない
- 上限: 同時演出、粒子、トレイル長、累積発光、GPU/CPU/メモリ、記録フレーム数

モデル/テクスチャ/アニメーションの asset identity と演出 Cue identity を分離。GeckoLib のボーン名だけでなくモデルバージョン/ボーン階層 hash に結び、変化したモデルへ古いエミッターを黙って適用しない。

### 4.3 Tank Frame Sequence v1（新規）

実描画の **1方向・時系列** を最初の正本とする。各フレームに:
- exact session/run/RunSnapshot/process/arena epoch・revision・subject UUID
- effect asset hash、attackInstanceId、FX Instance ID
- serverTick / gameTime / clientTick / renderFrame / partialTick / capture time
- VFX simulation time: DIRECT_OBSERVED / DERIVED / NOT_EXPOSED を区別
- camera pose/matrix/viewport/FOV、render stage、raw PNG hash、writer/source Observation ID
- missing frame、stale frame、drop、time skew、capacity、restoration outcome

**コマ送りの2モードを明確に分ける。**
A. RECORD_REPLAY: 実Minecraftで記録したフレームをそのまま順次閲覧。巻き戻しは「記録画像の表示」であり、実ゲーム世界が巻き戻ったとは主張しない。まずこれを実装する。
B. CONTROLLED_SEEK: 起点の状態に安全に再初期化し、演出時刻を指定して再描画。Photon/provider の粒子・時計・乱数・GPU 特性と実 world 固定の再現性を実証した場合だけ導入。未実証なら UNAVAILABLE。

四方向の同時点 VFX は optional。既存 Cardinal-4 はサーバー状態が同じでも描画フレームは異なるため、VFX 時間が完全停止/再現する保証がない限り SAME_VFX_INSTANT を主張しない。時刻が異なるなら SEQUENTIAL_TIME_SKEW とラベル表示する。

### 4.4 Spatial & Timeline Inspector v1（新規・既存の拡張）

- 既存 topDownSvg と structured facts をソースとして使用し、XZ 平面図と Y 高度図を組み合わせる。
- WORLD XYZ と ARENA-LOCAL XYZ の両方を明示し、Y を Z と取り違えない。原点/範囲/方向ラベルを必ず表示。
- 登録 UUID ごとの position, velocity, yaw/pitch, AABB をその tick に対応させる。見失った対象は MISSING / STALE。
- 武器/GeckoLib ボーンの座標は CLIENT_RENDER_POSE（実描画時のボーン行列・部分 tick・モデル hash）として別途観測。SERVER_ENTITY_STATE と混同しない。
- FX エミッター、ビーム始点/終点、当たり判定範囲、エフェクト発火イベントはそれぞれ SOURCE_KIND を持つ。GPU 粒子の全位置を取得できない場合は NOT_EXPOSED。
- 地形のブロック一覧は既存 XZ の機能ではない。必要な ROI だけ明示して bounded block samples を追加し、一般的な全ワールド地図にしない。
- サーバー攻撃イベントとクライアント FX フレームを同一実行IDで関連付ける。遅延/異時計は数値で表示し、因果確定はしない。
- 既存 Motion Trace / Decision Observatory が進んでいる場合は既存の時系列仕様へアダプトし、別の trajectory store/時刻モデルを作らない。

### 4.5 AI Review & Repair（新規）

AI に渡すのは最初は: 結び付いた単一の contact sheet/選択フレーム、必要なら切り出し、XZ + Y 図、FX/骨格/対象の数値、指定された検証期待値、すべての取得状態と欠損理由。
AI の判断は VISUAL_INFERRED、数値は DIRECT_OBSERVED / SAMPLED_OBSERVED、スクリーンショット上の推測と区別する。

修正は schema で制限された FX パラメータ（例: color, startOffsetTicks, emitterLocalOffset, lifetime, spawnRate, trailWidth）から開始。expected old value・asset hash・generation・scope を指定し、編集対象外が変わらないことを検証する。モデル編集は既存 Blockbench asset guard の承認済み経路へ委譲。

## 5. 実装順序・依存関係・各ゲート

### P0 — 実装差分とライセンスの再確認（開始条件）
- 現行 main の正本を再確認。旧 KNEEKURA-LAB 水槽v2や他の PR を勝手に取り込まない。
- Photon 1.1.17 Forge、必要 LDLib、GeckoLib の同居を isolated Forge profile で確認。ソース/配布物ハッシュと権利を記録。
- 現行 Cardinal-4 の pause/currentEffect/AFTER_LEVEL、既存 topDownSvg、並行 Score Mode と Motion Trace を調査。
- ゲート: exact inputs/capabilities/limitation matrix。未解決事項があれば Photon に固定せず provider を比較。

### P1 — 1つのFXの作成・実再生・停止
- 既存 Forge 水槽と切り離した disposable 作業領域で Photon を編集・再生する薄い adapter を実装。
- まず固定位置の円形衝撃波。正しいイベント1回につき表示1回、停止/セッション終了で残光が消えることを検証。
- ゲート: source tests と実 Minecraft client acceptance を別々に保持。再生が手動のみなら AI automated PASS は保留。

### P2 — VFX 時系列撮影（RECORD_REPLAY）
- まず 1カメラ、明示した短い区間・フレーム予算で撮影。各画面に client tick/renderFrame と raw image hash を紐づける。
- pause 中に動いてしまうエフェクト、camera takeover、screen postprocess、手元描画を実測して状態を分ける。
- Viewer は記録済みフレームをコマ送り・停止・前後比較するだけ。任意時刻の再シミュレーションはしない。
- ゲート: 行方不明フレームの欠損表示、raw image に無改変、キャプチャ前後の状態復元、有限のストレージ/処理負荷。

### P3 — Spatial & Timeline Inspector
- 既存 XZ と SERVER_ENTITY_STATE を再利用し Y 高度図、tick 同期、イベントマーキングを追加。
- 正確な位置を導く provenance に依存して既存の人間/AIビューへ載せる。床や壁の表示は必要 ROI のみ。
- ゲート: 指定の1体の XYZ, velocity, AABB と点描画が一致。別 UUID/別 run/別 epoch は混在不可。

### P4 — ボーン追従・命中 cue
- 試験用自作 GeckoLib モブ1体と武器1種に限定。武器ボーンの CLIENT_RENDER_POSE を観測・変換し FX emitter に適用。
- BCT-A/B/P/X に従い、server HIT と描画/音を分離。カメラ揺れは独立 opt-in。
- ゲート: 武器軌跡の同期誤差、命中位置、cancel/死亡/アンロード時の終端、送信量を実測。

### P5 — 1サイクルの AI診断→部分修正→再比較
- 斬撃1件について初期演出、数値/画像の不一致検出、狙いを定めた1変更、同一セットアップ比較、変化なし項目の確認。
- 検証は raw vs derived、structure vs visual vs gameplay vs performance を区別。
- ゲート: 誰でも同じ記録を見て再確認できる Evidence Packet と、偽 PASS の負例テスト。

### P6 — 高度演出（要求がある場合だけ）
- fullscreen/post-process/hand HUD を含む capture stage は新しい明示 opt-in 契約として追加。旧 Cardinal-4 の guard を黙って緩めない。
- bloom / distortion / impact frame / 3D volume / advanced shader は ANCHOR で能力と互換性を実証した順で採用。
- ゲート: 他MOD/シェーダーと競合、画面可読性、FPS/フレーム時間、GPU負荷、リソース復元と劣化時 fallback。

## 6. 受入試験の最小マトリクス

| 領域 | 必須試験 | 合格と認定しないもの |
| --- | --- | --- |
| ソース・契約 | profile/seed/event/asset/UUID/epoch/read-only hash の検証、悪意のある入力/重複 ID/パストラバーサル拒否 | テストが通っただけの実Minecraft動作 |
| 実機 | Forge 1.20.1 実クライアントで FX 作成→再生→停止。run と provider 由来が一致 | 映像があるだけの loaded revision 同一性 |
| 時間 | フレームの刻印、gap/skew、停止した演出・遅延の測定 | 連続フレームを「必ず決定論的」と表現 |
| 空間 | 登録 UUID の XYZ/Y + ボーン位置 + エミッター位置を同時刻の証拠とリンク | 投影矩形を実メッシュ衝突の証拠とする |
| 四方向 | CAMERA/FX_CLOCK の条件が等しいかを検査。異なる場合は非同時表示 | sameFrame=false の現在の仕様を上書きする |
| 機能 | 攻撃キャンセル/死亡/アンロード/target loss 後に FX が残らない | client FX がサーバー命中を決定する |
| 復元 | 水槽の original world/Camera/input/paused/config/FX インスタンスの復旧を検証 | UNKNOWN の後に無条件再試行 |
| 性能 | 有限数・キュー欠損・実測フレーム時間・負荷/劣化を記録 | 数値未測定の「軽量」「最適」 |

## 7. 最初の実装担当に渡す具体的順序

1. main と並行作業の状態を照合し、能力/未実証/誤解がある場合は表を修正する。
2. P0 の技術・権利ゲートを最初に実施し、実装によるローカル環境変更前にレビュー可能な plan delta を残す。
3. 新規の編集エンジンを作らず、Photon の1種類のFXを小さい外部 adapter で再生できるかを確認する。
4. 同時に既存地図・コマ送りViewerの再利用箇所を確定する。修正は小さく、依存順で P1→P2→P3→P4→P5 を行う。
5. 各 phase で失敗例と原始証拠を残し、実Minecraft未実行なら明示的に NOT_RUN とする。
6. マージ、Actions/runner/権限の変更、本番worldの操作、第三者コードの転載は別に承認を取る。

実装を「完了」と宣言できるのは P5 の１件の再現可能な実クライアント受入と、必要な安全・証拠ゲートを満たしたときだけ。P6は独立拡張であり P5 完了要件に含めない。

## 8. 制約・軽量化方針

- デフォルトで VFX Studio は OFF。インストール・依存解決・ネットワーク通信・常駐サーバー・カメラ制御を通常タスクで開始しない。
- 既存 Evidence Store/CAS、TaskContext、撮影、モデル guard、LAB runtime に薄い adapter と検証を追加する。全体の第二実装をしない。
- 画質、FPS、サンプル頻度、保存上限は試験ごとに明示・実測で調整する。無制限の動画撮影は行わない。
- AIが一般のシェーダーコードを直接実行する権限は与えない。レビュー済みの定義/パラメータだけ変更する。
- 調査先の呪術廻戦MOD等は見た目・時間設計の参照に留め、権利確認なく第三者のテクスチャ/音/エフェクト資産を複製しない。

## 9. 監査と状態

同ディレクトリ AUDIT.md に軽い敵対監査・現時点の未解決ゲートを記録する。判定は **PLAN READY WITH TECHNICAL GATES / CODE NOT IMPLEMENTED**。

この計画の採用は、既存のWater Tank/Blockbench/MOD-AIの成功した実装を破棄・置換・書き直すことを意味しない。
