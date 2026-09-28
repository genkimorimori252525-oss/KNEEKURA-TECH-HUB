// Contract fixture: real guard, fake editor API. NOT Blockbench desktop verification.
const {test} = require('node:test');
const assert = require('node:assert/strict');
const createGuard = require(process.env.KNEEKURA_TEST_GUARD);
function fixture(overrides={}) {
  const config={schema_version:1,request_hash:'a'.repeat(64),token:'b'.repeat(64),asset_name:'staff',
    texture_size:[32,32],palette:['#d4af37','#864fc7'],allow_write:true};
  const state={active:null,projects:[],format:null,plugins:['blockbench_mcp'],cubes:0,textures:[],serverAlreadyRunning:false};
  const calls=[];
  let clock=0;
  const host={state:()=>state,now:()=>clock, invoke:async(action,args)=>{
    calls.push({action,args:JSON.parse(JSON.stringify(args))});
    if(action==='new_project') {const project={uuid:'project-1'};state.active=project;state.projects=[project];state.format='java_block';return {uuid:project.uuid};}
    if(action==='create_texture') {state.textures=[{uuid:'tex-1',ready:true,width:32,height:32}];return {uuid:'tex-1'};}
    if(action==='add_cube') {state.cubes++;return {uuid:'cube-'+state.cubes};}
    if(action==='check_model') return {issue_count:0};
    throw new Error('Unexpected raw action '+action);
  },...overrides};
  const guard=createGuard(config,host);
  const call=(seq,operation,args={},project_uuid=state.active?.uuid||null)=>guard.dispatch('kneekura_asset',
    {token:config.token,request_hash:config.request_hash,seq,project_uuid,operation,arguments:args});
  const status=()=>guard.dispatch('kneekura_asset_status',{token:config.token,request_hash:config.request_hash});
  const cube={name:'handle',from:[7,0,7],to:[9,16,9],uv:[0,0,4,4]};
  return {config,state,calls,host,guard,call,status,cube,setClock:n=>clock=n};
}
async function ready(f){await f.call(0,'begin');await f.call(1,'texture',{fill:'#d4af37'});}

test('guard creates only a fixed-format disposable project and records exact sequence',async()=>{
 const f=fixture(); const r=await f.call(0,'begin');assert.equal(r.completion,'CONFIRMED');
 assert.equal(r.verification.visual,'NOT_RUN');assert.equal(r.project_uuid,'project-1');
 assert.deepEqual(f.calls[0],{action:'new_project',args:{format:'java_block',name:'staff',texture_width:32,texture_height:32}});
 const s=await f.status();assert.equal(s.next_sequence,1);assert.equal(s.loaded_revision,'UNATTESTED');
});
for(const action of ['execute_script','install_plugin','uninstall_plugin','save_project','export_model','export_project','load_project','close_project','add_cube','new_project','constructor','__proto__']){
 test('raw '+action+' cannot bypass guard',async()=>{const f=fixture();await assert.rejects(f.guard.dispatch(action,{}));assert.equal(f.calls.length,0);});
}
test('default/false permission cannot begin',async()=>{const f=fixture();f.config.allow_write=false;const g=createGuard(f.config,f.host);
 await assert.rejects(g.dispatch('kneekura_asset',{token:f.config.token,request_hash:f.config.request_hash,seq:0,project_uuid:null,operation:'begin',arguments:{}}));assert.equal(f.calls.length,0);});
test('configuration detached, changing caller permission/token later is inert',async()=>{const f=fixture();f.config.token='c'.repeat(64);
 await assert.rejects(f.call(0,'begin'));assert.equal(f.calls.length,0);});
test('wrong token is rejected without reflecting it',async()=>{const f=fixture();const params={token:'c'.repeat(64),request_hash:'a'.repeat(64)};
 await assert.rejects(f.guard.dispatch('kneekura_asset_status',params),e=>!e.message.includes(params.token));});
