import {DECISION_OBSERVATION_V1} from './decision-observation.mjs';

const HASH=/^[a-f0-9]{64}$/;
const NAME=/^[a-z0-9_.-]+:[a-z0-9_./-]+$/;
const descriptorKeys=['sdkVersion','id','version','namespace','modId','modVersion','minecraftVersion','loader','loaderVersion',
  'mappedArtifactSha256','classHashes','instrumentation','observerEffectRisk','supportedEpistemicLevels'];
const object=v=>v!==null&&typeof v==='object'&&!Array.isArray(v);
function bounded(value,depth=0,budget={count:0}) {
  if(++budget.count>8192||depth>12)return false;
  if(value===null||typeof value==='boolean')return true;
  if(typeof value==='number')return Number.isFinite(value);
  if(typeof value==='string')return value.length<=512;
  if(Array.isArray(value))return value.length<=64&&value.every(v=>bounded(v,depth+1,budget));
  return object(value)&&Object.keys(value).length<=32&&Object.entries(value).every(([k,v])=>k.length<=128&&bounded(v,depth+1,budget));
}
function freeze(value) {
  if(value&&typeof value==='object'){for(const v of Object.values(value))freeze(v);Object.freeze(value);}
  return value;
}
function descriptor(value) {
  if(!object(value)||Object.keys(value).sort().join(',')!==[...descriptorKeys].sort().join(',')||
      value.sdkVersion!==1||!NAME.test(value.id)||!/^[a-z0-9_.-]{1,64}$/.test(value.namespace)||
      !/^[a-z0-9_.-]{1,64}$/.test(value.modId)||value.namespace!==value.modId||!value.id.startsWith(value.namespace+':')||
      ['version','modVersion','minecraftVersion','loaderVersion','instrumentation','observerEffectRisk'].some(k=>typeof value[k]!=='string'||!value[k].length||value[k].length>128)||
      value.loader!=='forge'||!HASH.test(value.mappedArtifactSha256)||!object(value.classHashes)||
      Object.keys(value.classHashes).length<1||Object.keys(value.classHashes).length>32||
      Object.entries(value.classHashes).some(([k,v])=>!/^[A-Za-z_$][A-Za-z0-9_$.]{1,255}$/.test(k)||!HASH.test(v))||
      !Array.isArray(value.supportedEpistemicLevels)||!value.supportedEpistemicLevels.length||
      new Set(value.supportedEpistemicLevels).size!==value.supportedEpistemicLevels.length||
      value.supportedEpistemicLevels.some(k=>!DECISION_OBSERVATION_V1.epistemicStatuses.includes(k))) {
    throw new TypeError('VERSIONED_SOURCE_PROVEN_ADAPTER_DESCRIPTOR_REQUIRED');
  }
  return freeze(structuredClone(value));
}
function sameDescriptor(a,b) {
  return descriptorKeys.every(k=>k==='classHashes'?Object.keys(a[k]).length===Object.keys(b[k]).length&&
    Object.entries(a[k]).every(([owner,hash])=>b[k][owner]===hash):k==='supportedEpistemicLevels'?
    JSON.stringify(a[k])===JSON.stringify(b[k]):a[k]===b[k]);
}
function validRecord(record,expected) {
  const p=record?.payload;
  if(record?.kind!=='observation'||record.lane!=='AI_DECISION'||record.source?.side!=='SERVER'||record.epistemicStatus!=='OBSERVED'||
      record.completeness?.complete!==true||typeof record.observationId!=='string'||!record.observationId.length||record.observationId.length>512||
      p?.schema!=='kneekura.mod-decision-snapshot/v1'||p.semantics!=='SOURCE_SPECIFIC_CACHED_SNAPSHOT_ONLY'||
      !Number.isSafeInteger(p.targetRevision)||p.targetRevision<1||!Number.isSafeInteger(p.sampleTick)||p.sampleTick<0||
      p.sampleTick!==record.gameTime||p.compatibilityStatus!=='MATCHED_DEVELOPMENT_RESOURCE_NOT_RESIDENT_ATTESTATION'||
      Object.keys(p).some(k=>!['schema','semantics','targetRevision','sampleTick','entityClass','descriptor','compatibilityStatus','data',
        'observerCostNanos','observerCostScope'].includes(k))||!bounded(record)||!object(p.data)||
      typeof p.entityClass!=='string'||!Object.hasOwn(expected.classHashes,p.entityClass)||
      (p.observerCostNanos!==undefined&&(!Number.isSafeInteger(p.observerCostNanos)||p.observerCostNanos<0||
        p.observerCostScope!=='CACHED_CAPTURE_AND_ONCE_SOURCE_PROOF_EXCLUDES_ENCODING_WRITER_VIEWER'))||
      (p.observerCostNanos===undefined&&p.observerCostScope!==undefined))return false;
  try{return sameDescriptor(descriptor(p.descriptor),expected)&&new TextEncoder().encode(JSON.stringify(p)).length<=32768;}
  catch{return false;}
}
function validBurstRecord(record,expected) {
  const p=record?.payload;
  if(record?.kind!=='observation'||record.lane!=='AI_DECISION'||record.source?.side!=='SERVER'||record.epistemicStatus!=='OBSERVED'||
      record.completeness?.complete!==true||typeof record.observationId!=='string'||!record.observationId.length||
      p?.schema!=='kneekura.mod-decision-return/v1'||p.semantics!=='ORIGINAL_MOD_INVOCATION_RETURN_ONLY'||
      p.kind!=='MOD_TRANSITION_RETURN'||!Number.isSafeInteger(p.targetRevision)||p.targetRevision<1||
      !Number.isSafeInteger(p.returnTick)||p.returnTick<0||p.returnTick!==record.gameTime||
      !Number.isSafeInteger(p.returnLocalTick)||p.returnLocalTick<0||p.localTickScope!=='LAST_COMPLETED_SERVER_END_COUNTER'||
      !Number.isSafeInteger(p.eventIndex)||p.eventIndex<1||p.eventIndex>256||
      typeof p.burstId!=='string'||!new RegExp('^burst:'+p.targetRevision+':[0-9]{1,16}$').test(p.burstId)||
      !Number.isSafeInteger(Number(p.burstId.split(':')[2]))||Number(p.burstId.split(':')[2])>p.returnLocalTick||
      p.returnLocalTick-Number(p.burstId.split(':')[2])>=200||
      p.compatibilityStatus!=='MATCHED_DEVELOPMENT_RESOURCE_NOT_RESIDENT_ATTESTATION'||
      typeof p.entityClass!=='string'||!Object.hasOwn(expected.classHashes,p.entityClass)||
      !Number.isSafeInteger(p.observerCostNanos)||p.observerCostNanos<0||
      p.observerCostScope!=='BUILD_AND_FIRST_BYTE_CHECK_EXCLUDES_FINAL_ENCODING_WRITER'||!object(p.data)||!bounded(record)||
      Object.keys(p).some(k=>!['schema','semantics','targetRevision','returnTick','returnLocalTick','localTickScope','eventIndex','burstId','kind','entityClass',
        'descriptor','compatibilityStatus','observerCostNanos','observerCostScope','data'].includes(k)))return false;
  try{return sameDescriptor(descriptor(p.descriptor),expected)&&new TextEncoder().encode(JSON.stringify(p)).length<=32768;}
  catch{return false;}
}
function exactContext(records) {
  const contexts=records.map(r=>{
    if(['debugSessionId','runId','runSnapshotId'].some(k=>typeof r[k]!=='string'||!r[k].length||r[k].length>512)||
        !Number.isSafeInteger(r.processEpoch)||r.processEpoch<1||!Number.isSafeInteger(r.arenaEpoch)||r.arenaEpoch<0||
        r.scope?.kind!=='ENTITY_UUID'||typeof r.scope.entityUuid!=='string'||
        !/^[a-f0-9]{8}(?:-[a-f0-9]{4}){3}-[a-f0-9]{12}$/i.test(r.scope.entityUuid))throw new TypeError('SDK_EXACT_CONTEXT_REQUIRED');
    return JSON.stringify([r.debugSessionId,r.runId,r.runSnapshotId,r.processEpoch,r.arenaEpoch,r.scope.entityUuid,r.payload.targetRevision]);
  });
  if(new Set(contexts).size>1||new Set(records.map(r=>r.observationId)).size!==records.length)throw new Error('SDK_CONTEXT_OR_OBSERVATION_DUPLICATED');
}
function sourceRefs(value,ids) {
  return Array.isArray(value)&&value.length>0&&value.length<=64&&value.every(id=>ids.has(id));
}

