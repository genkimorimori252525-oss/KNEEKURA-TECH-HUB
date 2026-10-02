# Sinytra Connector の仕組みと再利用できる技術

## 結論

Connector の核は、**Fabric MOD が前提にしている「名前・コードの形・初期化の時機」を、Forge 側の実行環境に合わせて組み直すこと**にある。Fabric JAR を発見して名前を置換するだけでなく、依存関係を選び、ホストの MOD コンテナを作り、Fabric の entrypoint を適切な段階で呼び、Forge により変わった Minecraft のコード形状を個別に補う。

これを再利用する際に重要なのは「何でも変換する仕組み」よりも、**どの差を、どの段階で、どの条件に限って吸収するかを明示する設計**である。たとえば、依存グラフの発見と side による実行可否を分ける、同じ状態を参照する変換ビューを使う、パッチの前後関係を宣言する、といった技術は他のプラグイン基盤にも応用できる。一方、Minecraft のメソッド記述子や Forge の内部クラス名を含む修復規則は、対象版ごとに作り直す必要がある。

本稿と詳細レポートは、2026-10-01 の有限な**静的解析バッチ**をまとめたもの。ソースに書かれた動作とそこから導く設計上の教訓を分ける。上流コード、Gradle wrapper、MOD JAR、ゲームは実行していない。実機試験は依頼範囲外であり、互換性・速度・描画結果・実配布バイナリとの等価性は未検証のままとする。

## 版を混ぜない

