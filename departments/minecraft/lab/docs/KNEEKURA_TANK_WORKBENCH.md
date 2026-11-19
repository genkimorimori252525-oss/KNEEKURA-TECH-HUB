# Tank Workbench v1

TECH HUB内のLABが正本。元の正式水槽saveは保全し、実機試行はprivate複製へ限定する。単独HTML、集計、再現manifestは読み取り専用の派生成果であり、owner権限や合格を付与しない。

## 確認と表示

`node debug-workspace/cli.mjs tank-status --arena-epoch N --config CONFIG`

開始前は既存の[登録済み表示とpreflight](KNEEKURA_REGISTERED_TANK_PRESENTATION.md)を使用する。保存された状態は当時の記録。draw送信と実際に見えた画像を区別する。

`node debug-workspace/cli.mjs tank-view UUID --arena-epoch N --revision N --start-tick A --end-tick B --cursor-limit 32 --output OUTSIDE_RUN.html --config CONFIG`

図は同一UUID/revisionのcursorに連動する。対象変更は別artifactを生成する。図の縮尺は12px/ブロック固定。対象dimension不明では位置を水槽へ対応付けない。元tickとfact年齢を表示し、未来のfact、gapをまたぐ線、cursorで生成した観測点を追加しない。区間末尾概要は明示選択する。

128位置・64Pathノード・最大256cursor、入力50,000観測、共通データJSON256KiB。超過は明示エラー。表示対象/表示/省略件数は連続取得の証明ではない。位置だけから壁を生成しない。Motionと関連弾等のレイヤーは初期OFF。

## 実験カードと比較

`experiment-summary --run-dir RUN --request ORIGINAL_REQUEST --assertions ORIGINAL_ASSERTIONS --uuid UUID --revision N --arena-epoch N --start-tick A --end-tick B [--action-keys KEYS] [--context-relative SEALED_CONTEXT] --config CONFIG`

既存のfinalized inventory、request/assertion hash、canonical証拠、action journal/exportを照合する。action keysは既存形式の`[{"actionId":"...","idempotencyKey":"..."}]`。受付を効果確認へ昇格せず、既存assertionのINCONCLUSIVE/NOT_RUNを保持する。arrivalは登録済みposition-equalsの対象について、元観測間の区間だけを示す。

sealed contextがある場合、`observer`（channels/sampleIntervalTicks/tickRate）、`presentation`（grid/brightness等）、`worldBinding`（authorityHash/copyBaselineHash/fixtureHash）、`alignment`（actionReceiptHash/anchorTick）を指定できる。contextはfinalized inventory内の元ファイルに限定する。未取得値はnullのまま。宣言値だけでは実機の動作・完全なevent観測を証明しない。

alignmentは既存exportのAPPLIED receipt hashと同一run/Arenaのcanonical ACTION_APPLIED tickへ照合する。比較条件は登録actionとanchorからの相対windowであり、別runのreceipt hashや絶対tickの一致は要求しない。未取得・不一致はINCONCLUSIVE。元save/複製/fixtureの由来、実際のobserver/tickRate、区間全体のpresentationには現時点で完全なretained検証器がなく、宣言が一致してもUNVERIFIEDのまま比較を成立させない。[受入記録](KNEEKURA_TANK_WORKBENCH_ACCEPTANCE.md)に取得済み・未取得を記載する。

距離は指定区間の全ての適格canonical位置から計算する。表示点・bookmark・cursor選択に依存しない。欠測、次元、削除、テレポート、同tickの曖昧さ、距離閾値では接続しない。距離は点間和、同座標区間は保持されたサンプルの関係。全経路や連続停止、停止原因を保証しない。

`experiment-compare --before A.json --after B.json [--intended-differences EXACT.json] --config CONFIG`

条件差はNON_COMPARABLE、不足はINCONCLUSIVE。同じ登録UUID/論理subject対応を要求し、近い座標から対応を推測しない。sourceBindingだけ具体的なfield/before/after値で意図差を指定できる。wildcardや表示条件差の黙認は不可。比較可能でも「改善」やassertion合格を自動判定しない。

画像比較API`compareExperimentVisualEvidence`は既存`compareVisualRuns`へ委譲する。通常外観比較は両側grid OFF / brightness OFF。ON/OFF診断は別目的として明記する。画像なしでも構造化比較の可否を独立に報告する。

HTMLへ`--experiment DIGEST --comparison COMPARISON --guidance GUIDANCE --reproduction MANIFEST`を追加できる。同一run/Arena/対象を照合し、元run外の新規ファイルのみ出力する。

## 再現準備と次の確認

`experiment-reproduction`は`experiment-summary`と同じ入力に`[--output OUTSIDE_RUN.json]`を指定する。request/assertionの元bytesのhash、source/world/observer binding、既存CAS export参照を保持する。secret、credential、ローカル絶対パス、古いowner/leaseの再利用を拒否し、新identity・新owner・開始直前budget照合を要求する。元bytesを再serializeして同等と扱わない。閲覧で再実行しない。

`experiment-guidance --digest DIGEST --capabilities CAPABILITIES [--health HEALTH] [--bookmark-limit 32] --config CONFIG`

capabilitiesは`{"queries":["path_search","path_returned_nodes","movement_control","brain_memory_changes","terrain_ground","tank-status","tank-preflight"]}`の対応済み項目だけ。最大32bookmarkは最新の保持eventから選び、省略数を別記する。sealed inventoryと元画像hashを照合できた同tickのcaptureだけを参考画像として結び、eventの因果証拠にはしない。ないpre-frameを後から作らない。

確認候補はtyped読み取り質問と根拠参照であり、原因や確率、world操作命令ではない。残時間、容量、cold/warm起動、反復数、cleanupは未取得ならnull/UNKNOWN。記録済み残時間は開始権限にならない。

実機品質維持・性能と補正なし対照画像の受入は別途記録する。Nodeテストや単独HTMLのブラウザ確認を実機受入へ読み替えない。

反復起動の保存先と既存の検証を維持する設定は[local iterationの手順・有限性能記録](KNEEKURA_TANK_FAST_ITERATION.md)を参照する。格子OFFの比較で観察用の明るさ補正もOFFになる条件を明示し、描画補正とworld光量を混同しない。
