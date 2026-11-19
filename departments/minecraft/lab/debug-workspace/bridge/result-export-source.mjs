import path from 'node:path';
import { EvidenceStore } from '../evidence/store.mjs';
import { assertValidObservation, normalizeCompleteness } from '../evidence/schema.mjs';
import { validateVisualExperimentRequest } from '../evidence/visual-request-contract.mjs';
import { validateTechHubBinding } from './registration.mjs';
import { readRegisteredFile } from './materials.mjs';
import { decodeJson, sha256, stableJson, hashId, integer, canonicalRunSnapshotBytes } from './json.mjs';
export const same = (a,b) => stableJson(a) === stableJson(b);
export function require(value,code) { if (!value) throw new TypeError(code); }
export function privatePath(value) {
 if(typeof value==='string')return /(?:^|[^A-Za-z0-9._~-])\/[A-Za-z0-9._-]|[A-Za-z]:[\\/]|\\\\|file:\/\//.test(value);
 if(Array.isArray(value))return value.some(privatePath);
 return value&&typeof value==='object'?Object.values(value).some(privatePath):false;
}
export function rowsFromBytes(bytes,{allowTrailingPartial=false}={}) {
 const rows=[];let start=0;
 for(let i=0;i<=bytes.length;i++)if(i===bytes.length||bytes[i]===10){
  let end=i;if(end>start&&bytes[end-1]===13)end--;
  const raw=bytes.subarray(start,end);
  if(raw.length){
   require(rows.length<65536,'SOURCE_ROW_LIMIT');let row;
   try{row=decodeJson(raw,1024*1024);}catch(error){
    let partial=false;
    if(allowTrailingPartial&&i===bytes.length){
     try{JSON.parse(new TextDecoder('utf-8',{fatal:true}).decode(raw));}catch(syntax){partial=syntax instanceof SyntaxError;}
    }
    if(partial)break;throw error;
   }
   assertValidObservation(row);rows.push({row,bytes:Buffer.from(raw),offset:start,contentHash:sha256(raw)});
  }
  start=i+1;
 }
 return rows;
}
export function evidencePrefix(rows,count=rows.length) {
 integer(count,0,rows.length);const selected=rows.slice(0,count).map(x=>x.row);
 return {count,lastObservationId:selected.at(-1)?.observationId??null,
  observationIdsSha256:'sha256:'+sha256(selected.length?selected.map(r=>r.observationId).join('\n')+'\n':''),
  canonicalRecordsSha256:'sha256:'+sha256(selected.length?selected.map(stableJson).join('\n')+'\n':'')};
}
export function bindRow(row,identity,experimentId) {
 for(const key of ['debugSessionId','runId','runSnapshotId','processEpoch'])require(row[key]===identity[key],'EXPORT_OBSERVATION_IDENTITY');
 if(row.scope.kind==='EXPERIMENT')require(row.scope.experimentId===experimentId,'EXPORT_OBSERVATION_EXPERIMENT');
}
export async function readFinalizedSources({runDir,requestBytes,assertionsBytes}) {
 require(Buffer.isBuffer(requestBytes)&&requestBytes.length<=128*1024,'REQUEST_BYTES_REQUIRED');
 require(Buffer.isBuffer(assertionsBytes)&&assertionsBytes.length<=256*1024,'ASSERTION_BYTES_REQUIRED');
 const request=validateVisualExperimentRequest(decodeJson(requestBytes,128*1024));
 const finalFile=await readRegisteredFile({root:runDir,relativePath:'evidence/finalization.json',maxBytes:2*1024*1024});
 const finalization=decodeJson(finalFile.bytes,2*1024*1024);
 require(finalization.schemaVersion===1&&finalization.kind==='evidence_finalization'&&['EVIDENCE_COMPLETE','EVIDENCE_PARTIAL'].includes(finalization.status),'FINALIZED_EVIDENCE_REQUIRED');
 require(Array.isArray(finalization.artifacts)&&finalization.artifacts.length<=1024,'FINALIZATION_INVENTORY_LIMIT');
 const inventory=new Map();
 for(const a of finalization.artifacts){
  require(a&&typeof a.path==='string'&&path.isAbsolute(a.path),'FINALIZATION_ARTIFACT_PATH');
  const relative=path.relative(runDir,a.path).split(path.sep).join('/');
  require(relative&&!relative.split('/').some(p=>!p||p==='.'||p==='..')&&!path.isAbsolute(relative),'FINALIZATION_ARTIFACT_OUTSIDE_RUN');
  require(!inventory.has(relative),'DUPLICATE_FINALIZATION_ARTIFACT');
  require(typeof a.sha256==='string'&&a.sha256.startsWith('sha256:'),'FINALIZATION_ARTIFACT_HASH');hashId(a.sha256.slice(7));
  integer(a.size,0,Number.MAX_SAFE_INTEGER);inventory.set(relative,a);
 }
 async function retained(relativePath,maxBytes){
  const entry=inventory.get(relativePath);require(entry,'FINALIZED_ARTIFACT_MISSING');
  const file=await readRegisteredFile({root:runDir,relativePath,expectedSha256:entry.sha256.slice(7),maxBytes});
  require(file.sizeBytes===entry.size,'FINALIZED_ARTIFACT_SIZE');return file;
 }
 const snapshotFile=await retained('run-snapshot.json',2*1024*1024);const snapshot=decodeJson(snapshotFile.bytes,2*1024*1024);
 const snapshotFields=['schemaVersion','snapshotId','createdAt','debugProfile','workspaceId','debugSessionId','runId','processEpoch','worldName','source','observer','build','runtime','snapshotHash','techHub',...(Object.hasOwn(snapshot,'bridge')?['bridge']:[])];
 require(same(Object.keys(snapshot).sort(),snapshotFields.sort()),'SNAPSHOT_SCHEMA');
 for(const field of ['snapshotId','debugSessionId','runId','debugProfile','workspaceId'])require(typeof snapshot[field]==='string'&&/^[A-Za-z0-9][A-Za-z0-9._:-]{0,159}(?![\s\S])/.test(snapshot[field]),'SNAPSHOT_IDENTITY');
 integer(snapshot.processEpoch,0,Number.MAX_SAFE_INTEGER);
 for(const field of ['createdAt','worldName'])require(typeof snapshot[field]==='string'&&snapshot[field].length>=1&&snapshot[field].length<=256,'SNAPSHOT_METADATA');
 for(const field of ['source','observer','build','runtime'])require(snapshot[field]&&typeof snapshot[field]==='object'&&!Array.isArray(snapshot[field]),'SNAPSHOT_METADATA');
 const binding=validateTechHubBinding(snapshot.techHub);
 require(binding.request_hash===sha256(requestBytes)&&binding.experiment_id===request.experiment_id&&binding.generation===request.generation&&
  same(binding.target,request.target)&&binding.arena_id===request.arena.arena_id&&binding.arena_baseline_hash===request.arena.baseline_hash,'SNAPSHOT_REQUEST_BINDING');
 require(binding.assertions_hash===sha256(assertionsBytes)&&same(decodeJson(assertionsBytes,256*1024),request.assertions),'SNAPSHOT_ASSERTION_BINDING');
 const {snapshotHash,...snapshotBody}=snapshot;
 require(snapshot.schemaVersion===1&&snapshotHash==='sha256:'+sha256(canonicalRunSnapshotBytes(snapshotBody)),'SNAPSHOT_LOGICAL_HASH');
 const identity={debugSessionId:snapshot.debugSessionId,runId:snapshot.runId,runSnapshotId:snapshot.snapshotId,processEpoch:snapshot.processEpoch,experimentId:request.experiment_id};
 for(const key of ['debugSessionId','runId','runSnapshotId','processEpoch'])require(finalization[key]===identity[key],'FINALIZATION_IDENTITY');
 require(finalization.runSnapshotHash===snapshotHash,'FINALIZATION_SNAPSHOT_BINDING');
 const canonicalFile=await retained('evidence/observations.jsonl',64*1024*1024);const rows=rowsFromBytes(canonicalFile.bytes);
 require(finalization.counts?.observations===rows.length,'FINALIZATION_OBSERVATION_COUNT');
 const byId=new Map();for(const item of rows){bindRow(item.row,identity,request.experiment_id);require(!byId.has(item.row.observationId),'DUPLICATE_CANONICAL_OBSERVATION');byId.set(item.row.observationId,item);}
 const store=new EvidenceStore({runDir,...identity});await store.init();
 require(same(store.canonicalPrefixProof(),evidencePrefix(rows)),'FINALIZED_CANONICAL_PREFIX');
 // Snapshot/observation bytes remain exact private local inputs, never raw logs.
 return {runDir,request,requestHash:binding.request_hash,binding,identity,snapshot,snapshotFile,canonicalFile,rows,byId,store,
  finalization,finalFile,inventory,retained,evidenceCut:evidencePrefix(rows)};
}
export async function retainedProducerRows(source,wantedHashes) {
 const found=new Map();if(wantedHashes.size===0)return found;let total=0;
 for(const [relative,entry] of source.inventory){
  if(!/^evidence\/raw\/[^/]+\.jsonl$/.test(relative))continue;
  total+=entry.size;require(total<=64*1024*1024,'PRODUCER_SCAN_BYTE_LIMIT');
  let file;try{file=await source.retained(relative,64*1024*1024);}catch(error){if(error.code==='ENOENT')continue;throw error;}
  for(const item of rowsFromBytes(file.bytes,{allowTrailingPartial:source.finalization.status==='EVIDENCE_PARTIAL'&&source.finalization.counts.trailingPartialFiles>0}))if(wantedHashes.has(item.contentHash)){
   bindRow(item.row,source.identity,source.request.experiment_id);
   const canonical=source.byId.get(item.row.observationId);
   require(canonical&&same(canonical.row,{...item.row,completeness:normalizeCompleteness(item.row.completeness)}),'PRODUCER_CANONICAL_LINEAGE');
   found.set(item.contentHash,{...item,sourceFileHash:file.sha256});
  }
 }
 return found;
}
