import test from 'node:test';
import assert from 'node:assert/strict';
import {compareExperimentDigests,compareExperimentVisualEvidence} from '../experiment-comparison.mjs';
const digest=()=>({schema:'kneekura.experiment-digest/v1',identity:{debugSessionId:'s',runId:'r',runSnapshotId:'snap',processEpoch:1,arenaEpoch:0,subjectUuid:'u'},
  conditions:{baselineHash:'b',fixtureHash:'f',worldBinding:{authorityHash:'a',copyBaselineHash:'b',fixtureHash:'f'},sourceBinding:{revision:'a'},subject:{subjectId:'A',entityType:'mob',uuid:'u'},observer:{channels:['SERVER_ENTITY_STATE'],sampleIntervalTicks:1,tickRate:20},presentation:{grid:false,brightness:false},alignment:{actionReceiptHash:'h',anchorTick:0},initialState:[],actions:[],assertions:[{assertion_id:'a'}],windowDurationTicks:300},
  quality:{status:'SAMPLING_GRID_COMPLETE'},metrics:{observedDistance:{value:3}},registeredAssertions:[{assertion_id:'a',status:'INCONCLUSIVE'}]});
test('condition mismatch cannot be hidden by intentions, display differences or missing context',()=>{
  const a=digest(),b=digest();b.identity.runId='second';assert.equal(compareExperimentDigests({before:a,after:b}).status,'MATCHED_RETAINED_EVIDENCE');
  b.conditions.observer.tickRate=10;assert.equal(compareExperimentDigests({before:a,after:b}).status,'NON_COMPARABLE');
  assert.throws(()=>compareExperimentDigests({before:a,after:b,intendedDifferences:[{field:'*',before:20,after:10}]}),/INTENDED/);
  b.conditions.observer.tickRate=20;b.conditions.fixtureHash=null;assert.equal(compareExperimentDigests({before:a,after:b}).status,'INCONCLUSIVE');
});
test('specific source intention stays exact and never means improvement',()=>{
  const a=digest(),b=digest();b.conditions.sourceBinding.revision='b';
  assert.equal(compareExperimentDigests({before:a,after:b}).status,'NON_COMPARABLE');
  const out=compareExperimentDigests({before:a,after:b,intendedDifferences:[{field:'sourceBinding',before:{revision:'a'},after:{revision:'b'}}]});
  assert.equal(out.status,'MATCHED_RETAINED_EVIDENCE');assert.equal(out.improvement,'NOT_EVALUATED');
  b.quality.status='INCONCLUSIVE';assert.equal(compareExperimentDigests({before:a,after:b,intendedDifferences:out.intendedDifferences}).status,'INCONCLUSIVE');
});

test('appearance comparison requires both grid and brightness controls before canonical image work',async()=>{
  const out=await compareExperimentVisualEvidence({before:null,after:null,presentationBefore:{grid:true,brightness:false},presentationAfter:{grid:false,brightness:false}});
  assert.equal(out.status,'NON_COMPARABLE');assert.equal(out.reason,'GRID_OFF_BRIGHTNESS_OFF_CONTROLS_REQUIRED');
  const diagnostic=await compareExperimentVisualEvidence({before:null,after:null,presentationBefore:{grid:true,brightness:true},presentationAfter:{grid:false,brightness:false},displayDiagnostic:true});
  assert.equal(diagnostic.purpose,'DISPLAY_DIAGNOSTIC_NOT_APPEARANCE_ACCEPTANCE');assert.equal(diagnostic.comparison.status,'NON_COMPARABLE');
});
