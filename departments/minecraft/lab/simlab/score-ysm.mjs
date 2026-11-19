/* =============================================================================
   SimLab — ysm.js のボーン再生を「実機が録った姿勢トレース」で採点する
   -----------------------------------------------------------------------------
   Viewer には霊夢用の描画経路が2つある:

     (1) 姿勢トレース (.pose.bin)  実機が吐いた頂点をそのまま再生。定義上ズレない = 正解
     (2) ysm.js のボーン再生       main.json + *.animation.json をブラウザ側で組み直す

   (2) が正しければ 115MB の .pose.bin なしで実機と同じ絵が出せる (要件 VIEW-02)。
   このスクリプトは **ブラウザも Minecraft も使わずに** (2) を (1) で採点する。
   ysm.js は DOM/WebGL/fetch を一切使わない純粋な計算モジュールなので Node から
   そのまま読める (window が無ければ globalThis に付く)。

   対応付けは **UV 矩形** で取る —— 位置は答え合わせをしたい量なので、位置で対応を
   取ると循環する。複数 cube が同じ UV 矩形を共有する場合は曖昧なのでその矩形を捨てる。

   座標系: (1) はレンダラが吐いたまま、(2) は素のモデル空間。gl.js の描画行列
     (1) T(p)*rotY(-yaw)   (2) T(p)*rotY(180-yaw)*scale(-1,-1,1)*T(0,-1.501,0)
   を等値して整理すると v_pose = (x, 1.501 - y, -z)。総当たりで検証済み
   (他の候補は中央値が 5〜6 倍悪い)。

   usage:
     node simlab/score-ysm.mjs <xxx.pose.json> <arena-0.jsonl> [tick ...]
   ============================================================================= */
import fs from 'node:fs'; import path from 'node:path';
import { fileURLToPath } from 'node:url';
const HERE = path.dirname(fileURLToPath(import.meta.url));
const REPO = path.resolve(HERE, '..');
const [,,POSE,TRACE,...TICKS] = process.argv;
const TICK_LIST = TICKS.length ? TICKS.map(Number) : [10,48,95];
if (!POSE || !TRACE) {
  console.error('usage: node simlab/score-ysm.mjs <xxx.pose.json> <arena-0.jsonl> [tick ...]');
  process.exit(2);
}
// ysm.json を持つ最初のパックを採る (serve.mjs と同じ規則)
const PACK = (() => {
  const root = path.join(process.env.APPDATA || '', '.minecraft/config/yes_steve_model/custom');
  for (const d of fs.readdirSync(root)) {
    const p = path.join(root, d);
    if (fs.existsSync(path.join(p, 'ysm.json'))) return p;
  }
  throw new Error('ysm.json を持つパックが見つからない: ' + root);
})();
(0,eval)(fs.readFileSync(REPO+'/simlab/viewer/ysm.js','utf8'));
const YSM=globalThis.YSM, M=YSM.M;
const manifest=JSON.parse(fs.readFileSync(PACK+'/ysm.json','utf8'));
const model=JSON.parse(fs.readFileSync(path.join(PACK,manifest.files.player.model.main),'utf8'));
const anims={}; for(const [nm,rel] of Object.entries(manifest.files.player.animation||{})){
  try{Object.assign(anims,JSON.parse(fs.readFileSync(path.join(PACK,rel),'utf8')).animations||{});}catch{} }
const props=manifest.properties||{};
const geo=YSM.buildGeometry(model['minecraft:geometry'][0],props.width_scale||1,props.height_scale||1,YSM.collectHidden(anims));
const baseNames=Object.keys(anims).filter(n=>/^(pre_)?parallel/.test(n)).sort();
const base=baseNames.map(n=>YSM.sampleAnimation(anims[n],0,{}));

const fr=new Map();
for(const line of fs.readFileSync(TRACE,'utf8').split('\n')){ if(!line||line[0]!=='{')continue;
  let j;try{j=JSON.parse(line);}catch{continue;} if(j.ch==='anim')fr.set(j.t,j); }
const maxT=Math.max(...fr.keys());
const track={name:[],elapsed:new Float32Array(maxT+1),vars:[]};
{let cur=null,st=0,vars={};for(let t=0;t<=maxT;t++){const a=fr.get(t);
  if(a){const nm=(a.anim&&a.anim!=='-')?a.anim:null; if(nm!==cur){cur=nm;st=t;}
   if(a.molang&&a.molang!=='-')for(const m of a.molang.matchAll(/([A-Za-z_][A-Za-z0-9_.]*)\s*=\s*(-?[0-9.]+)/g)){vars=Object.assign({},vars);vars[m[1].toLowerCase()]=parseFloat(m[2]);}}
  track.name[t]=cur;track.elapsed[t]=(t-st)/20;track.vars[t]=vars;}}

