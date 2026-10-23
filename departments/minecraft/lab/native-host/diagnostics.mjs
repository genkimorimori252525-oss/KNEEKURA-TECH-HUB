import assert from 'node:assert/strict';
export const diagnosticSchemaHash='04f8199d9e640211d62ec0d98879f5346e467d3d76ed3a41bda3235d02b8f899';
export const diagnosticDefaults=()=>({schemaHash:diagnosticSchemaHash,startTrigger:'SUBJECT_MOTION',maxWallMs:20000,maxServerSamples:400,maxClientSamples:400,maxFrameSamples:1200,maxBytes:1048576,maxQueue:64});
export function validateDiagnostics(d,parentWallMs){
 const limits=diagnosticDefaults();assert(d&&typeof d==='object'&&!Array.isArray(d));assert.deepEqual(Object.keys(d).sort(),Object.keys(limits).sort(),'TANK_DIAGNOSTIC_FIELDS');
 assert.equal(d.schemaHash,diagnosticSchemaHash,'TANK_DIAGNOSTIC_SCHEMA');assert(['READY','SUBJECT_MOTION'].includes(d.startTrigger),'TANK_DIAGNOSTIC_TRIGGER');
 for(const [key,max] of Object.entries(limits)){if(key==='schemaHash'||key==='startTrigger')continue;assert(Number.isInteger(d[key])&&d[key]>=1&&d[key]<=max,'TANK_DIAGNOSTIC_'+key);}
 assert(d.maxWallMs<=parentWallMs,'TANK_DIAGNOSTIC_SUBLEASE');return structuredClone(d);
}
