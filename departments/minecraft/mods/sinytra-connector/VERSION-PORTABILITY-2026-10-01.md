# Connector の版間移植と技術の再利用

## 判断の前提

比較対象は ANCHOR `7f68ac02291fde986119a3f5cab85436bed5c350`（1.20.1 / Forge 47.4.6 / Java 17）と FRONTIER `c84a96a3c04aa4c5253032c338434de5329be08a`（26.1.2 / NeoForge 26.1.2.95 / Java 25）。以下の移植評価はソースから導く設計判断であり、実装・ビルド・実機で確認した backport 結果ではない。

FRONTIER のファイルが短くなったことやクラスがなくなったことを、必要な機能が不要になった証拠にはしない。Launchpad や FFAPI に担当が移る場合と、Minecraft / loader API の変化で以前の修復が不要になる場合を区別する。正確な依存実装が未取得なら、その理由も確定しない。

### 共通する大きな境界

| 境界 | ANCHOR | FRONTIER | 移植への影響 |
|---|---|---|---|
| ホスト統合 | Forge ModLauncher サービス、locator、独自 Forge metadata、早期 loader hooks | NeoForge の file reader / discovery pipeline / class processor と Launchpad | パッケージ名の置換で済まず、呼び出し段階とコンテナ API を再設計する |
| 名前と access | intermediary から resolver の current namespace、SRG/Mojmap に関係する複数方向の表、AW→AT | transformer の official-name 前提、Class Tweaker、Launchpad の access service | ANCHOR の mapping/refmap 処理を残すか作り直す。新しい名前を旧版の証拠にしない |
| 変換拡張 | JarTransformInstance に並ぶ処理、MixinPatchTransformer の固定グループ | transformer subproject、ServiceLoader plugins、前後制約、別の patch priority | 概念は再利用可能。FART/ART と Adapter API の差分を吸収する別実装が必要 |
| 依存 | loader fork 2.7.15、Adapter definition/data/runtime、FFAPI 0.92.0+1.11.5+1.20.1 | loader fork 2.5.85、Adapter core/runtime、Launchpad 1.9.1+26.1.2、FFAPI 0.155.2+26.1.2+3.5.0 | バージョン数字だけでは新旧互換を決めない。正確な classpath は未確定 |

