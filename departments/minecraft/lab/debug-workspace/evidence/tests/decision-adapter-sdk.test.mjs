import test from 'node:test';
import assert from 'node:assert/strict';
import {createDecisionAdapterRegistry} from '../decision-adapter-sdk.mjs';

const descriptor={sdkVersion:1,id:'example:boss-state',version:'1',namespace:'example',modId:'example',modVersion:'1.2',
  minecraftVersion:'1.20.1',loader:'forge',loaderVersion:'47.2.0',mappedArtifactSha256:'a'.repeat(64),
  classHashes:{'example.Boss':'b'.repeat(64)},instrumentation:'CACHED_REFLECTION',observerEffectRisk:'BOUNDED_SAMPLED_OBSERVER',
  supportedEpistemicLevels:['SAMPLED_OBSERVED']};
const source='obs:sdk:1';
const record={kind:'observation',lane:'AI_DECISION',observationId:source,gameTime:100,
  debugSessionId:'s',runId:'r',runSnapshotId:'snap',processEpoch:1,arenaEpoch:0,
  scope:{kind:'ENTITY_UUID',entityUuid:'00000000-0000-0000-0000-000000000001'},
  source:{side:'SERVER'},epistemicStatus:'OBSERVED',completeness:{complete:true},payload:{
    schema:'kneekura.mod-decision-snapshot/v1',semantics:'SOURCE_SPECIFIC_CACHED_SNAPSHOT_ONLY',
    targetRevision:1,sampleTick:100,entityClass:'example.Boss',descriptor:structuredClone(descriptor),
    compatibilityStatus:'MATCHED_DEVELOPMENT_RESOURCE_NOT_RESIDENT_ATTESTATION',
    data:{phase:'WAIT'}}};
function adapter(overrides={}) {
  return {descriptor,describeCapabilities:()=>({'example:state':{status:'AVAILABLE',source_observation_ids:[source]}}),
    captureSnapshot:records=>records.at(-1).payload.data,
    captureBurst:()=>({status:'NOT_EXPOSED'}),
    emitStructuredFacts:data=>[{key:'example:phase',value:data.phase,epistemic_status:'SAMPLED_OBSERVED',
      causal_relation:'UNKNOWN_CAUSALITY',source_observation_ids:[source]}],
    emitVisualPrimitives:()=>[],...overrides};
}
test('versioned explicit registry keeps provenance, namespaced facts and immutable retained input',()=>{
  const original=structuredClone(record),plugin=adapter();
  const registry=createDecisionAdapterRegistry([plugin]);
  const out=registry.captureSnapshot([record]);
  assert.equal(out.descriptor.id,'example:boss-state');assert.equal(out.facts[0].adapter_namespace,'example');
  assert.equal(out.facts[0].value,'WAIT');assert.deepEqual(record,original);
  plugin.descriptor.modVersion='changed';
  assert.equal(registry.captureSnapshot([record]).descriptor.modVersion,'1.2');
  plugin.descriptor.modVersion='1.2';
});
test('registry rejects same version with different artifact/class/resource compatibility and unknown adapters',()=>{
  const registry=createDecisionAdapterRegistry([adapter()]);
  for(const change of [r=>r.payload.descriptor.mappedArtifactSha256='c'.repeat(64),
    r=>r.payload.descriptor.classHashes['example.Boss']='d'.repeat(64),r=>r.payload.descriptor.loaderVersion='47.3.0',
    r=>r.payload.compatibilityStatus='VERSION_ONLY',r=>r.payload.sampleTick=99,r=>r.payload.descriptor.id='example:unknown']) {
    const value=structuredClone(record);change(value);assert.equal(registry.captureSnapshot([value]),null);
  }
});
test('SDK refuses unnamed extensions, authority metadata, duplicate registrations and absent source lineage',()=>{
  assert.throws(()=>createDecisionAdapterRegistry([adapter(),adapter()]),/DUPLICATE/);
  assert.throws(()=>createDecisionAdapterRegistry([adapter({descriptor:{...descriptor,ownerAuthority:true}})]));
  for(const change of [f=>f.key='vanilla_goal',f=>f.source_observation_ids=['invented'],
    f=>f.causal_relation='DIRECT_RUNTIME_RELATION',f=>f.epistemic_status='DIRECT_OBSERVED']) {
    const plugin=adapter();const base=plugin.emitStructuredFacts;
    plugin.emitStructuredFacts=data=>{const facts=base(data);change(facts[0]);return facts;};
    assert.throws(()=>createDecisionAdapterRegistry([plugin]).captureSnapshot([record]));
  }
});
test('retained capture cannot mutate input or substitute captured scope through a plugin',()=>{
  const plugin=adapter({captureSnapshot:records=>{records[0].payload.data.phase='INVENTED';return records[0].payload.data;}});
  assert.throws(()=>createDecisionAdapterRegistry([plugin]).captureSnapshot([record]),TypeError);
  assert.equal(record.payload.data.phase,'WAIT');
});
