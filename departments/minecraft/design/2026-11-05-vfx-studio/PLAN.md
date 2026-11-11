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

## 10. 2026-11-11 統合拡張：モデル・アニメーション・VFXの制作方式と検証

**方針:** v1.1のP0–P6、現行の技術調査・安全境界・受入条件は削除も縮小もしない。この章は新たにモデル生成/変換・リグ・アニメーション制作のレーンを追加する。共通の Verification Router・Human Review・Mob AI観測の規則は [共通デバッグ計画](../2026-10-09-shared-mod-debug-roadmap.md) §8–14 が正本であり、ここは各制作ルートの技術仕様と既存VFXへの接続を詳述する。実Minecraftが描画正本。Blockbench previewは実ゲーム画面の代替証拠にはならない。既存MOD-AI、統合LAB、Evidence/CAS、Blockbench guard、BCTを再利用。第二DB、第二runner、別Editor制御系は作らない。

**現在の真偽:** 静的Celestial Staffの生成・部分修正・書出しと限定されたLinux/X11実機試験には証拠がある。一方、任意のモブの画像→制作、アニメーション自動生成、GLBからの汎用変換、Windows実機、Photonの連続描画は今回未実証。ここに書く新しい手段はすべて提案であり、外部ソフト導入・実機起動の許可ではない。

### 10.1 外部OSSの比較と導入判定

