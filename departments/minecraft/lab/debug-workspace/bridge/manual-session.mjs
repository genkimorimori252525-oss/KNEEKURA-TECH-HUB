import assert from 'node:assert/strict';
import path from 'node:path';
import {validateDiagnostics} from '../../native-host/diagnostics.mjs';
import {validatePresentation} from '../../native-host/presentation.mjs';

const fields=['v','purpose','mode','nonce','playerUuid','subjectUuid','trialDir','worldDir','maxTicks','maxWallMs','maxEvents','captures','grants','sourceRevisions','productHash','adapterHash','installHash','materials'].sort();
const uuid=/^[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}$/i;
export function validateManualSession(value){
 assert(value&&typeof value==='object'&&!Array.isArray(value),'MANUAL_REQUEST_REQUIRED');
 const diagnostic=value.v===3,visual=diagnostic||value.v===2;assert.deepEqual(Object.keys(value).sort(),[...fields,...(visual?['presentation']:[]),...(diagnostic?['diagnostics']:[])].sort(),'MANUAL_EXACT_FIELDS');
 assert([1,2,3].includes(value.v));assert.equal(value.purpose,'MANUAL_INTERACTION');if(visual)validatePresentation(value.presentation);if(diagnostic)validateDiagnostics(value.diagnostics,value.maxWallMs);
 assert(['LIFECYCLE','MANUAL_RALLY','MANUAL_OBSERVE'].includes(value.mode),'MANUAL_MODE');
 for(const name of ['nonce','playerUuid','subjectUuid'])assert(typeof value[name]==='string'&&uuid.test(value[name]),'MANUAL_UUID_'+name);
 assert.notEqual(value.playerUuid,value.subjectUuid);
 for(const [name,max] of [['maxTicks',2400],['maxWallMs',120000],['maxEvents',512]])assert(Number.isInteger(value[name])&&value[name]>0&&value[name]<=max,'MANUAL_BOUND_'+name);
 assert.equal(value.captures,0);assert.deepEqual(value.grants,['MANUAL_EVENT_OBSERVATION',...(visual?['CLIENT_TANK_GRID_PRESENTATION']:[]),...(diagnostic?['FINITE_MOTION_DIAGNOSTICS']:[])]);
 assert.deepEqual(Object.keys(value.sourceRevisions).sort(),['target','techHub']);
 for(const [name,hash] of Object.entries(value.sourceRevisions))assert(name==='target'&&hash==='ARTIFACT_ONLY'||typeof hash==='string'&&/^[a-f0-9]{40}$/.test(hash),'MANUAL_SOURCE_PIN');
 for(const name of ['productHash','adapterHash','installHash'])assert(typeof value[name]==='string'&&/^[a-f0-9]{64}$/.test(value[name]),'MANUAL_MATERIAL_PIN');
 assert(Array.isArray(value.materials)&&value.materials.length<=32,'MANUAL_MATERIALS');const ids=new Set();
 for(const m of value.materials){assert.deepEqual(Object.keys(m).sort(),['id','sha256']);assert(typeof m.id==='string'&&/^[a-z][a-z0-9_]{1,63}$/.test(m.id)&&!ids.has(m.id)&&!['kneekura_manual_adapter','kneekura_tank_host'].includes(m.id),'MANUAL_MATERIAL_ID');ids.add(m.id);assert(typeof m.sha256==='string'&&/^[a-f0-9]{64}$/.test(m.sha256),'MANUAL_MATERIAL_HASH');}
 for(const name of ['trialDir','worldDir'])assert(typeof value[name]==='string'&&path.isAbsolute(value[name]),'MANUAL_ABSOLUTE_PATH');
 assert.equal(path.resolve(value.worldDir),path.join(path.resolve(value.trialDir),'game/saves/KNEEKURA_DEBUG_WORLD'),'MANUAL_PRIVATE_WORLD');
 return structuredClone(value);
}
export function manualBindingMatches(request,actual){
 validateManualSession(request);
 return actual?.connected===true&&actual.survival===true&&actual.fake===false&&actual.playerUuid===request.playerUuid&&typeof actual.worldDir==='string'&&path.resolve(actual.worldDir)===path.resolve(request.worldDir);
}
