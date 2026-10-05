# 水槽の状況確認・時刻連動・実験比較 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [x]`) syntax for tracking.

**Goal:** AIと人が、水槽の実際の表示状態・観測時刻・実験条件・結果を同じ証拠から確認できるようにする。

**Architecture:** 既存Debug WorkspaceとEvidence Storeの上に、読み取り中心の確認票・時刻別packet・実験カードを追加する。単独HTMLとCLI JSONは共通の有界packetを使用し、native側は格子の状態通知だけを拡張する。再現と画像比較は既存registration/export/CAS/visual comparisonへ接続する。

**Tech Stack:** 既存Node.js ESM/node:test、Java17/Forge1.20.1、Gson、Canvas2D/単独HTML。新規依存なし。

**Spec:** [改善設計](../specs/2026-10-06-tank-observability-design.md)

状態: 2026-10-06承認後、T1〜T5のsource実装・関連回帰と単一全体レビューの指摘修正を完了。基準HEAD `07c34216319400ddfa3d1a99f7b9970bf8857190`。T6は進行中。[受入記録](../../../departments/minecraft/lab/docs/KNEEKURA_TANK_WORKBENCH_ACCEPTANCE.md)に実際の成功・失敗・未取得を記載する。world/observer/区間全体のpresentationを既存証拠で完全照合できない比較はINCONCLUSIVE。実機品質維持と最終CIは未確認。
同日の軽量監査を反映済み。観測への干渉、表示条件、残lease、表示間引きの4点を必須のテスト・受入条件へ追加した。非劣化の実証はT6まで未完了。
実装はT1→T2→T3→T4→T5→T6を同一セッションで順次進め、全体の独立レビューを最後に一度行う方式を推奨する。packetの相互依存が強く、taskごとの大量の別セッション化は不要。

## Global Constraints

- TECH HUB内のLABを正本とする。正式元ワールドは保全し、実機変更は検証用複製に限定する。
- 格子ONは通常用profileの希望であり、既存のowner照合・recipe照合・120秒以内の元leaseを迂回しない。期限切れを黙って延長しない。
- raw/canonical証拠と既存public形式は保全する。新しいderived schema/CLIを追加し、旧artifactがそのまま読めることを確認する。finalized runへの追記を行わない。
- 新しい依存関係、常駐サービス、自動uploadは初版に追加しない。性能の許容値は各実験に登録し、平均値だけでcold outlierを隠さない。
- JSON概要256KiB、入力50,000観測、表示128点、Path64ノード、bookmark32件。取得不能な情報を推定値で埋めない。
- 通常native状態記録1Hz以下、状態変化込み2件/秒以下。元のwriter制限と観測OFFを維持する。
- 通常profileは格子ON。Motion/Projectile/deep観測は従来どおり明示選択。性能profileは表示と観測条件を明記する。
- 新status通知は既存heartbeatの抑制時計を更新しない。queue圧迫時は新statusを先に抑制し、既存観測のdropを追加で発生させない。
- 外観検証には格子OFF・明るさ補正OFFの対照画像を残す。性能はCPUだけでなくframe時間・server tick処理時間・heartbeat間隔・証拠dropを確認し、必要計測なしに非劣化と判定しない。
- `READY`には実験・結果確定・後片付け・余裕時間が元leaseの残時間内に収まる根拠を要求し、開始直前も照合する。記録済みremainingは権限として使わない。
- 指標は要求区間の照合済みcanonical証拠から計算し、表示点・bookmark・cursorの選択とは独立させる。coverage不足で全区間の成功を主張しない。

## Review Focus

1. 同じworld名・座標でも別fixture/recipe/ownerの証拠が混入する入力 → T1/T2でidentityと由来の回帰。
2. pause、期限切れ、disconnect、開始前の待ち時間、queue飽和 → T1でheartbeat/drop非干渉、T2でfreshnessと残時間再照合の回帰。
3. cursorより先のDecision概要、前windowのspawn除去、静止中の履歴消失 → T3で時刻境界と既存停止回帰。
4. A/Bで縮尺・観測密度・表示・時計・対象対応が違う入力、表示上限を超える記録 → T4で比較不能/coverage不足と集計不変性、T6で補正なし画像と性能の受入。
5. finalized run、欠けた過去画像、private path、壊れたhashを含むexport/replay → T5で不変性・非公開・不足表示回帰。

