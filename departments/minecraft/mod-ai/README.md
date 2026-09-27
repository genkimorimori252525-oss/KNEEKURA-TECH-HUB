# Minecraft MOD AI — headless adapter

確定設計 v1.4 のうち、**取得済みローカル成果を読む基礎アダプター**を実装したもの。
設計全体の完成版ではない。現在の範囲と残工程は [IMPLEMENTATION-STATUS.md](IMPLEMENTATION-STATUS.md)。
Knowledge Core・既存DB・既存runner・既存MOD解析を変更しない。Python標準ライブラリのみを使用する。

## 実行

KNEEKURA TECH HUB のルートで Python 3.11 以上を使う。既に editable install 済みなら PYTHONPATH の設定は不要。

```powershell
# Windows / PowerShell、TECH HUB のルート
$env:PYTHONPATH = (Join-Path $PWD 'src')
python -m kneekura_tech_hub.minecraft --help
```

```sh
# Linux/macOS、TECH HUB のルート
export PYTHONPATH="$PWD/src"
python -m kneekura_tech_hub.minecraft --help
```

`profile.example.json` を**調べたいMODのルートへコピー**し、実際の版・コミット・未コミット差分hash・依存物のパスを埋める。
テンプレートの `null` は未解決であり、Forgeの版を勝手に47.4.6等へ補完しない。
rootのパスはmanifestの置き場所からの相対パス、または絶対パス。登録していない依存は解析対象ではない。
ForgeGradleが解決したJAR、sources、生成source、AT/AW、設定、リソースをそれぞれ追加する。
Parchmentは注釈用のrootとし、実行namespaceには指定しない。

```sh
python -m kneekura_tech_hub.minecraft --store /path/to/cache profile prepare --manifest /path/to/mod/kneekura-profile.json --javap /path/to/jdk/bin/javap
```

`--javap` は任意。指定した場合だけ、そのJDKのツールで `.class` を逆アセンブルする。MODのクラスを実行しない。
Minecraft用Java 17と解析ツール用JDKは別物として記録する。この実装を検証した解析JDKは21、fixtureのclass targetは17。
`profile prepare` は登録済みローカル入力のcaptureのみ。Gradleの評価、依存download、Minecraftの起動は行わない。

返された `index_snapshot_id` と `document_id` を以後の問い合わせに使う。

```sh
python -m kneekura_tech_hub.minecraft --store /path/to/cache search --index INDEX_SHA256 --query LivingEntity
python -m kneekura_tech_hub.minecraft --store /path/to/cache inspect --index INDEX_SHA256 --document DOCUMENT_ID --view source
python -m kneekura_tech_hub.minecraft --store /path/to/cache inspect --index INDEX_SHA256 --document CLASS_DOCUMENT_ID --view bytecode
python -m kneekura_tech_hub.minecraft --store /path/to/cache inspect --index INDEX_SHA256 --owner demo/Example --member attack --descriptor '(I)I'
python -m kneekura_tech_hub.minecraft --store /path/to/cache context --index INDEX_SHA256 --query pathfinding --track all
```

`INDEX_SHA256` 等はプレースホルダー。descriptorは**実際のJVM descriptor**を使う。
`official` のようなprovider固有名は `namespace_aliases` へ明示する。namespaceフィルターは名前変換ではない。
結果の `next_cursor` があれば同じindex・同じ条件で `--cursor` を渡す。更新後の別indexや別queryへは流用できない。
`inspect --owner` も `--limit` と `--cursor` でページングでき、同名classやoverloadは勝手に統合しない。
memberのreferencesは先頭100件のpreviewで、全件は `full_reference_view` のbytecodeから読める。

## データの意味

| 項目 | 意味 |
|---|---|
| `CAPTURED_NOT_RUNTIME_VERIFIED` | 登録されたローカル入力を固定した。実行classpathや実ゲームとの一致は未証明。 |
| `identity_status=UNKNOWN` | 版や入力が未解決。読めた資料は利用できるが、完全な環境固定を主張しない。 |
| `source_binary_match=UNRESOLVED` | 隣にsources JARがあってもbinaryとの一致を自動認定しない。 |
| `RESEARCH_ONLY` | 原典・派生解析の参照。canonical Claimを作成・昇格していない。 |
| `PARTIAL` | 続きのページ、未解決入力、消失したartifact等がある。coverage/evidenceを読む。 |
| `NOT_FOUND` | 宣言した検索範囲内で一致なし。意味的・動的な不在証明ではない。 |
| `AMBIGUOUS` | 複数の由来/overloadが残る。実効ロードclassを推測で選ばない。 |
| `STALE` | index/query/runの組合せが不一致。 |

