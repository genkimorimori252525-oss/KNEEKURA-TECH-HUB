// Real guard with fake editor APIs: not real Blockbench acceptance.
const {test}=require('node:test');const assert=require('node:assert/strict');
const crypto=require('node:crypto');const createGuard=require(process.env.KNEEKURA_TEST_GUARD);
const clone=v=>JSON.parse(JSON.stringify(v));
function fixture(){
 const config={schema_version:1,request_hash:'a'.repeat(64),token:'b'.repeat(64),asset_name:'celestial_staff',texture_size:[32,32],palette:['#d4af37','#864fc7'],allow_write:true};
 const state={active:null,projects:[],format:null,plugins:['blockbench_mcp'],cubes:0,textures:[],serverAlreadyRunning:false};
 const elements=[],calls=[];let pixels=Buffer.alloc(32*32*4);for(let i=0;i<pixels.length;i+=4)pixels.set([212,175,55,255],i);
 const native=()=>({meta:{model_format:'java_block'},java_block_version:'1.9.0',elements:elements.map(e=>clone(e)),groups:[],outliner:elements.map(e=>e.uuid),textures:[{uuid:'texture-1',width:32,height:32,source:'encoded:'+pixels.toString('base64')}],display:clone(state.display)});
 const model=()=>({elements:elements.map(e=>({name:e.name,from:clone(e.from),to:clone(e.to),faces:Object.fromEntries(Object.entries(e.faces).map(([k,v])=>[k,{uv:v.uv.map(n=>n/2),texture:'#0'}]))})),display:clone(state.display)});
 const host={now:()=>0,state:()=>state,configureProject:(p,c)=>{state.java_block_version=c.java_block_version;state.display=clone(c.display);},elementIdentity:id=>elements.find(e=>e.uuid===id),textureIdentity:id=>state.textures.find(e=>e.uuid===id),
 snapshot:()=>({native:native(),model:model(),rgba:pixels.toString('base64')}),hash:async value=>crypto.createHash('sha256').update(value).digest('hex'),
 invoke:async(a,p)=>{calls.push({action:a,args:clone(p)});
  if(a==='new_project'){state.active={uuid:'project-1'};state.projects=[state.active];state.format='java_block';return {};}
  if(a==='create_texture'){state.textures.push({uuid:'texture-1',width:32,height:32,ready:true});return {uuid:'texture-1'};}
  if(a==='add_cube'){const e={uuid:'cube-'+elements.length,type:'cube',name:p.name,from:p.from,to:p.to,faces:Object.fromEntries(Object.entries(p.faces).map(([k,v])=>[k,{uv:v.uv,texture:0}]))};elements.push(e);state.cubes++;return clone(e);}
  if(a==='edit_element'){const e=elements.find(e=>e.uuid===p.element);if(p.from)e.from=clone(p.from);if(p.to)e.to=clone(p.to);return clone(e);}
  if(a==='set_cube_uv'){const e=elements.find(e=>e.uuid===p.cube);for(const [f,v] of Object.entries(p.faces))e.faces[f].uv=clone(v.uv);return clone(e);}
  if(a==='paint_texture'){const o=p.ops[0],color=Buffer.from(o.color.slice(1),'hex');for(let y=o.y;y<o.y+o.height;y++)for(let x=o.x;x<o.x+o.width;x++)pixels.set([...color,255],(y*32+x)*4);return {painted:true};}
  if(a==='check_model')return {};
  throw Error('unexpected action '+a);
 }, editDisplay:(slot,property,value)=>{state.display[slot][property]=clone(value);return {slot};},capture:async()=>{throw Error('not needed');}};
 const guard=createGuard(config,host);let seq=0;
 const call=async(op,args={})=>guard.dispatch('kneekura_asset',{token:config.token,request_hash:config.request_hash,seq:seq++,project_uuid:state.active?.uuid||null,operation:op,arguments:args});
 const status=()=>guard.dispatch('kneekura_asset_status',{token:config.token,request_hash:config.request_hash});
 const open=async()=>{await call('begin');await call('texture',{fill:'#d4af37'});await call('cube',{name:'head',from:[5,16,6],to:[11,20,10],uv:[4,0,12,8]});return (await call('snapshot')).result;};
 const mutation=(snapshot,op='part_edit')=>({schema_version:1,request_hash:config.request_hash,project_uuid:'project-1',expected_generation:snapshot.generation,expected_snapshot_hash:snapshot.snapshot_hash,operation:op,target:{part_id:'head',property:'to',axis:1},expected:20,value:19});
 return {config,state,elements,calls,host,call,status,open,mutation};
}
test('seal generation zero, edit one owned part, and retain native UUID',async()=>{const f=fixture(),s=await f.open();assert.equal(s.generation,0);const before=JSON.parse(s.content);assert.equal(before.parts[0].native_uuid,'cube-0');const m=f.mutation(s);const result=await f.call('part_edit',m);assert.equal(result.completion,'CONFIRMED');assert.deepEqual(f.calls.at(-1),{action:'edit_element',args:{element:'cube-0',to:[11,19,10]}});const after=(await f.call('snapshot')).result;assert.equal(after.generation,1);assert.equal(JSON.parse(after.content).parts[0].native_uuid,'cube-0');assert.notEqual(after.snapshot_hash,s.snapshot_hash);});
for(const op of ['uv_edit','texture_edit','display_edit'])test('separate exact '+op,async()=>{const f=fixture(),s=await f.open(),m=f.mutation(s,op);
 if(op==='uv_edit')Object.assign(m,{target:{part_id:'head',face:'north',texture_id:'atlas'},expected:[4,0,12,8],value:[24,24,28,28]});
 if(op==='texture_edit')Object.assign(m,{target:{texture_id:'atlas',rect:[24,24,32,32]},expected:crypto.createHash('sha256').update(Buffer.from(Array(64).fill([212,175,55,255]).flat())).digest('hex'),value:'#864fc7'});
 if(op==='display_edit')Object.assign(m,{target:{slot:'gui',property:'translation',axis:1},expected:-4,value:-3});
 await f.call(op,m);assert.equal((await f.call('snapshot')).result.generation,1);
});
for(const fault of ['request','project','generation','hash','expected','extra','target'])test('reject stale/foreign '+fault+' before invoking',async()=>{const f=fixture(),s=await f.open(),m=f.mutation(s),n=f.calls.length;
 if(fault==='request')m.request_hash='c'.repeat(64);if(fault==='project')m.project_uuid='foreign';if(fault==='generation')m.expected_generation=1;if(fault==='hash')m.expected_snapshot_hash='c'.repeat(64);if(fault==='expected')m.expected=21;if(fault==='extra')m.path='/secret';if(fault==='target')m.target.part_id='foreign';
 await assert.rejects(f.call('part_edit',m));assert.equal(f.calls.length,n);
});
for(const fault of ['recreated_cube','duplicate_cube','recreated_texture','other_field'])test('quarantine drift '+fault,async()=>{const f=fixture(),s=await f.open(),m=f.mutation(s),n=f.calls.length;
 if(fault==='recreated_cube')f.elements[0]=clone(f.elements[0]);if(fault==='duplicate_cube'){f.elements.push(clone(f.elements[0]));f.state.cubes++;}if(fault==='recreated_texture')f.state.textures[0]=clone(f.state.textures[0]);if(fault==='other_field')f.elements[0].hidden=true;
 await assert.rejects(f.call('part_edit',m));assert.equal(f.calls.length,n);assert.equal((await f.status()).state,'UNKNOWN');
});
test('provider unrelated-field mutation never confirms',async()=>{const f=fixture(),s=await f.open(),original=f.host.invoke;f.host.invoke=async(a,p)=>{const r=await original(a,p);f.elements[0].hidden=true;return r;};await assert.rejects(f.call('part_edit',f.mutation(s)));assert.equal((await f.status()).state,'UNKNOWN');});
test('state drift during asynchronous hash never seals',async()=>{const f=fixture();f.host.hash=async()=>{f.elements[0].hidden=true;return 'f'.repeat(64);};await assert.rejects(f.open());assert.equal((await f.status()).state,'UNKNOWN');});
test('post-seal cube creation is refused without provider calls',async()=>{const f=fixture();await f.open();const n=f.calls.length;await assert.rejects(f.call('cube',{name:'new',from:[0,0,0],to:[1,1,1],uv:[0,0,1,1]}));assert.equal(f.calls.length,n);});
test('partial mutation remains UNKNOWN and cannot be replayed',async()=>{const f=fixture(),s=await f.open(),m=f.mutation(s);f.host.invoke=async()=>{f.elements[0].to[1]=19;throw Error('partial');};await assert.rejects(f.call('part_edit',m));assert.equal((await f.status()).state,'UNKNOWN');await assert.rejects(f.call('part_edit',m));});
for(const stage of ['region','after'])test('deadline includes '+stage+' hashing and late resolution stays UNKNOWN',async()=>{
 const f=fixture(),s=await f.open(),m=f.mutation(s,stage==='region'?'texture_edit':'part_edit');
 if(stage==='region')Object.assign(m,{target:{texture_id:'atlas',rect:[24,24,32,32]},expected:crypto.createHash('sha256').update(Buffer.from(Array(64).fill([212,175,55,255]).flat())).digest('hex'),value:'#864fc7'});
 const callsBefore=f.calls.length;const originalSet=global.setTimeout,originalClear=global.clearTimeout;let expire,finish,hashValue;
 global.setTimeout=callback=>{expire=callback;return 1;};global.clearTimeout=()=>{};
 let hashes=0;f.host.hash=value=>++hashes===1?new Promise(resolve=>{finish=resolve;hashValue=value;}):Promise.resolve(crypto.createHash('sha256').update(value).digest('hex'));
 let settled=false;const call=f.call(m.operation,m).then(()=>{settled=true;return 'confirmed';},()=>{settled=true;return 'unknown';});
 await Promise.resolve();await Promise.resolve();await Promise.resolve();
 const timerWasCreated=typeof expire==='function';if(expire)expire();
 await new Promise(resolve=>originalSet(resolve,10));const completedByDeadline=settled;
 if(finish)finish(crypto.createHash('sha256').update(hashValue).digest('hex'));
 await call;global.setTimeout=originalSet;global.clearTimeout=originalClear;
 assert.equal(timerWasCreated,true);assert.equal(completedByDeadline,true);
 assert.equal((await f.status()).state,'UNKNOWN');
 assert.equal((await f.status()).last_receipt.completion,'UNKNOWN');
 if(stage==='region')assert.equal(f.calls.length,callsBefore,'late prehash must never invoke the mutator');
});
