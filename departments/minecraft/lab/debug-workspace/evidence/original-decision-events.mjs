import twilightForestAnchor from './adapters/twilightforest-anchor.json' with {type:'json'};
import {exactObjectKeys,validPathReferenceFact,validCachedPathFact,consistentRawPathMatch} from './cached-path-contract.mjs';

import {BRAIN_COMPUTE_KINDS,validBrainCompute} from './brain-compute-contract.mjs';
import {BRAIN_START_KINDS,validBrainStart} from './brain-start-contract.mjs';
import {validBrainMemoryRequirement} from './brain-memory-check-contract.mjs';

const KINDS = Object.freeze({
  BRAIN_PATH_MEMORY_REQUIREMENT_RETURN: ['EVALUATION','brain_navigation'],
  BRAIN_PATH_START_CONDITION_RETURN: ['EVALUATION','brain_navigation'],
  BRAIN_PATH_START_DISPATCH_RETURN: ['EXECUTION','brain_navigation'],
  BRAIN_PATH_TRY_START_RETURN: ['EVALUATION','brain_navigation'],
  BRAIN_PATH_COMPUTE_CONDITION_RETURN: ['EVALUATION','brain_navigation'],
  BRAIN_PATH_COMPUTE_RETURN: ['EVALUATION','brain_navigation'],
  BRAIN_PATH_CREATE_RETURN: ['EVALUATION','brain_navigation'],
  BRAIN_PATH_COMPUTE_PATH_WRITE_CHECKPOINT: ['EXECUTION','brain_navigation'],
  BRAIN_PATH_FINDER_RETURN: ['EVALUATION','brain_navigation'],
  MOD_COORDINATION_RETURN: ['EXECUTION','mod_coordination'],
  GOAL_ELIGIBILITY_RETURN: ['EVALUATION','goal_eligibility'],
  GOAL_CONTINUATION_RETURN: ['EVALUATION','goal_eligibility'],
  GOAL_START_RETURN: ['EXECUTION','goal_lifecycle'],
  GOAL_STOP_RETURN: ['EXECUTION','goal_lifecycle'],
  BRAIN_TICK_RETURN: ['EXECUTION','brain_execution'],
  BRAIN_ACTIVITY_QUERY_RETURN: ['EVALUATION','brain_activity'],
  BRAIN_ACTIVITY_REQUIREMENTS_RETURN: ['EVALUATION','brain_activity'],
  BRAIN_ACTIVITY_SET_RETURN: ['EXECUTION','brain_activity'],
  BRAIN_ACTIVITY_UPDATE_RETURN: ['EXECUTION','brain_activity'],
  NAVIGATION_MOVE_TO_RETURN: ['EXECUTION','navigation_move_to'],
  BRAIN_PATH_MEMORY_WRITE_RETURN: ['EXECUTION','brain_navigation'],
  BRAIN_PATH_NAVIGATION_RETURN: ['EXECUTION','brain_navigation'],
  BRAIN_PATH_SINK_RETURN: ['EXECUTION','brain_navigation'],
  BRAIN_PATH_NAVIGATION_STOP_RETURN: ['EXECUTION','brain_navigation'],
  BRAIN_PATH_MEMORY_ERASE_RETURN: ['EXECUTION','brain_navigation'],
  BRAIN_PATH_CONDITION_RETURN: ['EVALUATION','brain_navigation'],
  BRAIN_PATH_DISPATCH_RETURN: ['EXECUTION','brain_navigation'],
  BEHAVIOR_TRY_START_RETURN: ['EVALUATION','behavior_execution'],
  BEHAVIOR_TICK_OR_STOP_RETURN: ['EXECUTION','behavior_execution'],
  BEHAVIOR_STOP_RETURN: ['EXECUTION','behavior_execution'],
  SENSOR_SCAN_RETURN: ['INPUT','sensor_execution'],
  CONTROL_TICK_RETURN: ['EXECUTION','movement_control'],
  CONTROL_TELEPORT_RETURN: ['RESULT','teleport_result'],
  CONTROL_GHAST_REACH_RETURN: ['EVALUATION','custom_flight_reach'],
  CONTROL_PROJECTILE_SPAWN_RETURN: ['RESULT','related_projectile_spawn'],
  CONTROL_PROJECTILE_TICK_RETURN: ['EXECUTION','related_projectile_motion'],
  CONTROL_PROJECTILE_HIT_RETURN: ['RESULT','related_projectile_hit'],
  CONTROL_PROJECTILE_HURT_RETURN: ['RESULT','related_projectile_hurt'],
  BASE_MALUS_RETURN: ['EVALUATION','base_path_malus'],
  EFFECTIVE_MALUS_RETURN: ['EVALUATION','effective_malus'],
  PATH_SEARCH_STATE: ['EVALUATION','path_search_frontier'],
  PATH_SEARCH_RESULT: ['RESULT','path_search_result'],
  PATH_NEIGHBORS_RETURN: ['EVALUATION','path_search_neighbors'],
  PATH_HEAP_OPERATION_RETURN: ['EVALUATION','path_heap_operations'],
  PATH_NODE_CLOSED_CHECKPOINT: ['EVALUATION','path_closed_nodes'],
  PATH_NODE_G_WRITE_CHECKPOINT: ['EVALUATION','path_g_writes'],
  PATH_EDGE_DISTANCE_RETURN: ['EVALUATION','path_edge_distances'],
  PATH_RETURNED_NODES: ['RESULT','returned_path_nodes'],
});
const text = value => typeof value === 'string' && value.length > 0 && value.length <= 512;
const integer = value => Number.isSafeInteger(value);
const object = value => value !== null && typeof value === 'object' && !Array.isArray(value);
const uuid = value => typeof value==='string' && /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i.test(value);
const vector = value => object(value)&&['x','y','z'].every(k=>Number.isFinite(value[k]));
function bounded(value, depth=0, budget={count:0}) {
  if (++budget.count > 8192 || depth > 12) return false;
  if (typeof value === 'string') return value.length <= 512;
  if (typeof value === 'number') return Number.isFinite(value);
  if (value === null || typeof value === 'boolean') return true;
  if (Array.isArray(value)) return value.length <= 64 && value.every(v=>bounded(v,depth+1,budget));
  if (!object(value)) return false;
  const entries=Object.entries(value);
  return entries.length <= 32 && entries.every(([k,v])=>k.length <= 128 && bounded(v,depth+1,budget));
}
function numberOrUnknown(data,key) {
  return Number.isFinite(data[key]) || (data[key] === undefined && data[key+'Status'] === 'NOT_EXPOSED');
}
function validInstanceIdentity(data,requiredStatus=false) {
  const status=data.instanceIdentityStatus;
  if(text(data.instanceIdentity))return status==='AVAILABLE'||(!requiredStatus&&status===undefined);
  // The real writer's Gson omits JsonNull fields. Missing identity remains unknown, never an ID.
  return data.instanceIdentity==null&&(status==='NOT_EXPOSED'||(!requiredStatus&&status===undefined));
}
export function originalDecisionData(record) {
  const data=structuredClone(record.payload.data),kind=record.payload.kind;
  if(kind.startsWith('GOAL_')||kind.startsWith('BRAIN_')||kind.startsWith('BEHAVIOR_')||kind==='SENSOR_SCAN_RETURN') {
    data.instanceIdentity??=null;
    data.instanceIdentityStatus=data.instanceIdentity===null?'NOT_EXPOSED':'AVAILABLE';
  }
  return data;
}
function validFrontier(section) {
  if (!object(section)) return false;
  if (section.status === 'NOT_EXPOSED') return section.detail === 'CUSTOM_NODE_EVALUATOR';
  if (!['AVAILABLE','PARTIAL'].includes(section.status)) return false;
  const d=section.data;
  return object(d) && Array.isArray(d.nodes) && d.nodes.length <= 64 && integer(d.cacheNodeCount) &&
    d.cacheNodeCount >= d.nodes.length && typeof d.truncated === 'boolean' &&
    d.truncated === (d.cacheNodeCount > d.nodes.length) &&
    section.status === (d.truncated ? 'PARTIAL' : 'AVAILABLE') &&
    d.phase === 'OUTER_BEFORE_DONE_AFTER_INNER_RETURN' &&
    d.neighborEvaluationTraceStatus === 'NOT_EXPOSED' && d.rejectionReasonStatus === 'NOT_EXPOSED' &&
    d.nodes.every(n=>object(n) && ['x','y','z'].every(k=>integer(n[k])) && text(n.pathType) &&
      ['g','h','f','costMalus','walkedDistance'].every(k=>numberOrUnknown(n,k)) &&
      typeof n.openAtReturn === 'boolean' && typeof n.closedAtReturn === 'boolean' &&
      n.cacheRole === (n.closedAtReturn ? 'CLOSED_AT_RETURN' : n.openAtReturn ? 'OPEN_AT_RETURN' : 'OTHER_CACHED') &&
      (n.parentX === undefined ? n.parentY === undefined && n.parentZ === undefined :
        ['parentX','parentY','parentZ'].every(k=>integer(n[k]))));
}
function validKnightCoordination(d,record) {
  const knight='twilightforest.entity.boss.KnightPhantom';
  const goal='twilightforest.entity.ai.goal.PhantomUpdateFormationAndMoveGoal';
  const formations=['HOVER','LARGE_CLOCKWISE','SMALL_CLOCKWISE','LARGE_ANTICLOCKWISE','SMALL_ANTICLOCKWISE',
    'CHARGE_PLUSX','CHARGE_MINUSX','CHARGE_PLUSZ','CHARGE_MINUSZ','WAITING_FOR_LEADER','ATTACK_PLAYER_START','ATTACK_PLAYER_ATTACK'];
  const int32=v=>integer(v)&&v>=-2147483648&&v<=2147483647;
  const state=s=>object(s)&&Object.keys(s).length===3&&int32(s.number)&&int32(s.ticksProgress)&&formations.includes(s.currentFormation);
  const proof=d.sourceProof;
  const keys=['bossKind','methodOwner','methodName','sourceUuid','sourceStateAtReturn','sourceProof','originalListClass',
    'originalListCount','maxMembers','truncated','membersAtReturn','dispatchScope','memberStateScope','affectedMembersStatus',
    'leaderDecisionStatus','groupIdentityStatus'];
  return Object.keys(d).length===keys.length&&Object.keys(d).every(k=>keys.includes(k))&&
    d.bossKind==='KnightPhantom'&&d.methodOwner===goal&&d.methodName==='broadcastMyFormation'&&
    uuid(d.sourceUuid)&&d.sourceUuid===record.scope?.entityUuid&&state(d.sourceStateAtReturn)&&
    object(proof)&&Object.keys(proof).length===4&&proof.mappedArtifactSha256===twilightForestAnchor.mappedArtifactSha256&&
    proof.goalClassSha256==='bb1f3d4374a2f5926050c3fd9cf0dff142e47d81daf4d0f801d79b473f1fdaf1'&&
    proof.knightClassSha256===twilightForestAnchor.classHashes[knight]&&
    proof.compatibilityStatus==='MATCHED_DEVELOPMENT_RESOURCE_NOT_RESIDENT_ATTESTATION'&&
    d.originalListClass==='java.util.ArrayList'&&int32(d.originalListCount)&&d.originalListCount>=0&&
    integer(d.maxMembers)&&d.maxMembers>=1&&d.maxMembers<=16&&
    Array.isArray(d.membersAtReturn)&&d.membersAtReturn.length===Math.min(d.originalListCount,d.maxMembers)&&
    d.truncated===(d.originalListCount>d.maxMembers)&&
    d.membersAtReturn.every((m,i)=>object(m)&&m.listIndex===i&&text(m.entityClass)&&
      (m.stateStatus==='AVAILABLE'?Object.keys(m).length===5&&m.entityClass===knight&&uuid(m.entityUuid)&&state(m.cachedState):
        Object.keys(m).length===4&&m.stateStatus==='NOT_EXPOSED'&&m.detail==='UNSUPPORTED_MEMBER_CLASS'&&
        m.entityUuid===undefined&&m.cachedState===undefined))&&
    d.dispatchScope==='ORIGINAL_PASSED_LIST_AFTER_BROADCAST'&&d.memberStateScope==='CACHED_FIELDS_AT_RETURN'&&
    ['affectedMembersStatus','leaderDecisionStatus','groupIdentityStatus'].every(k=>d[k]==='NOT_EXPOSED');
}
function validReturnedNode(section,checkpoint=false) {
  if(!object(section))return false;
  if(section.status==='NOT_EXPOSED')return Object.keys(section).length===2&&section.detail==='NULL_NODE';
  const n=section.data,floats=['g','h','f','costMalus','walkedDistance'];
  const open=checkpoint?'openAtCheckpoint':'openAtReturn',closed=checkpoint?'closedAtCheckpoint':'closedAtReturn';
  return section.status==='AVAILABLE'&&Object.keys(section).length===2&&object(n)&&text(n.className)&&
    ['x','y','z'].every(k=>integer(n[k]))&&
    (text(n.pathType)||(n.pathType===undefined&&n.pathTypeStatus==='NOT_EXPOSED'))&&
    floats.every(k=>numberOrUnknown(n,k))&&typeof n[open]==='boolean'&&typeof n[closed]==='boolean'&&
    Object.keys(n).every(k=>['className','x','y','z','pathType','pathTypeStatus',open,closed,
      ...floats,...floats.map(f=>f+'Status')].includes(k));
}
function validNeighborReturn(d) {
  const keys=['searchId','evaluatorClass','currentNode','returnedCount','returnedArrayLength','maxNodes','neighbors','truncated',
    'phase','dispatchScope','subjectRelationScope','fieldScope','neighborPopulationStatus','rejectionReasonStatus'];
  return Object.keys(d).length===keys.length&&Object.keys(d).every(k=>keys.includes(k))&&text(d.searchId)&&text(d.evaluatorClass)&&
    validReturnedNode(d.currentNode)&&integer(d.returnedCount)&&d.returnedCount>=0&&integer(d.returnedArrayLength)&&
    d.returnedArrayLength>=d.returnedCount&&d.returnedArrayLength<=2147483647&&
    integer(d.maxNodes)&&d.maxNodes>=1&&d.maxNodes<=64&&Array.isArray(d.neighbors)&&
    d.neighbors.length===Math.min(d.returnedCount,d.maxNodes)&&d.truncated===(d.returnedCount>d.maxNodes)&&
    d.neighbors.every((n,i)=>object(n)&&Object.keys(n).length===2&&n.slot===i&&validReturnedNode(n.node))&&
    d.phase==='AFTER_ORIGINAL_GET_NEIGHBORS_BEFORE_RELAXATION'&&d.dispatchScope==='ORIGINAL_VIRTUAL_GET_NEIGHBORS_RETURN'&&
    d.subjectRelationScope==='SELECTED_OUTER_FIND_PATH_INVOCATION'&&d.fieldScope==='BASE_NODE_FIELDS_BEFORE_RELAXATION'&&
    d.neighborPopulationStatus==='NOT_EXPOSED'&&d.rejectionReasonStatus==='NOT_EXPOSED';
}
function validHeapReturn(d,record) {
  const insert=['START_INSERT','RELAXATION_INSERT'].includes(d.operation),change=d.operation==='CHANGE_COST';
  if(!insert&&!change&&d.operation!=='POP')return false;
  const keys=['searchId','heapClass','operation','phase','nodeRole','node','nodeIdentity','maxNodes',
    'dispatchScope','subjectRelationScope','neighborPopulationStatus','rejectionReasonStatus','finalPathCostStatus',
    ...(insert?['argumentMatchesReturned']:[]),...(change?[Number.isFinite(d.requestedCost)?'requestedCost':'requestedCostStatus']:[])];
  if(Object.keys(d).length!==keys.length||Object.keys(d).some(k=>!keys.includes(k))||!text(d.searchId)||
    !new RegExp('^search:'+record.payload.targetRevision+':[1-9][0-9]*$').test(d.searchId)||!text(d.heapClass)||
    !integer(d.maxNodes)||d.maxNodes<1||d.maxNodes>64||!validReturnedNode(d.node)||!object(d.nodeIdentity))return false;
  if(!validNodeIdentity(d))return false;
  return d.phase===(insert?'AFTER_ORIGINAL_INSERT':change?'AFTER_ORIGINAL_CHANGE_COST':'AFTER_ORIGINAL_POP_BEFORE_CALLER_CLOSE')&&
    d.nodeRole===(change?'PASSED_NODE_AFTER_ORIGINAL_CALL':'ORIGINAL_RETURNED_NODE')&&
    (!insert||typeof d.argumentMatchesReturned==='boolean')&&(!change||numberOrUnknown(d,'requestedCost'))&&
    d.dispatchScope==='ORIGINAL_PATHFINDER_INNER_HEAP_CALL_RETURN'&&d.subjectRelationScope==='SELECTED_OUTER_FIND_PATH_INVOCATION'&&
    ['neighborPopulationStatus','rejectionReasonStatus','finalPathCostStatus'].every(k=>d[k]==='NOT_EXPOSED');
}
function validNodeIdentity(d) {
  return validReferenceIdentity(d.nodeIdentity,d.node.status==='AVAILABLE',d.searchId,d.maxNodes);
}
function validReferenceIdentity(identity,present,searchId,maxNodes) {
  if(!object(identity))return false;
  if(identity.status==='AVAILABLE') {
    if(!present||Object.keys(identity).length!==2||!text(identity.id)||!identity.id.startsWith(searchId+':node:'))return false;
    const suffix=identity.id.slice((searchId+':node:').length);
    if(!/^[1-9][0-9]*$/.test(suffix)||!integer(Number(suffix))||Number(suffix)>maxNodes)return false;
  }else if(identity.status!=='NOT_EXPOSED'||Object.keys(identity).length!==2||
      identity.detail!==(present?'NODE_IDENTITY_LIMIT':'NULL_NODE'))return false;
  return true;
}
function validReturnedPath(d,record) {
  const keys=['searchId','resultPresent',...(d.resultPresent?['resultClass']:[]),'maxNodes','dimension','pathNodes','phase',
    'dispatchScope','fieldScope','navigationAdoptionStatus','finalEffectiveCostStatus'];
  if(Object.keys(d).length!==keys.length||Object.keys(d).some(k=>!keys.includes(k))||!text(d.searchId)||
    !new RegExp('^search:'+record.payload.targetRevision+':[1-9][0-9]*$').test(d.searchId)||typeof d.resultPresent!=='boolean'||
    (d.resultPresent&&!text(d.resultClass))||!integer(d.maxNodes)||d.maxNodes<1||d.maxNodes>64||!text(d.dimension)||
    d.phase!=='AFTER_ORIGINAL_OUTER_FIND_PATH_RETURN'||d.dispatchScope!=='SELECTED_OUTER_FIND_PATH_RETURN'||
    d.fieldScope!=='BASE_PATH_AND_NODE_CACHED_FIELDS_AT_RETURN'||d.navigationAdoptionStatus!=='NOT_EXPOSED'||
    d.finalEffectiveCostStatus!=='NOT_EXPOSED'||!object(d.pathNodes)||Object.keys(d.pathNodes).length!==2)return false;
  const section=d.pathNodes;
  if(section.status==='NOT_EXPOSED')return section.detail===(!d.resultPresent?'NULL_PATH':
    d.resultClass==='net.minecraft.world.level.pathfinder.Path'?'CUSTOM_NODE_LIST':'CUSTOM_PATH_CLASS');
  if(!d.resultPresent||d.resultClass!=='net.minecraft.world.level.pathfinder.Path'||!['AVAILABLE','PARTIAL'].includes(section.status))return false;
  const s=section.data,numeric=Number.isFinite(s?.distanceToTarget),fields=['listClass','nodeCount','retainedNodeCount','truncated',
    'nodes','terminalNode','target','canReach','nextNodeIndex',numeric?'distanceToTarget':'distanceToTargetStatus','distanceToTargetScope'];
  if(!object(s)||Object.keys(s).length!==fields.length||Object.keys(s).some(k=>!fields.includes(k))||s.listClass!=='java.util.ArrayList'||
    !integer(s.nodeCount)||s.nodeCount<0||s.nodeCount>2147483647||!Array.isArray(s.nodes)||s.nodes.length!==Math.min(s.nodeCount,d.maxNodes)||
    s.retainedNodeCount!==s.nodes.length||s.truncated!==(s.nodeCount>s.nodes.length)||section.status!==(s.truncated?'PARTIAL':'AVAILABLE')||
    typeof s.canReach!=='boolean'||!integer(s.nextNodeIndex)||s.nextNodeIndex< -2147483648||s.nextNodeIndex>2147483647||
    !numberOrUnknown(s,'distanceToTarget')||s.distanceToTargetScope!=='PATH_CONSTRUCTOR_CACHED_VALUE')return false;
  const slot=(entry,index)=>object(entry)&&Object.keys(entry).length===5&&
    Object.keys(entry).every(k=>['index','node','nodeIdentity','predecessorPresent','predecessorIdentity'].includes(k))&&entry.index===index&&
    validReturnedNode(entry.node)&&validReferenceIdentity(entry.nodeIdentity,entry.node.status==='AVAILABLE',d.searchId,d.maxNodes)&&
    typeof entry.predecessorPresent==='boolean'&&(entry.node.status==='AVAILABLE'||!entry.predecessorPresent)&&
    validReferenceIdentity(entry.predecessorIdentity,entry.predecessorPresent,d.searchId,d.maxNodes);
  if(!s.nodes.every((n,i)=>slot(n,i))||!object(s.terminalNode)||Object.keys(s.terminalNode).length!==2)return false;
  if(s.nodeCount===0) {
    if(s.terminalNode.status!=='NOT_EXPOSED'||s.terminalNode.detail!=='EMPTY_PATH')return false;
  }else if(s.terminalNode.status!=='AVAILABLE'||!slot(s.terminalNode.data,s.nodeCount-1))return false;
  if(s.nodeCount>0&&!s.truncated) {
    // The producer copies the already captured last prefix slot, without another read.
    const same=(a,b)=>Object.keys(a).length===Object.keys(b).length&&Object.keys(a).every(k=>
      object(a[k])?object(b[k])&&same(a[k],b[k]):a[k]===b[k]);
    if(!same(s.nodes.at(-1),s.terminalNode.data))return false;
  }
  const target=s.target;
  return object(target)&&Object.keys(target).length===2&&(target.status==='NOT_EXPOSED'?target.detail==='NULL_TARGET':
    target.status==='AVAILABLE'&&object(target.data)&&Object.keys(target.data).length===3&&['x','y','z'].every(k=>integer(target.data[k])));
}
function validClosedCheckpoint(d,record) {
  const keys=['searchId','priorPopEventIndex','nodeRole','node','nodeIdentity','maxNodes','phase','dispatchScope',
    'subjectRelationScope','referenceScope','neighborPopulationStatus','rejectionReasonStatus','finalPathCostStatus'];
  return Object.keys(d).length===keys.length&&Object.keys(d).every(k=>keys.includes(k))&&text(d.searchId)&&
    new RegExp('^search:'+record.payload.targetRevision+':[1-9][0-9]*$').test(d.searchId)&&
    integer(d.maxNodes)&&d.maxNodes>=1&&d.maxNodes<=64&&d.node?.status==='AVAILABLE'&&validReturnedNode(d.node,true)&&
    validNodeIdentity(d)&&integer(d.priorPopEventIndex)&&d.priorPopEventIndex>=1&&d.priorPopEventIndex<record.payload.eventIndex&&
    d.nodeRole==='PRECEDING_ORIGINAL_POP_RETURN_REFERENCE'&&d.phase==='AFTER_ORIGINAL_CALLER_CLOSED_FIELD_WRITE'&&
    d.dispatchScope==='ORIGINAL_PATHFINDER_INNER_CLOSED_FIELD_WRITE'&&d.subjectRelationScope==='SELECTED_OUTER_FIND_PATH_INVOCATION'&&
    d.referenceScope==='RETAINED_ORIGINAL_POP_RETURN_REFERENCE'&&
    ['neighborPopulationStatus','rejectionReasonStatus','finalPathCostStatus'].every(k=>d[k]==='NOT_EXPOSED');
}
function validGWriteCheckpoint(d,record) {
  const numeric=Number.isFinite(d.writtenG),keys=['searchId','maxNodes',numeric?'writtenG':'writtenGStatus','writtenGScope',
    'nodeRole','node','nodeIdentity','predecessorPresent','predecessorIdentity','phase','dispatchScope','subjectRelationScope','fieldScope',
    'comparisonOperandsStatus','neighborPopulationStatus','rejectionReasonStatus','finalPathCostStatus','navigationAdoptionStatus'];
  if(Object.keys(d).length!==keys.length||Object.keys(d).some(k=>!keys.includes(k))||!text(d.searchId)||
    !new RegExp('^search:'+record.payload.targetRevision+':[1-9][0-9]*$').test(d.searchId)||!integer(d.maxNodes)||d.maxNodes<1||d.maxNodes>64||
    !numberOrUnknown(d,'writtenG')||d.writtenGScope!=='ORIGINAL_PUTFIELD_ARGUMENT'||d.node?.status!=='AVAILABLE'||
    !validReturnedNode(d.node,true)||!validNodeIdentity(d)||typeof d.predecessorPresent!=='boolean'||
    !validReferenceIdentity(d.predecessorIdentity,d.predecessorPresent,d.searchId,d.maxNodes))return false;
  if(Number.isFinite(d.node.data.g)&&d.node.data.gStatus!==undefined)return false;
  return d.nodeRole==='ORIGINAL_FIELD_WRITE_RECEIVER'&&d.phase==='AFTER_ORIGINAL_ACCEPTED_G_FIELD_WRITE_BEFORE_HEURISTIC_UPDATE'&&
    d.dispatchScope==='ORIGINAL_PATHFINDER_INNER_ACCEPTED_G_FIELD_WRITE'&&d.subjectRelationScope==='SELECTED_OUTER_FIND_PATH_INVOCATION'&&
    d.fieldScope==='BASE_NODE_FIELDS_AFTER_WRITE_AND_CAPTURE_GATES'&&
    ['comparisonOperandsStatus','neighborPopulationStatus','rejectionReasonStatus','finalPathCostStatus','navigationAdoptionStatus'].every(k=>d[k]==='NOT_EXPOSED');
}
function validEdgeDistance(d,record) {
  const keys=['searchId','maxNodes','receiverClass','receiverScope',Number.isFinite(d.returnedDistance)?'returnedDistance':'returnedDistanceStatus',
    'returnedDistanceScope','fromNode','fromIdentity','toNode','toIdentity','phase','dispatchScope','subjectRelationScope','fieldScope',
    'comparisonOperandsStatus','neighborPopulationStatus','rejectionReasonStatus','finalPathCostStatus','navigationAdoptionStatus'];
  if(Object.keys(d).length!==keys.length||Object.keys(d).some(k=>!keys.includes(k))||!text(d.searchId)||
    !new RegExp('^search:'+record.payload.targetRevision+':[1-9][0-9]*$').test(d.searchId)||!integer(d.maxNodes)||d.maxNodes<1||d.maxNodes>64||
    !text(d.receiverClass)||!numberOrUnknown(d,'returnedDistance'))return false;
  for(const [section,identity] of [[d.fromNode,d.fromIdentity],[d.toNode,d.toIdentity]]) {
    if(!validReturnedNode(section)||!validReferenceIdentity(identity,section.status==='AVAILABLE',d.searchId,d.maxNodes))return false;
    if(section.status==='AVAILABLE'&&['g','h','f','costMalus','walkedDistance'].some(k=>Number.isFinite(section.data[k])&&section.data[k+'Status']!==undefined))return false;
  }
  return d.receiverScope==='ORIGINAL_CALLER_THIS'&&d.returnedDistanceScope==='ORIGINAL_VIRTUAL_CALL_RETURN'&&
    d.phase==='AFTER_ORIGINAL_EDGE_DISTANCE_BEFORE_WALKED_DISTANCE_WRITE'&&d.dispatchScope==='ORIGINAL_PATHFINDER_INNER_PROTECTED_VIRTUAL_DISTANCE_RETURN'&&
    d.subjectRelationScope==='SELECTED_OUTER_FIND_PATH_INVOCATION'&&d.fieldScope==='BASE_NODE_FIELDS_AFTER_ORIGINAL_RETURN_AND_CAPTURE_GATES'&&
    ['comparisonOperandsStatus','neighborPopulationStatus','rejectionReasonStatus','finalPathCostStatus','navigationAdoptionStatus'].every(k=>d[k]==='NOT_EXPOSED');
}
function validActivityValue(value) {
  return object(value)&&Object.keys(value).length===2&&(value.status==='AVAILABLE'?text(value.key):
    value.status==='NOT_EXPOSED'&&['NULL_ACTIVITY','CUSTOM_ACTIVITY_CLASS','UNREGISTERED_ACTIVITY'].includes(value.detail));
}
function validActivitySet(value) {
  if(!object(value))return false;
  if(value.status==='NOT_EXPOSED')return Object.keys(value).length===2&&['NULL_ACTIVITY_SET','CUSTOM_ACTIVITY_SET'].includes(value.detail);
  return Object.keys(value).length===4&&['AVAILABLE','PARTIAL'].includes(value.status)&&
    integer(value.count)&&value.count>=0&&value.count<=2147483647&&Array.isArray(value.values)&&
    value.values.length===Math.min(value.count,16)&&value.values.every(validActivityValue)&&
    value.truncated===(value.count>16)&&value.status===(value.truncated?'PARTIAL':'AVAILABLE');
}
function signedLong(value) {
  if(typeof value!=='string'||!/^(0|-?[1-9][0-9]{0,18})$/.test(value))return false;
  const n=BigInt(value);return n>=-9223372036854775808n&&n<=9223372036854775807n;
}
function validActivityState(value) {
  return object(value)&&Object.keys(value).length===4&&validActivitySet(value.activeActivities)&&
    validActivitySet(value.coreActivities)&&validActivityValue(value.defaultActivity)&&signedLong(value.lastScheduleUpdate);
}
function validActivityData(kind,d,record) {
  const component=(identity,status)=>identity==null?status==='NOT_EXPOSED':
    status==='AVAILABLE'&&typeof identity==='string'&&new RegExp('^component:'+record.payload.targetRevision+':[1-9][0-9]{0,2}$').test(identity)&&
    Number(identity.split(':').at(-1))<=128;
  const common=['brainClass','instanceIdentity','instanceIdentityStatus','activityInvocationId','dispatchScope','fieldScope',
    'behaviorStopStatus','movementOutcomeStatus','returnScope'];
  const extra=kind==='BRAIN_ACTIVITY_UPDATE_RETURN'?['dayTimeArgument','gameTimeArgument','before','after','preCallObserverCostNanos']:
    kind==='BRAIN_ACTIVITY_QUERY_RETURN'?['scheduleClass','scheduleInstanceIdentity','scheduleInstanceIdentityStatus','queryTickArgument','storedScheduleMatch','returnedActivity','stateAtReturn']:
    kind==='BRAIN_ACTIVITY_REQUIREMENTS_RETURN'?['requestedActivity','result','stateAtReturn']:['requestedActivity','stateAtReturn'];
  if(Object.keys(d).some(k=>![...common,...extra].includes(k))||!text(d.brainClass)||!component(d.instanceIdentity,d.instanceIdentityStatus)||
    !text(d.activityInvocationId)||!new RegExp('^activity:'+record.payload.targetRevision+':([1-9][0-9]{0,2})$').test(d.activityInvocationId)||
    Number(d.activityInvocationId.split(':').at(-1))>256||d.dispatchScope!=='UPDATE_ACTIVITY_FROM_SCHEDULE_ORIGINAL_VIRTUAL_CALL'||
    d.fieldScope!=='BASE_BRAIN_CACHED_FIELDS_ONLY'||d.behaviorStopStatus!=='NOT_EXPOSED'||d.movementOutcomeStatus!=='NOT_EXPOSED')return false;
  if(kind==='BRAIN_ACTIVITY_UPDATE_RETURN')return signedLong(d.dayTimeArgument)&&signedLong(d.gameTimeArgument)&&
    validActivityState(d.before)&&validActivityState(d.after)&&integer(d.preCallObserverCostNanos)&&d.preCallObserverCostNanos>=0&&
    d.returnScope==='NORMAL_VOID_RETURN_NOT_ACTIVITY_SUCCESS';
  if(!validActivityState(d.stateAtReturn))return false;
  if(kind==='BRAIN_ACTIVITY_QUERY_RETURN')return text(d.scheduleClass)&&component(d.scheduleInstanceIdentity,d.scheduleInstanceIdentityStatus)&&
    integer(d.queryTickArgument)&&d.queryTickArgument>=-2147483648&&d.queryTickArgument<=2147483647&&
    typeof d.storedScheduleMatch==='boolean'&&validActivityValue(d.returnedActivity)&&d.returnScope==='ORIGINAL_VIRTUAL_SCHEDULE_QUERY_RETURN';
  return validActivityValue(d.requestedActivity)&&(kind==='BRAIN_ACTIVITY_REQUIREMENTS_RETURN'?
    typeof d.result==='boolean'&&d.returnScope==='ORIGINAL_REGISTERED_MEMORY_REQUIREMENTS_RETURN':
    d.returnScope==='NORMAL_PRIVATE_SETTER_RETURN_NOT_SWITCH_SUCCESS');
}
function validNavigationReturn(d,record) {
  const revision=record.payload.targetRevision;
  const exact=exactObjectKeys;
  const speed=key=>Number.isFinite(d[key])?d[key+'Status']===undefined:d[key]===undefined&&d[key+'Status']==='NOT_EXPOSED';
  const component=d.instanceIdentityStatus==='AVAILABLE'?typeof d.instanceIdentity==='string'&&
    new RegExp('^component:'+revision+':([1-9][0-9]{0,2})$').test(d.instanceIdentity)&&Number(d.instanceIdentity.split(':').at(-1))<=128:
    d.instanceIdentityStatus==='NOT_EXPOSED'&&d.instanceIdentity==null;
  const keys=['navigationClass','instanceIdentityStatus',...(d.instanceIdentity==null?[]:['instanceIdentity']),'result',
    Number.isFinite(d.requestedSpeed)?'requestedSpeed':'requestedSpeedStatus',Number.isFinite(d.cachedSpeed)?'cachedSpeed':'cachedSpeedStatus',
    'requestedMatchesCachedPath','requestedPath','cachedPath','dispatchScope','fieldScope','resultScope','referenceScope',
    'reasonStatus','arrivalStatus','searchRelationStatus'];
  if(!exact(d,keys)||!text(d.navigationClass)||!component||typeof d.result!=='boolean'||!speed('requestedSpeed')||!speed('cachedSpeed')||
    typeof d.requestedMatchesCachedPath!=='boolean'||!validCachedPathFact(d.requestedPath,revision)||!validCachedPathFact(d.cachedPath,revision)||
    d.dispatchScope!=='BASE_PATHNAVIGATION_NORMAL_RETURN_NOT_FINAL_CUSTOM_OVERRIDE'||
    d.fieldScope!=='BASE_NAVIGATION_AND_EXACT_PATH_CACHED_FIELDS_AFTER_RETURN_AND_CAPTURE_GATES'||
    d.resultScope!=='ORIGINAL_BASE_METHOD_BOOLEAN_NOT_ARRIVAL'||d.referenceScope!=='RAW_ARGUMENT_VS_CACHED_PATH_REFERENCE_EQUALITY'||
    !['reasonStatus','arrivalStatus','searchRelationStatus'].every(k=>d[k]==='NOT_EXPOSED'))return false;
  return consistentRawPathMatch(d.requestedMatchesCachedPath,d.requestedPath,d.cachedPath,true);
}
function validBrainTickStop(kind,d,record) {
  const revision=record.payload.targetRevision,id=(value,prefix,max)=>typeof value==='string'&&new RegExp('^'+prefix+':'+revision+':([1-9][0-9]{0,2})$').test(value)&&Number(value.split(':').at(-1))<=max;
  const common=['sinkClass','instanceIdentityStatus',...(d.instanceIdentity==null?[]:['instanceIdentity']),'tickOrStopInvocationId','gameTimeArgument','dispatchScope','operandReasonStatus','arrivalStatus','searchRelationStatus'];
  const condition=kind==='BRAIN_PATH_CONDITION_RETURN',extra=condition?['condition','result','resultScope']:['branch','capturedSinkInvocationIds','capturedSinkInvocationsTruncated','childScope','returnScope'];
  if(!exactObjectKeys(d,[...common,...extra])||d.sinkClass!=='net.minecraft.world.entity.ai.behavior.MoveToTargetSink'||
    !(d.instanceIdentity==null?d.instanceIdentityStatus==='NOT_EXPOSED':d.instanceIdentityStatus==='AVAILABLE'&&id(d.instanceIdentity,'component',128))||
    !id(d.tickOrStopInvocationId,'tick-stop',256)||!signedLong(d.gameTimeArgument)||d.dispatchScope!=='ORIGINAL_BRAIN_RUNNING_BEHAVIOR_INTERFACE_CALL_EXACT_SINK'||
    !['operandReasonStatus','arrivalStatus','searchRelationStatus'].every(k=>d[k]==='NOT_EXPOSED'))return false;
  if(condition)return ['TIMED_OUT','CAN_STILL_USE'].includes(d.condition)&&typeof d.result==='boolean'&&d.resultScope==='ORIGINAL_VIRTUAL_BOOLEAN_NOT_INDIVIDUAL_OPERAND_REASONS';
  const children=d.capturedSinkInvocationIds;
  return ['TICK','STOP'].includes(d.branch)&&Array.isArray(children)&&children.length<=8&&children.every((v,i)=>id(v,'sink',256)&&(i===0||Number(v.split(':').at(-1))>Number(children[i-1].split(':').at(-1))))&&
    typeof d.capturedSinkInvocationsTruncated==='boolean'&&(!d.capturedSinkInvocationsTruncated||children.length===8)&&
    d.childScope==='DIRECT_CAPTURED_CONCRETE_CALL_SCOPES_NOT_COMPLETION_OR_FULL_CHILDREN'&&d.returnScope==='NORMAL_ORIGINAL_DISPATCH_VOID_NOT_ARRIVAL';
}
function validBrainNavigation(kind,d,record) {
  const revision=record.payload.targetRevision,exact=exactObjectKeys;
  const component=key=>d[key]==null?d[key+'Status']==='NOT_EXPOSED':d[key+'Status']==='AVAILABLE'&&typeof d[key]==='string'&&
    new RegExp('^component:'+revision+':([1-9][0-9]{0,2})$').test(d[key])&&Number(d[key].split(':').at(-1))<=128;
  const id=value=>typeof value==='string'&&new RegExp('^sink:'+revision+':([1-9][0-9]{0,2})$').test(value)&&Number(value.split(':').at(-1))<=256;
  const speed=(value,key)=>Number.isFinite(value[key])?value[key+'Status']===undefined:value[key]===undefined&&value[key+'Status']==='NOT_EXPOSED';
  const memory=value=>{
    if(value?.status==='NOT_EXPOSED')return exact(value,['status','detail'])&&typeof value.detail==='string'&&
      (['NULL_MEMORY_MAP','CUSTOM_MEMORY_MAP','UNEXPECTED_MEMORY_ENTRY','CUSTOM_MEMORY_WRAPPER','NON_PATH_MEMORY_VALUE'].includes(value.detail)||value.detail.startsWith('MEMBER_UNAVAILABLE:'));
    return value?.status==='AVAILABLE'&&typeof value.registered==='boolean'&&typeof value.present==='boolean'&&
      exact(value,['status','registered','present',...(value.present?['timeToLive','path']:[])])&&
      (!value.present||value.registered&&signedLong(value.timeToLive)&&value.path?.present===true&&validPathReferenceFact(value.path,revision));
  };
  const presence=value=>value?.status==='NOT_EXPOSED'?
    exact(value,['status','detail'])&&typeof value.detail==='string'&&
      (['NULL_MEMORY_MAP','CUSTOM_MEMORY_MAP','UNEXPECTED_MEMORY_ENTRY'].includes(value.detail)||value.detail.startsWith('MEMBER_UNAVAILABLE:')):
    value?.status==='AVAILABLE'&&exact(value,['status','registered','present'])&&typeof value.registered==='boolean'&&typeof value.present==='boolean'&&(!value.present||value.registered);
  const stopping=d.callSite==='STOP_FROM_BRIDGE';
  const state=value=>object(value)&&exact(value,['sinkPath','brainPath','navigationPath',...(stopping?['walkTargetSlot']:[]),
    Number.isFinite(value.sinkSpeed)?'sinkSpeed':'sinkSpeedStatus',Number.isFinite(value.navigationSpeed)?'navigationSpeed':'navigationSpeedStatus'])&&
    validPathReferenceFact(value.sinkPath,revision)&&memory(value.brainPath)&&validPathReferenceFact(value.navigationPath,revision)&&
    speed(value,'sinkSpeed')&&speed(value,'navigationSpeed')&&(!stopping||presence(value.walkTargetSlot));
  const common=['sinkClass','instanceIdentityStatus',...(d.instanceIdentity==null?[]:['instanceIdentity']),'sinkInvocationId',
    'parentInvocationStatus',...(d.parentInvocationStatus==='AVAILABLE'?['parentInvocationId']:[]),'callSite','gameTimeArgument',
    'dispatchScope','fieldScope','reasonStatus','arrivalStatus','searchRelationStatus'];
  const extra=kind==='BRAIN_PATH_SINK_RETURN'?['before','after','preCallObserverCostNanos','beforeScope','afterScope','returnScope']:
    kind==='BRAIN_PATH_MEMORY_WRITE_RETURN'?['brainClass','brainIdentityStatus',...(d.brainIdentity==null?[]:['brainIdentity']),
      'requestedPath','memoryAtReturn',Object.hasOwn(d,'requestedMatchesCachedMemory')?'requestedMatchesCachedMemory':'requestedMatchesCachedMemoryStatus','writeSite','returnScope','referenceScope']:
    kind==='BRAIN_PATH_MEMORY_ERASE_RETURN'?['brainClass','brainIdentityStatus',...(d.brainIdentity==null?[]:['brainIdentity']),
      'memoryModule','slotAtReturn','memoryScope','returnScope']:
    kind==='BRAIN_PATH_NAVIGATION_STOP_RETURN'?['navigationClass','navigationIdentityStatus',...(d.navigationIdentity==null?[]:['navigationIdentity']),
      'cachedPath',Number.isFinite(d.cachedSpeed)?'cachedSpeed':'cachedSpeedStatus','brainPathAtReturn','returnScope']:
    ['navigationClass','navigationIdentityStatus',...(d.navigationIdentity==null?[]:['navigationIdentity']),'result',
      Number.isFinite(d.requestedSpeed)?'requestedSpeed':'requestedSpeedStatus',Number.isFinite(d.cachedSpeed)?'cachedSpeed':'cachedSpeedStatus',
      'requestedMatchesCachedPath','requestedPath','cachedPath','brainPathAtReturn','returnScope','referenceScope'];
  if(!exact(d,[...common,...extra])||d.sinkClass!=='net.minecraft.world.entity.ai.behavior.MoveToTargetSink'||!component('instanceIdentity')||!id(d.sinkInvocationId)||
    !['START_FROM_BRIDGE','TICK_FROM_BRIDGE','START_FROM_TICK','STOP_FROM_BRIDGE'].includes(d.callSite)||!signedLong(d.gameTimeArgument)||
    d.dispatchScope!=='ORIGINAL_KNOWN_SINK_CONCRETE_CALL_FROM_BRIDGE_OR_RESTART'||d.fieldScope!=='BASE_CACHED_FIELDS_AT_DECLARED_CAPTURE_BOUNDARY'||
    !['reasonStatus','arrivalStatus','searchRelationStatus'].every(k=>d[k]==='NOT_EXPOSED'))return false;
  if(d.parentInvocationStatus==='AVAILABLE'){
    if(!id(d.parentInvocationId)||Number(d.parentInvocationId.split(':').at(-1))>=Number(d.sinkInvocationId.split(':').at(-1)))return false;
  }else if(d.parentInvocationStatus!=='NOT_CAPTURED')return false;
  if(kind==='BRAIN_PATH_SINK_RETURN')return state(d.before)&&state(d.after)&&integer(d.preCallObserverCostNanos)&&d.preCallObserverCostNanos>=0&&
    d.beforeScope==='BEFORE_ORIGINAL_CALL_AFTER_CAPTURE_GATES'&&d.afterScope==='AFTER_ORIGINAL_RETURN_AND_CAPTURE_GATES'&&
    d.returnScope==='NORMAL_ORIGINAL_VOID_RETURN_NOT_MOVEMENT_SUCCESS';
  if(kind==='BRAIN_PATH_MEMORY_ERASE_RETURN')return stopping&&text(d.brainClass)&&component('brainIdentity')&&
    ['PATH','WALK_TARGET'].includes(d.memoryModule)&&(d.memoryModule==='PATH'?memory(d.slotAtReturn):presence(d.slotAtReturn))&&
    d.memoryScope==='BASE_CACHED_PATH_OR_WALK_TARGET_OPTIONAL_SLOT_AFTER_RETURN'&&d.returnScope==='ORIGINAL_VIRTUAL_ERASE_NORMAL_RETURN_NOT_SLOT_CLEAR_SUCCESS';
  if(kind==='BRAIN_PATH_NAVIGATION_STOP_RETURN')return stopping&&text(d.navigationClass)&&component('navigationIdentity')&&
    validCachedPathFact(d.cachedPath,revision)&&speed(d,'cachedSpeed')&&memory(d.brainPathAtReturn)&&
    d.returnScope==='ORIGINAL_VIRTUAL_STOP_NORMAL_RETURN_NOT_ARRIVAL_OR_PATH_CLEAR_SUCCESS';
  if(kind==='BRAIN_PATH_MEMORY_WRITE_RETURN'){
    if(stopping||!text(d.brainClass)||!component('brainIdentity')||!validCachedPathFact(d.requestedPath,revision)||!memory(d.memoryAtReturn)||
      d.writeSite!==(d.callSite==='TICK_FROM_BRIDGE'?'TICK_PATH_RECONCILE':'START_PATH_WRITE')||
      d.returnScope!=='ORIGINAL_VIRTUAL_PATH_MEMORY_WRITE_NORMAL_RETURN_NOT_RETENTION_SUCCESS'||
      d.referenceScope!=='RAW_ARGUMENT_VS_CACHED_MEMORY_VALUE_REFERENCE_NOT_WRITE_SUCCESS')return false;
    return d.memoryAtReturn.status==='NOT_EXPOSED'?d.requestedMatchesCachedMemory===undefined&&d.requestedMatchesCachedMemoryStatus==='NOT_EXPOSED':
      typeof d.requestedMatchesCachedMemory==='boolean'&&consistentRawPathMatch(d.requestedMatchesCachedMemory,d.requestedPath,d.memoryAtReturn.path??{present:false});
  }
  return ['START_FROM_BRIDGE','START_FROM_TICK'].includes(d.callSite)&&text(d.navigationClass)&&component('navigationIdentity')&&typeof d.result==='boolean'&&
    speed(d,'requestedSpeed')&&speed(d,'cachedSpeed')&&typeof d.requestedMatchesCachedPath==='boolean'&&
    validCachedPathFact(d.requestedPath,revision)&&validCachedPathFact(d.cachedPath,revision)&&memory(d.brainPathAtReturn)&&
    consistentRawPathMatch(d.requestedMatchesCachedPath,d.requestedPath,d.cachedPath,true)&&
    d.returnScope==='ORIGINAL_VIRTUAL_MOVE_TO_RETURN_AT_SINK_CALL_SITE_NOT_ARRIVAL'&&d.referenceScope==='RAW_ARGUMENT_VS_CACHED_PATH_REFERENCE_EQUALITY';
}
function validData(kind,d,record) {
  if(BRAIN_COMPUTE_KINDS.includes(kind))return validBrainCompute(kind,d,record);
  if(kind==='BRAIN_PATH_MEMORY_REQUIREMENT_RETURN')return validBrainMemoryRequirement(d,record);
  if(BRAIN_START_KINDS.includes(kind))return validBrainStart(kind,d,record);
  if(['BRAIN_PATH_CONDITION_RETURN','BRAIN_PATH_DISPATCH_RETURN'].includes(kind))return validBrainTickStop(kind,d,record);
  if(kind.startsWith('BRAIN_PATH_'))return validBrainNavigation(kind,d,record);
  if(kind==='NAVIGATION_MOVE_TO_RETURN')return validNavigationReturn(d,record);
  if(kind.startsWith('BRAIN_ACTIVITY_'))return validActivityData(kind,d,record);
  if (kind === 'MOD_COORDINATION_RETURN') return validKnightCoordination(d,record);
  if (kind === 'PATH_NEIGHBORS_RETURN') return validNeighborReturn(d);
  if (kind === 'PATH_HEAP_OPERATION_RETURN') return validHeapReturn(d,record);
  if (kind === 'PATH_NODE_CLOSED_CHECKPOINT') return validClosedCheckpoint(d,record);
  if (kind === 'PATH_NODE_G_WRITE_CHECKPOINT') return validGWriteCheckpoint(d,record);
  if (kind === 'PATH_EDGE_DISTANCE_RETURN') return validEdgeDistance(d,record);
  if (kind === 'PATH_RETURNED_NODES') return validReturnedPath(d,record);
  if (kind === 'EFFECTIVE_MALUS_RETURN') {
    const numeric=Number.isFinite(d.returnedMalus),keys=['receiverUuid','receiverClass','evaluatorClass','pathType',
      numeric?'returnedMalus':'returnedMalusStatus','dispatchScope','callSiteScope','effectivePathCostStatus','underlyingSourceStatus'];
    return Object.keys(d).length===keys.length&&Object.keys(d).every(k=>keys.includes(k))&&
      uuid(d.receiverUuid)&&d.receiverUuid===record.scope?.entityUuid&&text(d.receiverClass)&&text(d.evaluatorClass)&&text(d.pathType)&&
      (numeric||(d.returnedMalus===undefined&&d.returnedMalusStatus==='NOT_EXPOSED'))&&
      d.dispatchScope==='ORIGINAL_EVALUATOR_VIRTUAL_MOB_MALUS_RETURN'&&d.callSiteScope==='KNOWN_BASE_EVALUATOR_CLASS_SET_NOT_EXACT_METHOD'&&
      d.effectivePathCostStatus==='NOT_EXPOSED'&&d.underlyingSourceStatus==='NOT_EXPOSED';
  }
  if (kind.startsWith('GOAL_')) {
    if (!['goal','target'].includes(d.selector) || !text(d.goalClass) || !integer(d.priority) ||
        !validInstanceIdentity(d,true)) return false;
    return kind.includes('ELIGIBILITY') || kind.includes('CONTINUATION')
      ? typeof d.result === 'boolean' && d.rejectionReasonStatus === 'NOT_EXPOSED' && d.callSiteStatus === 'NOT_EXPOSED'
      : typeof d.running === 'boolean' && d.reasonStatus === 'NOT_EXPOSED';
  }
  if (kind === 'BRAIN_TICK_RETURN') return text(d.brainClass) && typeof d.storedBrainMatch === 'boolean' && validInstanceIdentity(d);
  if (kind.startsWith('BEHAVIOR_')) return text(d.className) && validInstanceIdentity(d) &&
    ['RUNNING','STOPPED'].includes(d.cachedStatus) && d.reasonStatus === 'NOT_EXPOSED' &&
    (kind !== 'BEHAVIOR_TRY_START_RETURN' || typeof d.result === 'boolean');
  if (kind === 'SENSOR_SCAN_RETURN') return text(d.className) && validInstanceIdentity(d) && d.candidatePopulationStatus === 'NOT_EXPOSED';
  if (kind === 'CONTROL_TICK_RETURN') return ['move','look','jump'].includes(d.control) && object(d.cachedBaseFields) &&
    text(d.cachedBaseFields.className) && d.cachedBaseFields.fieldScope === 'BASE_CONTROL_FIELDS_ONLY';
  if (kind === 'CONTROL_TELEPORT_RETURN') return typeof d.result === 'boolean' &&
    [d.requestedPosition,d.returnedPosition].every(p=>object(p)&&['x','y','z'].every(k=>Number.isFinite(p[k]))) &&
    d.dispatchScope === 'BASE_RANDOM_TELEPORT_RETURN' && d.reasonStatus === 'NOT_EXPOSED';
  if (kind === 'CONTROL_GHAST_REACH_RETURN') {
    const keys=['receiverUuid','controllerClass','direction','stepCount','result','dispatchScope','pathSemantics','collisionLocationStatus','reasonStatus'];
    return Object.keys(d).length===keys.length&&Object.keys(d).every(k=>keys.includes(k))&&
      uuid(d.receiverUuid)&&d.receiverUuid===record.scope?.entityUuid&&
      d.controllerClass==='net.minecraft.world.entity.monster.Ghast$GhastMoveControl'&&vector(d.direction)&&Object.keys(d.direction).length===3&&
      integer(d.stepCount)&&d.stepCount>=0&&d.stepCount<=2147483647&&typeof d.result==='boolean'&&
      d.dispatchScope==='GHAST_ORIGINAL_CAN_REACH_RETURN'&&d.pathSemantics==='CUSTOM_STEERING_REACH_NOT_A_STAR'&&
      d.collisionLocationStatus==='NOT_EXPOSED'&&d.reasonStatus==='NOT_EXPOSED';
  }
  if (kind.startsWith('CONTROL_PROJECTILE_')) {
    if(!uuid(d.ownerUuid)||d.ownerUuid!==record.scope?.entityUuid||!uuid(d.projectileUuid)||d.projectileUuid===d.ownerUuid||
      !text(d.projectileClass)||!integer(d.spawnEventIndex)||d.spawnEventIndex<1||d.spawnEventIndex>record.payload.eventIndex||
      d.relationshipScope!=='ACCEPTED_FRESH_SPAWN_SELECTED_CACHED_OWNER')return false;
    if(kind==='CONTROL_PROJECTILE_SPAWN_RETURN')return typeof d.result==='boolean'&&d.trackingLimit===16&&
      d.spawnEventIndex===record.payload.eventIndex&&vector(d.position)&&vector(d.velocity)&&d.dispatchScope==='SERVER_ADD_FRESH_ENTITY_RETURN';
    if(d.spawnEventIndex>=record.payload.eventIndex)return false;
    if(kind==='CONTROL_PROJECTILE_TICK_RETURN')return vector(d.position)&&vector(d.velocity)&&typeof d.removed==='boolean'&&
      text(d.dimension)&&d.dispatchScope==='SERVER_NON_PASSENGER_ORIGINAL_TICK_AFTER';
    if(kind==='CONTROL_PROJECTILE_HIT_RETURN')return ['ENTITY','BLOCK'].includes(d.hitType)&&vector(d.hitPosition)&&
      (d.hitType==='ENTITY'?uuid(d.targetUuid):d.targetUuid==null)&&
      d.dispatchScope==='BASE_PROJECTILE_ON_HIT_RETURN'&&d.damageOutcomeStatus==='NOT_EXPOSED';
    if(kind==='CONTROL_PROJECTILE_HURT_RETURN')return uuid(d.targetUuid)&&typeof d.result==='boolean'&&Number.isFinite(d.requestedDamage)&&
      Number.isSafeInteger(d.preCallObserverCostNanos)&&d.preCallObserverCostNanos>=0&&
      d.requestedDamage>=0&&d.dispatchScope==='ARROW_OR_FIREBALL_ORIGINAL_ENTITY_HURT_CALL'&&d.damageReasonStatus==='NOT_EXPOSED'&&
      (d.healthStatus==='NOT_EXPOSED'?
        d.healthBefore===undefined&&d.healthAfter===undefined&&d.healthDelta===undefined&&d.healthScope==='NON_LIVING_OR_UNAVAILABLE':
        d.healthStatus==='AVAILABLE'&&['healthBefore','healthAfter','healthDelta'].every(k=>Number.isFinite(d[k]))&&
        d.healthScope==='BASE_LIVING_DATA_HEALTH_ACROSS_ORIGINAL_CALL'&&
        Math.abs(d.healthDelta-(d.healthBefore-d.healthAfter))<=1e-5);
    return false;
  }
  if (kind === 'BASE_MALUS_RETURN') return text(d.pathType) && numberOrUnknown(d,'returnedMalus') &&
    d.dispatchScope === 'BASE_METHOD_RETURN_NOT_CUSTOM_OVERRIDE_RESULT' && d.effectiveSourceStatus === 'NOT_EXPOSED';
  if (kind === 'PATH_SEARCH_STATE') return text(d.searchId) && validFrontier(d.frontier);
  if (kind === 'PATH_SEARCH_RESULT') return text(d.searchId) && typeof d.resultPresent === 'boolean' &&
    (!d.resultPresent || text(d.resultClass)) &&
    (d.canReach === undefined || typeof d.canReach === 'boolean') &&
    (d.resultNodeCount === undefined || (integer(d.resultNodeCount) && d.resultNodeCount >= 0));
  return false;
}

