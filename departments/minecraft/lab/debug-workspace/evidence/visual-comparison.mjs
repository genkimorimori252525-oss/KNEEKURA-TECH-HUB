import { canonicalVisualSource, contactSheet } from './visual-compiler.mjs';
import { readRawVisualImage } from './visual-capture.mjs';
import { derivedArtifact } from './visual-artifacts.mjs';
import { decodeJson, sha256, stableJson, exactKeys } from '../bridge/json.mjs';
import { validateVisualExperimentRequest } from './visual-request-contract.mjs';
import { decodePng, encodePngRgba } from '../../simlab/golden/png.mjs';
const same=(a,b)=>stableJson(a)===stableJson(b);
const ALLOWED_DIFFERENCES=['generation',...['profile_id','index_snapshot_id','build_artifact_hash','source_revision','dirty_hash','config_hash','resource_hash'].map(k=>'target.'+k)];
const targetFields=['profile_id','index_snapshot_id','build_artifact_hash','source_revision','dirty_hash','config_hash','resource_hash'];
function boundedList(value,max,label) {if(!Array.isArray(value)||value.length>max)throw new TypeError('INVALID_'+label);}
function fieldValue(request,field) {return field.startsWith('target.')?request.target[field.slice(7)]:request[field];}
function validateDifferences(entries) {
 boundedList(entries,8,'INTENDED_DIFFERENCES');const used=new Set();
 for(const entry of entries) {
  exactKeys(entry,['field','before','after'],'INTENDED_DIFFERENCE');
  if(!ALLOWED_DIFFERENCES.includes(entry.field)||used.has(entry.field)||same(entry.before,entry.after))throw new TypeError('INVALID_INTENDED_DIFFERENCE');
  used.add(entry.field);
 }
}
function requestFor(bytes,source) {
 if(!Buffer.isBuffer(bytes)||bytes.length>128*1024||sha256(bytes)!==source.manifest.identity.requestHash)throw new TypeError('REQUEST_HASH_MISMATCH');
 const r=validateVisualExperimentRequest(decodeJson(bytes,128*1024));
 const i=source.manifest.identity;
 if(r.experiment_id!==i.experimentId||r.generation!==i.generation||r.arena.arena_id!==i.arenaId||r.arena.baseline_hash!==i.baselineHash||
   !same(r.arena.bounds,source.facts.arenaBounds))throw new TypeError('REQUEST_CAPTURE_IDENTITY_OR_BASELINE_MISMATCH');
 if(!same(r.subjects.map(s=>s.uuid).sort(),[...source.manifest.subjects].sort()))throw new TypeError('REQUEST_CAPTURE_SUBJECT_MISMATCH');
 if(r.visual_rig.mode!==source.manifest.rig||source.manifest.frames.some(f=>!same(f.camera.viewport,r.visual_rig.viewport)||Math.abs(f.camera.fov-r.visual_rig.fov)>0.001))throw new TypeError('REQUEST_CAPTURE_CAMERA_MISMATCH');
 return r;
}
function declaredSetup(request) {
 return {experimentId:request.experiment_id,arena:request.arena,subjects:request.subjects,
  initialState:request.initial_state,actions:request.actions,assertions:request.assertions,
  observationScopes:request.observation_scopes,visualRig:request.visual_rig,budgets:request.budgets};
}
function captureConditions(source) {
 const m=source.manifest; const {cameraUuid,...humanState}=m.restorationProof.expected;
 return {rig:m.rig,sameFrame:m.sameFrame,dimension:source.facts.dimension,
  perturbations:m.result.perturbations,invalidatedAssertions:m.result.invalidatedAssertions,humanState,
  frames:m.frames.map(f=>({view:f.view,camera:f.camera,partialTick:f.partialTick,captureStage:f.captureStage,artifactRole:f.artifactRole}))};
}
const outcome=source=>({visualVerdict:source.manifest.visualVerdict,behaviorVerdict:source.manifest.behaviorVerdict,
  runtimeAttestation:source.manifest.runtimeAttestation,structuredFacts:source.facts,
  timeline:source.timeline.map(row=>({...row,relativeGameTime:row.gameTime===null?null:row.gameTime-source.facts.gameTime})),
  timelineSemantics:'SELECTED_CANONICAL_ROWS_NOT_CONTINUITY_PROOF'});
