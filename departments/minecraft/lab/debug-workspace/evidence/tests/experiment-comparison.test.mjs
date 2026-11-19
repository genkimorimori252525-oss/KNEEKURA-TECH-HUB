import test from 'node:test';
import assert from 'node:assert/strict';
import {compareExperimentDigests,compareExperimentVisualEvidence} from '../experiment-comparison.mjs';
const source=(revision='a'.repeat(40))=>({profile_id:'p',index_snapshot_id:'i',source_revision:revision,build_artifact_hash:'a'.repeat(64),dirty_hash:'b'.repeat(64),config_hash:'c'.repeat(64),resource_hash:'d'.repeat(64)});
const digest=()=>({schema:'kneekura.experiment-digest/v1',identity:{debugSessionId:'s',runId:'r',runSnapshotId:'snap',processEpoch:1,arenaEpoch:0,subjectUuid:'u'},
  conditions:{baselineHash:'b'.repeat(64),fixtureHash:'f'.repeat(64),worldBinding:{authorityHash:'a'.repeat(64),copyBaselineHash:'b'.repeat(64),fixtureHash:'f'.repeat(64)},sourceBinding:source(),subject:{subjectId:'A',entityType:'mob',uuid:'u'},observer:{channels:['SERVER_ENTITY_STATE'],sampleIntervalTicks:1,tickRate:20},presentation:{grid:false,brightness:false},alignment:{actionId:'start',operation:'wait_ticks',args:{ticks:1},windowStartOffset:0,windowEndOffset:300},initialState:[],actions:[],assertions:[{assertion_id:'a'}],windowDurationTicks:300},
  conditionEvidence:{source:'VERIFIED_REGISTERED_DISK_BINDING',world:'VERIFIED_RETAINED_EVIDENCE',observer:'VERIFIED_RETAINED_EVIDENCE',presentation:'VERIFIED_RETAINED_EVIDENCE',alignment:'VERIFIED_RETAINED_ACTION_EFFECT'},
  quality:{status:'SAMPLING_GRID_COMPLETE'},metrics:{observedDistance:{value:3}},registeredAssertions:[{assertion_id:'a',status:'INCONCLUSIVE'}]});
test('condition mismatch cannot be hidden by intentions, display differences or missing context',()=>{
  const a=digest(),b=digest();b.identity.runId='second';assert.equal(compareExperimentDigests({before:a,after:b}).status,'MATCHED_RETAINED_EVIDENCE');
  b.conditions.observer.tickRate=10;assert.equal(compareExperimentDigests({before:a,after:b}).status,'NON_COMPARABLE');
  assert.throws(()=>compareExperimentDigests({before:a,after:b,intendedDifferences:[{field:'*',before:20,after:10}]}),/INTENDED/);
  b.conditions.observer.tickRate=20;b.conditions.fixtureHash=null;assert.equal(compareExperimentDigests({before:a,after:b}).status,'INCONCLUSIVE');
});

test('relative action windows must match and declared conditions are not verified evidence',()=>{
  const a=digest(),b=digest();b.conditions.alignment.windowStartOffset=100;b.conditions.alignment.windowEndOffset=400;
  assert.equal(compareExperimentDigests({before:a,after:b}).status,'NON_COMPARABLE');
  b.conditions.alignment=a.conditions.alignment;b.conditionEvidence.world='UNVERIFIED';
  const out=compareExperimentDigests({before:a,after:b});assert.equal(out.status,'INCONCLUSIVE');assert(out.missingConditions.includes('WORLD_EVIDENCE'));
});

test('empty and partial nested conditions never establish matched evidence',()=>{
  for(const [field,value] of [['presentation',{}],['alignment',{}],['observer',{sampleIntervalTicks:1}],['worldBinding',{fixtureHash:'f'}],['sourceBinding',{}]]){
    const a=digest(),b=digest();a.conditions[field]=value;b.conditions[field]=value;
    const out=compareExperimentDigests({before:a,after:b});
    assert.equal(out.status,'INCONCLUSIVE',field);assert(out.missingConditions.includes(field));
  }
});
test('specific source intention stays exact and never means improvement',()=>{
  const a=digest(),b=digest();b.conditions.sourceBinding.source_revision='b'.repeat(40);
  assert.equal(compareExperimentDigests({before:a,after:b}).status,'NON_COMPARABLE');
  const out=compareExperimentDigests({before:a,after:b,intendedDifferences:[{field:'sourceBinding',before:source(),after:source('b'.repeat(40))}]});
  assert.equal(out.status,'MATCHED_RETAINED_EVIDENCE');assert.equal(out.improvement,'NOT_EVALUATED');
  b.quality.status='INCONCLUSIVE';assert.equal(compareExperimentDigests({before:a,after:b,intendedDifferences:out.intendedDifferences}).status,'INCONCLUSIVE');
});

test('appearance comparison requires both grid and brightness controls before canonical image work',async()=>{
  const out=await compareExperimentVisualEvidence({before:null,after:null,presentationBefore:{grid:true,brightness:false},presentationAfter:{grid:false,brightness:false}});
  assert.equal(out.status,'NON_COMPARABLE');assert.equal(out.reason,'GRID_OFF_BRIGHTNESS_OFF_CONTROLS_REQUIRED');
  const diagnostic=await compareExperimentVisualEvidence({before:null,after:null,presentationBefore:{grid:true,brightness:true},presentationAfter:{grid:false,brightness:false},displayDiagnostic:true});
  assert.equal(diagnostic.purpose,'DISPLAY_DIAGNOSTIC_NOT_APPEARANCE_ACCEPTANCE');assert.equal(diagnostic.comparison.status,'NON_COMPARABLE');
});