## ファイル表記と共通interface

以下はrepository root相対。`L = departments/minecraft/lab`、`W = L/debug-workspace`、`E = W/evidence`、`B = W/bridge`、`J = W/forge-bridge/src/main/java/com/github/tartaricacid/touhoulittlemaid/sim/debug`、`JT = W/forge-bridge/src/test/java/com/github/tartaricacid/touhoulittlemaid/sim/debug`。表の作成/変更パスにはこの定義を展開する。

既存のrun identityは変更しない。新しいderived値は `{status,value,sourceObservationIds,observedTick,limitations}` を持つ。`status`はそのschemaで定義したenumのみ、取得不能な`value`はnull。参照IDに必ずrun identityを対応させる。

- `TankStatus`: schema `kneekura.tank-status/v1`。`identity,worldBinding,geometry,presentation,channels,health,evidenceRefs`。
- `worldBinding`: `{authorityHash,copyBaselineHash,fixtureHash,fixtureChanges,provenanceStatus}`。hash不明はnull、未照合を同一と判定しない。
- `presentation`: `requested,registered,eligible,drawSubmitted,pixelEvidence,reason,reportedRemainingMs`。remainingは記録時点の参考値であり権限ではない。
- `TankPreflight`: schema `kneekura.tank-preflight/v1`。`profile,status,reasons,checks,timeBudget,leaseCheck,evidenceRefs`。状態は`READY/NOT_READY/UNKNOWN`。`timeBudget`は`{experimentMs,finalizationMs,cleanupMs,marginMs}`、各値は非負の有限整数、合計は元lease上限120,000ms以内。`leaseCheck`はowner照合が返す`{status,remainingMs,requiredMs}`のその時点の結果であり、保存・再読込して開始権限にしない。不明値はnull。
- `CursorDecisionPacket`: schema `kneekura.cursor-decision/v1`。`identity,cursorTick,window,overview,layers,quality,evidenceRefs`。
- `ExperimentDigest`: schema `kneekura.experiment-digest/v1`。`identity,question,registeredAssertions,conditions,actions,metrics,quality,cleanup,evidenceRefs`。
- `quality.coverage`: 要求/取得区間、取得件数、区間内の対象件数、gap/drop/上限による不足と根拠。不明件数はnull。表示側は別に`displaySelection`として対象件数・表示件数・省略件数・選択規則を記録し、metricsの入力にしない。件数が分かることだけで連続観測の完全性を保証しない。
- `ExperimentComparison`: schema `kneekura.experiment-comparison/v1`。`status,before,after,alignment,conditionDifferences,metricDifferences,limitations`。
- `ReproductionManifest`: schema `kneekura.reproduction-manifest/v1`。request/assertionの元hash、source/world/observer binding、既存export参照、有限budget。

## T1 — 格子の実状態と水槽の由来を記録する（P0）

**Files:** 作成 `J/KneekuraDebugTankStatus.java`、`JT/KneekuraDebugTankStatusSelfTest.java`、`E/tank-status.mjs`、`E/tests/tank-status.test.mjs`。変更 `J/KneekuraDebugTankPresentation.java`、`J/KneekuraDebugTankView.java`、`J/KneekuraDebugClientBootstrap.java`、`J/KneekuraDebugEvidenceWriter.java`、`B/runtime-api-selftest.mjs`、`L/package.json`。既存writerを再利用し、新status専用の有界受付とheartbeat非干渉を追加する。現行`recordGlobalObserved(...)`の無変更呼出しでは、dropされた通知もheartbeatを抑制するため不十分。

**Interfaces:** `buildTankStatus({observations,identity,expected,worldBinding,health}) -> TankStatus`。native通知はGLOBAL_HEALTH scopeの新lane `TANK_PRESENTATION_STATUS`、payload schema `kneekura.tank-presentation-status/v1`。payloadにrecipeHash/geometry/owner identity/状態理由/元lease内の記録時remainingを含め、credentialは含めない。

