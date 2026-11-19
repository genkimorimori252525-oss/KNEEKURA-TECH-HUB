# schematic_port — mcbuild 完成建築のバージョン別書き出し

計画: [../mcbuild/PLAN-2026-11-14-CROSS-VERSION.md](../mcbuild/PLAN-2026-11-14-CROSS-VERSION.md)／監査: [../mcbuild/AUDIT-2026-11-14.md](../mcbuild/AUDIT-2026-11-14.md)／実装状況: [../mcbuild/IMPLEMENTATION-STATUS-2026-11-14.md](../mcbuild/IMPLEMENTATION-STATUS-2026-11-14.md)

**状態: FILE-LEVEL IMPLEMENTED (P0–P3, P5) / WORLDEDIT RUNTIME NOT_RUN (P4)**

標準ライブラリのみ。ネットワーク通信なし・ワールド編集なし（`fetch-registry` だけが明示実行時に Mojang から取得）。`runner.py` には組み込んでいない（計画どおり、運用確認後に任意で接続）。

```text
mcbuild blueprint ─ export_sparse.py ─▶ sparse JSON（air 意図 KNOWN）─┐
mcbuild final.schem (Sponge v3) ─────────────────────▶ (air 意図 UNKNOWN) ┤
                                                                         ▼
                        Building IR → 1.20.1 公式レジストリで全 state 照合（fail-closed / 明示置換のみ）
                                  → Sponge v2 書出し → 独立 reader で読戻し → セル単位 ZERO_DIFF のときだけ保存
```

## 使い方（Tech Hub ルートから、`PYTHONPATH=departments/minecraft/building/portable`）

```bash
python -m schematic_port fetch-registry --target minecraft-java-1.20.1-forge
```

初回だけ明示実行。Mojang の 1.20.1 server.jar（SHA-1 固定）を `local-artifacts/registries/` に取得し、データ生成器 `--reports` で公式 `blocks.json` を作る。サーバーは起動しない。生成物の SHA-256 はプロファイルに固定済みで、一致しなければ失敗する。

```bash
python -m schematic_port inspect  path/to/final.schem
python -m schematic_port validate path/to/final.sparse.json --target minecraft-java-1.20.1-forge
python -m schematic_port convert  path/to/final.sparse.json --target minecraft-java-1.20.1-forge --out build-1.20.1.schem
```

air 意図を保つには、mcbuild の固定環境で疎な配置を書き出してから変換する:

```bash
cd departments/minecraft/local-artifacts/mcbuild/upstream
uv run --offline --frozen --no-sync python ../../../building/portable/export_sparse.py ../runs/<run>/final_blueprint.py ../runs/<run>/final.sparse.json
```

| オプション | 意味 |
| --- | --- |
| `--substitutions table.json` | `{"元state または id": "置換先state"}`。置換先も公式レジストリで検査。air への置換は拒否 |
| `--air-policy skip_air`（既定） | `//paste -a` 前提。明示 air は適用されない旨を警告 |
| `--air-policy full_region_replace --confirm-full-replace` | 領域内の全セルを上書き。明示確認が無いと実行しない |
| `--origin x,y,z` | 貼付け基準点（設計座標、既定 0,0,0）。`Metadata.WEOffset` に反映 |

終了コード: 0 成功、2 入力/利用エラー、3 互換性で拒否、4 読戻し差分。拒否・差分のときは何も書かない。既存ファイルは上書きしない。

出力の横に `<out>.report.json`（source_commit / source_sha256 / target_profile / block_count / dimensions / warnings / substitutions / air_policy / validation_level / out_schem_sha256 / 各ゲート）を書く。ゲート `P4_READABLE_BY_WORLDEDIT`・`P4_PASTE_IN_TEST_WORLD`・`P4_VISUALLY_CHECKED` は実機で確認するまで `NOT_RUN` のまま。

## テスト

```bash
python -m pytest tests/test_building_port.py
```

pytest が無い環境では `python tests/test_building_port.py`。T01–T08 を合成の小さなレジストリで検査し、公式レジストリがローカルにあれば実物でも検査する（無ければ skip）。

## 他バージョンの追加

`profiles/<id>.json` を足す（形式・DataVersion・レジストリ SHA を別々に固定）。現在のライターは Sponge v2 のみ。未検証の版を対応済みにしない。
