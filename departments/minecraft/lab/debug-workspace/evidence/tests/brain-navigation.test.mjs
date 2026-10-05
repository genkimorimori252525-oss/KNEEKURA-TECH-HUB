import test from 'node:test';
import assert from 'node:assert/strict';
import {normalizeDecisionBurst} from '../target-control.mjs';
import {decisionBurstFromArgs} from '../../decision-burst-cli.mjs';
import {validOriginalDecisionEvent,appendOriginalDecisionEvents} from '../original-decision-events.mjs';

const absent=()=>({present:false});
const memory=()=>({status:'AVAILABLE',registered:true,present:false});
const state=()=>({sinkPath:absent(),brainPath:memory(),navigationPath:absent(),sinkSpeed:0.5,navigationSpeed:0.5});
const base=()=>({sinkClass:'net.minecraft.world.entity.ai.behavior.MoveToTargetSink',instanceIdentity:'component:7:1',instanceIdentityStatus:'AVAILABLE',
  sinkInvocationId:'sink:7:1',parentInvocationStatus:'NOT_CAPTURED',callSite:'START_FROM_BRIDGE',gameTimeArgument:'100',
  dispatchScope:'ORIGINAL_KNOWN_SINK_CONCRETE_CALL_FROM_BRIDGE_OR_RESTART',fieldScope:'BASE_CACHED_FIELDS_AT_DECLARED_CAPTURE_BOUNDARY',
  reasonStatus:'NOT_EXPOSED',arrivalStatus:'NOT_EXPOSED',searchRelationStatus:'NOT_EXPOSED'});
const record=(kind,extra)=>({source:{side:'SERVER'},gameTime:100,observationId:'obs:sink:'+kind,payload:{
  schema:'kneekura.original-decision-event/v1',semantics:'ORIGINAL_INVOCATION_RETURN_ONLY',targetRevision:7,
  burstId:'burst:7:100',eventIndex:1,kind,data:{...base(),...extra},observerCostNanos:1,observerCostScope:'BUILD_AND_FIRST_BYTE_CHECK_EXCLUDES_FINAL_ENCODING_WRITER'}});
const frame=()=>record('BRAIN_PATH_SINK_RETURN',{before:state(),after:state(),preCallObserverCostNanos:0,
  beforeScope:'BEFORE_ORIGINAL_CALL_AFTER_CAPTURE_GATES',afterScope:'AFTER_ORIGINAL_RETURN_AND_CAPTURE_GATES',returnScope:'NORMAL_ORIGINAL_VOID_RETURN_NOT_MOVEMENT_SUCCESS'});
const write=()=>record('BRAIN_PATH_MEMORY_WRITE_RETURN',{brainClass:'Brain',brainIdentity:'component:7:2',brainIdentityStatus:'AVAILABLE',
  requestedPath:absent(),memoryAtReturn:memory(),requestedMatchesCachedMemory:true,writeSite:'START_PATH_WRITE',
  returnScope:'ORIGINAL_VIRTUAL_PATH_MEMORY_WRITE_NORMAL_RETURN_NOT_RETENTION_SUCCESS',referenceScope:'RAW_ARGUMENT_VS_CACHED_MEMORY_VALUE_REFERENCE_NOT_WRITE_SUCCESS'});
const move=()=>record('BRAIN_PATH_NAVIGATION_RETURN',{navigationClass:'CustomNavigation',navigationIdentity:'component:7:3',navigationIdentityStatus:'AVAILABLE',
  result:false,requestedSpeed:0.5,cachedSpeed:0.5,requestedMatchesCachedPath:true,requestedPath:absent(),cachedPath:absent(),brainPathAtReturn:memory(),
  returnScope:'ORIGINAL_VIRTUAL_MOVE_TO_RETURN_AT_SINK_CALL_SITE_NOT_ARRIVAL',referenceScope:'RAW_ARGUMENT_VS_CACHED_PATH_REFERENCE_EQUALITY'});

test('Brain Navigation is explicitly armed without enabling existing generic channels',()=>{
  assert.equal(decisionBurstFromArgs(['--decision-burst']).channels.includes('brain_navigation'),false);
  assert.deepEqual(decisionBurstFromArgs(['--decision-burst','--decision-channels','brain_navigation']).channels,['brain_navigation']);
  assert.throws(()=>normalizeDecisionBurst({...decisionBurstFromArgs(['--decision-burst']),channels:['brain_navigation','brain_navigation']}));
});
test('memory write, final virtual boolean and void return remain separate bounded execution facts',()=>{
  const records=[write(),move(),frame()];assert.ok(records.every(validOriginalDecisionEvent));
  const stages={},capabilities={},timeline=[];appendOriginalDecisionEvents(records,stages,capabilities,timeline);
  assert.equal(stages.EXECUTION.facts.length,3);assert.equal(capabilities.brain_navigation.status,'PARTIAL');
  for(const name of ['CANDIDATE','SELECTION','RESULT'])assert.equal(stages[name],undefined);
  const nested=frame();nested.payload.data.parentInvocationStatus='AVAILABLE';nested.payload.data.parentInvocationId='sink:7:1';nested.payload.data.sinkInvocationId='sink:7:2';nested.payload.data.callSite='START_FROM_TICK';
  assert.equal(validOriginalDecisionEvent(nested),true);
});
test('forged invocation identity, parent, memory presence, source scopes and movement success are rejected',()=>{
  for(const mutate of [d=>d.sinkInvocationId='sink:8:1',d=>d.sinkInvocationId='sink:7:257',d=>d.instanceIdentity='component:7:129',
    d=>d.parentInvocationId='sink:7:1',d=>{d.parentInvocationStatus='AVAILABLE';d.parentInvocationId='sink:7:1';},
    d=>{d.parentInvocationStatus='AVAILABLE';d.parentInvocationId='sink:8:1';},d=>d.gameTimeArgument='9223372036854775808',
    d=>d.callSite='UNKNOWN_CALLER',d=>d.sinkClass='CustomSink',d=>d.returnScope='ARRIVAL_SUCCESS',d=>d.arrivalStatus='AVAILABLE',
    d=>d.after.brainPath.present=true,d=>d.before.sinkSpeedStatus='NOT_EXPOSED',d=>d.result=true]){
    const r=frame();mutate(r.payload.data);assert.equal(validOriginalDecisionEvent(r),false);
  }
  for(const mutate of [d=>d.writeSite='TICK_PATH_RECONCILE',d=>d.requestedMatchesCachedMemory=false,
    d=>d.memoryAtReturn.timeToLive='10',d=>d.requestedMatchesCachedMemoryStatus='NOT_EXPOSED']){
    const r=write();mutate(r.payload.data);assert.equal(validOriginalDecisionEvent(r),false);
  }
  const r=move();r.payload.data.callSite='TICK_FROM_BRIDGE';assert.equal(validOriginalDecisionEvent(r),false);
});
test('custom memory maps and exhausted component identities stay explicit unknowns',()=>{
  const r=write(),d=r.payload.data;delete d.instanceIdentity;d.instanceIdentityStatus='NOT_EXPOSED';delete d.brainIdentity;d.brainIdentityStatus='NOT_EXPOSED';
  d.memoryAtReturn={status:'NOT_EXPOSED',detail:'CUSTOM_MEMORY_MAP'};delete d.requestedMatchesCachedMemory;d.requestedMatchesCachedMemoryStatus='NOT_EXPOSED';
  assert.equal(validOriginalDecisionEvent(r),true);d.memoryAtReturn.path={present:false};assert.equal(validOriginalDecisionEvent(r),false);
});