for(const mode of ['active','hidden','wrongformat','otherplugin','oldserver']){
 test('pre-existing '+mode+' editor state blocks creation',async()=>{const f=fixture();
 if(mode==='active') {f.state.active={uuid:'owned'};f.state.projects=[f.state.active];}
 if(mode==='hidden') f.state.projects=[{uuid:'hidden'}];
 if(mode==='wrongformat') f.state.format='free';
 if(mode==='otherplugin') f.state.plugins.push('arbitrary_script_plugin');
 if(mode==='oldserver') f.state.serverAlreadyRunning=true;
 await assert.rejects(f.call(0,'begin'));assert.equal(f.calls.length,0);
 });
}
test('proper texture and cube calls contain only bounded generated fields',async()=>{const f=fixture();await ready(f);const r=await f.call(2,'cube',f.cube);
 assert.equal(r.completion,'CONFIRMED');assert.equal(f.state.cubes,1);
 const args=f.calls.at(-1).args;assert.equal(args.autouv,0);assert.equal(args.box_uv,false);
 assert.equal(args.faces.north.texture,'tex-1');assert.equal(args.faces.north.uv[2],4);
});
for(const [k,v] of [['path','../evil'],['data_url','file:///secret'],['format','free'],['code','fetch()'],['parent','foreign']]){
 test('parameter '+k+' rejected before action',async()=>{const f=fixture();await ready(f);const n=f.calls.length;
 await assert.rejects(f.call(2,'cube',{...f.cube,[k]:v}));assert.equal(f.calls.length,n);
 });
}
for(const [k,v] of [['from',[NaN,0,0]],['to',[1e999,1,1]],['from',[-17,0,0]],['to',[33,20,10]],['to',[0,0,0]],['uv',[0,0,0,0]],['uv',[0,0,33,1]],['name','../unsafe']]){
 test('bad cube '+k+' '+String(v)+' rejected',async()=>{const f=fixture();await ready(f);const n=f.calls.length;
 await assert.rejects(f.call(2,'cube',{...f.cube,[k]:v}));assert.equal(f.calls.length,n);
 });
}
test('duplicate and out-of-order calls are never retried',async()=>{const f=fixture();await ready(f);await f.call(2,'cube',f.cube);const n=f.calls.length;
 await assert.rejects(f.call(2,'cube',f.cube));await assert.rejects(f.call(4,'cube',f.cube));assert.equal(f.calls.length,n);
});
test('foreign project UUID is refused before mutation',async()=>{const f=fixture();await ready(f);const n=f.calls.length;
 await assert.rejects(f.call(2,'cube',f.cube,'foreign'));assert.equal(f.calls.length,n);
});
test('same UUID on a different project object is not ownership',async()=>{const f=fixture();await ready(f);f.state.active={uuid:'project-1'};f.state.projects=[f.state.active];const n=f.calls.length;
 await assert.rejects(f.call(2,'cube',f.cube));assert.equal(f.calls.length,n);assert.equal((await f.status()).state,'UNKNOWN');
});
test('project switch inside an awaited action poisons session',async()=>{const f=fixture();await ready(f);const original=f.host.invoke;
 f.host.invoke=async(a,p)=>{const r=await original(a,p);f.state.active={uuid:'foreign'};return r;};
 await assert.rejects(f.call(2,'cube',f.cube));assert.equal((await f.status()).state,'UNKNOWN');
 const n=f.calls.length;await assert.rejects(f.call(3,'cube',f.cube));assert.equal(f.calls.length,n);
});
test('throw after partial write yields UNKNOWN, not retry or false failure certainty',async()=>{const f=fixture();await ready(f);
 f.host.invoke=async()=>{f.state.cubes++;throw new Error('might have mutated; secret stack');};
 await assert.rejects(f.call(2,'cube',f.cube),e=>e.code==='UNKNOWN'&&!e.message.includes('secret stack'));
 const s=await f.status();assert.equal(s.state,'UNKNOWN');assert.equal(s.last_receipt.completion,'UNKNOWN');assert.equal(s.next_sequence,3);
});
test('concurrent second action cannot enter the upstream handler',async()=>{const f=fixture();await ready(f);let finish;
 f.host.invoke=()=>new Promise(r=>finish=r);const first=f.call(2,'cube',f.cube);
 await assert.rejects(f.call(3,'cube',f.cube));f.state.cubes++;finish({uuid:'x'});await first;
});
test('unfinished texture load must not be accepted by a timer-based upstream success',async()=>{const f=fixture();await f.call(0,'begin');
 f.host.invoke=async()=>{f.state.textures=[{uuid:'tex-1',ready:false,width:32,height:32}];return {uuid:'tex-1'};};
 await assert.rejects(f.call(1,'texture',{fill:'#d4af37'}));assert.equal((await f.status()).state,'UNKNOWN');
});
test('extra texture or external cube edit prevents continuing',async()=>{const f=fixture();await ready(f);f.state.cubes=1000;
 await assert.rejects(f.call(2,'cube',f.cube));assert.equal((await f.status()).state,'UNKNOWN');
});
test('upstream numeric success is not structural/visual/runtime PASS',async()=>{const f=fixture();await ready(f);f.host.invoke=async()=>0;
 const r=await f.call(2,'inspect');assert.equal(r.completion,'CONFIRMED');assert.equal(r.result,0);
 assert.deepEqual(r.verification,{structural:'NOT_RUN',visual:'NOT_RUN',runtime:'NOT_RUN'});
});
test('lease expiry prevents writes; status remains readable',async()=>{const f=fixture();await ready(f);f.setClock(900001);
 await assert.rejects(f.call(2,'cube',f.cube));assert.equal((await f.status()).state,'UNKNOWN');
});
test('response overflow after mutation poisons session rather than reporting completion',async()=>{const f=fixture();await ready(f);f.host.invoke=async()=>({data:'x'.repeat(1024*1024+1)});
 await assert.rejects(f.call(2,'inspect'));assert.equal((await f.status()).state,'UNKNOWN');
});

