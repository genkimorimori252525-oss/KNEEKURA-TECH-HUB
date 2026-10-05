import {boundedTankPacket,requireTankIdentity} from '../evidence/tank-contract.mjs';

export function requireTankTimeBudget(budget) {
  const keys=['experimentMs','finalizationMs','cleanupMs','marginMs'];
  if(!budget||Object.keys(budget).length!==keys.length||keys.some(k=>!Number.isSafeInteger(budget[k])||budget[k]<0||budget[k]>120000))throw new TypeError('INVALID_TANK_TIME_BUDGET');
  const required=keys.reduce((n,k)=>n+budget[k],0);
  if(required>120000)throw new RangeError('TANK_TIME_BUDGET_EXCEEDS_ORIGINAL_LEASE');
  return required;
}
export function requireTankProfile(profile) {
  const keys=['kind','grid','brightness','motion','decisionChannels'];
  if(!profile||Object.keys(profile).length!==keys.length||!['OBSERVE_GRID','BENCHMARK'].includes(profile.kind)
      ||['grid','brightness','motion'].some(k=>typeof profile[k]!=='boolean')
      ||profile.kind==='OBSERVE_GRID'&&!profile.grid||!Array.isArray(profile.decisionChannels)
      ||profile.decisionChannels.length>16||new Set(profile.decisionChannels).size!==profile.decisionChannels.length
      ||profile.decisionChannels.some(k=>typeof k!=='string'||!/^[A-Z_]{1,64}$/.test(k)))throw new TypeError('EXPLICIT_TANK_PROFILE_REQUIRED');
}
export function buildTankPreflight({status,profile,requiredChannels,timeBudget,leaseCheck}={}) {
  requireTankProfile(profile);const requiredMs=requireTankTimeBudget(timeBudget);
  if(status?.schema!=='kneekura.tank-status/v1')throw new TypeError('TANK_STATUS_REQUIRED');
  const identity=requireTankIdentity(status.identity);
  if(!Array.isArray(requiredChannels)||requiredChannels.length>16||requiredChannels.some(k=>typeof k!=='string'||!/^[A-Z_]{1,64}$/.test(k)))throw new TypeError('TANK_REQUIRED_CHANNELS_BOUND');
  const checks=[];
  const add=(name,state,reason)=>checks.push({name,status:state,reason});
  const p=status.presentation??{};
  if(['EXPIRED','RECIPE_MISMATCH','SERVER_MISMATCH','DISCONNECTED'].includes(p.reason))add('presentation','NOT_READY',p.reason);
  else if(profile.grid) {
    for(const key of ['requested','registered','eligible','drawSubmitted'])add(key,
      p[key]?.value===true&&p[key].status==='SAMPLED_OBSERVED'?'READY':p[key]?.value===false?'NOT_READY':'UNKNOWN',
      p[key]?.value===true?'SAMPLED_RECORD':'REQUIRED_GRID_STATE_MISSING');
  }
  add('freshness',p.freshness?.status==='CURRENT'?'READY':'UNKNOWN',p.freshness?.status??'NOT_CAPTURED');
  add('brightness',typeof p.brightness?.value!=='boolean'?'UNKNOWN':p.brightness.value===profile.brightness?'READY':'NOT_READY','EXPLICIT_DISPLAY_CONDITION');
  add('motion',typeof p.motion?.value!=='boolean'?'UNKNOWN':p.motion.value===profile.motion?'READY':'NOT_READY','SAMPLED_OVERLAY_CONFIGURATION_NOT_VISIBLE_PIXELS');
  if(!profile.grid)add('grid-off',typeof p.eligible?.value!=='boolean'?'UNKNOWN':p.eligible.value?'NOT_READY':'READY','EXPLICIT_GRID_OFF');
  for(const lane of new Set([...requiredChannels,...profile.decisionChannels]))add('channel:'+lane,
    status.channels?.[lane]?.status==='AVAILABLE'?'READY':'UNKNOWN',status.channels?.[lane]?.status??'NOT_CAPTURED');
  const remainingMs=leaseCheck?.remainingMs;
  let leaseStatus='UNKNOWN';
  if(leaseCheck&&leaseCheck.status!=='UNKNOWN') {
    if(!['SUFFICIENT','INSUFFICIENT'].includes(leaseCheck.status)||!Number.isSafeInteger(remainingMs)||remainingMs<0||remainingMs>120000)throw new TypeError('INVALID_TANK_LEASE_CHECK');
    leaseStatus=leaseCheck.status==='SUFFICIENT'&&leaseCheck.requiredMs===requiredMs&&remainingMs>=requiredMs?'READY':'NOT_READY';
  }
  add('lease',leaseStatus,leaseStatus==='READY'?'FRESH_CHECK_REQUIRES_DISPATCH_RECHECK':leaseStatus==='UNKNOWN'?'LIVE_OWNER_RECHECK_REQUIRED':'INSUFFICIENT_OR_MISMATCHED_BUDGET');
  const state=checks.some(c=>c.status==='NOT_READY')?'NOT_READY':checks.some(c=>c.status==='UNKNOWN')?'UNKNOWN':'READY';
  return boundedTankPacket({schema:'kneekura.tank-preflight/v1',identity,profile,status:state,
    reasons:checks.filter(c=>c.status!=='READY').map(c=>({check:c.name,reason:c.reason})),checks,timeBudget,
    leaseCheck:{status:leaseStatus==='READY'?'SUFFICIENT':leaseStatus==='NOT_READY'?'INSUFFICIENT':'UNKNOWN',
      remainingMs:leaseStatus==='UNKNOWN'?null:remainingMs,requiredMs},evidenceRefs:status.evidenceRefs??[],
    semantics:{grantsAuthority:false,requiresDispatchRecheck:true,pixelVisibilityAcceptance:'SEPARATE_NOT_EVALUATED'}});
}
