import {boundedTankPacket,requireTankIdentity} from './tank-contract.mjs';
import {compareVisualRuns} from './visual-comparison.mjs';
import {stableJson} from '../bridge/json.mjs';
const same=(a,b)=>stableJson(a)===stableJson(b);
const required=['baselineHash','fixtureHash','worldBinding','sourceBinding','subject','observer','presentation','alignment','initialState','actions','assertions','windowDurationTicks'];
const allowed=['sourceBinding'];
const absent=v=>v==null||(typeof v==='object'&&Object.values(v).some(absent));
const object=v=>v!==null&&typeof v==='object'&&!Array.isArray(v);
const text=v=>typeof v==='string'&&v.length>0;
const hash=v=>typeof v==='string'&&/^[a-f0-9]{64}$/.test(v);
const positive=v=>Number.isSafeInteger(v)&&v>0;
function completeCondition(key,value) {
  if(absent(value))return false;
  switch(key) {
    case 'worldBinding':return object(value)&&['authorityHash','copyBaselineHash','fixtureHash'].every(k=>hash(value[k]));
    case 'sourceBinding':return object(value)&&['profile_id','index_snapshot_id'].every(k=>text(value[k]))
      &&/^(?:[a-f0-9]{40}|[a-f0-9]{64})$/.test(value.source_revision??'')
      &&['build_artifact_hash','dirty_hash','config_hash','resource_hash'].every(k=>hash(value[k]));
    case 'observer':return object(value)&&Array.isArray(value.channels)&&value.channels.length>0&&value.channels.every(text)
      &&positive(value.sampleIntervalTicks)&&positive(value.tickRate);
    case 'presentation':return object(value)&&typeof value.grid==='boolean'&&typeof value.brightness==='boolean';
    case 'alignment':return object(value)&&text(value.actionId)&&text(value.operation)&&object(value.args)
      &&Number.isSafeInteger(value.windowStartOffset)&&Number.isSafeInteger(value.windowEndOffset)&&value.windowEndOffset>=value.windowStartOffset;
    case 'subject':return object(value)&&['subjectId','entityType','uuid'].every(k=>text(value[k]));
    case 'baselineHash':case 'fixtureHash':return hash(value);
    case 'initialState':case 'actions':case 'assertions':return Array.isArray(value);
    case 'windowDurationTicks':return Number.isSafeInteger(value)&&value>=0;
    default:return true;
  }
}
export function compareExperimentDigests({before,after,intendedDifferences=[]}={}) {
  for(const d of [before,after]){if(d?.schema!=='kneekura.experiment-digest/v1')throw new TypeError('EXPERIMENT_DIGEST_REQUIRED');requireTankIdentity(d.identity);}
  if(!Array.isArray(intendedDifferences)||intendedDifferences.length>8)throw new TypeError('INVALID_INTENDED_DIFFERENCE');
  const used=new Set();for(const d of intendedDifferences){
    if(!d||Object.keys(d).sort().join(',')!=='after,before,field'||!allowed.includes(d.field)||used.has(d.field)||same(d.before,d.after))throw new TypeError('INVALID_INTENDED_DIFFERENCE');used.add(d.field);
    if(!same(before.conditions[d.field],d.before)||!same(after.conditions[d.field],d.after))throw new TypeError('STALE_INTENDED_DIFFERENCE');
  }
  const differences=[],missing=[];
  for(const key of required){const a=before.conditions?.[key],b=after.conditions?.[key];
    if(!completeCondition(key,a)||!completeCondition(key,b)){missing.push(key);continue;}
    // UUID correspondence must be registered explicitly in both conditions, never guessed by proximity.
    if(!same(a,b)&&!used.has(key))differences.push({field:key,before:a,after:b});
  }
  for(const side of [before,after])if(side.conditions.subject?.uuid!==side.identity.subjectUuid)differences.push({field:'subject.uuid',reason:'IDENTITY_MAPPING_MISMATCH'});
  if(before.quality?.status!=='SAMPLING_GRID_COMPLETE'||after.quality?.status!=='SAMPLING_GRID_COMPLETE')missing.push('SAMPLING_COVERAGE');
  const verified={source:'VERIFIED_REGISTERED_DISK_BINDING',world:'VERIFIED_RETAINED_EVIDENCE',observer:'VERIFIED_RETAINED_EVIDENCE',presentation:'VERIFIED_RETAINED_EVIDENCE',alignment:'VERIFIED_RETAINED_ACTION_EFFECT'};
  for(const [field,status] of Object.entries(verified))if([before,after].some(d=>d.conditionEvidence?.[field]!==status))missing.push(field.toUpperCase()+'_EVIDENCE');
  return boundedTankPacket({schema:'kneekura.experiment-comparison/v1',status:differences.length?'NON_COMPARABLE':missing.length?'INCONCLUSIVE':'MATCHED_RETAINED_EVIDENCE',
    before:before.identity,after:after.identity,alignment:{before:before.conditions.alignment,after:after.conditions.alignment},conditionDifferences:differences,
    intendedDifferences:structuredClone(intendedDifferences),missingConditions:missing,
    metricDifferences:{before:before.metrics,after:after.metrics,interpretation:'OBSERVED_METRICS_NOT_IMPROVEMENT'},
    improvement:'NOT_EVALUATED',assertionAcceptance:'NOT_EVALUATED',visual:{status:'NOT_CAPTURED'},limitations:['SAMPLED_GRID_COMPLETENESS_IS_NOT_CONTINUOUS_EVENT_COVERAGE']});
}
/** Delegate image provenance/camera/pixel work to the existing canonical comparison. */
export async function compareExperimentVisualEvidence({before,after,intendedDifferences=[],presentationBefore,presentationAfter,displayDiagnostic=false}) {
  const control=p=>p?.grid===false&&p?.brightness===false;
  if(!displayDiagnostic&&(!control(presentationBefore)||!control(presentationAfter)))return {status:'NON_COMPARABLE',reason:'GRID_OFF_BRIGHTNESS_OFF_CONTROLS_REQUIRED',artifacts:[]};
  const result=await compareVisualRuns({before,after,intendedDifferences});
  return {...result,purpose:displayDiagnostic?'DISPLAY_DIAGNOSTIC_NOT_APPEARANCE_ACCEPTANCE':'UNMODIFIED_APPEARANCE_COMPARISON'};
}
