import test from 'node:test';
import assert from 'node:assert/strict';
import {sha256, stableJson} from '../json.mjs';
import {writeFile, readFile, readdir} from 'node:fs/promises';
import path from 'node:path';
import {prepareOwnerControl, readPreparedOwnerControl} from '../owner-prelaunch.mjs';
import {recipe,rotationFixture,maintenance} from './owner-tank-rotation-fixtures.mjs';
import {TANK_ROTATION_PERMISSION, validateTankRotation} from '../owner-tank-rotation.mjs';

test('private rotation selection is sealed with fresh launch identity instead of preselected runtime authority', async t => {
  const f=await maintenance(t);
  for(const key of ['debugSessionId','runId','runSnapshotId','processEpoch','handshakeNonce','requestHash','grantId','leaseId','arenaId','expectedArenaEpoch','expectedArenaRevision'])delete f.operator.tankRotation[key];
  f.options.identity={debugSessionId:'fresh-session',runId:'fresh-run',runSnapshotId:'fresh-snapshot',processEpoch:2,handshakeNonce:'b'.repeat(32)};
  f.options.operatorRegistration=await f.select();const prepared=await prepareOwnerControl(f.options);
  for(const [key,value] of Object.entries(f.options.identity))assert.equal(prepared.tankRotation[key],value);
  assert.equal(prepared.tankRotation.grantId,prepared.grant.grantId);assert.equal(prepared.tankRotation.requestHash,prepared.grant.requestHash);
});

test('maintenance cannot dispatch or authorize experiment actions/captures/triggers', () => {
  for (const change of [c=>c.request.actions.push({operation:'set_block'}),c=>c.request.initial_state.push({operation:'wait_ticks'}),c=>c.grant.maxActions=1,
    c=>c.grant.allowedActions.push('set_block'),c=>c.grant.maxCaptures=4,c=>c.request.budgets.max_captures=4,c=>c.request.visual_rig.mode='cardinal-4-snapshot-v1',c=>c.triggerCapture={}]) {
    const f=rotationFixture();change(f.context);assert.throws(()=>validateTankRotation(f.plan,f.context));
  }
});
test('valid disjoint maintenance remains pure exact intent and preserves different Arena and Tank epochs', () => {
  const f=rotationFixture(),copy=validateTankRotation(f.plan,f.context);assert.deepEqual(copy,f.plan);assert.notEqual(copy,f.plan);
  assert.equal(copy.expectedArenaEpoch,0);assert.equal(copy.previousTankEpoch,8);assert.equal(Object.hasOwn(copy,'runtimeAccepted'),false);
});
test('exact sealed identity, hash, scope and field union rejects stale or additional input', () => {
  for(const key of ['debugSessionId','runId','runSnapshotId','processEpoch','handshakeNonce','requestHash','grantId','leaseId','arenaId','expectedArenaEpoch','expectedArenaRevision',
    'previousOwnerFileSha256','previousRecipeHash','previousTankEpoch','nextRecipeHash','scope','schemaVersion']) {
    const f=rotationFixture();f.plan[key]=typeof f.plan[key]==='number'?f.plan[key]+1:'wrong';assert.throws(()=>validateTankRotation(f.plan,f.context),key);
  }
  for(const key of ['command','ttlMs','runtimeAccepted']){const f=rotationFixture();f.plan[key]=true;assert.throws(()=>validateTankRotation(f.plan,f.context));}
});
test('permission, owner cleanliness and complete saved-owner raw bytes remain mandatory', () => {
  for(const fault of ['permission','ownerBytes','status','epoch','recipe','reservations']) {
    const f=rotationFixture();if(fault==='permission')f.context.world.permissions.pop();
    else if(fault==='ownerBytes')f.context.previousOwnerBytes=Buffer.from('other');
    else {if(fault==='status')f.owner.status='OUTCOME_UNKNOWN';if(fault==='epoch')f.owner.arenaEpoch=9;if(fault==='recipe')f.owner.recipeHash='b'.repeat(64);if(fault==='reservations')f.owner.reservedRegions=Array(16).fill(recipe({x:0,y:64,z:0}));f.context.previousOwnerBytes=Buffer.from(stableJson(f.owner));f.plan.previousOwnerFileSha256=sha256(f.context.previousOwnerBytes);}
    assert.throws(()=>validateTankRotation(f.plan,f.context),fault);
  }
});
test('shell overlap covers current and every prior region, including shared boundary cells', () => {
  for(const x of [0,18,20]) {const f=rotationFixture();f.plan.nextRecipe.origin.x=x;f.plan.nextRecipeHash=sha256(stableJson(f.plan.nextRecipe));assert.throws(()=>validateTankRotation(f.plan,f.context));}
  const f=rotationFixture();f.owner.reservedRegions=[recipe({x:80,y:224,z:0})];f.context.previousOwnerBytes=Buffer.from(stableJson(f.owner));f.plan.previousOwnerFileSha256=sha256(f.context.previousOwnerBytes);assert.throws(()=>validateTankRotation(f.plan,f.context));
});
test('dimensions, allocated shell, exact recipe and overworld boundaries are independently bounded', () => {
  for(const mutate of [r=>r.dimensions.width=65,r=>r.dimensions.height=0,r=>{r.preset='custom';r.dimensions={width:64,height:64,depth:64};},r=>r.origin.y=-64,r=>r.origin.y=319,
    r=>r.origin.x=Number.MAX_SAFE_INTEGER,r=>r.presentation.gridSpacing=2,r=>r.environment.mobSpawning=true,r=>r.shellBlock='minecraft:lava',r=>r.extra=true,r=>r.dimensions.width=9.5,r=>r.dimension='minecraft:the_nether']) {
    const f=rotationFixture();mutate(f.plan.nextRecipe);f.plan.nextRecipeHash=sha256(stableJson(f.plan.nextRecipe));assert.throws(()=>validateTankRotation(f.plan,f.context));
  }
});
test('counter exhaustion, duplicate source keys and oversized saved owner are rejected', () => {
  const exhausted=rotationFixture();exhausted.owner.arenaEpoch=Number.MAX_SAFE_INTEGER;exhausted.plan.previousTankEpoch=Number.MAX_SAFE_INTEGER;exhausted.context.previousOwnerBytes=Buffer.from(stableJson(exhausted.owner));exhausted.plan.previousOwnerFileSha256=sha256(exhausted.context.previousOwnerBytes);assert.throws(()=>validateTankRotation(exhausted.plan,exhausted.context));
  for(const bytes of [Buffer.from('{"status":"GEOMETRY_VERIFIED","status":"GEOMETRY_VERIFIED"}'),Buffer.alloc(65537)]) {const f=rotationFixture();f.context.previousOwnerBytes=bytes;f.plan.previousOwnerFileSha256=sha256(bytes);assert.throws(()=>validateTankRotation(f.plan,f.context));}
});

