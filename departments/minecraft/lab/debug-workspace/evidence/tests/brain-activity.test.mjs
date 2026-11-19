import test from 'node:test';
import assert from 'node:assert/strict';
import {normalizeDecisionBurst} from '../target-control.mjs';
import {decisionBurstFromArgs} from '../../decision-burst-cli.mjs';
import {validOriginalDecisionEvent,appendOriginalDecisionEvents} from '../original-decision-events.mjs';

const known=key=>({status:'AVAILABLE',key});
const state=()=>({activeActivities:{status:'AVAILABLE',count:2,truncated:false,values:[known('minecraft:core'),known('minecraft:rest')]},
  coreActivities:{status:'AVAILABLE',count:1,truncated:false,values:[known('minecraft:core')]},defaultActivity:known('minecraft:idle'),lastScheduleUpdate:'9223372036854775807'});
const data=()=>({brainClass:'net.minecraft.world.entity.ai.Brain',instanceIdentity:'component:7:1',instanceIdentityStatus:'AVAILABLE',activityInvocationId:'activity:7:1',
  dispatchScope:'UPDATE_ACTIVITY_FROM_SCHEDULE_ORIGINAL_VIRTUAL_CALL',fieldScope:'BASE_BRAIN_CACHED_FIELDS_ONLY',
  behaviorStopStatus:'NOT_EXPOSED',movementOutcomeStatus:'NOT_EXPOSED'});
const record=(kind,extra)=>({source:{side:'SERVER'},observationId:'obs:activity:1',gameTime:12000,
  payload:{schema:'kneekura.original-decision-event/v1',semantics:'ORIGINAL_INVOCATION_RETURN_ONLY',targetRevision:7,
    burstId:'burst:7:100',eventIndex:1,kind,data:{...data(),...extra},observerCostNanos:1,
    observerCostScope:'BUILD_AND_FIRST_BYTE_CHECK_EXCLUDES_FINAL_ENCODING_WRITER'}});
const query=()=>record('BRAIN_ACTIVITY_QUERY_RETURN',{scheduleClass:'Schedule',scheduleInstanceIdentity:'component:7:2',scheduleInstanceIdentityStatus:'AVAILABLE',
  queryTickArgument:-1,storedScheduleMatch:true,returnedActivity:known('minecraft:rest'),stateAtReturn:state(),returnScope:'ORIGINAL_VIRTUAL_SCHEDULE_QUERY_RETURN'});
const update=()=>record('BRAIN_ACTIVITY_UPDATE_RETURN',{dayTimeArgument:'-9223372036854775808',gameTimeArgument:'9223372036854775807',
  before:state(),after:state(),preCallObserverCostNanos:0,returnScope:'NORMAL_VOID_RETURN_NOT_ACTIVITY_SUCCESS'});

test('dedicated activity channel is explicit and does not change default channels',()=>{
  assert.equal(decisionBurstFromArgs(['--decision-burst']).channels.includes('brain_activity'),false);
  assert.deepEqual(decisionBurstFromArgs(['--decision-burst','--decision-channels','brain_activity']).channels,['brain_activity']);
  assert.throws(()=>normalizeDecisionBurst({...decisionBurstFromArgs(['--decision-burst']),channels:['brain_activity','brain_activity']}));
});
test('original activity call links exact decimal arguments and separates execution from outcome',()=>{
  const records=[query(),record('BRAIN_ACTIVITY_REQUIREMENTS_RETURN',{requestedActivity:known('minecraft:rest'),result:false,stateAtReturn:state(),returnScope:'ORIGINAL_REGISTERED_MEMORY_REQUIREMENTS_RETURN'}),
    record('BRAIN_ACTIVITY_SET_RETURN',{requestedActivity:known('minecraft:idle'),stateAtReturn:state(),returnScope:'NORMAL_PRIVATE_SETTER_RETURN_NOT_SWITCH_SUCCESS'}),update()];
  assert.ok(records.every(validOriginalDecisionEvent));
  const stages={},capabilities={},timeline=[];appendOriginalDecisionEvents(records,stages,capabilities,timeline);
  assert.equal(timeline.length,4);assert.equal(stages.EVALUATION.facts.length,2);assert.equal(stages.EXECUTION.facts.length,2);
  for(const name of ['CANDIDATE','SELECTION','RESULT'])assert.equal(stages[name],undefined);
  assert.equal(capabilities.brain_activity.status,'PARTIAL');
});
test('invalid invocation scope, overflow, invented success and malformed cached sets are rejected',()=>{
  for(const mutate of [r=>r.payload.data.activityInvocationId='activity:8:1',r=>r.payload.data.activityInvocationId='activity:7:257',
    r=>r.payload.data.instanceIdentity='component:8:1',r=>r.payload.data.instanceIdentity='component:7:129',
    r=>r.payload.data.dayTimeArgument='9223372036854775808',r=>r.payload.data.gameTimeArgument=12000,
    r=>r.payload.data.dayTimeArgument='01',r=>r.payload.data.result=true,r=>r.payload.data.behaviorStopStatus='AVAILABLE',
    r=>r.payload.data.after.activeActivities.count=3,r=>r.payload.data.after.activeActivities.values.push({status:'AVAILABLE',key:'x',result:true}),
    r=>r.payload.data.after.activeActivities.status='PARTIAL',r=>r.payload.data.returnScope='SWITCH_SUCCESS']){
    const r=update();mutate(r);assert.equal(validOriginalDecisionEvent(r),false);
  }
  const r=query();r.payload.data.queryTickArgument=2147483648;assert.equal(validOriginalDecisionEvent(r),false);
});
test('capped component identity and unsupported cached activity sets stay explicit unknowns',()=>{
  const r=update();delete r.payload.data.instanceIdentity;r.payload.data.instanceIdentityStatus='NOT_EXPOSED';
  r.payload.data.before.coreActivities={status:'NOT_EXPOSED',detail:'CUSTOM_ACTIVITY_SET'};
  r.payload.data.after.defaultActivity={status:'NOT_EXPOSED',detail:'UNREGISTERED_ACTIVITY'};
  assert.equal(validOriginalDecisionEvent(r),true);
});
