/** Sealed maintenance intent only; parsing never grants runtime authority. */
import {exactKeys, identifier, integer, hashId, decodeJson, sha256, stableJson} from './json.mjs';
export const TANK_ROTATION_PERMISSION = 'PRE_EXPERIMENT_TANK_ROTATION';
const IDENTITY = ['debugSessionId','runId','runSnapshotId','processEpoch','handshakeNonce'];
const FIELDS = ['schemaVersion','scope','rotationId',...IDENTITY,'requestHash','grantId','leaseId','arenaId','expectedArenaEpoch','expectedArenaRevision',
  'previousOwnerFileSha256','previousRecipeHash','previousTankEpoch','nextRecipeHash','nextRecipe'];
function require(value, reason) { if (!value) throw new Error(reason); }
function recipeHash(value) { return sha256(stableJson(value)); }
function savedHash(value) { return hashId(typeof value === 'string' && value.startsWith('sha256:') ? value.slice(7) : value); }

/** Private prelaunch selection cannot predict or override runtime identity; the existing owner seals it. */
export function buildTankRotationIntent(selection, context) {
  exactKeys(selection,['schemaVersion','scope','rotationId','previousOwnerFileSha256','previousRecipeHash','previousTankEpoch','nextRecipeHash','nextRecipe'],'PRIVATE_TANK_ROTATION');
  const {identity,grant}=context;
  return validateTankRotation({...selection,...identity,requestHash:grant.requestHash,grantId:grant.grantId,leaseId:grant.leaseId,arenaId:grant.arenaId,
    expectedArenaEpoch:grant.arenaEpoch,expectedArenaRevision:grant.expectedArenaRevision},context);
}

/** Pure source geometry, including the inclusive shell. No chunk/world query. */
export function validateRotationRecipe(value) {
  exactKeys(value,['v','kind','preset','dimensions','origin','dimension','shellBlock','environment','presentation'],'TANK_ROTATION_RECIPE');
  require(value.v === 1 && value.kind === 'tank_recipe' && value.dimension === 'minecraft:overworld' && value.shellBlock === 'minecraft:black_concrete','TANK_ROTATION_RECIPE_SCOPE');
  exactKeys(value.dimensions,['width','height','depth'],'TANK_ROTATION_DIMENSIONS');
  const {width,height,depth} = value.dimensions;
  for (const dimension of [width,height,depth]) integer(dimension,1,64);
  require(width * height * depth <= 65536 && (width+2)*(height+2)*(depth+2) <= 100000,'TANK_ROTATION_VOLUME_LIMIT');
  const presets = {narrow:[9,7,9],normal:[17,11,17],wide:[19,11,19]};
  require(value.preset === 'custom' || Object.hasOwn(presets,value.preset) && stableJson(presets[value.preset]) === stableJson([width,height,depth]),'TANK_ROTATION_PRESET_MISMATCH');
  exactKeys(value.origin,['x','y','z'],'TANK_ROTATION_ORIGIN');
  const {x,y,z} = value.origin;
  integer(x,-29999983,29999983);integer(z,-29999983,29999983);integer(y,-63,318);
  require(x+width <= 29999984 && z+depth <= 29999984 && y+height <= 319,'TANK_ROTATION_BUILD_BOUNDS');
  exactKeys(value.environment,['difficulty','time','daylightCycle','weatherCycle','weather','mobSpawning'],'TANK_ROTATION_ENVIRONMENT');
  require(stableJson(value.environment) === stableJson({difficulty:'normal',time:6000,daylightCycle:false,weatherCycle:false,weather:'clear',mobSpawning:false}),'TANK_ROTATION_ENVIRONMENT_RECIPE');
  exactKeys(value.presentation,['mode','gridSpacing'],'TANK_ROTATION_PRESENTATION');
  require(['OBSERVATION_BRIGHT','NATIVE'].includes(value.presentation.mode) && value.presentation.gridSpacing === 1,'TANK_ROTATION_PRESENTATION_SCOPE');
  return {min:[x-1,y-1,z-1],max:[x+width,y+height,z+depth]};
}
function overlaps(a,b) { return a.min.every((v,i) => v <= b.max[i] && b.min[i] <= a.max[i]); }

