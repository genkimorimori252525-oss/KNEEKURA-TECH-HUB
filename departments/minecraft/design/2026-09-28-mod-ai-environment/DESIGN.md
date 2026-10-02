# Minecraft MOD制作AI環境 — 確定設計

- Decision: MC-AI-ENV-2026-09-28
- Revision: 1.4 / 敵対監査4巡反映・確定
- Status: DESIGN_ONLY。機能実装・動作検証の完了を意味しない。
- 対象: KNEEKURA-TECH-HUB / 既存 departments/minecraft の拡張。
- 優先目的: AIがMinecraft MODを調査・理解・実装・検証する際の誤りと再調査を減らす。

## 1. 維持する決定

主戦場はMinecraft 1.20.1 + Forge。新しい技術の収集は他バージョン・他ローダーにも開き、ANCHOR / FRONTIER / COMPARATIVEを分離する。MOD一覧、解析量、グラフの大きさを成功指標にしない。

既存の黄昏の森解析、Connector待ち行列、Source → SourceSnapshot → Evidence → Claim、承認・由来管理は再利用する。Knowledge Coreを作り直さず、Minecraft用の読み取り・解析・実行アダプターを外側に置く。[S01–S04]

機能範囲は、Source Intelligence、全classpath調査、source/bytecode対応、Connector互換研究、情報源・実装例の整理、Runtime Observation、GameTest、AI向け窓口で確定する。それぞれを独立した大型サービスにはしない。

## 2. 調査時点の基準と変更範囲

既存技術部: PR #71 / jolly/minecraft-tech-department-2026-09-22 / 3741e90a5762371ce7c5e372d33cf4abd7fba620。PRは未マージ。mainのライブrefは69edebfb05df2f38b44ac4cad688ac191a3d8b5aで、PR情報にあるbase_shaと区別する。

黄昏の森READMEは両トラックの描画グラフ完了、runtime性能・互換測定の残件を記載する。リソース一致はコンパイル済みclass同一性の証明ではない。今回、既存成果や進捗状態を再判定・上書きしない。[S02]

設計変更は専用の子ブランチから既存技術部ブランチへのdocs-only PRにする。main、PR #71、実装コード、既存schema、DB、runner設定を変更・マージしない。

## 3. 構造と責任

```text
MOD制作AI（Codex等）
  └─ 小さな共通窓口（CLIを基本、同じ契約をMCPへ公開可能）
       ├─ 既存Hubの根拠付き知識・既存MOD解析
       ├─ Source Intelligence / 全classpath / mappings / bytecode
       ├─ Connector研究・対象を限定した互換性調査
       └─ 既存のローカル開発workspace・実行基盤
            ├─ build / unit test / GameTest
            └─ 必要なclient起動・runtime観測
```

Hubは知識・証拠・技術転用を担当する。ソース編集、ビルド、プロセス起動は既存の制作AIと実行基盤の担当。新しい汎用エージェント、scheduler、IDE、Minecraft模擬実行エンジンは作らない。

## 4. 正確な開発環境 — ProjectProfile

各workspaceからMinecraft、Forgeの完全な版、Java toolchain、Gradle wrapper/plugin、依存解決結果、mappings、Mixin/MixinExtras、AT/AW、config、sideを読み取り、固定したprofileへ記録する。Minecraftは1.20.1、ゲーム実行JDKは17を基準とする。解析ツール用JDKは別に管理できる。[S05]

既存MODのForgeを勝手に更新しない。Connector参照commitのbuild設定はForge 47.4.6だが、これを利用者の全MODの動作保証に転用しない。新規環境の候補値と実際に解決・起動した環境を区別する。[S06]

profileが未解決ならUNKNOWNを返す。47.4.x、latestなどの範囲指定だけで実行証拠を固定しない。ローダー、物理client/server、論理side、実行・開発namespaceを区別する。FRONTIERは別profileで、黙ってANCHORの検索へ混ぜない。[S07]