- [x] `tank-status.test.mjs`に、同名world・違うfixtureを同一扱いしない、未取得はnull、foreign run/Arena拒否、draw送信とpixel確認を別扱いにするテストを作成する。`node --test debug-workspace/evidence/tests/tank-status.test.mjs`で未実装による失敗を確認。
- [x] pure-Javaテストに、fake monotonic clockで元120秒期限、pause、server切替、max2件/秒、記録抑制数、disconnect後の状態を固定する。新しい期限を生成しないことを検証する。
- [x] `KneekuraDebugTankStatusSelfTest`とwriter接続テストで、同じ既存観測列・clock・drain順に対してstatus ON/OFFのheartbeat発行tickが一致することを確認する。statusの受付/dropの双方、queue満杯直前・満杯・回復を含め、既存観測の受付数とdrop数が悪化せず、status抑制数を別に報告することを固定する。
- [x] `KneekuraDebugTankStatus`へ状態のimmutable snapshotと送信頻度制御を実装。Presentation更新、render tickの失効検査、実際のgrid `endBatch`完了から通知し、既存writerへ非同期enqueueする。render callbackでdisk I/Oや追加world queryをしない。
- [x] writerにstatus専用の低優先受付を追加し、既存観測用queueの容量をstatusで占有しない有界な待機枠を使う。status受付/dropは既存heartbeat時計を更新せず、既存laneを優先してdrainする。既存laneの意味・上限・heartbeat抑制規則は維持する。
- [x] `buildTankStatus`でnative通知を既存canonical読取から整理する。producerが無い旧runは`NOT_CAPTURED`。freshnessは現在owner/serverと同一clock domainで判断し、別processのnanoTimeを比較しない。保存済み通知は「当時の状態」と明示する。
- [x] packageの既存Motion/Decision検証へNode回帰を追加し、Java pureテストを既存runtime/API selftest経路へ接続する（`W/bridge/runtime-api-selftest.mjs`）。関連Node/Java/Forge compileが成功したらこの単位をcommit。

**受入:** recipeファイルの存在だけで格子ONと報告しない。期限後の描画資格は失われ、保存済みの過去の描画証拠はその時刻のまま残る。status通知の有無によって既存heartbeatが抑制されたり、既存観測に追加dropが発生したりしない。実負荷での確認はT6でも行う。

## T2 — 通常検証の格子ONと開始前確認票（P0）

**Files:** 作成 `B/tank-preflight.mjs`、`B/tests/tank-preflight.test.mjs`。変更 `W/cli.mjs`、`B/owner-prelaunch.mjs`、`L/docs/KNEEKURA_REGISTERED_TANK_PRESENTATION.md`、`L/package.json`。

**Interfaces:** `buildTankPreflight({status,profile,requiredChannels,timeBudget,leaseCheck}) -> TankPreflight`。`profile`は`{kind:'OBSERVE_GRID'|'BENCHMARK',grid,brightness,motion,decisionChannels}`。全項目を指定し、BENCHMARKの暗黙既定値を禁止。既存`prepareOwnerControl(...)`の成果、T1のpacket、同一clock domainで経過時間を控除した最新のowner照合を入力に使う。`leaseCheck.status`は`SUFFICIENT/INSUFFICIENT/UNKNOWN`。これはread-only判定であり、実際の開始時には既存owner gateで再計算する。

- [x] テストで、要求格子ON/実記録なしはUNKNOWN、期限切れ・recipe不一致はNOT_READY、新しい同一runの描画送信・必要観測・十分な残leaseありはREADYと固定する。BENCHMARKではgrid=falseも明示条件として受理する。既存一般起動への副作用がないことを確認する。
- [x] 残時間の境界テストを追加する。実験30,000ms・結果確定5,000ms・後片付け5,000ms・余裕5,000msなら必要時間45,000ms。その他条件が有効な場合、最新残時間45,000msでREADY、44,999msでNOT_READY、照合不能/古い保存値だけならUNKNOWN。preflight後の待機で不足するケースはdispatch直前に拒否し、owner期限が延長されないことを確認する。
- [x] 通常profileの準備時に、保存済みrecipeから既存`kneekura/tank-presentation.json`をresource artifactへ入れる。owner登録を先に済ませ、起動後T1の証拠でpreflightを再確認する。登録済みartifactのin-place書換えは行わない。
- [x] 新CLI `tank-status` / `tank-preflight`でJSONを返す。実験開始の前提確認に接続し、UNKNOWN/NOT_READYの理由と既存の準備手順を示す。撮影や確認中の経過時間も控除し、dispatch直前に同じ予算を既存owner gateで再照合する。自動lease延長や勝手な再起動は追加しない。
- [x] `npm run test:bridge-owner-prelaunch`と追加テスト、既存起動selftestを実行し成功後commit。通常/性能profileのコマンド例を同じcommitに含める。

