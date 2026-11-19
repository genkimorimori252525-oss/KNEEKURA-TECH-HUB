"""4方向チェックポイント撮影（簡易・軽い）。モデルを変えるたびに、同じ4方向で撮って前回と比べ、
直した所以外を壊していないかを数値で確かめる。差が大きい向きだけ画像を見ればよい（トークン節約）。

使い方（Blockbench を --remote-debugging-port=<port> で起動しておく）:
  python bb_checkpoint.py <model.bbmodel> <出力フォルダ> [--anim IDLE_00 --sec 4.2] [--baseline <前回の出力フォルダ>]
                          [--port 9333] [--width 320] [--threshold 0.5]
出力: <出力フォルダ>/{front,back,left,right}.png（小さい画像）、sheet.png（4枚まとめ）、
      --baseline 指定時は diff.png（差の画素を赤く塗った 4 枚）と、向きごとの「差の画素の割合(%)」を1行ずつ表示。
カメラはモデルの外接箱から自動で決める（中心を見て、半径の 2.2 倍の距離。上から 20°）。
"""
import argparse, json, math, os, subprocess, sys, uuid
from PIL import Image, ImageChops, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
VIEWS = [('front', 0.0), ('right', 90.0), ('back', 180.0), ('left', 270.0)]  # 前 = -Z（エンティティの北）


def bbox_of(model):
    lo, hi = [1e18] * 3, [-1e18] * 3
    for e in model.get('elements', []):
        for k in ('from', 'to'):
            if k in e:
                for a in range(3):
                    lo[a] = min(lo[a], e[k][a])
                    hi[a] = max(hi[a], e[k][a])
    return lo, hi


