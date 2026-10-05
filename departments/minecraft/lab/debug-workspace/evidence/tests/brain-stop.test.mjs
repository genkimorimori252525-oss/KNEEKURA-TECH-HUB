import test from 'node:test';
import assert from 'node:assert/strict';
import {validOriginalDecisionEvent,appendOriginalDecisionEvents} from '../original-decision-events.mjs';

const slot=(present=false)=>({status:'AVAILABLE',registered:true,present});
const absent=()=>({present:false});
const state=()=>({sinkPath:absent(),brainPath:slot(),navigationPath:absent(),sinkSpeed:0.5,navigationSpeed:0.5,walkTargetSlot:slot()});
const base=()=>({sinkClass:'net.minecraft.world.entity.ai.behavior.MoveToTargetSink',instanceIdentity:'component:7:1',instanceIdentityStatus:'AVAILABLE',
  sinkInvocationId:'sink:7:1',parentInvocationStatus:'NOT_CAPTURED',callSite:'STOP_FROM_BRIDGE',gameTimeArgument:'100',
  dispatchScope:'ORIGINAL_KNOWN_SINK_CONCRETE_CALL_FROM_BRIDGE_OR_RESTART',fieldScope:'BASE_CACHED_FIELDS_AT_DECLARED_CAPTURE_BOUNDARY',
  reasonStatus:'NOT_EXPOSED',arrivalStatus:'NOT_EXPOSED',searchRelationStatus:'NOT_EXPOSED'});
const record=(kind,extra)=>({source:{side:'SERVER'},gameTime:100,observationId:'obs:stop:'+kind,payload:{
  schema:'kneekura.original-decision-event/v1',semantics:'ORIGINAL_INVOCATION_RETURN_ONLY',targetRevision:7,
  burstId:'burst:7:100',eventIndex:1,kind,data:{...base(),...extra},observerCostNanos:1,observerCostScope:'BUILD_AND_FIRST_BYTE_CHECK_EXCLUDES_FINAL_ENCODING_WRITER'}});
const frame=()=>record('BRAIN_PATH_SINK_RETURN',{before:state(),after:state(),preCallObserverCostNanos:0,
  beforeScope:'BEFORE_ORIGINAL_CALL_AFTER_CAPTURE_GATES',afterScope:'AFTER_ORIGINAL_RETURN_AND_CAPTURE_GATES',returnScope:'NORMAL_ORIGINAL_VOID_RETURN_NOT_MOVEMENT_SUCCESS'});
const erase=module=>record('BRAIN_PATH_MEMORY_ERASE_RETURN',{brainClass:'CustomBrain',brainIdentity:'component:7:2',brainIdentityStatus:'AVAILABLE',
  memoryModule:module,slotAtReturn:slot(module==='WALK_TARGET'),memoryScope:'BASE_CACHED_PATH_OR_WALK_TARGET_OPTIONAL_SLOT_AFTER_RETURN',
  returnScope:'ORIGINAL_VIRTUAL_ERASE_NORMAL_RETURN_NOT_SLOT_CLEAR_SUCCESS'});
const stop=()=>record('BRAIN_PATH_NAVIGATION_STOP_RETURN',{navigationClass:'CustomNavigation',navigationIdentity:'component:7:3',navigationIdentityStatus:'AVAILABLE',
  cachedPath:absent(),cachedSpeed:0.5,brainPathAtReturn:slot(),returnScope:'ORIGINAL_VIRTUAL_STOP_NORMAL_RETURN_NOT_ARRIVAL_OR_PATH_CLEAR_SUCCESS'});

test('stop, both erases and void return are separate partial execution facts without clear or arrival claims',()=>{
  const records=[stop(),erase('WALK_TARGET'),erase('PATH'),frame()];assert.ok(records.every(validOriginalDecisionEvent));
  const stages={},capabilities={},timeline=[];appendOriginalDecisionEvents(records,stages,capabilities,timeline);
  assert.equal(stages.EXECUTION.facts.length,4);assert.equal(timeline.length,4);assert.equal(capabilities.brain_navigation.status,'PARTIAL');
  for(const s of ['CANDIDATE','SELECTION','RESULT'])assert.equal(stages[s],undefined);
  const kept=frame();kept.payload.data.after.walkTargetSlot.present=true;assert.equal(validOriginalDecisionEvent(kept),true);
});

test('stop consumer rejects invented slot values, successful clear results, wrong caller phases and bad registration',()=>{
  for(const mutate of [d=>d.memoryModule='LOOK_TARGET',d=>d.result=true,d=>d.callSite='START_FROM_BRIDGE',d=>d.returnScope='ERASE_SUCCESS',
    d=>d.slotAtReturn.registered=false,d=>d.slotAtReturn.value={position:[1,2,3]},d=>d.slotAtReturn.timeToLive='5',d=>d.reasonStatus='AVAILABLE']){
    const r=erase('WALK_TARGET');mutate(r.payload.data);assert.equal(validOriginalDecisionEvent(r),false);
  }
  for(const mutate of [d=>d.callSite='START_FROM_TICK',d=>d.result=false,d=>d.cachedSpeedStatus='NOT_EXPOSED',d=>d.returnScope='ARRIVED']){
    const r=stop();mutate(r.payload.data);assert.equal(validOriginalDecisionEvent(r),false);
  }
  const r=frame();delete r.payload.data.before.walkTargetSlot;assert.equal(validOriginalDecisionEvent(r),false);
});

test('unsupported maps, capped component tokens and nonfinite stop speeds remain explicit unknowns',()=>{
  const r=erase('WALK_TARGET');r.payload.data.slotAtReturn={status:'NOT_EXPOSED',detail:'CUSTOM_MEMORY_MAP'};
  delete r.payload.data.instanceIdentity;r.payload.data.instanceIdentityStatus='NOT_EXPOSED';delete r.payload.data.brainIdentity;r.payload.data.brainIdentityStatus='NOT_EXPOSED';
  assert.equal(validOriginalDecisionEvent(r),true);r.payload.data.slotAtReturn.detail='CUSTOM_MEMORY_WRAPPER';assert.equal(validOriginalDecisionEvent(r),false);
  const n=stop();delete n.payload.data.cachedSpeed;n.payload.data.cachedSpeedStatus='NOT_EXPOSED';assert.equal(validOriginalDecisionEvent(n),true);
});

test('stop requires its own cached slot boundary and does not acquire start-only Path write or move facts',()=>{
  const r=frame();r.payload.data.callSite='TICK_FROM_BRIDGE';assert.equal(validOriginalDecisionEvent(r),false);
  const path=erase('PATH');path.payload.data.slotAtReturn.present=true;assert.equal(validOriginalDecisionEvent(path),false);
  const n=stop();n.payload.data.sinkInvocationId='sink:8:1';assert.equal(validOriginalDecisionEvent(n),false);
});
