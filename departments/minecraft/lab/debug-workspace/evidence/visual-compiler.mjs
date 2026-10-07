import { validatePacket } from './visual-packet.mjs';
import { EvidenceStore } from './store.mjs';
import { validateVisualManifest, readRawVisualImage, CARDINAL_VIEWS } from './visual-capture.mjs';
import { sha256, stableJson, identifier, exactKeys, integer } from '../bridge/json.mjs';
import { decodePng, encodePngRgba } from '../../simlab/golden/png.mjs';
import { derivedArtifact, persistDerivedArtifacts } from './visual-artifacts.mjs';
import { canvas, text, blit, validateFacts, annotatedImage, topDownSvg } from './visual-geometry.mjs';
const same=(a,b)=>stableJson(a)===stableJson(b);
function boundedList(value,max,label) {if(!Array.isArray(value)||value.length>max)throw new TypeError(label+'_LIMIT');}

/** Snapshot the existing canonical prefix. Never accept caller-supplied source facts/cut. */
export async function canonicalVisualSource({store,sourceObservationId,timelineObservationIds=[]}) {
  if(!(store instanceof EvidenceStore))throw new TypeError('CANONICAL_EVIDENCE_STORE_REQUIRED');
  identifier(sourceObservationId);boundedList(timelineObservationIds,128,'TIMELINE');
  timelineObservationIds.forEach(identifier);
  if(new Set(timelineObservationIds).size!==timelineObservationIds.length)throw new TypeError('DUPLICATE_TIMELINE_OBSERVATION');
  const evidenceCut=store.canonicalPrefixProof();
  const entries=[...store.observationById.entries()].slice(0,evidenceCut.count);
  const records=(await store.readObservations()).slice(0,evidenceCut.count);
  if(!same(records.map(r=>[r.observationId,stableJson(r)]),entries))throw new TypeError('CANONICAL_OBSERVATION_CHANGED');
  const record=records.find(r=>r.observationId===sourceObservationId);
  if(!record)throw new TypeError('SOURCE_OBSERVATION_MISSING');
  if(record.epistemicStatus!=='OBSERVED'||record.completeness?.complete!==true)throw new TypeError('COMPLETE_OBSERVED_CAPTURE_REQUIRED');
  const manifest=validateVisualManifest(record.payload);
  for(const key of ['debugSessionId','runId','runSnapshotId'])if(manifest.identity[key]!==store.identity[key]||manifest.identity[key]!==record[key])throw new TypeError('CAPTURE_IDENTITY_MISMATCH');
  for(const key of ['processEpoch','arenaEpoch'])if(manifest.identity[key]!==record[key])throw new TypeError('CAPTURE_IDENTITY_MISMATCH');
  if(record.scope?.kind!=='EXPERIMENT'||record.scope.experimentId!==manifest.identity.experimentId)throw new TypeError('CAPTURE_IDENTITY_MISMATCH');
  if(manifest.result.status!=='COMPLETE'||manifest.result.restoration!=='RESTORED')throw new TypeError('COMPLETE_RESTORED_CAPTURE_REQUIRED');
  const facts=validateFacts(manifest.structuredState,manifest.subjects);
  if(manifest.frames.some(f=>f.serverGameTime!==facts.gameTime))throw new TypeError('STRUCTURED_STATE_TICK_MISMATCH');
  const timeline=timelineObservationIds.map(id=>{
    const row=records.find(r=>r.observationId===id);
    if(!row)throw new TypeError('TIMELINE_OBSERVATION_MISSING');
    for(const key of ['debugSessionId','runId','runSnapshotId','processEpoch','arenaEpoch'])if(row[key]!==manifest.identity[key])throw new TypeError('TIMELINE_IDENTITY_MISMATCH');
    // Explicitly reject an unrelated experiment even inside the same run.
    if(row.scope.kind==='EXPERIMENT'&&row.scope.experimentId!==manifest.identity.experimentId)throw new TypeError('TIMELINE_EXPERIMENT_MISMATCH');
    return {observationId:id,lane:row.lane,writerId:row.writerId,writerSeq:row.writerSeq,gameTime:row.gameTime??null,
      epistemicStatus:row.epistemicStatus,completeness:row.completeness,scope:structuredClone(row.scope),source:structuredClone(row.source),
      observedAt:row.observedAt,resourceEpoch:row.resourceEpoch,
      contextRole:row.scope.kind==='ENTITY_UUID'?(manifest.subjects.includes(row.scope.entityUuid)?'CAPTURE_SUBJECT':'CONTEXT_ONLY_UNSELECTED_SUBJECT'):'EXPLICIT_RUN_CONTEXT',
      payload:structuredClone(row.payload)};
  });
  if(Buffer.byteLength(stableJson(timeline))>128*1024)throw new TypeError('TIMELINE_BYTE_LIMIT');
  const binding={...manifest.identity,...(manifest.rig==='tank-cardinal-4-snapshot-v2'?{rig:manifest.rig,tankObservationHash:manifest.tankObservationHash}:{}),captureId:manifest.captureId,subjects:[...manifest.subjects],evidenceCut,
    sourceObservationId,canonicalManifestHash:sha256(stableJson(manifest)),controlledStateHash:manifest.controlledStateHash,
    controlledStateHashSemantics:'PRODUCER_BYTES_NOT_REENCODED',
    stateWindow:{serverTickStart:manifest.frames[0].serverTick,serverTickEnd:manifest.frames.at(-1).serverTick,
      serverGameTime:manifest.frames[0].serverGameTime,clientTickStart:manifest.clientTickStart,clientTickEnd:manifest.clientTickEnd,
      renderFrameStart:manifest.renderFrameStart,renderFrameEnd:manifest.renderFrameEnd}};
  return {store,manifest,facts,timeline,binding,sourceObservationIds:[sourceObservationId,...timelineObservationIds.filter(id=>id!==sourceObservationId)]};
}
function checks(input,manifest) {
  boundedList(input,32,'VISUAL_CHECK');const seen=new Set();
  return input.map(c=>{
    exactKeys(c,['checkId','subjectUuid','question','answer','evidenceViews'],'VISUAL_CHECK');identifier(c.checkId);
    if(seen.has(c.checkId))throw new TypeError('DUPLICATE_VISUAL_CHECK');seen.add(c.checkId);
    if(!manifest.subjects.includes(c.subjectUuid)||typeof c.question!=='string'||!c.question.trim()||c.question.length>512)throw new TypeError('INVALID_VISUAL_CHECK');
    if(!['YES','NO','NOT_VISIBLE','AMBIGUOUS','NOT_RUN'].includes(c.answer))throw new TypeError('INVALID_VISUAL_ANSWER');
    boundedList(c.evidenceViews,4,'CHECK_VIEWS');
    if(new Set(c.evidenceViews).size!==c.evidenceViews.length||c.evidenceViews.some(v=>!CARDINAL_VIEWS.includes(v))||
        (c.answer!=='NOT_RUN'&&!c.evidenceViews.length))throw new TypeError('VISUAL_ANSWER_EVIDENCE_REQUIRED');
    return {...structuredClone(c),epistemicStatus:'INFERRED',resolution:['YES','NO'].includes(c.answer)?'ANSWERED_NOT_ACCEPTANCE':'UNRESOLVED',
      evidence:c.evidenceViews.map(view=>({view,imageHash:manifest.frames.find(f=>f.view===view).imageHash})),
      semantics:'VISUAL_FINDING_SUPPORT_ONLY_NEVER_OVERRIDES_STRUCTURED_FACTS'};
  });
}
export function contactSheet(images,{columns=2,headers=CARDINAL_VIEWS}={}) {
  if(images.length<1||images.some(i=>i.width!==images[0].width||i.height!==images[0].height))throw new TypeError('MATCHED_VIEWPORT_REQUIRED');
  const [width,height]=[images[0].width,images[0].height];
  const out=canvas(width*columns,(height+18)*Math.ceil(images.length/columns));
  images.forEach((image,i)=>{const x=(i%columns)*width,y=Math.floor(i/columns)*(height+18);text(out,headers[i].toUpperCase(),x+4,y+6);blit(out,image,x,y+18);});
  return out;
}
export async function compileVisualPacket(options) {
  const source=await canonicalVisualSource(options);const {manifest,facts,binding,timeline,sourceObservationIds}=source;
  const visualChecks=checks(options.visualChecks??[],manifest);
  const raw=await Promise.all(manifest.frames.map(f=>readRawVisualImage(options.store.runDir,f)));
  const images=raw.map(decodePng);
  const labels=[...manifest.subjects].sort().map((uuid,i)=>({label:String.fromCharCode(65+i),uuid,uuidSuffix:uuid.slice(-6)}));
  const artifacts=[];
  const rawSourceHashes=manifest.frames.map(f=>f.imageHash);
  const add=(bytes,role,mediaType,extension,details={})=>{const a=derivedArtifact(bytes,{role,mediaType,extension,sourceObservationIds,rawSourceHashes,binding,details});artifacts.push(a);return a.ref;};
  const contact=add(encodePngRgba(contactSheet(images)),'DERIVED_CONTACT_SHEET','image/png','png',{layout:[['north','east'],['south','west']],headerPixels:18});
  const annotations=images.map((image,i)=>annotatedImage(image,manifest.frames[i],facts,labels));
  const annotated=add(encodePngRgba(contactSheet(annotations.map(a=>a.image))),'DERIVED_ANNOTATED_CONTACT_SHEET','image/png','png',
    {views:annotations.map((a,i)=>({view:CARDINAL_VIEWS[i],annotations:a.annotations})),occlusion:'NOT_INFERRED'});
  const topDown=add(topDownSvg(facts,labels),'DERIVED_TOP_DOWN','image/svg+xml','svg',{coordinateSystem:'WORLD_XZ_NORTH_NEGATIVE_Z',factsHash:sha256(stableJson(facts))});
  const summary=add(Buffer.from(stableJson(facts)),'DERIVED_STRUCTURED_SUMMARY','application/json','json');
  const timelineRef=add(Buffer.from(stableJson(timeline)),'DERIVED_TIMELINE','application/json','json');
  const body={schemaVersion:1,kind:'ai_visual_observation_packet',binding,sameFrame:false,
    packetFormat:'PROVISIONAL_RGB_LABELS_TOPDOWN_V1',benchmark:{status:'DEFERRED_REAL_TASK_REQUIRED',defaultFrozen:false},
    labels,structuredSummary:facts,structuredSummaryArtifact:summary,topDown,contactSheet:contact,annotatedContactSheet:annotated,
    rawViews:manifest.frames.map(f=>({...structuredClone(f),manifestObservationId:binding.sourceObservationId,
      producerFrameObservationHash:manifest.result.frames[f.frameIndex].observationHash,
      producerFrameObservationHashSemantics:'EXACT_PRODUCER_FRAME_ROW_BYTES'})),
    visualChecks,timeline,timelineArtifact:timelineRef,
    drilldown:[{level:0,artifacts:[summary.artifactId,topDown.artifactId,contact.artifactId]},
      {level:1,views:CARDINAL_VIEWS,maxViewsPerRequest:2},
      {level:2,operation:'createVisualCrop',coordinates:'RAW_VIEW_PIXELS',maxPixels:1048576,requires:'UNRESOLVED_VISUAL_QUESTION'},
      {level:3,availability:'NOT_IMPLEMENTED_NO_PROVEN_NEED'}],
    capture:{status:manifest.result.status,restoration:manifest.result.restoration,restorationProof:manifest.restorationProof,perturbations:manifest.result.perturbations,
      invalidatedAssertions:manifest.result.invalidatedAssertions,barrierDurationMs:manifest.barrierDurationMs,
      captureDurationNanos:manifest.frames.reduce((sum,f)=>sum+f.captureDurationNanos,0)},
    visualVerdict:manifest.visualVerdict,behaviorVerdict:manifest.behaviorVerdict,
    acceptance:'NOT_EVALUATED',runtimeAttestation:manifest.runtimeAttestation};
  const packet={packetId:sha256(stableJson(body)),...body};
  const packetArtifact=add(Buffer.from(stableJson(packet)),'DERIVED_AI_PACKET','application/json','json');
  return {packet,packetArtifact,artifacts};
}
export async function persistVisualPacket({store,compiled}) {
  validatePacket(compiled.packet);
  for(const a of compiled.artifacts)if(!same(a.ref.binding,compiled.packet.binding)||
    !same(a.ref.sourceObservationIds,compiled.packet.contactSheet.sourceObservationIds)||
    !same(a.ref.rawSourceHashes,compiled.packet.rawViews.map(v=>v.imageHash)))throw new TypeError('PACKET_ARTIFACT_LINEAGE_MISMATCH');
  if(!same(store.identity,{debugSessionId:compiled.packet.binding.debugSessionId,runId:compiled.packet.binding.runId,runSnapshotId:compiled.packet.binding.runSnapshotId}))throw new TypeError('PACKET_STORE_IDENTITY_MISMATCH');
  return persistDerivedArtifacts(store,compiled.artifacts);
}
export async function createVisualCrop({...options}) {
  const source=await canonicalVisualSource(options);const {manifest,binding,sourceObservationIds}=source;
  if(!CARDINAL_VIEWS.includes(options.view))throw new TypeError('INVALID_CROP_VIEW');
  exactKeys(options.region,['x','y','width','height'],'CROP');const {x,y,width,height}=options.region;
  integer(x,0,2047);integer(y,0,2047);integer(width,1,2048);integer(height,1,2048);
  if(width*height>1048576)throw new TypeError('CROP_PIXEL_LIMIT');
  const frame=manifest.frames.find(f=>f.view===options.view);
  if(x+width>frame.camera.viewport[0]||y+height>frame.camera.viewport[1])throw new TypeError('CROP_OUTSIDE_VIEW');
  const image=decodePng(await readRawVisualImage(options.store.runDir,frame));const out=canvas(width,height);
  for(let row=0;row<height;row++)out.rgba.set(image.rgba.subarray(((y+row)*image.width+x)*4,((y+row)*image.width+x+width)*4),row*width*4);
  return derivedArtifact(encodePngRgba(out),{role:'DERIVED_RGB_CROP',mediaType:'image/png',extension:'png',sourceObservationIds,
    rawSourceHashes:[frame.imageHash],binding,details:{view:options.view,region:structuredClone(options.region),camera:frame.camera}});
}
