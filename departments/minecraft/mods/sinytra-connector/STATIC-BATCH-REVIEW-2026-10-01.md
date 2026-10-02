# Connector 静的技術解析のレビュー記録

## 対象と判定の意味

対象は、固定した ANCHOR / FRONTIER Connector ソース、選択した FFAPI base/lifecycle、Launchpad、およびそれらから作成した技術解説・変換経路・版間移植・八枚の技術候補である。レビューはソースの実体、証拠の所在、説明の意味、対象範囲の一致を確認する。実配布バイナリとの対応、ゲーム実行、互換性、性能を認定するものではない。

有限な静的解析範囲の独立レビューは、記録した修正を取り込んだうえで完了した。外部依存の全実装と source-binary equivalence は未確定、実行時互換性は UNKNOWN のまま。既存の PARTIAL capture 状態を完了状態へ書き換えていない。

## ANCHOR で独立に確認した事項

- ANCHOR 141 ファイルと追加依存 197 ファイルの size / Git-blob SHA-1 / SHA-256 を再計算し、取得台帳と一致
- host 範囲 87 パス、transformer/coremod 範囲 28 パスを台帳から独立に再構成し、欠落・余分なパスなし。後者の支援ファイルは別に 8 パス
- MixinPatches の builder 宣言 79 件と開始行を対応づけた。宣言件数と実適用件数は区別
- lifecycle、通常の変換順、cache/generated-library の分岐、AW/AT、refmap、field、coremods、防具の型・制御フロー修復を追跡
- registry/HUD/network/render/tag/recipebook の介入を限定した契約として検証し、万能なイベント・通信・コレクション互換性とは扱っていない
- FFAPI の END_SERVER_TICK は API→ArrayBackedEvent→MinecraftServerMixin の発火点まで対応づけた
- 選択した技術候補の証拠と八つの bundle、46 records を確認。bundle hash と CAS が一致し、既存 Core の preflight を通過。Claim 作成と canonical write は 0

## 修正した説明

### 開発 classpath の発見条件

mods ディレクトリと追加ディレクトリに適用する `.jar` / 除外位置の predicate を、開発 classpath へ一律に当てはめていた説明を修正した。scanClasspath は legacyClassPath の既存 claim、存在、非ディレクトリ、Fabric metadata を検査する独立の経路である。[発見処理](https://github.com/Sinytra/Connector/blob/7f68ac02291fde986119a3f5cab85436bed5c350/src/main/java/org/sinytra/connector/locator/ConnectorLocator.java#L161-L208)

### metadata の前処理と Mixin compatibility の組み合わせ

getMixinCompat 単体には loader dependency の interval に基づく分岐がある。しかし通常の変換経路では先に metadata の constraints が加工される。早い alias 条件に一致しない標準 `fabricloader` edge は削除され、それしか loader 条件がなければ compatibility の既定値 0.10.0 に進む。`fabric-loader` や先行 alias 処理から残る条件は区別した。これはコード経路から導く説明であり、実行時の失敗を観測したという意味ではない。[前処理](https://github.com/Sinytra/Connector/blob/7f68ac02291fde986119a3f5cab85436bed5c350/src/main/java/org/sinytra/connector/transformer/jar/JarTransformer.java#L177-L184)、[alias 優先順位](https://github.com/Sinytra/Connector/blob/7f68ac02291fde986119a3f5cab85436bed5c350/src/main/java/org/sinytra/connector/locator/DependencyResolver.java#L81-L100)、[compatibility 判定](https://github.com/Sinytra/Connector/blob/7f68ac02291fde986119a3f5cab85436bed5c350/src/main/java/org/sinytra/connector/service/FabricMixinBootstrap.java#L103-L142)

### 引用と説明順

cache key の引用を、キー構成が実際に書かれた行へ修正した。日本語の経路説明では、registry 等の介入が起動前後にまたがることを明記し、entrypoint 後だけの最終処理に見えないようにした。FRONTIER の preLaunch 呼び出しは LaunchpadMixinPlugin に結びつけ、enum extension を設定する EnvironmentSetup と区別した。

## FRONTIER レビュー

FRONTIER の完成版について、pipeline/plugin order、名前変換段階の有無、Launchpad の metadata/nested/side/lifecycle 境界、cache と safeguard、runtime の限定的な介入を独立に照合し、静的範囲で PASS と判定した。131 ファイルの hash と、完成版および日本語 synthesis の 133 件の source URL paths/line ranges も不一致なく確認した。取得台帳と意味解析の深さの区別は companion JSON に保持する。

レビューで特定した二点は、完成版へ修正し、再確認した。

- ConnectorPrelaunch.version は safeguard の trigger → pending cache marker の finalize → initialized=true の順。有効な safeguard が例外を投げた場合、後二者には到達しない。cache hit に fresh audit がないこととは別の事実である。[正しい順序](https://github.com/Sinytra/Connector/blob/c84a96a3c04aa4c5253032c338434de5329be08a/src/main/java/org/sinytra/connector/service/ConnectorPrelaunch.java#L19-L24)
- Locator は生成した ModFile を pipeline に渡すが、addModFile の boolean を検査していない。stub の削除を「全 MOD のホスト受入れ成功が確認された後」と説明しない。[結果の受け渡し](https://github.com/Sinytra/Connector/blob/c84a96a3c04aa4c5253032c338434de5329be08a/src/main/java/org/sinytra/connector/locator/ConnectorLocator.java#L70-L94)

## 公開用ファイルと repository 検証

[統合検証 JSON](STATIC-BATCH-VERIFICATION-2026-10-01.json)に、公開ファイルの hash、再確認した source paths/line ranges、相対リンク、有限範囲と残る境界を保持する。上流 raw source、JAR、個人のパス、credential、raw logs は公開対象にしない。

既存 repository のローカル full suite は **3,039 passed / 433 skipped / 1 failed**。失敗は以前から記録された sandbox 環境の `test_private_parent_validation_allows_real_external_directory` で、Git ancestor の検出により guard が拒否する。guard を弱める変更は行っていない。documentation contract は **3 passed**。この suite は TECH HUB の回帰確認であり、Connector の実機互換性試験ではない。

公開 commit に対応する hosted CI は [既存 Draft PR74](https://github.com/genkimorimori252525-oss/KNEEKURA-TECH-HUB/pull/74) の正確な head に対して別途確認する。この静的検証記録の数値で、後から実行される CI の結果を代用しない。merge、deploy、上流 build/game 実行は今回の作業に含めない。
