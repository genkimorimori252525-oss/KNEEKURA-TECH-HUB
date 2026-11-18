# PSP GMO モデル変換ツール（ISO → OBJ / glTF / Blockbench）

> **次のモデルを変換するときは、まず [PLAYBOOK.md](PLAYBOOK.md) を読む。** 手順・決めた方針と理由・毎回の検証基準・落とし穴の記録。

PSP ソフトのディスクイメージから 3D モデルを取り出し、Blockbench やマイクラ MOD で扱える形式に変換する自作ツール群。
**標準ライブラリ + Pillow（PNG 出力のみ）**。ゲーム由来のデータはこのリポジトリに入れない（下記「権利と範囲」）。

## できること

```
ISO ──isols.py──▶ ファイル表（位置・サイズ）
 └─ 切り出し ──▶ *.cpk ──cpk_extract.py──▶ *.pac ──pac_extract.py──▶ *.GMO / *.GIM
                                                              │
        ┌─────────────────────┬───────────────────────────────┤
   gmo2obj.py            gmo2gltf.py                     gmo2bbmodel.py
  OBJ+MTL+PNG        GLB（骨・ウェイト・アニメ）       .bbmodel（Blockbench 5.x, Generic Model）
```

| ツール | 役割 |
| --- | --- |
| `isols.py` | ISO9660 のファイル一覧（位置・サイズ） |
| `cpk.py` / `crila.py` / `cpk_extract.py` | CRI CPK の目次読み取りと展開（CRILAYLA 圧縮を自動展開） |
| `pac_extract.py` | PAC（`u16 件数, u16, u32 総サイズ` + 名前32B・offset・size の40B表）の展開 |
| `gmo.py` | GMO（`OMG.00.1PSP`）のチャンク木と PSP GE 頂点レイアウトの読み取り |
| `gim.py` | GIM（`MIG.00.1PSP`）→ RGBA。INDEX4/8/16/32・各 RGBA・PSP スウィズル対応 |
| `gmo2obj.py` | 基準姿勢の OBJ + MTL + PNG |
| `gmo2gltf.py` | GLB。骨・スキンウェイト・モーション GMO のアニメ付き |
| `gmo2bbmodel.py` | Blockbench の `.bbmodel`（メッシュ + armature + ウェイト + アニメ） |
| `obj_preview.py` / `glb_pose_check.py` | 簡易ソフトウェア描画（OBJ／GLB を読み直して姿勢を描く検証用） |
| `bb_cdp.mjs` / `bb_verify_build.py` | Blockbench を実際に起動して `.bbmodel` を読み込み、全骨の位置を検証（Node 22 以上） |
| `gmo_tree.py` | GMO チャンク木のダンプ（解析用） |
| `obj2schem.py` | OBJ+MTL+PNG → **Minecraft 1.20.1 の Sponge Schematic v2（`.schem`）**。表面だけの殻にするボクセライザ（中空）。1.20.1 標準ブロックの代表色（CIELAB 最近傍）に置換 |
| `hybrid2bbmodel.py` | **最終形の立方体モデル**。なめらかな面（ドレス・顔）は、元メッシュの面に沿った**斜めの板**（回転キューブ、厚み0・1面・テクスチャ両面表示）にし、元テクスチャを 1 ブロック = 1 ピクセルのドット絵にして貼る。抜き絵の飾りや歯車はブロック。顔など一部だけ絵を細かくできる |
| `bb_verify_hybrid.py` | 上を Blockbench 実機で検証（板の 4 隅の位置・板の全画素・ブロックの全露出面・geo.json の一致） |
| `voxel2bbmodel.py` | `.schem` → **Blockbench の立方体モデル**（Bedrock Entity 形式の `.bbmodel` + `.geo.json` + 色アトラス PNG）。ボクセルを直方体に統合し、1 ブロック = 1 ピクセルのテクスチャで色を持たせる（色が違っても 1 つの箱にまとめられる） |
| `bb_verify_cubes.py` | 上の立方体モデルを Blockbench 実機で検証（全露出面の色・自作 geo.json と Blockbench 書き出しの一致・読み込み時間・描画面数） |
| `schem_check.py` | `.schem` の独立検査（NBT 構造・パレット・varint 復号・セル数・材料表との一致。書き出し側のコードは使わない） |

使い方の例:

```bash
python tools/cpk_extract.py install.cpk out/ 'Scene_Dungeon/unit/<name>\.pac'
python tools/pac_extract.py out/Scene_Dungeon/unit/<name>.pac out/pac/
python tools/gmo2obj.py out/pac/<NAME>.GMO out/obj/
python tools/gmo2gltf.py out/pac/<NAME>.GMO out/<name>.glb --motion out/pac/<NAME>_*_*.GMO
python tools/gmo2bbmodel.py out/pac/<NAME>.GMO out/<name>.bbmodel --motion out/pac/<NAME>_*_*.GMO --scale 0.05
```

ブロック構成（ボクセル）にする場合:

```bash
python tools/obj2schem.py out/obj/<NAME>.obj out/<name>_128.schem --size 128 --exclude '<除外するグループの正規表現>' --gain 1.3 --sat 1.3 --preview out/preview
python tools/schem_check.py out/<name>_128.schem --materials out/<name>_128.materials.tsv
```