**受入:** 正式元save、変更したfixture、実験領域、格子要求/実状態をAIと人が別項目として確認できる。preflight時にREADYでも開始時に残時間不足なら拒否され、元leaseの内側に実験と終了処理の予算を確保する。

## T3 — 同じ時刻・固定座標の図とDecision（P1）

**Files:** 作成 `E/cursor-decision.mjs`、`E/tank-map.mjs`、`E/tank-workbench-view.mjs`、`E/tests/cursor-decision.test.mjs`、`E/tests/tank-map.test.mjs`、`E/tests/tank-workbench-view.test.mjs`。変更 `E/decision-presentation.mjs`、`W/cli.mjs`、`L/package.json`。既存`E/decision-view.mjs`の旧artifact表示は互換維持。

**Interfaces:** `buildCursorDecisionPacket({observations,identity,subjectUuid,window,cursorTick,maxGapTicks}) -> CursorDecisionPacket`、`buildTankMap({status,positions,declaredPaths,viewport}) -> {bounds,axes,layers,evidenceRefs}`、`renderTankWorkbenchHtml({status,preflight,cursorPackets,map,experiment,comparison}) -> string`。後2引数はT4接続前はnull。

- [x] cursor=105/観測100,110のfixtureで110のfactを出さず、100を105の新観測へ書換えないテストを作成する。前window spawn/停止/削除/再移動、gap、run/revision変更を併せて確認する。
- [x] `queryDecisionDrilldown`と`buildRetainedDecisionPresentation`を再利用してcursor上限のpacketを作る。参照に必要な過去spawn/terminalを保持し、表示位置のwindow制限と分離する。旧schemaを変更せず新schemaを返す。
- [x] mapの基準範囲をT1のgeometryに固定し、X/Z/北/1ブロック目盛と既存線種を描画する。位置だけから壁やtargetを補完しない。図からはみ出した点を境界内へ丸めず、範囲外と明記する。
- [x] HTMLでcursor時点/区間末尾を明記し、該当packetと図を連動させる。保存済み観測tick/イベントtickから最大256時点を選択する。共通samples/facts/layersは一度だけ格納し、各時点はindexで参照する。埋込JSON全体が256KiBを超える場合は範囲を狭める明示エラーとし、全tickの巨大packet複製や暗黙間引きはしない。
- [x] 点・cursorの選択に`displaySelection`を添え、対象/表示/省略件数と選択規則を示す。表示用配列をT4の集計入力へ渡さず、元区間の照合済み証拠への参照を保持する。
- [x] 新CLI `tank-view --output ...`へ接続し、出力はretained run外の新規ファイルのみ。実ブラウザで時刻戻し・対象変更・固定縮尺・空層・巨大値・HTMLエスケープを検証。関連Motion/Decisionとvisualテスト成功後commit。

**受入:** 同じcursorで図とDecisionに未来の情報が混入しない。A/Bで同じ1ブロックが同じ画面上の長さになり、取得なしと表示OFFが見分けられる。

## T4 — 実験カードと条件を照合したA/B比較（P1）

**Files:** 作成 `E/experiment-digest.mjs`、`E/experiment-comparison.mjs`、`E/tests/experiment-digest.test.mjs`、`E/tests/experiment-comparison.test.mjs`。変更 `E/tank-workbench-view.mjs`、`W/cli.mjs`、`L/package.json`。参照 `B/result-export.mjs`、`E/visual-comparison.mjs`。

**Interfaces:** `buildExperimentDigest({request,actionReceipts,observations,identity,window,limits}) -> ExperimentDigest`、`compareExperimentDigests({before,after,intendedDifferences}) -> ExperimentComparison`。意図した変更は具体的field/before/after値で指定し、wildcard許可をしない。

