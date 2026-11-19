import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import vm from 'node:vm';
import {traceAgeStyle} from '../trace-age-style.mjs';

const HERE=path.dirname(fileURLToPath(import.meta.url));
const index=fs.readFileSync(path.join(HERE,'index.html'),'utf8');
const store=fs.readFileSync(path.join(HERE,'store.js'),'utf8');
const serve=fs.readFileSync(path.join(HERE,'..','serve.mjs'),'utf8');

test('motion trace Viewer is OFF by default and requires explicit Mob selection',()=>{
  assert.match(index,/id="trail"[^>]*value="0"/);
  assert.match(index,/id="trailV"[^>]*>0t</);
  assert.match(index,/id="traceSubject"/);
  assert.match(index,/trail:0,traceSubject:''/);
  assert.match(index,/function selectedTraceEntity\(\)/);
});

test('selected Mob trace uses the same SampledMotionTrace contract as AI output',()=>{
  assert.match(store,/samples:\s*\(startTick, endTick, limit\)/);
  assert.match(store,/SIMLAB_POS_RETAINED_POINT/);
  assert.match(index,/import\('\/motion-trace\.mjs'\)/);
  assert.match(index,/MOTION_TRACE\.buildTraceFromSimStore\(/);
  assert.ok((index.match(/motion\.segments/g)||[]).length>=1,'shared renderer must use contract segments');
  assert.ok((index.match(/drawStyledMotionTrace\(motion/g)||[]).length>=2,'F3 and plan/elevation must use the shared renderer');
  assert.match(serve,/u\.pathname === '\/motion-trace\.mjs'/);
});

test('Mob and projectile traces have non-color visual distinction',()=>{
  assert.match(index,/setLineDash\(\[10,6\]\)/);
  assert.ok(/lineWidth=projectile\?1\.25:2\.5/.test(index),'Mob/projectile widths differ');
  assert.match(index,/arc\(q\.x,q\.y,2\.6/);
  assert.match(index,/if\(e\.role!=='projectile'\) continue/);
});

test('canvas age rendering preserves gaps, excludes expired samples and assigns projectile colors independently',()=>{
  const start=index.indexOf('function drawStyledMotionTrace('),end=index.indexOf('\nfunction load(',start),calls=[];
  assert.ok(start>=0&&end>start);
  const labels=[];
  const ctx={save(){},restore(){},setLineDash(){},beginPath(){this.points=[];this.closed=false;},moveTo(x,y){this.points.push([x,y]);},lineTo(x,y){this.points.push([x,y]);},closePath(){this.closed=true;},arc(){},fill(){},fillText(text){labels.push(text);},stroke(){calls.push({color:this.strokeStyle,alpha:this.globalAlpha,points:this.points,closed:this.closed});}};
  const scope=vm.createContext({TRACE_AGE_STYLE:{traceAgeStyle},T:{tick:100,trail:100},sctx:ctx});
  vm.runInContext(index.slice(start,end),scope);
  const make=id=>({trace_class:'PROJECTILE_ACTUAL',subject:{id},samples:[{sample_id:'old',tick:0,x:0,y:0},{sample_id:'a',tick:95,x:1,y:0},{sample_id:'b',tick:99,x:2,y:0}],segments:[{from_sample_id:'old',to_sample_id:'a'},{from_sample_id:'a',to_sample_id:'b'}]});
  const a=make('bullet-1'),b=make('bullet-2'),before=JSON.stringify([a,b]);
  scope.drawStyledMotionTrace(a,p=>p);scope.drawStyledMotionTrace(b,p=>p);
  const lines=calls.filter(c=>!c.closed&&c.points.length===2);assert.equal(lines.length,2);assert.notEqual(lines[0].color,lines[1].color);
  assert.deepEqual(lines[0].points,[[1,0],[2,0]]);assert.equal(JSON.stringify([a,b]),before);
  assert.deepEqual(labels,['bullet-1','bullet-2']);
  const count=lines.length;a.segments=[];scope.drawStyledMotionTrace(a,p=>p);
  assert.equal(calls.filter(c=>!c.closed&&c.points.length===2).length,count,'no new line across a gap');
});

test('all Viewer views use stable identity age styles on retained contract traces',()=>{
  assert.match(index,/import\('\/trace-age-style\.mjs'\)/);
  assert.match(index,/function drawStyledMotionTrace\(/);
  assert.match(index,/traceClass:'PROJECTILE_ACTUAL'/);
  assert.ok((index.match(/drawStyledMotionTrace\(motion/g)||[]).length>=2);
  assert.ok((index.match(/drawStyledMotionTrace\(projectile/g)||[]).length>=2);
  assert.match(index,/青.*黄.*赤/);
  assert.match(serve,/u\.pathname === '\/trace-age-style\.mjs'/);
});
