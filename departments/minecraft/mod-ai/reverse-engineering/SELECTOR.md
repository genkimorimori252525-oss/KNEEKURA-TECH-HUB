# 解析対象に応じたツール選択（常時 OFF）

この文書と `selector.py` は **逆解析を明示的に行うと決めた場合だけ** 利用する。
AIが通常のコーディングを行う際の起動条件・チェックリストではない。
`python toolkit.py choose` は計画 JSON を出すだけで、ツールの導入確認・実行・ダウンロードを行わない。
`selector.py` は標準ライブラリのみで動き、JDK、Node、MCP、IDEへの依存を増やさない。

## 実例

このディレクトリから使う。Windows PowerShellでも同様。

```text
python toolkit.py choose --input "C:/research/ysm-2.6.5.jar" --goal auto
python toolkit.py choose --input "C:/research/ysm-2.6.5.jar" --goal source
python toolkit.py choose --input "C:/research/ysm-2.6.5.jar" --goal source --signal poor-decompile
python toolkit.py choose --input "C:/research/ysm-2.6.5.jar" --goal bytecode --class-name example.a
python toolkit.py choose --input "C:/research/old.jar" --compare-to "C:/research/new.jar" --goal versions
python toolkit.py choose --input "C:/research/ysm-2.6.5.jar" --goal mapping
python toolkit.py choose --kind jar --goal auto
python selector.py inspect --input "C:/research/ysm-2.6.5.jar" --limit 100
python selector.py capabilities
```

`--kind` はファイルがまだ手元にないときの **自己申告・未検証** の計画。
実在する `--input` を指定した場合だけ、ファイル先頭のmagicとZIPのセントラルディレクトリを読み、
拡張子の偽装、JAR/APKの混同、巨大ファイル・不明形式を止める。
**クラス本体の展開、ロード、実行、難読化解除は行わない。**
最大256 MiB、100,000 ZIPエントリ、表示例300クラス。検査自体は対象への明示アクセスなので
任意の開発タスクで自動実行してはいけない。

## 選択の方針

| 目的 `--goal` | 最初の候補 | 理由・次段階 |
| --- | --- | --- |
| `auto` / `structure` とJAR | `archive-index` | 内蔵ZIPメタデータ調査（追加導入なし）。深い階層/注釈が要るときのみClassGraph |
| `source` とJAR/CLASS | Vineflower | 既存MOD-AIのCAS/profileに接続可能。読めない証拠があればCFRを別実行 |
| `source --signal poor-decompile` | CFR | 既存の逆コンパイルが問題だった場合の別解。双方の自動一括実行はしない |
| `bytecode` / `strings` | javap | 既存JDKの命令一覧・定数。JARの場合は `--class-name` が必要 |
| `calls` | SootUp（候補のみ） | Jimple、制御フロー、呼び出しグラフ。**アダプター未実装** |
| `mapping` | Enigma（候補のみ） | 証拠を付けて解析用の名前を管理。変換はMapping-IO、適用はTiny Remapper |
| `versions` + `--compare-to` | Matcher（候補のみ） | 2つの **JAR** が必要。似ていることは同一性の証明でない |
| `android` / APK | JADX（候補のみ） | Java JARではないAndroid DEXを対象とする |
| `native` / EXE・ELF | REA（別途エンジン要確認） | CLIとネイティブプロバイダーは別。ヘルプ表示≠実解析 |

`--signal` で `obfuscated-names`、`encrypted-strings`、
`invokedynamic`、`changed-versions` など **既に観測した症状** を伝えられる。
名前が短いだけで保護方式や元の名前を断定しない。
`--has-source` で実ソースがある場合、まず余計な逆コンパイルを省く
（配布JARとソースの差が判明した場合は別途調査する）。

## JSON 契約

- `decision=NO_TOOL`: 既存の証拠で足りる。何もしない。
- `decision=READY_FOR_EXPLICIT_INVOCATION`: 使うコマンド案があるだけで、ツール導入済みを意味しない。
- `decision=NEEDS_DETAIL`: 対象クラスや比較用の2つ目のJARなど、判定材料が足りない。
- `decision=ADVISORY_ONLY`: 研究候補は選定できたが、TechHubには実行アダプター・固定配布物がない。
- `decision=STOP`: 形式不明、不整合、異なるプラットフォームなど。
- `selected.integration`: `BUILTIN_READ_ONLY`, `JDK_EXPLICIT`, `EXISTING_EXPLICIT`,
  `ADVISORY_NOT_WIRED`, `RISK_REQUIRES_ISOLATION` を区別する。
- `evidence`: 分類に使った実物metadataか、`CALLER_DECLARED_UNVERIFIED`。
  `policy` は選択時に **実行・インストール・ネットワーク・元入力変更をしていない** ことを示す。

結果の `selected.suggested_argv` は引数配列であり、実行許可や実行証明ではない。
唯一の初期選択を提示し、別の道具は `next_if` に移す。
**実行が必要になったときにだけ**既存 `toolkit.py install TOOL` または
`toolkit.py decompile TOOL ... --run UNIQUE` を明示使用し、既存receiptのSHA-256と根拠を残す。

## 現在の実装境界

実装済みの直接利用経路は内蔵ZIP index、既存のCFR/Vineflower、REA CLIと、
環境側JDKに存在する場合の `javap` への**コマンド案**だけ。
ASM、ClassGraph、SootUp、Recaf、Enigma、Matcher、Mapping-IO、
Tiny Remapper、JADXは**適合性を判断する知識カタログ**であり、自動取得・自動起動できない。
ClassGraphの最新版v6はJDK25以上向けで、Forge 1.20.1のJava17解析ではv5系列の適合性を
検討する。Recaf4を動かすにはJDK22+が別途必要で、MOD側Java17の置換はしない。

ThreadtearやJava Deobfuscatorの一部の文字列復号は、対象の任意コードを
読み込み/実行しうる。**選択だけでこれらを起動・自動導入してはならない**。
実行するなら別途隔離・対象の権限・再現テストが必要。
このルーター自体はセキュリティ用のOSサンドボックスではない。

参考:
- [SootUp](https://github.com/soot-oss/SootUp)、[Matcher](https://wiki.fabricmc.net/documentation:matcher)
- [ClassGraph JDK互換性](https://github.com/classgraph/classgraph)
- [ASM](https://asm.ow2.io/)、[Enigma](https://github.com/FabricMC/Enigma)
- [Threadtearの警告](https://github.com/loerting/threadtear)

## 運用・テスト

通常作業はこのルーターを読み込まない。逆解析でも既存の原本ソース・保存済み証拠が
足りるなら `NO_TOOL` を尊重する。保護方式や名前の推定は `CONFIRMED` に昇格させず、
入力ハッシュ・元バイトコード・実機確認の対応表を残す。

この区画を**編集した場合のみ**次を実行する。

```text
python -m unittest discover -s departments/minecraft/mod-ai/reverse-engineering/tests -p "test_*.py" -v
```

CIは専用パスのみ。実CFR/Vineflower/REAスモークは手動 `real_tools=true` のみで、
SootUp/Matcherなどの未接続のツールが動いた証拠にはならない。
