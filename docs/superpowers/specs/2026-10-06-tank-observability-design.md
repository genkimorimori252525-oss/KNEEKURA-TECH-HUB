# 水槽の実験状況・証拠・比較を分かりやすくする改善設計

日付: 2026-10-06 JST。状態: 承認済み、実装中。T1のローカル回帰を確認し、後続と実機受入は未完了。
同日の軽量監査を反映済み。下記の品質維持条件は実装時の必須受入項目であり、現時点で非劣化を検証済みという意味ではない。
調査基準: TECH HUB `07c34216319400ddfa3d1a99f7b9970bf8857190`。将来の実装開始時に最新版との差分を確認する。

## 目的とユーザーの希望

AIと人が「どの水槽・設定・対象・時刻の証拠を見ているか」「何が分かり、何が不足しているか」を同じ根拠で理解できるようにする。通常の実機検証では格子表示ONを基本とし、性能比較ではON/OFFを実験条件に記録する。AI向けの小さな構造化データと、人向けの図・時間軸を対応させる。

今回判明した課題は、正式ワールド由来のsave、実験用に変更した領域、格子の描画状態が一括して「水槽で検証した」と説明されてしまうこと。これらを別の確認項目にする。既存の観測範囲や実機受入を、この改善計画によって取得済みに変更しない。

## 既存機能と追加範囲

以下のパスはrepository root相対。

| 確認した既存機能 | 主な実装 | 今回の追加 |
|---|---|---|
| 正式水槽の指定、元save保全、private複製 | `departments/minecraft/DEBUG-WORLD-AUTHORITY-2026-10-04.md` | 元saveの由来と実験fixtureの変更履歴を同じ確認票に表示 |
| 1ブロック格子と明るさ表示、登録・120秒以内の期限 | `lab/debug-workspace/forge-bridge/.../KneekuraDebugTankView.java`、`KneekuraDebugTankPresentation.java`（`lab/`は`departments/minecraft/lab/`） | 要求、登録、描画送信、画像確認、期限切れを区別した状態記録 |
| 実サンプルの軌跡、7段階Decision、型付き詳細 | `departments/minecraft/lab/debug-workspace/evidence/decision-presentation.mjs`、`decision-drilldown.mjs` | 同じcursor時刻の概要と証拠参照 |
| PLAN_XZ / ELEVATION / 固定isometric | `departments/minecraft/lab/debug-workspace/evidence/decision-view.mjs` | 水槽基準の固定縮尺・座標軸・方角・目的地・範囲表示 |
| 四方向画像、座標図、画像比較、結果出力 | `visual-compiler.mjs`、`visual-geometry.mjs`、`visual-comparison.mjs`、`bridge/result-export.mjs` | 同じ実験の操作・期待条件・結果・比較をまとめた索引 |
| イベント前後の有限記録、異常watchpoint | `evidence/trigger-capture.mjs`、`evidence/watchpoints.mjs` | 既存記録へのbookmark、不足証拠と次の確認候補 |

完全な3D renderer、独立した観測DB、別の画像比較エンジンは追加しない。既存の保存済み証拠と型付き操作を使う。

## 採用方針

候補は、(A)既存CLI・JSON・単独HTMLへ段階的に接続、(B)常駐Webダッシュボードを新設、(C)Minecraft内HUDへ集約。Aを採用する。現行の権限・保存・比較を再利用でき、ゲーム再起動なしで表示側を検証しやすい。Bは常駐サービスと認証の範囲が増え、CだけではAIの構造化入力を満たさない。ゲーム内では小さな状態記録だけを追加する。

## 第1段階: 実験開始前に水槽の状態を確認する（P0）

**水槽確認票**をJSONとHTMLで同じ内容から生成する。

- 正式元saveの識別hash、複製baseline hash、実験fixture hash、変更理由、使用領域のorigin/dimensions、dimensionを表示する。由来が不明なら`UNKNOWN`。元saveとfixtureが同一とは表現しない。
- session/run/snapshot/process/Arena、対象UUID/選択revision、source/build/resourceの参照を保持する。
- 格子は`requested`（希望）、`registered`（登録）、`eligible`（描画可能条件）、`drawSubmitted`（実際の描画API送信）、`pixelEvidence`（該当画像の参照）を分離する。`drawSubmitted=true`だけで「画面内に格子が見える」と判定しない。
- 未登録、recipe不一致、別server、期限切れ、古い記録を区別する。表示用記録は権限付与に使わない。
- 通常用`OBSERVE_GRID`は格子ONを要求する。性能用`BENCHMARK`は格子/明るさ/軌跡/各観測のON/OFFを明示指定する。既存の一般起動やdeep観測の既定値は変更しない。
- preflightは`READY` / `NOT_READY` / `UNKNOWN`と根拠を返す。要求した格子の新しい描画送信記録が無ければ`READY`にしない。画像による可視性は別の受入項目とする。
- `READY`には、実験・結果確定・後片付け・余裕時間の登録済み予算が元leaseの残時間内に収まることも必要とする。格子確認や撮影に費やした時間を差し引き、同じclock domainの新しいowner照合で判断する。保存済み`reportedRemainingMs`は参考値に限定し、開始直前にも再確認する。残時間の根拠が不明なら`UNKNOWN`、不足なら`NOT_READY`とし、leaseの延長・再利用で通過させない。

