import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs/promises';
import os from 'node:os';
import path from 'node:path';
import {releaseStaleLock} from './tank.mjs';

// Regression: a warm stopped by a watchdog left host-lock.json with no official way to release it.
async function host(t,operation='warm'){
 const root=await fs.realpath(await fs.mkdtemp(path.join(os.tmpdir(),'tank-stale-')));t.after(()=>fs.rm(root,{recursive:true,force:true}));
 await fs.writeFile(path.join(root,'host-lock.json'),JSON.stringify({token:'t1',operation,pid:4242,at:'x'}));return root;
}
const quiet=[{pid:1,parentPid:0,name:'System',commandLine:null},{pid:process.pid,parentPid:1,name:'node.exe',commandLine:'node tank.mjs'}];
const exists=file=>fs.stat(file).then(()=>true,()=>false);
test('warm lock with dead owner and no installation users is released with a receipt',async t=>{
 const h=await host(t);const r=await releaseStaleLock(h,{list:async()=>quiet});assert.equal(r.status,'STALE_LOCK_RELEASED');assert.equal(await exists(path.join(h,'host-lock.json')),false);
 assert.equal(JSON.parse(await fs.readFile(path.join(h,'released-locks','t1.json'),'utf8')).lock.operation,'warm');
});
test('live owner node or any process referencing the installation keeps the lock',async t=>{
 const h=await host(t);
 await assert.rejects(releaseStaleLock(h,{list:async()=>[...quiet,{pid:4242,parentPid:1,name:'node.exe',commandLine:'node tank.mjs warm'}]}),/OWNER_OR_USER_PRESENT 4242/);
 await assert.rejects(releaseStaleLock(h,{list:async()=>[...quiet,{pid:77,parentPid:1,name:'java.exe',commandLine:'java -cp '+h+'\\native-host\\host GradleWrapperMain'}]}),/OWNER_OR_USER_PRESENT 77/);
 await assert.rejects(releaseStaleLock(h,{list:async()=>[...quiet,{pid:78,parentPid:1,name:'java.exe',commandLine:null}]}),/OWNER_OR_USER_PRESENT 78/);
 await assert.rejects(releaseStaleLock(h,{list:async()=>{throw Error('TANK_PROCESS_LISTING_FAILED');}}),/LISTING_FAILED/);
 assert.equal(await exists(path.join(h,'host-lock.json')),true);
});
test('a reused PID that is not node does not count as the owner; trial locks are refused',async t=>{
 const h=await host(t);assert.equal((await releaseStaleLock(h,{list:async()=>[...quiet,{pid:4242,parentPid:1,name:'chrome.exe',commandLine:'chrome'}]})).status,'STALE_LOCK_RELEASED');
 const r=await host(t,'run:C:/trial');await assert.rejects(releaseStaleLock(r,{list:async()=>quiet}),/USE_STOP_OR_ABORT/);
 assert.equal((await releaseStaleLock(await host(t),{list:async()=>quiet})).status,'STALE_LOCK_RELEASED');
});
