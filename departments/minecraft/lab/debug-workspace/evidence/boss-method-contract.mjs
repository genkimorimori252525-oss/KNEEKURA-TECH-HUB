import anchor from './adapters/twilightforest-anchor.json' with {type:'json'};

const knight='twilightforest.entity.boss.KnightPhantom';
const goal='twilightforest.entity.ai.goal.PhantomUpdateFormationAndMoveGoal';
const hydra='twilightforest.entity.boss.Hydra';
const head='twilightforest.entity.boss.HydraHeadContainer';
const goalHash='bb1f3d4374a2f5926050c3fd9cf0dff142e47d81daf4d0f801d79b473f1fdaf1';
const object=v=>v!==null&&typeof v==='object'&&!Array.isArray(v);
const keys=(v,names)=>object(v)&&Object.keys(v).length===names.length&&Object.keys(v).every(k=>names.includes(k));
const int32=v=>Number.isSafeInteger(v)&&v>=-2147483648&&v<=2147483647;
const uuid=v=>typeof v==='string'&&/^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i.test(v);
const target=v=>v===null||uuid(v);
const formations=['HOVER','LARGE_CLOCKWISE','SMALL_CLOCKWISE','LARGE_ANTICLOCKWISE','SMALL_ANTICLOCKWISE',
  'CHARGE_PLUSX','CHARGE_MINUSX','CHARGE_PLUSZ','CHARGE_MINUSZ','WAITING_FOR_LEADER','ATTACK_PLAYER_START','ATTACK_PLAYER_ATTACK'];
const states=['IDLE','BITE_BEGINNING','BITE_READY','BITING','BITE_ENDING','FLAME_BEGINNING','FLAMING','FLAME_ENDING',
  'MORTAR_BEGINNING','MORTAR_SHOOTING','MORTAR_ENDING','DYING','DEAD','ATTACK_COOLDOWN','BORN','ROAR_START','ROAR_RAWR'];
const knightState=s=>keys(s,['number','currentFormation','ticksProgress'])&&int32(s.number)&&
  formations.includes(s.currentFormation)&&int32(s.ticksProgress);
const attackType=s=>['BITE_BEGINNING','BITE_READY','BITING'].includes(s)?'BITE':
  ['FLAME_BEGINNING','FLAMING'].includes(s)?'FLAME':['MORTAR_BEGINNING','MORTAR_SHOOTING'].includes(s)?'MORTAR':'NONE';
const common=['bossKind','methodOwner','methodName','sourceUuid','sourceProof'];

function validProof(p,kind){
  if(!keys(p,['mappedArtifactSha256','classHashes','compatibilityStatus'])||p.mappedArtifactSha256!==anchor.mappedArtifactSha256||
    p.compatibilityStatus!=='MATCHED_DEVELOPMENT_RESOURCE_NOT_RESIDENT_ATTESTATION')return false;
  const owners=kind==='KnightPhantom'?[knight,goal]:[hydra,head];
  return keys(p.classHashes,owners)&&owners.every(o=>p.classHashes[o]===(o===goal?goalHash:anchor.classHashes[o]));
}
function base(d,record,kind,owner,method,extra){
  return keys(d,[...common,...extra])&&d.bossKind===kind&&d.methodOwner===owner&&d.methodName===method&&
    uuid(d.sourceUuid)&&d.sourceUuid===record.scope?.entityUuid&&validProof(d.sourceProof,kind);
}

