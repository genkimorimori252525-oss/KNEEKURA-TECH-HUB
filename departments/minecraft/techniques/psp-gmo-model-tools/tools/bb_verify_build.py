"""Blockbench実機検証用のJSを組み立てる。
使い方: python bb_verify_build.py <model.gmo> <model.bbmodel> <scale> <out.js> [pose]
  pose: none | shoulder (右肩を回して変形を確認)
"""
import json, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gmo
from gmo2gltf import read_bones, world_matrices

gmo_path, bb_path, scale, out_js = sys.argv[1], sys.argv[2], float(sys.argv[3]), sys.argv[4]
pose = sys.argv[5] if len(sys.argv) > 5 else 'none'
model = gmo.parse(open(gmo_path, 'rb').read())[0].children[0]
bones = read_bones(model)
W = world_matrices(bones, scale)
expected = {b['name']: [W[i][0][3], W[i][1][3], W[i][2][3]] for i, b in enumerate(bones)}
anim_name, anim_sec = None, 0.0
if pose.startswith('anim:'):
    # 元データ(float16のfカーブ)から独立に、指定時刻の各骨ワールド位置を計算する
    import glob, math
    from gmo2gltf import read_motion, trs, mul
    _, anim_name, sec = pose.split(':')
    anim_sec = float(sec)
    mp = glob.glob(os.path.join(os.path.dirname(gmo_path), '*_' + anim_name + '.GMO'))[0]
    mo = read_motion(mp)
    frame = anim_sec * mo['rate']

    def sample(times, vals):
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
    T = [list(b['t']) for b in bones]
    Q = [tuple(b['q']) for b in bones]
    for bone, cmd, fci in mo['channels']:
        _d, times, vals = mo['fcurves'][fci]
        if cmd == 0x48:
            T[bone] = sample(times, vals)
        elif cmd == 0x4b:
            Q[bone] = tuple(sample(times, vals))
    Wa = [None] * len(bones)

    def wa(i):
        if Wa[i] is None:
            loc = trs([c * scale for c in T[i]], Q[i])
            Wa[i] = loc if bones[i]['parent'] < 0 else mul(wa(bones[i]['parent']), loc)
        return Wa[i]
    expected = {b['name']: [wa(i)[0][3], wa(i)[1][3], wa(i)[2][3]] for i, b in enumerate(bones)}
doc = open(bb_path, encoding='utf-8').read()

body = r"""
(async () => {
  const out = {};
  try {
    Codecs.project.load(MODEL, { path: '', name: 'model.bbmodel' });
    await new Promise(r => setTimeout(r, 2500));
    // API経由の読み込みではプロジェクト設定ダイアログが開くので閉じる
    if (typeof Dialog !== 'undefined' && Dialog.open) { out.closed_dialog = true; Dialog.open.cancel(); await new Promise(r => setTimeout(r, 500)); }
    out.format = Format && Format.id;
    out.armatures = Armature.all.length;
    out.bones = ArmatureBone.all.length;
    out.meshes = Mesh.all.length;
    out.textures = Texture.all.length;
    out.faces = Mesh.all.reduce((n, m) => n + Object.keys(m.faces).length, 0);
    out.verts = Mesh.all.reduce((n, m) => n + Object.keys(m.vertices).length, 0);
    // 骨のワールド位置を期待値と比較
    let worst = 0, worstName = '';
    for (const b of ArmatureBone.all) {
      const w = b.getWorldCenter();
      const e = EXPECTED[b.name];
      if (!e) { out.unknown_bone = (out.unknown_bone || []).concat(b.name); continue; }
      const d = Math.hypot(w.x - e[0], w.y - e[1], w.z - e[2]);
      if (d > worst) { worst = d; worstName = b.name; }
    }
    out.bone_world_max_error = +worst.toFixed(4); out.bone_world_worst = worstName;
    // ウェイト
    let weighted = 0;
    for (const b of ArmatureBone.all) weighted += Object.keys(b.vertex_weights).length;
    out.weight_entries = weighted;
    // カメラ
    const pv = Preview.selected;
    const cx = 0, cy = 170, cz = 0;
    // 紋様の円盤(TR_pattern*)は大きく視界を塞ぐので隠す
    for (const m of Mesh.all) if (/^TR_pattern/.test(m.name)) { m.visibility = false; }
    Canvas.updateAll();
    pv.camera.position.set(750, 330, 1050);
    pv.controls.target.set(cx, cy, cz);
    pv.controls.update();
    POSE_CODE
    Canvas.updateAll();
    await new Promise(r => setTimeout(r, 1200));
  } catch (e) { out.error = String(e && e.stack || e).slice(0, 1500); }
  return out;
})()
"""
pose_code = ''
if pose == 'shoulder':
    pose_code = """
    const sh = ArmatureBone.all.find(b => b.name === 'shoulder_R');
    const el = ArmatureBone.all.find(b => b.name === 'elbow_R');
    out.pose = 'shoulder_R rot z=+50, elbow_R rot z=-40';
    // 骨そのものを回すのではなく、アニメーションと同じ経路(preview_controller)で姿勢だけ変える
    sh.rotation[2] += 50; el.rotation[2] -= 40;
    Canvas.updateView({ elements: [sh, el], element_aspects: { transform: true } });
    """