profileには順序付きclasspathとscope（compile/runtime/client/server/buildscript）、config/data/resource-pack fingerprint、作業tree revisionと未commit差分hashを持たせる。buildscript用classをゲーム実行classpathへ混ぜない。編集後の未compile sourceと前回buildのclassは別世代として表示する。

## 5. Source Intelligenceと全classpath

最初は既存ForgeGradle/userdev環境と取得済み依存を使い、必要なsourceとclassを解決する。decompiler、remapper、Gradleを自作しない。既存source jarを優先できるが、配布binaryとの対応は別途記録する。[S08–S10]

検索対象はworkspace source、Minecraft、Forge、依存MOD、ライブラリ、生成source、Mixin設定、AT/AW、resources/data。全classpathとは対象profileで解決した集合であって、世の中の全MODではない。解決できない依存はcoverageに残す。

Symbolのidentityは最低限profile、artifact hash、namespace、class内部名、member名、JVM descriptorを持つ。変換stage、由来となるroot、既知のclassloader領域もidentityに含める。同名classが複数あるときはロード順を示し、実効classを断定できなければAMBIGUOUSとする。表示用名前だけでoverloadを統合しない。obf、SRG、Mojmap、intermediary、Yarnは明示的な名前空間。Parchmentは引数名・説明の注釈であり、独立した実行用namespaceとして扱わない。[S11]

providerごとにofficial/named等の別名を明示的に正規化する。mappingのdescriptor内typeも変換し、未対応・複数候補を保持する。別Minecraft版の同名methodは名前だけで同一としない。source対応状態はEXACT_BYTES / MATCHED_SYMBOLS / CANDIDATE / UNRESOLVEDのように比較対象と手段を添えて区別する。

読む表現は同じ入力由来のsource、bytecode、ASM命令列、mapping対応を並べる。逆コンパイル結果を元ソースと同一視しない。vanilla、Forge patch後、MOD変換後は別stage。元JARのbytecodeを実際のロード後bytecodeと言い換えない。

必要な関係はextends、implements、overrides、calls/references、patches、injects、transforms、remaps、depends_on。静的callgraphには動的dispatchやreflectionの未解決があることを返す。イベント登録、callback、Mixin条件plugin、reflection等の未解決も列挙し、辺がないことを実行されない証明にしない。全プログラム解析完成を利用開始条件にしない。

## 6. データと知識の二層

大量のsymbol、全文索引、関係エッジは再生成可能な解析データ。既存Hubのcanonical Knowledge Entity / Claimと混ぜない。graph DBや第2の正規知識DBは作らない。

技術説明、移植判断、互換性判断を保存するときだけ、既存のstaged observationとEvidence経路へ接続する。AIが検証済み知識へ自動昇格する経路は増やさない。複数artifactを用いた分析はそれぞれの由来を保持し、単一の原典を偽装しない。[S01,S04]

各Evidenceは一つのSourceSnapshotを指す。複数原典を合成した解析は、親snapshot群とtool/optionsを記載した派生成果manifestを一つの解析成果snapshotとして固定するか、原典ごとのEvidenceをClaimへ関連付ける。異なる原典の断片を同じ原典と称してstagingへ渡さない。canonical書き込みは既存adapterの制約を満たす場合だけ行う。

検索はexact symbol・namespace解決と全文検索から開始し、必要な関係だけ展開する。既存のcontext guidanceを利用し、全文検索順位と主張の信頼性を区別する。Vector DB、巨大embedding、Neo4j、独自CPGは初期範囲外。

未昇格の解析や実装例もresearch表示で利用できる。canonical validation未了を理由に全文調査を禁止せず、Candidateと検証済みをラベルで分ける。候補sourceの発見・整理はAIが進められるが、人間の判断が必要な既存coreの操作を別経路で迂回しない。

## 7. 情報源の利用

一律のT0〜T7順位は採用しない。問い、版、環境、直接性、再現条件、出所を別々に扱う。methodの存在は対象class、推奨使用法は対象版のmaintainer資料、クラッシュ事例はその環境のログと修正履歴に当たる。

