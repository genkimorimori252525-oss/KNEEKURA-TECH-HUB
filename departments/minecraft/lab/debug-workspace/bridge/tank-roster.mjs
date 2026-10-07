/** Finite discovery, never automatic selected-subject tracking. */
import path from 'node:path';
import {mkdir,lstat,realpath,open,link,unlink} from 'node:fs/promises';
import {randomUUID} from 'node:crypto';
import {exactKeys,integer,hashId,decodeJson,sha256,stableJson} from './json.mjs';
import {readRegisteredFile} from './materials.mjs';
import {readPreparedOwnerControl} from './owner-prelaunch.mjs';
import {readInstalledControl} from './owner-action-adapter.mjs';
import {EvidenceRuntime} from '../evidence/runtime.mjs';
import {validateVisualIdentity} from '../evidence/visual-capture.mjs';

const relative=index=>'control/tank-roster/'+String(index).padStart(2,'0');
async function read(runDir,file,limit=65536){return decodeJson((await readRegisteredFile({root:runDir,relativePath:file,maxBytes:limit})).bytes,limit);}
async function selected(options){
 const p=await readPreparedOwnerControl({...options,requireSnapshot:true});
 if(!p.tankObservation)throw new Error('TANK_ROSTER_SCOPE_REQUIRED');
 integer(options.sampleIndex,0,p.tankObservation.maxSamples-1);return p;
}
function markerMatches(m,p,envelopeHash,index){
 exactKeys(m,['schemaVersion','sampleIndex','ownerEnvelopeHash','runSnapshotId','runSnapshotHash','requestHash','handshakeNonce','leaseId','expectedArenaEpoch','expectedArenaRevision','tankObservationHash'],'TANK_ROSTER_MARKER');
 if(m.schemaVersion!==1||m.sampleIndex!==index||m.ownerEnvelopeHash!==envelopeHash||m.runSnapshotId!==p.envelope.runSnapshotId||
  m.runSnapshotHash!==p.snapshot.snapshotHash||m.requestHash!==p.envelope.requestHash||m.handshakeNonce!==p.envelope.handshakeNonce||m.leaseId!==p.grant.leaseId||
  m.tankObservationHash!==p.envelope.tankObservationHash||m.expectedArenaEpoch!==p.grant.arenaEpoch)throw new Error('TANK_ROSTER_MARKER_IDENTITY');
 integer(m.expectedArenaRevision,p.grant.expectedArenaRevision,Number.MAX_SAFE_INTEGER);
}
export async function publishTankRoster({runDir,envelopeHash,sampleIndex}){
 const p=await selected({runDir,envelopeHash,sampleIndex}),dir=relative(sampleIndex);
 try{const m=await read(runDir,dir+'/request.json',16384);markerMatches(m,p,envelopeHash,sampleIndex);return {status:'ALREADY_REQUESTED',sampleIndex,execution:'NOT_CONFIRMED'};}
 catch(error){if(error.code!=='ENOENT')throw error;}
 if(sampleIndex>0){const prior=await inspectTankRoster({runDir,envelopeHash,sampleIndex:sampleIndex-1});if(!['COMPLETE','PARTIAL','REJECTED'].includes(prior.status))throw new Error('TANK_ROSTER_PRIOR_RECONCILIATION_REQUIRED');}
 const {control}=await readInstalledControl({runDir,envelopeHash,minRemainingMs:100});
 const marker={schemaVersion:1,sampleIndex,ownerEnvelopeHash:envelopeHash,runSnapshotId:p.envelope.runSnapshotId,runSnapshotHash:p.snapshot.snapshotHash,
  requestHash:p.envelope.requestHash,handshakeNonce:p.envelope.handshakeNonce,leaseId:p.grant.leaseId,expectedArenaEpoch:control.arenaEpoch,expectedArenaRevision:control.arenaRevision,tankObservationHash:p.envelope.tankObservationHash};
 for(const dirName of ['control/tank-roster',dir]){
  const file=path.join(runDir,dirName);try{await mkdir(file);}catch(error){if(error.code!=='EEXIST')throw error;}
  if(await realpath(file)!==file||!(await lstat(file)).isDirectory())throw new Error('TANK_ROSTER_DIRECTORY_UNSAFE');
 }
 const current=await readInstalledControl({runDir,envelopeHash,minRemainingMs:100});
 if(current.control.arenaRevision!==control.arenaRevision||current.control.arenaEpoch!==control.arenaEpoch)throw new Error('TANK_ROSTER_OWNER_CHANGED');
 const bytes=Buffer.from(stableJson(marker)),temporary=path.join(runDir,dir,'.request-'+randomUUID()+'.tmp'),h=await open(temporary,'wx',0o600);
 try{await h.writeFile(bytes);await h.sync();}finally{await h.close();}
 try{await link(temporary,path.join(runDir,dir,'request.json'));}finally{await unlink(temporary);}
 return {status:'REQUESTED',sampleIndex,markerHash:sha256(bytes),execution:'NOT_CONFIRMED'};
}
function vector(v,length=3){if(!Array.isArray(v)||v.length!==length||v.some(n=>typeof n!=='number'||!Number.isFinite(n)||Math.abs(n)>30000000))throw new Error('TANK_ROSTER_VECTOR');}
export function validateTankRoster(payload,p,index){
 const s=p.tankObservation;
 integer(index,0,s.maxSamples-1);
 exactKeys(payload,['schemaVersion','kind','identity','ownerEnvelopeHash','tankObservationHash','sampleIndex','dimension','boundsSemantics','min','max','serverTick','gameTime','status','missingEntityNotAbsent','subsetSelection','coverage','limits','entities'],'TANK_ROSTER_PAYLOAD');
 if(payload.schemaVersion!==1||payload.kind!=='tank_room_roster'||payload.sampleIndex!==index||payload.ownerEnvelopeHash!==p.envelopeHash||
  payload.tankObservationHash!==p.envelope.tankObservationHash||payload.dimension!==s.dimensionId||payload.boundsSemantics!=='MIN_INCLUSIVE_MAX_EXCLUSIVE'||
  stableJson(payload.min)!==stableJson(s.min)||stableJson(payload.max)!==stableJson(s.max)||!['COMPLETE','PARTIAL'].includes(payload.status))throw new Error('TANK_ROSTER_IDENTITY');
 const g=p.grant,id=validateVisualIdentity(payload.identity);
 for(const k of ['debugSessionId','runId','runSnapshotId','processEpoch','experimentId','generation','requestHash','arenaId','arenaEpoch','baselineHash'])if(id?.[k]!==g[k])throw new Error('TANK_ROSTER_RUN_IDENTITY');
 integer(id.arenaRevision,g.expectedArenaRevision,Number.MAX_SAFE_INTEGER);integer(payload.serverTick,0,Number.MAX_SAFE_INTEGER);integer(payload.gameTime,0,Number.MAX_SAFE_INTEGER);
 exactKeys(payload.coverage,['allChunksLoaded','missingChunks','truncationReasons'],'TANK_ROSTER_COVERAGE');
 exactKeys(payload.limits,['maxEntities','maxSamples','maxPassengerDepth','maxPacketBytes'],'TANK_ROSTER_LIMITS');
 if(stableJson(payload.limits)!==stableJson({maxEntities:s.maxEntities,maxSamples:s.maxSamples,maxPassengerDepth:8,maxPacketBytes:65536})||
  typeof payload.coverage.allChunksLoaded!=='boolean'||!Array.isArray(payload.coverage.missingChunks)||payload.coverage.missingChunks.length>25||
  !Array.isArray(payload.coverage.truncationReasons)||payload.coverage.truncationReasons.some(r=>!['ENTITY_LIMIT','PASSENGER_DEPTH','BYTE_LIMIT'].includes(r))||
  payload.coverage.allChunksLoaded!==(payload.coverage.missingChunks.length===0))throw new Error('TANK_ROSTER_COVERAGE');
 const chunks=new Set();for(const c of payload.coverage.missingChunks){
  if(!Array.isArray(c)||c.length!==2)throw new Error('TANK_ROSTER_CHUNK');
  integer(c[0],Math.floor(s.min[0]/16),Math.floor((s.max[0]-1)/16));integer(c[1],Math.floor(s.min[2]/16),Math.floor((s.max[2]-1)/16));
  const key=stableJson(c);if(chunks.has(key))throw new Error('TANK_ROSTER_DUPLICATE_CHUNK');chunks.add(key);
 }
 if(new Set(payload.coverage.truncationReasons).size!==payload.coverage.truncationReasons.length)throw new Error('TANK_ROSTER_DUPLICATE_TRUNCATION');
 const complete=payload.coverage.allChunksLoaded&&payload.coverage.truncationReasons.length===0;
 if((payload.status==='COMPLETE')!==complete||payload.missingEntityNotAbsent!==!complete||payload.subsetSelection!==(complete?'COMPLETE_SCOPE_UUID_SORTED':'NATIVE_ENUMERATION_SUBSET_UUID_SORTED'))throw new Error('TANK_ROSTER_COMPLETENESS');
 if(!Array.isArray(payload.entities)||payload.entities.length>s.maxEntities||Buffer.byteLength(stableJson(payload))>61440)throw new Error('TANK_ROSTER_SIZE');
 let previous='';
 for(const e of payload.entities){
  exactKeys(e,['uuid','entityType','world','local','aabbMin','aabbMax','living','mob','player','knownSubjectId','vehicleUuid','passengerUuids','fullyContained'],'TANK_ROSTER_ENTITY');
  if(typeof e.uuid!=='string'||e.uuid.length!==36||!e.uuid.match(/^[a-f0-9]{8}-(?:[a-f0-9]{4}-){3}[a-f0-9]{12}$/)||e.uuid<=previous||typeof e.entityType!=='string'||e.entityType.includes('\n')||!e.entityType.match(/^[a-z0-9_.-]+:[a-z0-9_/.-]+$/))throw new Error('TANK_ROSTER_ENTITY_IDENTITY');previous=e.uuid;
  for(const k of ['world','local','aabbMin','aabbMax'])vector(e[k]);
  if(e.local.some((n,i)=>Math.abs(n-(e.world[i]-s.min[i]))>1e-8)||e.aabbMin.some((n,i)=>n>=e.aabbMax[i]||n>=s.max[i]||e.aabbMax[i]<=s.min[i])||
   e.fullyContained!==e.aabbMin.every((n,i)=>n>=s.min[i]&&e.aabbMax[i]<=s.max[i]))throw new Error('TANK_ROSTER_ENTITY_GEOMETRY');
  for(const k of ['living','mob','player','fullyContained'])if(typeof e[k]!=='boolean')throw new Error('TANK_ROSTER_ENTITY_FLAGS');
  const subject=p.request.subjects.find(s=>s.uuid===e.uuid&&s.entity_type===e.entityType);
  if(e.knownSubjectId!==(subject?.subject_id??null)||!Array.isArray(e.passengerUuids)||e.passengerUuids.length>65||e.passengerUuids.some(u=>typeof u!=='string'||!u.match(/^[a-f0-9]{8}-(?:[a-f0-9]{4}-){3}[a-f0-9]{12}$/))||e.vehicleUuid!==null&&(typeof e.vehicleUuid!=='string'||!e.vehicleUuid.match(/^[a-f0-9]{8}-(?:[a-f0-9]{4}-){3}[a-f0-9]{12}$/)))throw new Error('TANK_ROSTER_RELATIONS');
 }
 return structuredClone(payload);
}
export async function inspectTankRoster({runDir,envelopeHash,sampleIndex,observations=null}){
 const p={...await selected({runDir,envelopeHash,sampleIndex}),envelopeHash},dir=relative(sampleIndex);
 const unknown={status:'UNKNOWN',sampleIndex,execution:'NOT_CONFIRMED',roster:null,evidenceHash:null};
 let marker,receipt;
 try{marker=await read(runDir,dir+'/request.json',16384);markerMatches(marker,p,envelopeHash,sampleIndex);receipt=await read(runDir,dir+'/receipt.json');}
 catch(error){if(error.code==='ENOENT')return unknown;throw error;}
 if(receipt.schemaVersion!==1||receipt.kind!=='tank_roster_receipt'||receipt.ownerEnvelopeHash!==envelopeHash||receipt.runSnapshotHash!==p.snapshot.snapshotHash||
  receipt.requestHash!==p.envelope.requestHash||receipt.sampleIndex!==sampleIndex||receipt.markerHash!==sha256(stableJson(marker))||!['COMPLETE','PARTIAL','REJECTED','OUTCOME_UNKNOWN'].includes(receipt.status))throw new Error('TANK_ROSTER_RECEIPT_IDENTITY');
 if(!['COMPLETE','PARTIAL'].includes(receipt.status))return {...unknown,status:receipt.status};
 const payload=validateTankRoster(receipt.roster,p,sampleIndex);hashId(receipt.observationLineHash);
 if(payload.status!==receipt.status)throw new Error('TANK_ROSTER_PAYLOAD_STATUS');
 const reservation=await read(runDir,dir+'/native-reservation.json',16384);
 for(const k of ['schemaVersion','kind','sampleIndex','ownerEnvelopeHash','runSnapshotHash','requestHash','observedAt','markerHash'])if(reservation[k]!==receipt[k])throw new Error('TANK_ROSTER_RESERVATION_MISMATCH');
 if(observations===null){const runtime=new EvidenceRuntime({runDir,...p.identity});await runtime.init();if(!runtime.finalized)await runtime.ingestAvailable();observations=await runtime.store.readObservations();}
 const canonical=observations.filter(r=>r.lane==='TANK_ROOM_ROSTER'&&r.payload?.sampleIndex===sampleIndex&&r.payload?.ownerEnvelopeHash===envelopeHash);
 if(canonical.length!==1||stableJson(canonical[0].payload)!==stableJson(payload))return unknown;
 const raw=(await readRegisteredFile({root:runDir,relativePath:'evidence/raw/forge-runtime-'+p.snapshot.runtime.pid+'.jsonl',maxBytes:16*1024*1024})).bytes.toString('utf8');
 const matches=raw.split('\n').filter(line=>sha256(line)===receipt.observationLineHash);
 const rawRow=matches.length===1?JSON.parse(matches[0]):null;
 const {completeness:rawCompleteness,...rawBody}=rawRow??{}, {completeness:canonicalCompleteness,...canonicalBody}=canonical[0];
 if(matches.length!==1||rawCompleteness?.status!==canonicalCompleteness?.status||stableJson(rawBody)!==stableJson(canonicalBody))throw new Error('TANK_ROSTER_RAW_PROOF_MISMATCH');
 return {status:receipt.status,sampleIndex,execution:'CANONICAL_STRUCTURED_EVIDENCE',roster:payload,evidenceHash:receipt.observationLineHash};
}

