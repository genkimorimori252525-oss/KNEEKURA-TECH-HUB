/** Selected source opt-in. It cannot enlarge the sealed image budget or choose a callback. */
import { exactKeys, integer, identifier } from './json.mjs';
export function ownerTriggerIdentity(prepared, arenaRevision = prepared.grant.expectedArenaRevision) {
  const g = prepared.grant;
  return { ...Object.fromEntries(['debugSessionId','runId','runSnapshotId','processEpoch'].map(k => [k,g[k]])),
    experimentId:g.experimentId,generation:g.generation,requestHash:g.requestHash,arenaId:g.arenaId,
    arenaEpoch:g.arenaEpoch,arenaRevision,baselineHash:g.baselineHash };
}
export function validateOwnerTriggerConfig(value, grant) {
  exactKeys(value,['enabled','triggerKinds','offsetsMs','toleranceMs','cooldownMs','maxWindows','captureBudget','timeoutMs','captureIndices'],'OWNER_TRIGGER_CONFIG');
  const {captureIndices,...config}=value;
  if(config.enabled!==true||!Array.isArray(config.triggerKinds)||config.triggerKinds.length!==1||
    config.triggerKinds[0]!=='ARENA_EXIT'||!Array.isArray(config.offsetsMs)||config.offsetsMs.length<1||config.offsetsMs.length>21)
    throw new Error('OWNER_TRIGGER_EXPLICIT_SELECTED_SOURCE_REQUIRED');
  config.offsetsMs.forEach((n,i)=>{integer(n,-10000,10000);if(i&&n-config.offsetsMs[i-1]<250)throw new Error('TRIGGER_SAMPLE_RATE');});
  integer(config.toleranceMs,0,250);integer(config.cooldownMs,1000,60000);integer(config.maxWindows,1,8);
  integer(config.captureBudget,1,4);integer(config.timeoutMs,Math.max(1,...config.offsetsMs),Math.min(20000,grant.timeBudgetMs));
  if(config.triggerKinds.some(k=>k!=='ARENA_EXIT')||config.captureBudget<1||config.timeoutMs>grant.timeBudgetMs||
     !Array.isArray(captureIndices)||captureIndices.length!==config.captureBudget||new Set(captureIndices).size!==captureIndices.length)
    throw new Error('OWNER_TRIGGER_SCOPE_OR_BUDGET');
  for(const index of captureIndices)integer(index,0,Math.floor(grant.maxCaptures/4)-1);
  return structuredClone(value);
}

export function validateOwnerTriggerIntent(prepared, captureIndex, trigger, now) {
  const config=prepared.triggerCapture;
  if(!config||!config.captureIndices.includes(captureIndex))throw new Error('OWNER_TRIGGER_SLOT_NOT_RESERVED');
  exactKeys(trigger,['configHash','kind','observationId','windowId','triggerAt','offsetMs','deadline'],'OWNER_TRIGGER_INTENT');
  identifier(trigger.observationId);identifier(trigger.windowId);
  for(const key of ['triggerAt','deadline'])integer(trigger[key],0,Number.MAX_SAFE_INTEGER);
  integer(trigger.offsetMs,0,10000);
  if(trigger.configHash!==prepared.envelope.triggerConfigHash||!config.triggerKinds.includes(trigger.kind)||
    !config.offsetsMs.includes(trigger.offsetMs)||trigger.deadline!==trigger.triggerAt+config.timeoutMs||
    trigger.triggerAt+trigger.offsetMs>now||trigger.deadline-now<100)throw new Error('OWNER_TRIGGER_DEADLINE_OR_SCOPE');
}
