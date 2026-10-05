import test from 'node:test';
import assert from 'node:assert/strict';
import {writeFile,readFile} from 'node:fs/promises';
import path from 'node:path';
import {fixture} from '../../bridge/tests/result-export-fixture.mjs';
import {readExperimentDigest} from '../../experiment-cli.mjs';
const uuid='00000000-0000-0000-0000-000000000001';
test('digest reader uses sealed source inventory and existing journal export without rewriting finalized evidence',async t=>{
  const f=await fixture(t,{journal:'ACCEPTED'}),requestFile=path.join(f.runDir,'outside-request-input.json'),assertionsFile=path.join(f.runDir,'outside-assertions-input.json');
  await writeFile(requestFile,f.requestBytes);await writeFile(assertionsFile,f.assertionsBytes);
  const finalFile=path.join(f.runDir,'evidence/finalization.json'),before=await readFile(finalFile);
  const args={runDir:f.runDir,requestFile,assertionsFile,subjectUuid:uuid,targetRevision:1,arenaEpoch:0,window:{startTick:0,endTick:40},actionKeys:[{actionId:'action-1',idempotencyKey:'key-1'}]};
  const {digest}=await readExperimentDigest(args);assert.equal(digest.quality.status,'INCONCLUSIVE');
  assert(digest.actions.every(a=>a.status==='UNKNOWN'));assert.equal(digest.quality.coverage.sourceBinding.verifiedCanonical,true);
  assert.deepEqual(await readFile(finalFile),before);
  await writeFile(requestFile,Buffer.from('{}'));await assert.rejects(readExperimentDigest(args));
});