export async function sealTankRosterArtifacts(runDir,observations,artifacts){
 let envelope;try{envelope=await read(runDir,'control/owner-envelope.json',16384);}catch(error){if(error.code==='ENOENT')return;throw error;}
 if(!envelope.tankObservationHash)return;
 const envelopeHash=sha256(stableJson(envelope)),p=await readPreparedOwnerControl({runDir,envelopeHash,requireSnapshot:true});
 async function retain(relativePath,limit){const file=await readRegisteredFile({root:runDir,relativePath,maxBytes:limit});
  const row={path:path.join(runDir,relativePath),size:file.bytes.length,sha256:'sha256:'+file.sha256},old=artifacts.find(a=>a.path===row.path);
  if(old&&stableJson(old)!==stableJson(row))throw new Error('TANK_ROSTER_SEAL_CONFLICT');if(!old)artifacts.push(row);
 }
 await retain('control/owner-tank-observation.json',16384);
 for(let i=0;i<p.tankObservation.maxSamples;i++)for(const name of ['request.json','native-reservation.json','receipt.json']){
  try{await retain(relative(i)+'/'+name,name==='receipt.json'?65536:16384);}catch(error){if(error.code!=='ENOENT')throw error;continue;}
  if(name==='receipt.json'){const result=await inspectTankRoster({runDir,envelopeHash,sampleIndex:i,observations});
   if(['COMPLETE','PARTIAL'].includes((await read(runDir,relative(i)+'/receipt.json')).status)&&result.status==='UNKNOWN')throw new Error('TANK_ROSTER_CANONICAL_SOURCE_MISSING');}
 }
}