- [x] 操作受付だけ、失敗、効果未確認、記録欠損のfixtureで、既存exportのstatusを勝手にAPPLIED/PASSへ上げないテストを作成する。
- [x] 固定した期待条件と実際のaction receiptを実験カードへ接続する。metricは元tick/算出条件/証拠IDを保持し、到達は観測区間で示す。サンプルgapがある停止時間を連続停止と断言しない。
- [x] metricは指定identity/windowの照合済みcanonical証拠から計算する。`quality.coverage`と表示選択を分離し、50,000観測を超える入力は明示エラーで範囲縮小を求める。gap/identity境界をまたぐ距離を加算せず、証拠不足で判定できないassertionはINCONCLUSIVEとする。件数は保持された観測の件数であり、未記録イベントの全数とは表現しない。
- [x] 128点・32イベント・256時点をそれぞれ超えるfixtureを用い、同じ要求区間で表示点数・bookmark選択・cursor選択だけを変えても距離/件数の指標が一致することを検証する。gap、drop、50,001観測、区間の片側欠落も含め、部分集計を全区間の成功へ昇格しないことを確認する。
- [x] A/Bのbaseline/fixture/source差分/対象対応/観測項目/採取間隔/表示/整列receiptを検査する。意図しない差はNON_COMPARABLE、必要証拠なしはINCONCLUSIVE。比較可能でも自動で「改善」と判定しない。
- [x] 画像がある場合は既存`compareVisualRuns({before,after,intendedDifferences})`の判定・画像を参照する。別のpixel比較を実装しない。格子/明るさのON/OFF対照は表示診断としてラベルし、通常の外観A/Bは格子OFF・明るさ補正OFFの同条件で行う。表示差を隠して比較可能にするテスト回避は禁止。画像なしでも構造化比較の可否は独立に示す。
- [x] 新CLI `experiment-summary` / `experiment-compare`、共通HTMLへ接続。条件一致/不一致、UUID誤対応、違うtick速度、固定縮尺、可視性不足のテストと既存visual comparison/export回帰を実行してcommit。

**受入:** 「良くなったように見える」ことと、登録条件を満たすことを別欄に示せる。同じ条件の2試行から元証拠まで辿れる。表示選択は集計値を変えず、coverage不足は明示される。補正された画像だけで外観の合格を主張しない。

## T5 — 再現manifest・bookmark・次の確認候補（P2）

**Files:** 作成 `E/reproduction-manifest.mjs`、`E/experiment-guidance.mjs`、`E/tests/reproduction-manifest.test.mjs`、`E/tests/experiment-guidance.test.mjs`。変更 `E/tank-workbench-view.mjs`、`W/cli.mjs`、`L/package.json`。参照 `E/watchpoints.mjs`、`E/trigger-capture.mjs`、`B/result-export.mjs`。

**Interfaces:** `buildReproductionManifest({requestBytes,assertionsBytes,sourceBinding,worldBinding,observerProfile,comparison}) -> ReproductionManifest`、`buildExperimentGuidance({digest,health,capabilities,maxBookmarks:32}) -> {bookmarks,suggestions,budgets}`。suggestionは`{reason,evidenceRefs,proposedQuery,expectedInformation}`で、実行命令ではない。

- [x] 元request/assertion bytes/hash不一致、private path、credential、finalized出力先、存在しないpre-frame、古いownerのfixtureで不正なexport/replay準備を拒否するテストを作成する。
- [x] 元bytes/hashと既存export/CASへの参照をmanifestへまとめる。新実行には新identityとowner登録が必要であることを記録し、既存の元save復元・predecessor保全手順を参照する。
- [x] 保存済みevents/watchpointsから最大32bookmarkを生成し、取得済み画像/packetへリンクする。対象/選択/省略件数と選択規則を表示し、bookmark数をイベント総数にしない。ない過去画像を生成して補わない。
- [x] 不足に対する確認候補を、既存typed query/観測channelのallowlistから作る。優先候補は対象不一致、期限切れ、gap、Path採用記録なし。推測したAI理由や確率値を付けない。
- [x] 残時間・容量・cold/warm起動時間・反復予算と前回cleanup結果をカードへ接続。準備確認までを初版に含め、world操作の自動再実行は新規に追加しない。関連export/trigger/owner回帰成功後commit。