採用する情報源群は、対象版のForge Docs、Forge Forumの事例、Minecraft/Forge/他MODのコード、GitHub Issue/PR/commit/release、Parchment、Mixin/MixinExtras、Connector研究用Fabric資料、McJty等の対応コード付き実装例。[S05–S14]

Redditは困りごと・候補sourceの発見に使い、投稿の賛同数や評判を設計根拠にしない。今回再取得できなかった過去紹介スレは検証済み情報へ昇格しない。Discord自動取り込み、全動画解析、大量サイト巡回は追加しない。Modrinth/CurseForgeは版・loader・依存と原典URLを探す入口とする。

Example/Failure記録は、課題、完全な環境、元コードlocator、説明、必要依存、制約、観測結果、未確認点を持つ。修正PRの存在だけで修正済み・当該releaseへ収録済み・再現成功とは断定しない。コピーされた同じ話を独立した複数証拠と数えない。

## 8. Connector研究

既存mods/sinytra-connectorを唯一の作業場所とし、黄昏の森の次というキューを維持する。参考原典は https://github.com/Sinytra/Connector 。ANCHOR参照commitは7f68ac02291fde986119a3f5cab85436bed5c350で、build設定のConnectorは1.0.0-beta.50。これは配布JARのhashや全機能解析完了を意味しない。[S03,S06]

調べる経路は検出・metadata・nested JAR・依存解決 → loader/entrypoint → remapping → bytecode/Mixin/AT/AW → Fabric API bridge → classloading/cache → 制約・失敗・1.20.1転用。

ForgifiedFabricAPIとConnectorExtrasなど必要な依存は別snapshotへ固定する。Launchpad等の新しい系列を1.20.1の必須依存と推測しない。FRONTIERは実行時の最新有用版を改めて固定し、差分だけ別記する。

互換性回答はSUPPORTED_IN_OBSERVED_SCOPE / POTENTIAL_CONFLICT / UNKNOWN / REPRODUCED_FAILUREなど環境付きの表現にする。同じmethodへのMixinが二つあるだけで競合確定としない。注入点、順序、条件、変換stageを根拠にし、未検査の組合せを安全保証しない。[S12]

## 9. 保存とアクセス

ローカルの管理領域には必要なfull source、JAR、逆コンパイル、assetsを保持し、全文へ到達できるようにする。品質を落とすための強制要約・抜粋制限は設けない。Gitには設計、manifest、由来、必要な小さな索引、解析・差分・証拠を残す。巨大な再生成ファイルの毎回commitは避ける。

privateという可視性だけで取得条件を消去しないが、承認済み範囲の読み取りに毎回人間承認を追加しない。既存の取得・保存方針を再利用し、公開・再配布の工程を解析工程と分ける。ここでは法的適否を包括保証しない。

blobはcontent-addressed、索引は入力hashとtool/optionsで区別する。出力hashも記録し、索引はimmutable IndexSnapshot単位でatomicに切り替える。検索・詳細・ページcursorは同じsnapshotへ固定し、更新後の別世代へ黙って継続しない。未完了生成物を成功cacheとして公開しない。sourceの場所を示すだけでなく、制作AIがreadできるresolverを用意する。クラウドAIからローカルへ接続できない場合はARTIFACT_UNAVAILABLEを返し、読めたふりをしない。

cacheと証拠保存を分ける。Claim/RunManifestが参照する証拠blobはpinして保持し、再生成cacheの容量回収で消さない。削除・破損・失効が起きた場合はavailabilityを別途記録し、既存の内容hashや履歴を書き換えない。正規化した相対path、entry数・展開量・処理時間の上限でJAR/ZIPや外部成果の取り込みを扱い、path traversalや展開爆弾を受け入れない。

## 10. AI向け窓口

初期の操作群をprofile、search、inspect、context、validate、observeにまとめる。CLIを基準にMCPは同じ契約の薄い入口とする。実行は既存runnerへ委譲する。