- `--size` は最長辺のブロック数。`--exclude` は板状の背景など、ブロックにしたくないグループ。
- `--gain` / `--sat` は、色をブロックに置き換える前の明るさ・彩度の倍率。ゲームのテクスチャは暗めなので 1.3 前後が見た目に近かった（1 体での目視判断）。
- 向きは元データのまま（OBJ の +Y が上、+Z が南）。出力は `.schem` と、ブロック別の個数 `.materials.tsv`、確認用の `--preview` 画像。
- このリポジトリの建築ジャンル（`departments/minecraft/building/`）の 1.20.1 / Sponge v2 検証に渡せる形式。

立方体（ブロック）だけの Blockbench モデルにする場合（マイクラ本体や GeckoLib はメッシュを持てないが、立方体なら載る）:

```bash
python tools/voxel2bbmodel.py out/<name>_128.schem out/cubes --name <name>_128   # 最適化つき（既定）
python tools/voxel2bbmodel.py out/<name>_128.schem out/cubes_legacy --legacy      # 最適化なし（比較用）
```

最適化（見た目は変えない）:
1. 外から見えない閉じた空洞を埋める（外から見える面は不変）。
2. 幾何だけで直方体に統合（色は無視。色はテクスチャが持つので、違う色のブロックを 1 つの箱にまとめられる）。伸ばす軸と走査順の 36 通りから、見える箱が最少のものを選ぶ。
3. 外から 1 ピクセルも見えない箱は捨て、箱の中の隠れた面は書かない（Blockbench / Bedrock は `texture: null` の面を描画せず書き出さない）。
4. `.geo.json` は圧縮して書く（`--pretty` でインデント付き）。

1 体（128 ブロック版・74,395 ブロック）での実測（Blockbench 5.2.1、毎回クリーン起動）:

| | キューブ | 描画する面 | 頂点 | `.bbmodel` | `.geo.json` | 読み込み |
| --- | --- | --- | --- | --- | --- | --- |
| 旧（`--legacy` 相当） | 8,259 | 49,554 | 198,216 | 5.0MB | 9.0MB | 5.6 秒 |
| 最適化後 | 5,851（−29%） | 29,871（−40%） | 140,424（−29%） | 2.8MB | 1.5MB（−84%） | 3.8 秒（−33%） |

どちらも、露出する全ボクセル面（旧 136,834 / 新 85,754）でテクスチャ色が期待色と一致（不一致 0）。旧新の画面比較で差のある画素は 0.3%（目視では同一）。
**GeckoLib / マイクラ実機で「書かれていない面」が描画されないことは未確認**（Bedrock の仕様と Blockbench の挙動は確認済み）。

形式の詳細は [FORMATS.md](FORMATS.md)。

## 検証（実機で確認した範囲）

- 1 体（ボス級の敵モデル、4796 頂点・37 骨・9 アニメ）で全工程を通した。
- 四角形の頂点順（輪郭順 634 / ジグザグ 0）と面の向き（法線と一致 2111 / 逆 0）が実測で一意に決まった。
- 逆バインド行列と骨ワールド行列の逆行列が最大誤差 0.0002 で一致。
- GLB は Khronos 公式バリデータでエラー 0・警告 0。
- `.bbmodel` は **Blockbench 5.2.1 に実際に読み込み**、静止姿勢の全骨位置の誤差 0。9 本のアニメを 2 時刻ずつ再生し、全骨の位置を元データから独立に計算した値と比較して最大誤差 約 0.12（キー間引きによる）。
- `tests/test_psp_gmo_model_tools.py`（合成データのみ。頂点レイアウト・チャンク木・回転・行列・GIM スウィズル・キー間引き・ボクセル化・`.schem` の書き出しと独立検査）。
- `.schem` は、書き出し側とは別実装の自作検査ツールと、第三者ライブラリ `nbtlib` の両方で読み直し、寸法・パレット・セル数・非空気数・向き（最下層／最上層の個数）が一致。パレットのブロック ID 61 種は minecraft-data の 1.20 ブロック一覧（1003 種）にすべて存在。**ゲーム内（WorldEdit での貼り付け）は未確認**。

## 未検証・限界

- **マイクラ本体では表示できない**。Java Block / Bedrock のモデル形式は立方体専用で、メッシュを持てない。ゲーム内で動かすには、メッシュを描く MOD 側の仕組みが必要。
- Blockbench のウェイトは 1 頂点あたり最大 4 本。5 本以上のモデルでは切り捨てが起きる（件数を出力する）。
- UV アニメーション（`0x98`）、モーフ、複数の UV レイヤーは未対応。
- 他タイトル・他モデルでの動作は未確認。GMO / GIM は多くの PSP ゲームで使われるが、独自拡張がありうる。

## 権利と範囲

- このフォルダに入れるのは**自作コードと形式の事実だけ**。ISO・CPK・GMO・GIM・テクスチャ・変換結果（OBJ/GLB/.bbmodel）は入れない。
- 変換するのは利用者が正規に持つメディア。結果は個人の学習・研究にとどめ、再配布しない。
- 参考にした公開資料: Rich Whitehouse "Dissidia Model Format"（Web Archive）の GMO チャンク構造、Blockbench のオープンソース（`armature` / `armature_bone` / `mesh` の保存形式）。