/** Pure projection of a verified retained sample, never a new world read. */
export function spatialMapFromRoster(result){
 const r=result?.roster;
 if(!r||!['COMPLETE','PARTIAL'].includes(result.status)||r.status!==result.status||
  result.execution!=='CANONICAL_STRUCTURED_EVIDENCE'||!result.evidenceHash)
  throw new Error('SPATIAL_MAP_VERIFIED_ROSTER_REQUIRED');
 hashId(result.evidenceHash);
 const escape=value=>String(value).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
 const coord=value=>value.join(', ');
 function view(vertical,label){
  const left=44,top=32,width=440,height=280;
  const x=n=>left+(n-r.min[0])/(r.max[0]-r.min[0])*width;
  const y=n=>vertical===1?top+height-(n-r.min[1])/(r.max[1]-r.min[1])*height:top+(n-r.min[2])/(r.max[2]-r.min[2])*height;
  const rect=(lo,hi,attributes)=>`<rect x="${x(lo[0])}" y="${Math.min(y(lo[vertical]),y(hi[vertical]))}" width="${x(hi[0])-x(lo[0])}" height="${Math.abs(y(hi[vertical])-y(lo[vertical]))}" ${attributes}/>`;
  const gaps=r.coverage.missingChunks.map(([cx,cz])=>{
   const lo=[Math.max(r.min[0],cx*16),r.min[1],Math.max(r.min[2],cz*16)],hi=[Math.min(r.max[0],cx*16+16),r.max[1],Math.min(r.max[2],cz*16+16)];
   return rect(lo,hi,`class="gap" data-gap="${cx},${cz}"`);
  }).join('');
  const bodies=r.entities.map((e,i)=>rect(e.aabbMin,e.aabbMax,`class="body ${e.knownSubjectId===null?'resident':'selected'}" data-aabb="${escape(coord(e.aabbMin)+' / '+coord(e.aabbMax))}"`)+
   `<circle cx="${x(e.world[0])}" cy="${y(e.world[vertical])}" r="3"/><text x="${x(e.world[0])+5}" y="${y(e.world[vertical])-5}">${i+1}</text>`).join('');
  return `<figure><figcaption>${label} world projection</figcaption><svg viewBox="0 0 540 355" role="img" aria-label="${label} retained positions"><defs><clipPath id="scope-${vertical}"><rect x="${left}" y="${top}" width="${width}" height="${height}"/></clipPath></defs><rect class="scope" x="${left}" y="${top}" width="${width}" height="${height}"/><g clip-path="url(#scope-${vertical})">${gaps}${bodies}</g><text x="${left}" y="340">X ${r.min[0]} to ${r.max[0]}; ${vertical===1?'Y':'Z'} ${r.min[vertical]} to ${r.max[vertical]}</text></svg></figure>`;
 }
 const rows=r.entities.map((e,i)=>`<tr><td>${i+1}</td><td>${escape(e.uuid)}<br>${escape(e.entityType)}<br>${escape(e.knownSubjectId??'Unregistered resident')}</td><td>${coord(e.world)}</td><td>${coord(e.local)}</td><td>${coord(e.aabbMin)}<br>${coord(e.aabbMax)}</td><td>${e.fullyContained}</td></tr>`).join('');
 const html=`<!doctype html><meta charset="utf-8"><title>Retained Tank spatial map</title><style>body{font:15px system-ui;background:#18212a;color:#eee;margin:24px}main{display:flex;flex-wrap:wrap}figure{margin:8px;width:540px}svg{width:100%}text{fill:#eee;font-size:13px}.scope{fill:#202f3c;stroke:#a9bdcf}.gap{fill:#ce5148;opacity:.3}.body{fill:#efc469;fill-opacity:.35;stroke:#efc469}.selected{stroke:#60dfb2;fill:#60dfb2}circle{fill:white}table{border-collapse:collapse}td,th{border:1px solid #617588;padding:8px;text-align:left;vertical-align:top}</style><h1>Retained Tank spatial map</h1><p>DERIVED_ARTIFACT — ${result.status}; sample ${result.sampleIndex}; server tick ${r.serverTick}; game time ${r.gameTime}. Current positions and sample age: UNKNOWN. No new sampling, registration or history.</p><p>Source raw observation SHA256: ${result.evidenceHash}. Interior [${coord(r.min)}] to [${coord(r.max)}) is half-open. Bodies are clipped to this projection; exact full AABBs remain below.</p><p>${r.missingEntityNotAbsent?'Missing residents are not absent.':'COMPLETE applies only to the retained scope/tick.'} Red bands: missing chunks (X/Y is a conservative projection across Z). Truncation: ${escape(r.coverage.truncationReasons.join(', ')||'none')}. Elevation projection can overlap different Z positions; it is not visibility or LOS.</p><main>${view(2,'X/Z')}${view(1,'X/Y')}</main><table><thead><tr><th>#</th><th>Identity</th><th>World xyz</th><th>Local xyz (world−min)</th><th>AABB min / max</th><th>Fully contained</th></tr></thead><tbody>${rows}</tbody></table>`;
 return {artifactRole:'DERIVED_ARTIFACT',currentPositions:'UNKNOWN',sourceTick:r.serverTick,sourceEvidenceHash:result.evidenceHash,html};
}