検索は文字列・path検索、symbolは準備済みbytecodeのexact lookupから始める。静的参照は完全なcallgraphではない。
reflection、動的dispatch、callback、Mixin条件plugin、ロード後の変換は未解決と表示する。
通常検索ではbuildscript scopeと別trackを除外する。必要な場合だけ `--scope buildscript` や `--track all` を指定する。
既存の黄昏の森などの解析資料は `scope=research, role=analysis` のdirectory rootとして登録できる。
異なるトラックの資料はroot側でも明示する。`context` は今のところresearch用の文字列検索で、Knowledge Coreのguidance連携ではない。

## 保存・制限

source、JAR、assetsはローカルCASへ保持する。**元JARそのものも保持**し、directoryの場合は元ファイルhashのinventoryを保存する。
`profile.roots[].artifact_hash` は元JAR、元file、またはdirectory inventoryのblobへ解決する。
Python APIでは `Store(cache_path).read(hash)` / `.json(hash)` で取得できる。
CLIはdocumentの全文・bytecode・raw bytesをページで返す。要約に置き換えて元データを捨てない。

デフォルトは50,000 files、1 file 16 MiB、展開合計512 MiB、root capture 300秒、bytecode準備500 classes。
大きな対象は `Limits` または `--max-classes` を明示して調整する。超過を完全解析成功としない。
ページ上限は通常20候補、source 32 KiB（最大64 KiB）。続きはcursorで取得する。
準備済みJDK出力は入力classhashとJDK launcher/image/optionsで再利用する。読み取り操作は再生成しない。
このバージョンは自動GCを持たない。`Store.pin` は参照保持用markerを記録するが、利用者による手動削除を防止するものではない。
各プロセスのbytecode準備は逐次実行。プロセス間のjob数調整は既存実行基盤側で行う。
storeは信頼できる利用者の管理領域に置き、credentialや本番saveを入力rootに登録しない。

## 検証と観測

```sh
python -m kneekura_tech_hub.minecraft validate plan --registry /path/to/runner-registry.json --kind gametest --world /path/to/test-world
python -m kneekura_tech_hub.minecraft validate report --contract /path/to/run-contract.json --report /path/to/gametest-report.json
python -m kneekura_tech_hub.minecraft observe --contract /path/to/run-contract.json --report /path/to/observation.json
```

`validate plan` は既存runnerへ渡す計画だけを返す。workspace/test world/残り起動回数を確認するが、worldの作成・budget消費・起動はしない。
`validate run` はこのCLIにrunnerが未接続のため **UNSUPPORTED / NOT_RUN**。
Pythonの `delegate_run(plan, runner=...)` に既存の権限付きrunner adapterを接続できるが、接続先の認可・回数管理・実worldの選択はhostの責任。

reportのidentityは `verification.IDENTITY_FIELDS` を参照。profile/index/build/source/dirty/scenario/assertionのhashだけでなく、
run/epoch、world/template/seed/config、side、adapter名と版を照合する。
GameTest reportは `kind=gametest`、`completed`、`exit_code`、`detected_test_ids` / `executed_test_ids` と各count、
`tests=[{id,status,required}]` を持つ。contractの `expected_tests` が空なら成功扱いしない。
`expected_required={test_id: boolean}` を指定した場合はrequired/optionalモードの変更も拒否する。
0件、欠落、optional対象失敗、タイムアウト、別runの結果をPASSにしない。対象外の失敗は別欄に残す。

observeは**既存bridgeが出力したJSONを検査する取り込み口**であり、新しいForge観測MODやlive接続はまだない。
entityのUUID/dimension、position/velocity/health/target_uuid、server tick/log sequence区間、必要時のclient frameを検査する。
観測はatomicと呼ばず、観測JSON自体から行動assertionのPASSを作らない。
すべてのreport評価は `IMPORTED_REPORT_NOT_LIVE_ATTESTATION`。入力producerの真正性や実際のMinecraft起動を、このmoduleだけでは証明しない。

## ローカルテスト（CI不要）

```sh
python -m pytest tests/test_minecraft_storage.py tests/test_minecraft_index.py tests/test_minecraft_verification.py tests/test_minecraft_cli.py -q
```

JDKがあれば実際のJava 17 target fixtureをコンパイルして解析する。JDKなしではそのfixtureはskipされる。
このテストは実Minecraft、実MODの挙動、既存Hub全体の回帰テストの代わりではない。
