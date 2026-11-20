import assert from 'node:assert/strict';

/**
 * Declarative scenario and its judgement. Data only here: the game side (ManualScenario.java) runs the steps and writes
 * facts; this module validates input and judges `expect` from those facts (scenario-result.json, ai.jsonl, trails/ai
 * results). Ticks are server ticks counted from the first measured tick after the Player is bound (tick 0).
 *
 * scenario: [{at, run|check|screenshot|mark}]   (non-decreasing `at`, < maxTicks, at most 128 steps)
 *   run: vanilla command as the Player, permission 4 (FAIL if it throws or does not parse)
 *   try: same, but recorded only and never judged (idempotent setup such as `difficulty normal`, which vanilla reports as an error when unchanged)
 *   check: command that must succeed with a result > 0 (e.g. "execute if entity @e[type=mymod:boss]")
 *   screenshot: name -> game/screenshots/scenario-<name>.png (for eyes, never judged)
 *   mark: name -> starts a load segment at this tick; also records entity counts
 * expect: [...] at most 32, each one of
 *   {entity, target, by}            the entity type targets `target` type at some tick <= by
 *   {entity, goal, between:[a,b]}   a running goal / target goal / behavior named `goal` overlaps [a,b]
 *   {entity, state:{k:v}, after?, by?}  state fields or tankWhy notes equal these values at some overlapping tick
 *   {entity, gone, by}              gone: REMOVED | OUT_OF_SELECTION | ANY, at tick <= by
 *   {seen}                          entity type observed by the AI lens or trails
 *   {tickMs:{segment, mean?, p95?, max?, tankExcluded?}}  load budget for a mark segment ('baseline' = tick 0 to first mark)
 */
const NAME=/^[a-z0-9][a-z0-9-]{0,31}$/,TYPE=/^[a-z0-9_.-]+:[a-z0-9_./-]+$/;
const exactKeys=(o,keys,code)=>assert(o&&typeof o==='object'&&!Array.isArray(o)&&Object.keys(o).every(k=>keys.includes(k)),code);
const tick=(v,max,code)=>assert(Number.isInteger(v)&&v>=0&&v<max,code);

export function validateScenario(steps,maxTicks){
 assert(Array.isArray(steps)&&steps.length>0&&steps.length<=128,'TANK_SCENARIO_STEPS');
 let previous=0;const marks=new Set();
 for(const s of steps){
  const kinds=['run','try','check','screenshot','mark'].filter(k=>Object.hasOwn(s??{},k));
  assert(kinds.length===1,'TANK_SCENARIO_STEP_KIND');exactKeys(s,['at',kinds[0]],'TANK_SCENARIO_STEP_FIELDS');
  tick(s.at,maxTicks,'TANK_SCENARIO_AT');assert(s.at>=previous,'TANK_SCENARIO_ORDER');previous=s.at;const v=s[kinds[0]];
  if(['run','try','check'].includes(kinds[0]))assert(typeof v==='string'&&v.length>0&&v.length<=256&&!/[\r\n]/.test(v),'TANK_SCENARIO_COMMAND');
  else assert(typeof v==='string'&&NAME.test(v)&&v!=='baseline','TANK_SCENARIO_NAME');
  if(kinds[0]==='mark'){assert(!marks.has(v),'TANK_SCENARIO_DUPLICATE_MARK');marks.add(v);}
 }
 return steps.map(s=>({...s}));
}

