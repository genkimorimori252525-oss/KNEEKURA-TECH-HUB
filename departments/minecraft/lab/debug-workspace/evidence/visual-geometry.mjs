import { exactKeys } from '../bridge/json.mjs';
const FONT = {
 A:['010','101','111','101','101'], B:['110','101','110','101','110'], C:['011','100','100','100','011'],
 D:['110','101','101','101','110'], E:['111','100','110','100','111'], F:['111','100','110','100','100'],
 G:['011','100','101','101','011'], H:['101','101','111','101','101'], I:['111','010','010','010','111'],
 J:['001','001','001','101','010'], K:['101','101','110','101','101'], L:['100','100','100','100','111'],
 M:['101','111','111','101','101'], N:['101','111','111','111','101'], O:['010','101','101','101','010'],
 P:['110','101','110','100','100'], Q:['010','101','101','111','011'], R:['110','101','110','101','101'],
 S:['011','100','010','001','110'], T:['111','010','010','010','010'], U:['101','101','101','101','111'],
 V:['101','101','101','101','010'], W:['101','101','111','111','101'], X:['101','101','010','101','101'],
 Y:['101','101','010','010','010'], Z:['111','001','010','100','111'],
};
export const escapeXml = value => String(value).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
export function canvas(width,height,color=[20,25,33,255]) {
  const rgba = new Uint8Array(width*height*4);
  for(let i=0;i<rgba.length;i+=4) rgba.set(color,i);
  return {width,height,rgba};
}
export function pixel(image,x,y,color) {
  x=Math.round(x); y=Math.round(y);
  if(x>=0&&y>=0&&x<image.width&&y<image.height) image.rgba.set(color,(y*image.width+x)*4);
}
export function text(image,value,x,y,color=[255,255,255,255]) {
  for(const character of value) { const rows=FONT[character]??[];
    rows.forEach((row,j)=>[...row].forEach((v,i)=>{if(v==='1')pixel(image,x+i,y+j,color);}));x+=4; }
}
export function line(image,x1,y1,x2,y2,color=[255,190,60,255]) {
  const count=Math.ceil(Math.max(Math.abs(x2-x1),Math.abs(y2-y1)));
  if(count>8192)return;
  for(let i=0;i<=count;i++) {const t=count?i/count:0;pixel(image,x1+t*(x2-x1),y1+t*(y2-y1),color);}
}
export function blit(destination,source,x,y) {
  for(let row=0;row<source.height;row++) destination.rgba.set(source.rgba.subarray(row*source.width*4,(row+1)*source.width*4),((y+row)*destination.width+x)*4);
}
export function validateFacts(facts,subjects) {
  exactKeys(facts,['dimension','gameTime','arenaBounds','subjects',...(Object.hasOwn(facts,'observationBounds')?['observationBounds']:[])],'STRUCTURED_STATE');
  if(typeof facts.dimension!=='string'||!/^\w+:[a-z0-9_./-]+$/.test(facts.dimension)||!Number.isSafeInteger(facts.gameTime)||facts.gameTime<0) throw new TypeError('INVALID_STRUCTURED_STATE');
  const vector=(v,n)=>{if(!Array.isArray(v)||v.length!==n||v.some(x=>!Number.isFinite(x)||Math.abs(x)>30000000))throw new TypeError('INVALID_STRUCTURED_VECTOR');};
  if(facts.observationBounds){exactKeys(facts.observationBounds,['min','max'],'OBSERVATION_BOUNDS');vector(facts.observationBounds.min,3);vector(facts.observationBounds.max,3);if(facts.observationBounds.min.some((n,i)=>facts.observationBounds.max[i]<=n||facts.observationBounds.max[i]-n>64))throw new TypeError('INVALID_OBSERVATION_BOUNDS');}
  exactKeys(facts.arenaBounds,['min','max'],'ARENA_BOUNDS');
  vector(facts.arenaBounds.min,3);vector(facts.arenaBounds.max,3);
  if(facts.arenaBounds.min.some((v,i)=>facts.arenaBounds.max[i]<=v))throw new TypeError('INVALID_ARENA_BOUNDS');
  if(!Array.isArray(facts.subjects)||facts.subjects.length!==subjects.length||new Set(facts.subjects.map(s=>s.uuid)).size!==subjects.length) throw new TypeError('STRUCTURED_SUBJECTS_REQUIRED');
  for(const s of facts.subjects) {
    exactKeys(s,['uuid','position','velocity','yaw','pitch','bounds'],'STRUCTURED_SUBJECT');
    if(!subjects.includes(s.uuid))throw new TypeError('STRUCTURED_SUBJECT_MISMATCH');
    vector(s.position,3);vector(s.velocity,3);vector(s.bounds,6);
    if(!Number.isFinite(s.yaw)||!Number.isFinite(s.pitch)||s.bounds.slice(0,3).some((v,i)=>s.bounds[i+3]<v))throw new TypeError('INVALID_SUBJECT_BOUNDS');
  }
  return structuredClone(facts);
}
/** Exact renderer matrix; world coordinates are first made camera-relative. */
export function project(point,camera) {
  if(camera.matrixConvention!=='JOML_COLUMN_MAJOR_CAMERA_RELATIVE')throw new TypeError('UNSUPPORTED_MATRIX_CONVENTION');
  const v=[...point.map((n,i)=>n-camera.position[i]),1];
  const multiply=(matrix,vector)=>Array.from({length:4},(_,row)=>vector.reduce((sum,n,col)=>sum+n*matrix[col*4+row],0));
  const clip=multiply(camera.projectionMatrix,multiply(camera.viewMatrix,v));
  if(clip.some(n=>!Number.isFinite(n))||clip[3]<=0)return null;
  const ndc=clip.slice(0,3).map(n=>n/clip[3]);
  if(ndc[2]<-1||ndc[2]>1)return null;
  return {x:(ndc[0]+1)*camera.viewport[0]/2,y:(1-ndc[1])*camera.viewport[1]/2,inside:Math.abs(ndc[0])<=1&&Math.abs(ndc[1])<=1};
}
export function annotatedImage(image,frame,facts,labels) {
  const out={...image,rgba:Uint8Array.from(image.rgba)}; const annotations=[];
  for(const s of facts.subjects) {
    const label=labels.find(l=>l.uuid===s.uuid).label;
    const points=[];
    for(const x of [s.bounds[0],s.bounds[3]])for(const y of [s.bounds[1],s.bounds[4]])for(const z of [s.bounds[2],s.bounds[5]])points.push(project([x,y,z],frame.camera));
    const visible=points.filter(p=>p&&p.inside);
    if(points.some(p=>!p)||!visible.length) {annotations.push({uuid:s.uuid,label,projectionStatus:'CLIPPED_OR_OUTSIDE',visibility:'NOT_INFERRED'});continue;}
    const xs=points.map(p=>p.x),ys=points.map(p=>p.y);
    const rect={x:Math.max(0,Math.min(...xs)),y:Math.max(0,Math.min(...ys)),right:Math.min(image.width-1,Math.max(...xs)),bottom:Math.min(image.height-1,Math.max(...ys))};
    line(out,rect.x,rect.y,rect.right,rect.y);line(out,rect.right,rect.y,rect.right,rect.bottom);
    line(out,rect.right,rect.bottom,rect.x,rect.bottom);line(out,rect.x,rect.bottom,rect.x,rect.y);
    text(out,label,rect.x+2,Math.max(0,rect.y-7));
    annotations.push({uuid:s.uuid,label,projectionStatus:'PROJECTED_BOUNDS',visibility:'NOT_INFERRED',rect,camera:structuredClone(frame.camera)});
  }
  return {image:out,annotations};
}
export function topDownSvg(facts,labels) {
  const b=facts.observationBounds??facts.arenaBounds; const scale=440/Math.max(b.max[0]-b.min[0],b.max[2]-b.min[2]);
  const x=v=>40+(v-b.min[0])*scale, z=v=>40+(v-b.min[2])*scale;
  const geometry=facts.subjects.map(s=>{
    const l=labels.find(l=>l.uuid===s.uuid);const px=x(s.position[0]),pz=z(s.position[2]);
    const yaw=s.yaw*Math.PI/180;
    return `<g data-uuid="${s.uuid}" data-world-x="${s.position[0]}" data-world-z="${s.position[2]}"><title>${escapeXml(JSON.stringify(s))}</title><rect x="${x(s.bounds[0])}" y="${z(s.bounds[2])}" width="${(s.bounds[3]-s.bounds[0])*scale}" height="${(s.bounds[5]-s.bounds[2])*scale}" fill="#79b8ff22" stroke="#79b8ff"/><line x1="${px}" y1="${pz}" x2="${x(s.position[0]+s.velocity[0])}" y2="${z(s.position[2]+s.velocity[2])}" stroke="#ffd166"/><line x1="${px}" y1="${pz}" x2="${x(s.position[0]-Math.sin(yaw))}" y2="${z(s.position[2]+Math.cos(yaw))}" stroke="#77dd99"/><circle cx="${px}" cy="${pz}" r="3" fill="#fff"/><text x="${px+6}" y="${pz-6}">${l.label} / ${l.uuidSuffix}</text></g>`;
  }).join('');
  return Buffer.from(`<svg xmlns="http://www.w3.org/2000/svg" width="560" height="550" viewBox="0 0 560 550"><rect width="560" height="550" fill="#141921"/><g fill="#fff" font-family="sans-serif" font-size="12"><text x="20" y="20">Exact X/Z schematic · NORTH = −Z · EAST = +X</text><rect x="40" y="40" width="${(b.max[0]-b.min[0])*scale}" height="${(b.max[2]-b.min[2])*scale}" fill="none" stroke="#8a94a8"/>${geometry}<text x="20" y="510">Blue: bounds · Green: facing (1 block) · Gold: velocity (1 tick)</text><text x="20" y="532">Derived structured facts; hidden/occluded appearance is not inferred</text></g></svg>`);
}
