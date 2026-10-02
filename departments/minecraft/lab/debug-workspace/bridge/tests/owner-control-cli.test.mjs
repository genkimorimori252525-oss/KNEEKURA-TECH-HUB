import test from 'node:test';
import assert from 'node:assert/strict';
import {writeFile,readdir} from 'node:fs/promises';
import {spawnSync} from 'node:child_process';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
import {preparedOwner} from './owner-action-fixture.mjs';
const cli=fileURLToPath(new URL('../owner-control-cli.mjs',import.meta.url));
async function fixture(t){
 const f=await preparedOwner(t,{capture:true}),ownerFile=path.join(f.root,'owner.json'),commandFile=path.join(f.inputs,'control-command.json');
 const identity={...Object.fromEntries(['debugSessionId','runId','runSnapshotId','processEpoch'].map(k=>[k,f.identity[k]])),experimentId:f.prepared.request.experiment_id,requestHash:f.prepared.envelope.requestHash};
 await writeFile(ownerFile,JSON.stringify({schemaVersion:1,runtimeRoot:f.runtimeRoot,inputRoot:f.inputs,run:{runDir:f.runDir,identity,ownerEnvelopeHash:f.prepared.envelopeHash}}));
 return {...f,async call(operation,fields={}){await writeFile(commandFile,JSON.stringify({schemaVersion:1,operation,requestHash:identity.requestHash,...fields}));const result=spawnSync(process.execPath,[cli,'--owner',ownerFile,'--request',commandFile],{encoding:'utf8',timeout:5000});assert.ifError(result.error);return {code:result.status,value:JSON.parse(result.stdout),stderr:result.stderr};}};
}
test('fixed CLI emits minimal reported owner/action/capture protocol without private inputs',async t=>{
 const f=await fixture(t);
 const inspected=await f.call('inspect_owner');assert.equal(inspected.code,0);assert.equal(inspected.value.status,'OWNER_RECORDED');
 assert.deepEqual(Object.keys(inspected.value).sort(),['schemaVersion','operation','requestHash','status','runtimeAttestation','ownerEnvelopeHash'].sort());
 const submit=await f.call('submit_action',{selectedActionId:'wait'});assert.equal(submit.code,0);assert.equal(submit.value.status,'REQUESTED');
 const query=await f.call('inspect_action',{selectedActionId:'wait'});assert.equal(query.value.status,'REQUESTED');assert.equal(query.value.dispatchAllowed,false);assert.deepEqual(query.value.evidenceHashes,[]);
 const capture=await f.call('request_capture',{captureIndex:0});assert.equal(capture.value.status,'REQUESTED');
 for(const response of [inspected,submit,query,capture]){assert.equal(response.value.runtimeAttestation,'NOT_ESTABLISHED');assert.equal(JSON.stringify(response).includes(f.root),false);assert.equal(JSON.stringify(response).includes(f.identity.handshakeNonce),false);assert.equal(response.stderr,'');}
});
test('CLI rejects generic execution and caller action parameters before any intent',async t=>{
 const f=await fixture(t);
 for(const [op,args] of [['execute',{}],['start',{}],['submit_action',{selectedActionId:'wait',args:{ticks:1200}}]]){
  const response=await f.call(op,args);assert.equal(response.code,2);assert.equal(response.value.status,'BLOCKED');assert.equal(response.stderr,'');
 }
 await assert.rejects(readdir(path.join(f.runDir,'control/actions')),{code:'ENOENT'});
});
