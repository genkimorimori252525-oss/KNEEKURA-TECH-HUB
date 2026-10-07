import test from 'node:test';
import assert from 'node:assert/strict';
import * as fs from 'node:fs/promises';
import os from 'node:os';
import path from 'node:path';
import {verifyCompiledClasses} from '../native/class-readiness.mjs';
import {sha256} from '../json.mjs';

test('selected compiled output must contain every finite required resource and match its pinned hash',async()=>{
 const outputRoot=await fs.mkdtemp(path.join(os.tmpdir(),'tank-readiness-'));
 await fs.mkdir(path.join(outputRoot,'p'));const bytes=Buffer.from('cafebabe0000003d0001','hex');
 await fs.writeFile(path.join(outputRoot,'p/A.class'),bytes);
 const classes=[{className:'p.A',sha256:sha256(bytes)}];
 const receipt=await verifyCompiledClasses({outputRoot,classes});
 assert.deepEqual(receipt.classResources,classes);assert.equal(receipt.sourceFreshness,'NOT_ATTESTED');
 await assert.rejects(verifyCompiledClasses({outputRoot,classes:[...classes,{className:'p.Missing'}]}),/ENOENT/);
 await assert.rejects(verifyCompiledClasses({outputRoot,classes:[{className:'p.A',sha256:'0'.repeat(64)}]}),/MATERIAL_HASH_MISMATCH/);
 await fs.writeFile(path.join(outputRoot,'p/A.class'),'not bytecode');
 await assert.rejects(verifyCompiledClasses({outputRoot,classes:[{className:'p.A'}]}),/INVALID_CLASS_RESOURCE/);
});
test('readiness rejects empty, duplicate, excessive or path-like selection',async()=>{
 for(const classes of [[],[{className:'../A'}],[{className:'p.A'},{className:'p.A'}],Array.from({length:65},(_,i)=>({className:'p.A'+i}))])
  await assert.rejects(verifyCompiledClasses({outputRoot:process.cwd(),classes}),/CLASS_READINESS_SELECTION/);
});