def cdp(port, js_path, out_json, shot=None):
    args = ['node', os.path.join(HERE, 'bb_cdp.mjs'), str(port), js_path, out_json]
    if shot:
        args += ['--screenshot', shot]
    subprocess.run(args, check=True, stdout=subprocess.DEVNULL)
    with open(out_json, encoding='utf-8') as f:
        return json.load(f)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('model')
    ap.add_argument('outdir')
    ap.add_argument('--anim', default='rest')
    ap.add_argument('--sec', type=float, default=0.0)
    ap.add_argument('--baseline')
    ap.add_argument('--port', type=int, default=9333)
    ap.add_argument('--width', type=int, default=320)
    ap.add_argument('--threshold', type=float, default=0.1,
                    help='これ（%）を超えた向きに印を付ける。変えていない版どうしは 0.01% 以下（実測）なので、0.1% でも十分敏感')
    a = ap.parse_args()
    os.makedirs(a.outdir, exist_ok=True)
    text = open(a.model, encoding='utf-8').read()
    camf = os.path.join(a.baseline, 'camera.json') if a.baseline else None
    if camf and os.path.exists(camf):  # 比べるときは前回と全く同じカメラ（外接箱が少し違っても構図をずらさない）
        cam0 = json.load(open(camf, encoding='utf-8'))
        cen, rad = cam0['center'], cam0['radius']
    else:
        lo, hi = bbox_of(json.loads(text))
        cen = [(lo[i] + hi[i]) / 2 for i in range(3)]
        rad = max(hi[i] - lo[i] for i in range(3)) / 2
    with open(os.path.join(a.outdir, 'camera.json'), 'w', encoding='utf-8') as f:
        json.dump(dict(center=cen, radius=rad), f)
    tag = uuid.uuid4().hex[:8]
    load_js = os.path.join(a.outdir, '_load.js')
    with open(load_js, 'w', encoding='utf-8') as f:
        f.write(f'var M_{tag} = {text};\n' + r"""
(async () => {
  const sleep = ms => new Promise(r => setTimeout(r, ms));
  Codecs.project.load(M_TAG, { path: '', name: 'checkpoint.bbmodel' });
  await sleep(3000);
  if (typeof Dialog !== 'undefined' && Dialog.open) { Dialog.open.cancel(); await sleep(400); }
  if ('ANIM' !== 'rest') {
    Modes.options.animate.select(); await sleep(400);
    Animation.all.find(x => x.name === 'ANIM').select(); await sleep(300);
    Timeline.setTime(SEC); Animator.preview();
  }
  const r = Preview.selected.canvas.getBoundingClientRect();
  return JSON.stringify({ x: r.x, y: r.y, w: r.width, h: r.height, dpr: window.devicePixelRatio });
})()
""".replace('M_TAG', f'M_{tag}').replace('ANIM', a.anim).replace('SEC', str(a.sec)))
    rect = cdp(a.port, load_js, os.path.join(a.outdir, '_load.json'))
    if isinstance(rect, str):
        rect = json.loads(rect)
    s = rect.get('dpr', 1) or 1
    box = tuple(int(round(v * s)) for v in (rect['x'], rect['y'], rect['x'] + rect['w'], rect['y'] + rect['h']))
    ims = {}
    for name, yaw in VIEWS:
        th, el = math.radians(yaw), math.radians(20)
        d = 2.2 * rad
        cam = [cen[0] + d * math.sin(th) * math.cos(el), cen[1] + d * math.sin(el), cen[2] - d * math.cos(th) * math.cos(el)]
        js = os.path.join(a.outdir, '_cam.js')
        with open(js, 'w', encoding='utf-8') as f:
            f.write(r"""(async () => {
  const pv = Preview.selected;
  pv.camera.position.set(%s); pv.controls.target.set(%s); pv.controls.update();
  if ('%s' !== 'rest') Animator.preview();
  for (let i = 0; i < 3; i++) { pv.render(); await new Promise(r => setTimeout(r, 250)); }
  return '"ok"';
})()""" % (','.join(f'{c:.3f}' for c in cam), ','.join(f'{c:.3f}' for c in cen), a.anim))
        shot = os.path.join(a.outdir, f'_{name}_full.png')
        cdp(a.port, js, os.path.join(a.outdir, '_cam.json'), shot)
        im = Image.open(shot).convert('RGB').crop(box)
        im = im.resize((a.width, max(1, round(im.height * a.width / im.width))))
        im.save(os.path.join(a.outdir, f'{name}.png'))
        os.remove(shot)
        ims[name] = im
    w, h = ims['front'].size
    sheet = Image.new('RGB', (w * 2 + 4, h * 2 + 4), (0, 0, 0))
    for i, (name, _) in enumerate(VIEWS):
        sheet.paste(ims[name], ((i % 2) * (w + 4), (i // 2) * (h + 4)))
    sheet.save(os.path.join(a.outdir, 'sheet.png'))
    if not a.baseline:
        print('checkpoint saved:', a.outdir)
        return
    diff_sheet = Image.new('RGB', sheet.size, (0, 0, 0))
    worst = 0.0
    for i, (name, _) in enumerate(VIEWS):
        base = Image.open(os.path.join(a.baseline, f'{name}.png')).convert('RGB').resize((w, h))
        d = ImageChops.difference(base.convert('L'), ims[name].convert('L')).point(lambda v: 255 if v > 40 else 0)
        pct = 100.0 * d.histogram()[255] / (w * h)  # d は 0/255 の2値
        worst = max(worst, pct)
        over = Image.blend(ims[name], Image.new('RGB', (w, h)), 0.6)
        over.paste(Image.new('RGB', (w, h), (255, 0, 0)), mask=d)
        ImageDraw.Draw(over).text((4, 2), f'{name} {pct:.2f}%', fill=(255, 255, 0))
        diff_sheet.paste(over, ((i % 2) * (w + 4), (i // 2) * (h + 4)))
        print(f'{name:5} diff {pct:5.2f}%' + ('  <- check' if pct > a.threshold else ''))  # 文字化けしないよう英字
    diff_sheet.save(os.path.join(a.outdir, 'diff.png'))
    print('diff sheet:', os.path.join(a.outdir, 'diff.png'), '(look only at marked views)' if worst > a.threshold else '(all views under threshold)')


if __name__ == '__main__':
    main()
