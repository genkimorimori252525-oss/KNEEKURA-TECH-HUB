import test from 'node:test';
import assert from 'node:assert/strict';
import {buildTankPresentationResource} from '../tank-resource.mjs';
import {sha256,stableJson} from '../json.mjs';
const recipe={v:1,kind:'tank_recipe',dimension:'minecraft:overworld',origin:{x:0,y:64,z:0},dimensions:{width:16,height:8,depth:16},presentation:{gridSpacing:1,mode:'NATIVE'}};
const saved={status:'GEOMETRY_VERIFIED',recipe,recipeHash:sha256(stableJson(recipe)),displayMode:'NATIVE'};
const profile={kind:'OBSERVE_GRID',grid:true,brightness:false,motion:false,decisionChannels:[]};
test('new resource capsule contains the exact verified saved marker; inputs stay immutable',()=>{
  const before=JSON.stringify(saved),artifact=buildTankPresentationResource({saved,profile});
  assert(Buffer.isBuffer(artifact));assert.equal(artifact.readUInt32LE(0),0x04034b50);
  assert.equal(artifact.readUInt16LE(8),0); // standard uncompressed ZIP, usable by native ZipInputStream
  const nameLength=artifact.readUInt16LE(26),dataLength=artifact.readUInt32LE(18);
  assert.equal(artifact.subarray(30,30+nameLength).toString(),'kneekura/tank-presentation.json');
  assert.deepEqual(JSON.parse(artifact.subarray(30+nameLength,30+nameLength+dataLength).toString()),saved);
  assert.equal(JSON.stringify(saved),before);
  assert.equal(buildTankPresentationResource({saved,profile:{...profile,kind:'BENCHMARK',grid:false}}).length,22);
});
test('preparation refuses hash, geometry and display mismatches before registration',()=>{
  for(const wrong of [{...saved,recipeHash:'b'.repeat(64)},{...saved,status:'UNKNOWN'},
    {...saved,displayMode:'OBSERVATION_BRIGHT'}, {...saved,recipe:{...recipe,dimensions:{width:999,height:8,depth:16}}}])
    assert.throws(()=>buildTankPresentationResource({saved:wrong,profile}),/TANK/);
});
test('saved owner metadata and credentials do not enter the resource capsule',()=>{
  const artifact=buildTankPresentationResource({saved:{...saved,handshakeNonce:'PRIVATE_NONCE',owner:{path:'C:/private/world'}},profile});
  assert.equal(artifact.includes(Buffer.from('PRIVATE_NONCE')),false);
  assert.equal(artifact.includes(Buffer.from('C:/private/world')),false);
});
