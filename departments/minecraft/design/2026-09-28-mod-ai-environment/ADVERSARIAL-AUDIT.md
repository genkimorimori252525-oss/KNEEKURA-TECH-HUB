# 敵対的設計監査 — 4巡

対象: MC-AI-ENV-2026-09-28。方法: 同一assistantによる観点を切り替えた反例レビュー。独立サブエージェント・別モデル・実ゲーム実験を使用した監査ではない。

順序は初回設計1.0固定 → R1 → R2 → R3 → R4 → 最終1.4。各版は作業中に別ファイルへ保存しhashを固定した。設計上の修正完了と、実装による反例試験合格は区別する。下記「対応」は設計本文への反映を指す。

## 初回固定時に修正済みの会話案

外部機能の存在を即座にHubの実装済み能力としない。T0〜T7の一律序列は使わない。source/bytecodeを二つの絶対的真実とせず表現と変換stageを分ける。GameTestをMinecraft不要の模擬テストとしない。1.20.1を優先してもFRONTIER収集は捨てない。これらはR1以後の新発見として重複計上しない。

## R1 — identity・静的解析・由来

| ID | 反例 / 問題 | 採用した最小修正 | 設計 / 受け入れ |
|---|---|---|---|
| F01 | 同じFQCNが別JAR・scopeに存在。編集済sourceと古いbinaryも混ざる | ordered classpath、stage/origin/classloader領域、dirty identityを分離。未確定はAMBIGUOUS | §4–5 / A02,A03,A05,A06 |
| F02 | officialの意味がproviderで異なる、overloadのdescriptor内typeが未変換 | namespace別名契約とdescriptor変換。部分・複数対応を保持 | §5 / A01,A04 |
| F03 | reflectionや条件pluginをgraphから落とし、安全と断定 | 未解決とcoverageを返す。辺なしを不存在証明にしない | §5,8 / A07–A10 |
| F04 | vanilla+Forge+Connectorの結果を一つの原典と称してcoreに渡す | 原典別Evidenceまたは親一覧付き派生成果snapshot | §6 / A12,A13 |
| F05 | ページ1と2でindex世代が変わり、未完了cacheを読む | immutable IndexSnapshot、出力hash、atomic公開、snapshot固定cursor | §9 / A11 |

この巡回では汎用型解析や完全callgraphを新造せず、誤った断定が出る境界だけを定義した。

## R2 — 実行証拠・偽成功・操作

| ID | 反例 / 問題 | 採用した最小修正 | 設計 / 受け入れ |
|---|---|---|---|
| F06 | classpathを知るだけの検索で不明なGradle scriptを実行 | passive inspectと明示prepareを分離。既存許可runnerで実行 | §10 / A16,A17 |
| F07 | 再起動後のentity ID使い回し、古いbuildの画像、tickとframeの混在 | epoch/UUID/build hashと観測区間。handshakeでidentity照合 | §11 / A18,A20 |
| F08 | summon受付後に切断し、retryで二重召喚 | 受付/完了を分離、request_id、結果不明はUNKNOWN、盲目再送なし | §11 / A19 |
| F09 | GameTest exit 0だが0件実行・対象optional失敗 | 期待test集合、実行数、required設定と結果を照合 | §12 / A21 |
| F10 | helperが成功を直接作る、assertionを弱める、world残留 | 要求起点のassertion/known-bad fixture、試験world、実機枠と観測範囲の固定 | §12 / A23,A24 |

広い任意コード実行を必須化する案も、観測しか許さず試験を作れなくする案も採用しない。既存workspace権限内のscenario実行を使う。

## R3 — 使い勝手・膨張・保存