**受入:** 1件の実験を別セッションから読み直して、何を確認すれば再実行できるか分かる。閲覧だけではゲーム状態が変わらない。

## T6 — 格子ONの実機受入・性能確認・最終引き継ぎ

**Files:** 作成 `L/docs/KNEEKURA_TANK_WORKBENCH_ACCEPTANCE.md`。変更 `L/docs/KNEEKURA_REGISTERED_TANK_PRESENTATION.md`、`departments/minecraft/CURRENT-HANDOFF-2026-10-04.md`。証拠本体は既存のprivate保存先。

- [ ] 正式元save/複製baseline/source/build/resourceをhashで固定し、原本を保全した試行を準備する。T2で格子ONと必要観測のpreflightを確認し、画像と記録の時刻を結ぶ。
- [ ] 最小実機ケースを実施する: (a)格子ON→期限終了、(b)移動→停止/壁で停止した候補→再移動、(c)複数弾が停止しても元時刻の期限まで経路を保持、(d)A/B同条件と意図しない条件差。未取得のケースは未検証として残し、正常ケースへ読み替えない。
- [ ] 同じfixture・対象・camera条件で格子OFF/明るさ補正OFFの実画像を取得する。格子ONや補正ONとの対照で、格子による遮蔽や補正に隠れる照明差を点検する。各表示条件とidentity/tickを記録し、表示診断を通常の外観A/Bの合格根拠に混ぜない。通常A/Bは両側とも補正なしの同条件に揃える。
- [ ] 観測費用を、同一save/optionsで順序を反転した有限回数の比較として計測する。grid ON/OFF、新status通知ON/OFFをそれぞれ比較し、CPU、frame時間とserver tick処理時間のp50/p95/p99、heartbeat間隔、lane別証拠drop/status抑制数、記録量、実験準備時間、packetサイズを記録する。取得方法と計測自体の費用を明記し、heartbeat間隔をtick処理時間の代替にしない。必要な計測が取得不能ならNOT_CAPTUREDとして非劣化の受入を未完了にする。GPU readbackを通常測定へ混ぜず、GPU完了時間とは表現しない。cold outlierと観測上限も報告する。
- [ ] T1のheartbeat/drop非干渉、T2の開始直前の予算不足拒否、T4の表示選択に依存しない集計を受入記録へ結ぶ。事前登録した性能予算を超えた場合は原因を調べ、品質維持の受入を完了扱いにしない。都合の悪い試行を除外して再試行だけで合格にしない。
- [ ] 必要な関連回帰を実行する: `npm run test:motion-decision`、`npm run test:visual-evidence`、`npm run test:visual-capture`、`npm run test:result-export`、`npm run test:bridge-owner-prelaunch`、`npm run test:bridge-owner-control`、genuine Forge/runtime API。新taskのテストは各既存scriptに接続済みとする。
- [ ] 全体差分の独立レビューを最後に一度行い、指摘の必要修正は同じレビューで確認する。最終HEADの既存source CI/pytest/pinned MOD buildを確認し、Draftと引き継ぎへ成功・未取得・限界を反映する。

**受入:** 通知による既存観測への干渉、表示による見落とし、残時間不足、間引きによる集計の偏りの4項目を証拠付きで判定する。unit/CI成功だけで実機の品質維持まで検証済みとはしない。

## リリース単位と作業量

| 単位 | 内容 | 規模と依存 |
|---|---|---|
| A | T1+T2: 実状態と開始前確認 | 中。native状態通知とowner連携が主な検証対象 |
| B | T3: 同時刻の図と概要 | 中。Aのgeometry/statusを使用。保存済み証拠で大部分を検証可能 |
| C | T4: 実験カードと比較 | 中。Bの表示を再利用。比較条件と欠測の扱いが主な対象 |
| D | T5: 再現と調査支援 | 小〜中。既存export/triggerを接続 |
| 受入 | T6 | 実機起動・撮影・CI待ちで変動。時間の固定見積りは置かない |

最初の到達点はAと格子ONの実画像。そこで実際の使い勝手を確認してからBへ進む。新たな機能候補はこの初版へ無制限に追加せず、必要な根拠と別の受入条件を持つ後続項目にする。
