import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import vm from 'node:vm';
import { fileURLToPath } from 'node:url';

const HERE=path.dirname(fileURLToPath(import.meta.url));
const src=fs.readFileSync(path.join(HERE,'store.js'),'utf8');
function makeStore(){
  const sandbox={};
  vm.createContext(sandbox);
  vm.runInContext(src,sandbox,{filename:'store.js'});
  return sandbox.SimStore.create();
}

test('trimmed forward-fill anchor remains queryable state but is not exposed as sampled evidence',()=>{
  const s=makeStore();
  s.append([
    JSON.stringify({t:0,ch:'spawn',id:1,type:'minecraft:zombie',role:'target',w:.6,h:1.95}),
    JSON.stringify({t:0,ch:'pos',id:1,x:0,y:64,z:0}),
    JSON.stringify({t:10,ch:'pos',id:1,x:5,y:64,z:0}),
  ].join('\n'));
  s.trimBefore(5);
  const state=s.stateAt('pos',1,5);
  assert.ok(state);
  assert.equal(state.x,0);
  const tr=s.trackOf(1);
  assert.deepEqual(tr.samples(5,10,10).map(p=>p.t),[10]);
  assert.equal(tr.sampleAtOrBefore(5),null);
  assert.equal(tr.sampleAtOrBefore(10).t,10);
});

test('a real sample exactly at the trim boundary remains sampled evidence',()=>{
  const s=makeStore();
  s.append([
    JSON.stringify({t:0,ch:'spawn',id:2,type:'minecraft:zombie',role:'target',w:.6,h:1.95}),
    JSON.stringify({t:0,ch:'pos',id:2,x:0,y:64,z:0}),
    JSON.stringify({t:5,ch:'pos',id:2,x:2,y:64,z:0}),
    JSON.stringify({t:10,ch:'pos',id:2,x:3,y:64,z:0}),
  ].join('\n'));
  s.trimBefore(5);
  const tr=s.trackOf(2);
  assert.deepEqual(tr.samples(5,10,10).map(p=>p.t),[5,10]);
  assert.equal(tr.sampleAtOrBefore(5).t,5);
});