export function validateExpect(list,steps,maxTicks,{ai=true,trails=true}={}){
 assert(Array.isArray(steps),'TANK_EXPECT_NEEDS_SCENARIO');
 assert(Array.isArray(list)&&list.length>0&&list.length<=32,'TANK_EXPECT_LIST');
 const marks=new Set(['baseline',...(steps??[]).filter(s=>s.mark).map(s=>s.mark)]);
 for(const e of list){
  assert(e&&typeof e==='object'&&!Array.isArray(e),'TANK_EXPECT_ITEM');
  if(Object.hasOwn(e,'tickMs')){exactKeys(e,['tickMs'],'TANK_EXPECT_FIELDS');const t=e.tickMs;exactKeys(t,['segment','mean','p95','max','tankExcluded'],'TANK_EXPECT_TICKMS_FIELDS');
   assert(marks.has(t.segment),'TANK_EXPECT_SEGMENT');assert(['mean','p95','max'].some(k=>Object.hasOwn(t,k)),'TANK_EXPECT_TICKMS_BOUND');
   for(const k of ['mean','p95','max'])if(Object.hasOwn(t,k))assert(typeof t[k]==='number'&&t[k]>0&&t[k]<=10000,'TANK_EXPECT_TICKMS_VALUE');
   if(Object.hasOwn(t,'tankExcluded'))assert(typeof t.tankExcluded==='boolean','TANK_EXPECT_TANK_EXCLUDED');continue;}
  if(Object.hasOwn(e,'seen')){exactKeys(e,['seen'],'TANK_EXPECT_FIELDS');assert(TYPE.test(e.seen),'TANK_EXPECT_TYPE');assert(ai||trails,'TANK_EXPECT_NEEDS_AI_OR_TRAILS');continue;}
  assert(ai,'TANK_EXPECT_NEEDS_AI');
  assert(typeof e.entity==='string'&&TYPE.test(e.entity),'TANK_EXPECT_ENTITY');
  if(Object.hasOwn(e,'target')){exactKeys(e,['entity','target','by'],'TANK_EXPECT_FIELDS');assert(TYPE.test(e.target),'TANK_EXPECT_TYPE');tick(e.by,maxTicks,'TANK_EXPECT_BY');}
  else if(Object.hasOwn(e,'goal')){exactKeys(e,['entity','goal','between'],'TANK_EXPECT_FIELDS');assert(typeof e.goal==='string'&&/^[A-Za-z0-9_$]{1,80}$/.test(e.goal),'TANK_EXPECT_GOAL');
   assert(Array.isArray(e.between)&&e.between.length===2,'TANK_EXPECT_BETWEEN');tick(e.between[0],maxTicks,'TANK_EXPECT_BETWEEN');tick(e.between[1],maxTicks,'TANK_EXPECT_BETWEEN');assert(e.between[0]<=e.between[1],'TANK_EXPECT_BETWEEN');}
  else if(Object.hasOwn(e,'state')){exactKeys(e,['entity','state','after','by'],'TANK_EXPECT_FIELDS');assert(e.state&&typeof e.state==='object'&&!Array.isArray(e.state)&&Object.keys(e.state).length>0&&Object.values(e.state).every(v=>['string','number','boolean'].includes(typeof v)),'TANK_EXPECT_STATE');
   if(Object.hasOwn(e,'after'))tick(e.after,maxTicks,'TANK_EXPECT_AFTER');if(Object.hasOwn(e,'by'))tick(e.by,maxTicks,'TANK_EXPECT_BY');}
  else if(Object.hasOwn(e,'gone')){exactKeys(e,['entity','gone','by'],'TANK_EXPECT_FIELDS');assert(['REMOVED','OUT_OF_SELECTION','ANY'].includes(e.gone),'TANK_EXPECT_GONE');tick(e.by,maxTicks,'TANK_EXPECT_BY');}
  else assert.fail('TANK_EXPECT_KIND');
 }
 return structuredClone(list);
}

const quantile=(sorted,q)=>sorted.length?sorted[Math.min(sorted.length-1,Math.ceil(q*sorted.length)-1)]:null;
const round=v=>v==null?null:Math.round(v*1000)/1000;
function stats(values){const s=[...values].sort((a,b)=>a-b);return {mean:round(s.reduce((a,b)=>a+b,0)/Math.max(1,s.length)),p50:round(quantile(s,.5)),p95:round(quantile(s,.95)),max:round(s.at(-1)??null)};}
/** Load per segment: baseline = [0, first mark), each mark = [its tick, next mark tick or end). Milliseconds. */
export function tickSegments(result){
 const ticks=result.tickMicros??[],tools=result.tankToolMicros??[],marks=(result.steps??[]).filter(s=>s.mark&&s.status==='MARKED').map(s=>({name:s.mark,from:s.tick,loadedEntities:s.loadedEntities,mobsNear:s.mobsNear}));
 const bounds=[{name:'baseline',from:0},...marks];const out={};
 bounds.forEach((b,i)=>{const to=i+1<bounds.length?bounds[i+1].from:ticks.length;const all=ticks.slice(b.from,to).map(v=>v/1000),own=tools.slice(b.from,to).map(v=>v/1000);
  if(!all.length){out[b.name]={from:b.from,to,n:0};return;}
  out[b.name]={from:b.from,to,n:all.length,...(b.loadedEntities!=null?{loadedEntities:b.loadedEntities,mobsNear:b.mobsNear}:{}),ms:stats(all),tankExcludedMs:stats(all.map((v,j)=>Math.max(0,v-(own[j]??0)))),tankToolMeanMs:stats(own).mean};});
 return out;
}

