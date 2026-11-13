# 実装状況 — mcbuild 完成建築のバージョン別移植（2026-11-14）

ブランチ `jolly/building-cross-version-impl-20261114`（基点 PR #115 `97600491`）。計画書・監査の本文は変更していない。実装: [`../portable/`](../portable/README.md)

## ゲート別の実測

| ゲート | 判定 | 実測した証拠 |
| --- | --- | --- |
| **P0** 再現可能なベースライン | **PASS（ローカル）** | pinned `34ce8637` を `prepare`/`install` し FakeLLM デモ（API 不使用）で `final.schem` 生成（sha256 `98852601…`）。独自 reader と mcbuild の nbtlib の読取りが一致: Version 3 / DataVersion 3953 / 5×3×5 / Offset [0,0,0] / palette {stone:0, air:1} / Data 75 byte。同じ blueprint から `export_sparse.py` で得た疎配置と v3 の非 air セル 55 個が完全一致 |
| **P1** Building IR | **PASS（単体）** | ABSENT / EXPLICIT_AIR / SOLID_OR_OTHER を区別。実データでは v3 の air 20 セルが実際は**未配置**（内部・扉の clear）だったことを疎配置で確認（監査 A05 の実例）。負座標・非ゼロ origin・L 字・消去後 bounds をテスト |
| **P2** 対象版の厳密互換 | **PASS（公式レジストリ）** | Mojang 1.20.1 server.jar（sha1 `84194a2f…`、内蔵 version.json の world_version=3465）の `--reports` から公式 blocks.json（1003 ブロック、sha256 `f10d5da8…`）を生成しプロファイルに固定。実データは LOSSLESS。`trial_spawner` は公式レジストリに無く拒否されることを確認 |
| **P3** v2 書出しと読戻し | **PASS（ファイルレベル）** | 実データを v2 に変換し、独立 reader でセル単位 ZERO_DIFF。さらに **第三者実装の nbtlib** でも読み、ルート名 `Schematic`・各タグ型（Version/DataVersion/PaletteMax=Int、寸法=Short、Offset=IntArray、BlockData=ByteArray）が WorldEdit 7.2.15 reader の要求どおりであることを確認 |
| **P4** Forge 1.20.1 実機 | **NOT_RUN** | `READABLE_BY_WORLDEDIT` / `PASTE_IN_TEST_WORLD` / `VISUALLY_CHECKED` は全て NOT_RUN。WorldEdit 7.2.15 の Java reader での読込みも未実施 |
| **P5** CLI・レポート | **PASS（単体）** | `inspect` / `validate` / `convert` / `fetch-registry`。レポートに計画の必須項目と分離ゲートを記録 |

テスト: `tests/test_building_port.py` 17/17（T01–T08、WorldEdit の式による生 NBT 照合、セル数爆弾、CLI の成功/上書き拒否/互換拒否/全置換確認、実レジストリ。skip 0）、`tests/test_mcbuild_bridge.py` に UTF-8 子プロセステスト追加。実行環境: Windows 11, Python 3.10.11（pytest 未導入のため素の実行モード）。CI（Python 3.12 + pytest）は未実行。

## 独立レビュー（reviewer-opus、読み取りのみ、2026-11-14）

WorldEdit 7.2.15 で位置ずれ・state 欠落・air 置換・読込失敗を起こす形式差は見つからず。指摘は全て修正済み:

| ID | 指摘 | 対応 |
| --- | --- | --- |
| H1 | v3 読取りでセル上限確認より前に最大 3200 万要素の dict を作り得る | 非 air セルを先に数えて `CELL_LIMIT` |
| H2 | 読戻しが air を含む全体積を dict 化 | 密データは `array` で保持し dict は非 air のみ、`state_at` で照会 |
| M1 | WEOffset が 0 のテストしかなく符号を検証できない | 原点≠min の配置で生 NBT を WorldEdit の式と直接照合 |
| M2 | CLI テストが名前と違う理由で exit 2 になっていた | 一時レジストリに固定したプロファイルで 0/2/3 と書込み経路を実行 |
| M3 | v3 入力の全置換で置換範囲が元の箱より縮む | 元 v3 の箱を置換範囲にし警告 |
| 低 | 配列の増幅・疎 JSON 上限・未捕捉例外・cave_air の air 化・置換表の重複キー・書込み TOCTOU・SKIP の合格計上・高さ超過 | それぞれ修正（typed array、64MB、例外を exit 2 に、air 変種保持、重複拒否、hard link による排他公開、skip 別計上、`TALLER_THAN_TARGET_BUILD_HEIGHT` 警告） |

修正後も実データの出力は同一バイト（sha256 `398ec38d…`）で、疎配置入力と v3 入力のどちらからでも同じ出力になる。

## 計画からの変更・追加（自己改善）

1. **NBT ライブラリを追加しない**: 計画は「採用済みの NBT ライブラリ優先」だが Tech Hub 本体には無い。nbtlib を新規依存にする代わりに、境界付きの小さな標準ライブラリ実装にした（長さを残りバイトで検査してから確保、gzip 爆弾・重複キー・末尾ゴミを拒否）。代わりに検証では mcbuild 側の nbtlib を**独立の第三者 reader**として使い、独立性はむしろ上がった。
2. **公式レジストリの取得元**: 第三者のデータセットではなく、Mojang 自身のデータ生成器の出力を SHA 固定で使う。Git には入れない。
3. **部分 state の扱い**: mcbuild は `oak_stairs[facing=east]` のように一部 property だけを書く。WorldEdit は残りを既定値で補うので合法として通し、件数を `partial_states_default_filled` に記録する。
4. **v3 入力の air は運ばない**: v3 だけの入力では air の意図が分からないため、air セルは IR に入れず `AIR_INTENT_UNKNOWN` とし、`full_region_replace` を選ぶと「未配置セルも air で上書きされる」と警告する。
5. **runner.py の Windows 不具合を修正**: 日本語 Windows（cp932）で upstream の `rich` が em dash を出力して `UnicodeEncodeError` で落ちることを実測した。子プロセスに `PYTHONUTF8=1` / `PYTHONIOENCODING=utf-8` を渡して解消（修正後にデモが完走することを確認）。
6. **出力の再現性**: gzip の mtime を 0 に固定し、同じ入力からは同じバイト列（同じ sha256）になる。

## 残り（次の一手）

- P4: 隔離した Forge 1.20.1 + WorldEdit 7.2.15 のワールドで、バックアップ後に手動で `//schem load` → clipboard 確認 → `//paste -a`。T01–T04 相当の小さな fixture で、state・負座標・air スキップを観測する。実機起動は別承認。
- 明示 air だけを貼る仕組み（sidecar マスク）は未実装。v2 単体では表現できない。
- MOD ブロック: 名前空間が minecraft 以外のものは現在すべて `UNKNOWN_MOD_BLOCK` で拒否。MOD のレジストリを固定する仕組みは未実装。
