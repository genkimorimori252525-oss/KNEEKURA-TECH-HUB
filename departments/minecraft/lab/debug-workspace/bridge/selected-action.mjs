/** Pure selection from sealed intent. Creating this value grants no runtime authority. */
import {hashId,integer,identifier,sha256,stableJson} from './json.mjs';
import {validateVisualExperimentRequest} from '../evidence/visual-request-contract.mjs';

export function actionIdempotencyKey(grant,actionId) {
  for(const key of ['runId','runSnapshotId']) identifier(grant[key]);
  identifier(actionId);integer(grant.processEpoch,1,2147483647);hashId(grant.requestHash);
  return sha256(stableJson({actionId,processEpoch:grant.processEpoch,requestHash:grant.requestHash,
    runId:grant.runId,runSnapshotId:grant.runSnapshotId}));
}
export function selectRetainedAction({request,grant,selectedActionId}) {
  request=validateVisualExperimentRequest(request);
  if(!grant||grant.schemaVersion!==1||grant.experimentId!==request.experiment_id||
      grant.generation!==request.generation||grant.arenaId!==request.arena.arena_id||
      grant.baselineHash!==request.arena.baseline_hash) throw new Error('OWNER_REQUEST_IDENTITY_MISMATCH');
  integer(grant.arenaEpoch,0,Number.MAX_SAFE_INTEGER);integer(grant.expectedArenaRevision,0,Number.MAX_SAFE_INTEGER);
  identifier(grant.debugSessionId);identifier(grant.experimentId);identifier(grant.arenaId);
  const actions=[...request.initial_state,...request.actions],index=actions.findIndex(a=>a.action_id===selectedActionId);
  if(index<0)throw new Error('UNKNOWN_RETAINED_ACTION');
  const selected=actions[index];
  if(!['set_block','teleport_subject','wait_ticks'].includes(selected.operation)||
      !Array.isArray(grant.allowedActions)||!grant.allowedActions.includes(selected.operation))throw new Error('ACTION_BACKEND_UNAVAILABLE');
  const revision=grant.expectedArenaRevision+actions.slice(0,index).filter(a=>a.operation!=='wait_ticks').length;
  integer(revision,0,Number.MAX_SAFE_INTEGER);
  const {action_id,operation,...args}=selected;
  return {priorActionIds:actions.slice(0,index).map(a=>a.action_id),action:{
    schemaVersion:1,debugSessionId:grant.debugSessionId,runId:grant.runId,runSnapshotId:grant.runSnapshotId,
    processEpoch:grant.processEpoch,arenaId:grant.arenaId,arenaEpoch:grant.arenaEpoch,expectedArenaRevision:revision,
    experimentId:grant.experimentId,actionId:action_id,idempotencyKey:actionIdempotencyKey(grant,action_id),
    type:operation,args:structuredClone(args)}};
}