/** Per-uuid intervals of the AI lens' change-only records: [tick, next record) with relative ticks. */
function timelines(lines,start,end){
 const by=new Map();for(const r of lines){if(!r.uuid)continue;const rel=r.tick-start;(by.get(r.uuid)??by.set(r.uuid,[]).get(r.uuid)).push({...r,rel});}
 const spans=[];for(const [uuid,rows] of by){rows.sort((a,b)=>a.rel-b.rel);const type=rows.find(r=>r.type)?.type;
  rows.forEach((r,i)=>{if(r.event==='CHANGE')spans.push({uuid,type,from:r.rel,to:i+1<rows.length?rows[i+1].rel:end,row:r});});}
 return {spans,gone:lines.filter(r=>r.event==='GONE').map(r=>({...r,rel:r.tick-start}))};
}
const named=(list,goal)=>(list??[]).some(x=>x.replace(/^\d+:/,'').split('$').pop()===goal||x.replace(/^\d+:/,'')===goal);

export function judge({expect,result,aiLines=[],seenTypes=[]}){
 const rows=[];const end=result.ticks??0;const start=result.startGameTime;
 const steps=result.steps??[];
 for(const s of steps.filter(s=>s.run||s.check||s.status==='NOT_REACHED'&&!s.try))rows.push({kind:s.run?'run':s.check?'check':'step',at:s.at,what:s.run??s.check??s.mark??s.screenshot,status:s.status==='PASS'?'PASS':'FAIL',...(s.status!=='PASS'?{why:s.status,messages:s.messages}:{})});
 const segments=tickSegments(result);const {spans,gone}=start>=0?timelines(aiLines,start,end):{spans:[],gone:[]};
 for(const e of expect??[]){
  let ok=false,evidence=null;
  if(e.tickMs){const seg=segments[e.tickMs.segment];const m=seg?.n?(e.tickMs.tankExcluded===false?seg.ms:seg.tankExcludedMs):null;
   if(m){const over=['mean','p95','max'].filter(k=>Object.hasOwn(e.tickMs,k)&&m[k]>e.tickMs[k]);ok=over.length===0;evidence={segment:e.tickMs.segment,n:seg.n,measured:m,...(over.length?{over}:{})};}
   else evidence={segment:e.tickMs.segment,n:0,why:'NO_TICKS_IN_SEGMENT'};}
  else if(e.seen){ok=seenTypes.includes(e.seen);}
  else if(e.target){const hit=spans.find(s=>s.type===e.entity&&s.row.target?.type===e.target&&s.from<=e.by);ok=!!hit;evidence=hit?{tick:hit.from,uuid:hit.uuid}:null;}
  else if(e.goal){const [a,b]=e.between;const hit=spans.find(s=>s.type===e.entity&&s.from<=b&&s.to>=a&&(named(s.row.goals,e.goal)||named(s.row.targetGoals,e.goal)||named(s.row.behaviors,e.goal)));ok=!!hit;evidence=hit?{from:hit.from,to:hit.to,uuid:hit.uuid}:null;}
  else if(e.state){const a=e.after??0,b=e.by??end;const hit=spans.find(s=>s.type===e.entity&&s.from<=b&&s.to>=a&&Object.entries(e.state).every(([k,v])=>[s.row.state?.[k],s.row.why?.[k]].some(x=>x!=null&&String(x)===String(v))));ok=!!hit;evidence=hit?{from:hit.from,to:hit.to,uuid:hit.uuid}:null;}
  else if(e.gone){const hit=gone.find(g=>g.type===e.entity&&g.rel<=e.by&&(e.gone==='ANY'||g.why===e.gone));ok=!!hit;evidence=hit?{tick:hit.rel,why:hit.why,uuid:hit.uuid}:null;}
  rows.push({kind:'expect',expect:e,status:ok?'PASS':'FAIL',...(evidence?{evidence}:{})});
 }
 const failed=rows.filter(r=>r.status!=='PASS');const screenshots=steps.filter(s=>s.screenshot).map(s=>({name:s.screenshot,tick:s.tick??null,status:s.status,file:s.file??null}));
 return {status:failed.length||result.ticks==null?'FAIL':'PASS',passed:rows.length-failed.length,failed:failed.length,rows,segments,screenshots,
  scope:'JUDGED_FROM_RECORDED_FACTS; ai expectations see only the AI lens selection (nearest 32 Mobs within 48/32 of the Player, every 5 ticks)'};
}
