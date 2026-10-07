/** Retained planning only: no server raycast, slot reservation or world read. */
import path from 'node:path';
import {lstat} from 'node:fs/promises';
import {integer,hashId} from './json.mjs';
import {readPreparedOwnerControl} from './owner-prelaunch.mjs';
import {readRegisteredFile} from './materials.mjs';
import {captureSlotKey} from './owner-action-adapter.mjs';
import {tankBounds} from './tank-observation.mjs';
import {decodeJson} from './json.mjs';
import {validateTankRoster} from './tank-roster.mjs';

function framing(pose,rig,entity){
 if(!entity)return {provenance:'UNKNOWN',cornersInside:null,totalCorners:8};
 const yaw=pose.yaw*Math.PI/180,pitch=pose.pitch*Math.PI/180,forward=[-Math.sin(yaw)*Math.cos(pitch),-Math.sin(pitch),Math.cos(yaw)*Math.cos(pitch)],right=[Math.cos(yaw),0,Math.sin(yaw)],up=[-Math.sin(yaw)*Math.sin(pitch),Math.cos(pitch),Math.cos(yaw)*Math.sin(pitch)];
 const vertical=Math.tan(rig.fov*Math.PI/360),horizontal=vertical*rig.viewport[0]/rig.viewport[1];let count=0;
 for(let i=0;i<8;i++){const d=entity.aabbMin.map((n,j)=>((i>>j)&1?entity.aabbMax[j]:n)-pose.eye[j]),dot=a=>d.reduce((sum,n,j)=>sum+n*a[j],0),depth=dot(forward);
  if(depth>=.05&&Math.abs(dot(right))<=depth*horizontal&&Math.abs(dot(up))<=depth*vertical)count++;}
 return {provenance:'PREDICTED_FROM_RETAINED_STATE',cornersInside:count,totalCorners:8,cameraInsideBody:pose.eye.every((n,i)=>n>=entity.aabbMin[i]&&n<=entity.aabbMax[i]),
  interpretation:'CORNER_PROJECTION_ONLY_NOT_PIXEL_VISIBILITY_OR_FRUSTUM_ABSENCE'};
}

