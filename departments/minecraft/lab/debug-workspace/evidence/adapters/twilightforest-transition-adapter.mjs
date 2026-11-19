import base from './twilightforest-anchor.json' with {type:'json'};
import {validTwilightForestCachedState,normalizeTwilightForestCachedState} from './twilightforest-decision-adapter.mjs';
const descriptor={...base,id:'twilightforest:boss-original-return',
  instrumentation:'ORIGINAL_METHOD_RETURN_AND_CACHED_POST_STATE',observerEffectRisk:'BOUNDED_ORIGINAL_CALLBACK_WITH_ONCE_SOURCE_IO',
  supportedEpistemicLevels:['DIRECT_OBSERVED','DERIVED_FROM_OBSERVED']};
const methods={Hydra:['HydraHeadContainer','advanceHeadState'],SnowQueen:['SnowQueen','setCurrentPhase'],
  KnightPhantom:['KnightPhantom','switchToFormation'],UrGhast:['UrGhast','setInTantrum']};
function valid(record) {
  const d=record.payload.data,kind=d.bossKind,method=methods[kind];
  if(!method||record.payload.entityClass!=='twilightforest.entity.boss.'+kind||
      d.methodOwner!=='twilightforest.entity.boss.'+method[0]||d.methodName!==method[1]||
      d.stateChangeStatus!=='NOT_EXPOSED'||d.reasonStatus!=='NOT_EXPOSED'||
      Object.keys(d).some(k=>!['bossKind','methodOwner','methodName','requestedValue','requestedValueStatus','cachedState',
        'headNum','stateChangeStatus','reasonStatus'].includes(k))||!validTwilightForestCachedState(kind,d.cachedState))return false;
  if(kind==='Hydra')return d.requestedValue===undefined&&d.requestedValueStatus==='NOT_APPLICABLE'&&
    Number.isInteger(d.headNum)&&d.headNum>=0&&d.headNum<7;
  return d.headNum===undefined&&d.requestedValueStatus==='AVAILABLE'&&(kind==='SnowQueen'?
    ['SUMMON','DROP','BEAM'].includes(d.requestedValue)&&d.requestedValue===d.cachedState.phase:kind==='KnightPhantom'?
    d.requestedValue===d.cachedState.currentFormation:typeof d.requestedValue==='boolean'&&d.requestedValue===d.cachedState.inTantrum);
}
export const twilightForestTransitionAdapter=Object.freeze({
  descriptor,
  captureSnapshot(){throw new TypeError('ORIGINAL_RETURN_IS_NOT_SNAPSHOT');},
  captureBurst(records) {
    if(records.some(r=>!valid(r)))throw new TypeError('TF_ORIGINAL_RETURN_CONTRACT');
    return {events:records.map(r=>({tick:r.gameTime,burstId:r.payload.burstId,eventIndex:r.payload.eventIndex,
      ...structuredClone(r.payload.data),cachedState:normalizeTwilightForestCachedState(r.payload.data.bossKind,r.payload.data.cachedState),
      source_observation_ids:[r.observationId]}))};
  },
  describeCapabilities(records){return {'twilightforest:original_returns':{status:'PARTIAL',
    source_observation_ids:records.map(r=>r.observationId),detail:'Finite original method-return callbacks; exact change/reason remains unavailable.'}};},
  emitStructuredFacts(capture){return capture.events.map(event=>({key:'twilightforest:original_invocation_return',
    value:event,epistemic_status:'DIRECT_OBSERVED',causal_relation:'DIRECT_RUNTIME_RELATION',source_observation_ids:event.source_observation_ids}));},
  emitVisualPrimitives(){return [];},
});
