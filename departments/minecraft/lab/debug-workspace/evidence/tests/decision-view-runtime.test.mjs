import test from 'node:test';
import assert from 'node:assert/strict';
import vm from 'node:vm';
import {buildRetainedDecisionPresentation} from '../decision-presentation.mjs';
import {renderDecisionPresentationHtml} from '../decision-view.mjs';
const uuid='00000000-0000-0000-0000-000000000001';
const identity={debugSessionId:'s',runId:'r',runSnapshotId:'snap',processEpoch:1,arenaEpoch:0,targetRevision:1};
function runView(presentation){
 const html=renderDecisionPresentationHtml(presentation),elements=new Map(),strokes=[];
 const context={strokeStyle:'',globalAlpha:1,dash:[],segments:[],clearRect(){},fillText(){},setLineDash(value){this.dash=[...value];},beginPath(){this.segments=[];},moveTo(x,y){this.last=[x,y];},lineTo(x,y){this.segments.push([this.last,[x,y]]);this.last=[x,y];},stroke(){strokes.push({color:this.strokeStyle,alpha:this.globalAlpha,dash:[...this.dash],segments:[...this.segments]});},arc(){},rect(){},closePath(){}};
 const element=()=>({checked:false,value:'',textContent:'',children:[],listeners:{},append(...items){this.children.push(...items);},addEventListener(name,fn){this.listeners[name]=fn;},getContext(){return context;},width:900,height:420});
 for(const match of html.matchAll(/\bid="([^"]+)"/g))elements.set(match[1],element());
 elements.get('data').textContent=html.match(/<script id="data"[^>]*>([\s\S]*?)<\/script>/)[1];elements.get('view').value='PLAN_XZ';
 const scripts=[...html.matchAll(/<script(?:\s[^>]*)?>([\s\S]*?)<\/script>/g)];
 const scope=vm.createContext({document:{getElementById:id=>elements.get(id)??null,createElement:element},console});
 vm.runInContext(scripts.at(-1)[1],scope,{timeout:1000});return {html,elements,strokes};
}
function presentation(){return buildRetainedDecisionPresentation({observations:[],subjectUuid:uuid,identity,request:{startTick:100,endTick:200}});}
test('all retained layers have OFF controls and empty related data renders without an exception',()=>{
 const p=presentation(),before=JSON.stringify(p),view=runView(p);
 for(const key of Object.keys(p.layers))assert.equal(view.elements.get(key).checked,false,key);
 assert.equal(view.strokes.length,0);assert.equal(JSON.stringify(p),before);
});
test('related projectiles draw their own segments and stable identity colors without cross-entity joins',()=>{
 const p=presentation();p.layers.relatedProjectiles.status='PARTIAL';
 p.layers.relatedProjectiles.traces=[1,2].map(n=>({trace:{trace_class:'PROJECTILE_ACTUAL',subject:{id:'00000000-0000-0000-0000-'+String(n).padStart(12,'0')},samples:[{sample_id:'a'+n,tick:190,x:n,y:64,z:0},{sample_id:'b'+n,tick:195,x:n+1,y:64,z:0}],segments:[{from_sample_id:'a'+n,to_sample_id:'b'+n}],gaps:[]}}));
 const before=JSON.stringify(p),view=runView(p);view.elements.get('relatedProjectiles').checked=true;view.elements.get('relatedProjectiles').listeners.change();
 assert.ok(new Set(view.strokes.map(s=>s.color)).size>=2);assert.equal(JSON.stringify(p),before);
 assert.match(view.elements.get('projectileLegend').textContent,/000000000001/);assert.match(view.elements.get('projectileLegend').textContent,/000000000002/);
 view.elements.get('tick').value=190;view.elements.get('tick').listeners.input();assert.equal(JSON.stringify(p),before);
});
test('visible gap summary distinguishes omitted source interval from age expiry and stays tied to the whole retained window',()=>{
 const p=presentation();p.layers.motion.trace.gaps=[{kind:'SOURCE_GAP',after_tick:130,before_tick:175}];
 const before=JSON.stringify(p),view=runView(p),summary=view.elements.get('gapStatus');
 assert.ok(summary,'a visible retained-window gap status is required');
 assert.match(summary.textContent,/指定区間全体/);assert.match(summary.textContent,/補間なし/);
 assert.match(summary.textContent,/SOURCE_GAP/);assert.match(summary.textContent,/130.*175/);
 view.elements.get('tick').value=120;view.elements.get('tick').listeners.input();
 assert.match(summary.textContent,/130.*175/,'cursor must not relabel a whole-window boundary');
 assert.equal(JSON.stringify(p),before);
});
test('gap summary bounds detailed rows and preserves each projectile identity without implying a complete trace',()=>{
 const p=presentation();p.layers.motion.trace.gaps=[];
 p.layers.relatedProjectiles.traces=[1,2].map(n=>({trace:{subject:{id:'00000000-0000-0000-0000-'+String(n).padStart(12,'0')},
   samples:[],segments:[],gaps:Array.from({length:3},(_,i)=>({kind:'SOURCE_GAP',after_tick:100+i*20,before_tick:115+i*20}))}}));
 const view=runView(p),summary=view.elements.get('gapStatus');assert.ok(summary);
 assert.match(summary.textContent,/6/);assert.match(summary.textContent,/000000000001/);assert.match(summary.textContent,/000000000002/);
 assert.match(summary.textContent,/省略/);assert.equal((summary.textContent.match(/SOURCE_GAP/g)??[]).length,4);
 const empty=runView(presentation());assert.match(empty.elements.get('gapStatus').textContent,/連続取得を保証しません/);
});
test('returned Path uses an opt-in distinct layer with bounded slot/cache/source inspection and no line over missing indices',()=>{
 const p=presentation(),node=index=>({index,x:index,y:64,z:0,g:index*10,h:2,f:index*10+2,costMalus:1,
   predecessorPresent:index>0,predecessorIdentity:{status:'NOT_EXPOSED',detail:index?'NODE_IDENTITY_LIMIT':'NULL_NODE'}});
 p.layers.returnedPath={...p.layers.returnedPath,status:'PARTIAL',tick:190,nodes:[node(0),node(2),node(3)],
   terminal:node(9),target:{x:10,y:64,z:0},queryNodesTruncated:true,source_observation_ids:['obs:returned:42'],
   data:{pathNodes:{status:'PARTIAL',data:{nodeCount:10,retainedNodeCount:4,truncated:true,distanceToTarget:1}}}};
 const before=JSON.stringify(p),view=runView(p);assert.ok(view.elements.get('returnedPath'));assert.equal(view.strokes.length,0);
 view.elements.get('returnedPath').checked=true;view.elements.get('returnedPath').listeners.change();
 const edges=view.strokes.filter(s=>s.dash.join(',')==='2,5');assert.equal(edges.length,1,'only actual adjacent slots 2 to 3');
 assert.equal(edges[0].segments.length,1);assert.match(view.elements.get('returnedPathDetails').textContent,/obs:returned:42/);
 assert.match(view.elements.get('returnedPathDetails').textContent,/g/);assert.match(view.elements.get('returnedPathDetails').textContent,/90/);
 assert.match(view.elements.get('returnedPathDetails').textContent,/Navigation/);assert.match(view.elements.get('returnedPathDetails').textContent,/省略/);
 assert.equal(JSON.stringify(p),before);
 const count=view.strokes.length;view.elements.get('view').value='ELEVATION';view.elements.get('view').listeners.change();
 assert.equal(view.strokes.length,count,'a single Path return does not create a tick/y trajectory');
 view.elements.get('view').value='PLAN_XZ';view.elements.get('tick').value=180;view.elements.get('tick').listeners.input();
 assert.equal(view.strokes.length,count,'future returned Path is hidden');assert.match(view.elements.get('returnedPathDetails').textContent,/未来/);
});
test('an independently retained terminal is a point, and unavailable returned Path does not reuse earlier geometry',()=>{
 const p=presentation();p.layers.returnedPath={...p.layers.returnedPath,status:'PARTIAL',tick:190,nodes:[],
   terminal:{index:9,x:9,y:64,z:0,gStatus:'NOT_EXPOSED'},target:null,
   data:{pathNodes:{status:'PARTIAL',data:{nodeCount:10,retainedNodeCount:4,truncated:true}}}};
 let view=runView(p);view.elements.get('returnedPath').checked=true;view.elements.get('returnedPath').listeners.change();
 assert.equal(view.strokes.filter(s=>s.dash.length).length,0);assert.ok(view.strokes.length>0,'separate actual terminal remains inspectable');
 assert.match(view.elements.get('returnedPathDetails').textContent,/NOT_EXPOSED/);
 p.layers.returnedPath={...p.layers.returnedPath,status:'NOT_EXPOSED',nodes:[],terminal:null,data:{pathNodes:{status:'NOT_EXPOSED',detail:'NULL_PATH'}}};
 view=runView(p);view.elements.get('returnedPath').checked=true;view.elements.get('returnedPath').listeners.change();
 assert.equal(view.strokes.length,0);assert.match(view.elements.get('returnedPathDetails').textContent,/NULL_PATH/);
});
