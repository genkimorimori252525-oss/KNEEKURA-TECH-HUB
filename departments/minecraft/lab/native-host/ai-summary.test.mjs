import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs/promises';
import os from 'node:os';
import path from 'node:path';
import {summarizeAi} from './tank.mjs';

test('AI summary points at ai.jsonl and suggests the template only when nothing explained itself',async t=>{
 const trial=await fs.mkdtemp(path.join(os.tmpdir(),'tank-ai-'));t.after(()=>fs.rm(trial,{recursive:true,force:true}));
 assert.equal((await summarizeAi(trial)).status,'NO_AI_RESULT');
 const dir=path.join(trial,'runtime','s','r','evidence');await fs.mkdir(dir,{recursive:true});
 await fs.writeFile(path.join(dir,'ai-result.json'),JSON.stringify({records:3,droppedRecords:0,goalsSeen:['1:A'],explainedClasses:[],whyErrors:0}));
 let s=await summarizeAi(trial);assert.equal(s.status,'RECORDED');assert.equal(s.log,path.join(dir,'ai.jsonl'));assert.match(s.next,/TankWhy\.java/);
 await fs.writeFile(path.join(dir,'ai-result.json'),JSON.stringify({records:3,explainedClasses:['Boss'],whyErrors:1}));
 s=await summarizeAi(trial);assert.deepEqual(s.explainedClasses,['Boss']);assert.equal(s.whyErrors,1);assert.match(s.next,/why/);
});