| 対象 | 固定した Connector ソース | 宣言された対象環境 | この資料の扱い |
|---|---|---|---|
| ANCHOR | [7f68ac02291fde986119a3f5cab85436bed5c350](https://github.com/Sinytra/Connector/tree/7f68ac02291fde986119a3f5cab85436bed5c350) | 1.0.0-beta.50、Minecraft 1.20.1、Forge 47.4.6、Java 17 | Forge 向けの仕組みを理解する主対象 |
| FRONTIER | [c84a96a3c04aa4c5253032c338434de5329be08a](https://github.com/Sinytra/Connector/tree/c84a96a3c04aa4c5253032c338434de5329be08a) | 3.0.0-beta.6、Minecraft 26.1.2、NeoForge 26.1.2.95、Java 25 | Launchpad 分離とプラグイン化後の比較対象 |
| 以前の COMPARATIVE | beta.49 の別証拠 | 以前の Clumps / FFAPI 静的受入れ資料に記録 | beta.50 の証拠に読み替えない |

「宣言された環境」は固定ソース内の設定を指す。配布 JAR から実際に解決された依存関係一式を証明する表ではない。[依存と来歴](DEPENDENCIES-AND-API-2026-10-01.md)に、正確な座標と未取得の境界をまとめた。

## Fabric JAR が Forge に参加するまで

以下は ANCHOR のコード経路を説明するためのモデルであり、特定の MOD を起動して観測した手順ではない。

1. **発見する。** MOD フォルダーなどから Fabric メタデータを持つ候補を調べる。通常の Forge MOD、除外対象、入れ子 JAR を区別する
2. **グラフを作って選ぶ。** 入れ子の依存を含め、Forge で既に見つかった MOD も Fabric 側の依存解決に渡す。最終的な side 判定は解決後に行う
3. **JAR を変換する。** 未更新ならキャッシュを使い、変換が必要な通常 JAR には名前変換、refmap、Mixin の修復、必要な access 変換、メタデータなどの処理を登録する。生成ライブラリは別の短絡経路を取る
4. **Forge のコンテナとして渡す。** Java module の split package を処理し、元の Fabric メタデータを保持した Forge 向け ModFile / ModFileInfo を作る
5. **Fabric 側の見え方を整える。** FML が受け入れた MOD リストを Fabric Loader fork に渡し、setup と preLaunch をホストの起動段階に組み込む
6. **Fabric の初期化を呼ぶ。** main の後、物理 side に応じて client または server entrypoint を呼ぶ。クライアント、専用サーバー、datagen では呼び出し位置が異なる
7. **起動から実行中にまたがってゲーム側の前提差を補う。** レジストリの凍結、Holder、描画データの型、HUD の挿入位置、タグ名など、Forge により変わる部分へ限定的な修復を加える

経路の根拠は [Locator](https://github.com/Sinytra/Connector/blob/7f68ac02291fde986119a3f5cab85436bed5c350/src/main/java/org/sinytra/connector/locator/ConnectorLocator.java#L92-L158)、[Fabric 側の setup](https://github.com/Sinytra/Connector/blob/7f68ac02291fde986119a3f5cab85436bed5c350/src/main/java/org/sinytra/connector/loader/ConnectorEarlyLoader.java#L90-L141)、[entrypoint の呼び出し](https://github.com/Sinytra/Connector/blob/7f68ac02291fde986119a3f5cab85436bed5c350/src/mod/java/org/sinytra/connector/mod/ConnectorLoader.java#L32-L57)。詳細は [ANCHOR のロードとゲーム側介入](ANCHOR-HOST-2026-10-01.md)を参照。

### なぜ名前変換だけでは足りないか

Fabric MOD の Mixin は、元の Minecraft にある「このメソッドの、この呼び出しの、この引数」を変更する。しかし Forge がその呼び出し自体を別の形に変えていれば、名前を正しく変換しても注入先は一致しない。

具体例が防具描画だ。ANCHOR の規則は、特定の HumanoidArmorLayer の ModifyArg(index=4) を見つけると、HumanoidModel と文字列のテクスチャを受ける呼び出しから、Forge の Model と ResourceLocation を受ける呼び出しへ変更する。さらにハンドラーを Model→Model に変え、必要な cast と instanceof 判定を加える。Forge 側が HumanoidModel 以外を渡した場合は、そのモデルを変更せず返す。[修復規則の実体](https://github.com/Sinytra/Connector/blob/7f68ac02291fde986119a3f5cab85436bed5c350/src/main/java/org/sinytra/connector/transformer/MixinPatches.java#L586-L615)

ここから得られる技術は、**メソッド名だけでなく、引数・戻り値・局所変数・制御フローまで、一つの契約として適応させる**こと。ただし、この特定規則が任意の防具 MOD に一致することも、描画が正しいことも静的宣言だけでは証明できない。

### なぜ初期化の時機も API なのか

同じ登録 API が存在しても、レジストリが凍結した後に呼べば同じ意味にならない。Connector は Fabric の初期化を早い位置に組み込み、必要なレジストリ状態や属性登録を補っている。上の第7項は最後だけに行う処理ではなく、初期化前の抑制や実行中のフックも含む。したがって、互換性を考える単位は「その関数があるか」ではなく、「その時点で対象の状態が変更可能か」まで含む。[起動時機とレジストリの詳細](ANCHOR-HOST-2026-10-01.md)

## Connector と FFAPI の役割

- **Connector** は、ホストへの参加、バイトコードと Mixin の適応、既知のゲーム側差異の修復を担当する
- **Forgified Fabric Loader** は、Connector が呼ぶ Fabric のメタデータ・依存解決・MOD 一覧・entrypoint の実装を提供する。宣言版と一致する実装ソースの対応には未確定部分が残る
- **Forgified Fabric API (FFAPI)** は、Fabric MOD が使う API と実装・フックを提供する
- **Adapter、renaming、Mixin、access 系ライブラリ** は、変換機構やパッチ適用を支える。Connector の呼び出し箇所を読めたことは、これらのアルゴリズム全体を検証したことにはならない
- **Launchpad** は FRONTIER で Fabric 規約のメタデータ、入れ子、ライフサイクル等のホスト統合を受け持つ。ANCHOR の依存ではない

たとえば ANCHOR FFAPI の END_SERVER_TICK は、登録した callback を保持・呼び出す Event 実装を持ち、MinecraftServerMixin が tick の末尾から呼び出す。「Fabric のイベントをすべて Forge EventBus に流す」と説明すると、この実装を取り違える。[イベント API](https://github.com/Sinytra/ForgifiedFabricAPI/blob/6ba6353854d0138d5c6a0ca2a6c1eb00ab8a6a6f/fabric-lifecycle-events-v1/src/main/java/net/fabricmc/fabric/api/event/lifecycle/v1/ServerTickEvents.java#L29-L45)、[実際の呼び出し箇所](https://github.com/Sinytra/ForgifiedFabricAPI/blob/6ba6353854d0138d5c6a0ca2a6c1eb00ab8a6a6f/fabric-lifecycle-events-v1/src/main/java/net/fabricmc/fabric/mixin/event/lifecycle/MinecraftServerMixin.java#L66-L74)

## 再利用できる八つの技術

以下の応用はソースと履歴から導いた設計上の推論。コード上の観察そのもの、実機で検証した移植手順、承認済みの汎用規則とは区別する。[機械可読カード](TECHNIQUE-CARDS-2026-10-01.json)には条件・機構・不変条件・失敗形・限界・固定した証拠を保持した。

| ID | 技術 | 他の仕組みへ応用する際の要点 |
|---|---|---|
| T01 | 発見と実行可否を分ける | 使わない親コンテナを早く捨てると、必要な入れ子依存まで失う。先にグラフを構築する |
| T02 | 元の識別子とホスト側の識別子を併存させる | 正規化後の ID だけを残さず、alias と元メタデータから対応を追えるようにする |
| T03 | 型と制御フローを含む契約を修復する | 精密な一致条件を設け、非対象の入力にどう振る舞うかを明示する |
| T04 | データ構造の差を live view で埋める | コピーして同期を増やすより、同じ backing state を参照する。未対応操作を隠さない |
| T05 | 初期化時機を契約に含める | callback の名前だけでなく、登録・凍結・snapshot の前後関係を追う |
| T06 | API と発火点を両方実装する | callback を登録できても、正しいゲーム段階で呼ばれなければ互換 API にならない |
| T07 | キャッシュの同一性を入力条件に合わせる | MOD 本体の hash だけで十分か、config・mapping・依存・生成物との関係を明示する |
| T08 | 拡張処理の順序を明示する | transformer の前後制約と patch priority を別の規則として扱う |

T01 には実際の修復履歴がある。#926 の早期 side 除外の後、#991 で入れ子依存が見つからない問題が報告され、後続の修復は side 判定を依存解決後に移した。作者の因果説明と、前後コードで確認できる処理順変更を区別して記録した。[失敗と修復](FAILURE-REPAIR-HISTORY.md)

T04 の map 互換ビューには未対応操作がある。T07 のキーは環境全体の fingerprint ではない。T08 の新 API は Forge 1.20.1 にそのまま持ち込めない。こうした制約まで含めて使うための [版間移植表](VERSION-PORTABILITY-2026-10-01.md)を添えた。

八枚は既存の Core staging でレビュー可能な source-backed research candidate にした。**canonical write は 0、Claim 作成は 0**。staging の成功は技術の実用上の正しさや正式採用を意味しない。[レビュー用 bundle](TECHNIQUE-REVIEW-BUNDLES-2026-10-01.json)

## 性能と互換性について言える範囲

静的に確認できるのは、キャッシュ hit が変換を省くこと、未変換 JAR ごとの並列処理、マッピング・クラス情報のキャッシュや再構築などの構造である。起動時間が何秒短縮するか、tick コストが増えるか、メモリがどれだけ必要かは測定していない。

互換性は、少なくとも候補 MOD、Minecraft とホスト版、依存関係、side、config、mapping、Mixin の一致条件に依存する。API が存在すること、変換が終了すること、ホストに列挙されること、entrypoint が呼べること、ゲーム中の挙動が正しいことは、それぞれ別の確認事項になる。ファイル数・パッチ数・CI の成功から MOD の動作率を推定しない。

## 詳細資料と残る境界

- [ANCHOR のロード・classloading・キャッシュ・ゲーム側介入](ANCHOR-HOST-2026-10-01.md) / [全対象パスの台帳](ANCHOR-HOST-2026-10-01.json)
- [ANCHOR の mapping・refmap・Mixin・AW・coremods](ANCHOR-TRANSFORM-2026-10-01.md) / [79 のパッチ宣言を含む台帳](ANCHOR-TRANSFORM-2026-10-01.json)
- [FRONTIER の処理経路・Launchpad・plugin 順序](FRONTIER-PIPELINE-2026-10-01.md) / [対象パスの台帳](FRONTIER-PIPELINE-2026-10-01.json)
- [依存・FFAPI・パッケージング・ライセンス来歴](DEPENDENCIES-AND-API-2026-10-01.md) / [分離した依存ソースの証拠](DEPENDENCY-SOURCE-EVIDENCE-2026-10-01.json)
- [版間移植表](VERSION-PORTABILITY-2026-10-01.md)、[検証記録](STATIC-BATCH-VERIFICATION-2026-10-01.json)、[独立レビュー](STATIC-BATCH-REVIEW-2026-10-01.md)

未解決なのは、正確な配布バイナリとソースの対応、実際に解決される全依存、未取得の loader / Adapter 等の実装、FFAPI の今回未選択の module、実行時の互換性・性能である。これらは「存在しない」「該当しない」ではなく、未確定の境界として保持する。有限な静的解析バッチを閉じても、全依存・全 MOD の互換性調査が完了したとはしない。