const pj=JSON.parse(fs.readFileSync(POSE,'utf8'));
const binb=fs.readFileSync(path.join(path.dirname(POSE),pj.bin));
const f32=new Float32Array(binb.buffer,binb.byteOffset,binb.byteLength/4);
const foff=[];{let o=0;for(const n of pj.lens){foff.push(o);o+=n*pj.stride;}}
const rk=(a,b,c,d)=>[a,b,c,d].map(x=>x.toFixed(4)).join(',');
const XF=(x,y,z)=>[x,1.501-y,-z];
const pct=(a,p)=>a.length?a[Math.min(a.length-1,Math.floor(a.length*p))]:NaN;

function ysmQuads(tick,useAnim){
  const vars=Object.assign({},track.vars[tick]||{});
  const layers=base.slice();
  const nm=track.name[tick],a=useAnim&&nm&&anims[nm];
  if(a)layers.push(YSM.sampleAnimation(a,track.elapsed[tick],vars));
  const B=YSM.poseBones(geo.bones,layers);
  const v=geo.verts,bi=geo.boneIndex,S=8,m=new Map(),dup=new Set();
  for(let q=0;q+6*S<=v.length;q+=6*S){
    let u0=1/0,v0=1/0,u1=-1/0,v1=-1/0,cx=0,cy=0,cz=0,bn=bi[q/S]|0;
    for(let k=0;k<6;k++){const o=q+k*S;const u=v[o+3],vv=v[o+4];
      if(u<u0)u0=u;if(u>u1)u1=u;if(vv<v0)v0=vv;if(vv>v1)v1=vv;
      const b=bi[o/S]|0,mm=B.subarray(b*16,b*16+16),p=M.apply(mm,[v[o],v[o+1],v[o+2]]),w=XF(p[0],p[1],p[2]);
      cx+=w[0];cy+=w[1];cz+=w[2];}
    const k=rk(u0,v0,u1,v1); if(m.has(k)){dup.add(k);continue;}
    m.set(k,{p:[cx/6,cy/6,cz/6],bone:geo.bones[bn]?geo.bones[bn].name:'?'});}
  for(const k of dup)m.delete(k); return m;
}
function poseQuads(tick){
  const slot=(pj.slots||[])[tick+(pj.base||0)]; if(slot==null||slot<0)return null;
  const a=f32.subarray(foff[slot],foff[slot]+pj.lens[slot]*pj.stride),S=pj.stride,m=new Map(),dup=new Set();
  for(let q=0;q+6*S<=a.length;q+=6*S){let u0=1/0,v0=1/0,u1=-1/0,v1=-1/0,cx=0,cy=0,cz=0;
    for(let k=0;k<6;k++){const o=q+k*S;const u=a[o+3],vv=a[o+4];
      if(u<u0)u0=u;if(u>u1)u1=u;if(vv<v0)v0=vv;if(vv>v1)v1=vv;cx+=a[o];cy+=a[o+1];cz+=a[o+2];}
    const k=rk(u0,v0,u1,v1); if(m.has(k)){dup.add(k);continue;} m.set(k,[cx/6,cy/6,cz/6]);}
  for(const k of dup)m.delete(k); return m;
}
function cmp(tick,useAnim){
  const A=ysmQuads(tick,useAnim),P=poseQuads(tick); if(!P)return null;
  const d=[],byBone=new Map();
  for(const [k,p] of P){const y=A.get(k);if(!y)continue;
    const e=Math.hypot(p[0]-y.p[0],p[1]-y.p[1],p[2]-y.p[2]); d.push(e);
    let b=byBone.get(y.bone);if(!b){b={n:0,s:0,mx:0};byBone.set(y.bone,b);} b.n++;b.s+=e;if(e>b.mx)b.mx=e;}
  d.sort((x,y)=>x-y);
  return {n:d.length,med:pct(d,0.5),p95:pct(d,0.95),max:d[d.length-1],byBone,
          within1px:d.filter(x=>x<1/16).length/d.length, within4px:d.filter(x=>x<4/16).length/d.length};
}
console.log(`アニメ ${Object.keys(anims).length}種 / base(parallel系) ${baseNames.length}本: ${baseNames.slice(0,6).join(', ')}...`);
for(const t of TICK_LIST) console.log(`  tick ${t}: anim="${track.name[t]||'(なし)'}" elapsed=${track.elapsed[t].toFixed(2)}s vars=${JSON.stringify(track.vars[t]).slice(0,80)}`);
console.log('');
for(const t of TICK_LIST){
  const withA=cmp(t,true), noA=cmp(t,false);
  if(!withA){console.log(`tick ${t}: 未記録`);continue;}
  console.log(`--- tick ${t} (対応 ${withA.n} quad) ---`);
  console.log(`  アニメ有り : 中央値 ${withA.med.toFixed(4)}  p95 ${withA.p95.toFixed(4)}  最大 ${withA.max.toFixed(3)}  1px以内 ${(withA.within1px*100).toFixed(1)}%  4px以内 ${(withA.within4px*100).toFixed(1)}%`);
  console.log(`  アニメ無し : 中央値 ${noA.med.toFixed(4)}  p95 ${noA.p95.toFixed(4)}   ← 有りと変わらなければアニメが効いていない`);
  const bb=[...withA.byBone].filter(([,v])=>v.n>=4).sort((a,b)=>b[1].s/b[1].n-a[1].s/a[1].n);
  console.log('  誤差の大きいボーン上位8: '+bb.slice(0,8).map(([n,v])=>`${n}(${(v.s/v.n).toFixed(2)},n=${v.n})`).join(' '));
  console.log('  誤差の小さいボーン下位5: '+bb.slice(-5).map(([n,v])=>`${n}(${(v.s/v.n).toFixed(3)},n=${v.n})`).join(' '));
}