if anim_name:
    # アニメを再生して、全骨のワールド位置を期待値と比較する（rest比較は上のコードがすでに済み）
    pose_code = """
    out.anim_names = Animation.all.map(a => a.name);
    const AN = Animation.all.find(a => a.name === 'ANIM_NAME');
    out.anim_found = !!AN;
    if (AN) {
      Modes.options.animate.select();
      await new Promise(r => setTimeout(r, 500));
      AN.select();
      await new Promise(r => setTimeout(r, 300));
      Timeline.setTime(ANIM_SEC);
      Animator.preview();
      Project.model_3d.updateMatrixWorld(true);
      let worst2 = 0, worstName2 = '', moved = 0, rows = [];
      for (const b of ArmatureBone.all) {
        const w = b.getWorldCenter();
        const e = EXPECTED_ANIM[b.name];
        const d = Math.hypot(w.x - e[0], w.y - e[1], w.z - e[2]);
        if (d > worst2) { worst2 = d; worstName2 = b.name; }
        const r = EXPECTED_REST[b.name];
        if (Math.hypot(e[0] - r[0], e[1] - r[1], e[2] - r[2]) > 0.5) moved++;
      }
      out.anim_world_max_error = +worst2.toFixed(4); out.anim_worst_bone = worstName2;
      out.bones_displaced_vs_rest = moved;
      out.time = Timeline.time; out.anim_length = AN.length; out.anim_animators = Object.keys(AN.animators).length;
    }
    """.replace('ANIM_NAME', anim_name).replace('ANIM_SEC', str(anim_sec))
body = body.replace('POSE_CODE', pose_code)
# 同じページで何度評価しても再宣言エラーにならないよう、実行ごとに変数名を変える
import uuid
tag = uuid.uuid4().hex[:8]
body = body.replace('MODEL', 'MODEL_' + tag).replace('EXPECTED', 'EXPECTED_' + tag)
rest_expected = {b['name']: [W[i][0][3], W[i][1][3], W[i][2][3]] for i, b in enumerate(bones)}
# 上の置換で本文中の EXPECTED_ANIM / EXPECTED_REST は EXPECTED_<tag>_ANIM / EXPECTED_<tag>_REST になっている
js = (f'var MODEL_{tag} = ' + doc + f';\nvar EXPECTED_{tag} = ' + json.dumps(rest_expected) + ';\n'
      + f'var EXPECTED_{tag}_ANIM = ' + json.dumps(expected) + f';\nvar EXPECTED_{tag}_REST = ' + json.dumps(rest_expected) + ';\n' + body)
open(out_js, 'w', encoding='utf-8').write(js)
print('wrote', out_js, len(js) // 1024, 'KB')
