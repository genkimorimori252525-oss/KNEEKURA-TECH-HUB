import { exactKeys, hashId, identifier, integer, sha256, stableJson } from '../bridge/json.mjs';
import { validateRawFrame, validateVisualManifest, validateVisualIdentity, CARDINAL_VIEWS } from './visual-capture.mjs';
const same=(a,b)=>stableJson(a)===stableJson(b);
const IDENTITY_KEYS=['debugSessionId','runId','runSnapshotId','processEpoch','experimentId','generation','requestHash','arenaId','arenaEpoch','arenaRevision','baselineHash'];
const PACKET_KEYS=['packetId','schemaVersion','kind','binding','sameFrame','packetFormat','benchmark','labels','structuredSummary','structuredSummaryArtifact',
 'topDown','contactSheet','annotatedContactSheet','rawViews','visualChecks','timeline','timelineArtifact','drilldown','capture','visualVerdict','behaviorVerdict','acceptance','runtimeAttestation'];
function require(value,reason) {if(!value)throw new TypeError(reason);}
function artifact(ref,{role,extension,mediaType,binding,ids,rawHashes}) {
 exactKeys(ref,['artifactId','schemaVersion','role','mediaType','derived','sha256','bytes','path','sourceObservationIds','rawSourceHashes','binding','details'],'PACKET_ARTIFACT');
 const {artifactId,...body}=ref;hashId(artifactId);hashId(ref.sha256);integer(ref.bytes,1,32*1024*1024);
 require(ref.schemaVersion===1&&ref.role===role&&ref.mediaType===mediaType&&ref.derived===true&&
   ref.path===`evidence/derived/visual/${ref.sha256}.${extension}`&&sha256(stableJson(body))===artifactId,'PACKET_ARTIFACT_INTEGRITY');
 require(same(ref.binding,binding)&&same(ref.sourceObservationIds,ids)&&same(ref.rawSourceHashes,rawHashes),'PACKET_ARTIFACT_LINEAGE_MISMATCH');
}
/** Validate self-integrity AND consistent nested identity; a self-hash alone is not a schema. */
export function validatePacket(input) {
 const packet=structuredClone(input);exactKeys(packet,PACKET_KEYS,'AI_PACKET');
 const {packetId,...body}=packet;hashId(packetId);
 require(sha256(stableJson(body))===packetId&&packet.schemaVersion===1&&packet.kind==='ai_visual_observation_packet','AI_PACKET_INTEGRITY');
 const b=packet.binding;
 exactKeys(b,[...IDENTITY_KEYS,'captureId','subjects','evidenceCut','sourceObservationId','canonicalManifestHash','controlledStateHash','controlledStateHashSemantics','stateWindow',...(b.rig==='tank-cardinal-4-snapshot-v2'?['rig','tankObservationHash']:[])],'PACKET_BINDING');
 const identity=Object.fromEntries(IDENTITY_KEYS.map(key=>[key,b[key]]));validateVisualIdentity(identity);identifier(b.captureId);identifier(b.sourceObservationId);
 for(const key of ['canonicalManifestHash','controlledStateHash'])hashId(b[key]);
 require(b.controlledStateHashSemantics==='PRODUCER_BYTES_NOT_REENCODED','PACKET_HASH_SEMANTICS');
 exactKeys(b.evidenceCut,['count','lastObservationId','observationIdsSha256','canonicalRecordsSha256'],'PACKET_CUT');
 integer(b.evidenceCut.count,1,Number.MAX_SAFE_INTEGER);identifier(b.evidenceCut.lastObservationId);
 for(const key of ['observationIdsSha256','canonicalRecordsSha256']) {require(typeof b.evidenceCut[key]==='string'&&b.evidenceCut[key].startsWith('sha256:'),'PACKET_CUT_HASH');hashId(b.evidenceCut[key].slice(7));}
 const w=b.stateWindow;
 exactKeys(w,['serverTickStart','serverTickEnd','serverGameTime','clientTickStart','clientTickEnd','renderFrameStart','renderFrameEnd'],'PACKET_WINDOW');
 for(const value of Object.values(w))integer(value,0,Number.MAX_SAFE_INTEGER);
 require(Array.isArray(packet.rawViews)&&packet.rawViews.length===4,'PACKET_RAW_VIEWS');
 const frames=packet.rawViews.map(v=>{
  const {manifestObservationId,producerFrameObservationHash,producerFrameObservationHashSemantics,...raw}=v;
  require(manifestObservationId===b.sourceObservationId&&producerFrameObservationHashSemantics==='EXACT_PRODUCER_FRAME_ROW_BYTES','PACKET_SOURCE_REFERENCE');
  hashId(producerFrameObservationHash);return validateRawFrame(raw);
 });
 exactKeys(packet.capture,['status','restoration','restorationProof','perturbations','invalidatedAssertions','barrierDurationMs','captureDurationNanos'],'PACKET_CAPTURE');
 const m=validateVisualManifest({schemaVersion:1,kind:'cardinal4_capture_manifest',captureId:b.captureId,rig:b.rig??'cardinal-4-snapshot-v1',...(b.rig==='tank-cardinal-4-snapshot-v2'?{tankObservationHash:b.tankObservationHash}:{}),
  identity,subjects:b.subjects,controlledStateHash:b.controlledStateHash,sameFrame:packet.sameFrame,
  result:{status:packet.capture.status,sameFrame:packet.sameFrame,restoration:packet.capture.restoration,perturbations:packet.capture.perturbations,
   invalidatedAssertions:packet.capture.invalidatedAssertions,frames:frames.map((f,i)=>({view:f.view,status:'PRESENT',renderFrame:f.renderFrame,imageHash:f.imageHash,observationHash:packet.rawViews[i].producerFrameObservationHash})),gaps:[]},
  frames,structuredState:packet.structuredSummary,renderFrameStart:w.renderFrameStart,renderFrameEnd:w.renderFrameEnd,
  clientTickStart:w.clientTickStart,clientTickEnd:w.clientTickEnd,barrierDurationMs:packet.capture.barrierDurationMs,
  restorationProof:packet.capture.restorationProof,runtimeAttestation:packet.runtimeAttestation,visualVerdict:packet.visualVerdict,behaviorVerdict:packet.behaviorVerdict});
 require(m.result.status==='COMPLETE'&&m.result.restoration==='RESTORED'&&sha256(stableJson(m))===b.canonicalManifestHash&&
   w.serverTickStart===frames[0].serverTick&&w.serverTickEnd===frames.at(-1).serverTick&&w.serverGameTime===frames[0].serverGameTime&&
   packet.capture.captureDurationNanos===frames.reduce((sum,f)=>sum+f.captureDurationNanos,0),'PACKET_CAPTURE_BINDING');
 const labels=[...b.subjects].sort().map((uuid,i)=>({label:String.fromCharCode(65+i),uuid,uuidSuffix:uuid.slice(-6)}));
 require(same(packet.labels,labels),'PACKET_LABEL_MISMATCH');
 require(Array.isArray(packet.timeline)&&packet.timeline.length<=128&&Buffer.byteLength(stableJson(packet.timeline))<=128*1024,'PACKET_TIMELINE_LIMIT');
 const timelineIds=packet.timeline.map(r=>identifier(r.observationId));require(new Set(timelineIds).size===timelineIds.length,'PACKET_TIMELINE_DUPLICATE');
 const ids=[b.sourceObservationId,...timelineIds.filter(id=>id!==b.sourceObservationId)];const rawHashes=frames.map(f=>f.imageHash);
 for(const [key,role,extension,mediaType] of [
  ['contactSheet','DERIVED_CONTACT_SHEET','png','image/png'],['annotatedContactSheet','DERIVED_ANNOTATED_CONTACT_SHEET','png','image/png'],
  ['topDown','DERIVED_TOP_DOWN','svg','image/svg+xml'],['structuredSummaryArtifact','DERIVED_STRUCTURED_SUMMARY','json','application/json'],
  ['timelineArtifact','DERIVED_TIMELINE','json','application/json']])artifact(packet[key],{role,extension,mediaType,binding:b,ids,rawHashes});
 require(packet.structuredSummaryArtifact.sha256===sha256(stableJson(packet.structuredSummary))&&packet.timelineArtifact.sha256===sha256(stableJson(packet.timeline)), 'PACKET_FACT_ARTIFACT_MISMATCH');
 require(packet.acceptance==='NOT_EVALUATED'&&packet.packetFormat==='PROVISIONAL_RGB_LABELS_TOPDOWN_V1'&&
  same(packet.benchmark,{status:'DEFERRED_REAL_TASK_REQUIRED',defaultFrozen:false}),'PACKET_VERDICT_OR_FORMAT');
 require(Array.isArray(packet.visualChecks)&&packet.visualChecks.length<=32,'PACKET_VISUAL_CHECK_LIMIT');
 const checkIds=new Set();
 for(const c of packet.visualChecks) {
  exactKeys(c,['checkId','subjectUuid','question','answer','evidenceViews','epistemicStatus','resolution','evidence','semantics'],'PACKET_VISUAL_CHECK');
  identifier(c.checkId);require(!checkIds.has(c.checkId),'PACKET_VISUAL_CHECK_DUPLICATE');checkIds.add(c.checkId);
  require(b.subjects.includes(c.subjectUuid)&&['YES','NO','NOT_VISIBLE','AMBIGUOUS','NOT_RUN'].includes(c.answer)&&
   c.epistemicStatus==='INFERRED'&&c.resolution===(['YES','NO'].includes(c.answer)?'ANSWERED_NOT_ACCEPTANCE':'UNRESOLVED')&&
   c.semantics==='VISUAL_FINDING_SUPPORT_ONLY_NEVER_OVERRIDES_STRUCTURED_FACTS'&&
   typeof c.question==='string'&&c.question.trim().length>0&&c.question.length<=512&&Array.isArray(c.evidenceViews)&&c.evidenceViews.length<=4&&
   new Set(c.evidenceViews).size===c.evidenceViews.length&&c.evidenceViews.every(view=>CARDINAL_VIEWS.includes(view))&&
   (c.answer==='NOT_RUN'||c.evidenceViews.length>0)&&
   same(c.evidence,c.evidenceViews.map(view=>({view,imageHash:frames.find(f=>f.view===view)?.imageHash}))), 'PACKET_VISUAL_CHECK');
 }
 require(Array.isArray(packet.drilldown)&&same(packet.drilldown.map(d=>d.level),[0,1,2,3]),'PACKET_DRILLDOWN');
 return packet;
}