// --- 残差が「定数のズレ」か「姿勢の違い」かを切り分ける ---
function fit(tick){
  const A=ysmQuads(tick,true),P=poseQuads(tick); if(!P)return;
  const pairs=[]; for(const [k,p] of P){const y=A.get(k); if(y)pairs.push([p,y.p,y.bone]);}
  if(!pairs.length)return;
  const md=a=>a[Math.floor(a.length/2)];
  const raw=pairs.map(x=>Math.hypot(x[0][0]-x[1][0],x[0][1]-x[1][1],x[0][2]-x[1][2])).sort((a,b)=>a-b);
  let dx=0,dy=0,dz=0; for(const x of pairs){dx+=x[0][0]-x[1][0];dy+=x[0][1]-x[1][1];dz+=x[0][2]-x[1][2];}
  const n=pairs.length; dx/=n;dy/=n;dz/=n;
  const afterT=pairs.map(x=>Math.hypot(x[0][0]-x[1][0]-dx,x[0][1]-x[1][1]-dy,x[0][2]-x[1][2]-dz)).sort((a,b)=>a-b);
  let cpx=0,cpy=0,cpz=0,cyx=0,cyy=0,cyz=0;
  for(const x of pairs){cpx+=x[0][0];cpy+=x[0][1];cpz+=x[0][2];cyx+=x[1][0];cyy+=x[1][1];cyz+=x[1][2];}
  cpx/=n;cpy/=n;cpz/=n;cyx/=n;cyy/=n;cyz/=n;
  let num=0,den=0;
  for(const x of pairs){const a=[x[0][0]-cpx,x[0][1]-cpy,x[0][2]-cpz],b=[x[1][0]-cyx,x[1][1]-cyy,x[1][2]-cyz];
    num+=a[0]*b[0]+a[1]*b[1]+a[2]*b[2]; den+=b[0]*b[0]+b[1]*b[1]+b[2]*b[2];}
  const sc=num/den;
  const afterS=pairs.map(x=>{const b=[(x[1][0]-cyx)*sc+cpx,(x[1][1]-cyy)*sc+cpy,(x[1][2]-cyz)*sc+cpz];
    return Math.hypot(x[0][0]-b[0],x[0][1]-b[1],x[0][2]-b[2]);}).sort((a,b)=>a-b);
  console.log('--- tick '+tick+' ('+n+'対応) ---');
  console.log('  そのまま           : 中央値 '+md(raw).toFixed(4));
  console.log('  平行移動を当てた後 : 中央値 '+md(afterT).toFixed(4)+'   ずれ ('+dx.toFixed(4)+', '+dy.toFixed(4)+', '+dz.toFixed(4)+')');
  console.log('  +一様スケール後    : 中央値 '+md(afterS).toFixed(4)+'   スケール '+sc.toFixed(5));
  // ボーン別に「平行移動後」の誤差を見る（定数を除いた後の真の姿勢差）
  const bb=new Map();
  for(const x of pairs){const e=Math.hypot(x[0][0]-x[1][0]-dx,x[0][1]-x[1][1]-dy,x[0][2]-x[1][2]-dz);
    let b=bb.get(x[2]); if(!b){b={n:0,s:0};bb.set(x[2],b);} b.n++;b.s+=e;}
  const srt=[...bb].filter(v=>v[1].n>=6).sort((a,b)=>b[1].s/b[1].n-a[1].s/a[1].n);
  console.log('  平行移動を除いた後で誤差が大きいボーン: '+srt.slice(0,6).map(v=>v[0]+'('+(v[1].s/v[1].n).toFixed(3)+')').join(' '));
  console.log('  同・小さいボーン                      : '+srt.slice(-6).map(v=>v[0]+'('+(v[1].s/v[1].n).toFixed(3)+')').join(' '));
}
console.log('');
console.log('=== 残差の内訳（定数のズレか、姿勢の違いか） ===');
for(const t of TICK_LIST) fit(t);