最初の実機受入は、正式水槽の複製に対する格子ONの確認と、前回の停止後経路線の再撮影を含める。壁への衝突は実際の状態記録と画像を採り、単に速度ゼロだったことを衝突原因の証明にしない。

## 第2段階: 図と判断を同じ時刻・座標で読む（P1）

- 新しい「cursor時点」表示で、Decision概要・実移動・関連弾・宣言経路・操作履歴を同じtick上限に揃える。既存の「区間末尾の概要」は名称を残し、切り替えられるようにする。
- 過去の記録を参照するときは元の取得tickと古さを表示する。cursor時刻に観測した事実へ書き換えない。未来のfactは表示しない。run/Arena/revisionの境界は越えない。
- PLAN_XZは水槽の範囲を基準に固定縮尺とし、X/Z軸、北（−Z）、1ブロック格子、対象の向き、取得済みの目標位置・壁・観測範囲を示す。未知の壁や目標は描かない。自動fitは明示操作にする。
- 上面図の高さ情報はラベルと既存ELEVATIONで確認する。ELEVATIONはtick対yの図として維持し、上面図と混同しない。
- 「実移動」「宣言された経路」「検索から返されたPath」「検索cache」を現行の線種・ラベルで分離する。
- 未取得、非公開、観測期限切れ、記録上限、サンプルgapを別表示にする。レイヤをOFFにしたことと、記録が無いことも分ける。

## 第3段階: 実験を単位として結果を比較する（P1）

- **実験カード**: 調べたいこと、事前に登録した期待条件、初期条件、実行した操作、実際のreceipt、観測結果、未知情報、後片付け結果をまとめる。
- 操作の予定時刻と実際の実行receiptの時刻を分離する。`ACCEPTED`だけで適用済みとせず、既存journal/exportの判定を継承する。
- **A/B比較**: 元baseline、fixture、subject対応、観測項目、サンプリング、表示、時刻整列方法、意図した変更を検査してから比較する。UUIDの対応は明示し、距離が近い個体を自動で同一視しない。
- 初期指標は観測点間の距離、実サンプル数/gap数、目標領域への到達を挟む観測tick区間、同一座標で観測された期間、攻撃/hit/hurtの件数とする。真の連続経路長、到達の厳密tick、停止理由、撃った全弾数へ拡張しない。
- 指標は要求区間の照合済みcanonical証拠から計算し、表示128点・bookmark32件・cursor256時点の選択とは独立させる。取得件数、区間内の対象件数、表示件数、省略件数、選択規則とcoverageを明示する。入力50,000件を超える区間は範囲縮小を求め、先頭だけで全区間を集計した扱いにしない。欠測・記録上限による不足は明示し、十分なcoverageを要するassertionは`INCONCLUSIVE`とする。gapやidentity境界を距離・時間の集計で接続しない。
- 外観検証には格子OFF・明るさ補正OFFの対照画像を残す。格子ONや補正ONとの対照は表示条件による遮蔽・照明差を確認する診断として扱い、通常の外観A/Bは補正なしの同じ表示条件で比較する。既存画像比較の条件照合を緩めない。
- 条件不一致は`NON_COMPARABLE`、証拠不足は`INCONCLUSIVE`とする。期待条件の合否は登録済みassertionとその証拠で扱い、単なる画像差や距離短縮を成功判定にしない。
- A/Bの図は同じ座標・縮尺・時刻基準を使用する。初版はworld座標と登録済みaction receiptを基準とし、任意の位置合わせや時間伸縮は行わない。

## 第4段階: 再現と次の調査を容易にする（P2）

