import { readFile, writeFile, mkdir, rm } from 'node:fs/promises';
import path from 'node:path';
import { fixture as visualFixture, request } from '../../evidence/tests/visual-fixture.mjs';
import { compileVisualPacket, persistVisualPacket } from '../../evidence/visual-compiler.mjs';
import { finalizeEvidenceRun } from '../../evidence/finalize.mjs';
import { beginAction, recordActionOutcome } from '../action-journal.mjs';
import { sha256, stableJson } from '../json.mjs';
import { writeImmutableRunSnapshot } from '../../core.mjs';
export async function fixture(t,{journal='VERIFIED',effect=true,visual=false,partial=false,sparseProducer=false,requestValue=null,requestBytesOverride=null,assertionsBytesOverride=null,privateRow=false,effectSide='SERVER',effectOverride={},trailingPartial=false,numericSnapshotKeys=false}={}) {
 const req=requestValue??request();const requestBytes=requestBytesOverride??Buffer.from(stableJson(req));const assertionsBytes=assertionsBytesOverride??Buffer.from(stableJson(req.assertions));
 const f=await visualFixture(t,{request:req,mutate:m=>{m.identity.requestHash=sha256(requestBytes);}});
 f.requestBytes=requestBytes;f.assertionsBytes=assertionsBytes;
 const identity={debugSessionId:'session',runId:'run',runSnapshotId:'run-snapshot',processEpoch:1,experimentId:req.experiment_id};
 const binding={schema_version:1,experiment_id:req.experiment_id,generation:1,request_hash:sha256(requestBytes),target:req.target,
  arena_id:req.arena.arena_id,arena_baseline_hash:req.arena.baseline_hash,assertions_hash:sha256(assertionsBytes)};
 const body={schemaVersion:1,snapshotId:identity.runSnapshotId,createdAt:'2026-10-01T00:00:00.000Z',debugProfile:'profile',workspaceId:'workspace',
  debugSessionId:identity.debugSessionId,runId:identity.runId,processEpoch:1,worldName:'KNEEKURA_DEBUG_WORLD',
  source:{revision:req.target.source_revision},observer:{forgeBridgeSourceDir:'/private/compiler/source'},build:{status:'DISK_ONLY'},
  runtime:{attestation:'CLASS_RESOURCE_ONLY_NOT_RUNTIME_MATERIAL_EQUIVALENCE'},techHub:binding};
 if(numericSnapshotKeys)body.runtime.sample={2:'two',10:'ten'};
 const snapshot=await writeImmutableRunSnapshot(path.join(f.runDir,'run-snapshot.json'),body);
 const snapshotBytes=await readFile(path.join(f.runDir,'run-snapshot.json'));
 await writeFile(path.join(f.runDir,'process.log'),'DO NOT EXPORT /private/raw-process-secret');
 const effectRow={observationId:'obs:action:1',processEpoch:1,arenaEpoch:0,resourceEpoch:0,writerId:'action',writerSeq:1,level:'L2',lane:'ACTION_APPLIED',
  observedAt:'2026-10-01T00:00:00.001Z',gameTime:30,scope:{kind:'EXPERIMENT',experimentId:req.experiment_id},
  source:{side:effectSide,method:'arena_controller'},epistemicStatus:'OBSERVED',completeness:{complete:true},
  payload:{actionId:'action-1',idempotencyKey:'key-1',arenaId:'arena',beforeEpoch:0,afterEpoch:0,beforeRevision:1,afterRevision:1,
   elapsedServerTicks:5,postconditionMatched:true,classification:'INCONCLUSIVE',...effectOverride}};
 let effectBytes;
 if(effect){const got=await f.store.appendObservation(effectRow);effectBytes=Buffer.from(JSON.stringify(sparseProducer?{...got.record,completeness:{status:'COMPLETE',complete:true}}:got.record));
  await writeFile(path.join(f.runDir,'evidence/raw/action.jsonl'),Buffer.concat([effectBytes,Buffer.from(trailingPartial?'\n{"v":':'\n')]));}
 const arena={schemaVersion:1,arenaId:'arena',arenaEpoch:0,arenaRevision:1,baselineHash:req.arena.baseline_hash,bounds:req.arena.bounds,
  allowedMutationBounds:req.arena.bounds,resetClasses:{blocks:'RESETTABLE'}};
 let journalDir=null;
 if(journal!=='MISSING'){
  const started=await beginAction({runDir:f.runDir,arena,identity,action:{schemaVersion:1,...identity,arenaId:'arena',arenaEpoch:0,expectedArenaRevision:1,
   actionId:'action-1',idempotencyKey:'key-1',type:'wait_ticks',args:{ticks:5}}});journalDir=started.directory;
  const statuses=journal==='NOT_RUN'?['NOT_RUN']:journal==='REJECTED'?['FAILED']:journal==='VERIFIED'?['ACCEPTED','APPLIED','VERIFIED']:['ACCEPTED'];
  for(const status of statuses)await recordActionOutcome({runDir:f.runDir,identity,idempotencyKey:'key-1',outcome:{status,evidenceHashes:['APPLIED','VERIFIED'].includes(status)?[effect?sha256(effectBytes):'f'.repeat(64)]:[]}});
 }
 let visualPacketHash=null;
 if(visual){const c=await compileVisualPacket(f);await persistVisualPacket({store:f.store,compiled:c});visualPacketHash=c.packetArtifact.sha256;}
 if(privateRow)await f.store.appendObservation({...effectRow,observationId:'obs:private:1',writerId:'private',writerSeq:1,lane:'ENTITY_STATE',payload:{health:0,diagnosticPath:'file=/private/selected-row-secret'}});
 const final=await finalizeEvidenceRun({...identity,runDir:f.runDir,live:false,status:'STOPPED',runSnapshotHash:snapshot.snapshotHash},
  {cleanShutdown:!partial,shutdownMode:partial?'UNKNOWN':'SOURCE_FIXTURE'});
 return {...f,req,identity,snapshotBytes,snapshot,effectBytes,journalDir,final,visualPacketHash,
  actionKeys:[{actionId:'action-1',idempotencyKey:'key-1'}],observationIds:privateRow?['obs:capture:1','obs:private:1']:['obs:capture:1'],timelineObservationIds:[]};
}