/** Optional permission and sealed plan supplement, never expand, the existing diagnostic grant. */
export function validateTankRotation(value, {identity,grant,request,world,triggerCapture,previousOwnerBytes}) {
  exactKeys(value,FIELDS,'TANK_ROTATION');integer(value.schemaVersion,1,1);
  require(value.scope === TANK_ROTATION_PERMISSION,'TANK_ROTATION_SCOPE');identifier(value.rotationId);
  for (const key of IDENTITY) {
    if (key === 'processEpoch') integer(value[key],1,2147483647); else identifier(value[key]);
    require(value[key] === identity[key] && value[key] === grant[key],'TANK_ROTATION_IDENTITY_MISMATCH');
  }
  require(value.handshakeNonce.length >= 16,'TANK_ROTATION_NONCE');
  for (const key of ['grantId','leaseId','arenaId']) { identifier(value[key]);require(value[key] === grant[key],'TANK_ROTATION_GRANT_MISMATCH'); }
  for (const key of ['requestHash','previousOwnerFileSha256','previousRecipeHash','nextRecipeHash']) hashId(value[key]);
  require(value.requestHash === grant.requestHash,'TANK_ROTATION_REQUEST_MISMATCH');
  integer(value.expectedArenaEpoch,0,Number.MAX_SAFE_INTEGER);integer(value.expectedArenaRevision,0,Number.MAX_SAFE_INTEGER);
  require(value.expectedArenaEpoch === grant.arenaEpoch && value.expectedArenaRevision === grant.expectedArenaRevision,'TANK_ROTATION_ARENA_MISMATCH');
  integer(value.previousTankEpoch,0,Number.MAX_SAFE_INTEGER-1);
  require(world.dimensionId === 'minecraft:overworld' && grant.dimensionId === world.dimensionId && Array.isArray(world.permissions) && world.permissions.includes(TANK_ROTATION_PERMISSION),'TANK_ROTATION_PERMISSION_MISSING');
  require(grant.maxActions === 0 && grant.maxCaptures === 0 && Array.isArray(grant.allowedActions) && grant.allowedActions.length === 0 &&
    request.budgets?.max_actions === 0 && request.budgets?.max_captures === 0 && Array.isArray(request.actions) && request.actions.length === 0 &&
    Array.isArray(request.initial_state) && request.initial_state.length === 0 && request.visual_rig?.mode === 'none' && triggerCapture == null,'TANK_ROTATION_MAINTENANCE_ONLY');
  require(Buffer.isBuffer(previousOwnerBytes) && previousOwnerBytes.length <= 65536 && sha256(previousOwnerBytes) === value.previousOwnerFileSha256,'TANK_ROTATION_SAVED_OWNER_BYTES_MISMATCH');
  const owner = decodeJson(previousOwnerBytes,65536);
  require(owner.status === 'GEOMETRY_VERIFIED' && owner.arenaEpoch === value.previousTankEpoch,'TANK_ROTATION_SAVED_OWNER_STATE');
  require(savedHash(owner.recipeHash) === value.previousRecipeHash && recipeHash(owner.recipe) === value.previousRecipeHash,'TANK_ROTATION_PREDECESSOR_RECIPE_MISMATCH');
  const prior = owner.reservedRegions ?? [];
  require(Array.isArray(prior) && prior.length < 16,'TANK_ROTATION_RESERVATION_LIMIT');
  const next = validateRotationRecipe(value.nextRecipe);
  require(recipeHash(value.nextRecipe) === value.nextRecipeHash,'TANK_ROTATION_NEXT_RECIPE_HASH_MISMATCH');
  for (const recipe of [...prior,owner.recipe]) require(!overlaps(next,validateRotationRecipe(recipe)),'TANK_ROTATION_RESERVED_REGION_OVERLAP');
  return structuredClone(value);
}
