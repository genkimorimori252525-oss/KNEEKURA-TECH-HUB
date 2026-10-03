import test from 'node:test';
import assert from 'node:assert/strict';
import vm from 'node:vm';
import {buildRetainedDecisionPresentation} from '../decision-presentation.mjs';
import {renderDecisionPresentationHtml} from '../decision-view.mjs';
const uuid='00000000-0000-0000-0000-000000000001';
const identity={debugSessionId:'s',runId:'r',runSnapshotId:'snap',processEpoch:1,arenaEpoch:0,targetRevision:1};
function runView(presentation){
 const html=renderDecisionPresentationHtml(presentation),elements=new Map(),strokes=[];
 const context={strokeStyle:'',globalAlpha:1,clearRect(){},fillText(){},setLineDash(){},beginPath(){},moveTo(){},lineTo(){},stroke(){strokes.push({color:this.strokeStyle,alpha:this.globalAlpha});},arc(){},rect(){},closePath(){}};
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