/** Explicit trusted retained-evidence adapters. No dynamic discovery, world API or action authority. */
export function createDecisionAdapterRegistry(plugins) {
  if(!Array.isArray(plugins)||plugins.length>32)throw new TypeError('BOUNDED_EXPLICIT_ADAPTER_REGISTRATION_REQUIRED');
  const entries=plugins.map(plugin=>{
    const d=descriptor(plugin.descriptor);
    const methods=['describeCapabilities','captureSnapshot','captureBurst','emitStructuredFacts','emitVisualPrimitives'];
    if(methods.some(k=>typeof plugin[k]!=='function'))throw new TypeError('SDK_METHOD_CONTRACT_REQUIRED');
    return {descriptor:d,...Object.fromEntries(methods.map(k=>[k,plugin[k].bind(plugin)]))};
  });
  if(new Set(entries.map(e=>e.descriptor.id)).size!==entries.length)throw new Error('SDK_DUPLICATE_ADAPTER');
  function capture(observations,burst) {
      if(!Array.isArray(observations)||observations.length>50000)throw new TypeError('SDK_BOUNDED_RETAINED_INPUT_REQUIRED');
      for(const entry of entries) {
        const matched=observations.filter(r=>(burst?validBurstRecord:validRecord)(r,entry.descriptor));
        if(!matched.length)continue;
        exactContext(matched);
        if(burst&&new Set(matched.map(r=>r.payload.burstId+':'+r.payload.eventIndex)).size!==matched.length)throw new Error('SDK_BURST_EVENT_DUPLICATED');
        matched.sort((a,b)=>a.gameTime-b.gameTime||(a.writerSeq??0)-(b.writerSeq??0));
        const retained=freeze(structuredClone(matched.slice(burst?-8:-64))),ids=new Set(retained.map(r=>r.observationId));
        const snapshot=(burst?entry.captureBurst:entry.captureSnapshot)(retained);
        if(!bounded(snapshot))throw new TypeError('SDK_BOUNDED_SNAPSHOT_REQUIRED');
        const immutableSnapshot=freeze(structuredClone(snapshot));
        const capabilities=entry.describeCapabilities(retained,immutableSnapshot);
        if(!object(capabilities)||Object.entries(capabilities).some(([key,c])=>!key.startsWith(entry.descriptor.namespace+':')||
            !NAME.test(key)||!DECISION_OBSERVATION_V1.capabilityStatuses.includes(c.status)||
            (['AVAILABLE','PARTIAL'].includes(c.status)&&!sourceRefs(c.source_observation_ids,ids))))throw new TypeError('SDK_NAMESPACED_CAPABILITY_LINEAGE_REQUIRED');
        const facts=entry.emitStructuredFacts(immutableSnapshot,retained);
        if(!Array.isArray(facts)||facts.length>64||facts.some(f=>!NAME.test(f.key)||!f.key.startsWith(entry.descriptor.namespace+':')||
            !entry.descriptor.supportedEpistemicLevels.includes(f.epistemic_status)||
            !(burst?['DIRECT_OBSERVED','DERIVED_FROM_OBSERVED']:['SAMPLED_OBSERVED','DERIVED_FROM_OBSERVED']).includes(f.epistemic_status)||
            !(burst?['DIRECT_RUNTIME_RELATION','UNKNOWN_CAUSALITY','TEMPORAL_ASSOCIATION']:
              ['UNKNOWN_CAUSALITY','TEMPORAL_ASSOCIATION','DERIVED_SPATIAL_ASSOCIATION']).includes(f.causal_relation)||
            !sourceRefs(f.source_observation_ids,ids)))throw new TypeError('SDK_SNAPSHOT_FACT_NAMESPACE_AND_LINEAGE_REQUIRED');
        const primitives=entry.emitVisualPrimitives(immutableSnapshot,retained);
        if(!Array.isArray(primitives)||primitives.length>64||primitives.some(p=>p.namespace!==entry.descriptor.namespace||
            !['point','segment','label','cell'].includes(p.kind)||p.semantics!=='DERIVED_PRESENTATION_ONLY'||
            !sourceRefs(p.source_observation_ids,ids)))throw new TypeError('SDK_DERIVED_VISUAL_LINEAGE_REQUIRED');
        const output={descriptor:entry.descriptor,capabilities,facts:facts.map(f=>({...f,adapter_namespace:entry.descriptor.namespace})),primitives,
          retainedInputTruncated:matched.length>retained.length};
        if(!bounded(output)||new TextEncoder().encode(JSON.stringify(output)).length>32768)throw new TypeError('SDK_OUTPUT_BYTE_BUDGET');
        return structuredClone(output);
      }
      return null;
  }
  return Object.freeze({
    descriptors:freeze(entries.map(e=>e.descriptor)),
    acceptsSnapshot:record=>entries.some(e=>validRecord(record,e.descriptor)),
    acceptsBurst:record=>entries.some(e=>validBurstRecord(record,e.descriptor)),
    captureSnapshot:observations=>capture(observations,false),
    captureBurst:observations=>capture(observations,true),
  });
}
