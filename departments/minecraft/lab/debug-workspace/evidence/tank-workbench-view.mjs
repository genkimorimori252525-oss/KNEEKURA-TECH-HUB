import {randomBytes} from 'node:crypto';
import {realpath,writeFile} from 'node:fs/promises';
import path from 'node:path';
import {traceAgeStyle} from '../../simlab/trace-age-style.mjs';
import {requireTankIdentity,sameTankIdentity,boundedTankPacket} from './tank-contract.mjs';

/** Deduplicated immutable object table: cursor packets refer to shared samples/facts/layers. */
export function packTankWorkbenchData({status,preflight=null,cursorPackets,map,experiment=null,comparison=null,cursorSelection=null}) {
  requireTankIdentity(status?.identity);
  if(!Array.isArray(cursorPackets)||!cursorPackets.length||cursorPackets.length>256)throw new RangeError('TANK_WORKBENCH_CURSOR_LIMIT');
  for(const p of cursorPackets) {
    if(p?.schema!=='kneekura.cursor-decision/v1'||!sameTankIdentity(p.identity,status.identity))throw new TypeError('WORKBENCH_IDENTITY_MISMATCH');
    if(p.identity.subjectUuid!==cursorPackets[0].identity.subjectUuid||p.identity.targetRevision!==cursorPackets[0].identity.targetRevision)throw new TypeError('WORKBENCH_SUBJECT_SELECTION_IDENTITY_MISMATCH');
    if(p.dimension!=null&&p.dimension!=='minecraft:overworld')throw new TypeError('TANK_MAP_DIMENSION_MISMATCH');
    boundedTankPacket(p);
  }
  for(const item of [preflight,map,experiment])if(item&&(!item.identity||!sameTankIdentity(item.identity,status.identity)))throw new TypeError('WORKBENCH_IDENTITY_MISMATCH');
  if(experiment&&(experiment.identity.subjectUuid!==cursorPackets[0].identity.subjectUuid||experiment.identity.targetRevision!==cursorPackets[0].identity.targetRevision))throw new TypeError('WORKBENCH_EXPERIMENT_SUBJECT_MISMATCH');
  if(comparison&&!sameTankIdentity(comparison.before,status.identity)&&!sameTankIdentity(comparison.after,status.identity))throw new TypeError('WORKBENCH_COMPARISON_IDENTITY_MISMATCH');
  const nodes=[],intern=new Map();
  function encode(value,depth=0) {
    if(depth>64)throw new RangeError('TANK_WORKBENCH_NESTING_LIMIT');
    if(value===null||typeof value!=='object')return value;
    const key=JSON.stringify(value);
    if(intern.has(key))return {ref:intern.get(key)};
    const id=nodes.length;intern.set(key,id);nodes.push(null);
    if(nodes.length>50000)throw new RangeError('TANK_WORKBENCH_NODE_LIMIT');
    nodes[id]=Array.isArray(value)?['array',value.map(v=>encode(v,depth+1))]
      :['object',Object.entries(value).map(([k,v])=>[k,encode(v,depth+1)])];
    return {ref:id};
  }
  const roots={status:encode(status),preflight:encode(preflight),map:encode(map),experiment:encode(experiment),comparison:encode(comparison),
    cursorPackets:cursorPackets.map(p=>encode(p))};
  return boundedTankPacket({schema:'kneekura.tank-workbench-data/v1',nodes,roots,
    cursorSelection:cursorSelection??{eligibleCount:null,displayedCount:cursorPackets.length,omittedCount:null,selectionPolicy:'EXPLICIT_CURSOR_PACKETS_NOT_CONTINUOUS_COVERAGE'}});
}

export async function writeTankWorkbenchArtifact(input,output,runDir) {
  const file=path.resolve(output),parent=await realpath(path.dirname(file)),run=await realpath(runDir),resolved=path.join(parent,path.basename(file));
  const relative=path.relative(run,resolved);
  if(relative===''||(!relative.startsWith('..'+path.sep)&&relative!=='..'&&!path.isAbsolute(relative)))throw new Error('TANK_VIEW_OUTPUT_MUST_BE_OUTSIDE_RETAINED_RUN');
  await writeFile(resolved,renderTankWorkbenchHtml(input),{encoding:'utf8',flag:'wx'});return resolved;
}