/** Validate retained output; no invocation, neighbor population or causal reason is reconstructed. */
export function validOriginalDecisionEvent(record) {
  const p=record.payload;
  return record.source?.side === 'SERVER' && p?.schema === 'kneekura.original-decision-event/v1' &&
    p.semantics === (['PATH_NODE_CLOSED_CHECKPOINT','PATH_NODE_G_WRITE_CHECKPOINT','BRAIN_PATH_COMPUTE_PATH_WRITE_CHECKPOINT'].includes(p.kind)?'ORIGINAL_FIELD_WRITE_CHECKPOINT_ONLY':'ORIGINAL_INVOCATION_RETURN_ONLY') &&
    integer(p.targetRevision) && p.targetRevision > 0 &&
    integer(p.eventIndex) && p.eventIndex >= 1 && p.eventIndex <= 256 && text(p.burstId) &&
    Object.hasOwn(KINDS,p.kind) && object(p.data) && bounded(p) &&
    Number.isSafeInteger(p.observerCostNanos) && p.observerCostNanos >= 0 &&
    p.observerCostScope === 'BUILD_AND_FIRST_BYTE_CHECK_EXCLUDES_FINAL_ENCODING_WRITER' &&
    validData(p.kind,p.data,record) && new TextEncoder().encode(JSON.stringify(p)).length <= 32768;
}

