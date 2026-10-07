/** Reconcile the original slot and reference existing evidence. Never request a capture. */
import {open,realpath} from 'node:fs/promises';
import {integer,hashId,decodeJson,sha256,stableJson} from './json.mjs';
import {readRegisteredFile} from './materials.mjs';
import {readPreparedOwnerControl} from './owner-prelaunch.mjs';
import {captureSlotKey} from './owner-action-adapter.mjs';
import {EvidenceRuntime} from '../evidence/runtime.mjs';
import {validateVisualManifest,readRawVisualImage,CARDINAL_VIEWS} from '../evidence/visual-capture.mjs';

export async function bundleFromManifest({runDir,manifest}){
 const m=validateVisualManifest(manifest),views=[];let missing=false,invalid=false;
 for(const view of CARDINAL_VIEWS){
  const frame=m.frames.find(f=>f.view===view);let verification='MISSING',image=null;
  if(frame)try{await readRawVisualImage(runDir,frame);verification='VERIFIED_RAW_PNG';image={path:frame.imagePath,sha256:frame.imageHash,bytes:frame.imageBytes};}
  catch(e){if(e.code==='ENOENT'){verification='MISSING';missing=true;}else{verification='UNKNOWN_INTEGRITY';invalid=true;}}
  else missing=true;
  views.push({view,verification,image,camera:frame?.camera??null,serverTick:frame?.serverTick??null,serverGameTime:frame?.serverGameTime??null});
 }
 const status=invalid||m.result.status==='UNKNOWN'?'UNKNOWN':missing||m.result.status==='PARTIAL'?'PARTIAL':'COMPLETE';
 return {schemaVersion:1,artifactRole:'REFERENCES_TO_RAW_AND_STRUCTURED_EVIDENCE',status,recordedStatus:m.result.status,rig:m.rig,
  captureId:m.captureId,identity:m.identity,sourceBinding:'CALLER_MUST_VERIFY_CANONICAL_OWNER_SOURCE',tankObservationHash:m.tankObservationHash??null,
  views,structuredState:m.structuredState,controlledStateHash:m.controlledStateHash,controlledStateHashSemantics:'PRODUCER_BYTES_NOT_REENCODED',
  restoration:m.result.restoration,restorationProof:m.restorationProof,sameFrame:false,rosterTimePairing:'SEPARATE_ROSTER_NOT_SYNCHRONIZED',
  visualVerdict:'NOT_ESTABLISHED',execution:'RETAINED_REFERENCES_ONLY'};
}
// Native receipts hash Java's exact canonical numeric bytes, not a Node re-encoding.
function memberBytes(bytes,key){
 const s=bytes.toString('utf8'),needle='"'+key+'":',at=s.indexOf(needle);if(at<0||s.indexOf(needle,at+needle.length)>=0)throw new Error('CAPTURE_RECEIPT_MEMBER_AMBIGUOUS');
 const start=at+needle.length;let depth=0,string=false,escape=false;
 for(let i=start;i<s.length;i++){
  const c=s[i];if(string){if(escape)escape=false;else if(c==='\\')escape=true;else if(c==='"')string=false;continue;}
  if(c==='"')string=true;else if(c==='{'||c==='[')depth++;else if(c==='}'||c===']'){if(--depth===0)return Buffer.from(s.slice(start,i+1));}
 }throw new Error('CAPTURE_RECEIPT_MEMBER_INCOMPLETE');
}
export async function captureBundle({runDir,envelopeHash,captureIndex}){
 const p=await readPreparedOwnerControl({runDir,envelopeHash,requireSnapshot:true});
 integer(captureIndex,0,Math.floor(p.grant.maxCaptures/4)-1);
 if(!['cardinal-4-snapshot-v1','tank-cardinal-4-snapshot-v2'].includes(p.request.visual_rig.mode))throw new Error('CAPTURE_BUNDLE_RIG');
 const key=captureSlotKey(p.grant,captureIndex),dir='control/captures/'+key,unknown={schemaVersion:1,status:'UNKNOWN',captureIndex,captureId:'capture-'+key,bundle:null,execution:'NOT_CONFIRMED'};
 let marker,receipt,receiptBytes;
 try{
  marker=decodeJson((await readRegisteredFile({root:runDir,relativePath:dir+'/request.json',maxBytes:16384})).bytes,16384);
  receiptBytes=(await readRegisteredFile({root:runDir,relativePath:dir+'/receipt.json',maxBytes:128*1024})).bytes;receipt=decodeJson(receiptBytes,128*1024);
 }catch(e){if(e.code==='ENOENT')return unknown;throw e;}
 for(const k of ['ownerEnvelopeHash','requestHash','runSnapshotHash']){
  const expected=k==='ownerEnvelopeHash'?envelopeHash:k==='requestHash'?p.envelope.requestHash:p.snapshot.snapshotHash;
  if(marker[k]!==expected||receipt[k]!==expected)throw new Error('CAPTURE_BUNDLE_OWNER_IDENTITY');
 }
 if(marker.schemaVersion!==1||receipt.schemaVersion!==1||receipt.kind!=='owner_capture_receipt'||marker.captureKey!==key||receipt.captureKey!==key||
  marker.captureIndex!==captureIndex||receipt.captureIndex!==captureIndex||marker.captureId!==unknown.captureId||receipt.captureId!==unknown.captureId||marker.handshakeNonce!==p.envelope.handshakeNonce||marker.leaseId!==p.grant.leaseId)throw new Error('CAPTURE_BUNDLE_SLOT_IDENTITY');
 if(receipt.status==='OUTCOME_UNKNOWN'||receipt.status==='EXPIRED_NOT_DISPATCHED')return unknown;
 if(!['COMPLETE','PARTIAL','UNKNOWN'].includes(receipt.status))throw new Error('CAPTURE_BUNDLE_RECEIPT_STATUS');
 hashId(receipt.manifestPayloadHash);const manifest=validateVisualManifest(receipt.manifest);
 if(sha256(memberBytes(receiptBytes,'manifest'))!==receipt.manifestPayloadHash||manifest.result.status!==receipt.status||manifest.captureId!==unknown.captureId||manifest.rig!==p.request.visual_rig.mode||
  manifest.tankObservationHash!==(manifest.rig==='tank-cardinal-4-snapshot-v2'?p.envelope.tankObservationHash:undefined))throw new Error('CAPTURE_BUNDLE_MANIFEST_BINDING');
 for(const k of ['debugSessionId','runId','runSnapshotId','processEpoch','experimentId','generation','requestHash','arenaId','arenaEpoch','baselineHash'])if(manifest.identity[k]!==p.grant[k])throw new Error('CAPTURE_BUNDLE_RUN_IDENTITY');
 if(manifest.identity.arenaRevision!==marker.expectedArenaRevision||manifest.identity.arenaEpoch!==marker.expectedArenaEpoch||
  stableJson([...manifest.subjects].sort())!==stableJson(p.grant.subjects.map(s=>s.uuid).sort())||manifest.frames.some(f=>Math.abs(f.camera.fov-p.request.visual_rig.fov)>.001||stableJson(f.camera.viewport)!==stableJson(p.request.visual_rig.viewport)))throw new Error('CAPTURE_BUNDLE_REQUEST_BINDING');
 const reserved=decodeJson((await readRegisteredFile({root:runDir,relativePath:dir+'/native-reservation.json',maxBytes:16384})).bytes,16384);
 for(const k of ['debugSessionId','runId','runSnapshotId','processEpoch','ownerEnvelopeHash','requestHash','runSnapshotHash','leaseId','arenaId','arenaEpoch','arenaRevision'])if(reserved[k]!==receipt[k])throw new Error('CAPTURE_BUNDLE_RESERVATION_BINDING');
 if(manifest.structuredState&&stableJson(manifest.structuredState.arenaBounds)!==stableJson(p.grant.bounds))throw new Error('CAPTURE_BUNDLE_ACTION_BOUNDS');
 if(manifest.rig==='tank-cardinal-4-snapshot-v2'&&manifest.structuredState&&stableJson(manifest.structuredState.observationBounds)!==stableJson({min:p.tankObservation.min,max:p.tankObservation.max}))throw new Error('CAPTURE_BUNDLE_OBSERVATION_BOUNDS');
 const runtime=new EvidenceRuntime({runDir,...p.identity});await runtime.init();if(!runtime.finalized)await runtime.ingestAvailable();
 const records=(await runtime.store.readObservations()).filter(r=>r.payload?.kind==='cardinal4_capture_manifest'&&r.payload?.captureId===unknown.captureId);
 if(records.length!==1||stableJson(validateVisualManifest(records[0].payload))!==stableJson(manifest))return unknown;
 const bundle=await bundleFromManifest({runDir,manifest});bundle.sourceBinding='CANONICAL_OWNER_CAPTURE';bundle.sourceObservationId=records[0].observationId;
 return {schemaVersion:1,status:bundle.status,captureIndex,captureId:manifest.captureId,bundle,execution:'VERIFIED_RETAINED_REFERENCES'};
}
export const inspectCapture=captureBundle;

