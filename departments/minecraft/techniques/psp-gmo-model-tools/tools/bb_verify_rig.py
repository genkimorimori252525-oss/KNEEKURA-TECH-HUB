"""骨付き立方体モデル（hybrid2bbmodel --rig --motion）を Blockbench 実機で検証するJSを組み立てる。
使い方: python bb_verify_rig.py <model.gmo> <in.bbmodel> <in.geo.json> <expected.json> <out.js> <アニメ:秒> [...]
  モーションGMOは model.gmo と同じフォルダの <MODEL>_<アニメ>.GMO を使う。
実機で確認すること:
  1. グループ（骨）の数、各キューブが期待どおりの骨に入っているか
  2. 各アニメ・各時刻で、全キューブの全頂点が「元データから独立に計算した、その骨の動き D_b(t)」で動かした
     静止位置と一致するか（D_b(t) = S · W_t[b] · W_rest[b]^-1 · S^-1、S はゲーム座標 -> モデル座標）
  3. 自作 .geo.json と Blockbench の書き出しが骨ごとに一致するか
  4. Blockbench 自身の Bedrock アニメ書き出し（GeckoLib が読む animation.json の中身）を返す
"""
import glob, json, math, os, sys, uuid
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gmo
from gmo2gltf import read_bones, read_motion, trs, mul, rigid_inv, world_matrices

gmo_path, bb, geo, exp, out = sys.argv[1:6]
tests = [(t.split(':')[0], float(t.split(':')[1])) for t in sys.argv[6:]]
model = gmo.parse(open(gmo_path, 'rb').read())[0].children[0]
bones = read_bones(model)
rig = json.load(open(exp, encoding='utf-8'))['rig']
mn, cell, dims, unit, keep_front, ox, oz = (rig[k] for k in ('mn', 'cell', 'dims', 'unit', 'keep_front', 'ox', 'oz'))
w, h, l = dims
f = 1 if keep_front else -1
s = unit / cell
# S: ゲーム座標 -> モデル座標（アフィン）
A = [f * s, s, f * s]


def to_bb(p):
    x, y, z = ((p[a] - mn[a]) / cell for a in range(3))
    if not keep_front:
        x, z = w - x, l - z
    return [(x + ox) * unit, y * unit, (z + oz) * unit]


c0 = to_bb((0, 0, 0))
S4 = [[A[0], 0, 0, c0[0]], [0, A[1], 0, c0[1]], [0, 0, A[2], c0[2]], [0, 0, 0, 1]]
S4i = [[1 / A[0], 0, 0, -c0[0] / A[0]], [0, 1 / A[1], 0, -c0[1] / A[1]], [0, 0, 1 / A[2], -c0[2] / A[2]], [0, 0, 0, 1]]
W_rest = world_matrices(bones, 1.0)
prefix = os.path.splitext(os.path.basename(gmo_path))[0]


def sample(times, vals, frame):
    if frame <= times[0]:
        return list(vals[0])
    if frame >= times[-1]:
        return list(vals[-1])
    hi = next(i for i, t in enumerate(times) if t >= frame)
    lo = hi - 1
    u = (frame - times[lo]) / ((times[hi] - times[lo]) or 1)
    a, b = vals[lo], vals[hi]
    if len(a) == 4 and sum(x * y for x, y in zip(a, b)) < 0:
        b = [-c for c in b]
    r = [x + (y - x) * u for x, y in zip(a, b)]
    if len(r) == 4:
        n = math.sqrt(sum(c * c for c in r)) or 1
        r = [c / n for c in r]
    return r


