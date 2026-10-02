export const DECISION_OBSERVATION_VERSION=1;
export const DECISION_STAGES=Object.freeze(['INPUT','STATE','CANDIDATE','EVALUATION','SELECTION','EXECUTION','RESULT']);
export const DECISION_EPISTEMIC=Object.freeze([
  'DIRECT_OBSERVED','SAMPLED_OBSERVED','INSTRUMENTED_ALGORITHM_STATE','DERIVED_FROM_OBSERVED',
  'COMMUNITY_HYPOTHESIS','NOT_EXPOSED','NOT_APPLICABLE','NOT_CAPTURED','UNKNOWN'
]);
export const DECISION_RELATIONS=Object.freeze([
  'DIRECT_RUNTIME_RELATION','ALGORITHM_TRACE_RELATION','TEMPORAL_ASSOCIATION',
  'DERIVED_SPATIAL_ASSOCIATION','UNKNOWN_CAUSALITY'
]);
export const DECISION_VISUAL_PRIMITIVES=Object.freeze([
  'POINT','VECTOR','PATH','REGION','VOXEL_FIELD','CANDIDATE_SET','SCALAR_SCORE',
  'STATE_MACHINE','SCHEDULER_LANE','RELATION_EDGE','EVENT_MARKER','TEXT_FACT'
]);
export const DECISION_CAPABILITY_STATES=Object.freeze([
  'DIRECT','SAMPLED','PARTIAL','DERIVED','AVAILABLE','ON_DEMAND_INSTRUMENTED',
  'CAPTURE_REQUIRED','DIRECT_OR_DERIVED','NOT_EXPOSED','NOT_APPLICABLE','NOT_CAPTURED','UNKNOWN'
]);

const obj=v=>v!==null&&typeof v==='object'&&!Array.isArray(v);
const copy=v=>v==null?v:structuredClone(v);
function str(v,n,nullable=false){
  if(nullable&&v==null)return null;
  if(typeof v!=='string'||!v.trim())throw new TypeError(n+' must be a non-empty string');
  return v.trim();
}
function uint(v,n,min=0){
  if(!Number.isSafeInteger(v)||v<min)throw new TypeError(n+' must be a safe integer >= '+min);
  return v;
}
function iso(v,n){
  if(typeof v!=='string'||!Number.isFinite(Date.parse(v)))throw new TypeError(n+' must be an ISO timestamp');
  return v;
}
function idList(v,n,allowEmpty=false){
  if(!Array.isArray(v)||(!allowEmpty&&v.length===0))throw new TypeError(n+' must be '+(allowEmpty?'an':'a non-empty')+' array');
  const out=v.map((x,i)=>str(x,n+'['+i+']'));
  if(new Set(out).size!==out.length)throw new TypeError(n+' contains duplicate IDs');
  return out;
}
function epistemic(v,n='epistemicStatus'){
  const s=str(v,n);if(!DECISION_EPISTEMIC.includes(s))throw new TypeError(n+' invalid: '+s);return s;
}
function runtimeEpistemic(v,n='epistemicStatus'){
  const s=epistemic(v,n);
  if(s==='COMMUNITY_HYPOTHESIS')throw new TypeError('COMMUNITY_HYPOTHESIS is research-only and cannot be runtime truth');
  return s;
}
function unavailable(s){return ['NOT_EXPOSED','NOT_APPLICABLE','NOT_CAPTURED','UNKNOWN'].includes(s);}