共通返却はrequest/profile/snapshot identity、結果、evidence locator、coverage、warnings、続きのlocator。小さな要約から必要な全文・bytecodeへ段階的に読む。上限到達を隠さず、未解決をnot foundと混同しない。statusはOK / PARTIAL / NOT_FOUND / AMBIGUOUS / STALE / ARTIFACT_UNAVAILABLE / UNSUPPORTED / ERRORを区別し、証拠の成熟度とは別fieldにする。壊れた由来を信頼済み回答に使わない一方、無関係な一部欠損で読める原典まで全停止しない。partial結果の対象範囲と不足を明記する。NOT_FOUNDは宣言した検索範囲が完了した場合だけに用いる。読み取りが勝手にbuild・起動・再取得・新しいprofileへの更新を始めない。

profile inspectは保存済みmanifest等を読むだけ。profile prepareが取得・依存解決・decompile/indexの明示的入口で、実行を伴うGradle評価は既存の許可されたrunnerで行う。repositoryの文書・コメント・ログはデータとして扱い、そこに書かれた命令から権限拡大やshell実行をしない。trusted workspace以外のbuild scriptを検索処理内で実行しない。

contextには関連実装、対象版のAPI、介入点候補、既知の失敗、必要な検証を返す。モデルに全リポを一括投入しない。履歴を丸ごと注入するより、質問に必要な範囲とその原典を返す。

初期値は1応答20候補・64 KiB・関係探索深度2を目安にし、利用側で変更できる。上限は情報破棄ではなく、ページとartifact locatorへの分割条件である。巨大依存の解析は重いjobを同時に一つまでとし、decompiler内部のthread数はproviderの適正値を使う。冷cacheと温cacheを区別し、差分入力だけ再計算する。OOM・失敗を無限再試行しない。

## 11. Runtime Observation

既存ローカル実行環境へ小さなForge 1.20.1観測adapterを接続する。外部DebugBridgeは設計参考であり、当該環境での採用・互換性検証済みとはしない。[S10]

初期観測はentityの位置/速度/target/health、近傍block、tick、ログ、必要時の画面。entity挙動はserver側、描画はclient側で取得する。run/profile/build identityを添え、古いrunの観測を新buildの結果へ流用しない。

RunManifestはrun_id、session epoch、profile/index identity、実際に配備されたJARのhash、source/build/dirty identity、scenario/assertionのhash、world/seed/dimension/config、観測adapter版を持つ。起動直前と接続handshakeで照合する。entity識別はsession+dimension+UUIDを基本とし、一時entity IDの使い回しを同一個体とみなさない。server tick、client frame、ログsequence、観測区間を記録し、非同時観測をatomic snapshotと呼ばない。

操作は登録済み開発workspaceと試験用worldに限定し、観測と状態変更を分ける。任意Groovy実行を標準機能にしない。既存の権限を尊重した範囲で検証用コマンドを許可する。endpointを公開ネットワークへ勝手に露出しない。

loopback接続にもsession識別・認証を付け、通信権限と操作対象profileを照合する。状態変更にはrequest_idと実行結果を記録し、受付と完了を分ける。切断・crashで結果不明ならUNKNOWNのまま保留し、summon等を盲目的に再送しない。再接続はsession epochを照合する。

## 12. 検証の段階

1. schema・静的検査・純粋なunit test。
2. 対象profileでのcompileとpackaging。
3. server挙動が必要なときのGameTest。
4. 描画、同期、client起動、実MOD組合せが必要なときの実機観測。

GameTestは実際のMinecraftを動かす。headlessであっても模擬エンジンではなく、描画の正しさを証明しない。compile成功を動作成功としない。[S13]

ユーザーが指定する実機検証の時点・回数を尊重する。自動client連続起動を必須化しない。環境未準備・検証省略を成功へ丸めず、NOT_RUN/BLOCKED/FAIL/PASSを区別する。既存テストを弱めて通す変更は許容しない。

GameTestの成功判定はexit codeだけに依存しない。期待したtest ID集合、検出/実行数、required/optional設定、個別結果、同じrunの終了記録を照合する。0件実行、未実行、欠落、宣言した対象testに含まれるoptional失敗、タイムアウトを目的の成功へ丸めない。対象外testの失敗は別欄に記録し、無関係な失敗だけで目的の検証を自動失敗にしない。[S13]

