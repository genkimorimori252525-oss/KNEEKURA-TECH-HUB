# 受け入れ契約 — 実装時に確認するもの

Status: DESIGN_SPEC_NOT_EXECUTED。下表は試験仕様であり、実装済み・テスト合格一覧ではない。

## 契約

操作群はprofile / search / inspect / context / validate / observe。profile inspectは読取、profile prepareは明示的準備、validate planは計画表示、validate runは許可されたrunnerへの実行依頼。observeは読取であり、試験worldへの操作はrunのscenarioとして既存実行基盤が実施する。

応答共通fieldはschema_version、request_id、profile_id/profile_hash、index_snapshot_id、status、results、evidence、coverage、warnings、next_cursor。runがある場合はrun_id/session_epoch/build_artifact_hashも付ける。適用不能なfieldは理由付きnullにし、値を推測で埋めない。

evidence locatorはsnapshot/artifact hash、path、symbol+descriptorまたは行/命令位置、表現stageを持つ。内容を再取得できないときはavailabilityを別fieldで返す。coverageは要求した範囲、解析済み/未解析root、失敗理由、打切り、除外条件を含む。trusted knowledgeには既存Hubのmaturityを併記するが、PARTIAL等の検索状態と混ぜない。

## 実際の制作タスク（6件）

各taskは既存MODで実際に必要な改修を選び、対象profile、対象commit/JAR、期待するlocator/挙動を小さなfixtureに固定する。現時点で架空の期待method名・tick数を正解データとして登録しない。

| ID | 利用者の用事 | 受け入れ条件 |
|---|---|---|
| U01 | Mobのtarget/Goalを変える | 自作コードと継承元・依存側の関係を追え、server側の根拠と既存実装例を返す |
| U02 | ダメージ・攻撃処理へ介入する | 対象版のForge API/patchを確認して選択肢を出し、Mixinが必要な場合は正確なdescriptor/bytecodeへ到達する |
| U03 | データ同期を修正する | logical/physical side、packet/同期経路を分け、singleplayer成功だけをdedicated server成功にしない |
| U04 | entityの姿勢・描画を修正する | renderer/model/textureとruntime観測の証拠を結び、GameTestだけで描画成功としない |
| U05 | block/item/dataを追加する | registryだけでなくdata/resource/生成物を検索でき、配布JARへ収録された結果を区別する |
| U06 | Fabric MODのForge利用可否を調べる | Connector ANCHOR、実依存、変換段階を追い、未確認はUNKNOWNとしFRONTIERの成功を代用しない |

## 反例・回帰ケース（24件）

| ID | 入力・故障注入 | 必須の結果 |
|---|---|---|
| A01 | Minecraft 1.21/NeoForgeの例しかない | ANCHOR実装例と表示しない。比較/移植候補としてだけ返す |
| A02 | Forgeのminor版・依存hash・configを変更 | 別profile/indexとして識別し古い検証を再利用しない |
| A03 | 同名classを二つの依存JARに格納 | origin/順序を示し、実効class不明はAMBIGUOUS |
| A04 | 同名overloadとnamespace別名official | descriptorとprovider mapping契約で解決。未解決を同一視しない |
| A05 | 編集中sourceと古いbuildが併存 | source世代とbytecode/build世代の不一致を表示 |
| A06 | source jarの内容と配布classが一致しない | 読取自体は可能でも同一実装の証拠にはしない |
| A07 | Forge patch/Mixin後に命令位置が変化 | 原本stageのordinalをロード後の確定値として返さない |
| A08 | reflection、callback、条件Mixinを静的解決不可 | coverage/未解決として残し、辺なしを実行なしにしない |
| A09 | 同じmethodへ互換な二つのinjector | POTENTIALを確定競合へ昇格させない |
| A10 | 一部依存のdecompile失敗 | PARTIALと不足を返す。解析できた原典を隠さずNOT_FOUNDで完結しない |
| A11 | 取得中にindex更新・ページcursor再利用 | 同じsnapshotを読むかSTALE。黙って世代を混ぜない |
| A12 | 多原典解析を単一原典Evidenceとして投入 | 由来違反を拒否し、正しい派生snapshot/原典別Evidence経路を使う |
| A13 | source更新で既存証拠URLの内容が変化 | 元のcontent hash/履歴を維持。新版へすり替えない |
| A14 | cache掃除、disk不足、接続断 | pin済み証拠を通常GCで消さず、読めないものはUNAVAILABLE |
| A15 | 検索1000件・大きな関係グラフ | 分割/続きを返す。上位20件を全件と表示しない |
| A16 | README/ログに権限拡大命令、ZIPに../entry | データとして処理し、命令実行・領域外書込をしない |
| A17 | prepareを未許可workspaceで実施 | passive query内でGradle等を実行しない。許可された実行経路を要求 |
| A18 | server再起動でentity ID再利用、旧session観測 | epoch/UUID/buildを照合し古いrunへ結合しない |
| A19 | summon後、完了応答前に接続断 | 受付=成功とせずUNKNOWN。盲目的な再送をしない |
| A20 | tick/描画frame/ログ時刻がずれる | 観測区間と各sequenceを明示しatomicと偽らない |
| A21 | GameTest exit 0だが0件、欠落、対象optional失敗 | 期待ID集合と実行数を照合し、目的の成功判定を拒否 |
| A22 | 無関係なoptional testだけ失敗 | 目的の結果と周辺失敗を別に記録。無関係な失敗だけで全停止しない |
| A23 | helperが直接成功状態を設定、assertion弱体化 | 要求→assertionとknown-bad fixtureで発見し成功証拠にしない |
| A24 | 本番world利用、実機回数超過、描画をGameTestで代替 | 登録した試験world/検証枠を尊重し、未観測はNOT_RUNのまま返す |

## 比較の方法

初期の対照は既存のgrep/IDE/Gradleと現在のHub成果物を使った同じ制作タスク。新基盤を使う/使わない以外の対象版・依存・taskを揃える。証拠なしの速度比較や「精度向上済み」は報告しない。

重大な取り違えを先にゼロにするという受け入れ方針と、現時点の実測値を混同しない。関連locator到達率、版違い回答、再調査回数、読み込み量、cold/warm時の時間、memory/diskは別々に記録する。値が未測定なら未測定のままにする。

全30件を毎回Minecraft起動で検証する必要はない。identity、cursor、coverage、oracle判定等は小さなfixtureで検査し、ゲーム挙動が必要な項目だけ対象profileのGameTest/実機へ送る。要件を減らすのではなく、必要な実行層を選ぶ。