export function normalizeDecisionIdentity(value){
  if(!obj(value))throw new TypeError('identity must be an object');
  const out={
    debugSessionId:str(value.debugSessionId,'identity.debugSessionId'),
    runId:str(value.runId,'identity.runId'),
    runSnapshotId:str(value.runSnapshotId,'identity.runSnapshotId',true),
    processEpoch:uint(value.processEpoch,'identity.processEpoch'),
    experimentId:str(value.experimentId,'identity.experimentId',true),
    generationId:str(value.generationId,'identity.generationId',true),
    requestId:str(value.requestId,'identity.requestId',true),
    arenaId:str(value.arenaId,'identity.arenaId',true),
    arenaEpoch:value.arenaEpoch==null?null:uint(value.arenaEpoch,'identity.arenaEpoch'),
    arenaRevision:value.arenaRevision==null?null:uint(value.arenaRevision,'identity.arenaRevision'),
    resourceEpoch:value.resourceEpoch==null?null:uint(value.resourceEpoch,'identity.resourceEpoch'),
    entityUuid:str(value.entityUuid,'identity.entityUuid'),
    stableEntityId:str(value.stableEntityId,'identity.stableEntityId',true),
    entityType:str(value.entityType,'identity.entityType'),
    gameTime:uint(value.gameTime,'identity.gameTime'),
    observedAt:iso(value.observedAt,'identity.observedAt')
  };
  return out;
}
export function decisionIdentityFingerprint(value){
  const i=normalizeDecisionIdentity(value);
  return [i.debugSessionId,i.runId,i.runSnapshotId??'',i.processEpoch,i.experimentId??'',i.generationId??'',
    i.requestId??'',i.arenaId??'',i.arenaEpoch??'',i.arenaRevision??'',i.resourceEpoch??'',
    i.entityUuid,i.stableEntityId??'',i.entityType].join('|');
}
export function assertSameDecisionIdentity(expected,actual){
  const a=decisionIdentityFingerprint(expected),b=decisionIdentityFingerprint(actual);
  if(a!==b)throw new TypeError('decision identity mismatch');
  return true;
}
export function normalizeDecisionAdapter(value){
  if(!obj(value))throw new TypeError('adapter must be an object');
  return {id:str(value.id,'adapter.id'),version:uint(value.version,'adapter.version',1),
    targetModId:str(value.targetModId,'adapter.targetModId',true),
    targetModVersion:str(value.targetModVersion,'adapter.targetModVersion',true),
    minecraftVersion:str(value.minecraftVersion,'adapter.minecraftVersion',true),
    loader:str(value.loader,'adapter.loader',true),
    instrumentation:str(value.instrumentation,'adapter.instrumentation',true),
    observerEffectRisk:str(value.observerEffectRisk,'adapter.observerEffectRisk',true),
    sourceProvenance:value.sourceProvenance==null?null:copy(value.sourceProvenance)};
}
export function normalizeDecisionCapabilities(value){
  if(!obj(value))throw new TypeError('capabilities must be an object');
  const out={};
  for(const [key,val] of Object.entries(value)){
    if(!/^[A-Za-z0-9_.:-]{1,128}$/.test(key))throw new TypeError('invalid capability key: '+key);
    const status=str(val,'capability '+key);
    if(!DECISION_CAPABILITY_STATES.includes(status))throw new TypeError('invalid capability state for '+key+': '+status);
    out[key]=status;
  }
  return out;
}
export function normalizeDecisionStage(value){
  if(!obj(value))throw new TypeError('decision stage must be an object');
  const stage=str(value.stage,'stage');
  if(!DECISION_STAGES.includes(stage))throw new TypeError('invalid decision stage: '+stage);
  const status=runtimeEpistemic(value.epistemicStatus);
  const sourceIds=idList(value.sourceIds??[],'sourceIds',true);
  if(!unavailable(status)&&sourceIds.length===0)throw new TypeError('observed/derived decision stage requires sourceIds');
  return {stage,epistemicStatus:status,facts:value.facts==null?{}:copy(value.facts),sourceIds,
    completeness:str(value.completeness,'completeness',true),limitations:Array.isArray(value.limitations)?value.limitations.map(x=>str(x,'limitation')):[]};
}
export function normalizeDecisionRelation(value){
  if(!obj(value))throw new TypeError('decision relation must be an object');
  const semantics=str(value.semantics,'relation.semantics');
  if(!DECISION_RELATIONS.includes(semantics))throw new TypeError('invalid relation semantics: '+semantics);
  const status=runtimeEpistemic(value.epistemicStatus);
  const sourceIds=idList(value.sourceIds??[],'relation.sourceIds',true);
  if(!unavailable(status)&&sourceIds.length===0)throw new TypeError('observed/derived relation requires sourceIds');
  return {relationId:str(value.relationId,'relation.relationId'),fromRef:str(value.fromRef,'relation.fromRef'),
    toRef:str(value.toRef,'relation.toRef'),semantics,epistemicStatus:status,sourceIds,
    label:str(value.label,'relation.label',true),details:value.details==null?null:copy(value.details)};
}
export function normalizeDecisionPrimitive(value){
  if(!obj(value))throw new TypeError('decision visual primitive must be an object');
  const type=str(value.type,'primitive.type');
  if(!DECISION_VISUAL_PRIMITIVES.includes(type))throw new TypeError('invalid visual primitive: '+type);
  const status=runtimeEpistemic(value.epistemicStatus);
  const sourceIds=idList(value.sourceIds??[],'primitive.sourceIds',true);
  if(!unavailable(status)&&sourceIds.length===0)throw new TypeError('observed/derived primitive requires sourceIds');
  if(!obj(value.payload))throw new TypeError('primitive.payload must be an object');
  return {primitiveId:str(value.primitiveId,'primitive.primitiveId'),type,epistemicStatus:status,
    sourceIds,payload:copy(value.payload),label:str(value.label,'primitive.label',true)};
}
export function buildDecisionObservationModel(input){
  if(!obj(input))throw new TypeError('DecisionObservationModel input must be an object');
  const identity=normalizeDecisionIdentity(input.identity),adapter=normalizeDecisionAdapter(input.adapter);
  const capabilities=normalizeDecisionCapabilities(input.capabilities??{});
  if(!Array.isArray(input.stages??[])||!Array.isArray(input.relations??[])||!Array.isArray(input.visualPrimitives??[]))
    throw new TypeError('stages/relations/visualPrimitives must be arrays');
  if((input.stages??[]).length>DECISION_STAGES.length)throw new TypeError('too many stage groups');
  if((input.relations??[]).length>256||(input.visualPrimitives??[]).length>256)throw new TypeError('decision model bounded collection limit exceeded');
  const stages=(input.stages??[]).map(normalizeDecisionStage);
  const names=new Set();for(const s of stages){if(names.has(s.stage))throw new TypeError('duplicate decision stage: '+s.stage);names.add(s.stage);}
  stages.sort((a,b)=>DECISION_STAGES.indexOf(a.stage)-DECISION_STAGES.indexOf(b.stage));
  const relations=(input.relations??[]).map(normalizeDecisionRelation);
  const relIds=new Set();for(const r of relations){if(relIds.has(r.relationId))throw new TypeError('duplicate relationId: '+r.relationId);relIds.add(r.relationId);}
  const visualPrimitives=(input.visualPrimitives??[]).map(normalizeDecisionPrimitive);
  const primitiveIds=new Set();for(const p of visualPrimitives){if(primitiveIds.has(p.primitiveId))throw new TypeError('duplicate primitiveId: '+p.primitiveId);primitiveIds.add(p.primitiveId);}
  const sourceIds=[...new Set([...stages.flatMap(s=>s.sourceIds),...relations.flatMap(r=>r.sourceIds),...visualPrimitives.flatMap(p=>p.sourceIds)])];
  const model={schema:'kneekura.decision_observation_model',version:1,kind:'DecisionObservationModel',
    identity,adapter,capabilities,stages,relations,visualPrimitives,provenance:{sourceIds,sourceCount:sourceIds.length},
    policy:{allStagesOptional:true,causalNarrativeGenerated:false,motivesInferred:false,rawEvidenceSeparate:true,
      visualizationMutatesGameplay:false,decisionViewDefault:'OFF'},
    limitations:Array.isArray(input.limitations)?input.limitations.map(x=>str(x,'limitation')):[]};
  return assertValidDecisionObservationModel(model);
}
export function assertValidDecisionObservationModel(model){
  if(!obj(model)||model.schema!=='kneekura.decision_observation_model'||model.version!==1||model.kind!=='DecisionObservationModel')
    throw new TypeError('DecisionObservationModel contract mismatch');
  normalizeDecisionIdentity(model.identity);normalizeDecisionAdapter(model.adapter);normalizeDecisionCapabilities(model.capabilities);
  if(model.policy?.causalNarrativeGenerated!==false||model.policy?.motivesInferred!==false||
     model.policy?.rawEvidenceSeparate!==true||model.policy?.visualizationMutatesGameplay!==false)
    throw new TypeError('decision epistemic safety policy mismatch');
  const stageNames=new Set();
  for(const s of model.stages??[]){const n=normalizeDecisionStage(s);if(stageNames.has(n.stage))throw new TypeError('duplicate decision stage');stageNames.add(n.stage);}
  for(const r of model.relations??[])normalizeDecisionRelation(r);
  for(const p of model.visualPrimitives??[])normalizeDecisionPrimitive(p);
  return model;
}
export function buildDecisionObservationPacket(model,options={}){
  assertValidDecisionObservationModel(model);
  const maxStages=options.maxStages??DECISION_STAGES.length,maxRelations=options.maxRelations??128,maxPrimitives=options.maxPrimitives??64;
  for(const [v,n,limit] of [[maxStages,'maxStages',DECISION_STAGES.length],[maxRelations,'maxRelations',256],[maxPrimitives,'maxPrimitives',256]])
    if(!Number.isInteger(v)||v<0||v>limit)throw new TypeError(n+' out of bounds');
  const stages=model.stages.slice(0,maxStages),relations=model.relations.slice(0,maxRelations),visualPrimitives=model.visualPrimitives.slice(0,maxPrimitives);
  const sourceIds=[...new Set([...stages.flatMap(s=>s.sourceIds),...relations.flatMap(r=>r.sourceIds),...visualPrimitives.flatMap(p=>p.sourceIds)])];
  const available={},unavailableCaps={};
  for(const [k,v] of Object.entries(model.capabilities)){
    (['NOT_EXPOSED','NOT_APPLICABLE','NOT_CAPTURED','UNKNOWN'].includes(v)?unavailableCaps:available)[k]=v;
  }
  return {schema:'kneekura.decision_observation_packet',version:1,kind:'DecisionObservationPacket',
    identity:copy(model.identity),adapter:copy(model.adapter),capabilities:copy(model.capabilities),
    capabilitySummary:{available,unavailable:unavailableCaps},
    structuredState:stages,relations,visualPrimitives,
    availableDrillDownChannels:Object.entries(model.capabilities).filter(([,v])=>['AVAILABLE','ON_DEMAND_INSTRUMENTED','CAPTURE_REQUIRED','DIRECT','SAMPLED','PARTIAL','DERIVED','DIRECT_OR_DERIVED'].includes(v)).map(([k])=>k),
    provenance:{sourceIds,sourceCount:sourceIds.length},
    policy:{causalNarrativeGenerated:false,motivesInferred:false,screenshotsPrimaryInput:false,
      relationshipSemanticsAuthoritative:true,rawEvidenceSeparate:true},
    truncation:{stages:model.stages.length-stages.length,relations:model.relations.length-relations.length,
      visualPrimitives:model.visualPrimitives.length-visualPrimitives.length},
    limitations:copy(model.limitations)};
}