根拠: [ANCHOR の通常変換順](https://github.com/Sinytra/Connector/blob/7f68ac02291fde986119a3f5cab85436bed5c350/src/main/java/org/sinytra/connector/transformer/jar/JarTransformInstance.java#L128-L163)、[FRONTIER の通常変換構築](https://github.com/Sinytra/Connector/blob/c84a96a3c04aa4c5253032c338434de5329be08a/transformer/src/main/java/org/sinytra/connector/transformer/jar/JarTransformInstance.java)、[FRONTIER の version catalog](https://github.com/Sinytra/Connector/blob/c84a96a3c04aa4c5253032c338434de5329be08a/gradle/libs.versions.toml)、[詳細な依存の境界](DEPENDENCIES-AND-API-2026-10-01.md)。

## T01 依存の発見と実行可否を分ける

**不変の概念:** 実行しないコンテナの中にも、別の要素が必要とする依存が存在しうる。

**ANCHOR:** ConnectorLocator が入れ子 JAR を再帰的に発見して候補グラフを作り、DependencyResolver が Fabric Loader fork の resolver を呼んだ後に loadsInEnvironment で変換対象を絞る。#926→#991 の履歴は、この順序が実際に重要だったことを示す。[解決後の filter](https://github.com/Sinytra/Connector/blob/7f68ac02291fde986119a3f5cab85436bed5c350/src/main/java/org/sinytra/connector/locator/DependencyResolver.java#L52-L75)

**FRONTIER:** Launchpad の FabricJarInJarLocator が nested discovery を担当し、Connector は stub と NeoForge discovery pipeline を使う。Connector の候補選択では ID ごとに高い version、同じなら浅い nesting を優先する。これは ANCHOR の resolver 全体と同じアルゴリズムだという意味ではない。Launchpad の通常の compatible reader は ModFile 作成前に side を検査する一方、Connector の stub は nested discovery を経て後段の side filter に進むため、この二経路も区別する。[nested locator](https://github.com/Sinytra/Launchpad/blob/a1d958c952f5ffd38daa8671354e9b8fdf30f9c9/src/main/java/org/sinytra/launchpad/service/FabricJarInJarLocator.java)、[候補選択](https://github.com/Sinytra/Connector/blob/c84a96a3c04aa4c5253032c338434de5329be08a/src/main/java/org/sinytra/connector/locator/ConnectorLocator.java)

**移植判定:** 概念は使えるが、FRONTIER の nested/selection 実装の直接 backport は不可と評価。Forge 1.20.1 の locator と Fabric 候補グラフへ書き直す必要がある。解決規則・side filter・version 制約の順序が変わると、除外すべき MOD の実行や必要依存の消失を招く。namespace より loader API と graph policy が主な差分。

## T02 元の識別子を保存したホスト metadata

**不変の概念:** ホスト向けの正規化と元の artifact identity を切り離さない。

**ANCHOR:** 元の Fabric metadata を保持したまま ID を正規化し、元 ID を provides に残す。Forge の ModFileInfo は in-memory NightConfig から作る。[metadata wrapper](https://github.com/Sinytra/Connector/blob/7f68ac02291fde986119a3f5cab85436bed5c350/src/main/java/org/sinytra/connector/loader/ConnectorLoaderModMetadata.java)

**FRONTIER:** 変換後の Fabric metadata に active/Launchpad-compatible marker 等を加え、FabricModFactory へ渡す。Launchpad 側の MetadataConverter / FabricModMetadata がホスト表現を担う。[出力 metadata](https://github.com/Sinytra/Connector/blob/c84a96a3c04aa4c5253032c338434de5329be08a/transformer/src/main/java/org/sinytra/connector/transformer/transform/FabricMetadataTransformer.java)、[Launchpad metadata](https://github.com/Sinytra/Launchpad/blob/a1d958c952f5ffd38daa8671354e9b8fdf30f9c9/src/main/java/org/sinytra/launchpad/impl/MetadataConverter.java)

**移植判定:** identity/alias を保存する設計は流用可能。NeoForge の container API、marker、version conversion を Forge の TOML / ModFile 規約へ置き換える必要がある。version 条件を緩めたり alias を増やしたりしても、API・バイナリの等価性は得られない。依存として Launchpad をそのまま追加できるとは判断しない。

## T03 型と制御フローを含む契約修復

**不変の概念:** 注入先・引数・戻り値・局所変数・非対象入力の扱いを一組として変換する。

**ANCHOR:** ArmorLayer の限定した ModifyArg を HumanoidModel/String から Model/ResourceLocation の形へ適応し、guard と cast を加える。[具体例](https://github.com/Sinytra/Connector/blob/7f68ac02291fde986119a3f5cab85436bed5c350/src/main/java/org/sinytra/connector/transformer/MixinPatches.java#L586-L615)

**FRONTIER:** Adapter 2 系の MethodPatch と plugin registrar によって修復群を組み立てる。ANCHOR の防具用 descriptor/規則がそのまま存在することは主張しない。[built-in registration](https://github.com/Sinytra/Connector/blob/c84a96a3c04aa4c5253032c338434de5329be08a/transformer/src/main/java/org/sinytra/connector/transformer/plugin/BuiltinConnectorPlugin.java)、[新しい patch 定義](https://github.com/Sinytra/Connector/blob/c84a96a3c04aa4c5253032c338434de5329be08a/transformer/src/main/java/org/sinytra/connector/transformer/transform/MixinPatches.java)

**移植判定:** 旧版の Minecraft / Forge 差分を再抽出し、ANCHOR の mapping と Adapter API で規則を書き直す必要がある。新しい patch DSL の単純 copy は不適切。一致条件を広げすぎる、stack/frame を壊す、無関係な model に処理を適用する、といった意味上の危険がある。静的規則の読解だけでは実 MOD の一致と変換結果を保証しない。

## T04 同じ状態を参照する互換ビュー

**不変の概念:** 異なるデータ表現を、一つの authoritative state への限定的な view で結ぶ。

**ANCHOR:** 15 の field→getter 規則に加え、particle/color 周辺には ID と host registry key を変換する live view がある。map の全操作を実装しているわけではない。[field rules](https://github.com/Sinytra/Connector/blob/7f68ac02291fde986119a3f5cab85436bed5c350/src/main/java/org/sinytra/connector/transformer/FieldToMethodTransformer.java)、[live view](https://github.com/Sinytra/Connector/blob/7f68ac02291fde986119a3f5cab85436bed5c350/src/mod/java/org/sinytra/connector/mod/compat/fieldtypes/RedirectingInt2ObjectMap.java)

**FRONTIER:** field→getter の表は official owner+field を照合する 4 fields に変わり、Class Tweaker 側もその owner/field で filtering する。ANCHOR の live view と同一の runtime data model が残っていると推定しない。[新しい field matching](https://github.com/Sinytra/Connector/blob/c84a96a3c04aa4c5253032c338434de5329be08a/transformer/src/main/java/org/sinytra/connector/transformer/transform/FieldToMethodTransformer.java)

**移植判定:** owner を含む一致条件は ANCHOR 改善の設計候補になる。ただし intermediary/SRG/current namespace を含めた key 設計、getter descriptor、static/instance instruction の扱いを再設計する必要がある。両版とも表示上 GETSTATIC を受けても INVOKEVIRTUAL を生成する実装があるため、一般的な static field 移行の手本として無条件に転用しない。新しい field 数の少なさは全旧版問題の解消を意味しない。

## T05 初期化時機を API 契約に含める

**不変の概念:** callback が触る状態の準備・凍結・snapshot の前後関係を保存する。

**ANCHOR:** Connector の loader hooks が Fabric setup/preLaunch と main/client/server を呼び、registry / attribute adapters がその状態差を埋める。[dispatch](https://github.com/Sinytra/Connector/blob/7f68ac02291fde986119a3f5cab85436bed5c350/src/mod/java/org/sinytra/connector/mod/ConnectorLoader.java)

**FRONTIER:** Launchpad の LaunchpadMixinPlugin と EntrypointRunner、ゲーム側 mixin が entrypoint 呼び出しを担い、Connector には変換済み MOD の早期準備が残る。[preLaunch の呼び出し](https://github.com/Sinytra/Launchpad/blob/a1d958c952f5ffd38daa8671354e9b8fdf30f9c9/src/gameLibrary/java/org/sinytra/launchpad/game/LaunchpadMixinPlugin.java)、[EntrypointRunner](https://github.com/Sinytra/Launchpad/blob/a1d958c952f5ffd38daa8671354e9b8fdf30f9c9/src/gameLibrary/java/org/sinytra/launchpad/game/EntrypointRunner.java)

**移植判定:** 初期化責務を分ける設計は有用。Forge 47 の phase と NeoForge の phase を別に調べ、registry freeze/holder/attribute の前提を再構成する必要がある。二重 invocation、エラー後の半初期化、snapshot 後の登録が主な危険。Launchpad の source license も Connector の MIT とは別に確認する。

## T06 API と callback の発火点を両方供給する

**不変の概念:** 登録インターフェース、listener の保持・順序、実際の trigger を一続きで追う。

**ANCHOR:** 正確な FFAPI tag `0.92.0+1.11.5+1.20.1` の EventFactory / ArrayBackedEvent / MinecraftServerMixin を確認。END_SERVER_TICK は tick の tail で呼ばれる。[event trigger](https://github.com/Sinytra/ForgifiedFabricAPI/blob/6ba6353854d0138d5c6a0ca2a6c1eb00ab8a6a6f/fabric-lifecycle-events-v1/src/main/java/net/fabricmc/fabric/mixin/event/lifecycle/MinecraftServerMixin.java#L66-L74)

**FRONTIER:** 正確な FFAPI tag `0.155.2+26.1.2+3.5.0` でも base/lifecycle を別 snapshot として取得。LifecycleEventsImpl は Fabric ModInitializer になり、ANCHOR の FML @Mod 構築時の実装とは起動経路が異なる。[initializer](https://github.com/Sinytra/ForgifiedFabricAPI/blob/6b6e10ac2ccea496b6dfbde891be6ba50e2bfe57/fabric-lifecycle-events-v1/src/main/java/net/fabricmc/fabric/impl/event/lifecycle/LifecycleEventsImpl.java)

**移植判定:** API→実装→trigger の追跡方法はそのまま使える。新しい FFAPI JAR の direct backport は不可と評価し、1.20.1 の API descriptor とゲームの tick / lifecycle hook に実装を合わせる。順序、cancellation、side、呼び出し回数を変えると名目上同じ API でも意味が変わる。選択外の FFAPI modules は未調査。

## T07 キャッシュを変換入力の同一性に合わせる

**不変の概念:** 省略する処理の全前提と cache key / invalidation の関係を説明できるようにする。

**ANCHOR:** 実装版と physical dist、入力 hash を marker に使い、出力名には MC と naming が入る。生成 Adapter JAR は別の共有 cache で管理される。[cache](https://github.com/Sinytra/Connector/blob/7f68ac02291fde986119a3f5cab85436bed5c350/src/main/java/org/sinytra/connector/ConnectorUtil.java#L129-L158)、[版と side](https://github.com/Sinytra/Connector/blob/7f68ac02291fde986119a3f5cab85436bed5c350/src/main/java/org/sinytra/connector/locator/EmbeddedDependencies.java#L52-L60)、[共有生成物](https://github.com/Sinytra/Connector/blob/7f68ac02291fde986119a3f5cab85436bed5c350/src/main/java/org/sinytra/connector/transformer/jar/BytecodeFixerUpperFrontend.java#L63-L87)

**FRONTIER:** TransformerEnvironment が cache version を供給し、TransformerUtil が input hash と組み合わせる。キャッシュから返した TransformedFabricModPath の auditTrail は null であり、再利用結果を fresh audit と同一視できない。[cache helper](https://github.com/Sinytra/Connector/blob/c84a96a3c04aa4c5253032c338434de5329be08a/transformer/src/main/java/org/sinytra/connector/transformer/transform/TransformerUtil.java)、[cached return](https://github.com/Sinytra/Connector/blob/c84a96a3c04aa4c5253032c338434de5329be08a/transformer/src/main/java/org/sinytra/connector/transformer/jar/JarTransformer.java)

**移植判定:** key を作る責務を環境から注入する分離は再利用可能。実際に含める dependency/config/plugin/mapping 等を列挙し、旧版の生成物・cache paths と一緒に設計し直す。全依存の変更が自動で key に入るとは両版とも判断しない。これはコードから読む境界であり、cache 障害や速度改善の実測結果ではない。

## T08 前後関係のある拡張処理

**不変の概念:** 発見順に頼らず、処理の依存関係と優先度を公開する。

**ANCHOR:** 通常 JAR の transformer chain は JarTransformInstance に明示した順で構築する。Mixin patch 群には別の固定順がある。[chain](https://github.com/Sinytra/Connector/blob/7f68ac02291fde986119a3f5cab85436bed5c350/src/main/java/org/sinytra/connector/transformer/jar/JarTransformInstance.java#L128-L163)

**FRONTIER:** ServiceLoader の plugins が transformer と patches を登録する。TransformerRegistrarImpl は before/after の graph と ordering hint/name による tie-break を使い、重複した transformer 名を拒否し、存在しない任意対象を無視する。PatchRegistrarImpl は別に numeric priority の降順で並べる。[transformer order](https://github.com/Sinytra/Connector/blob/c84a96a3c04aa4c5253032c338434de5329be08a/transformer/src/main/java/org/sinytra/connector/transformer/plugin/TransformerRegistrarImpl.java)、[patch priority](https://github.com/Sinytra/Connector/blob/c84a96a3c04aa4c5253032c338434de5329be08a/transformer/src/main/java/org/sinytra/connector/transformer/plugin/PatchRegistrarImpl.java)

**移植判定:** 今回の中では汎用 plugin 基盤へ応用しやすい設計候補。Java 17 対応、FART の型、旧 Adapter DSL、service layer の classloader 制約に合わせた独立実装が必要。cycle の処理は外部 TopologicalSort の実装境界。順序が決まっても、二つの patch の意味上の競合までは解消しない。plugin ID と transformer 名の契約も区別する。

## 再利用の出発点

Forge 1.20.1 の MOD 開発へ知見を持ち帰るなら、まず対象 MOD が必要とする API、Mixin target、registry timing、resource / network 契約を列挙し、この八つの観点で差分を分類する。汎用基盤を新設する前に、どの相違が source-level adaptation で解け、どの相違が外部実装に依存しているかを一件ずつ追える状態にする。

この資料は修復や移植の自動実行を指示しない。今回の成果は、固定ソースから追跡できる技術候補と版ごとの再設計点である。実装をコピーする場合は [ライセンス来歴](DEPENDENCIES-AND-API-2026-10-01.md)の root/file-level 区別も再確認する。
