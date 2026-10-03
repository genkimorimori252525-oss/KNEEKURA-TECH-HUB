import {randomBytes} from 'node:crypto';
import {realpath,writeFile} from 'node:fs/promises';
import path from 'node:path';
import {traceAgeStyle} from '../../simlab/trace-age-style.mjs';

export async function writeDecisionPresentationArtifact(presentation,output,runDir) {
  const file=path.resolve(output),parent=await realpath(path.dirname(file)),run=await realpath(runDir);
  const resolved=path.join(parent,path.basename(file)),relative=path.relative(run,resolved);
  if(relative===''||(!relative.startsWith('..'+path.sep)&&relative!=='..'&&!path.isAbsolute(relative))) {
    throw new Error('DECISION_VIEW_OUTPUT_MUST_BE_OUTSIDE_RETAINED_RUN');
  }
  await writeFile(resolved,renderDecisionPresentationHtml(presentation),{encoding:'utf8',flag:'wx'});
  return resolved;
}

/** Standalone derived view. No network, world control or evidence-store writes. */
export function renderDecisionPresentationHtml(presentation) {
  if(presentation?.schema!=='kneekura.retained-decision-presentation/v1')throw new TypeError('RETAINED_DECISION_PRESENTATION_REQUIRED');
  const json=JSON.stringify(presentation);
  if(Buffer.byteLength(json)>262144)throw new RangeError('DECISION_PRESENTATION_BYTE_BUDGET_EXCEEDED');
  const data=json.replace(/</g,'\\u003c').replace(/\u2028/g,'\\u2028').replace(/\u2029/g,'\\u2029');
  const nonce=randomBytes(18).toString('base64');
  return `<!doctype html><html lang="ja"><meta charset="utf-8">
<meta http-equiv="Content-Security-Policy" content="default-src 'none'; script-src 'nonce-${nonce}'; style-src 'unsafe-inline'; connect-src 'none'; base-uri 'none'; form-action 'none'">
<meta name="viewport" content="width=device-width,initial-scale=1"><title>Retained Decision Observatory</title>
<style>body{font:15px system-ui;background:#101826;color:#e2e8f0;margin:24px}h1{font-size:24px}label{margin:8px;display:inline-block}button,select,input{font:inherit}canvas{width:100%;max-width:900px;background:#172334;border:1px solid #566579}pre{white-space:pre-wrap;overflow-wrap:anywhere}.stages{display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:12px}.stage{padding:12px;background:#1c2b3d;border:1px solid #566579}.muted{color:#b6c5d6}details{margin:12px 0}#timeline{max-height:240px;overflow:auto}</style>
<h1>Retained Decision Observatory</h1><p id="identity"></p>
<p class="muted">保存済み観測だけを表示します。時間的な近接は因果関係の証明ではありません。欠測は補間しません。</p>
<h2>Decision概要（指定区間の末尾）</h2><p id="overviewTick"></p><div class="stages" id="stages"></div>
<h2>観測timelineと空間表示</h2><p>概要は区間末尾の集約です。下のcursorは空間表示だけを絞ります。各層には取得tickを表示します。</p>
<label>tick <input id="tick" type="range"><output id="tickLabel"></output></label>
<label>表示 <select id="view"><option value="PLAN_XZ">PLAN_XZ</option><option value="ISOMETRIC_3D">固定isometric</option><option value="ELEVATION">ELEVATION (tick / y)</option></select></label><br>
<label><input type="checkbox" id="motion">実移動：実サンプルの点と細い実線</label>
<label><input type="checkbox" id="relatedProjectiles">関連する弾：UUIDごとの色、破線と菱形（取得した弾のみ）</label>
<label><input type="checkbox" id="terrain">観測用地形：四角（PathFinder評価ではない）</label>
<label><input type="checkbox" id="pathCache">探索cache：三角／×（全neighborではない）</label>
<label><input type="checkbox" id="declaredNavigation">宣言された経路：太い破線と菱形</label>
<p id="layerStatus"></p><canvas id="space" width="900" height="420" aria-label="任意表示の保存済み空間観測"></canvas>
<p class="muted">軌跡の色はcursorとの差です：<span style="color:rgb(105,215,255)">青 0–33t</span> → <span style="color:rgb(255,211,83)">黄 34–66t</span> → <span style="color:rgb(255,96,83)">赤 67–99t</span> → 100tで非表示。通常20t/秒。弾はUUIDの固定色から黄・赤へ寄せます。色が近い弾はUUIDとmarkerで確認してください。</p>
<p id="projectileLegend"></p>
<p class="muted">ELEVATIONの横軸はtickです。地形・cache・宣言経路はこの表示には重ねません。宣言経路は実移動ではありません。</p>
<div id="timeline"></div><details><summary>表示データ・参照元ID・欠測・省略情報</summary><pre id="raw"></pre></details>
<script id="data" type="application/json" nonce="${nonce}">${data}</script>
<script nonce="${nonce}">
const p=JSON.parse(document.getElementById('data').textContent),byId=id=>document.getElementById(id);
const traceAgeStyle=${traceAgeStyle.toString()};
byId('identity').textContent=JSON.stringify(p.identity);
byId('overviewTick').textContent='区間 '+p.request.startTick+' … '+p.request.endTick+'（最新の異なるfactのみ。省略情報とsource IDは詳細を参照）';
for(const [name,stage] of Object.entries(p.overview.stages)){
  const box=document.createElement('div');box.className='stage';
  const title=document.createElement('strong');title.textContent=name+' · '+stage.status;box.append(title);
  const count=document.createElement('p');count.textContent='観測fact '+stage.totalObservedFacts+' / 異なる項目 '+stage.totalDistinctFactKeys;box.append(count);
  for(const fact of stage.facts){const detail=document.createElement('details'),summary=document.createElement('summary'),text=document.createElement('pre');
    summary.textContent=fact.key+' · '+fact.epistemic_status; text.textContent=JSON.stringify(fact,null,2);detail.append(summary,text);box.append(detail);}
  byId('stages').append(box);
}
byId('raw').textContent=JSON.stringify(p,null,2);
const cursor=byId('tick');cursor.min=p.request.startTick;cursor.max=p.request.endTick;cursor.value=p.request.endTick;
const colors={motion:'#78d7ff',terrain:'#89d596',pathCache:'#ffc76b',declaredNavigation:'#f2a0e2'};
function draw(){
  const tick=Number(cursor.value),view=byId('view').value,elevation=view==='ELEVATION';byId('tickLabel').textContent=tick;
  const layers=p.layers,visible={},points=[];
  const alive=s=>s.tick<=tick&&tick-s.tick<100;
  byId('projectileLegend').textContent=byId('relatedProjectiles').checked?(layers.relatedProjectiles?.traces??[]).filter(group=>group.trace.samples.some(alive)).map(group=>group.trace.subject.id+' · 初期色 '+traceAgeStyle({traceClass:'PROJECTILE_ACTUAL',identity:group.trace.subject.id,sampleTick:tick,currentTick:tick}).color).join(' | '):'';
  const selected=Object.entries(layers).map(([key,layer])=>key+': '+layer.status+(layer.tick===null||layer.tick===undefined?'':' / 取得tick '+layer.tick)+(layer.tick>tick?' / cursorより未来なので非表示':''));
  byId('layerStatus').textContent=selected.join(' | ');
  for(const [key,layer] of Object.entries(layers)){
    if(!byId(key)?.checked||layer.tick>tick||(elevation&&!['motion','relatedProjectiles'].includes(key)))continue;
    const rows=key==='motion'?layer.trace.samples.filter(alive):key==='relatedProjectiles'?layer.traces.map(group=>({...group.trace,samples:group.trace.samples.filter(alive)})):key==='terrain'?layer.cells:layer.nodes;
    visible[key]=rows;points.push(...(key==='relatedProjectiles'?rows.flatMap(trace=>trace.samples):rows).filter(s=>[s.x,s.y,s.z].every(Number.isFinite)));
  }
  const canvas=byId('space'),ctx=canvas.getContext('2d');ctx.clearRect(0,0,canvas.width,canvas.height);
  const project=s=>elevation?[s.tick,s.y]:view==='PLAN_XZ'?[s.x,s.z]:[s.x-s.z,(s.x+s.z)/2-s.y];
  const projected=points.map(project).filter(q=>q.every(Number.isFinite));
  if(!projected.length){ctx.fillStyle='#b6c5d6';ctx.fillText('層を明示的に選択してください。現在のcursorに観測点がない場合も表示しません。',20,30);return;}
  const xs=projected.map(q=>q[0]),ys=projected.map(q=>q[1]),minX=Math.min(...xs),minY=Math.min(...ys),rangeX=Math.max(1,Math.max(...xs)-minX),rangeY=Math.max(1,Math.max(...ys)-minY);
  const scale=Math.min(830/rangeX,350/rangeY),xy=s=>{const q=project(s);return [35+(q[0]-minX)*scale,385-(q[1]-minY)*scale];};
  function drawTrace(trace,rows){
    const projectile=trace.trace_class==='PROJECTILE_ACTUAL',samples=new Map(rows.map(s=>[s.sample_id,s]));
    const style=s=>{const age=traceAgeStyle({traceClass:trace.trace_class,identity:trace.subject.id,sampleTick:s.tick,currentTick:tick});ctx.strokeStyle=age.color;ctx.globalAlpha=age.alpha;};
    ctx.lineWidth=projectile?2.5:1.5;ctx.setLineDash(projectile?[6,4]:[]);
    for(const segment of trace.segments){const a=samples.get(segment.from_sample_id),b=samples.get(segment.to_sample_id);if(!a||!b)continue;style(b);ctx.beginPath();ctx.moveTo(...xy(a));ctx.lineTo(...xy(b));ctx.stroke();}
    ctx.setLineDash([]);
    for(const point of rows){style(point);const [x,y]=xy(point);ctx.beginPath();if(projectile){ctx.moveTo(x,y-4);ctx.lineTo(x+4,y);ctx.lineTo(x,y+4);ctx.lineTo(x-4,y);ctx.closePath();}else ctx.arc(x,y,3,0,2*Math.PI);ctx.stroke();}
    if(projectile&&rows.length){const point=rows.at(-1);style(point);ctx.fillStyle=ctx.strokeStyle;const [x,y]=xy(point);ctx.fillText(trace.subject.id.slice(-12),x+6,y-6);}
    ctx.globalAlpha=1;
  }
  for(const [key,rows] of Object.entries(visible)){
    if(key==='motion'){drawTrace(layers.motion.trace,rows);continue;}
    if(key==='relatedProjectiles'){for(const trace of rows)drawTrace(trace,trace.samples);continue;}
    ctx.strokeStyle=colors[key];ctx.fillStyle=colors[key];ctx.lineWidth=key==='declaredNavigation'?3:1.5;
    ctx.setLineDash(key==='declaredNavigation'?[8,5]:[]);
    const line=(a,b)=>{const from=xy(a),to=xy(b);ctx.beginPath();ctx.moveTo(...from);ctx.lineTo(...to);ctx.stroke();};
    if(key==='declaredNavigation')for(let i=1;i<rows.length;i++)line(rows[i-1],rows[i]);
    ctx.setLineDash([]);
    for(const point of rows){if(![point.x,point.y,point.z].every(Number.isFinite))continue;const [x,y]=xy(point);ctx.beginPath();
      if(key==='terrain')ctx.rect(x-4,y-4,8,8);
      else if(key==='pathCache'&&point.closedAtReturn){ctx.moveTo(x-4,y-4);ctx.lineTo(x+4,y+4);ctx.moveTo(x+4,y-4);ctx.lineTo(x-4,y+4);}
      else if(key==='pathCache'){ctx.moveTo(x,y-5);ctx.lineTo(x+5,y+4);ctx.lineTo(x-5,y+4);ctx.closePath();}
      else if(key==='declaredNavigation'){ctx.moveTo(x,y-5);ctx.lineTo(x+5,y);ctx.lineTo(x,y+5);ctx.lineTo(x-5,y);ctx.closePath();}
      else ctx.arc(x,y,3,0,2*Math.PI);ctx.stroke();
    }
  }
}
for(const event of p.overview.timeline){const button=document.createElement('button');button.type='button';button.textContent=event.tick+' · '+event.kind;
  button.title=JSON.stringify(event);button.addEventListener('click',()=>{cursor.value=event.tick;draw();});byId('timeline').append(button);}
cursor.addEventListener('input',draw);byId('view').addEventListener('change',draw);
for(const key of Object.keys(p.layers))byId(key)?.addEventListener('change',draw);draw();
</script></html>`;
}
