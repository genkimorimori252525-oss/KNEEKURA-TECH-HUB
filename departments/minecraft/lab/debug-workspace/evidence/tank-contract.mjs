const identityKeys=['debugSessionId','runId','runSnapshotId','processEpoch','arenaEpoch'];
export function requireTankIdentity(identity) {
  if(!identity||identityKeys.some(key=>typeof identity[key]==='undefined'))throw new TypeError('TANK_IDENTITY_REQUIRED');
  for(const key of identityKeys.slice(0,3))if(typeof identity[key]!=='string'||!identity[key].length||identity[key].length>256)throw new TypeError('TANK_IDENTITY_REQUIRED');
  for(const key of identityKeys.slice(3))if(!Number.isSafeInteger(identity[key])||identity[key]<0)throw new TypeError('TANK_IDENTITY_REQUIRED');
  return Object.fromEntries(identityKeys.map(key=>[key,identity[key]]));
}
export function sameTankIdentity(row,identity) {return identityKeys.every(key=>row?.[key]===identity[key]);}
export function boundedTankPacket(packet) {
  if(Buffer.byteLength(JSON.stringify(packet),'utf8')>256*1024)throw new RangeError('TANK_PACKET_BYTE_BUDGET_EXCEEDED');
  return structuredClone(packet);
}
export function requireTankObservations(observations) {
  if(!Array.isArray(observations)||observations.length>50000)throw new RangeError('TANK_OBSERVATION_LIMIT_EXCEEDED');
  return observations;
}
export function tankFact(value,status='SAMPLED_OBSERVED',row=null,limitations=[]) {
  return {status,value:value===undefined?null:value,sourceObservationIds:row?[row.observationId]:[],observedTick:row?.gameTime??null,limitations};
}
export function validTankGeometry(g) {
  return g&&['x','y','z','width','height','depth'].every(k=>Number.isSafeInteger(g[k]))
    &&g.width>=1&&g.width<=64&&g.depth>=1&&g.depth<=64&&g.height>=1&&g.height<=64
    &&g.width*g.height*g.depth<=65536&&g.y>=-63&&g.y+g.height<=319&&Math.abs(g.x)<=29999983&&Math.abs(g.z)<=29999983
    &&g.x+g.width<=29999984&&g.z+g.depth<=29999984;
}