test('actual pinned new_project status has no UUID; bind the newly created Project object',async()=>{
 const f=fixture(), original=f.host.invoke;
 f.host.invoke=async(action,args)=>{const out=await original(action,args);
  if(action==='new_project')return {name:'staff',format:'java_block',texture_width:32,texture_height:32,cubes:0,groups:0,textures:0,animations:0,mode:'edit'};
  return out;
 };
 const r=await f.call(0,'begin');assert.equal(r.project_uuid,'project-1');assert.equal(r.completion,'CONFIRMED');
});
test('no asynchronous gap between project check and starting a mutator',async()=>{
 const f=fixture();await ready(f);const original=f.host.invoke;let seen;
 f.host.invoke=(action,args)=>{seen=f.state.active;return original(action,args);};
 const expected=f.state.active;const pending=f.call(2,'cube',f.cube);
 const other={uuid:'other'};f.state.active=other;f.state.projects=[other];
 await assert.rejects(pending);assert.equal(seen,expected,'mutator must not start against a switched project');
});
for(const value of [NaN,Infinity,-Infinity]){
 test('nonfinite clock refuses mutation: '+value,async()=>{const f=fixture();await ready(f);const before=f.calls.length;
  f.setClock(value);await assert.rejects(f.call(2,'cube',f.cube));assert.equal(f.calls.length,before);
 });
}
test('timed out write remains UNKNOWN after late completion; no replay or new writes',async()=>{
 const f=fixture();await ready(f);let complete;
 f.host.invoke=()=>new Promise(r=>{complete=r;});
 await assert.rejects(f.call(2,'cube',f.cube),e=>e.code==='UNKNOWN');
 assert.equal((await f.status()).state,'UNKNOWN');
 f.state.cubes++;complete({uuid:'late'});await Promise.resolve();
 await assert.rejects(f.call(2,'cube',f.cube));await assert.rejects(f.call(3,'cube',{...f.cube,name:'another'}));
 assert.equal((await f.status()).last_receipt.completion,'UNKNOWN');
});
