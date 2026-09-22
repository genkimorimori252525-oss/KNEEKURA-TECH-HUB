# Twilight Forest 描画グラフ — 実行状況と検証記録

記録日: 2026-09-23 JST。状態: **FULL_CHECKOUT_EXECUTION_PENDING**。

**FRONTIER / ANCHOR の本番描画グラフと両者の差分は、まだ生成していない。**
この記録は抽出器の確認用テスト修正と実行条件の確認であり、静的解析全体の完了報告ではない。

## 対象と再開位置

- TECH HUB: `genkimorimori252525-oss/KNEEKURA-TECH-HUB`、PR #71。
- 作業ブランチ: `jolly/minecraft-tech-department-2026-09-22`。
- 確認した開始 head: `ad9571163d1de8f929258c52cb2c8458fcbb04cd`。
- FRONTIER: `TeamTwilight/twilightforest@793c4d4c7b0a2892f702cbb9a8d751fbe7218828`。
- ANCHOR: `TeamTwilight/twilightforest@a7dd8f13c653e137f977f5ffaa870fcb20fc1625`。

既存仕様の FRONTIER 期待件数は blockstate 528、model 1,773、item definition 663、atlas 1、texture 1,159。
**これは以前の索引に基づく期待値であり、今回の全件抽出で測定した値ではない。**
ANCHOR JAR の既存照合結果も今回再検証したものではない。

## 本番実行が進まない具体的な条件

既存の GitHub Actions run `35741797862`（Twilight Forest Render Graph）は `queued`、conclusion は null。
job `106793165992`（build-graph）も queued、steps は null だった。
イベントの head は `87cb15aa8951dc9d935a36267452b05e218dec3a`。

この workflow は `[self-hosted, Windows, X64]` を要求する。
リポジトリの runner 一覧 API を再確認した結果は **total_count=0、runners=[]**。
したがって、このリポジトリで要求を満たす runner の登録が確認できず、ジョブは開始していない。
これは他の通常 test workflow の失敗原因まで確定したという意味ではない。

別途、接続された作業環境の実行ツールは安全確認で拒否されたため、再試行・迂回していない。
アシスタント側の隔離環境からの公開 upstream 取得も名前解決に失敗し、full checkout は取得できなかった。
重複ジョブの投入、runner の登録、権限変更、他プロジェクトの実行基盤への接続は行っていない。

## 今回修正したもの

既存の抽出器とテストの2ファイルだけを、GitHub の固定 head から読み取った内容で隔離環境に再現した。
編集前のバイト列は次の Git blob SHA-1 と一致した。

| ファイル | 編集前の Git blob SHA-1 |
|---|---|
| `tools/build_render_asset_graph.py` | `b18f242bc9ccad16d86da12bb6523f32ea27e066` |
| `tests/test_twilight_forest_render_asset_graph_tool.py` | `52d9d77028c620695101037e7275c555c7f812bb` |

元のテスト2件は Python 3.13.5 で両方とも失敗した。
原因はテスト用の動的 import が `sys.modules` にモジュールを登録せず、dataclass が遅延評価された型注釈を調べる段階で落ちることだった。
テスト読込時だけ登録し、終了後は元の登録状態に戻すよう修正した。抽出器の CLI 自体がこの理由で失敗したという主張ではない。

抽出器本体の変更は、生成 Markdown の source commit を囲むバッククォートの不要なエスケープを除いた1行だけ。
この不具合を検出するテストの失敗（1 failed / 2 passed）を確認してから修正した。
**描画グラフの抽出ロジックは変更していない。**

## 検証結果と限界

修正後の確認用テストは **12 passed**。構文検査も warnings-as-errors で終了コード0。
実行コマンドとファイルハッシュは `RENDER-GRAPH-EXECUTION-EVIDENCE.json` に記録した。

確認対象は、モデル・親・テクスチャ参照、欠落参照、入れ子の item definition、atlas の参照記録、重複資産、JSON破損、親モデル循環、外部参照・テクスチャ変数の区別、ハッシュ・サイズ・反復結果、5種の資産を含む CLI 出力、テスト読込の隔離、Markdown 表示。

これは **合成 fixture を使った選択ファイルの検証**であり、full checkout に対する解析ではない。
atlas のテストは参照文字列の保持を確認するもので、全 atlas の展開・解決を実証するものではない。
リポジトリ全体のテスト、workflow が指定する Python 3.12、GitHub CI 成功、Minecraft 実機動作は未検証。
レビューも同一アシスタントによる差分確認であり、独立したレビューではない。

## 次の作業

必要なのは、対象リポジトリに対して承認された、固定ソース全体を取得・実行できる環境。
まず既存の queued run を確認し、無条件に重複実行を追加しない。
現在の workflow は FRONTIER のみを処理し、TECH HUB はブランチ名で checkout するため、再開時は run のイベント SHA だけでなく実際の TECH HUB head と抽出器のハッシュも記録する。

実行環境が整ったら、FRONTIER 全件抽出、件数・ハッシュ・未解決参照・重複・破損・循環の確認、ANCHOR の同様の抽出、両トラックの描画差分、成果物の統合の順で進める。
両ソースの証拠を混同せず、未解決参照を黙って解決済みにしない。

これが済むまでは描画グラフを完了扱いにせず、Runtime Evidence に進んだとも記録しない。
今回、Minecraft 起動・性能計測・raw third-party asset の保存・main への merge は行っていない。