| 技術・出典 | 提供する独自価値 | 採否・優先度 | 実装前に確認すること |
| --- | --- | --- | --- |
| [orca-gamedev/img2blockbench](https://github.com/orca-gamedev/img2blockbench) | 画像から直方体・テクスチャを組み立て、編集可能な.bbmodel/geo等を作る。direct/mesh/Three.jsの3系統 | **優先PoC**。現行のBlockbenchを代替せず、生成候補として接続 | MIT、commit固定、画像の不明側面、provider送信先・費用、構造・アトラスの検査 |
| [MopicMP/mosaicary](https://github.com/MopicMP/mosaicary) | 既存GLB/glTF/Sketchfab→cuboid、GeckoLib/Bedrock/Java。条件により骨格とアニメも引継ぎ | **優先PoC**。外部3Dとanimationを持つ入力向け | MIT、ローカルplugin hash固定（URLロード自動更新禁止）、元モデルのライセンス/作者、token・アカウント初期OFF |
| [sosadly/blockbench-mcp](https://github.com/sosadly/blockbench-mcp) | 既存採用済みBlockbench操作。上流のbone/animation機能を選択して利用できる余地 | **中核維持・最小拡張** | 既存固定revとのAPI差分、bounded repair/UV/restore、安全guard、無制限execute_scriptは禁止 |
| [bernie-g/geckolib](https://github.com/bernie-g/geckolib) | Forge 1.20.1でbone・clip・controller・renderを実行 | **既存GeckoLib 4を適用**。静的itemへ強制依存させない | exact Forge・GeckoLib版、実クライアント側controller/描画の独立試験 |
| [gbusto/blocksmith](https://github.com/gbusto/blocksmith) | 文章→block model、bbmodel/GLB変換、animate/link。別の生成経路 | **研究・補欠PoC** | alpha 0.0.1、Python 3.12、Gemini等のAPI料金/秘密管理、Blenderが必要な出力と不要な出力を分離 |
| [Jahrome907/minecraft-agent-skills](https://github.com/Jahrome907/minecraft-agent-skills) | modding/resource-pack/testingなどの専門手順、validator | **選択的な知識・検査ルール導入** | MIT、Forge 1.20.1の対象範囲、既存AGENTS/TaskContextとの重複、13種を一括導入しない |
| [adhi-jp/minecraft-blockbench-mcp](https://github.com/adhi-jp/minecraft-blockbench-mcp) | GeckoLibアニメーション操作、特定時刻の静止画像、scope/認証/上書きの参考実装 | **隔離でコード研究**。標準の第二MCPは追加しない | editがclip全体を上書きする問題、effect-keyframeの欠落、session・ファイル権限と既存guardの整合 |
| [RenasDemirbas/BlockBenchMCP](https://github.com/RenasDemirbas/BlockBenchMCP) | IK、motion presets、接地・intersections、multi-viewなど制作検査 | **必要機能だけ研究** | GPL-3.0、eval系機能や旧版セキュリティ、現行editorに二重接続しない |
| [img2threejs/img2threejs](https://github.com/img2threejs/img2threejs) | 画像→手続き的Three.js立体 | **img2blockbench route3を介して評価** | Apache-2.0、コードの隔離実行、アップストリーム版固定 |
| [ahujasid/mcp-for-blender](https://github.com/ahujasid/mcp-for-blender)・[Nusiq/mcblend](https://github.com/Nusiq/mcblend) | 特殊なメッシュ、IK、Bedrock向けモデル/アニメ出力 | **特殊案件のみ** | Minecraft cuboidへの変換損失、bone/UV/GeckoLib互換、別アプリ起動の負担 |
| [Photon](https://github.com/Low-Drag-MC/Photon)、[LDLib](https://github.com/Low-Drag-MC/LDLib-MultiLoader)、[Lodestone](https://github.com/LodestarMC/Lodestone) | VFX・particle・trail・shader | **従来P0–P6を維持**。モデル作成ツールではない | ANCHORのAPI、ライセンス、依存、描画時計、停止、性能と復元 |

**採否の共通尺度:** Minecraftらしさ、editable cuboids/part identity、rig/pivot、UV/atlas、animationの保持・移植、部分修復、Forge 1.20.1互換、安全性、ライセンス・送信先・課金、ベンチマークでの品質/人間工数。READMEやスター数はPASSの根拠にしない。プラグインやMCPを複数同時常駐させるより、既存sosadlyの安全な編集経路へ必要な機能だけを接続する。

### 10.2 モデル生成方法のAI選択・途中変更

- 明瞭なMinecraft風の参照画像なら img2blockbench.direct をまず候補にする。
- 有機的な形状・複雑な奥行きなら img2blockbench.mesh または img2blockbench.img2threejs を比較。外部3D生成サービスの費用・外部送信は別の明示許可が必要。
- 既存のGLB/glTFとrig、clipがあるなら mosaicary.gltf を候補にする。
- 正確な杖/静的アイテム、特定パーツの修正なら blockbench.direct（現行guard）を優先する。
- 文章からcuboidモデルを作るなら blocksmith.experimental は検証用。アルファ版を既定にしない。

**途中切替はAIができる**。ただし①旧候補の入力/出力hashと品質状態を保存 ②変更理由と代替案を記録 ③新しいproviderのversion/権利/料金/権限を照合 ④別の出力candidateとして生成 ⑤骨格・アニメ・FXへの依存を再検証、という順番を守る。途中の失敗したモデルを削除せず、比較とrollbackのため既存CASに残す。人間への通知は「制作開始」「重要な方法変更」「完成時」のみ。細かなpart編集の通知は不要。

**未知の側面:** 画像一枚では背面・内部・寸法の正確さは保証できない。推測した形状は推定として記録。元の絵を勝手に原画像と異なる「正解3D」として認定しない。

### 10.3 Asset Method Manifest v1（設計契約、未実装）

最終成果物を model + texture/atlas + rig + animation clips + VFX cues + target profile + validation として一つのmanifestにまとめ、参照だけを保存する。各フェーズの方法・変更・差し替えを追えるようにする。新しいDBは作らず、既存CASのblob hash・Evidence/SourceSnapshotを利用する。

~~~json
{
  "schema_version": 1,
  "asset_id": "kneekura:dragon_boss",
  "profile_ref": "sha256:<profile>",
  "model": {
    "method": "mosaicary.gltf",
    "candidate": "B",
    "source_ref": "sha256:<licensed-input>",
    "bbmodel_ref": "sha256:<native-project>",
    "geo_ref": "sha256:<geckolib-geo>",
    "texture_refs": ["sha256:<atlas>"],
    "rig_ref": "sha256:<bone-layout>"
  },
  "animations": {
    "idle": {"method": "import_retarget", "clip_ref": "sha256:<idle>"},
    "walk": {"method": "generated_keyframes", "clip_ref": "sha256:<walk>"},
    "attack": {"method": "procedural_baked", "clip_ref": "sha256:<attack>"}
  },
  "vfx": [{"method": "photon_candidate", "cue_ref": "sha256:<cue>"}],
  "method_history_refs": ["sha256:<choice>", "sha256:<switch-a-to-b>"],
  "verification_refs": ["sha256:<structure>"],
  "human_review": "NOT_REQUESTED"
}
~~~

このJSONは説明用サンプル。実装時はschema_id、required/optional fields、source/profile/format version、hashの厳格検査、未定義key・パスや実行権限の注入・循環や欠損refの拒否を加える。山括弧付きplaceholderは実成果物として禁止。制作方法の選択イベントには、候補リスト、選択理由、対象条件、provider/版/commit、入力と出力hash、license、費用・送信先、計測した品質、切替前後・棄却理由・残る未検証領域を必須とする。

**差し替えの依存無効化:** 名前が同じでもbone親子関係、pivot、bind pose、座標・単位、左右反転、UVの割当が変われば古いclipは無条件流用しない。bone emitterもモデルlayout hashに結ぶ。glTFから移植不能なmaterial/IK/曲線/effect keyframe等は LOSSY_CONVERSION を記録し、変換成功を意味保存のPASSとしない。

### 10.4 Animation Production Contract（アニメーションを独立した制作物にする）

方式を **clip単位** で選ぶ。
1. keyframes_direct：idle/walk/attack等をAIが時刻・rotation/translation/scaleで生成。
2. import_retarget：GLB/glTFや既存素材の動作をbone対応・軸・ピボット・clip時間へ変換。
3. procedural_baked：IK、歩行、翼/尻尾などをルールから生成して固定keyframe化。
4. runtime_procedural：視線追従、反動、移動速度との同期などゲーム中に動的更新。
5. 必要に応じて同じclipの方式変更を許し、変更理由と修正前後を記録。idleだけ移植、walkはkeyframes、attackはproceduralなどを自由に組み合わせる。

**機械の検査:** 骨格参照・親子cycle・pivot/bind・clip loop/once/hold・時刻順/重複/異常値・補間/easing・Molang構文・静的poseの連続性・足の床貫通/接地滑りの有限sample・骨/武器の限定intersections・attack window・state transitionsを明示。これらはBlockbench previewと構造チェックで先に検査する。メッシュ衝突の厳密性やゲーム中のMolang評価までは証明しない。

**実機の確認が必要:** GeckoLib controllerの実状態遷移・実描画のpose・client/server同期・attack hit/animation/VFXのタイミング・実World collision/FX停止・描画負荷。モブAIの実際の意思決定理由についてはEntity Decision Observatoryの取得済み内部stateと結果だけを証拠にする。

**人間が判断する内容:** 動きの自然さ、迫力、キャラクター性、操作感、演出の好み。AIが骨格不一致や欠損テクスチャを人に発見させるのは非効率。画像/短い動画で判断できるものは水槽を起動せず提示する。

**更新安全:** clip一括replaceが既存の人手修正を消す可能性がある。対象clipのexpected old hash・project/generation・対象boneを固定し、editor readbackと不変部分比較を実施。未知完了の後に盲目retryしない。無制限のJS/任意ファイル読込を制作のために許さない。

### 10.5 VFX連携・水槽の位置づけ

- モデルの構造/UV/texture/clip syntax/骨格参照は、まずオフライン/Blockbenchで検証。毎回のMinecraft起動は禁止ではないが、必要性を説明できない繰返しは抑制。
- 水槽の重点を、Mob AI・経路探索の結果、実ゲームの物理/衝突、GeckoLib Controllerとserver/client時刻、bone/FX emitter、実際の表示、同期、実性能の計測に置く。
- 実機開始前に検証主張、既存証拠が不足する理由、新たに採るログ/対象UUID/時間窓・停止条件を記録。source/build/asset/scenarioが同等で追加証拠の無い反復はSKIPPED_WITH_REASONを残す。確率/再現性試験は目的と試行予算を明示して反復可。skipはPASSではない。
- 実ゲームでの演出は、AIがデータとログを検査。自然さ・迫力など人間の方が判断しやすい事項だけ比較画像/短い映像・必要なら一操作Debug Wandへ渡す。AIが対象配置、装備、背景/明るさ、録画、復元まで準備し、人にはコマンドを打たせない。
- VFXのRECORD_REPLAY/P2、時刻差があるCardinal-4、server authoritative HITとclient FXの分離、原画像不変、終了時復元など従来のP0–P6の条件を緩めない。

### 10.6 元のP0–P6と併走する新A0–A6実装レーン

| 段階 | 具体的作業 | 受入 |
| --- | --- | --- |
| A0: 現状棚卸し | main/PRの現行実装、モデルguard・GeckoLib・Provider API・権利/依存・Windows差を確認 | 機能をIMPLEMENTED/PLANNED/UNVERIFIEDで区別し、外部API/新プラグインの無断導入無し |
| A1: 生成・変換PoC | img2blockbench三ルート、Mosaicary GLB、既存direct editorの少数課題を比較 | 編集可能bbmodel、texture/UV/rig、未確定面の状態、版・入力hash |
| A2: Method Registry | 選択・方式変更・旧候補保全・最終manifest・差し替え互換性チェック | 旧アニメ流用の失敗/骨格変更/重複hash・欠損refを検出 |
| A3: Animation | 一体のモブでidle/walk/attack、keyframe/import/proceduralを必要に応じ選択 | clip/骨格・静的pose・loopと遷移の負例PASS。runtimeは別結果 |
| A4: Verification Router | source/offline/build/GameTest/Tank/humanの主張別ルーティング | 静的修正では不要水槽を使わず、Mob AI・実同期などlive必須の見落としも避ける |
| A5: runtime×VFX | 既存P1–P5を活用しbone追従演出とMob AIの観測を必要なrunで実施 | Source/build/run/UUID/tick、server HIT/client FXの時間差、復元/stopの実証 |
| A6: Human Review | 画像/録画による簡易確認。必要なら有限のdebug-only Wandシナリオ | 1操作・短い判断、不要な起動や人間による準備無し、未回答はPENDING |

**依存関係:** A1–A3はPhotonのlicense gateを待たずに独立できるが、A5のbone/FX実機同期は元P4以降の正当な条件を満たすこと。元のFX実装P0–P6はそのまま残す。

### 10.7 統合実証と敵対的受入

1. **静的アイテム**: UVやパーツ修正だけでEditor/static/export checkを完了し、実機未実行と「不要につき実機省略」を正直に記録。
2. **画像→四足モブ**: img2blockbench/Mosaicaryの適性を比較し、意図的な方式変更1回を行う。失敗候補も保存、rig/texture/idle/walk/attackの方法・clip・assetセットを検証。
3. **モブAI+攻撃+演出**: goal→実移動→攻撃→server HITとclient clip/FX→cancel/unloadを限定runで観測する。人間へは演出の自然さのみを短く示す。

**独立結果列:** model_structure、texture_uv、rig_layout、clip_structure、editor_preview、GeckoLib_runtime、mob_ai_runtime、VFX_runtime、performance、human_preference。それぞれsource/asset/runの証拠とPASS/FAIL/NOT_RUN/UNKNOWN/INCONCLUSIVEを保持し、単一スコアに合算しない。

**敵対的負例:** 画像正面だけ似る、背面UNKNOWNを正解とする、missing texture、同名でpivotが違うbone、animation effect/補間のロス、古いclipの無検証流用、上書き後の人手修正消失、無関係な変更で何度も水槽再起動、偽のdecision reason、異時刻4視点を同時映像と説明、未回答の人間レビューをPASSとする、許可のないAPI課金/素材ダウンロード。

**測定:** 同じ課題のbaselineに対し制作時間、失敗・方式変更数、clip修正数、必要証拠の欠損、実機起動時間・回数、人間操作回数、false-PASS率、LLM/API costを測定。改善数値を先に捏造しない。改訂による実装と実クライアント受入は未実施。

**状態:** DESIGN ONLY / EXTERNAL PROVIDER PROOF NOT_RUN / ANIMATION AUTOMATION NOT_RUN。元P0–P6の目標、安全・ライセンス・実験ワールド・履歴・復元・監査の全条件を維持する。

## 11. 2026-11-11 Animation Provider Selection — 小さく導入し、実装AIに改善余地を残す

**ユーザー判断:** Kimodo および video2mocap は不採用。依存関係、実装候補、MVP、将来の自動選択いずれにも入れない。暗黙のfallbackにも用いない。前節のモデル生成・VFX・検証・人間レビュー計画はそのまま保持し、本章はアニメーション制作の不足を補う段階導入・機能重複抑制・AIの改善権限を具体化する。

### 11.1 最終目的・既存コードの正本

1. AIが1体の rigged mob に対して idle/walk/attack（必要なら fly/cast/death）を制作し、途中でclipの制作・変換手段を変更できる。変換と実Minecraft上の再生はそれぞれ独立判定。アニメーション/clipごとの選択理由、変更・失敗、構造と動画証拠を既存Asset Method Manifestで参照する。
2. 第一制作手段は現在のTECH HUBのBlockbench編集ガードを通した sosadly。**上流 README に機能が載っていても、テックハブのピン止めしたアダプターから使用できると推測しない**。source-based capability inventoryを最初に作る。
3. 二番手以降のrepoは、sosadly+既存自作validatorと比べて不足する **具体的な機能** が確認できた場合にだけ薄いadapter/独立validator/スキル資料として採用する。別MCP server/別Blockbench pluginを常駐させない。
4. Forge 1.20.1 / Java 17 / exact target Forge patch / GeckoLib 4 ANCHOR。GeckoLib/Bedrock/glTFと一般Blockbench formatの座標・軸・単位・補間・effect keyframeの意味差を固定。モデルのscene/editor、ゲーム内GeoModel、server AI制御・HIT、client animation controller/visual、Photon VFX のauthorityを混同しない。
5. Owner/editor/live attest、使い捨てworkspace、無上書き、expected generation/hash、UNKNOWN後blind retry禁止、source/asset provenance、既存Evidence CASというハードゲートは継続。汎用JS実行・plugin install/uninstall・任意外部パスやネット接続は標準AIルートに出さない。新機能はこれらを迂回せず延長する。

### 11.2 repoの優先順位と「どこまで取り込むか」

| 順位 | upstream・調査対象 | 既存基盤との重複 | 導入の判断・範囲 |
| --- | --- | --- | --- |
| **S0 中核の機能開放** | [sosadly/blockbench-mcp](https://github.com/sosadly/blockbench-mcp) | 現在の選定済みprovider。create_rig, check_rig, get_rig, generate_animation, create_animation, add_keyframe(s), analyze_animation, preview_animation, export_project, request_review が上流にある | **最優先**。既存固定revのAPI/実態を調べ、未公開で価値があるtyped操作のみ現在のexclusive editor guardへ増設。丸ごと最新版に切替しない |
| **S1 静的な検証部品** | [adhi-jp/minecraft-blockbench-mcp](https://github.com/adhi-jp/minecraft-blockbench-mcp) | 作成・クリップ編集はsosadlyと重複。GeckoLib4向けfile checker・readback・still frame/format checksに差分 | **独立したread-only file validatorを第一候補**。export済みgeometry/animationsのschema、orphan bone、easingArgs、effect-keyframe検証を自作の最小検査へ移植/参考。全MCP常駐はしない |
| **S2 精密編集・知識** | [jasonjgardner/blockbench-mcp-plugin](https://github.com/jasonjgardner/blockbench-mcp-plugin) と [blockbench-animation skill](https://github.com/jasonjgardner/blockbench-mcp-project/blob/main/skills/blockbench-animation/SKILL.md) | create/keyframesは重複。animation timeline、range mirror/offset、GeckoLib専用easing、部分的なcurve編集・保存手順に特徴 | **Animation Skillは読み取り専用の参考知識として選択導入**。未対応の編集操作だけ source/format tests後に現行adapterへ追加。一般BezierをGeckoLibで再現可能と主張しない |
| **S3 手続き動作・IK** | [RenasDemirbas/BlockBenchMCP](https://github.com/RenasDemirbas/BlockBenchMCP) | rig, walk animation, analysis, screenshotの大部分が重複。足の接地、IK、モーションプリセット、干渉検査に差分候補 | **不足が実測された場合のみ、アルゴリズム/fixtureを研究**。GPL-3.0等の権利と不確かな任意コード経路を先に監査。無条件でコードをコピーしない |
| **S4 特殊制作のfallback** | [EL4CTEO/blender-skills](https://github.com/EL4CTEO/blender-skills) 中の blender-animation、blender-character-rigging、export/bake | 通常のkeyframeは重複。IK constraints、NLA、bake、特殊なリグ/変換などで差分 | **特定の要件がBlockbenchで不可能/非効率と証明された時だけ** headless・隔離 Blender adapterを検討。Blenderの完成をGeckoLib対応と扱わない。全スキル一括導入なし |
| **再利用** | img2blockbench、Mosaicary、BlockSmith、Minecraft Agent Skills、既存GeckoLib 4 | 直前§10で既に責務・導入ゲートを定義済み | 別のanimation systemとして複製しない。Mosaicaryは変換経路、img2blockbenchは主にモデル制作、BlockSmithは候補、Agent Skillsは選択的な知識、GeckoLibは実ランタイム |
| **不採用** | NVIDIA Kimodo、video2mocap | 生成規模と依存が今回の目的と不一致 | **対象外**。PoC、provider登録、隠れたfallback、調査前提にしない。ユーザー判断なしに復活させない |

先に比較すべき能力一覧は **①基本clip生成 ②既存clipの一部分だけ修正 ③骨格/回転中心/左右識別 ④GeckoLib4 exportとeffect easing ⑤基準フレーム取得 ⑥滑り・貫通・loop seam診断 ⑦状態遷移とserver eventとの整合 ⑧変更前後のreadbackと復元**。同じ機能を2つのtoolへ宣伝するのではなく、1機能につき **primary implementation 一つ**、必要なら独立validatorを一つにする。

### 11.3 単一の編集経路 — Adapter Capability Map

- **唯一の編集authority:** 現存のBlockbench owner/editor guard内の編集窓口だけ。AIや外部repoがsosadlyへMCPで直結して第二の書込能力を得る経路は提供しない。Blockbenchのproject UUID、instance identity、model format、plugin/adapter pinned hashes、generationを操作前後に確認。
- **Adapter registry:** capability_id → primary_provider + status(AVAILABLE/NEEDS_IMPLEMENTATION/RESEARCH_ONLY/BLOCKED)、supported format and exact versions、argument schema、expected output、failure/rollback semantics、provenance、required budgetを保存。単純なファイル参照/validatorにはMCP不要。上流が機能宣伝していても、capabilityに昇格できるのは実ソースと限定実行が通ったものだけ。
- **固定の高水準操作候補:** rig.inspect/validate、animation.create_baseline、animation.edit_keyframes、animation.edit_easing、animation.inspect/compare、animation.preview_frame、animation.export、animation.validate_file、animation.prepare_review。操作名は設計案で、既存CLIの実装済みAPIではない。AIが使うtoolの名前は1セットに整理し、外部provider固有名は記録・adapter内へ閉じる。
- **新規実装の要件:** typed finite input、対象clip/bone/channel/time range、expected old generation/hash、relative output in owned staging、bounded readback、editor/project identityを要求。新機能の該当箇所だけを許可リストへ加え、script-eval一般許可の解禁は不可。Undo履歴の存在は書込成功の証明やCAS snapshotの代わりではない。
- **二重書込検出:** 別プラグインからの非授権変更、手編集、format switch、bone UUID再生成、競合transactionによりexpected stateが変われば編集を中断、readbackで差を示し、勝手に重ねてapplyしない。
- **結果の独立性:** geometry/clip static、editor pose screenshot、export JSON、runtime controller/render、human aestheticはそれぞれ別のassertion domain。人間レビューは同一視点の短い比較が最優先で、BLOCKING request_reviewの無制限待機を標準の自律制作に組み込まない。

### 11.4 アニメーション制作と転送を別々のrouteとして記録

モデル生成手法とは独立に、各 clip は少なくとも下記を別々に選択する。必要に応じて一部だけ変更可能にする。

| stage | route候補 | 目的 |
| --- | --- | --- |
| skeleton | sosadly_rig / existing_rig / validated_retarget | bone tree、joint/pivot、自然な関節の配置 |
| motion authoring | sosadly_generated / direct_keyframes / procedural_baked / imported_existing_animation / specialist_blender | idle/walk/attackなどの実際の姿勢と時間変化 |
| motion repair | targeted_keyframes / interpolation_easing / retime_mirror / retarget / regenerate_clip | 部分変更。再生成したことを隠さず旧候補を保存 |
| format transfer | native_geckolib_export / validated_converter / mosaicary_from_gltf | json・geometry・textureのフォーマットと意味の変換 |
| runtime playback | geckolib4_controller / appropriate_mod_adapter | AI状態・attack event・server/clientとアニメ開始・終了の関係 |
| verification | offline_schema / editor_frame / event_trace / necessary_real_client / human_comparison | 何の性質を証明したかと未検証を分ける |

**Method Registry追加項目:** method_stage、provider_id + revision + license、input/output hash、source_format/target_format/format_version、bone_map hash、coordinate transform spec、pivot/bind layout hash、sampling policy、interpolation/easing/effect loss report、authoring methodとtransfer methodを独立したrefsとしてfinal asset bundleに記載。clipが同名でもbone UUID/階層/ピボット/アニメ効果の互換判定が通るまでは古い成果を使わない。

**フォーマットの落とし穴:** jasonjgardnerの一般Bezier/easingはGeckoLibでは同等に書出せない場合がある。GeckoLib専用easing指定・実exportのreadbackで確認する。adhiのclip upsertはreplace時に既存の手動調整を失うため、まず差分・期待hash・復旧点を作る。glTFからのmotion transferはRotation Euler/Quaternion、軸反転、単位、global/local transform、sampling、root motion、動作時間とeffect keyframeを区別する。

### 11.5 AI自己改善の自由度（自己改善は品質改善であり権限拡大ではない）

実装AIへ **手法/アルゴリズム・選択と比較の自由**を与える。ただしユーザーの判断・本番保護・ライセンス・予算・証拠を勝手に変更しない。

**変更してよいもの（通常の管理範囲内）**:
1. 動画/画像/数値の問題から clipごとに生成方式、補間、keyframe密度、IK/接地モデル、部分編集範囲、preview角度、テストfixtureを変える。
2. 不十分な結果から別の許可済みprovider/routeへ切替し、旧候補・理由・比較を保全する。不要な分岐を作らず、改善したものだけ採用する。
3. 未知の不具合に対して追加の **安価な静的validator・fixture・回帰テスト** やログprobeを提案/実装する。既存実装と重複するなら拡張または置換を試験・比較し、二重実装を放置しない。
4. 既存のSourceSnapshotや失敗修復履歴、上流Issue/README/ソースから、次に調べるべき候補を仮説として追加する。ただし自動install・外部への素材送信・新料金発生・unsafe actionを許可するものではない。
5. 本計画のphase順は、明示された依存関係と受入ゲートを満たす限り実装AIが合理的な順序へ変更してよい。方針変更時には plan delta・効果/理由・検証の変更点を短く残す。

**変更できないもの:** 利用者が不採用にした技術の黙った復活、実験対象外の製品改変、秘密/課金/公開範囲変更、無制限script、verified scope未満のPASS認定、外部ライセンス違反、既存run/asset/evidence破棄、無意味なMinecraft連続起動、無確認の破壊的置換、未回答の人間レビューを自動で承認すること。

**改善ループ（小さく閉じる）:**
- B0: 欲しい動作とacceptanceを固定し、現状のsource/capability/未確認を参照する。
- B1: 最小の既存routeを選んで1回作る。構造/previewで失敗原因を独立検証。
- B2: 失敗・変換損失・source不足があれば、対応する最小scopeのrepairか別routeを選ぶ。新規ツールを増やす前に現行の能力で解決可能か確認。
- B3: 同じclipと同じ確認観点でbefore/afterを比較し、効果がない編集・検証を反復しない。必要なら条件を変えて追加の証拠を採る。
- B4: 成功/失敗/未検証と時間・人の操作回数・実機必要性を履歴へ保存。上手くいった工夫は固定ルールでなく version付き推奨として蓄積。将来の作業で異なる結果なら再検討できる。
- B5: 複数の候補に有利な特徴がある場合は、人の好みで決める部分だけコンパクトな比較レビューを求める。途中で毎回確認を求めない。

**改善の権限区分:** オフラインでの生成・局所編集・検査/方法切替は既存の明示された許可範囲ならAI主体。新しい provider のインストール、外部ネット送信、破壊的書換、権限/課金・CI/本番変更は人間による別の明示的承認に留める。実機試験の反復はVerification Routerの三要件・owner・コスト予算を守れば根拠付きで行える。固定回数の一律禁止はしない。

### 11.6 具体的な段階実装 — 既存A0–A6と重複しない

| substep | 必要な最小実装・手順 | 独立した受入基準 |
| --- | --- | --- |
| S0 既存の能力棚卸し | pinned sosadly/現行asset guard、target Blockbench/GeckoLib4、Minecraft Forgeソースを調査。上流機能と利用可能scopeの対応表、依存/ライセンスを保存 | 何が使える/使えない/未検証かを区別。現在のCelestial Staff生成・repair・exportの回帰が壊れない |
| S1 中核のrig/clip制作 | sosadlyのcreate_rig/check_rig、generate_animation/add_keyframes、analyze/previewを最低限のtyped guardへ接続。まず自作・単純な四足or二足のモデルを用い、idle/walk/attackを制作 | bone tree/pivot、loop seams、位置/姿勢、before-after、失敗・partial/UNKNOWNを区別。実ゲーム未実行ならNOT_RUN |
| S2 読取検査と精密修復 | adhi由来のGeckoLib JSON validator、jasonjgardnerのskill/部分keyframe/easing手法を既存機能と比較。**不足のあった** 操作・validatorだけ新規採用 | export-readbackが一致。GeckoLib easingやeffect JSONの誤用を拒否。clip以外の不変を立証、二重MCP常駐0 |
| S3 手続き生成の追加 | 歩行/攻撃に接地・IK等が実際に必要なら、Renasのアルゴリズムを参考にオフラインfixtureを追加。必要に応じ許可済みBlenderでbake/retargetを別routeで試す | 生成した動作と同じ入力で従来routeを比較し、改善幅・conversion loss・CPU/IO/human負担を記録。権利/依存が不明ならBLOCKED |
| S4 方式・変換履歴の保存 | 既存Asset Method Manifestへclipごとのauthoring/transfer/repair/playback参照、旧候補、切替理由、rig layout・loss reportを接続 | 同名でpivotが違うrigへの古いclip混入、費用/外部権限の勝手な拡張、成果物改竄を負例で拒否 |
| S5 実ランタイムとHuman Review | Geckolib Controller、Mob AI、HIT→clip→VFXの因果が実機を必要とするケースだけWater Tankへ。原則Log first。美的判断は同一camera画像/短いclipでまとめて人間に依頼 | Editor/構造/RUNTIME/人間を別結論。不要Tank起動を防ぎつつ、必要なreal runを省かない。人間の操作数と未回答を記録 |
| S6 実装AIの改善受入 | 意図的なclip生成失敗・method change、sourceの変化、未知のeasing、接地不良を注入し、AIが最小scope修復/方法変更/結果記録できるか試す | 最小変更・失敗原因・再試行合理性・旧成果保全を証拠化、ガード破り0、人手操作を安易に増やさない |

**重複排除:** S0–S6は A0–A6 のうち A3（Animation）の詳細タスクであり、P0–P6（VFX）と並行可能。phaseを二重カウントせず、共通CI/Store/実験管理を再利用する。「別の新しい計画書」は作らない。

**初期実証モデル:** 一つは四足の歩行（接地と前後の脚）、もう一つは腕/武器のattack（ボーン回転・命中とVFX同期）を優先。単純な動作が通っていないのに膨大なモブ/多数のclipへ広げない。Windowsなど未検証プラットフォームの実機成功を先取りしない。

### 11.7 移行/非採用ルールと完了条件

1. SOSADLYを大幅更新する前に固定旧版・新候補を同じパイロットで比較し、既存杖/rig/animation/editor repair機能の回帰と権限の差分を確認。単に新API数が多いだけでは更新しない。
2. adhi/jason/Renasの機能が現在のsosadly+自作minimal validatorと同等なら外部実装を採用せず、調査参考としてのみ残す。選んだcapabilityにはprimary_providerを必ず一つにし、代替fallbackは異常時だけ明示選択する。
3. 成果が人の好み次第ならAIは決め打ちせず、1つの短いレビューにまとめる。一方、形式エラーや挙動ログの原因は人間へ手作業で探させない。
4. 今回の成功判定は「3clipが作れた」だけではない。method/format/playbackの証拠、構造/Editor/実ゲーム/Humanの独立状態、過剰起動なし、旧成果と人の編集保護、どのrouteを選び変更したか、を一緒に報告する。
5. 外部OSSの固定commit・出典・ライセンス・依存/安全条件を満たさない場合は、代替の安全な小実装またはNOT_RUN/BLOCKEDを選択し、すべての機能を無理に採用しない。

**章の状態:** IMPLEMENTATION PLAN ONLY。新規 animation adapter、provider導入、検証実行、外部課金・インストール・main mergeは未実施。
