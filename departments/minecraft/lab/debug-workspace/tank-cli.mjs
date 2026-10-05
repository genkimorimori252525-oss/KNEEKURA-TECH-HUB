import path from 'node:path';
import {readRegisteredFile} from './bridge/materials.mjs';
import {decodeJson} from './bridge/json.mjs';
import {buildTankStatus} from './evidence/tank-status.mjs';
import {buildTankPreflight,requireTankTimeBudget} from './bridge/tank-preflight.mjs';
import {readInstalledControl} from './bridge/owner-action-adapter.mjs';
import {buildTankPresentationResource} from './bridge/tank-resource.mjs';
import {writeFile} from 'node:fs/promises';
import {requireTankObservations} from './evidence/tank-contract.mjs';

export async function readTankJsonFile(file) {
  const full=path.resolve(file),root=path.dirname(full);
  return decodeJson((await readRegisteredFile({root,relativePath:path.basename(full),maxBytes:256*1024})).bytes);
}
export async function prepareTankResourceFile({savedFile,profileFile,output}) {
  const artifact=buildTankPresentationResource({saved:await readTankJsonFile(savedFile),profile:await readTankJsonFile(profileFile)});
  await writeFile(path.resolve(output),artifact,{flag:'wx',mode:0o600});
  return {outputFile:path.resolve(output),artifactBytes:artifact.length,requiresNewRegistration:true,grantsAuthority:false};
}
export async function readTankContext({current,observations,arenaEpoch,expectedRecipeHash,worldBinding,profile,timeBudget}={}) {
  requireTankObservations(observations);
  const identity={debugSessionId:current.debugSessionId,runId:current.runId,runSnapshotId:current.runSnapshotId,processEpoch:current.processEpoch,arenaEpoch};
  let installed=null,ownerReason='LIVE_OWNER_NOT_CAPTURED';
  if(current.live===true&&current.ownerControlIntent?.envelopeHash) {
    try { installed=await readInstalledControl({runDir:current.runDir,envelopeHash:current.ownerControlIntent.envelopeHash}); }
    catch { ownerReason='CURRENT_OWNER_UNAVAILABLE'; }
  }
  const sameArena=installed?.control.arenaEpoch===arenaEpoch;
  const channels={};
  for(const row of observations)if(row.kind==='observation'&&['debugSessionId','runId','runSnapshotId','processEpoch','arenaEpoch'].every(k=>row[k]===identity[k])
      &&row.epistemicStatus==='OBSERVED'&&row.completeness?.complete===true&&row.source?.side==='SERVER')
    channels[row.lane]={status:'AVAILABLE',sourceObservationIds:[row.observationId],observedTick:row.gameTime??null,limitation:'RETAINED_SAMPLE_NOT_CONTINUOUS_COVERAGE'};
  const status=buildTankStatus({observations,identity,worldBinding,health:{channels},
    expected:{recipeHash:expectedRecipeHash,currentClock:sameArena?installed.status.runtimeClock:null}});
  if(!profile)return {status,ownerReason:installed&&sameArena?'CURRENT_SCOPED_OWNER':ownerReason};
  const requiredMs=requireTankTimeBudget(timeBudget),remaining=installed?.status.leaseRemainingMs;
  const ageMs=installed?Date.now()-Date.parse(installed.status.observedAt):NaN;
  const remainingMs=sameArena&&Number.isSafeInteger(remaining)&&ageMs>=0&&ageMs<=2000?Math.max(0,Math.floor(remaining-ageMs)):null;
  const leaseCheck={status:remainingMs===null?'UNKNOWN':remainingMs>=requiredMs?'SUFFICIENT':'INSUFFICIENT',remainingMs,requiredMs};
  return {status,preflight:buildTankPreflight({status,profile,requiredChannels:profile.decisionChannels,timeBudget,leaseCheck}),ownerReason};
}