expected_tests = []
for anim, sec in tests:
    mp = glob.glob(os.path.join(os.path.dirname(gmo_path), f'{prefix}_{anim}.GMO'))[0]
    mo = read_motion(mp)
    frame = sec * mo['rate']
    T = [list(b['t']) for b in bones]
    Q = [tuple(b['q']) for b in bones]
    for bone, cmd, fci in mo['channels']:
        _d, times, vals = mo['fcurves'][fci]
        if cmd == 0x48:
            T[bone] = sample(times, vals, frame)
        elif cmd == 0x4b:
            Q[bone] = tuple(sample(times, vals, frame))
    Wt = [None] * len(bones)

    def wt(i):
        if Wt[i] is None:
            loc = trs(T[i], Q[i])
            Wt[i] = loc if bones[i]['parent'] < 0 else mul(wt(bones[i]['parent']), loc)
        return Wt[i]
    D = {}
    for i, b in enumerate(bones):
        M = mul(wt(i), rigid_inv(W_rest[i]))
        D[b['name']] = [v for row in mul(mul(S4, M), S4i) for v in row]  # 行優先 16
    expected_tests.append(dict(anim=anim, sec=sec, D=D))

tag = uuid.uuid4().hex[:8]
body = r"""
(async () => {
  const out = {};
  try {
    Codecs.project.load(MODEL_T, { path: '', name: 'rig.bbmodel' });
    await new Promise(r => setTimeout(r, 4000));
    if (typeof Dialog !== 'undefined' && Dialog.open) { Dialog.open.cancel(); await new Promise(r => setTimeout(r, 500)); }
    out.groups = Group.all.length; out.cubes = Cube.all.length; out.animations = Animation.all.map(a => a.name);
    let wrongBone = 0;
    for (const c of Cube.all) if (!c.parent || c.parent.name !== RIG_T.cube_bone[c.name]) wrongBone++;
    out.cubes_in_wrong_bone = wrongBone;
    // 静止姿勢の全頂点（ワールド）
    Project.model_3d.updateMatrixWorld(true);
    const rest = Cube.all.map(c => {
      const pos = c.mesh.geometry.attributes.position, M = c.mesh.matrixWorld, arr = [];
      for (let i = 0; i < pos.count; i++) { const v = new THREE.Vector3(pos.getX(i), pos.getY(i), pos.getZ(i)).applyMatrix4(M); arr.push([v.x, v.y, v.z]); }
      return arr;
    });
    Modes.options.animate.select();
    await new Promise(r => setTimeout(r, 500));
    out.tests = [];
    for (const T of TESTS_T) {
      const an = Animation.all.find(a => a.name === T.anim);
      if (!an) { out.tests.push({ anim: T.anim, error: 'no animation' }); continue; }
      an.select();
      await new Promise(r => setTimeout(r, 200));
      Timeline.setTime(T.sec);
      Animator.preview();
      Project.model_3d.updateMatrixWorld(true);
      // 重み付きの混合: M = Σ w D_b（元のなめらかな変形＝スキニング）
      const blendOf = wts => { const M = new Array(16).fill(0); for (const [bn, wv] of Object.entries(wts)) { const Db = T.D[bn]; for (let k = 0; k < 16; k++) M[k] += wv * Db[k]; } return M; };
      const apply = (Dm, r) => [0, 1, 2].map(k => Dm[k * 4] * r[0] + Dm[k * 4 + 1] * r[1] + Dm[k * 4 + 2] * r[2] + Dm[k * 4 + 3]);
      let worst = 0, worstBone = '', worstBlend = 0, worstBlendBone = '', moved = 0, n = 0;
      const skinErr = [];
      Cube.all.forEach((c, ci) => {
        const g = c.parent.name;
        const isBlend = !T.D[g];
        const Dm = isBlend ? blendOf(RIG_T.blend_weights[g]) : T.D[g];
        const Ds = RIG_T.plate_weights && RIG_T.plate_weights[c.name] ? blendOf(RIG_T.plate_weights[c.name]) : null;
        const pos = c.mesh.geometry.attributes.position, M = c.mesh.matrixWorld;
        for (let i = 0; i < pos.count; i++) {
          const v = new THREE.Vector3(pos.getX(i), pos.getY(i), pos.getZ(i)).applyMatrix4(M);
          const r = rest[ci][i];
          const e = apply(Dm, r);
          const d = Math.hypot(v.x - e[0], v.y - e[1], v.z - e[2]);
          if (Math.hypot(v.x - r[0], v.y - r[1], v.z - r[2]) > 1) moved++;
          n++;
          if (isBlend) { if (d > worstBlend) { worstBlend = d; worstBlendBone = g; } }
          else if (d > worst) { worst = d; worstBone = g; }
          if (Ds) { const es = apply(Ds, r); skinErr.push(Math.hypot(v.x - es[0], v.y - es[1], v.z - es[2])); }
        }
      });
      skinErr.sort((a, b) => a - b);
      const pct = p => skinErr.length ? +skinErr[Math.min(skinErr.length - 1, Math.floor(p * skinErr.length))].toFixed(2) : null;
      out.tests.push({ anim: T.anim, sec: T.sec, vertices: n, moved_vertices: moved, max_error: +worst.toFixed(3), worst_bone: worstBone,
                       blend_max_error: +worstBlend.toFixed(2), blend_worst: worstBlendBone,
                       plate_skin_p50: pct(0.5), plate_skin_p95: pct(0.95), plate_skin_max: pct(1.0) });
    }
    // Bedrock アニメの書き出し（GeckoLib が読む animation.json の中身）
    const anims = {};
    for (const a of Animation.all) anims['animation.' + NAME_T + '.' + a.name.toLowerCase()] = a.compileBedrockAnimation();
    out.animation_file = { format_version: '1.8.0', animations: anims };
    // geo.json の比較（骨ごと、数値は許容誤差つき）
    Modes.options.edit.select();
    await new Promise(r => setTimeout(r, 300));
    const bbgeo = JSON.parse(Codecs.bedrock.compile({}))['minecraft:geometry'][0];
    const mine = GEO_T['minecraft:geometry'][0];
    const close = (a, b) => {
      if (typeof a === 'number' && typeof b === 'number') return Math.abs(a - b) < 0.002;
      if (Array.isArray(a) && Array.isArray(b)) return a.length === b.length && a.every((v, i) => close(v, b[i]));
      if (a && b && typeof a === 'object' && typeof b === 'object') { const ka = Object.keys(a).sort(), kb = Object.keys(b).sort(); return ka.length === kb.length && ka.every((k, i) => k === kb[i] && close(a[k], b[k])); }
      return a === b;
    };
    const byName = new Map(bbgeo.bones.map(b => [b.name, b]));
    let diff = 0; const firstDiff = [];
    for (const b of mine.bones) { const o = byName.get(b.name); if (!close(o, b)) { diff++; if (firstDiff.length < 1) firstDiff.push({ name: b.name, bb_keys: o && Object.keys(o), mine_keys: Object.keys(b), bb_pivot: o && o.pivot, mine_pivot: b.pivot, bb_cubes: o && o.cubes && o.cubes.length, mine_cubes: b.cubes && b.cubes.length }); } }
    out.geo_bones_bb = bbgeo.bones.length; out.geo_bones_mine = mine.bones.length; out.geo_bones_different = diff; out.geo_first_diff = firstDiff;
  } catch (e) { out.error = String(e && e.stack || e).slice(0, 1500); }
  return out;
})()
"""
name = json.load(open(bb, encoding='utf-8'))['name']
body = (body.replace('MODEL_T', f'MODEL_{tag}').replace('GEO_T', f'GEO_{tag}').replace('RIG_T', f'RIG_{tag}')
        .replace('TESTS_T', f'TESTS_{tag}').replace('NAME_T', json.dumps(name)))
js = (f'var MODEL_{tag} = ' + open(bb, encoding='utf-8').read() + ';\n'
      f'var GEO_{tag} = ' + open(geo, encoding='utf-8').read() + ';\n'
      f'var RIG_{tag} = ' + json.dumps(rig) + ';\n'
      f'var TESTS_{tag} = ' + json.dumps(expected_tests) + ';\n' + body)
open(out, 'w', encoding='utf-8').write(js)
print('wrote', out, len(js) // 1024, 'KB', 'tests', len(tests))
