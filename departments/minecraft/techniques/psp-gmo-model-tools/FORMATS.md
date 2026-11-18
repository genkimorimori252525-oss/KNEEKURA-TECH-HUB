# 形式メモ（実測で確定したもの）

## コンテナ
- **CPK**: `CPK ` ヘッダ + `@UTF` 表。ファイルは `CRILAYLA` 圧縮のことがある（`crila.py`）。目次の `FileOffset` は `TocOffset` か `ContentOffset` の小さい方を基準にする。
- **PAC**: `u16 件数, u16 ?, u32 総サイズ`、続いて `name[32] + u32 offset + u32 size` の 40 バイト表。

## GMO（`OMG.00.1PSP`）
- チャンク: `u16 type, u16 header_size, u32 total_size`（total は先頭 8 バイトを含む）。`type` に `0x8000` が立つものは属性（リーフ。ヘッダ長 0、データは +8 から）。
- 参照値は u32、下位 12 bit が番号（例 `0x00071000` = 配列 #0、型は上位 16 bit）。
- 容器: `0x02` ファイル / `0x03` モデル / `0x04` 骨 / `0x05` パーツ / `0x06` メッシュ / `0x07` 頂点配列 / `0x08` 材質 / `0x09` 材質レイヤー / `0x0a` テクスチャ / `0x0b` モーション / `0x0c` fカーブ。
- **頂点配列 `0x07`**: ヘッダの後に `u32 vtype, u32 頂点数, u32, u32` と頂点データ。`vtype` は PSP GE の頂点型（重み・UV・色・法線・位置の並びとサイズ）。位置は `s16/32768 × scale + bias`、UV は `u16/32768 × scale + bias`。
- **scale/bias `0x8015`**（モデル直下）: 先頭 u32 が 384 なら位置（bias xyz, scale xyz の 6 float）、3 なら UV（bias uv, scale uv の 4 float）。
- **索引 `0x8066`**: `u16 配列参照, u16, i32 primType, i32 a1, i32 a2` の後に u16 索引。primType 3 = 三角形リスト（a1 = 索引数）。primType 5 = a1 頂点の多角形を a2 個（3 = 三角形、4 = 四角形・頂点は輪郭順）。
- メッシュ属性: `0x8061` 材質参照 / `0x8062` ボーンパレット（パーツの骨リストへの添字）。重みの本数 = パレット数。
- **骨 `0x04`**: `0x8041` 親 / `0x8048` 移動(3 float) / `0x804b` 回転クォータニオン(x,y,z,w) / `0x8044` スキン骨リスト / `0x8045` 逆バインド行列(4x4, 行ベクトル規約) / `0x804e` 持ち主パーツ。逆バインド × 骨ワールドは単位行列なので、**基準姿勢の頂点データはそのままモデル空間の座標**。
- **モーション `0x0b`**: `0x80b1` ループ範囲（float 開始, 終了フレーム）/ `0x80b2` フレームレート / `0x80b3` = (対象骨, cmd, _, fカーブ)。cmd `0x48` 移動 / `0x4b` 回転 / `0x4c` 拡縮 / `0x98` UV。
- **fカーブ `0x0c`**: 本体は `fmt, dims, keys, 0` の後に keys 個の `[時刻, 値×dims]`。**すべて float16**、時刻はフレーム番号。値は絶対値（rest への加算ではない）。

## GIM（`MIG.00.1PSP`）
- ブロック: `u16 type, u16 0, u32 size, u32 next, u32 data_offset(=0x10)`。`0x02` ルート / `0x03` 絵 / `0x04` 画像 / `0x05` パレット。
- 画像・パレットのヘッダ: `+4 format, +6 order(0 = 線形, 1 = PSP スウィズル), +8 w, +10 h, +14 pitch_align, +16 height_align, +0x1c ピクセル開始`。
- format: 0 RGB565 / 1 RGBA5551 / 2 RGBA4444 / 3 RGBA8888 / 4 INDEX4 / 5 INDEX8 / 6 INDEX16 / 7 INDEX32。
- スウィズル: 16 バイト幅 × 8 行のブロックを横に並べて順に格納。

## Sponge Schematic v2（`.schem`, Minecraft 1.20.1 = DataVersion 3465）
- gzip された NBT。ルートは Compound（名前 `Schematic`）で、`Version`(int 2) / `DataVersion`(int) / `Metadata`(compound) / `Width` `Height` `Length`(short) / `Offset`(int[3]) / `PaletteMax`(int) / `Palette`(compound: ブロック状態文字列 → int) / `BlockData`(byte[])。
- `BlockData` は varint の列。並びは `index = x + z*Width + y*Width*Length`。パレットは 0 番を `minecraft:air` にして 0..N-1 で連続させる。
- ブロック色の選び方（`obj2schem.py`）: 三角形を 0.45 ボクセル間隔でサンプルしてテクスチャ色を平均（α<128 は除外）→ 明るさ・彩度の倍率 → CIELAB 最近傍で標準ブロックの代表色に置換。代表色は近似値。

## Blockbench 5.x（`.bbmodel`, Generic Model）
5.2.1 を実機で確認。
- 構成: `armature` の下に `armature_bone`（入れ子）と `mesh`。メッシュは骨の**現在の姿勢を束縛姿勢**として扱う。**編集モードで骨を動かすと束縛姿勢が更新される**ので、変形の検証はアニメ再生で行う。
- 骨 `origin` は**親からの相対**（親の回転も効く）、`rotation` は Euler **ZYX** の度数。
- ウェイトは骨側 `vertex_weights["<メッシュuuid先頭6文字>:<頂点キー>"] = 重み`。1 頂点あたり最大 4 本。
- 面 `faces[key] = {vertices:[...], uv:{頂点キー:[u,v]}（テクスチャのピクセル座標）, texture:番号}`。
- アニメの合成: 位置は加算、回転は rest の Euler 成分に**成分ごと加算**、拡縮は乗算。よって GMO の絶対値は「アニメ値 − rest 値」に変換する（回転は時間方向に ±360° を連続化）。
- 検証手順: `Blockbench.exe --remote-debugging-port=<port> --user-data-dir=<使い捨てフォルダ>` で起動し、`bb_cdp.mjs` で JS を評価。タブを積みすぎるとレンダラーが肥大する（約 20 個で 1.7GB）ので定期的に再起動する。