/** Explicit derived HTML outside a retained run. Caller chooses a new output file. */
export async function writeCaptureContactSheet({runDir,envelopeHash,captureIndex,outputFile}){
 const path=(await import('node:path')).default;
 if(typeof outputFile!=='string'||!path.isAbsolute(outputFile)||path.resolve(outputFile)!==outputFile)throw new Error('CONTACT_SHEET_OUTSIDE_RUN_REQUIRED');
 const relative=path.relative(runDir,outputFile);
 if(!(relative.startsWith('..'+path.sep)||path.isAbsolute(relative))||await realpath(path.dirname(outputFile))!==path.dirname(outputFile))throw new Error('CONTACT_SHEET_OUTSIDE_RUN_REQUIRED');
 const result=await captureBundle({runDir,envelopeHash,captureIndex});if(!result.bundle||result.status!=='COMPLETE')throw new Error('CONTACT_SHEET_VERIFIED_CAPTURE_REQUIRED');
 const figures=[];for(const v of result.bundle.views){const frame=result.bundle.views.find(x=>x.view===v.view);const bytes=(await readRegisteredFile({root:runDir,relativePath:frame.image.path,expectedSha256:frame.image.sha256,maxBytes:4*1024*1024})).bytes;
  figures.push('<figure><figcaption>'+v.view+'</figcaption><img alt="'+v.view+'" src="data:image/png;base64,'+bytes.toString('base64')+'"></figure>');}
 const html='<!doctype html><meta charset="utf-8"><title>Tank capture '+captureIndex+'</title><style>body{background:#181818;color:white;font:16px sans-serif}main{display:grid;grid-template-columns:1fr 1fr}img{width:100%}figure{margin:8px}</style><p>Derived contact sheet. Sequential paused views; raw PNGs and structured state remain authoritative.</p><main>'+figures.join('')+'</main>';
 const h=await open(outputFile,'wx',0o600);try{await h.writeFile(html);await h.sync();}finally{await h.close();}
 return {artifactRole:'DERIVED_ARTIFACT',outputFile,sourceCaptureId:result.captureId};
}