export function cardinalCameraPoses(mode,bounds){
 const {min,max}=bounds;
 if(!Array.isArray(min)||!Array.isArray(max)||min.length!==3||max.length!==3)throw new Error('CAMERA_PLAN_BOUNDS');
 min.forEach(n=>integer(n,-30000000,30000000));max.forEach((n,i)=>integer(n,min[i]+1,min[i]+64));
 const [x,y,z]=min.map((n,i)=>(n+max[i])/2),tank=mode==='tank-cardinal-4-snapshot-v2';
 if(!tank&&mode!=='cardinal-4-snapshot-v1')throw new Error('CAMERA_PLAN_CARDINAL_RIG');
 if(tank&&(max[0]-min[0]<=3||max[2]-min[2]<=3))throw new Error('CAMERA_PLAN_ROOM_TOO_SMALL');
 const radius=Math.max(max[0]-min[0],max[2]-min[2])*1.5+2,elevation=Math.max(2,(max[1]-min[1])*.25);
 return ['north','east','south','west'].map((view,i)=>({view,
  eye:tank?[i===1?max[0]-1.5:i===3?min[0]+1.5:x,y,i===0?min[2]+1.5:i===2?max[2]-1.5:z]:[x+(i===1?radius:i===3?-radius:0),y+elevation,z+(i===0?-radius:i===2?radius:0)],
  yaw:i===3?-90:i*90,pitch:tank?0:Math.atan2(elevation,radius)*180/Math.PI}));
}
async function slot(runDir,file){try{const s=await lstat(path.join(runDir,file));if(s.isSymbolicLink())throw new Error('CAMERA_PLAN_SLOT_UNSAFE');return 'RESERVED_OR_RECORDED';}catch(e){if(e.code==='ENOENT')return 'AVAILABLE_DECLARED_SLOT';throw e;}}
export async function cameraPlan({runDir,envelopeHash}){
 hashId(envelopeHash);const p=await readPreparedOwnerControl({runDir,envelopeHash,requireSnapshot:true}),rig=p.request.visual_rig;
 const tank=p.tankObservation,poses=['cardinal-4-snapshot-v1','tank-cardinal-4-snapshot-v2'].includes(rig.mode)?cardinalCameraPoses(rig.mode,rig.mode==='tank-cardinal-4-snapshot-v2'?tank:p.grant.bounds):[];
 const captureSlots=[];if(poses.length)for(let i=0;i<Math.floor(p.grant.maxCaptures/4);i++)captureSlots.push({index:i,status:await slot(runDir,'control/captures/'+captureSlotKey(p.grant,i))});
 const roomSlots=[];if(tank)for(let i=0;i<tank.maxSamples;i++)roomSlots.push({index:i,status:await slot(runDir,'control/tank-roster/'+String(i).padStart(2,'0'))});
 let lastRoster=null,retained=null;
 if(tank)for(let i=tank.maxSamples-1;i>=0;i--){
  try{const r=decodeJson((await readRegisteredFile({root:runDir,relativePath:'control/tank-roster/'+String(i).padStart(2,'0')+'/receipt.json',maxBytes:65536})).bytes,65536);
   if(r.ownerEnvelopeHash===envelopeHash&&['COMPLETE','PARTIAL'].includes(r.status)){lastRoster={sampleIndex:i,serverTick:r.roster?.serverTick??null,status:r.status,basis:'RETAINED_RECEIPT_NOT_CURRENT_WORLD'};break;}
  }catch(e){if(e.code!=='ENOENT')throw e;}
 }
 if(tank)try{
  const raw=(await readRegisteredFile({root:runDir,relativePath:'evidence/observations.jsonl',maxBytes:16*1024*1024})).bytes.toString('utf8');
  for(const line of raw.split('\n').filter(Boolean)){
   const row=decodeJson(Buffer.from(line),128*1024);if(row.lane!=='TANK_ROOM_ROSTER'||row.payload?.ownerEnvelopeHash!==envelopeHash)continue;
   const candidate=validateTankRoster(row.payload,{...p,envelopeHash},row.payload.sampleIndex);
   if(retained===null||candidate.serverTick>retained.payload.serverTick)retained={observationId:row.observationId,payload:candidate};
  }
 }catch(e){if(e.code!=='ENOENT')throw e;}
 return {schemaVersion:1,artifactRole:'DERIVED_PLANNING',rig:structuredClone(rig),requestHash:p.envelope.requestHash,ownerEnvelopeHash:envelopeHash,
  subjects:p.request.subjects.map(s=>({...s})),actionBounds:structuredClone(p.grant.bounds),tankBounds:tank?tankBounds(tank):null,tankObservationHash:p.envelope.tankObservationHash??null,
  poses:poses.map(pose=>({...pose,fov:rig.fov,viewport:[...rig.viewport],geometryBasis:'REGISTERED_BOUNDS_PREDICTION',insidePhysicalBounds:tank?pose.eye.every((n,i)=>n>=tank.min[i]-1&&n<tank.max[i]+1):null,
   occlusion:{provenance:'UNKNOWN',visibility:'UNKNOWN'},framing:{sourceObservationId:retained?.observationId??null,sourceServerTick:retained?.payload.serverTick??null,
    subjects:p.request.subjects.map(s=>({uuid:s.uuid,...framing(pose,rig,retained?.payload.entities.find(e=>e.uuid===s.uuid&&e.entityType===s.entity_type))}))}})),
  captureSlots,roomReadSlots:roomSlots,lastRetainedRoster:lastRoster,nativeReadSamplesConsumed:0,imageSlotsConsumed:0,
  freshness:'RETAINED_INPUTS_ONLY_CURRENT_WORLD_UNKNOWN',execution:'NOT_RUN',authority:'NO_ADDITIONAL_AUTHORITY'};
}
