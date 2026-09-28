# Minecraft MOD AI — connected headless adapters

Minecraft 1.20.1 / Forge / Java 17を主対象とする、既存KNEEKURA TECH HUB内の解析・実行接続。
Source/bytecode、実際のForgeGradle依存物、mapping、MOD介入候補、既存Knowledge Core、検証・観測を接続する。
MODの設計・編集をする新しいAIや、別DB、別スケジューラは追加しない。

現在は接続実装と実Forgeビルド・依存解決まで検証済み。実際のMinecraft/GameTest/描画を含む全体完成は未達。
正確な実行環境・根拠・残工程は [IMPLEMENTATION-STATUS.md](IMPLEMENTATION-STATUS.md) と
[HOSTED-VERIFICATION-2026-09-28.md](HOSTED-VERIFICATION-2026-09-28.md) を参照。
従来の `verification/local-run.json` は最初の実装時の履歴であり、最新CIの結果ではない。

## 実行と信頼境界

TECH HUBルートでPython 3.11以上を使用する。editable install済みならPYTHONPATH設定は不要。

```powershell
$env:PYTHONPATH = (Join-Path $PWD 'src')
python -m kneekura_tech_hub.minecraft --help
python -m kneekura_tech_hub.minecraft --store C:/Kneekura/cache capabilities
```

Linuxでは `export PYTHONPATH="$PWD/src"`。console entryは `kneekura-minecraft`。
実行権限はユーザーが管理するregistryで明示する。MODのREADME、ログ、Issue本文から権限を取得しない。
Gradleは対象プロジェクトのコードを実行するため、registryへの登録はsandbox化を意味しない。
検索・参照はGradle、ネットワーク、逆コンパイラやMinecraftを自動実行しない。

JSONの `status` は入力/取得状態、`outcome` は検証結果、`assertion_domain` は証明範囲。
コマンドが存在すること、exit 0、観測JSONが返ったことだけでゲームの動作をPASSにしない。

## 1. 実際のMOD開発環境を取り込む

`profile discover --workspace C:/mods/reimu` はbuild設定の受動的確認だけで、依存解決はUNKNOWN。
実際の依存物は [registry.example.json](registry.example.json) にworkspace、wrapper hash、許可操作を設定して取得する。

```powershell
(Get-FileHash C:/mods/reimu/gradlew.bat -Algorithm SHA256).Hash.ToLower()
python -m kneekura_tech_hub.minecraft --store C:/Kneekura/cache profile resolve --registry C:/Kneekura/registry.json --request-id resolve-001 --physical-side server --javap C:/Java/jdk-17/bin/javap.exe
```

実際のForgeGradleで `kneekuraExportInputs` を実行し、compile/runtime別の順序付き依存物、座標、hash、
source/resource/output roots、設定とソースのfingerprint、Java toolchainを出力する。
出力は `<workspace>/build/kneekura/resolved-inputs.json`。
既存exportを読むだけなら `profile import --workspace ... --resolved ... --javap ...`。
設定や依存hashが変わったexportは拒否する。ソースだけ変わった場合も旧classを最新ソースと同一と認めない。
名前空間を解決できない他MODはUNKNOWNのまま残し、読める資料まで隠さない。

手動root登録も引き続き可能。`profile.example.json` の版・由来・scope・namespaceを埋め、
`profile prepare --manifest /path/to/profile.json` で固定する。pathはmanifest位置からの相対パスか絶対パス。
`--javap` を指定したときだけ実行用classを逆アセンブルする。ゲーム用Javaと解析JDKのidentityは別々に記録する。

## 2. ソース・bytecode・名前・介入候補

以下は `python -m kneekura_tech_hub.minecraft --store CACHE` の後へ渡す。

```text
search --index INDEX --query LivingEntity
inspect --index INDEX --document DOCUMENT_ID --view source
inspect --index INDEX --document CLASS_DOCUMENT_ID --view bytecode
inspect --index INDEX --owner demo/Example --member attack --descriptor "(I)I"
relations --index INDEX --owner demo/Example --depth 1
interventions --index INDEX --owner net/minecraft/world/entity/LivingEntity
mapping import --path mappings.tiny --format tiny
mapping lookup --mapping MAPPING_RECORD_HASH --from-namespace intermediary --to-namespace mojmap --owner CLASS --member METHOD --descriptor "()V"
```

INDEX等は返された実IDに置き換える。同名class/overloadはowner・member・JVM descriptor・由来で区別する。
`next_cursor` は同じsnapshot/条件にのみ再使用できる。previewで切った原文は捨てない。
静的referencesは完全なcallgraphではない。reflection、動的dispatch、条件付きMixin/refmap等は未解決として残る。
同じ対象に介入する候補があっても競合確定とはしない。`official` 等の別名はprofileごとに明示し、
Parchmentはparameter/Javadoc注釈であって実行namespaceではない。

Vineflower/tiny-remapperは [provider.example.json](provider.example.json) へ実在するtool/JDKとSHA-256を登録し、
明示的に `profile transform --index INDEX --root ROOT_ID --operation decompile --provider PROVIDER_JSON`。
remapには `--mapping-hash RAW_MAPPING_TEXT_HASH --from-namespace ... --to-namespace ...` も必要。
入力/出力/使用tool/classpath/mappingのhashを保持する。派生sourceは元sourceや実行時classとの一致証明ではない。
これら外部providerの実機結合はまだ未検証。プロトコルfixtureの合格を実ツール成功に置き換えない。

