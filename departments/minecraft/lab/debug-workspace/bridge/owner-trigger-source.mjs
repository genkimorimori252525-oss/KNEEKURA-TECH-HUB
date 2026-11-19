/** Opt-in source binding on the existing EvidenceRuntime. No background worker or second evidence store. */
import { open } from 'node:fs/promises';
import path from 'node:path';
import { stableJson, integer } from './json.mjs';
import { readInstalledControl, requestDeclaredCapture } from './owner-action-adapter.mjs';
import { readPreparedOwnerControl } from './owner-prelaunch.mjs';
import { ownerTriggerIdentity } from './owner-trigger-config.mjs';
export { ownerTriggerIdentity, validateOwnerTriggerConfig } from './owner-trigger-config.mjs';
const bindings = new WeakMap();
function same(a,b){return stableJson(a)===stableJson(b);}
function acceptedSource(prepared,row) {
  const p=row.payload;
  if(!p?.identity||typeof p.identity!=='object'||Array.isArray(p.identity))return false;
  const subject=prepared.grant.subjects.find(s=>s.subjectId===p?.subjectId);
  const identity=ownerTriggerIdentity(prepared,p?.identity?.arenaRevision);
  const point=x=>Array.isArray(x)&&x.length===3&&x.every(Number.isFinite);
  const bounds=prepared.grant.bounds,inside=x=>x.every((v,i)=>v>=bounds.min[i]&&v<bounds.max[i]);
  return ['debugSessionId','runId','runSnapshotId','processEpoch'].every(k=>row[k]===identity[k])&&
    row.completeness?.complete===true&&row.epistemicStatus==='OBSERVED'&&row.source?.side==='SERVER'&&
    row.source?.method==='KneekuraDebugOwnerConnection.arena_exit'&&row.lane==='SERVER_ENTITY_STATE'&&
    p?.kind==='owner_trigger_event'&&p.triggerKind==='ARENA_EXIT'&&p.transition==='INSIDE_TO_OUTSIDE'&&
    p.ownerEnvelopeHash===prepared.envelopeHash&&p.triggerConfigHash===prepared.envelope.triggerConfigHash&&
    same(p.identity,identity)&&row.arenaEpoch===identity.arenaEpoch&&subject?.uuid===p.uuid&&row.scope?.kind==='ENTITY_UUID'&&row.scope.entityUuid===p.uuid&&
    point(p.previousPosition)&&point(p.position)&&inside(p.previousPosition)&&!inside(p.position);
}
export async function armOwnerTriggerCapture(runtime,{runDir=runtime.runDir,envelopeHash}) {
  if(runDir!==runtime.runDir||runtime.finalized||runtime.triggerController||bindings.has(runtime))throw new Error('TRIGGER_OWNER_NOT_AVAILABLE');
  const prepared={...await readPreparedOwnerControl({runDir,envelopeHash,requireSnapshot:true}),envelopeHash};
  if(!prepared.triggerCapture)throw new Error('OWNER_TRIGGER_NOT_CONFIGURED');
  const {control,receipt}=await readInstalledControl({runDir,envelopeHash});
  const {captureIndices,...config}=prepared.triggerCapture;
  const identity=ownerTriggerIdentity(prepared,control.arenaRevision);
  for(const key of ['debugSessionId','runId','runSnapshotId','processEpoch'])
    if(runtime[key]!==identity[key])throw new Error('FOREIGN_TRIGGER_RUN');
  // Exclusive for the whole run. Restart/concurrent watchers never re-arm consumed windows or budgets.
  const armedAt=Date.now();
  const accepts=row=>Date.parse(row.observedAt)>=armedAt&&acceptedSource(prepared,row);
  const reservation=await open(path.join(runDir,'control/owner-trigger-watch.json'),'wx',0o600);
  try{await reservation.writeFile(stableJson({schemaVersion:1,ownerEnvelopeHash:envelopeHash,
    triggerConfigHash:prepared.envelope.triggerConfigHash,armedAt:new Date().toISOString(),automaticRetry:false}));await reservation.sync();}
  finally{await reservation.close();}
  const pending=new Set();let index=0;
  const callback=command=>{
    if(index>=captureIndices.length)throw new Error('TRIGGER_CAPTURE_BUDGET_EXHAUSTED');
    const captureIndex=captureIndices[index++];
    const task=(async()=>{
      const raw=runtime.store.observationById.get(command.triggerObservationId),row=raw?JSON.parse(raw):null;
      if(!row||!accepts(row)||!same(command.identity,row.payload.identity))throw new Error('TRIGGER_SOURCE_MISMATCH');
      if(runtime.triggerController.closed||Date.now()>=command.deadline)throw new Error('TRIGGER_OWNER_CLOSED_OR_DEADLINE');
      const trigger={configHash:prepared.envelope.triggerConfigHash,kind:row.payload.triggerKind,
        observationId:row.observationId,windowId:command.triggerCaptureId,triggerAt:Date.parse(row.observedAt),
        offsetMs:command.offsetMs,deadline:command.deadline};
      const result=await requestDeclaredCapture({runDir,envelopeHash,captureIndex,
        trigger,expectedIdentity:command.identity,isClosed:()=>runtime.triggerController.closed||runtime.finalized});
      if(result.status!=='REQUESTED')throw new Error('TRIGGER_CAPTURE_'+result.status);
      return {captureId:result.captureId};
    })();
    pending.add(task);task.then(()=>pending.delete(task),()=>pending.delete(task));return task;
  };
  runtime.armTriggerCapture({...config,identity},callback,accepts);
  bindings.set(runtime,{pending,prepared,deadline:Date.parse(receipt.observedAt)+prepared.grant.timeBudgetMs});
  return {enabled:true,triggerKinds:config.triggerKinds,captureIndices,continuousRecording:false,automaticRetry:false};
}
export async function drainOwnerTriggerDispatches(runtime) {
  const binding=bindings.get(runtime);if(binding)await Promise.allSettled([...binding.pending]);
}
/** Explicit, foreground, finite polling. Ordinary evidence reads never arm this route. */
export async function watchOwnerTriggerCaptures(runtime,options,{pollMs=100}={}) {
  integer(pollMs,50,250);const armed=await armOwnerTriggerCapture(runtime,options),binding=bindings.get(runtime);
  const deadline=binding.deadline;const captures=[];let reason='OWNER_WATCH_DEADLINE';
  try{
    while(Date.now()<deadline){
      const {prepared}=binding;
      try{await readInstalledControl({runDir:runtime.runDir,envelopeHash:prepared.envelopeHash,allowBusyObservation:true});}
      catch{reason='OWNER_NOT_ACTIVE';break;}
      const result=await runtime.refresh();captures.push(...(result.triggerCaptures??[]));
      await drainOwnerTriggerDispatches(runtime);
      if(runtime.triggerController.usedIds.size>=runtime.triggerController.config.maxWindows&&runtime.triggerController.windows.size===0){reason='WINDOWS_FINISHED';break;}
      await new Promise(resolve=>setTimeout(resolve,pollMs));
    }
  }finally{
    runtime.triggerController.close();await drainOwnerTriggerDispatches(runtime);
    if(!runtime.finalized)captures.push(...await runtime.pollTriggerCaptures());
  }
  return {...armed,status:reason,captures,visualVerdict:'NOT_RUN',behaviorVerdict:'INCONCLUSIVE_CAPTURE_PERTURBATION'};
}