function nonComparable(reasons,before=null,after=null) {
 const body={schemaVersion:1,kind:'matched_visual_comparison',status:'NON_COMPARABLE',reasons,before:before?.binding??null,after:after?.binding??null,
  outcomes:{before:before?outcome(before):null,after:after?outcome(after):null},acceptance:'NOT_EVALUATED',pixelDifferenceMeansImprovement:false};
 return {comparison:{comparisonId:sha256(stableJson(body)),...body},artifacts:[]};
}
/** Registered request identities stay exact; execution run/snapshot/capture IDs and ticks are lineage. */
export async function compareVisualRuns({before,after,intendedDifferences=[]}) {
 validateDifferences(intendedDifferences);
 const reasons=[];let a,b,ar,br;
 try {a=await canonicalVisualSource(before);ar=requestFor(before.requestBytes,a);}catch(error){reasons.push('BEFORE:'+error.message);}
 try {b=await canonicalVisualSource(after);br=requestFor(after.requestBytes,b);}catch(error){reasons.push('AFTER:'+error.message);}
 if(reasons.length)return nonComparable(reasons,a,b);
 for(const d of intendedDifferences)if(!same(fieldValue(ar,d.field),d.before)||!same(fieldValue(br,d.field),d.after))throw new TypeError('STALE_INTENDED_DIFFERENCE');
 for(const key of ['generation',...targetFields.map(k=>'target.'+k)])if(!same(fieldValue(ar,key),fieldValue(br,key))&&!intendedDifferences.some(d=>d.field===key))reasons.push('UNINTENDED_DIFFERENCE:'+key);
 if(a.manifest.identity.requestHash!==b.manifest.identity.requestHash&&br.generation<=ar.generation)reasons.push('GENERATION_LINEAGE');
 const setupA=declaredSetup(ar),setupB=declaredSetup(br);
 for(const key of Object.keys(setupA))if(!same(setupA[key],setupB[key]))reasons.push('SETUP_MISMATCH:'+key);
 const ca=captureConditions(a),cb=captureConditions(b);
 for(const key of Object.keys(ca))if(!same(ca[key],cb[key]))reasons.push('CAPTURE_CONDITIONS_MISMATCH:'+key);
 if(reasons.length)return nonComparable(reasons,a,b);
 const images=[];
 try {for(let i=0;i<4;i++)for(const source of [a,b])images.push(decodePng(await readRawVisualImage(source.store.runDir,source.manifest.frames[i])));}
 catch(error){return nonComparable(['RAW_IMAGE:'+error.message],a,b);}
 const subjectCorrespondence=ar.subjects.map(s=>({subjectId:s.subject_id,beforeUuid:s.uuid,afterUuid:br.subjects.find(t=>t.subject_id===s.subject_id).uuid,entityType:s.entity_type}));
 const structuredDifferences=subjectCorrespondence.flatMap(pair=>{
  const {uuid:ua,...factsA}=a.facts.subjects.find(s=>s.uuid===pair.beforeUuid);
  const {uuid:ub,...factsB}=b.facts.subjects.find(s=>s.uuid===pair.afterUuid);
  return same(factsA,factsB)?[]:[{subjectId:pair.subjectId,before:factsA,after:factsB,interpretation:'OBSERVED_STATE_DIFFERENCE_NOT_IMPROVEMENT'}];
 });
 const artifacts=[];const binding={before:a.binding,after:b.binding};
 const sourceObservationIds=[...new Set([...a.sourceObservationIds,...b.sourceObservationIds])];
 const rawSourceHashes=[...a.manifest.frames.map(f=>f.imageHash),...b.manifest.frames.map(f=>f.imageHash)];
 const add=(bytes,role,mediaType,extension,details={})=>{const artifact=derivedArtifact(bytes,{role,mediaType,extension,sourceObservationIds,rawSourceHashes,binding,details});artifacts.push(artifact);return artifact.ref;};
 const sideBySide=add(encodePngRgba(contactSheet(images,{headers:a.manifest.frames.flatMap(f=>[f.view+' A',f.view+' B'])})),
  'DERIVED_BEFORE_AFTER_SHEET','image/png','png',{rows:['north','east','south','west'],columns:['before','after']});
 const body={schemaVersion:1,kind:'matched_visual_comparison',status:'MATCHED_EVIDENCE_ONLY',reasons:[],before:a.binding,after:b.binding,
  intendedDifferences:structuredClone(intendedDifferences),subjectCorrespondence,
  requestLineage:{before:{experimentId:ar.experiment_id,requestHash:a.manifest.identity.requestHash,target:ar.target,actions:[...ar.initial_state,...ar.actions].map(x=>x.action_id)},
    after:{experimentId:br.experiment_id,requestHash:b.manifest.identity.requestHash,target:br.target,actions:[...br.initial_state,...br.actions].map(x=>x.action_id)}},
  declaredSetupHash:sha256(stableJson(setupA)),captureConditionsHash:sha256(stableJson(ca)),sideBySide,
  viewPairs:a.manifest.frames.map((f,i)=>({view:f.view,before:{imageHash:f.imageHash,camera:f.camera,sourceObservationId:a.binding.sourceObservationId},
    after:{imageHash:b.manifest.frames[i].imageHash,camera:b.manifest.frames[i].camera,sourceObservationId:b.binding.sourceObservationId}})),
  structuredDifferences,outcomes:{before:outcome(a),after:outcome(b)},acceptance:'NOT_EVALUATED',pixelDifferenceMeansImprovement:false,
  runtimeAttestation:'OWNER_GATE_REQUIRED_NOT_INFERRED_FROM_COMPARISON'};
 const comparison={comparisonId:sha256(stableJson(body)),...body};
 const comparisonArtifact=add(Buffer.from(stableJson(comparison)),'DERIVED_COMPARISON_BUNDLE','application/json','json');
 return {comparison,comparisonArtifact,artifacts};
}