/** Source-bound facts only: no persistent group, skipped-member reason, or executed attack is inferred. */
export function validBossMethodBoundary(kind,d,record){
  if(kind==='MOD_KNIGHT_LEADER_RETURN')return base(d,record,'KnightPhantom',goal,'isThisTheLeader',
    ['leaderResult','originalListClass','originalListCount','maxMembers','truncated','sourceStateAtReturn','membersAtReturn',
      'returnScope','memberStateScope','groupIdentityStatus','sharedTargetStatus'])&&typeof d.leaderResult==='boolean'&&
    d.originalListClass==='java.util.ArrayList'&&int32(d.originalListCount)&&d.originalListCount>=0&&
    Number.isSafeInteger(d.maxMembers)&&d.maxMembers>=1&&d.maxMembers<=16&&
    d.truncated===(d.originalListCount>d.maxMembers)&&knightState(d.sourceStateAtReturn)&&
    Array.isArray(d.membersAtReturn)&&d.membersAtReturn.length===Math.min(d.originalListCount,d.maxMembers)&&
    d.membersAtReturn.every((m,i)=>object(m)&&m.listIndex===i&&
      (m.stateStatus==='AVAILABLE'?keys(m,['listIndex','entityClass','entityUuid','stateStatus','cachedState','targetUuid'])&&
        m.entityClass===knight&&uuid(m.entityUuid)&&knightState(m.cachedState)&&target(m.targetUuid):
        keys(m,['listIndex','entityClass','stateStatus','detail'])&&typeof m.entityClass==='string'&&m.entityClass.length<=512&&
          m.stateStatus==='NOT_EXPOSED'&&m.detail==='UNSUPPORTED_MEMBER_CLASS'))&&
    d.returnScope==='ORIGINAL_LEADER_PREDICATE_RETURN'&&d.memberStateScope==='CACHED_FIELDS_AT_RETURN'&&
    d.groupIdentityStatus==='NOT_EXPOSED'&&d.sharedTargetStatus==='NOT_EXPOSED';
  if(kind==='MOD_KNIGHT_MEMBER_DISPATCH_RETURN')return base(d,record,'KnightPhantom',goal,'broadcastMyFormation',
    ['memberUuid','memberStateAtReturn','targetUuid','dispatchScope','requestedValueStatus','stateChangeStatus','groupIdentityStatus'])&&
    uuid(d.memberUuid)&&knightState(d.memberStateAtReturn)&&target(d.targetUuid)&&
    d.dispatchScope==='ORIGINAL_LOOP_MEMBER_SWITCH_RETURN'&&d.requestedValueStatus==='NOT_CAPTURED'&&
    d.stateChangeStatus==='NOT_EXPOSED'&&d.groupIdentityStatus==='NOT_EXPOSED';
  if(kind==='MOD_HYDRA_TARGET_RETURN')return base(d,record,'Hydra',head,'setTargetEntity',
    ['headNum','requestedTargetUuid','cachedTargetUuid','assignmentScope','attackSuccessStatus'])&&
    Number.isSafeInteger(d.headNum)&&d.headNum>=0&&d.headNum<7&&target(d.requestedTargetUuid)&&target(d.cachedTargetUuid)&&
    d.requestedTargetUuid===d.cachedTargetUuid&&d.assignmentScope==='ORIGINAL_TARGET_SETTER_RETURN'&&d.attackSuccessStatus==='NOT_EXPOSED';
  if(kind==='MOD_HYDRA_STATE_WRITE_CHECKPOINT')return base(d,record,'Hydra',head,'advanceHeadState',
    ['headNum','previousState','currentState','valueChanged','targetUuid','ticksProgress','ticksNeeded','isSecondaryAttacking',
      'activeAttackType','attackTypeScope','assignmentScope','reasonStatus','attackSuccessStatus'])&&
    Number.isSafeInteger(d.headNum)&&d.headNum>=0&&d.headNum<7&&states.includes(d.previousState)&&states.includes(d.currentState)&&
    d.valueChanged===(d.previousState!==d.currentState)&&target(d.targetUuid)&&d.ticksProgress===0&&int32(d.ticksNeeded)&&
    typeof d.isSecondaryAttacking==='boolean'&&d.activeAttackType===attackType(d.currentState)&&
    d.attackTypeScope==='DERIVED_FROM_STORED_STATE'&&d.assignmentScope==='AFTER_ORIGINAL_CONDITIONAL_CURRENT_STATE_WRITE'&&
    d.reasonStatus==='NOT_EXPOSED'&&d.attackSuccessStatus==='NOT_EXPOSED';
  return false;
}
