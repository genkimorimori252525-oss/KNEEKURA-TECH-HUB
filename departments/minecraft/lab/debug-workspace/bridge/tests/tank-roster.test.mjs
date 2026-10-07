import test from 'node:test';
import assert from 'node:assert/strict';
import path from 'node:path';
import {readFile,readdir,writeFile} from 'node:fs/promises';
import {preparedOwner} from './owner-action-fixture.mjs';
// Optional import lets the RED assertion identify the missing public contract.
const roster=await import('../tank-roster.mjs').catch(e=>{if(e.code==='ERR_MODULE_NOT_FOUND')return {};throw e;});
test('room reader exposes explicit bounded publication and original-slot reconciliation',()=>{
 assert.equal(typeof roster.publishTankRoster,'function');assert.equal(typeof roster.inspectTankRoster,'function');
});
test('old owner does not gain room-read authority',async t=>{
 const f=await preparedOwner(t);assert.equal(f.prepared.tankObservation,null);
 assert.equal(typeof roster.publishTankRoster,'function');
 await assert.rejects(roster.publishTankRoster({...f.controlOptions,sampleIndex:0}),/TANK_ROSTER_SCOPE/);
});
test('read slots are owner-wide sequential, immutable and unknown reads cannot be retried at a fresh index',async t=>{
 const f=await preparedOwner(t,{observation:true}),o=f.controlOptions;
 await writeFile(path.join(f.runDir,'control/owner-status.json'),JSON.stringify({...f.status,leaseRemainingMs:5000}));
 await assert.rejects(roster.publishTankRoster({...o,sampleIndex:1}),/PRIOR_RECONCILIATION/);
 await assert.rejects(roster.publishTankRoster({...o,sampleIndex:2}));
 assert.equal((await roster.publishTankRoster({...o,sampleIndex:0})).status,'REQUESTED');
 const file=path.join(f.runDir,'control/tank-roster/00/request.json'),before=await readFile(file);
 assert.equal((await roster.publishTankRoster({...o,sampleIndex:0})).status,'ALREADY_REQUESTED');
 assert.deepEqual(await readFile(file),before);
 assert.equal((await roster.inspectTankRoster({...o,sampleIndex:0})).status,'UNKNOWN');
 await assert.rejects(roster.publishTankRoster({...o,sampleIndex:1}),/PRIOR_RECONCILIATION/);
 assert.deepEqual(await readdir(path.join(f.runDir,'control/tank-roster')),['00']);
});
test('structured roster enforces half-open body overlap, local xyz and partial absence semantics',async t=>{
 const f=await preparedOwner(t,{observation:true}),p=f.prepared,g=p.grant;
 const identity=Object.fromEntries(['debugSessionId','runId','runSnapshotId','processEpoch','experimentId','generation','requestHash','arenaId','arenaEpoch','baselineHash'].map(k=>[k,g[k]]));identity.arenaRevision=0;
 const payload={schemaVersion:1,kind:'tank_room_roster',identity,ownerEnvelopeHash:p.envelopeHash,tankObservationHash:p.envelope.tankObservationHash,sampleIndex:0,dimension:'minecraft:overworld',boundsSemantics:'MIN_INCLUSIVE_MAX_EXCLUSIVE',min:[0,0,0],max:[16,8,16],serverTick:42,gameTime:100,status:'COMPLETE',missingEntityNotAbsent:false,subsetSelection:'COMPLETE_SCOPE_UUID_SORTED',coverage:{allChunksLoaded:true,missingChunks:[],truncationReasons:[]},limits:{maxEntities:4,maxSamples:2,maxPassengerDepth:8,maxPacketBytes:65536},entities:[{uuid:g.subjects[0].uuid,entityType:'minecraft:pig',world:[-.1,1,1],local:[-.1,1,1],aabbMin:[-.5,1,.5],aabbMax:[.5,2,1.5],living:true,mob:true,player:false,knownSubjectId:'pig',vehicleUuid:null,passengerUuids:[],fullyContained:false}]};
 assert.equal(roster.validateTankRoster(payload,p,0).entities.length,1);
 for(const reason of ['ENTITY_LIMIT','PASSENGER_DEPTH','BYTE_LIMIT']){
  const partial=structuredClone(payload);partial.coverage.truncationReasons=[reason];partial.status='PARTIAL';partial.missingEntityNotAbsent=true;partial.subsetSelection='NATIVE_ENUMERATION_SUBSET_UUID_SORTED';
  assert.equal(roster.validateTankRoster(partial,p,0).status,'PARTIAL');
  assert.throws(()=>roster.validateTankRoster({...partial,missingEntityNotAbsent:false},p,0),/COMPLETENESS/);
 }
 const unloaded=structuredClone(payload);unloaded.coverage={allChunksLoaded:false,missingChunks:[[0,0]],truncationReasons:[]};
 assert.throws(()=>roster.validateTankRoster(unloaded,p,0),/COMPLETENESS/);
 unloaded.status='PARTIAL';unloaded.missingEntityNotAbsent=true;unloaded.subsetSelection='NATIVE_ENUMERATION_SUBSET_UUID_SORTED';assert.equal(roster.validateTankRoster(unloaded,p,0).status,'PARTIAL');
 const touches=structuredClone(payload);touches.entities[0].aabbMax[0]=0;assert.throws(()=>roster.validateTankRoster(touches,p,0),/GEOMETRY/);
 const drift=structuredClone(payload);drift.entities[0].local[0]=1;assert.throws(()=>roster.validateTankRoster(drift,p,0),/GEOMETRY/);
 for(const mutate of [r=>r.identity.extra=true,r=>r.sampleIndex=2,r=>r.coverage.missingChunks=[[1,0]],r=>r.coverage.truncationReasons=['BYTE_LIMIT','BYTE_LIMIT'],r=>r.entities[0].uuid+='\n']){
  const bad=structuredClone(payload);mutate(bad);assert.throws(()=>roster.validateTankRoster(bad,p,bad.sampleIndex));
 }
});
