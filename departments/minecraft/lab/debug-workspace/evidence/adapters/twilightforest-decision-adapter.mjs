import descriptor from './twilightforest-anchor.json' with {type:'json'};

const integer=Number.isSafeInteger;
const object=v=>v!==null&&typeof v==='object'&&!Array.isArray(v);
const only=(v,keys)=>object(v)&&Object.keys(v).every(k=>keys.includes(k));
const name=v=>typeof v==='string'&&/^[A-Z_]{1,64}$/.test(v);
const uuid=v=>v===null||(typeof v==='string'&&/^[a-f0-9]{8}(?:-[a-f0-9]{4}){3}-[a-f0-9]{12}$/i.test(v));
const KEYS={Hydra:'hydra_heads',SnowQueen:'snow_queen_phase',KnightPhantom:'knight_formation',UrGhast:'ur_ghast_custom_flight'};
function validState(kind,s) {
  if(kind==='Hydra')return only(s,['numHeads','scope','heads'])&&s.numHeads===7&&
    s.scope==='SELECTED_COORDINATOR_STORED_HEAD_CONTAINERS'&&Array.isArray(s.heads)&&s.heads.length===7&&
    new Set(s.heads.map(h=>h.headNum)).size===7&&s.heads.every(h=>only(h,
      ['headNum','prevState','currentState','nextState','nextStateSemantics','ticksNeeded','ticksProgress','targetUuid','headUuid'])&&
      integer(h.headNum)&&h.headNum>=0&&h.headNum<7&&name(h.prevState)&&name(h.currentState)&&
      (h.nextState==null?h.nextStateSemantics==='AUTOMATIC_SENTINEL':name(h.nextState)&&h.nextStateSemantics==='STORED_REQUESTED_STATE')&&
      integer(h.ticksNeeded)&&integer(h.ticksProgress)&&(h.targetUuid===undefined||uuid(h.targetUuid))&&
      (h.headUuid===undefined||uuid(h.headUuid)));
  if(kind==='SnowQueen')return only(s,['phase','beamActive','summonsRemaining','successfulDrops','maxDrops','damageWhileBeaming'])&&
    ['SUMMON','DROP','BEAM'].includes(s.phase)&&typeof s.beamActive==='boolean'&&
    ['summonsRemaining','successfulDrops','maxDrops','damageWhileBeaming'].every(k=>integer(s[k]));
  if(kind==='KnightPhantom')return only(s,['number','ticksProgress','currentFormation','chargePos','chargePosStatus','groupIdentityStatus','leaderStatus'])&&
    integer(s.number)&&integer(s.ticksProgress)&&name(s.currentFormation)&&s.groupIdentityStatus==='NOT_EXPOSED'&&s.leaderStatus==='NOT_EXPOSED'&&
    (s.chargePos===undefined?s.chargePosStatus==='NOT_EXPOSED':only(s.chargePos,['x','y','z'])&&
      ['x','y','z'].every(k=>integer(s.chargePos[k]))&&s.chargePosStatus===undefined);
  if(kind==='UrGhast') {
    const f=s.customFlight;
    return only(s,['inTantrum','damageUntilNextPhase','nextTantrumCry','wanderFactor','customFlight'])&&typeof s.inTantrum==='boolean'&&
      Number.isFinite(s.damageUntilNextPhase)&&integer(s.nextTantrumCry)&&Number.isFinite(s.wanderFactor)&&
      only(f,['controllerClass','courseChangeCooldown','operation','wantedX','wantedY','wantedZ','speedModifier','candidatePopulationStatus','aStarExplanationStatus'])&&
      f.controllerClass==='twilightforest.entity.ai.control.NoClipMoveControl'&&integer(f.courseChangeCooldown)&&
      ['WAIT','MOVE_TO','STRAFE','JUMPING'].includes(f.operation)&&['wantedX','wantedY','wantedZ','speedModifier'].every(k=>Number.isFinite(f[k]))&&
      f.candidatePopulationStatus==='NOT_EXPOSED'&&f.aStarExplanationStatus==='NOT_EXPOSED';
  }
  return false;
}
export const twilightForestDecisionAdapter=Object.freeze({
  descriptor,
  captureSnapshot(records) {
    const record=records.at(-1),d=record.payload.data;
    if(!['AVAILABLE','NOT_EXPOSED'].includes(d.status)||!only(d,['status','bossKind','stateSemantics','state','detail'])||
        (d.status==='AVAILABLE'&&(!Object.hasOwn(KEYS,d.bossKind)||record.payload.entityClass!=='twilightforest.entity.boss.'+d.bossKind||
        d.stateSemantics!=='CACHED_STATE_NOT_ORIGINAL_TRANSITION_OR_REASON'||!validState(d.bossKind,d.state))))throw new TypeError('TF_CACHED_STATE_CONTRACT');
    const snapshot=structuredClone(d);
    if(d.status==='AVAILABLE'&&d.bossKind==='Hydra') {
      // Native Gson omits null fields. Only the explicit sentinel proves automatic next-state semantics;
      // an omitted Entity reference remains unknown rather than becoming an observed null target.
      for(const head of snapshot.state.heads) {
        if(head.nextState===undefined)head.nextState=null;
        if(head.targetUuid===undefined)head.targetUuidStatus='NOT_CAPTURED';
        if(head.headUuid===undefined)head.headUuidStatus='NOT_CAPTURED';
      }
    }
    return {...snapshot,subjectUuid:record.scope.entityUuid,source_observation_ids:[record.observationId]};
  },
  describeCapabilities(records,snapshot) {
    return {'twilightforest:boss_state':{status:snapshot.status,source_observation_ids:snapshot.source_observation_ids,
      detail:'Pinned cached Boss state; no exact transition invocation or causal reason.'},
      'twilightforest:original_transitions':{status:'NOT_EXPOSED',source_observation_ids:[],detail:'Original MOD transition hooks are not registered.'}};
  },
  captureBurst(){return {status:'NOT_EXPOSED',detail:'ORIGINAL_INVOCATION_MOD_BURST_NOT_REGISTERED'};},
  emitStructuredFacts(snapshot) {
    if(snapshot.status!=='AVAILABLE')return [];
    return [{key:'twilightforest:'+KEYS[snapshot.bossKind],value:snapshot.state,epistemic_status:'SAMPLED_OBSERVED',
      causal_relation:'UNKNOWN_CAUSALITY',source_observation_ids:snapshot.source_observation_ids}];
  },
  emitVisualPrimitives(snapshot) {
    if(snapshot.status!=='AVAILABLE')return [];
    const value=snapshot.bossKind==='SnowQueen'?snapshot.state.phase:snapshot.bossKind==='KnightPhantom'?
      snapshot.state.currentFormation:snapshot.bossKind==='UrGhast'?'tantrum='+snapshot.state.inTantrum:'heads='+snapshot.state.numHeads;
    return [{kind:'label',namespace:'twilightforest',subjectUuid:snapshot.subjectUuid,text:snapshot.bossKind+': '+value,
      semantics:'DERIVED_PRESENTATION_ONLY',source_observation_ids:snapshot.source_observation_ids}];
  },
});