| ID | 反例 / 問題 | 採用した最小修正 | 設計 / 受け入れ |
|---|---|---|---|
| F11 | canonical承認待ちで有用な未昇格sourceを何も読めない | research表示とmaturityを分離。正規知識昇格のgateだけ維持 | §6 / A10,A12 |
| F12 | 全てcache扱いして、引用した証拠を掃除で削除。危険なarchive展開 | evidence pinとcache GCを分離。入力path/展開量の上限 | §9 / A14,A16 |
| F13 | 全classpathを毎回全量decompileし、全文を一応答へ投入 | 差分cache、重いjob一つ、結果の段階展開と続きを明示 | §9–10 / A11,A15 |
| F14 | 参考MCPを全部必須にし、IDE・新loader・多数runtimeへ依存 | headless基準、単一providerから開始、能力の未対応を正直に公開 | §13 / A01,A17 |

省略はアクセス方法の段階化であり、原文情報を捨てる処理にしない。全件解析という利用価値を保持する。

## R4 — 監査修正そのものによる劣化を点検

| ID | 再点検した反例 | 追加した狭い修正 | 設計 / 受け入れ |
|---|---|---|---|
| F15 | 一つの依存や証拠の欠損で無関係な検索結果まで全面停止 | trusted断定は止めるが、読める原典はPARTIALとして返す | §10 / A10,A14 |
| F16 | optional失敗チェック強化で、無関係な第三者test失敗まで当該taskを不合格にする | 宣言した対象testの判定と対象外結果を分離 | §12 / A21,A22 |

最終確認: U01〜U06の制作導線、A01〜A24の反例契約、ANCHOR/FRONTIER、全文可用性、既存coreの権限境界、実機枠、既存成果再利用を再照合。各ケースへの設計上の応答を記載できた。実装による合格数は0件ではなく「未実行」であり、試験未実施を失敗率・成功率へ変換しない。

## 採らなかった拡張・改悪案

| 案 | 不採用の理由 | 残す代替 |
|---|---|---|
| T0〜T7で一律の真実順位 | 問いと環境を無視した権威付けになる | 証拠type/直接性/版/再現範囲を別field |
| 全symbolのClaim化、Neo4j/巨大CPG | 再生成索引と正規知識を二重化しcore凍結にも反する | 派生索引と既存Claim経路 |
| 三つのMCPとIntelliJを全て必須 | 参考の採用が依存の急増になる | 小さなheadless adapter、任意provider |
| Frontier削除、1.20.1の情報しか集めない | 既存の技術獲得目的を劣化させる | 収集は広く、適用はprofileで分離 |
| privateなので出所不要 / 心配なので原文を捨てる | 前者は再現性、後者は解析能力を壊す | フル取得と由来を両立 |
| 毎変更で全MOD解析・全実機テスト | 実作業を遅らせ、ユーザーの検証枠も破る | 変更に関係するfixture・必要な実行層 |
| 監査のための新サービス・新承認gate | 解決する故障以上に運用を増やす | 既存adapter/manifest/runnerへの限定変更 |

## 限界と再開条件

16件の採用修正、7件の不採用案を記録。これは監査者が独立して16個の実装bugを再現したという意味ではない。再現実験、providerの全コード監査、sourceと配布JARの完全一致、Minecraft実機、性能測定は未実施。

実装時に反例が残れば、その反例と影響範囲だけを根拠に設計を更新する。理由のない追加監査・要件追加を続けず、既存の強みを残したまま停止する。

## 改訂hash

各値はUTF-8/LFのDESIGN.mdファイルのSHA-256。Git blob SHAとは異なる。

| Revision | SHA-256 |
|---|---|
| v1.0 | `666a3dbead66de30b60d6c3e60701385dd3aaaef0cd94663cbab1b02b9c2c087` |
| v1.1 | `b040fc9499440b7afbd9c8a8dca34c3c603f3fdf7f7b73c43c4a4293bb69cf21` |
| v1.2 | `5cfbf2f390e2f9f2a749c4298fe001753613c454ce128641013ad023c965bbd1` |
| v1.3 | `cbf5140410e951a044aa2abcfa71a2ecb694c644c03848aee724b6ba1995b85b` |
| v1.4 | `c1f495a44d60baf8246066334c6042569738440c302c38ce556711265dfeeca7` |