test('prelaunch seals maintenance and its complete predecessor without runtime attestation', async t => {
  const f=await maintenance(t),prepared=await prepareOwnerControl(f.options);
  assert.equal(prepared.envelope.tankRotationHash,sha256(stableJson(prepared.tankRotation)));
  for(const [key,value] of Object.entries(f.operator.tankRotation))assert.deepEqual(prepared.tankRotation[key],value);
  assert.deepEqual(await readFile(path.join(f.runDir,'control/owner-tank-predecessor.json')),f.previousOwnerBytes);
  assert.equal(prepared.ownerControlIntent.fullTargetAttestation,'NOT_ESTABLISHED');
  // Immutable preparation remains readable after the live owner advances; it does not attest that world state.
  await writeFile(path.join(f.operator.worldRegistration.canonicalWorldRoot,'kneekura-tank-owner.json'),'new owner');
  assert.deepEqual((await readPreparedOwnerControl({runDir:f.runDir,envelopeHash:prepared.envelopeHash})).tankRotation,prepared.tankRotation);
  await writeFile(path.join(f.runDir,'control/owner-tank-predecessor.json'),'altered');
  await assert.rejects(readPreparedOwnerControl({runDir:f.runDir,envelopeHash:prepared.envelopeHash}));
});
test('private selection rejects run identity, lease override or additional commands before owner writes', async t => {
  for(const key of ['runId','leaseId','expectedArenaEpoch','ttlMs','command']){
    const f=await maintenance(t);f.operator.tankRotation[key]=key==='expectedArenaEpoch'?1:'override';f.options.operatorRegistration=await f.select();
    await assert.rejects(prepareOwnerControl(f.options),/PRIVATE_TANK_ROTATION/);assert.deepEqual(await readdir(f.runDir),[]);
  }
});
test('prelaunch refuses an unpermitted or changed predecessor before writing the owner closure', async t => {
  for(const fault of ['permission','previousOwner']) {
    const f=await maintenance(t);if(fault==='permission'){f.operator.worldRegistration.permissions.pop();f.options.operatorRegistration=await f.select();}
    else await writeFile(path.join(f.operator.worldRegistration.canonicalWorldRoot,'kneekura-tank-owner.json'),'changed');
    await assert.rejects(prepareOwnerControl(f.options));assert.deepEqual(await readdir(f.runDir),[]);
  }
});
