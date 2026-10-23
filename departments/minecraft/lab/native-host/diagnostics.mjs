import assert from 'node:assert/strict';
export const diagnosticSchemaHash='a06284789167a3632d58058738402b0dcf24bfee7c5412a8d68cd58d65bec61d';
export const diagnosticDefaults=()=>({schemaHash:diagnosticSchemaHash,maxWallMs:20000,maxServerSamples:400,maxClientSamples:400,maxFrameSamples:1200,maxBytes:1048576,maxQueue:64});
export function validateDiagnostics(d,parentWallMs){
 const limits=diagnosticDefaults();assert(d&&typeof d==='object'&&!Array.isArray(d));assert.deepEqual(Object.keys(d).sort(),Object.keys(limits).sort(),'TANK_DIAGNOSTIC_FIELDS');
 assert.equal(d.schemaHash,diagnosticSchemaHash,'TANK_DIAGNOSTIC_SCHEMA');
 for(const [key,max] of Object.entries(limits)){if(key==='schemaHash')continue;assert(Number.isInteger(d[key])&&d[key]>=1&&d[key]<=max,'TANK_DIAGNOSTIC_'+key);}
 assert(d.maxWallMs<=parentWallMs,'TANK_DIAGNOSTIC_SUBLEASE');return structuredClone(d);
}