- **再現用manifest**: 元request/assertionのhash、source/build/resource/fixture、対象対応、観測profile、操作列、budget、復元手順への参照を保存する。既存export/CASを使い、private pathやcredentialを公開版へ含めない。
- **再試行の準備確認**: baselineを戻せるか、必要素材と空き容量があるか、前回の所有processが終了したか、次の新しいowner登録が可能かを確認する。履歴閲覧と再実行は別操作にし、古いleaseを再利用しない。manifestだけで完全な決定論的再現を約束しない。
- **重要時点bookmark**: 停止、目標変更、projectile hit、観測終了などを最大32件選ぶ。既存trigger/記録だけを参照し、過去画像が無ければ`NOT_CAPTURED`。
- **次の確認候補**: 「選択対象が変わった」「gapがある」「Pathは返ったが採用記録が無い」など、証拠付きの不足から許可された次のquery/観測を提案する。原因断定や自動world操作にはしない。
- **運用予算**: 残り観測時間、上限到達、証拠容量、試行回数、cold/warm起動の所要時間を実験カードへ添える。初版の反復実行は明示した有限回数で行う。

## 共通契約と制約

1. TECH HUB内のLABを正本とする。正式元ワールドは保全し、実機変更は検証用複製に限定する。
2. 格子ONは通常用profileの希望であり、既存のowner照合・recipe照合・120秒以内の元leaseを迂回しない。期限切れを黙って延長しない。
3. AI向けJSONと人向け図は同じidentity/tick/evidence refsを使用する。概要はUTF-8 JSONで最大256KiB、入力観測は最大50,000件、表示位置は既存の最大128点、Pathノード最大64、bookmark最大32を維持する。
4. 追加native状態記録は既存writerへ有界にenqueueし、frameごとのdisk I/OやGPU readbackを行わない。通常は最大1Hz、状態変化を含めても最大2件/秒に抑え、抑制件数を残す。遷移の完全取得は主張しない。新status通知の送信・dropが既存heartbeatの抑制時計を更新してはならない。queue圧迫時は新statusを先に抑制し、既存観測のdropを追加で発生させない。既存laneのheartbeat規則を変えず、通知ON/OFFとqueue飽和の回帰で確認する。
5. 観測・派生・未取得・非公開を分ける。補間、未来の情報、別runの証拠を現在の観測として使わない。
6. raw/canonical証拠と既存public形式は保全する。新しいderived schema/CLIを追加し、旧artifactがそのまま読めることを確認する。finalized runへの追記を行わない。
7. 実機画像はMinecraftが生成したものを使う。格子図・注釈・重ね図は派生表示と明記する。raw撮影時のoverlay抑制規則を維持する。
8. 新しい依存関係、常駐サービス、自動uploadは初版に追加しない。性能の許容値は各実験に登録し、平均値だけでcold outlierを隠さない。CPUに加え、frame時間・server tick処理時間の分布、heartbeat間隔、証拠drop/抑制件数を通知ON/OFF・格子ON/OFFで比較する。取得方法と範囲を明記し、heartbeat間隔をtick処理時間の代替にしない。必要な計測が欠ければ非劣化は未確認とする。GPU完了時間とは表現せず、通常測定へGPU readbackを追加しない。

## 初版から外す項目

全MODの思考理由推定、全Boss branchの自動理解、汎用world reset、常時録画、3D renderer再実装、未知の衝突/目標の画像だけによる確定、GPU完了時間の新計測は別案件。必要になった項目はこの計画の達成条件へ後付けせず、別の目的と検証条件を定義する。

## 完了条件

- 同じsave由来でもfixtureや格子が違えば確認票で判別できる。
- 格子ONの複製実機で、表示開始・期限終了と停止後の経路保持を実画像/元tick付きで確認する。
- cursorより未来のDecision情報が混入せず、図・概要・詳細が同じ証拠を指す。
- 同条件A/Bは比較でき、意図しない条件差/証拠不足は明示される。
- 新status通知がheartbeatを抑制せず、queue圧迫時にも既存証拠の追加dropを起こさないことを確認する。性能の登録予算超過・必要測定の欠落があれば品質維持の受入は完了にしない。
- 格子OFF・明るさ補正OFFの対照画像で外観を確認し、表示診断と通常の外観A/Bを区別する。
- preflight後に残時間が不足した場合も開始直前の確認で拒否し、元leaseを延長しない。
- 表示点数・bookmark・cursor選択を変えても同じ証拠区間の指標は変わらず、不完全なcoverageで全区間の成功を主張しない。
- 1件の保存済み実験から概要→図→元証拠→再現manifestを辿れる。
- unit/contract、関連Forge build、代表実機、観測費用比較、最後の独立レビューと最終HEAD CIを確認する。未取得は未取得として報告する。

実装計画: [2026-10-06-tank-observability.md](../plans/2026-10-06-tank-observability.md)
