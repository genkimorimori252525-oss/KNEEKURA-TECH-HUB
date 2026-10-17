# 逆解析専用区画 — CFR / Vineflower / REA

**必要なタスクだけ使う、常時OFFの道具棚。** 通常の開発で、この文書の読込、
ツールの導入確認、バージョン確認、doctor、MCP起動を行う必要はない。
既存のVineflowerがあるMOD-AI部門へ配置し、新しい重複部門は作らない。

## 使い分け

| 道具 | この区画での用途 | 選択の目安 |
|---|---|---|
| Vineflower 1.11.1 | 既存MOD-AIのJava逆コンパイル | 通常のJAR研究。既存CAS/profile経路を優先 |
| CFR 0.152 | Java逆コンパイルの別解・比較 | Vineflowerだけでは読みにくい箇所など、必要な場合だけ |
| REA 6.5.0 | 対応するバイナリ等の明示的なCLI解析 | Java専用ツールでは扱えない対象や、REAが適した調査 |

REA本体とGhidra/JADX/IDA等の解析エンジンは別物。ここではエンジンを一括導入しない。
対応OS・形式・必要なエンジンは、実際に選んだ操作の上流ドキュメントで確認する。
Javaの難読化解除や任意ゲームの完全解析を保証する機能ではない。

## 初回だけ、選んだ道具を導入する

Python 3.11以上。以下はこのフォルダー内で実行する。PowerShellでも同じ形式。
全ツールを入れる必要はなく、必要な行だけ実行する。

```text
python toolkit.py install cfr
python toolkit.py install vineflower
python toolkit.py install rea
```

Java用の2ツールは固定版JARを取得するだけで、インストール時にはJavaを実行しない。
実際の逆コンパイルにはJava 17以上を用意する。REAはNodeの上流対応範囲
`^22.19.0 || ^24.11.0 || >=26.0.0` とnpmが必要。Java/Node自体は自動導入しない。

ファイルは既定でこの区画の `.local/` に置く。npmもローカルprefixを使い、
ライフサイクルスクリプトを無効化する。ユーザーのグローバルnpm、Codex設定、
MCP設定、スキルフォルダーには登録しない。`npx ...@latest setup` は使わない。
REA内部のキャッシュや状態保存先まで、このラッパーが隔離するわけではない。

`tools.json` に版・取得元・チェックサムを記録。Vineflowerは既存実証済みSHA-256を再利用。
CFRの配布元が示す旧式MD5との一致を確認し、取得した実物のSHA-256も記録する。
**CFRのMD5は暗号学的に強い署名やSHA-256ピンの代用ではない。**
REAは直接依存を6.5.0へ固定し、推移依存は初回npm解決後のローカルlockに記録する。
マシン間で全依存が同一である保証や、全npm依存の独立監査は含まない。

## Javaの比較解析

```text
python toolkit.py decompile cfr C:/research/example.jar --run example-cfr-001
python toolkit.py decompile vineflower C:/research/example.jar --run example-vf-001
```

2行は選択例であり、毎回両方を実行する指示ではない。
`--java "C:/Java/jdk-17/bin/java.exe"` でJavaを選べる。
依存JARは `--library C:/research/dependency.jar` を必要な数だけ指定する。

入力は作業コピーを解析し、元JARを変更・起動しない。出力と `receipt.json` は
`.local/runs/実行名/` に保存。同名実行は上書きせず拒否する。
receiptは入力・道具・依存物・生成JavaのSHA-256、コマンド、終了状態を保持する。
`COMPLETED` はツール終了とJava出力を確認しただけで、全クラスの復元や動作一致を意味しない。
失敗時は失敗記録を残す。対象アプリの再コンパイル・実行・検証は別工程。

## 既存VineflowerのCAS経路と接続

既存の `src/kneekura_tech_hub/minecraft/providers.py` は変更しない。
現在のprofile/indexへ派生ソースを追加するときは、従来の `profile transform` を使う。
この区画から設定JSONだけ生成できる。

```text
python toolkit.py provider-config --java C:/Java/jdk-17/bin/java.exe --classpath-root-id ROOT_ID
```

返されたJSONをUTF-8で保存し、TECH HUBルートから従来コマンドへ渡す。
`ROOT_ID` は実際の依存JARのroot IDであり、依存の順序を維持して繰り返し指定する。
依存が必要ないfixtureだけ、オプションを省略する。PowerShell 5.1の `>` はUTF-16出力に
なるため、そのままJSON保存に使わない。設定生成はJavaを実行しない。

```text
python -m kneekura_tech_hub.minecraft --store CACHE profile transform --index INDEX --root INPUT_ROOT_ID --operation decompile --provider PROVIDER_JSON
```

## REAを必要なときだけ使う

```text
python toolkit.py rea -- --help
```

この明示的なヘルプから必要なCLI操作だけ選ぶ。`setup/mcp/upgrade/uninstall` は
この入口の対象外。常駐MCPの全ツール一覧を毎セッションAIへ渡さないためのCLI方式であり、
CLIを呼べるCodex等から利用する。MCP自動登録と同じ使い勝手を提供するものではない。

選択したREA操作が対象プログラム、通信、端末を動かす場合は、それぞれの権限・隔離条件を
別途確認する。この区画はOSサンドボックスではなく、悪意ある入力への防御境界でもない。
Javaの時間上限・ヒープ上限はあるが、ログ出力量や全ディスク使用量はOSで強制制限しない。

## 変更時の検証

この区画を編集したときだけ、TECH HUBルートから実行する。

```text
python -m unittest discover -s departments/minecraft/mod-ai/reverse-engineering/tests -p "test_*.py" -v
```

専用CIはパスを限定し、通常は外部ツールを導入しない契約テストのみ。
実ツールの合成fixture検証は、Actionsの手動実行で `real_tools=true` を選んだ場合だけ行う。
自作fixture以外のゲーム、ユーザーPC、ネイティブ解析エンジンまで合格扱いにしない。
実施済み範囲は [VERIFICATION.md](VERIFICATION.md)、構造は [DESIGN.md](DESIGN.md)。
