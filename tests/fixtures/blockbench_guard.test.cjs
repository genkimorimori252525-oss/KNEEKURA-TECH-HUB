// Host doubles only: this is NOT a Blockbench desktop/renderer acceptance test.
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const {test} = require('node:test');
const file = path.join(__dirname, '../../src/kneekura_tech_hub/minecraft/blockbench_guard.js');
function factory() {
  assert.ok(fs.existsSync(file), 'The guarded provider dispatcher has not been implemented');
  const box = {setTimeout, clearTimeout, TextEncoder};
  vm.createContext(box); vm.runInContext(fs.readFileSync(file, 'utf8'), box);
  return box.createAssetGuard;
}
function setup(options={}) {
  const config = {session_id:'s'.repeat(32), request_hash:'a'.repeat(64), token:'t'.repeat(64),
    asset_id:'probe:staff', texture_size:[16,16], texture_data_url:'data:image/png;base64,AAAA',
    blueprint:{schema_version:1, texture_rows:['0'.repeat(16)],
      cubes:[{name:'handle',from:[7,0,7],to:[9,20,9],uv:[0,0,2,16]}],
      display:{gui:{rotation:[0,0,0],translation:[0,0,0],scale:[1,1,1]}}},
    required_views:['front','left','back'], timeout_ms:1000};
  const project = {}; const events=[];
  const state={active:null, foreign:false, extraPlugin:false, fingerprint:'before', loaded:true};
  const host={
    epoch:()=> 'e'.repeat(32),
    assertEmpty(){events.push('empty'); if(state.active||state.extraPlugin) throw Error('busy editor');},
    project(){return state.active;},
    assertOwned(p){if(state.foreign||state.extraPlugin||state.active!==p) throw Error('wrong project');},
    async createProject(c){events.push('create'); state.active=project;},
    async createTexture(c){events.push('texture'); if(options.texture) await options.texture(state);},
    assertTexture(){if(!state.loaded) throw Error('image did not load');},
    async createCubes(c){events.push('cubes'); if(options.cubes) await options.cubes(state);},
    async setDisplay(c){events.push('display');},
    async exportBytes(){events.push('export'); return {model:'{}',native:'{}',texture:'data:image/png;base64,AAAA'};},
    async fingerprint(){return state.fingerprint;},
    async screenshot(view){events.push(view); if(options.shot) await options.shot(state,view);
      return 'data:image/png;base64,AAAA';},
  };
  const dispatch=factory()(config,host);
  const auth={token:config.token,session_id:config.session_id,request_hash:config.request_hash};
  const args={...auth,epoch:'e'.repeat(32),operation_id:'o'.repeat(32)};
  return {dispatch,auth,args,config,state,events};
}

