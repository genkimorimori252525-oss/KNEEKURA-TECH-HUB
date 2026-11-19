import test from 'node:test';
import assert from 'node:assert/strict';
import {mkdtemp,mkdir,writeFile,readFile,rm} from 'node:fs/promises';
import path from 'node:path';
import os from 'node:os';
import {sha256} from '../../bridge/json.mjs';
import {request as registeredRequest} from './visual-fixture.mjs';
import {buildReproductionManifest,writeReproductionManifest} from '../reproduction-manifest.mjs';
const requestBytes=Buffer.from(JSON.stringify(registeredRequest(),null,2)),assertionsBytes=Buffer.from(JSON.stringify(registeredRequest().assertions,null,1));
const sourceBinding={requestHash:sha256(requestBytes),assertionsHash:sha256(assertionsBytes),canonicalFileHash:'a'.repeat(64),finalizationHash:'b'.repeat(64)};
const input={requestBytes,assertionsBytes,sourceBinding,worldBinding:{authorityHash:'a'.repeat(64),copyBaselineHash:'b'.repeat(64),fixtureHash:'c'.repeat(64)},observerProfile:{channels:['SERVER_ENTITY_STATE']},comparison:null};
test('manifest preserves original byte hashes and blocks private fields and stale owner reuse',()=>{
  const m=buildReproductionManifest(input);assert.equal(m.request.contentHash,sha256(requestBytes));assert.equal(m.assertions.contentHash,sha256(assertionsBytes));
  assert.equal(m.replay.requiresNewRunIdentity,true);assert.equal(m.replay.requiresNewOwnerRegistration,true);assert.equal(m.images.status,'NOT_CAPTURED');
  assert.throws(()=>buildReproductionManifest({...input,requestBytes:Buffer.from(JSON.stringify(registeredRequest()))}),/HASH/);
  assert.throws(()=>buildReproductionManifest({...input,sourceBinding:{...sourceBinding,runDir:'C:/private/run'}}),/PRIVATE/);
  assert.throws(()=>buildReproductionManifest({...input,observerProfile:{credential:'private'}}),/PRIVATE/);
  assert.throws(()=>buildReproductionManifest({...input,observerProfile:{reuseOwner:true}}),/OWNER/);
  assert.throws(()=>buildReproductionManifest({...input,assertionsBytes:Buffer.from('[]'),sourceBinding:{...sourceBinding,assertionsHash:sha256('[]')}}),/ASSERTION/);
});
test('manifest output is exclusive and cannot write inside finalized or retained run',async t=>{
  const root=await mkdtemp(path.join(os.tmpdir(),'tank-replay-'));t.after(()=>rm(root,{recursive:true,force:true}));const run=path.join(root,'run');await mkdir(run);
  const m=buildReproductionManifest(input);await assert.rejects(writeReproductionManifest({manifest:m,output:path.join(run,'new.json'),runDir:run}),/OUTSIDE/);
  const output=path.join(root,'manifest.json');await writeReproductionManifest({manifest:m,output,runDir:run});const before=await readFile(output);
  await assert.rejects(writeReproductionManifest({manifest:m,output,runDir:run}),{code:'EEXIST'});assert.deepEqual(await readFile(output),before);
  const other=path.join(root,'other-run');await mkdir(path.join(other,'evidence'),{recursive:true});await writeFile(path.join(other,'evidence','finalization.json'),'{}');
  await assert.rejects(writeReproductionManifest({manifest:m,output:path.join(other,'evidence','new.json'),runDir:run}),/OUTSIDE/);
});
