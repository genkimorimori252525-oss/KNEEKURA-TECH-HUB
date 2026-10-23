import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs/promises';
import {openSync,closeSync} from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import {spawn} from 'node:child_process';
import {pathToFileURL,fileURLToPath} from 'node:url';

test('detached Node supervisor really executes attached PowerShell -File', {skip:process.platform!=='win32'},async t=>{
 const root=await fs.mkdtemp(path.join(os.tmpdir(),'tank-detached-test-'));t.after(()=>fs.rm(root,{recursive:true,force:true}));
 const script=path.join(root,'proof.ps1'),entry=path.join(root,'entry.mjs'),marker=path.join(root,'executed.txt');
 await fs.writeFile(script,"[System.IO.File]::WriteAllText($env:KNEEKURA_LAUNCH_TEST_MARKER, 'executed')\n");
 const url=pathToFileURL(path.join(path.dirname(fileURLToPath(import.meta.url)),'launch-gradle.mjs')).href;
 await fs.writeFile(entry,`import {runPowerShellScript} from ${JSON.stringify(url)};process.exitCode=await runPowerShellScript(${JSON.stringify(script)});\n`);
 const fd=openSync(path.join(root,'process.log'),'wx');const child=spawn(process.execPath,[entry],{detached:true,windowsHide:true,env:{...process.env,KNEEKURA_LAUNCH_TEST_MARKER:marker},stdio:['ignore',fd,fd]});closeSync(fd);
 const code=await new Promise((resolve,reject)=>{child.once('error',reject);child.once('exit',resolve);});assert.equal(code,0);assert.equal(await fs.readFile(marker,'utf8'),'executed');
});
