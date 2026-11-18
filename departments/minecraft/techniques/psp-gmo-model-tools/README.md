# PSP GMO モデル変換ツール（ISO → OBJ / glTF / Blockbench）

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

使い方の例:

```bash
python tools/cpk_extract.py install.cpk out/ 'Scene_Dungeon/unit/<name>\.pac'
python tools/pac_extract.py out/Scene_Dungeon/unit/<name>.pac out/pac/
python tools/gmo2obj.py out/pac/<NAME>.GMO out/obj/
python tools/gmo2gltf.py out/pac/<NAME>.GMO out/<name>.glb --motion out/pac/<NAME>_*_*.GMO
python tools/gmo2bbmodel.py out/pac/<NAME>.GMO out/<name>.bbmodel --motion out/pac/<NAME>_*_*.GMO --scale 0.05
```

形式の詳細は [FORMATS.md](FORMATS.md)。

## 検証（実機で確認した範囲）

- 1 体（ボス級の敵モデル、4796 頂点・37 骨・9 アニメ）で全工程を通した。
- 四角形の頂点順（輪郭順 634 / ジグザグ 0）と面の向き（法線と一致 2111 / 逆 0）が実測で一意に決まった。
- 逆バインド行列と骨ワールド行列の逆行列が最大誤差 0.0002 で一致。
- GLB は Khronos 公式バリデータでエラー 0・警告 0。
- `.bbmodel` は **Blockbench 5.2.1 に実際に読み込み**、静止姿勢の全骨位置の誤差 0。9 本のアニメを 2 時刻ずつ再生し、全骨の位置を元データから独立に計算した値と比較して最大誤差 約 0.12（キー間引きによる）。
- `tests/test_psp_gmo_model_tools.py`（合成データのみ。頂点レイアウト・チャンク木・回転・行列・GIM スウィズル・キー間引き）。

## 未検証・限界

- **マイクラ本体では表示できない**。Java Block / Bedrock のモデル形式は立方体専用で、メッシュを持てない。ゲーム内で動かすには、メッシュを描く MOD 側の仕組みが必要。
- Blockbench のウェイトは 1 頂点あたり最大 4 本。5 本以上のモデルでは切り捨てが起きる（件数を出力する）。
- UV アニメーション（`0x98`）、モーフ、複数の UV レイヤーは未対応。
- 他タイトル・他モデルでの動作は未確認。GMO / GIM は多くの PSP ゲームで使われるが、独自拡張がありうる。

## 権利と範囲

- このフォルダに入れるのは**自作コードと形式の事実だけ**。ISO・CPK・GMO・GIM・テクスチャ・変換結果（OBJ/GLB/.bbmodel）は入れない。
- 変換するのは利用者が正規に持つメディア。結果は個人の学習・研究にとどめ、再配布しない。
- 参考にした公開資料: Rich Whitehouse "Dissidia Model Format"（Web Archive）の GMO チャンク構造、Blockbench のオープンソース（`armature` / `armature_bone` / `mesh` の保存形式）。
