"""立方体モデル(.bbmodel / .geo.json)を Blockbench 実機で検証するJSを組み立てる。
使い方: python bb_verify_cubes.py <in.bbmodel> <in.geo.json> <expected.json> <unit> <out.js>
実機で確認すること:
  1. キューブ数・テクスチャ数
  2. 露出している全面について、Blockbench のジオメトリ（頂点とUVの実座標）から面の中心のUVを求め、
     テクスチャのその画素の色が、期待色（元ボクセルのブロック色）と一致するか
  3. Blockbench 自身の Bedrock 書き出し（Codecs.bedrock.compile）と、自作 .geo.json のキューブが一致するか
"""
import sys, uuid

bb, geo, exp, unit, out = sys.argv[1:6]
tag = uuid.uuid4().hex[:8]
body = r"""
(async () => {
  const out = {};
  try {
    const t0 = performance.now();
    Codecs.project.load(MODEL_T, { path: '', name: 'cubes.bbmodel' });
    out.load_call_ms = Math.round(performance.now() - t0);
    await new Promise(r => setTimeout(r, 4000));
    if (typeof Dialog !== 'undefined' && Dialog.open) { out.closed_dialog = true; Dialog.open.cancel(); await new Promise(r => setTimeout(r, 500)); }
    out.format = Format.id;
    out.cubes = Cube.all.length;
    out.textures = Texture.all.length;
    // 実際に描画される面（クアッド）と頂点の数。無効化した面は索引に入らない
    let quads = 0, vertices = 0;
    for (const c of Cube.all) { const g = c.mesh.geometry; quads += (g.index ? g.index.count : 0) / 6; vertices += g.attributes.position.count; }
    out.rendered_quads = quads; out.vertices = vertices;
    const U = UNIT_T;
    // --- テクスチャ画素 ---
    const tex = Texture.all[0];
    const S = tex.width;
    const cv = document.createElement('canvas'); cv.width = S; cv.height = S;
    const cx = cv.getContext('2d');
    cx.drawImage(tex.img || tex.canvas, 0, 0);
    const data = cx.getImageData(0, 0, S, S).data;
    out.atlas = S;
    // --- セル -> キューブ ---
    const cellOf = new Map();
    Cube.all.forEach((c, idx) => {
      for (let x = Math.round(c.from[0] / U); x < Math.round(c.to[0] / U); x++)
        for (let y = Math.round(c.from[1] / U); y < Math.round(c.to[1] / U); y++)
          for (let z = Math.round(c.from[2] / U); z < Math.round(c.to[2] / U); z++)
            cellOf.set(x + ',' + y + ',' + z, idx);
    });
    out.cells = cellOf.size;
    const FACE_INDEX = { east: 0, west: 1, up: 2, down: 3, south: 4, north: 5 };
    let bad = 0, checked = 0, nocube = 0; const samples = [];
    for (const e of EXPECTED_T) {
      const [vx, vy, vz, face, r, g, b] = e;
      const ci = cellOf.get(vx + ',' + vy + ',' + vz);
      if (ci === undefined) { nocube++; continue; }
      const c = Cube.all[ci];
      const geom = c.mesh.geometry;
      const pos = geom.attributes.position, uv = geom.attributes.uv;
      const f = FACE_INDEX[face] * 4;
      const p0 = [pos.getX(f), pos.getY(f), pos.getZ(f)], p1 = [pos.getX(f + 1), pos.getY(f + 1), pos.getZ(f + 1)], p2 = [pos.getX(f + 2), pos.getY(f + 2), pos.getZ(f + 2)];
      // 面の中心（BB座標）
      const cxm = (vx + 0.5) * U, cym = (vy + 0.5) * U, czm = (vz + 0.5) * U;
      const P = [cxm, cym, czm];
      if (face === 'east') P[0] = (vx + 1) * U; else if (face === 'west') P[0] = vx * U;
      else if (face === 'up') P[1] = (vy + 1) * U; else if (face === 'down') P[1] = vy * U;
      else if (face === 'south') P[2] = (vz + 1) * U; else P[2] = vz * U;
      const e1 = [p1[0] - p0[0], p1[1] - p0[1], p1[2] - p0[2]], e2 = [p2[0] - p0[0], p2[1] - p0[1], p2[2] - p0[2]];
      const d = [P[0] - p0[0], P[1] - p0[1], P[2] - p0[2]];
      const a = (d[0] * e1[0] + d[1] * e1[1] + d[2] * e1[2]) / (e1[0] ** 2 + e1[1] ** 2 + e1[2] ** 2);
      const bb = (d[0] * e2[0] + d[1] * e2[1] + d[2] * e2[2]) / (e2[0] ** 2 + e2[1] ** 2 + e2[2] ** 2);
      const u0 = uv.getX(f), v0 = uv.getY(f);
      const u = u0 + a * (uv.getX(f + 1) - u0) + bb * (uv.getX(f + 2) - u0);
      const v = v0 + a * (uv.getY(f + 1) - v0) + bb * (uv.getY(f + 2) - v0);
      const tx = Math.floor(u * S), ty = Math.floor((1 - v) * S);
      const k = (ty * S + tx) * 4;
      checked++;
      if (data[k] !== r || data[k + 1] !== g || data[k + 2] !== b || data[k + 3] !== 255) {
        bad++;
        if (samples.length < 5) samples.push({ cell: [vx, vy, vz], face, expected: [r, g, b], got: [data[k], data[k + 1], data[k + 2], data[k + 3]], uv: [+u.toFixed(4), +v.toFixed(4)] });
      }
    }
    out.faces_checked = checked; out.faces_mismatch = bad; out.faces_without_cube = nocube; out.mismatch_samples = samples;
    // --- Blockbench の書き出しとの比較 ---
    const bbgeo = JSON.parse(Codecs.bedrock.compile({}));
    const mine = GEO_T;
    const gb = bbgeo['minecraft:geometry'][0], gm = mine['minecraft:geometry'][0];
    const canon = cu => JSON.stringify(cu);
    const bbCubes = gb.bones.flatMap(b => b.cubes || []).map(canon).sort();
    const myCubes = gm.bones.flatMap(b => b.cubes || []).map(canon).sort();
    out.geo_cubes_bb = bbCubes.length; out.geo_cubes_mine = myCubes.length;
    out.geo_cubes_identical = bbCubes.length === myCubes.length && bbCubes.every((s, i) => s === myCubes[i]);
    out.geo_desc_bb = gb.description; out.geo_desc_mine = gm.description;
    out.geo_bones_bb = gb.bones.map(b => b.name);
    // --- 見た目 ---
    const pv = Preview.selected;
    pv.camera.position.set(900, 760, -1700);
    pv.controls.target.set(0, 430, 0);
    pv.controls.update();
    Canvas.updateAll();
    await new Promise(r => setTimeout(r, 1500));
  } catch (e) { out.error = String(e && e.stack || e).slice(0, 1500); }
  return out;
})()
""".replace('MODEL_T', f'MODEL_{tag}').replace('EXPECTED_T', f'EXPECTED_{tag}').replace('GEO_T', f'GEO_{tag}').replace('UNIT_T', unit)
js = (f'var MODEL_{tag} = ' + open(bb, encoding='utf-8').read() + ';\n'
      f'var GEO_{tag} = ' + open(geo, encoding='utf-8').read() + ';\n'
      f'var EXPECTED_{tag} = ' + open(exp, encoding='utf-8').read() + ';\n' + body)
open(out, 'w', encoding='utf-8').write(js)
print('wrote', out, len(js) // 1024, 'KB')