export function appendOriginalDecisionEvents(records,stages,capabilities,timeline) {
  for (const record of records) {
    if (!validOriginalDecisionEvent(record)) continue;
    const p=record.payload;
    const data=originalDecisionData(record);
    const [stage,capability]=KINDS[p.kind];
    const algorithm=['PATH_SEARCH_STATE','PATH_NODE_CLOSED_CHECKPOINT','PATH_NODE_G_WRITE_CHECKPOINT'].includes(p.kind);
    const status=algorithm ? 'INSTRUMENTED_ALGORITHM_STATE' : 'DIRECT_OBSERVED';
    const relation=algorithm ? 'ALGORITHM_TRACE_RELATION' : 'DIRECT_RUNTIME_RELATION';
    stages[stage] ??= {facts:[]};
    stages[stage].facts.push({key:p.kind.toLowerCase(),value:data,epistemic_status:status,
      causal_relation:relation,source_observation_ids:[record.observationId],
      note:'Bounded original observation boundary only; no reason, complete decision history or adjacent-event causality is inferred.'});
    const unavailable=(p.kind === 'PATH_SEARCH_STATE' && p.data.frontier.status === 'NOT_EXPOSED')||
      (p.kind === 'PATH_RETURNED_NODES' && p.data.pathNodes.status === 'NOT_EXPOSED');
    if (!unavailable) {
      const existing=capabilities[capability];
      capabilities[capability]={status:'PARTIAL',source_observation_ids:[...new Set([
        ...(existing?.source_observation_ids ?? []),record.observationId])],
        detail:'Finite opt-in capture of observed boundaries; absent or suppressed observations and causal reasons remain unknown.'};
    }
    timeline.push({event_id:record.observationId,tick:record.gameTime,stage,kind:p.kind,
      summary:{...data,burstId:p.burstId,eventIndex:p.eventIndex},epistemic_status:status,
      causal_relation:relation,source_observation_ids:[record.observationId]});
  }
}
