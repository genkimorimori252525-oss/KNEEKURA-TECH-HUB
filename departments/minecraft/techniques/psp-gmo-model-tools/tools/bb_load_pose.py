"""Blockbench で .bbmodel を読み込み、指定アニメ・時刻の姿勢にしてカメラを置くJSを作る（見た目の比較用）。
使い方: python bb_load_pose.py <in.bbmodel> <アニメ名|rest> <秒> <camX,camY,camZ> <tgtX,tgtY,tgtZ> <out.js>
"""
import sys, uuid
bb, anim, sec, cam, tgt, out = sys.argv[1:7]
tag = uuid.uuid4().hex[:8]
body = r"""
(async () => {
  Codecs.project.load(MODEL_T, { path: '', name: 'pose.bbmodel' });
  await new Promise(r => setTimeout(r, 3000));
  if (typeof Dialog !== 'undefined' && Dialog.open) { Dialog.open.cancel(); await new Promise(r => setTimeout(r, 400)); }
  if ('ANIM' !== 'rest') {
    Modes.options.animate.select();
    await new Promise(r => setTimeout(r, 400));
    const an = Animation.all.find(a => a.name === 'ANIM');
    an.select();
    await new Promise(r => setTimeout(r, 200));
    Timeline.setTime(SEC);
    Animator.preview();
  }
  const pv = Preview.selected;
  pv.camera.position.set(CAM);
  pv.controls.target.set(TGT);
  pv.controls.update();
  Canvas.updateAll();
  if ('ANIM' !== 'rest') Animator.preview();
  // 窓が裏にあると requestAnimationFrame が止まり、画面が古い姿勢のまま撮れてしまう → 明示的に描く
  for (let i = 0; i < 3; i++) { pv.render(); await new Promise(r => setTimeout(r, 300)); }
  await new Promise(r => setTimeout(r, 800));
  return 'ok';
})()
""".replace('MODEL_T', f'MODEL_{tag}').replace('ANIM', anim).replace('SEC', sec).replace('CAM', cam).replace('TGT', tgt)
open(out, 'w', encoding='utf-8').write(f'var MODEL_{tag} = ' + open(bb, encoding='utf-8').read() + ';\n' + body)
print('wrote', out)
