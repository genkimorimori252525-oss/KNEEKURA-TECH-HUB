# ゲームの3Dモデル → マイクラ（Blockbench / ブロック）変換プレイブック

PSP の GMO モデル（ワルプルギスの夜）で確立した手順。次のモデルも、同じ順で・同じ検証で進める。
各ツールの詳細は [README.md](README.md)、形式の事実は [FORMATS.md](FORMATS.md)。

## 0. 成果物（作れる形）

| 形 | ツール | 用途 |
| --- | --- | --- |
| OBJ + PNG | `gmo2obj.py` | 形と色の確認、他ツールへの入力 |
| GLB（骨・ウェイト・アニメ） | `gmo2gltf.py` | Blender / Unity / MOD の自前描画 |
| `.bbmodel`（メッシュ・骨格・アニメ） | `gmo2bbmodel.py` | Blockbench で見る・編集する（マイクラ本体には載らない） |
| `.schem`（1.20.1 のブロック構成） | `obj2schem.py` | WorldEdit で建てる |
| **`.bbmodel` + `.geo.json`（立方体だけ）** | `hybrid2bbmodel.py`（推奨）/ `voxel2bbmodel.py` | **マイクラ・GeckoLib に載る立方体モデル** |

立方体モデルは `hybrid2bbmodel.py`（**斜めの板 + ブロック**）が最終形。`voxel2bbmodel.py`（全部ブロック）は比較用。

## 1. 手順（ワルプルギスで実際に使った値）

```bash
# 取り出し
python tools/isols.py <iso>                                             # 位置を見て CPK を切り出す
python tools/cpk_extract.py install.cpk out/ 'Scene_Dungeon/unit/<name>\.pac'
python tools/pac_extract.py out/Scene_Dungeon/unit/<name>.pac out/pac/
# 中間形
python tools/gmo2obj.py out/pac/<NAME>.GMO out/obj/
python tools/gmo2gltf.py out/pac/<NAME>.GMO out/<name>.glb --motion out/pac/<NAME>_*_*.GMO
# ブロック構成（建てる用）
python tools/obj2schem.py out/obj/<NAME>.obj out/<name>_128.schem --size 128 --exclude 'TR_pattern' --gain 1.3 --sat 1.3 --preview out/preview
# 立方体モデル（マイクラ・GeckoLib 用。最終形）
python tools/hybrid2bbmodel.py out/pac/<NAME>.GMO out/slanted --name <name>_slanted \
  --size 128 --unit 16 --texel 1.0 --thickness 0 --coverage 0.12 \
  --plates '^(AL_body|AL_head)' --plate-tex 'walpurgis_01' --fine-parts '^AL_head' --fine-texel 0.25
```

## 2. 決めること（にーくらと決めた方針と理由）

1. **姿勢は元のまま**。ワルプルギスの逆さ吊りは特徴なので直さない。
2. **背景の板は除外**（結界の紋様 `TR_pattern`。平らで巨大、本体ではない）。パーツ名とバウンディングボックスを見て決める。
3. **中は空**（表面だけの殻）。スカートの内側は見える面なので埋めない。外から見えない閉じた空洞だけは埋めてよい（見た目は変わらず、軽くなる）。
4. **前は -Z**（マイクラのエンティティの北向き）。元データの前（顔の向き）を確認してから回す。
5. **色**: ゲームのテクスチャは暗めなので、明るさ・彩度 ×1.3 でブロック色（1.20.1 の標準 61 種）に寄せる。4 通りを並べて目で選んだ値。
6. **細かさ**: 最長辺 128 ブロック、1 ブロック = 1 ピクセル。にーくらは「細かさはこのままでいい」。
7. **なめらかな面は斜めの板にする**（「完全な立方体で構成しなくていい」）。
   - 板は**厚み 0**（元のメッシュの面そのもの）。厚みがあると、側面が継ぎ目で「浮き出した斜めの線」になる。
   - 板は**1 面だけ + テクスチャ両面表示**。表裏 2 面を同じ位置に置くと縞模様のチラつきになる。
   - ピクセルを塗る判定は **coverage 0.12**。0.5 だと継ぎ目に点線の隙間、低すぎると隣の板からはみ出す。
   - **抜き絵（レースの縁取りなど）は板にしない**。1 ブロック = 1 ピクセルに粗くすると枠だけの板になり、宙に浮いた線に見える → `--plate-tex` で本体テクスチャの面だけ板にし、飾りはブロックに残す。
