"""斜めの板 + ブロックのハイブリッドモデルを Blockbench 実機で検証するJSを組み立てる。
使い方: python bb_verify_hybrid.py <in.bbmodel> <in.geo.json> <expected.json> <out.js>
実機で確認すること:
  1. キューブ数（ブロック b*、板 p*）・読み込み時間・実際に描画される面
  2. 板: 外側の面の4隅のワールド座標が、期待する板の位置・向き（回転）と一致するか
  3. 板: 外側・内側の全画素について、Blockbench のジオメトリ（頂点とUVの実座標）から求めた色が期待色と一致するか
  4. ブロック部: 露出する全面の色が期待色と一致するか
  5. 自作 .geo.json と Blockbench 自身の Bedrock 書き出しのキューブが（数値の許容誤差内で）一致するか
"""
import sys, uuid

bb, geo, exp, out = sys.argv[1:5]
tag = uuid.uuid4().hex[:8]
body = r"""
(async () => {
  const out = {};
  try {
    const t0 = performance.now();
    Codecs.project.load(MODEL_T, { path: '', name: 'hybrid.bbmodel' });
    out.load_call_ms = Math.round(performance.now() - t0);
    await new Promise(r => setTimeout(r, 4000));
    if (typeof Dialog !== 'undefined' && Dialog.open) { Dialog.open.cancel(); await new Promise(r => setTimeout(r, 500)); }
    out.format = Format.id;
    out.cubes = Cube.all.length;
    out.block_cubes = Cube.all.filter(c => c.name[0] === 'b').length;
    out.plate_cubes = Cube.all.filter(c => c.name[0] === 'p').length;
    let quads = 0, vertices = 0;
    for (const c of Cube.all) { const g = c.mesh.geometry; quads += (g.index ? g.index.count : 0) / 6; vertices += g.attributes.position.count; }
    out.rendered_quads = quads; out.vertices = vertices;
    const tex = Texture.all[0], S = tex.width;
    const cv = document.createElement('canvas'); cv.width = S; cv.height = S;
    const cx = cv.getContext('2d'); cx.drawImage(tex.img || tex.canvas, 0, 0);
    const data = cx.getImageData(0, 0, S, S).data;
    out.atlas = S;
    const FI = { east: 0, west: 1, up: 2, down: 3, south: 4, north: 5 };
    const faceVerts = (c, face) => {
      const pos = c.mesh.geometry.attributes.position, uv = c.mesh.geometry.attributes.uv, f = FI[face] * 4;
      const P = [], UV = [];
      for (let i = 0; i < 4; i++) { P.push([pos.getX(f + i), pos.getY(f + i), pos.getZ(f + i)]); UV.push([uv.getX(f + i), uv.getY(f + i)]); }
      return { P, UV };
    };
    const pixelAt = (fv, local) => {
      const [p0, p1, p2] = fv.P;
      const e1 = [p1[0] - p0[0], p1[1] - p0[1], p1[2] - p0[2]], e2 = [p2[0] - p0[0], p2[1] - p0[1], p2[2] - p0[2]];
      const d = [local[0] - p0[0], local[1] - p0[1], local[2] - p0[2]];
      const a = (d[0] * e1[0] + d[1] * e1[1] + d[2] * e1[2]) / (e1[0] ** 2 + e1[1] ** 2 + e1[2] ** 2);
      const b = (d[0] * e2[0] + d[1] * e2[1] + d[2] * e2[2]) / (e2[0] ** 2 + e2[1] ** 2 + e2[2] ** 2);
      const u = fv.UV[0][0] + a * (fv.UV[1][0] - fv.UV[0][0]) + b * (fv.UV[2][0] - fv.UV[0][0]);
      const v = fv.UV[0][1] + a * (fv.UV[1][1] - fv.UV[0][1]) + b * (fv.UV[2][1] - fv.UV[0][1]);
      const k = (Math.floor((1 - v) * S) * S + Math.floor(u * S)) * 4;
      return [data[k], data[k + 1], data[k + 2], data[k + 3]];
    };
    // ---- 板 ----
    const byName = new Map(Cube.all.map(c => [c.name, c]));
    let cornerWorst = 0, cornerWorstName = '', pxChecked = 0, pxBad = 0, platesChecked = 0; const samples = [];
    for (const p of EXPECTED_T.plates) {
      const c = byName.get(p.name);
      if (!c) { out.missing_plate = (out.missing_plate || []).concat(p.name); continue; }
      c.mesh.updateWorldMatrix(true, false);
      const M = c.mesh.matrixWorld, inv = new THREE.Matrix4().copy(M).invert();
      platesChecked++;
      // 4隅（外側の面 = up）
      const fv = faceVerts(c, 'up');
      const exp4 = [];
      for (const sx of [-1, 1]) for (const sz of [-1, 1])
        exp4.push([0, 1, 2].map(k => p.C[k] + p.N[k] * p.t / 2 + p.X[k] * sx * p.w / 2 + p.Z[k] * sz * p.h / 2));
      const worldCorners = fv.P.map(q => { const v = new THREE.Vector3(q[0], q[1], q[2]).applyMatrix4(M); return [v.x, v.y, v.z]; });
      let worst = 0;
      for (const wc of worldCorners) {
        let best = 1e9;
        for (const e of exp4) best = Math.min(best, Math.hypot(wc[0] - e[0], wc[1] - e[1], wc[2] - e[2]));
        worst = Math.max(worst, best);
      }
      if (worst > cornerWorst) { cornerWorst = worst; cornerWorstName = p.name; }
      // 外側(up)と内側(down)の全画素
      for (const [face, sgn] of [['up', 1], ['down', -1]]) {
        if (c.faces[face].texture === null || c.faces[face].texture === undefined) continue;  // 1面だけの板（厚み0）
        const fvf = faceVerts(c, face);
        for (let pv = 0; pv < p.ph; pv++) for (let pu = 0; pu < p.pw; pu++) {
          const lx = -p.w / 2 + (pu + 0.5) / p.pw * p.w, lz = -p.h / 2 + (pv + 0.5) / p.ph * p.h;
          const W = [0, 1, 2].map(k => p.C[k] + p.X[k] * lx + p.Z[k] * lz + p.N[k] * sgn * p.t / 2);
          const L = new THREE.Vector3(W[0], W[1], W[2]).applyMatrix4(inv);
          const got = pixelAt(fvf, [L.x, L.y, L.z]);
          const ex = p.pix[pv * p.pw + pu];
          pxChecked++;
          if (got[0] !== ex[0] || got[1] !== ex[1] || got[2] !== ex[2] || got[3] !== ex[3]) {
            pxBad++;
            if (samples.length < 5) samples.push({ plate: p.name, face, pu, pv, expected: ex, got });
          }
        }
      }
    }
    out.plates_checked = platesChecked; out.plate_corner_max_error = +cornerWorst.toFixed(4); out.plate_corner_worst = cornerWorstName;
    out.plate_pixels_checked = pxChecked; out.plate_pixels_mismatch = pxBad; out.plate_mismatch_samples = samples;
    // ---- ブロック部 ----
    const U = EXPECTED_T.unit;
    const cellOf = new Map();
    Cube.all.forEach((c, idx) => {
      if (c.name[0] !== 'b') return;
      for (let x = Math.round(c.from[0] / U); x < Math.round(c.to[0] / U); x++)
        for (let y = Math.round(c.from[1] / U); y < Math.round(c.to[1] / U); y++)
          for (let z = Math.round(c.from[2] / U); z < Math.round(c.to[2] / U); z++) cellOf.set(x + ',' + y + ',' + z, idx);
    });
    let bad = 0, checked = 0, nocube = 0; const vs = [];
    for (const [vx, vy, vz, face, r, g, b] of EXPECTED_T.vox) {
      const ci = cellOf.get(vx + ',' + vy + ',' + vz);
      if (ci === undefined) { nocube++; continue; }
      const c = Cube.all[ci];
      const P = [(vx + 0.5) * U, (vy + 0.5) * U, (vz + 0.5) * U];
      if (face === 'east') P[0] = (vx + 1) * U; else if (face === 'west') P[0] = vx * U;
      else if (face === 'up') P[1] = (vy + 1) * U; else if (face === 'down') P[1] = vy * U;
      else if (face === 'south') P[2] = (vz + 1) * U; else P[2] = vz * U;
      const got = pixelAt(faceVerts(c, face), P);
      checked++;
      if (got[0] !== r || got[1] !== g || got[2] !== b || got[3] !== 255) { bad++; if (vs.length < 5) vs.push({ cell: [vx, vy, vz], face, expected: [r, g, b], got }); }
    }
    out.block_faces_checked = checked; out.block_faces_mismatch = bad; out.block_faces_without_cube = nocube; out.block_mismatch_samples = vs;
    // ---- Blockbench の書き出しとの比較（数値は許容誤差つき）----
    const bbgeo = JSON.parse(Codecs.bedrock.compile({}));
    const gb = bbgeo['minecraft:geometry'][0], gm = GEO_T['minecraft:geometry'][0];
    const close = (a, b) => {
      if (typeof a === 'number' && typeof b === 'number') return Math.abs(a - b) < 0.002;
      if (Array.isArray(a) && Array.isArray(b)) return a.length === b.length && a.every((v, i) => close(v, b[i]));
      if (a && b && typeof a === 'object' && typeof b === 'object') { const ka = Object.keys(a).sort(), kb = Object.keys(b).sort(); return ka.length === kb.length && ka.every((k, i) => k === kb[i] && close(a[k], b[k])); }
      return a === b;
    };
    const A = gb.bones.flatMap(b => b.cubes || []), B = gm.bones.flatMap(b => b.cubes || []);
    out.geo_cubes_bb = A.length; out.geo_cubes_mine = B.length;
    let diff = 0; const firstDiff = [];
    for (let i = 0; i < Math.min(A.length, B.length); i++) if (!close(A[i], B[i])) { diff++; if (firstDiff.length < 2) firstDiff.push({ i, bb: A[i], mine: B[i] }); }
    out.geo_cubes_different = diff; out.geo_first_diff = firstDiff;
    out.geo_desc_bb = gb.description; out.geo_desc_mine = gm.description;
    // ---- 見た目 ----
    const pv = Preview.selected;
    pv.camera.position.set(1000, 800, -1500);
    pv.controls.target.set(0, 400, 0);
    pv.controls.update();
    Canvas.updateAll();
    await new Promise(r => setTimeout(r, 1500));
  } catch (e) { out.error = String(e && e.stack || e).slice(0, 1500); }
  return out;
})()
""".replace('MODEL_T', f'MODEL_{tag}').replace('EXPECTED_T', f'EXPECTED_{tag}').replace('GEO_T', f'GEO_{tag}')
js = (f'var MODEL_{tag} = ' + open(bb, encoding='utf-8').read() + ';\n'
      f'var GEO_{tag} = ' + open(geo, encoding='utf-8').read() + ';\n'
      f'var EXPECTED_{tag} = ' + open(exp, encoding='utf-8').read() + ';\n' + body)
open(out, 'w', encoding='utf-8').write(js)
print('wrote', out, len(js) // 1024, 'KB')
