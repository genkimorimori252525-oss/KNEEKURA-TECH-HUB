"""アニメに追従せず浮いて残るキューブの検査（Blockbench 実機の再生で測る）。

考え方: 静止姿勢で触れ合っているキューブどうしを「つながり」とし、各アニメ・各時刻で、つながりの2つの中心の距離が
静止時から threshold ブロック以上変わったら、そのつながりは切れたとみなす。静止時に本体（一番大きいまとまり）に
つながっていたのに、ある時刻で本体から切り離されたキューブを「浮き」として数える。
（回る歯車や、はためくスカートのように正しく大きく動く所は、隣と一緒に動くので数えない。）

使い方（Blockbench を --remote-debugging-port=<port> で起動しておく）:
  python bb_float_check.py <model.bbmodel> <out.json> [--samples 8] [--threshold 1.5] [--port 9333]
出力: アニメごとの「浮いたキューブの数（最大の時刻）」と、浮いたキューブ（名前・グループ・アニメ・時刻）の上位。
"""
import argparse, json, os, subprocess, uuid

HERE = os.path.dirname(os.path.abspath(__file__))

JS = r"""
(async () => {
  const sleep = ms => new Promise(r => setTimeout(r, ms));
  Codecs.project.load(M_TAG, { path: '', name: 'floatcheck.bbmodel' });
  await sleep(3000);
  if (typeof Dialog !== 'undefined' && Dialog.open) { Dialog.open.cancel(); await sleep(400); }
  const unit = __UNIT__, thr = __THR__ * unit, samples = __SAMPLES__;
  const cubes = Cube.all;
  const V = THREE.Vector3;
  function centers() {
    return cubes.map(c => {
      const b = new THREE.Box3().setFromObject(c.mesh);
      const v = new V(); b.getCenter(v); return v;
    });
  }
  function radii() {
    return cubes.map(c => { const b = new THREE.Box3().setFromObject(c.mesh); const s = new V(); b.getSize(s); return s.length() / 2; });
  }
  Modes.options.animate.select(); await sleep(400);
  Animator.showDefaultPose && Animator.showDefaultPose();
  Animation.all[0].select(); await sleep(200); Timeline.setTime(0);
  // 静止姿勢（アニメを外した姿勢）で隣接を作る
  Animation.selected && Animation.selected.unselect && Animation.selected.unselect();
  Animator.showDefaultPose && Animator.showDefaultPose();
  scene.updateMatrixWorld(true);
  const c0 = centers(), r0 = radii();
  const boxes = cubes.map(c => new THREE.Box3().setFromObject(c.mesh));
  // 空間ハッシュで近いものだけ調べる
  const cellSz = 4 * unit, grid = new Map();
  const key = (x, y, z) => x + ',' + y + ',' + z;
  c0.forEach((c, i) => { const k = key(Math.floor(c.x / cellSz), Math.floor(c.y / cellSz), Math.floor(c.z / cellSz)); if (!grid.has(k)) grid.set(k, []); grid.get(k).push(i); });
  const edges = [];
  c0.forEach((c, i) => {
    const gx = Math.floor(c.x / cellSz), gy = Math.floor(c.y / cellSz), gz = Math.floor(c.z / cellSz);
    const span = Math.ceil((r0[i] + 0.5 * unit) / cellSz) + 1;
    for (let x = gx - span; x <= gx + span; x++) for (let y = gy - span; y <= gy + span; y++) for (let z = gz - span; z <= gz + span; z++) {
      const l = grid.get(key(x, y, z)); if (!l) continue;
      for (const j of l) if (j > i) {
        // 箱どうしの近さ（それぞれの箱を中心から半径の球と見なすと甘すぎるので、軸並びの箱で判定）
        const bi = boxes[i].clone().expandByScalar(0.25 * unit);
        if (bi.intersectsBox(boxes[j])) edges.push([i, j, c.distanceTo(c0[j])]);
      }
    }
  });
  const n = cubes.length;
  function components(alive) {
    const parent = Array.from({ length: n }, (_, i) => i);
    const find = i => { while (parent[i] !== i) { parent[i] = parent[parent[i]]; i = parent[i]; } return i; };
    edges.forEach(([i, j], e) => { if (alive[e]) { const a = find(i), b = find(j); if (a !== b) parent[a] = b; } });
    const size = new Map(); for (let i = 0; i < n; i++) { const r = find(i); size.set(r, (size.get(r) || 0) + 1); }
    let main = -1, best = -1; size.forEach((s, r) => { if (s > best) { best = s; main = r; } });
    const inMain = Array.from({ length: n }, (_, i) => find(i) === main);
    inMain.compSize = Array.from({ length: n }, (_, i) => size.get(find(i)));
    return inMain;
  }
  const restMain = components(edges.map(() => true));
  const report = { cubes: n, edges: edges.length, in_main_at_rest: restMain.filter(x => x).length, anims: [], worst: [] };
  const hits = new Map();
  for (const an of Animation.all) {
    an.select(); await sleep(150);
    let worstCount = 0, worstT = 0;
    for (let s = 0; s < samples; s++) {
      const t = an.length * (s + 0.5) / samples;
      Timeline.setTime(t); Animator.preview(); scene.updateMatrixWorld(true);
      const c = centers();
      const alive = edges.map(([i, j, d0]) => Math.abs(c[i].distanceTo(c[j]) - d0) < thr);
      const main = components(alive);
      let cnt = 0;
      // 同じグループ（骨）のうち本体から離れた割合。グループごと離れる（≥ 半分）なら部品そのものの正しい動き
      const gTot = new Map(), gOff = new Map();
      for (let i = 0; i < n; i++) {
        const g = cubes[i].parent && cubes[i].parent.name;
        gTot.set(g, (gTot.get(g) || 0) + 1);
        if (restMain[i] && !main[i]) gOff.set(g, (gOff.get(g) || 0) + 1);
      }
      // 浮き = 本体から切り離された「小さいまとまり」（SMALL 個以下）で、しかも自分のグループの大半は本体に残っているもの
      // （= 1 つだけ取り残された／ちぎれたブロック。歯車ごと飛ぶ・部品ごと離れるのは数えない）
      for (let i = 0; i < n; i++) if (restMain[i] && !main[i] && main.compSize[i] <= __SMALL__) {
        const g = cubes[i].parent && cubes[i].parent.name;
        if ((gOff.get(g) || 0) / gTot.get(g) >= 0.5) continue;
        cnt++;
        // 本体からどれだけ離れたか: 静止時に隣だった本体側のキューブとの距離の変化の最大
        let off = 0;
        edges.forEach(([a, b, d0], e) => { if ((a === i && main[b]) || (b === i && main[a])) off = Math.max(off, Math.abs(c[a].distanceTo(c[b]) - d0)); });
        const prev = hits.get(i);
        if (!prev || off > prev.off) hits.set(i, { off, anim: an.name, t: +t.toFixed(2) });
      }
      if (cnt > worstCount) { worstCount = cnt; worstT = t; }
    }
    report.anims.push({ anim: an.name, floating_max: worstCount, at: +worstT.toFixed(2) });
  }
  report.floating_total = hits.size;
  report.by_group = {};
  hits.forEach((h, i) => { const g = cubes[i].parent && cubes[i].parent.name; report.by_group[g] = (report.by_group[g] || 0) + 1; });
  report.worst = [...hits.entries()].sort((a, b) => b[1].off - a[1].off).slice(0, 15)
    .map(([i, h]) => ({ cube: cubes[i].name, group: cubes[i].parent && cubes[i].parent.name, blocks: +(h.off / unit).toFixed(2), anim: h.anim, t: h.t }));
  return JSON.stringify(report);
})()
"""


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('model')
    ap.add_argument('out')
    ap.add_argument('--samples', type=int, default=8, help='アニメごとの時刻の数')
    ap.add_argument('--threshold', type=float, default=1.5, help='つながりが切れたとみなす距離の変化（ブロック）')
    ap.add_argument('--small', type=int, default=20, help='これ以下の個数で本体から切り離されたまとまりを浮きとする')
    ap.add_argument('--unit', type=float, default=16.0)
    ap.add_argument('--port', type=int, default=9333)
    a = ap.parse_args()
    tag = uuid.uuid4().hex[:8]
    js = os.path.splitext(a.out)[0] + '.js'
    with open(js, 'w', encoding='utf-8') as f:
        f.write(f'var M_{tag} = ' + open(a.model, encoding='utf-8').read() + ';\n' +
                JS.replace('M_TAG', f'M_{tag}').replace('__UNIT__', str(a.unit)).replace('__THR__', str(a.threshold))
                  .replace('__SAMPLES__', str(a.samples)).replace('__SMALL__', str(a.small)))
    subprocess.run(['node', os.path.join(HERE, 'bb_cdp.mjs'), str(a.port), js, a.out], check=True, stdout=subprocess.DEVNULL)
    rep = json.load(open(a.out, encoding='utf-8'))
    print(f"cubes {rep['cubes']}  edges {rep['edges']}  in main body at rest {rep['in_main_at_rest']}  floating (any time) {rep['floating_total']}")
    print('  by group:', rep.get('by_group'))
    for r in rep['anims']:
        print(f"  {r['anim']:12} floating max {r['floating_max']:4}  at {r['at']}s")
    for w in rep['worst'][:8]:
        print(f"  worst: {w['cube']} ({w['group']}) {w['blocks']} blocks  {w['anim']} {w['t']}s")


if __name__ == '__main__':
    main()
