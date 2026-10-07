import test from 'node:test';
import assert from 'node:assert/strict';
import path from 'node:path';
import {writeFile,readFile} from 'node:fs/promises';
import {sha256,stableJson} from '../json.mjs';
import {ownerPrelaunchFixture} from './owner-prelaunch-fixtures.mjs';
import {prepareOwnerControl,readPreparedOwnerControl} from '../owner-prelaunch.mjs';

const recipe={v:1,kind:'tank_recipe',dimension:'minecraft:overworld',origin:{x:0,y:224,z:0},dimensions:{width:52,height:24,depth:52},presentation:{mode:'NATIVE',gridSpacing:1}};
const saved={status:'GEOMETRY_VERIFIED',displayMode:'NATIVE',recipe,recipeHash:'sha256:'+sha256(stableJson(recipe))};
const scope={schemaVersion:1,scope:'TANK_OBSERVATION_READ',dimensionId:'minecraft:overworld',min:[0,224,0],max:[52,248,52],recipeHash:sha256(stableJson(recipe)),maxEntities:64,maxSamples:2};

test('owner seals recipe-derived observation bounds independently of small action grant',async t=>{
 const f=await ownerPrelaunchFixture(t);await writeFile(path.join(f.operator.worldRegistration.canonicalWorldRoot,'kneekura-tank-owner.json'),JSON.stringify(saved));
 f.operator.tankObservation=scope;f.operator.worldRegistration.permissions.push(scope.scope);
 const p=await prepareOwnerControl({...f.options,operatorRegistration:await f.select()});
 assert.deepEqual(p.tankObservation,scope);assert.deepEqual(p.grant.bounds,{min:[0,0,0],max:[8,8,8]});
 assert.equal(p.envelope.tankObservationHash,sha256(await readFile(path.join(f.runDir,'control/owner-tank-observation.json'))));
 assert.deepEqual((await readPreparedOwnerControl({runDir:f.runDir,envelopeHash:p.envelopeHash})).tankObservation,scope);
});
test('observation scope rejects unrelated bounds and missing separate read permission',async t=>{
 for(const missingPermission of [true,false]){
  const f=await ownerPrelaunchFixture(t);await writeFile(path.join(f.operator.worldRegistration.canonicalWorldRoot,'kneekura-tank-owner.json'),JSON.stringify(saved));
  f.operator.tankObservation={...scope,max:missingPermission?scope.max:[51,248,52]};
  if(!missingPermission)f.operator.worldRegistration.permissions.push(scope.scope);
  await assert.rejects(prepareOwnerControl({...f.options,operatorRegistration:await f.select()}),/TANK_OBSERVATION_(PERMISSION|RECIPE)/);
 }
});
