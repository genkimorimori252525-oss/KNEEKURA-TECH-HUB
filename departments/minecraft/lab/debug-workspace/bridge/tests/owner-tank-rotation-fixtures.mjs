import {sha256,stableJson} from '../json.mjs';
import {writeFile} from 'node:fs/promises';
import path from 'node:path';
import {ownerPrelaunchFixture} from './owner-prelaunch-fixtures.mjs';
import {TANK_ROTATION_PERMISSION} from '../owner-tank-rotation.mjs';

const identity = {debugSessionId:'s',runId:'r',runSnapshotId:'snapshot',processEpoch:1,handshakeNonce:'n'.repeat(32)};
export function recipe(origin = {x:0,y:224,z:0}, dimensions = {width:19,height:11,depth:19}, preset = 'wide') {
  return {v:1,kind:'tank_recipe',preset,dimensions,origin,dimension:'minecraft:overworld',shellBlock:'minecraft:black_concrete',
    environment:{difficulty:'normal',time:6000,daylightCycle:false,weatherCycle:false,weather:'clear',mobSpawning:false},presentation:{mode:'OBSERVATION_BRIGHT',gridSpacing:1}};
}
export function rotationFixture() {
  const previousRecipe = recipe(), nextRecipe = recipe({x:80,y:224,z:0},{width:9,height:7,depth:9},'narrow');
  const owner = {status:'GEOMETRY_VERIFIED',recipe:previousRecipe,recipeHash:'sha256:'+sha256(stableJson(previousRecipe)),arenaEpoch:8,reservedRegions:[]};
  const previousOwnerBytes = Buffer.from(stableJson(owner));
  const grant = {...identity,requestHash:'a'.repeat(64),grantId:'grant',leaseId:'lease',arenaId:'arena',arenaEpoch:0,expectedArenaRevision:0,maxActions:0,maxCaptures:0,allowedActions:[],dimensionId:'minecraft:overworld'};
  const request = {initial_state:[],actions:[],visual_rig:{mode:'none'},budgets:{max_actions:0,max_captures:0}};
  const world = {dimensionId:'minecraft:overworld',permissions:['BOUNDED_DIAGNOSTIC_CONTROL',TANK_ROTATION_PERMISSION]};
  const plan = {schemaVersion:1,scope:TANK_ROTATION_PERMISSION,rotationId:'rotation',...identity,requestHash:grant.requestHash,grantId:'grant',leaseId:'lease',arenaId:'arena',
    expectedArenaEpoch:0,expectedArenaRevision:0,previousOwnerFileSha256:sha256(previousOwnerBytes),previousRecipeHash:sha256(stableJson(previousRecipe)),previousTankEpoch:8,nextRecipeHash:sha256(stableJson(nextRecipe)),nextRecipe};
  return {plan,context:{identity,grant,request,world,triggerCapture:null,previousOwnerBytes},owner};
}
export async function maintenance(t,suppliedRoot=null,sourceRevision='c'.repeat(40)) {
  const f=await ownerPrelaunchFixture(t,suppliedRoot,sourceRevision,r=>{r.actions=[];r.budgets.max_actions=0;r.budgets.time_budget_ms=120000;});
  f.operator.selection.allowedActions=[];f.operator.worldRegistration.permissions.push(TANK_ROTATION_PERMISSION);
  const rotation=rotationFixture();const plan={...rotation.plan,...f.identity,requestHash:f.bridgeContext.binding.request_hash,arenaId:f.bridgeContext.request.arena.arena_id};
  await writeFile(path.join(f.operator.worldRegistration.canonicalWorldRoot,'kneekura-tank-owner.json'),rotation.context.previousOwnerBytes);
  f.operator.tankRotation=Object.fromEntries(['schemaVersion','scope','rotationId','previousOwnerFileSha256','previousRecipeHash','previousTankEpoch','nextRecipeHash','nextRecipe'].map(key=>[key,plan[key]]));
  f.options.operatorRegistration=await f.select();return {...f,previousOwnerBytes:rotation.context.previousOwnerBytes};
}
