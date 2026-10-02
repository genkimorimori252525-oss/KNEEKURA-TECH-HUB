/** Read-only private LAB→TECH evidence transport. No execution, publication, or new evidence store. */
import { readRegisteredFile } from './materials.mjs';
import { readActionOutcome } from './action-journal.mjs';
import { decodeJson, sha256, stableJson, exactKeys, identifier, hashId, integer } from './json.mjs';
import { readFinalizedSources, retainedProducerRows, same, require, privatePath, evidencePrefix } from './result-export-source.mjs';
import { validatePacket } from '../evidence/visual-packet.mjs';
import { validateVisualManifest, readRawVisualImage } from '../evidence/visual-capture.mjs';
function ids(value,max,label){require(Array.isArray(value)&&value.length<=max,'EXPORT_'+label+'_LIMIT');value.forEach(identifier);require(new Set(value).size===value.length,'DUPLICATE_EXPORT_'+label);}
export async function exportFinalizedExperiment({runDir,requestBytes,assertionsBytes,actionKeys=[],observationIds=[],timelineObservationIds=[],visualPacketHash=null}) {
 ids(observationIds,32,'OBSERVATION');ids(timelineObservationIds,32,'TIMELINE');
 const s=await readFinalizedSources({runDir,requestBytes,assertionsBytes});
 const blobs=new Map(),evidence=new Map(),gaps=new Map();let totalBytes=0;
 const gap=(code,assertion_id=null)=>gaps.set(code+':'+assertion_id,{code,assertion_id});
 const add=(bytes,kind=null,classification='PRIVATE_RETAINED_EVIDENCE')=>{
  require(Buffer.isBuffer(bytes)&&bytes.length>0&&bytes.length<=16*1024*1024,'EXPORT_BLOB_SIZE_LIMIT');const hash=sha256(bytes);
  if(!blobs.has(hash)){totalBytes+=bytes.length;require(totalBytes<=64*1024*1024,'EXPORT_TOTAL_BYTE_LIMIT');blobs.set(hash,{contentHash:hash,bytes,classification});}
  if(kind){if(evidence.has(hash))require(evidence.get(hash).kind===kind,'EXPORT_EVIDENCE_KIND_COLLISION');else evidence.set(hash,{kind,content_hash:hash,size_bytes:bytes.length});require(evidence.size<=128,'EXPORT_EVIDENCE_COUNT_LIMIT');}
  return hash;
 };
 const derived=(value,kind)=>add(Buffer.from(stableJson(value)),kind,'DERIVED_EVIDENCE_PROJECTION');
 const snapshotHash=add(s.snapshotFile.bytes,null,'PRIVATE_RUN_SNAPSHOT');
 gap('UNKNOWN'); // Loaded target equivalence and Arena cleanup are not established by disk/class-resource evidence.
 const f=s.finalization;
 if(f.status!=='EVIDENCE_COMPLETE'||['dropped','errors','trailingPartialFiles','partialCaptures'].some(k=>(f.counts?.[k]??0)>0)||['PARTIAL','UNKNOWN'].includes(f.captures?.coverageStatus))gap('PARTIAL');
 const cleanupHash=derived({schemaVersion:1,kind:'lab_evidence_seal_projection',semantics:'EVIDENCE_SEAL_NOT_ARENA_CLEANUP',
  identity:s.identity,sourceFinalizationHash:s.finalFile.sha256,evidenceCut:s.evidenceCut,status:f.status,
  shutdown:{clean:f.shutdown?.clean===true,mode:['UNKNOWN','GRACEFUL','FORCED','SOURCE_FIXTURE'].includes(f.shutdown?.mode)?f.shutdown.mode:'OTHER_RETAINED_MODE'},
  counts:Object.fromEntries(['observations','findings','dropped','errors','trailingPartialFiles','partialCaptures'].map(k=>[k,Number.isSafeInteger(f.counts?.[k])?f.counts[k]:null])),
  cleanup:'UNKNOWN',runtimeAttestation:'NOT_ESTABLISHED'},'cleanup_receipt');
 const selection=(selected,kind)=>{
  if(!selected.length)return null;
  const refs=selected.map(id=>{
   const item=s.byId.get(id);if(!item){gap('MISSING');return {observationId:id,status:'MISSING'};}
   if(item.row.completeness?.complete!==true)gap('PARTIAL');if(item.row.epistemicStatus==='UNKNOWN')gap('UNKNOWN');
   if(privatePath(item.row)){gap('UNAVAILABLE');return {observationId:id,status:'PRIVATE_FIELDS_NOT_EXPORTED',sourceContentHash:item.contentHash};}
   const hash=add(item.bytes,'structured');return {observationId:id,status:'RETAINED',contentHash:hash,sourceCanonicalFileHash:s.canonicalFile.sha256,
    sourceByteOffset:item.offset,sourceByteLength:item.bytes.length};
  });
  return derived({schemaVersion:1,kind:kind==='structured'?'lab_structured_selection':'lab_timeline_selection',identity:s.identity,evidenceCut:s.evidenceCut,
   semantics:'EXACT_SELECTED_ROWS_NOT_CONTINUITY_OR_ACCEPTANCE',observations:refs},kind);
 };
 const structuredSummary=selection(observationIds,'structured');const timelineSummary=selection(timelineObservationIds,'timeline');
 const requested=[...s.request.initial_state,...s.request.actions];
 require(Array.isArray(actionKeys)&&actionKeys.length<=32,'ACTION_KEY_LIMIT');const keys=new Map();
 for(const entry of actionKeys){exactKeys(entry,['actionId','idempotencyKey'],'EXPORT_ACTION_KEY');identifier(entry.actionId);identifier(entry.idempotencyKey);
  require(requested.some(a=>a.action_id===entry.actionId)&&!keys.has(entry.actionId)&&![...keys.values()].includes(entry.idempotencyKey),'EXPORT_ACTION_KEY_MISMATCH');keys.set(entry.actionId,entry.idempotencyKey);}
 const journal=[];const wanted=new Set();
 for(const action of requested){
  const key=keys.get(action.action_id);if(!key){journal.push({action,status:'UNKNOWN',records:[],effectHashes:[]});gap('MISSING');continue;}
  const out=await readActionOutcome({runDir,identity:s.identity,idempotencyKey:key});
  if(!out.action){journal.push({action,key,status:'UNKNOWN',records:[],effectHashes:[]});gap(out.status==='NEVER_SEEN'?'MISSING':'UNKNOWN');continue;}
  const {action_id,operation,...args}=action;
  require(out.action.actionId===action_id&&out.action.idempotencyKey===key&&out.action.type===operation&&same(out.action.args,args)&&out.action.arenaId===s.request.arena.arena_id,'EXPORT_ACTION_SETUP_MISMATCH');
  const directory='control/actions/'+sha256(key);const records=[];const statuses=[];
  for(const name of ['canonical-action.json','request.json',...Array.from({length:5},(_,i)=>`receipt-${String(i).padStart(6,'0')}.json`)]){
   let file;try{file=await readRegisteredFile({root:runDir,relativePath:directory+'/'+name,maxBytes:128*1024});}catch(error){if(error.code==='ENOENT'&&name.startsWith('receipt-'))break;throw error;}
   if(name==='canonical-action.json')require(file.sha256===sha256(stableJson(out.action))&&same(decodeJson(file.bytes),out.action),'ACTION_CANONICAL_BYTES');
   if(name.startsWith('receipt-'))statuses.push(decodeJson(file.bytes).status);
   records.push({record:name.replace('.json',''),content_hash:file.sha256,encoding:'base64',bytes_base64:file.bytes.toString('base64')});
  }
  const reread=await readActionOutcome({runDir,identity:s.identity,idempotencyKey:key});require(same(out,reread),'ACTION_JOURNAL_CHANGED_DURING_EXPORT');
  for(const hash of out.evidenceHashes)wanted.add(hash);
  journal.push({action,key,status:out.status,recordedStatus:out.recordedStatus,records,statuses,effectHashes:out.evidenceHashes,envelope:out.action});
 }
 const producer=await retainedProducerRows(s,wanted);const receipts=[];
 for(const item of journal){
  let status='UNKNOWN';const effectRefs=[];
  for(const hash of item.effectHashes){
   const source=producer.get(hash);const p=source?.row.payload;
   const bound=source&&source.row.lane==='ACTION_APPLIED'&&source.row.source?.side==='SERVER'&&source.row.epistemicStatus==='OBSERVED'&&source.row.completeness.complete===true&&
    p?.actionId===item.action.action_id&&p.idempotencyKey===item.key&&p.arenaId===s.request.arena.arena_id&&p.postconditionMatched===true&&
    p.beforeEpoch===item.envelope.arenaEpoch&&p.beforeRevision===item.envelope.expectedArenaRevision&&
    p.afterEpoch===item.envelope.arenaEpoch&&source.row.arenaEpoch===p.afterEpoch&&
    p.afterRevision===item.envelope.expectedArenaRevision+(item.action.operation==='wait_ticks'?0:1)&&
    (item.action.operation!=='wait_ticks'||p.elapsedServerTicks===item.action.ticks);
   if(bound&&!privatePath(source.row)){effectRefs.push({contentHash:add(source.bytes,'structured'),observationId:source.row.observationId,sourceFileHash:source.sourceFileHash,
     sourceByteOffset:source.offset,sourceByteLength:source.bytes.length});}
   else gap('UNAVAILABLE');
  }
  if(item.status==='VERIFIED'&&item.effectHashes.length>0&&effectRefs.length===item.effectHashes.length)status='APPLIED';
  else if(item.status==='NOT_RUN')status='NOT_RUN';
  else if(item.status==='FAILED'&&same(item.statuses,['REQUESTED','FAILED']))status='REJECTED';
  if(status==='UNKNOWN')gap('UNKNOWN');
  const hash=item.records.length?derived({schemaVersion:1,kind:'lab_action_receipt_export',identity:s.identity,requestHash:s.requestHash,actionId:item.action.action_id,
   idempotencyKey:item.key,reportedStatus:status,journalStatus:item.recordedStatus,semantics:'EXACT_JOURNAL_BYTES_AND_SEALED_OBSERVATION_BACKING_NOT_RUNTIME_ATTESTATION',
   sourceRecords:item.records,effectEvidence:effectRefs},'action_receipt'):null;
  receipts.push({action_id:item.action.action_id,status,evidence_hash:hash});
 }
 let visualBundle=null;
 if(visualPacketHash!==null){
  hashId(visualPacketHash);const file=await s.retained(`evidence/derived/visual/${visualPacketHash}.json`,1024*1024);
  require(file.sha256===visualPacketHash,'EXPORT_VISUAL_SEALED_HASH');
  const packet=validatePacket(decodeJson(file.bytes));const b=packet.binding;
  for(const key of ['debugSessionId','runId','runSnapshotId','processEpoch','experimentId'])require(b[key]===s.identity[key],'EXPORT_VISUAL_IDENTITY');
  require(b.requestHash===s.requestHash&&b.generation===s.request.generation&&same(evidencePrefix(s.rows,b.evidenceCut.count),b.evidenceCut),'EXPORT_VISUAL_PREFIX');
  const capture=s.byId.get(b.sourceObservationId);require(capture&&s.rows.indexOf(capture)<b.evidenceCut.count&&sha256(stableJson(validateVisualManifest(capture.row.payload)))===b.canonicalManifestHash,'EXPORT_VISUAL_CANONICAL_SOURCE');
  const sourceIds=new Set(s.rows.slice(0,b.evidenceCut.count).map(i=>i.row.observationId));
  for(const id of packet.contactSheet.sourceObservationIds){
   const item=s.byId.get(id);require(item&&sourceIds.has(id),'EXPORT_VISUAL_SOURCE_MISSING');
   require(!privatePath(item.row),'EXPORT_PRIVATE_VISUAL_SOURCE');add(item.bytes,'structured');
  }
  for(const row of packet.timeline){
   const source=s.byId.get(row.observationId)?.row;require(source,'EXPORT_VISUAL_TIMELINE_SOURCE');
   const expected={observationId:source.observationId,lane:source.lane,writerId:source.writerId,writerSeq:source.writerSeq,gameTime:source.gameTime??null,
    epistemicStatus:source.epistemicStatus,completeness:source.completeness,scope:source.scope,source:source.source,observedAt:source.observedAt,resourceEpoch:source.resourceEpoch,
    contextRole:source.scope.kind==='ENTITY_UUID'?(b.subjects.includes(source.scope.entityUuid)?'CAPTURE_SUBJECT':'CONTEXT_ONLY_UNSELECTED_SUBJECT'):'EXPLICIT_RUN_CONTEXT',payload:source.payload};
   require(same(row,expected),'EXPORT_VISUAL_TIMELINE_LINEAGE');
  }
  for(const ref of [packet.contactSheet,packet.annotatedContactSheet,packet.topDown,packet.structuredSummaryArtifact,packet.timelineArtifact]){
   require(ref.sourceObservationIds.every(id=>sourceIds.has(id)),'EXPORT_VISUAL_SOURCE_MISSING');
   const sealed=await s.retained(ref.path,16*1024*1024);require(sealed.sha256===ref.sha256,'EXPORT_VISUAL_SEALED_HASH');
   const bytes=sealed.bytes;
   require(bytes.length===ref.bytes,'EXPORT_VISUAL_SIZE');add(bytes,'derived_visual');
  }
  for(const frame of packet.rawViews)add(await readRawVisualImage(runDir,((({manifestObservationId,producerFrameObservationHash,producerFrameObservationHashSemantics,...raw})=>raw)(frame))),'raw_scene');
  require(!privatePath(packet),'EXPORT_PRIVATE_VISUAL_FIELDS');visualBundle=add(file.bytes,'visual_bundle');
  if(packet.capture.perturbations.length)gap('PERTURBED');
 }else if(s.request.visual_rig.mode!=='none')gap('UNAVAILABLE');
 const all=(value)=>receipts.length>0&&receipts.every(r=>r.status===value);
 const executionStatus=all('APPLIED')?'COMPLETED':all('NOT_RUN')?'NOT_RUN':receipts.some(r=>r.status==='APPLIED')?'PARTIAL':
  receipts.length>0&&receipts.every(r=>['REJECTED','NOT_RUN'].includes(r.status))?'FAILED':'UNKNOWN';
 const result={schema_version:1,experiment_id:s.request.experiment_id,generation:s.request.generation,request_hash:s.requestHash,
  run_snapshot_id:s.snapshot.snapshotId,run_snapshot_content_hash:snapshotHash,
  execution:{status:executionStatus,action_receipts:receipts,cleanup:executionStatus==='NOT_RUN'?'NOT_RUN':'UNKNOWN'},
  observations:{structured_summary:structuredSummary,timeline_summary:timelineSummary,visual_bundle:visualBundle},
  assertions:s.request.assertions.map(a=>({assertion_id:a.assertion_id,status:executionStatus==='NOT_RUN'?'NOT_RUN':'INCONCLUSIVE',evidence_hashes:[]})),
  gaps:[...gaps.values()],evidence:[...evidence.values()]};
 require(result.gaps.length<=64,'EXPORT_GAP_LIMIT');const resultBytes=Buffer.from(stableJson(result));require(resultBytes.length<=1024*1024,'EXPORT_RESULT_SIZE_LIMIT');
 const resultHash=add(resultBytes,null,'PRIVATE_EXPERIMENT_RESULT');
 const manifest={schema_version:1,kind:'lab_experiment_export',request_hash:s.requestHash,result_hash:resultHash,run_snapshot_content_hash:snapshotHash,
  contains_private_evidence:true,provenance:'FINALIZED_LAB_EVIDENCE_REPORT',runtime_attestation:'NOT_ESTABLISHED',
  blobs:[...blobs.values()].map(b=>({content_hash:b.contentHash,size_bytes:b.bytes.length,classification:b.classification}))};
 require(Buffer.byteLength(stableJson(manifest))<=128*1024,'EXPORT_MANIFEST_LIMIT');
 // Final reread closes the source-selection window without modifying the finalized run.
 await readRegisteredFile({root:runDir,relativePath:'evidence/finalization.json',expectedSha256:s.finalFile.sha256,maxBytes:2*1024*1024});
 await s.retained('evidence/observations.jsonl',64*1024*1024);
 return {result,resultBytes,manifest,blobs:[...blobs.values()]};
}