test('a sealed build returns separately labelled bytes, not a visual pass', async()=>{
  const x=setup(); let st=await x.dispatch('kneekura_asset_status',x.auth);
  assert.equal(st.phase,'READY'); assert.equal(st.epoch,x.args.epoch);
  const r=await x.dispatch('kneekura_asset_build',x.args);
  assert.equal(r.phase,'EXPORTED_NOT_REVIEWED'); assert.equal(r.request_hash,x.auth.request_hash);
  assert.deepEqual(Object.keys(r.views).sort(),['back','front','left']);
  assert.equal(r.verification.visual,'NOT_RUN'); assert.equal(r.verification.runtime,'NOT_RUN');
  assert.equal(r.operation_id,x.args.operation_id);
  assert.equal(x.events.filter(v=>v==='create').length,1);
  assert.ok(!JSON.stringify(r).includes(x.auth.token));
  st=await x.dispatch('kneekura_asset_status',x.auth);
  assert.equal(st.phase,'EXPORTED_NOT_REVIEWED');
});
for(const action of ['execute_script','install_plugin','uninstall_plugin','export_project','save_project',
                     'load_project','new_project','add_cubes','get_status','constructor','toString','__proto__']) {
  test('provider denies raw upstream action '+action,async()=>{
    const x=setup(); await assert.rejects(()=>x.dispatch(action,x.auth)); assert.equal(x.events.length,0);
  });
}
for(const field of ['token','session_id','request_hash','epoch','operation_id']) {
  test('mismatched/invalid '+field+' never creates a project',async()=>{
    const x=setup(); const args={...x.args,[field]:'wrong'};
    await assert.rejects(()=>x.dispatch('kneekura_asset_build',args)); assert.equal(x.events.length,0);
  });
}
test('runtime callers cannot smuggle blueprint or file paths',async()=>{
  for(const field of ['path','blueprint','params','script']) {
    const x=setup(); await assert.rejects(()=>x.dispatch('kneekura_asset_build',{...x.args,[field]:'anything'}));
    assert.equal(x.events.length,0);
  }
});
test('existing project is never closed or overwritten',async()=>{
  const x=setup(); const other={}; x.state.active=other;
  await assert.rejects(()=>x.dispatch('kneekura_asset_build',x.args));
  assert.strictEqual(x.state.active,other); assert.ok(!x.events.includes('create'));
});
test('an additional plugin prevents mutations',async()=>{
  const x=setup(); x.state.extraPlugin=true;
  await assert.rejects(()=>x.dispatch('kneekura_asset_build',x.args)); assert.ok(!x.events.includes('create'));
});
test('a switched project during an await taints the session and stops further actions',async()=>{
  const x=setup({texture:async state=>{state.foreign=true;}});
  await assert.rejects(()=>x.dispatch('kneekura_asset_build',x.args));
  assert.ok(!x.events.includes('cubes')); assert.equal((await x.dispatch('kneekura_asset_status',x.auth)).phase,'TAINTED');
});
test('same-project edits during screenshot invalidate the captured generation',async()=>{
  const x=setup({shot:async(state,view)=>{if(view==='front')state.fingerprint='edited';}});
  await assert.rejects(()=>x.dispatch('kneekura_asset_build',x.args)); assert.ok(!x.events.includes('left'));
});
test('a texture timeout is not image-load success',async()=>{
  const x=setup({texture:async state=>{state.loaded=false;}});
  await assert.rejects(()=>x.dispatch('kneekura_asset_build',x.args)); assert.ok(!x.events.includes('cubes'));
});
test('replaying even the same operation does not repeat a mutation',async()=>{
  const x=setup(); await x.dispatch('kneekura_asset_build',x.args);
  await assert.rejects(()=>x.dispatch('kneekura_asset_build',x.args));
  await assert.rejects(()=>x.dispatch('kneekura_asset_build',{...x.args,operation_id:'n'.repeat(32)}));
  assert.equal(x.events.filter(v=>v==='create').length,1);
});
test('concurrent build calls cannot enter the same editor',async()=>{
  let release; const waiting=new Promise(r=>release=r);
  const x=setup({texture:()=>waiting}); const first=x.dispatch('kneekura_asset_build',x.args);
  await new Promise(r=>setTimeout(r,0));
  await assert.rejects(()=>x.dispatch('kneekura_asset_build',x.args)); release(); await first;
  assert.equal(x.events.filter(v=>v==='create').length,1);
});
test('deadline taints the session; late async completion never starts the next mutation',async()=>{
  let release; const waiting=new Promise(r=>release=r);
  const x=setup({texture:()=>waiting});
  // Fresh guard to exercise the configurable bounded deadline, not mutation of sealed config.
  x.config.timeout_ms=20;
  // Default config is deep-copied. The existing guard must retain 1000 ms.
  const started=Date.now(); const pending=x.dispatch('kneekura_asset_build',x.args);
  await assert.rejects(()=>pending);
  assert.ok(Date.now()-started>=900); release(); await new Promise(r=>setTimeout(r,5));
  assert.ok(!x.events.includes('cubes'));
  assert.equal((await x.dispatch('kneekura_asset_status',x.auth)).phase,'TAINTED');
});