8. **顔は細かく**（`--fine-parts '^AL_head' --fine-texel 0.25` = 1 ブロックに 4×4 ピクセル）。顔だけで十分に精密に見える。
9. **重さ**: 立方体は「色ごと」ではなく「形だけ」でまとめる（色はテクスチャが持つ）。見えない箱・面は出さない。geo.json は圧縮。

## 3. 検証ゲート（毎回。数字で合否を出す）

| 対象 | 確かめること | 合格 |
| --- | --- | --- |
| GMO 読み取り | 四角形の頂点順・面の向き（法線との一致） | 片方が 0 件（例: 634 / 0、2111 / 0） |
| 骨 | 逆バインド行列 = 骨ワールドの逆行列 | 誤差 < 0.01 |
| GLB | Khronos 公式バリデータ（npm `gltf-validator`） | エラー 0・警告 0 |
| `.schem` | `schem_check.py` と `nbtlib` の両方で読み直す。ブロック ID を minecraft-data の一覧と照合 | 寸法・パレット・セル数・材料表が一致、未知 ID 0 |
| 立方体モデル | `bb_verify_hybrid.py`（Blockbench 実機）: 板の 4 隅の位置、板の全画素、ブロックの全露出面の色、自作 geo.json と Blockbench 書き出しの一致 | 4 隅誤差 < 0.01、色の不一致 0、geo の差 0 |
| 見た目 | Blockbench で全体・気になる所（スカート・顔）を近くから撮って並べる | にーくらが目で判断 |

Blockbench の起動: `Blockbench.exe --remote-debugging-port=9333 --user-data-dir=<使い捨てフォルダ>`（本人の設定に触れない）。
検証が終わったら、自分で起動した Blockbench だけを終了する。

## 4. 落とし穴（実際に踏んだもの）

- API 経由で `.bbmodel` を読むとプロジェクト設定ダイアログが開く → `Dialog.open.cancel()`。
- 同じページで検証 JS を何度も評価すると `const` が再宣言エラー → 変数名を実行ごとに変える。
- タブを積むと Blockbench が肥大（約 20 個で 1.7GB）してタイムアウト → 定期的に再起動。重い検証は `BB_TIMEOUT_MS` を延ばす。
- Blockbench の編集モードで骨を動かすと**束縛姿勢が更新される**（変形しない）→ 変形の確認はアニメ再生で。
- 自作 NBT 読み手で「代入は右辺が先に評価される」バグ → 名前を先に読んでから値を読む。
- テストの前提ミス: 閉じた殻は空洞を埋めると箱 1 個になる → 穴のある殻で試す。
- PowerShell 5.1 の `Set-Content -Encoding utf8` は BOM を付ける → コミットメッセージ等は BOM なしで書く。
- 出力フォルダの `Remove-Item *` は保護で止まることがある → 上書きか、パスを明示して消す。

## 5. ワルプルギスでの実測（128 ブロック版）

| | 全部ブロック（旧） | 全部ブロック（軽量化） | **斜めの板 + ブロック（最終）** |
| --- | --- | --- | --- |
| キューブ | 8,259 | 5,851 | **2,890**（ブロック 2,255 + 板 635） |
| 描画する面 | 49,554 | 29,871 | **11,942** |
| `.geo.json` | 9.0MB | 1.5MB | **0.7MB** |
| Blockbench 読み込み | 5.6 秒 | 3.8 秒 | **0.4 秒** |

## 6. まだ確かめていないこと

- マイクラ実機・GeckoLib での表示（両面表示・書かれていない面・テクスチャの抜き）。
- WorldEdit での `.schem` の貼り付け。
- 他のモデル・他のタイトルでの動作（GMO / GIM の独自拡張がありうる）。
