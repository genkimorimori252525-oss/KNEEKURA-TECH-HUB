import test from 'node:test';
import assert from 'node:assert/strict';
import {ownerPrelaunchFixture} from './owner-prelaunch-fixtures.mjs';
import {validateVisualExperimentRequest} from '../../evidence/visual-request-contract.mjs';
import {preparedOwner} from './owner-action-fixture.mjs';
import {readdir} from 'node:fs/promises';
import path from 'node:path';
const planning=await import('../camera-plan.mjs').catch(e=>{if(e.code==='ERR_MODULE_NOT_FOUND')return {};throw e;});
test('v2 request explicitly registers a four-image rig',async t=>{
 const f=await ownerPrelaunchFixture(t,null,'c'.repeat(40),r=>{r.visual_rig={mode:'tank-cardinal-4-snapshot-v2',fov:90,viewport:[640,480]};r.budgets.max_captures=4;});
 assert.equal(validateVisualExperimentRequest(f.bridgeContext.request).visual_rig.mode,'tank-cardinal-4-snapshot-v2');
});
test('retained camera-plan consumes no slots and preserves unknown occlusion',async t=>{
 const f=await preparedOwner(t,{capture:true,captureRig:'tank-cardinal-4-snapshot-v2',observation:true});
 const before=await readdir(path.join(f.runDir,'control')),plan=await planning.cameraPlan(f.controlOptions);
 assert.equal(plan.artifactRole,'DERIVED_PLANNING');assert.equal(plan.nativeReadSamplesConsumed,0);assert.equal(plan.imageSlotsConsumed,0);
 assert.equal(plan.captureSlots.length,1);assert.equal(plan.poses.length,4);assert(plan.poses.every(p=>p.insidePhysicalBounds&&p.occlusion.provenance==='UNKNOWN'));
 assert.deepEqual(await readdir(path.join(f.runDir,'control')),before);
});
test('fixed v2 predicted poses stay inside broad half-open room and do not claim native visibility',()=>{
 assert.equal(typeof planning.cardinalCameraPoses,'function');
 const poses=planning.cardinalCameraPoses('tank-cardinal-4-snapshot-v2',{min:[0,224,0],max:[52,248,52]});
 assert.deepEqual(poses.map(p=>p.eye),[[26,236,1.5],[50.5,236,26],[26,236,50.5],[1.5,236,26]]);
 assert.deepEqual(poses.map(p=>p.yaw),[0,90,180,-90]);
 assert.throws(()=>planning.cardinalCameraPoses('tank-cardinal-4-snapshot-v2',{min:[0,224,0],max:[3,248,52]}),/ROOM_TOO_SMALL/);
 const legacy=planning.cardinalCameraPoses('cardinal-4-snapshot-v1',{min:[7,224,6],max:[13,235,13]});
 assert.deepEqual(legacy[0].eye,[10,232.25,-3]);
});
