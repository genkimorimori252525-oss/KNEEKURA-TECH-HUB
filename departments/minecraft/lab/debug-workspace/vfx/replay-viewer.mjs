// RECORD_REPLAY viewer (PLAN §4.3, P2). A self-contained derived HTML file that steps through recorded
// frames, stops, and pins one frame for side-by-side comparison. It never re-simulates anything.
import { derivedArtifact } from '../evidence/visual-artifacts.mjs';
import { buildReplayIndex, validateFrameSequence } from './frame-sequence.mjs';
import { require } from './common.mjs';

const safeJson = value => JSON.stringify(value).replace(/</g, '\\u003c').replace(/>/g, '\\u003e').replace(/&/g, '\\u0026')
  .replace(/\u2028/g, '\\u2028').replace(/\u2029/g, '\\u2029');

export function replayViewerHtml(sequenceInput, options = {}) {
  const sequence = validateFrameSequence(sequenceInput);
  const index = buildReplayIndex(sequence, options);
  // Derived HTML lives at evidence/derived/visual/<hash>.html; raw frames at evidence/raw/visual/<hash>.png.
  const data = { sequenceId: sequence.sequenceId, origin: sequence.origin, status: index.status, restoration: index.restoration,
    effectId: sequence.fx.effectId, attackInstanceId: sequence.fx.attackInstanceId, fxInstanceId: sequence.fx.fxInstanceId,
    rows: index.rows.map(r => ({ ...r, src: r.imagePath ? `../../raw/visual/${r.imageHash}.png` : null })) };
  return `<!doctype html><html lang="ja"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Tank Frame Replay</title><style>
:root{--bg:#141921;--fg:#e8edf4;--muted:#8a94a8;--warn:#ffb86c;--line:#2a3140}
body{margin:0;background:var(--bg);color:var(--fg);font:14px/1.5 system-ui,sans-serif}
header,main{padding:12px 16px}header{border-bottom:1px solid var(--line)}
.banner{color:var(--warn);font-weight:600}.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(280px,1fr));gap:12px}
figure{margin:0;border:1px solid var(--line);padding:8px}img{max-width:100%;image-rendering:pixelated;display:block}
.missing{display:flex;align-items:center;justify-content:center;min-height:160px;color:var(--warn);border:1px dashed var(--warn)}
table{border-collapse:collapse;width:100%;font-variant-numeric:tabular-nums}td,th{border-bottom:1px solid var(--line);padding:2px 6px;text-align:left}
button{background:#232a36;color:var(--fg);border:1px solid var(--line);padding:4px 10px;border-radius:4px;cursor:pointer}
input[type=range]{width:100%}.flags{color:var(--warn)}
</style></head><body>
<header><div class="banner">RECORDED_IMAGE_REPLAY_NOT_WORLD_REWIND — 記録画像の再生です。ゲーム世界を巻き戻してはいません。</div>
<div id="meta"></div></header>
<main><div><button id="prev">◀ 前</button> <button id="play">▶ 再生</button> <button id="next">次 ▶</button> <button id="pin">この frame を比較に固定</button>
<input id="slider" type="range" min="0" value="0" aria-label="frame"></div>
<div class="grid"><figure><figcaption id="capCur"></figcaption><div id="cur"></div></figure><figure><figcaption id="capPin">比較: 未固定</figcaption><div id="pinned"></div></figure></div>
<table id="facts"></table></main>
<script id="data" type="application/json">${safeJson(data)}</script>
<script>
const D=JSON.parse(document.getElementById('data').textContent);let cur=0,pin=null,timer=null;
const el=id=>document.getElementById(id);const slider=el('slider');slider.max=D.rows.length-1;
el('meta').textContent='sequence '+D.sequenceId.slice(0,12)+' · origin '+D.origin+' · status '+D.status+' · restoration '+D.restoration+' · effect '+D.effectId+' · attack '+D.attackInstanceId;
function frame(target,row){target.replaceChildren();if(row.src){const img=new Image();img.src=row.src;img.alt='frame '+row.index;target.append(img);}else{const d=document.createElement('div');d.className='missing';d.textContent=row.status+' — 画像なし';target.append(d);}}
function caption(row){return '#'+row.index+' · serverTick '+row.serverTick+' · clientTick '+row.clientTick+' · renderFrame '+row.renderFrame+' · partial '+row.partialTick.toFixed(3)+(row.flags.length?' · ⚠ '+row.flags.join(', '):'');}
function show(i){cur=Math.max(0,Math.min(D.rows.length-1,i));slider.value=cur;const r=D.rows[cur];frame(el('cur'),r);el('capCur').textContent=caption(r);
 const rows=[['status',r.status],['VFX time',r.vfxTime.status+(r.vfxTime.ticks!==undefined?' '+r.vfxTime.ticks:'')],['client−server skew (ticks)',r.clientMinusServerTicks],['capture ms from start',r.captureMillisFromStart.toFixed(2)],['image sha256',r.imageHash||'NONE'],['flags',r.flags.join(', ')||'—']];
 if(pin!==null){const p=D.rows[pin];rows.push(['Δ serverTick vs pinned',r.serverTick-p.serverTick],['Δ renderFrame vs pinned',r.renderFrame-p.renderFrame]);}
 el('facts').replaceChildren(...rows.map(([k,v])=>{const tr=document.createElement('tr');const a=document.createElement('th');a.textContent=k;const b=document.createElement('td');b.textContent=String(v);if(k==='flags'&&r.flags.length)b.className='flags';tr.append(a,b);return tr;}));}
function stop(){clearInterval(timer);timer=null;el('play').textContent='▶ 再生';}
el('prev').onclick=()=>{stop();show(cur-1)};el('next').onclick=()=>{stop();show(cur+1)};slider.oninput=()=>{stop();show(+slider.value)};
el('play').onclick=()=>{if(timer){stop();return;}el('play').textContent='■ 停止';timer=setInterval(()=>{if(cur>=D.rows.length-1){stop();return;}show(cur+1)},100);};
el('pin').onclick=()=>{pin=cur;const r=D.rows[pin];frame(el('pinned'),r);el('capPin').textContent='比較: '+caption(r);show(cur);};
addEventListener('keydown',e=>{if(e.key==='ArrowLeft'){stop();show(cur-1)}else if(e.key==='ArrowRight'){stop();show(cur+1)}else if(e.key===' '){e.preventDefault();el('play').click()}});
show(0);
</script></body></html>`;
}

/** Package the viewer as a derived artifact bound to the sequence and its raw frames. */
export function replayViewerArtifact(sequenceInput, binding, options = {}) {
  const sequence = validateFrameSequence(sequenceInput);
  const present = sequence.frames.filter(f => f.status === 'PRESENT');
  require(present.length > 0, 'NO_PRESENT_FRAMES');
  return derivedArtifact(Buffer.from(replayViewerHtml(sequence, options), 'utf8'), {
    role: 'DERIVED_REPLAY_VIEWER', mediaType: 'text/html', extension: 'html',
    sourceObservationIds: present.map(f => f.sourceObservationId), rawSourceHashes: present.map(f => f.imageHash),
    binding, details: { sequenceId: sequence.sequenceId, semantics: 'RECORDED_IMAGE_REPLAY_NOT_WORLD_REWIND' } });
}