試験用worldはtemplateから再作成し、seedだけで再現性を保証しない。乱数、tick順、config、負荷の差と再現範囲を記す。利用者の本番saveを自動で流用・削除しない。実機回数を使い切った場合は残項目をNOT_RUNとして報告し、無断追加起動しない。

要求から導いたassertionと既知の失敗fixtureを先に固定する。AIが実装に合わせて期待値を弱める変更は別差分として説明する。単にhelperがtargetを直接セットしたことをAI挙動の成功証明にしない。描画・ネット同期・性能はそれぞれ専用の観測範囲を持ち、GameTestや観測adapterありの成功を未観測の製品環境へ拡張しない。

## 13. 外部実装からの採用境界

MCDxAI/minecraft-dev-mcpから取得・remap・MOD解析・全文検索、MixinMCPから全classpath・参照・bytecode、mcdev-mcp/DebugBridgeからrun観測の発想を取り込む。[S08–S10]

外部READMEの機能説明はauthor claimであり、当Hubの検証済み実装ではない。最初に一つのproviderを既存データと1.20.1 Forgeで試し、契約を満たすものを使う。三つ全部を必須依存にしない。IntelliJ必須、最新MixinExtras必須、任意コード実行必須という設計は採らない。

標準経路は既存workspaceのsource/生成成果/JARを読む小さなheadless adapter。providerがprofile・namespace・stage・coverageを返せない機能は、情報を捏造して埋めずcapabilityをUNSUPPORTEDとして宣言する。providerごとにsupport matrix（入力環境、機能、参照版、未実行/実測）を記録する。IDE連携や外部MCPは任意の差し替え先であり、それらの全機能を再実装しない。

## 14. 実装のまとまりと停止条件

A: profile・既存成果の利用・source/bytecode/全文検索を接続し、一つの実MOD改修で使う。
B: Connector研究、介入点・実装例・失敗例をその検索へ接続する。
C: 対象改修のbuild/GameTest/必要なruntime観測を既存実行基盤へ接続する。

これは実装の順序であり、この文書保存によって実装着手を意味しない。詳細な実装計画は実際のworkspaceを確認してから既存コードに合わせる。

受け入れでは、正しい対象版のsymbol/根拠へ到達できること、依存側の介入候補を見落としたときにcoverageが分かること、同一buildの検証結果を戻せること、既存の由来・権限境界を壊さないことを確認する。

まず実際のMOD制作ループが一巡したら機能追加を止める。以後は再現した失敗か、既存経路では遂行できない必要タスクだけを根拠に再開する。監査のためだけに新サービス・新DB・新しい承認儀式を増やさない。

受け入れ仕様は[ACCEPTANCE.md](ACCEPTANCE.md)、根拠・参考の状態は[SOURCES.md](SOURCES.md)、反例と採否は[ADVERSARIAL-AUDIT.md](ADVERSARIAL-AUDIT.md)に分離する。これらはテスト結果ではない。実装の評価は同じ対象task/profile/buildで、版違い回答、根拠なし断定、未実行の成功扱いがないことを先に確認し、その上で関連コード到達率、再調査回数、読む量、冷温cacheの待ち時間・memory/diskを比較する。総合点一つに潰さない。

## 15. 設計確定の意味と未実装境界

この確定は合意した製品範囲・責任・契約を固定するもの。Source Intelligenceの接続、Connector全件解析、新観測adapter、GameTest配線、provider適合試験を実施済みとはしない。source/binary/実行の同一性が未確認な箇所は未確認のまま実装時の受け入れに渡す。

監査は同一assistantが観点を切り替えて行った反例ベースの設計レビューで、独立agent・別モデル監査ではない。実コードの動作保証や脆弱性不存在証明でもない。今回の変更は設計資料と案内リンクだけであり、既存研究成果、canonical core、実行権限の意味は変えない。