/** Explicit new derived HTML outside the retained run, analogous to contact sheets. */
export async function writeTankRosterSpatialMap({runDir,envelopeHash,sampleIndex,outputFile}){
 if(typeof outputFile!=='string'||!path.isAbsolute(outputFile)||path.resolve(outputFile)!==outputFile)
  throw new Error('SPATIAL_MAP_OUTSIDE_RUN_REQUIRED');
 const relative=path.relative(runDir,outputFile);
 if(!(relative.startsWith('..'+path.sep)||path.isAbsolute(relative))||await realpath(path.dirname(outputFile))!==path.dirname(outputFile))
  throw new Error('SPATIAL_MAP_OUTSIDE_RUN_REQUIRED');
 let finalization;
 try{finalization=await read(runDir,'evidence/finalization.json',4*1024*1024);}
 catch(error){if(error.code==='ENOENT')throw new Error('SPATIAL_MAP_FINALIZED_RUN_REQUIRED');throw error;}
 if(finalization.kind!=='evidence_finalization'||!['EVIDENCE_COMPLETE','EVIDENCE_PARTIAL'].includes(finalization.status))
  throw new Error('SPATIAL_MAP_FINALIZED_RUN_REQUIRED');
 // Supply retained canonical rows explicitly: no EvidenceRuntime.init/ingest, even on a partial seal.
 const canonical=(await readRegisteredFile({root:runDir,relativePath:'evidence/observations.jsonl',maxBytes:16*1024*1024})).bytes.toString('utf8');
 const observations=canonical.split('\n').filter(line=>line.trim()).map(line=>JSON.parse(line));
 const result=await inspectTankRoster({runDir,envelopeHash,sampleIndex,observations});
 if(result.roster)for(const k of ['debugSessionId','runId','runSnapshotId','processEpoch'])
  if(finalization[k]!==result.roster.identity[k])throw new Error('SPATIAL_MAP_FINALIZATION_IDENTITY');
 const derived=spatialMapFromRoster(result);
 const h=await open(outputFile,'wx',0o600);try{await h.writeFile(derived.html);await h.sync();}finally{await h.close();}
 const {html,...metadata}=derived;return {...metadata,outputFile,sampleIndex};
}
