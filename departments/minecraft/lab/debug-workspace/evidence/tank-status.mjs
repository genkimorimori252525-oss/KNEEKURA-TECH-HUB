import {requireTankIdentity,sameTankIdentity,boundedTankPacket,requireTankObservations,tankFact,validTankGeometry} from './tank-contract.mjs';

const hash=h=>typeof h==='string'&&/^[a-f0-9]{64}$/.test(h);
function freshness(row,expected) {
  if(!row)return {status:'NOT_CAPTURED',ageMs:null};
  const current=expected.currentClock,old=row.clock;
  if(!current)return {status:'STORED',ageMs:null};
  if(!old||['domain','processId','processStartedAt','monotonicOriginWallClock'].some(k=>current[k]==null||current[k]!==old[k])
      ||!Number.isSafeInteger(current.monotonicElapsedNanos)||!Number.isSafeInteger(old.monotonicElapsedNanos))return {status:'UNKNOWN',ageMs:null};
  const ageMs=(current.monotonicElapsedNanos-old.monotonicElapsedNanos)/1e6;
  const maxAgeMs=expected.maxAgeMs??2000;
  if(!Number.isFinite(maxAgeMs)||maxAgeMs<0||maxAgeMs>5000)throw new TypeError('TANK_FRESHNESS_BOUND_REQUIRED');
  return {status:ageMs<0?'UNKNOWN':ageMs<=maxAgeMs?'CURRENT':'STALE',ageMs:ageMs<0?null:ageMs};
}
function bindingOf(binding={}) {
  const out={};
  for(const key of ['authorityHash','copyBaselineHash','fixtureHash']) {
    const value=binding[key]??null;
    if(value!==null&&!hash(value))throw new TypeError('TANK_WORLD_HASH_REQUIRED');
    out[key]=value;
  }
  out.fixtureChanges=binding.fixtureChanges??[];
  if(!Array.isArray(out.fixtureChanges)||out.fixtureChanges.length>32||out.fixtureChanges.some(s=>typeof s!=='string'||s.length>512))throw new TypeError('TANK_FIXTURE_CHANGES_BOUND');
  // Hash equality alone proves neither authoritative provenance nor how a fixture was prepared.
  out.provenanceStatus='UNKNOWN';
  return out;
}
export function buildTankStatus({observations,identity,expected={},worldBinding,health={}}={}) {
  const id=requireTankIdentity(identity),rows=requireTankObservations(observations).filter(r=>r?.lane==='TANK_PRESENTATION_STATUS');
  const seen=new Set();
  for(const r of rows) {
    if(!sameTankIdentity(r,id))throw new TypeError('TANK_STATUS_IDENTITY_MISMATCH');
    const p=r.payload;
    if(r.kind!=='observation'||r.scope?.kind!=='GLOBAL_HEALTH'||r.source?.side!=='CLIENT'||r.epistemicStatus!=='OBSERVED'
        ||r.completeness?.complete!==true||typeof r.observationId!=='string'||r.observationId.length>512
        ||!Number.isSafeInteger(r.writerSeq)||r.writerSeq<1||!(r.gameTime==null||Number.isSafeInteger(r.gameTime))
        ||p?.schema!=='kneekura.tank-presentation-status/v1'
        ||['requested','registered','eligible','drawSubmitted','brightness'].some(k=>typeof p[k]!=='boolean')
        ||typeof p.reason!=='string'||p.reason.length>128
        ||!(p.recipeHash==null||hash(p.recipeHash))||!(p.geometry==null||validTankGeometry(p.geometry))
        ||!(p.reportedRemainingMs==null||Number.isSafeInteger(p.reportedRemainingMs)&&p.reportedRemainingMs>=0&&p.reportedRemainingMs<=120000)
        ||p.registered&&(p.recipeHash==null||p.geometry==null||p.reportedRemainingMs==null)
        ||p.motionEnabled!=null&&typeof p.motionEnabled!=='boolean'
        ||p.drawSubmitted&&!p.eligible||p.eligible&&!p.registered)throw new TypeError('INVALID_TANK_STATUS');
    if(seen.has(r.observationId))throw new TypeError('DUPLICATE_TANK_STATUS');seen.add(r.observationId);
  }
  const latest=rows.toSorted((a,b)=>a.writerSeq-b.writerSeq).at(-1),p=latest?.payload;
  const fact=k=>latest&&p[k]!=null?tankFact(p[k],'SAMPLED_OBSERVED',latest):tankFact(null,'NOT_CAPTURED',latest??null);
  const mismatch=p&&expected.recipeHash!=null&&expected.recipeHash!==p.recipeHash;
  return boundedTankPacket({schema:'kneekura.tank-status/v1',identity:id,worldBinding:bindingOf(worldBinding),
    geometry:fact('geometry'),presentation:{requested:fact('requested'),registered:fact('registered'),eligible:fact('eligible'),
      drawSubmitted:fact('drawSubmitted'),brightness:fact('brightness'),recipeHash:fact('recipeHash'),
      motion:typeof p?.motionEnabled==='boolean'?tankFact(p.motionEnabled,'SAMPLED_OBSERVED',latest):tankFact(null,'NOT_CAPTURED'),
      pixelEvidence:tankFact(null,'NOT_CAPTURED',null,['DRAW_SUBMISSION_DOES_NOT_PROVE_VISIBLE_PIXELS']),
      reportedRemainingMs:latest&&p.reportedRemainingMs!=null?tankFact(p.reportedRemainingMs,'SAMPLED_OBSERVED',latest,['REFERENCE_ONLY_NOT_AUTHORITY']):tankFact(null,'NOT_CAPTURED',latest??null),
      reason:mismatch?'RECIPE_MISMATCH':p?.reason??'NOT_CAPTURED',freshness:freshness(latest,expected)},
    channels:structuredClone(health.channels??{}),health:{status:'NOT_EVALUATED',statusSuppressedTotal:p?.statusSuppressedTotal??null},
    evidenceRefs:latest?[latest.observationId]:[],semantics:{grantsAuthority:false,storedEvidenceIsHistorical:true,drawSubmissionProvesVisibility:false}});
}
