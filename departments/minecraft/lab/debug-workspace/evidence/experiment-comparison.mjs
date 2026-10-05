import {boundedTankPacket,requireTankIdentity} from './tank-contract.mjs';
import {compareVisualRuns} from './visual-comparison.mjs';
import {stableJson} from '../bridge/json.mjs';
const same=(a,b)=>stableJson(a)===stableJson(b);
const required=['baselineHash','fixtureHash','worldBinding','sourceBinding','subject','observer','presentation','alignment','initialState','actions','assertions','windowDurationTicks'];
const allowed=['sourceBinding'];
const absent=v=>v==null||(typeof v==='object'&&Object.values(v).some(absent));
export function compareExperimentDigests({before,after,intendedDifferences=[]}={}) {
  for(const d of [before,after]){if(d?.schema!=='kneekura.experiment-digest/v1')throw new TypeError('EXPERIMENT_DIGEST_REQUIRED');requireTankIdentity(d.identity);}
  if(!Array.isArray(intendedDifferences)||intendedDifferences.length>8)throw new TypeError('INVALID_INTENDED_DIFFERENCE');
  const used=new Set();for(const d of intendedDifferences){
    if(!d||Object.keys(d).sort().join(',')!=='after,before,field'||!allowed.includes(d.field)||used.has(d.field)||same(d.before,d.after))throw new TypeError('INVALID_INTENDED_DIFFERENCE');used.add(d.field);
    if(!same(before.conditions[d.field],d.before)||!same(after.conditions[d.field],d.after))throw new TypeError('STALE_INTENDED_DIFFERENCE');
  }
  const differences=[],missing=[];
  for(const key of required){const a=before.conditions?.[key],b=after.conditions?.[key];
    if(absent(a)||absent(b)){missing.push(key);continue;}
    // UUID correspondence must be registered explicitly in both conditions, never guessed by proximity.
    if(!same(a,b)&&!used.has(key))differences.push({field:key,before:a,after:b});
  }
  for(const side of [before,after])if(side.conditions.subject?.uuid!==side.identity.subjectUuid)differences.push({field:'subject.uuid',reason:'IDENTITY_MAPPING_MISMATCH'});
  if(before.quality?.status!=='SAMPLING_GRID_COMPLETE'||after.quality?.status!=='SAMPLING_GRID_COMPLETE')missing.push('SAMPLING_COVERAGE');
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
