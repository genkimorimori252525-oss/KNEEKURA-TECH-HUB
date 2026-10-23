import test from 'node:test';import assert from 'node:assert/strict';
import {diagnosticDefaults,validateDiagnostics} from './diagnostics.mjs';
test('motion diagnostics have independently finite scope inside original window',()=>{assert.equal(validateDiagnostics(diagnosticDefaults(),120000).maxWallMs,20000);assert.throws(()=>validateDiagnostics(diagnosticDefaults(),19999));});
for(const key of Object.keys(diagnosticDefaults()).filter(k=>k!=='schemaHash'))test('reject invalid diagnostic '+key,()=>{for(const value of [0,-1,1.5,NaN,Infinity,diagnosticDefaults()[key]+1,'1'])assert.throws(()=>validateDiagnostics({...diagnosticDefaults(),[key]:value},120000));});
test('no hidden diagnostics capabilities or foreign schema',()=>{for(const change of [{native_input:true},{captures:1},{schemaHash:'b'.repeat(64)},{maxWallMs:120000}])assert.throws(()=>validateDiagnostics({...diagnosticDefaults(),...change},120000));});