## 3. 知識・失敗履歴

`context --index INDEX --query ...` は原典の研究用検索。`--entity ke:... --context-json '{...}'` を付けると、
設定済みの `KTHUB_DATABASE_URL` にある既存Coreのexact guidanceを参照する。DB/provenanceが不調でも原文を返すが、
別版の知識へ黙ってfallbackしない。全文のCore説明はCAS hashから `artifact read --hash HASH` で参照する。

`knowledge stage --index INDEX --document DOCUMENT_ID --summary ... --actor-id ...` は既存Core用のレビュー候補bundleを作る。
Source/Snapshot/Evidence/NEW観測の形で、一観測一snapshotを保つ。Claim作成/昇格やDBへの自動投入はしない。

他MODのIssue→原因→修正diff→教訓を読む工程は、[Failure/Repair History](../FAILURE-REPAIR-HISTORY-v1.md) を参照。
記録・検索用の入口は次の独立submoduleで、同じCASを使う。新しいDBではない。

```text
python -m kneekura_tech_hub.minecraft.history --store CACHE import --record FAILURE-REPAIR-HISTORY.json
python -m kneekura_tech_hub.minecraft.history --store CACHE query --history HISTORY_HASH --query "target" --track ANCHOR
```

これから制作する自分たちのMODも同じ形式で記録する。原因不明、著者報告、分析者の推定、実験記録を分離する。
IssueのcloseやPRのmergeを修正確認済みにしない。検索0件は記録済み範囲内の一致なしであり、不具合が存在しない証明ではない。

## 4. 明示的ビルド・テスト・観測

```text
validate run --registry REGISTRY --kind compile --request-id build-001
validate run --registry REGISTRY --kind unit --request-id unit-001
world prepare --registry REGISTRY --template REGISTERED_TEMPLATE --request-id world-001
contract prepare --registry REGISTRY --index INDEX --world PREPARED_WORLD --scenario SCENARIO_JSON --output CONTRACT_JSON
validate run --registry REGISTRY --kind gametest --request-id test-001 --world PREPARED_WORLD --contract CONTRACT_JSON
observe --session SESSION_JSON --operation observe --query-json "{}"
```

compileの実taskは`build`。成功receiptをregistryの `build_receipt_hash` に設定し、同じsource世代のindexと組み合わせる。
userdevでは通常 `build_artifact=build/classes/java/main` を使い、reobf済みJARと開発時classを混同しない。
world prepareは登録したtemplateを `.kneekura-runs` 下へ複写し、本番worldや既存テストworldを上書きしない。
scenarioは `world_seed`（整数）、`assertion_domain`、`expected_tests`、任意の`expected_required`を持つ。
起動にはregistryで許可したkindと明示的なlaunch budgetが必要。claimされたhashではなく実artifact/receiptを照合する。
通常の `validate run` はsessionを作るため、先に同じ場所へ `session create` しない。

同一request IDの再送は再実行しない。完了不明のwriteを自動retryしない。
`validate plan` と `validate run --plan` は旧来の既存runner委譲口で、adapter未接続ならNOT_RUNのまま。
直接registry方式と混同しない。

Forge observerは開発環境で明示session指定がある場合のみ有効。127.0.0.1上で認証し、run/epoch/build/world/configを照合する。
コードは実Forge 1.20.1でコンパイル・reobfJarまで成功したが、**ゲーム起動後のhandshake/GameTest/描画はまだ未検証**。
観測はatomicな世界状態とも行動assertionの合格とも呼ばない。命令は `validate operation --session ... --command-id ... --request-id ...`
に分離し、registryの命令だけを許可する。観測ルートから命令を実行しない。

既存JSONの `validate report` / `observe --contract ... --report ...` は残るが、常にimported evidenceでありlive attestationではない。
実装上、GameTestは期待対象ID/実行件数/required flags/個別結果とrun identityを確認し、0件/欠落/optional対象失敗をPASSにしない。
対象外失敗は別欄に残す。クライアント起動だけでは描画・同期・性能が正しいという結論は出さない。

## 5. 保存・制限・テスト

元JAR、source、resources、派生物をCASへ保持する。directoryはファイルhash一覧と各原文。
`artifact read --hash HASH --view text|bytes`、Pythonの `Store.read` / `.json` で全文へ到達できる。
自動GCはなく、pinはユーザーの手動削除までは防がない。credentialや本番saveを入力rootにしない。
デフォルトcaptureは50,000 files、1 file16MiB、合計512MiB、300秒、bytecode準備500classes。
超過はPARTIALであって全解析成功ではない。調整は `Limits` / `--max-classes` で明示する。

```text
python -m pip install -e ".[dev]"
python -m pytest -q
```

全体のPostgreSQL試験は `KTHUB_TEST_DATABASE_URL` を設定する。CIはGitHub-hosted Linux/Java17/PostgreSQL16で実行する。
公開中のself-hosted実行は使っていない。CIなしでも同じPython/Gradleコマンドをローカルで使用できる。
fixtureのテスト、実Forgeビルド、実ゲームの受け入れ試験はそれぞれ別の証拠として扱う。
