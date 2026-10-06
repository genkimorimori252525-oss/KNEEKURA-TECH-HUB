# 水槽の軽量MOD構成

2026-10-06。通常の水槽検証では`TANK_CORE`を使い、追加MODの互換試験では
`FULL_COMPAT`に戻す。対象MODのコード、観測、owner/lease、ソース・生成物・worldの
照合は維持する。MODを外すことは実験入力の変更であり、軽量構成の結果を外した
MODの互換性の証拠には使わない。TECH HUB内のLABが正本。

## 使用するソースとワールド

MODの固定revisionは`7f14960999bc2955d85ae9d3619090ad37817c38`
（[Draft MOD PR19](https://github.com/genkimorimori252525-oss/reimu-mod/pull/19)）。
ローカルの専用checkoutは`C:/temp/kneekura-tank-mod-profile-20261006/reimu-mod`、
branchは`codex/tank-mod-profile-20261006`。K:の旧固定checkoutと既存証拠は保全した。
Javaやresourceを編集したら通常の`runClient`/buildで再コンパイルする。
`-x compileJava`は使用しない。

正式原本は
`C:/Users/genki/.codex/worktrees/g3-real-machine-acceptance/reimu-mod/run/client_a/saves/KNEEKURA_DEBUG_WORLD`。
原本を停止状態で新規private game/savesへhash照合して複製する。今回の原本85ファイル、
2,764件の非空MCA記録、圧縮level/player dataを読み取り監査した。
registry文脈の識別子は`minecraft`/`forge`/`touhou_little_maid`のみ、保存された
WorldGenSettingsも標準3次元のみだった。他のsaveでも安全にMODを外せるという証明ではない。

## 残すMODと外すMOD

Minecraft、Forge、Touhou Little Maid/Reimu、TECHのdebug bridge、音声/YAMLライブラリを
保持する。外部MODは既存のEmbeddiumとCloth Configを残す。描画と設定UIの現在の経路を
保つためであり、新しいダウンロードは不要だった。ReimuのGeckoモデル基盤は対象MODに
内蔵されており、外部GeckoLibとは別の依存である。

レシピ表示（JEI/REI/EMI）、KubeJS/Rhino、地図、外部銃器・剣、収納・バックパック、
Curios、帽子、調理、Create/Ponder、関連する補助MODは通常のruntimeから外す。
兼用開発環境では意味のある互換用構成だが、今回の水槽スナップショットでは必須ではない。
APIはcompile-onlyとして保持し、本体全体のコンパイル対象を減らさない。
debug source setがcompile classpath経由でそれらを再ロードする経路も軽量構成で除いた。

通常ビルドと未指定のdebug起動は従来の`FULL_COMPAT`を維持する。
`TANK_CORE`はdebug mode必須で、未知の名前は起動前に拒否される。
init scriptやgame/modsに外部jarを追加すれば再びロードされるため、毎回実際の一覧を確認する。
MOD、JDK、Forgeの更新や、新しい最適化MODの導入は行っていない。

## 起動設定

[設定例](../debug-workspace/config.tank-core.example.json)は低遅延配置用の例であり、
`C:/KNEEKURA`へ自動配置済みという意味ではない。workspaceDirは上記固定revision以降の
MOD checkoutに合わせ、gameDir/runtimeRootを実際の専用配置へ変更する。
ForgeのworkingDirectoryを同じgameDirへ合わせるprivate init scriptは
[保存先の手順](KNEEKURA_TANK_FAST_ITERATION.md)を参照する。

`launch.env.KNEEKURA_DEBUG_MOD_PROFILE=TANK_CORE`が今回の構成指定。
`debugProfile=FAST_DEBUG`とは別の項目である。設定例には開始権限や過去のowner登録を
含めない。新規copy、変更したfixture、source/build/config/resource hash、実canonicalWorldRootを
新しいrequestとoperator登録へ結び直し、開始直前のbudgetを確認する。
今回のprivate runの古いowner/lease/READY記録を開始権限として再利用しない。

格子とOBSERVATION_BRIGHTは既存の登録済みpresentation機能で有効にする。
MOD削減だけでは表示権限を付与しない。明るさ補正はclient側であり、world光量や
serverの暗視効果を変更しない。通常外観の比較では補正OFFを別途記録する。

## 有限の実機起動・性能確認

native producerはTECH `d90b8d3d81b71642d1f22b1cec6e80f9ce9cfb0f`、MODは上記固定SHA。
正式85ファイルから毎回新規複製し、C:上の同じsource/build配置、options/resourcepacks、
geometry、camera、固定NoAI/NoGravity Pig、grid/brightness ONで
FULL→CORE→CORE→FULLの4試行を行った。通常のcompile taskを全試行で有効にした。
profileの切替でコンパイル入力が変わるため、ビルド費用と実行開始後の費用を分ける。

| 試行 | 構成 | launch→READY確認 (秒) | ビルド完了→READY確認 (秒) | frame p95 (ms) | server p95/max (ms) | server >50ms |
|---|---|---:|---:|---:|---|---:|
| 01 retry | FULL_COMPAT | 108.177 | 78.835 | 2.8942 | 9.4297 / 14.0512 | 0/201 |
| 02 | TANK_CORE | 56.427 | 41.797 | 1.6109 | 7.7296 / 24.0589 | 0/200 |
| 03 | TANK_CORE | 55.141 | 42.662 | 1.6249 | 10.3843 / 13.1424 | 0/200 |
| 04 | FULL_COMPAT | 93.740 | 79.210 | 3.4286 | 12.1433 / 20.8803 | 0/200 |

launch→READY確認は`launchDebugRun`開始から`readCurrent`までで、通常ビルドを含む。
ビルド完了は既存の実T1 markerのbuiltAt。READY確認にはpolling遅延を含む。
初回依存取得、cold cache、別端末の時間を保証しない。旧K: source/C: game比較と
今回のC: source/build試行を同じ条件の結果として結合しない。

計測は5秒warmup後の10秒、CPU callback wall時間でGPU完了ではない。
一回の画像読み取りとloaded MOD/霊夢metadata取得は計測窓の後に行った。
少数の固定対象による診断であり、全world/observer条件の同等性や一般的な品質PASSを
自動判定しない。COREのserver最大24.0589msはFULLの最大より高く、全指標の改善ともしない。

実ロードはFULL 44 ID、CORE 8 ID。COREの一覧は`minecraft`、`forge`、
`touhou_little_maid`、`cloth_config`、`embeddium`、`rubidium`、`mixinextras`、
`kneekura_private_tank_workbench`。最後は私用の有限計測MODで製品構成に追加しない。
`rubidium`はEmbeddiumの同じjarが宣言する互換ID、`mixinextras`は内蔵ライブラリであり、
それぞれ追加の最適化MODを別途入れたものではない。通常構成では計測IDを除く。

起動後のserver/client両方で保存UUIDのEntityReimuとEntityMaidRendererを確認した。
元の霊夢はy=64に残したため、性能4試行のPNGを水槽内の霊夢描画の証明には使わない。
水槽内のmodel fixtureは別の明示登録試行として記録する。

static classpath回帰はREDで漏出を検出した後にGREEN。既存compile APIの欠落0、
runtime artifactは153→121。未知設定、debug無効、空白正規化の確認と、
実TECH bridgeを含むgenuine compileも成功した。
[MOD exact HEAD CI](https://github.com/genkimorimori252525-oss/reimu-mod/actions/runs/37413818089)は
通常・COREのgenuine compile/classpathと拒否条件に成功。空bridgeはCIのclasspath fixtureであり、
ローカルの実bridge compileやnative受入の代用にはしていない。

## 描画対照と証拠の完了

06 CORE / 07 FULLは元の保存UUIDの霊夢をprivate copy内だけで(7.5,224,9.5)へ移し、
NoAI/NoGravity、Rotationを固定した独立のmodel fixtureである。Pigと霊夢の2個体を
明示登録し、両姿勢を含むbaseline hashを実ownerが照合した。
双方で同じcamera、EntityReimu、EntityMaidRenderer、指定位置と格子内の実モデル描画を
確認した。チャットbubble等のフレーム差があり、画素完全一致や通常外観CAS合格は主張しない。
CORE PNG SHA256は`752b1eca05a36e29a422abaa266275978200bd696dce62e5cbf72786b7d227e7`、
FULL対照は`d700066cbc1f6679e8cc9a2676416d6af6f08d7ef780c5b846bb8610122629a5`。
これらの起動時間・callback計測は上の固定Pig性能pairへ混ぜない。

成功6試行はcanonical89/88/88/93/88/87件、計533件・各9lane、全て
EVIDENCE_COMPLETE。drop/error/残queue/partialは0、clean ACKとowned exitを確認した。
PNGはpost-window derived診断で、captureManifestsは0。新CAS受入の代用にはしない。
正式原本85hash、固定MODの4,320 tracked file hash、native bridgeの155 source hashは
最終集計後も不変。fixtureは原本へ書き戻していない。

私用記録は`C:/temp/kneekura-tank-mod-profile-20261006/native`、最終集計
`summary-final.json`のSHA256は`3160437bd381d4bbdfabaf1900925595d1bf5cce42dd319751b20f9b1b511ac8`。
初回のWindows起動引数分割によるREADY前終了（01）と、追加した霊夢の登録漏れをownerが
UNCONTROLLED_ARENA_ENTITYとして拒否した試行（05）は保存し、成功集計から除いた。
前者は無権限help呼出しでUnknown optionを再現し私用引数を修正、後者は新requestへ
2個体を登録して新規copyでやり直した。製品の権限チェックを緩めていない。

COREに残るFabricBlockView/RenderAttachedBlockViewの任意mixin探索警告はFULLにも存在する。
今回のCORE起動で、除外MODの必須class欠落による新たな起動失敗は確認しなかった。
既存警告や旧保存先比較の不利な測定は削除しない。

自律AIの全状態、move→stop/wall→resume、複数停止弾、除外MODの連携、GPU完了、長時間、
全world/observer条件の同等性・一般的な非劣化受入は引き続き未確認。
今回の有限な起動・表示・観測確認を実運用全体の検証完了には読み替えない。
両成果はDraftのまま保持する。