export function renderTankWorkbenchHtml(input) {
  const packet=packTankWorkbenchData(input),nonce=randomBytes(18).toString('base64');
  const data=JSON.stringify(packet).replace(/</g,'\\u003c').replace(/\u2028/g,'\\u2028').replace(/\u2029/g,'\\u2029');
  return `<!doctype html><html lang="ja"><meta charset="utf-8"><meta name="viewport" content="width=device-width">
<meta http-equiv="Content-Security-Policy" content="default-src 'none'; script-src 'nonce-${nonce}'; style-src 'nonce-${nonce}'; img-src data:; base-uri 'none'; form-action 'none'">
<title>水槽の実験状況と証拠</title><style nonce="${nonce}">
body{background:#101923;color:#e7edf3;font:15px system-ui;margin:24px}h1{font-size:24px}main{display:grid;grid-template-columns:minmax(320px,1fr) minmax(320px,1fr);gap:20px}
section{background:#182533;border:1px solid #3b4c5f;padding:16px;border-radius:8px}select,input,button{font:inherit;background:#263748;color:#e7edf3;border:1px solid #668096;padding:5px;margin:4px}canvas{display:block;background:#111c27;max-width:100%;height:auto}
pre{white-space:pre-wrap;overflow-wrap:anywhere;font-size:12px}label{display:inline-block;margin-right:10px}.muted{color:#b2c1cf}details{margin-top:12px}@media(max-width:900px){main{grid-template-columns:1fr}}
</style><h1>水槽の実験状況と証拠</h1><p class="muted">保存済みの観測を読む派生表示。元画像・連続取得・原因の証明とは別です。</p>
<section><div id="status"></div><div id="identity" class="muted"></div><details><summary>水槽の確認票・由来</summary><pre id="statusDetail"></pre></details></section>
<p><label>時刻 <input type="range" id="cursor" min="0" max="0" value="0"><output id="tick"></output></label>
<label>概要 <select id="overviewMode"><option value="CURSOR">cursor時点</option><option value="WINDOW_END">区間末尾の概要</option></select></label>
<label>図 <select id="projection"><option>PLAN_XZ</option><option>ELEVATION</option></select></label></p>
<p id="selection" class="muted"></p><p><label><input type="checkbox" id="motion">実移動</label><label><input type="checkbox" id="projectiles">関連弾</label>
<label><input type="checkbox" id="declared">宣言された経路</label><label><input type="checkbox" id="returned">検索から返されたPath</label><label><input type="checkbox" id="cache">検索cache（点）</label></p>
<main><section><h2>固定座標の図</h2><p id="mapInfo" class="muted"></p><canvas id="canvas" width="960" height="960"></canvas><p id="quality"></p></section>
<section><h2 id="overviewTitle">Decision</h2><div id="stages"></div><details><summary>現在のpacketと証拠参照</summary><pre id="packet"></pre></details></section></main>
<section><h2>実験・比較</h2><pre id="experiment"></pre></section>
<script type="application/json" id="data" nonce="${nonce}">${data}</script><script nonce="${nonce}">
const data=JSON.parse(document.getElementById('data').textContent),cache=new Map(),byId=id=>document.getElementById(id);
function decode(value){if(!value||typeof value!=='object')return value;const id=value.ref;if(cache.has(id))return cache.get(id);const [kind,entries]=data.nodes[id];const result=kind==='array'?entries.map(decode):Object.fromEntries(entries.map(([k,v])=>[k,decode(v)]));cache.set(id,result);return result;}
const p=Object.fromEntries(Object.entries(data.roots).map(([k,v])=>[k,k==='cursorPackets'?v.map(decode):decode(v)]));
const style=${traceAgeStyle.toString()};
const packets=p.cursorPackets.toSorted((a,b)=>a.cursorTick-b.cursorTick),cursor=byId('cursor'),canvas=byId('canvas'),ctx=canvas.getContext('2d');
cursor.max=packets.length-1;cursor.value=packets.length-1;
byId('status').textContent='開始前確認：'+(p.preflight?.status??'未確認')+' / 表示記録：'+(p.status.presentation?.reason??'未取得')+' / 画像の可視性は別途確認';
byId('identity').textContent='run '+p.status.identity.runId+' / Arena '+p.status.identity.arenaEpoch+' / 対象 '+packets[0].identity.subjectUuid+' / 選択revision '+packets[0].identity.targetRevision;
byId('statusDetail').textContent=JSON.stringify({status:p.status,preflight:p.preflight},null,2);
byId('experiment').textContent=JSON.stringify({experiment:p.experiment,comparison:p.comparison},null,2);
function point(pos,packet){const g=p.map?.geometry,v=p.map?.viewport;if(!g||!v)return null;return byId('projection').value==='ELEVATION'
 ?[v.margin+(pos.tick-packet.window.startTick)*2,v.margin+(g.y+g.height-pos.y)*v.pixelsPerBlock]
 :[v.margin+(pos.x-g.x)*v.pixelsPerBlock,v.margin+(pos.z-g.z)*v.pixelsPerBlock];}
function dot(pos,packet,color,r=3){const xy=point(pos,packet);if(!xy)return;ctx.fillStyle=color;ctx.beginPath();ctx.arc(xy[0],xy[1],r,0,Math.PI*2);ctx.fill();}
function trace(trace,packet,projectile=false){const index=new Map(trace.samples.map(s=>[s.sample_id,s]));ctx.lineWidth=projectile?3:2;ctx.setLineDash(projectile?[7,4]:[]);
 for(const edge of trace.segments){const a=index.get(edge.from_sample_id),b=index.get(edge.to_sample_id);if(!a||!b)continue;const color=style({traceClass:projectile?'PROJECTILE_ACTUAL':'MOB_ACTUAL',identity:trace.subject.id,sampleTick:b.tick,currentTick:packet.cursorTick});if(!color)continue;
 const x=point(a,packet),y=point(b,packet);if(!x||!y)continue;ctx.strokeStyle=color.color;ctx.globalAlpha=color.alpha;ctx.beginPath();ctx.moveTo(...x);ctx.lineTo(...y);ctx.stroke();}
 ctx.globalAlpha=1;ctx.setLineDash([]);for(const s of trace.samples){const color=style({traceClass:projectile?'PROJECTILE_ACTUAL':'MOB_ACTUAL',identity:trace.subject.id,sampleTick:s.tick,currentTick:packet.cursorTick});if(color){ctx.globalAlpha=color.alpha;dot(s,packet,color.color,projectile?4:2);}}ctx.globalAlpha=1;}
function pathLayer(layer,packet,color,connect){if(layer?.tick>packet.cursorTick)return;const nodes=layer?.nodes??[];ctx.strokeStyle=color;ctx.setLineDash([5,5]);ctx.lineWidth=1;
 for(let i=0;i<nodes.length;i++){const n={...nodes[i],tick:layer.tick};dot(n,packet,color,3);if(!connect||i===0||nodes[i].index!==nodes[i-1].index+1)continue;const a=point({...nodes[i-1],tick:layer.tick},packet),b=point(n,packet);if(a&&b){ctx.beginPath();ctx.moveTo(...a);ctx.lineTo(...b);ctx.stroke();}}ctx.setLineDash([]);}
function draw(){const packet=packets[Number(cursor.value)],latest=packets.at(-1),overviewPacket=byId('overviewMode').value==='WINDOW_END'?latest:packet;
 byId('tick').textContent=packet.cursorTick;byId('overviewTitle').textContent=(overviewPacket===packet?'cursor時点':'区間末尾の概要')+'：tick '+overviewPacket.cursorTick;
 const selected=packet.displaySelection.motion;byId('selection').textContent='cursor表示 '+packets.length+'時点 / 対象 '+(data.cursorSelection.eligibleCount??'不明')+' / 省略 '+(data.cursorSelection.omittedCount??'不明')+'（連続取得ではありません） / 実移動 '+selected.displayedCount+' / 対象 '+selected.eligibleCount+' / 省略 '+selected.omittedCount;
 byId('packet').textContent=JSON.stringify(packet,null,2);byId('stages').replaceChildren();
 for(const [name,stage] of Object.entries(overviewPacket.overview.stages)){const box=document.createElement('details'),title=document.createElement('summary'),text=document.createElement('pre');title.textContent=name+' / '+stage.status; text.textContent=JSON.stringify(stage,null,2);box.append(title,text);byId('stages').append(box);}
 ctx.clearRect(0,0,canvas.width,canvas.height);const g=p.map?.geometry,v=p.map?.viewport;
 if(!g||!v){byId('mapInfo').textContent='水槽のgeometry未取得。座標枠は生成しません。';return;}
 canvas.width=v.width;canvas.height=v.height;ctx.strokeStyle='#334657';ctx.lineWidth=1;
 const elevation=byId('projection').value==='ELEVATION';byId('mapInfo').textContent=elevation?'横：元tick / 縦：y（高度）':'北 ↑ −Z / 横 +X / 縦 +Z / 固定 '+v.pixelsPerBlock+'px/ブロック';
 if(!elevation){for(let x=0;x<=g.width;x++){ctx.beginPath();ctx.moveTo(v.margin+x*v.pixelsPerBlock,v.margin);ctx.lineTo(v.margin+x*v.pixelsPerBlock,v.margin+g.depth*v.pixelsPerBlock);ctx.stroke();}for(let z=0;z<=g.depth;z++){ctx.beginPath();ctx.moveTo(v.margin,v.margin+z*v.pixelsPerBlock);ctx.lineTo(v.margin+g.width*v.pixelsPerBlock,v.margin+z*v.pixelsPerBlock);ctx.stroke();}}
 const layers=packet.layers;if(byId('motion').checked)trace(layers.motion.trace,packet);if(byId('projectiles').checked)for(const group of layers.relatedProjectiles.traces)trace(group.trace,packet,true);
 if(byId('declared').checked)pathLayer(layers.declaredNavigation,packet,'#efa4df',true);if(byId('returned').checked)pathLayer(layers.returnedPath,packet,'#dce5ed',true);if(byId('cache').checked)pathLayer(layers.pathCache,packet,'#ffc76b',false);
 byId('quality').textContent='欠測・境界 '+packet.quality.gaps.length+'件（表示部分） / 連続取得は未確認 / 青→黄→赤は元tickからの表示年齢 / レイヤOFFは未取得とは別';
}
for(const id of ['cursor','overviewMode','projection','motion','projectiles','declared','returned','cache'])byId(id).addEventListener('input',draw);draw();
</script></html>`;
}
