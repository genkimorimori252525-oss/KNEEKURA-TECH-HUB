/** Portable real-JVM source contracts. This never installs an owner or launches Minecraft. */
import {mkdtemp,mkdir,rm,writeFile} from 'node:fs/promises';
import path from 'node:path';
import os from 'node:os';
import {fileURLToPath} from 'node:url';
import {spawn,spawnSync} from 'node:child_process';
import {ownerFixture} from './tests/owner-action-fixture.mjs';
import {maintenance} from './tests/owner-tank-rotation-fixtures.mjs';
import {prepareOwnerControl,readPreparedOwnerControl} from './owner-prelaunch.mjs';
import {buildRunSnapshot,writeImmutableRunSnapshot} from '../core.mjs';
const root=fileURLToPath(new URL('../../',import.meta.url));
const packageName='com.github.tartaricacid.touhoulittlemaid.sim.debug';
const packagePath=packageName.replaceAll('.','/');
const main=path.join(root,'debug-workspace/forge-bridge/src/main/java',packagePath);
const tests=path.join(root,'debug-workspace/forge-bridge/src/test/java',packagePath);
const gson=process.env.KNEEKURA_GSON_JAR;
if(!gson||!path.isAbsolute(gson))throw new Error('Explicit genuine KNEEKURA_GSON_JAR required');
const executable=name=>process.env[name==='java'?'KNEEKURA_JAVA':name==='javac'?'KNEEKURA_JAVAC':'KNEEKURA_JAR']||
 (process.env.JAVA_HOME?path.join(process.env.JAVA_HOME,'bin',name+(process.platform==='win32'?'.exe':'')):name);
const temp=await mkdtemp(path.join(os.tmpdir(),'kneekura-owner-source-')),cleanup=[];
function run(command,args){const r=spawnSync(command,args,{cwd:root,encoding:'utf8',timeout:60000,maxBuffer:4*1024*1024});
 if(r.stdout)process.stdout.write(r.stdout);if(r.stderr)process.stderr.write(r.stderr);
 if(r.error||r.status!==0)throw new Error('Owner source verification failed',{cause:r.error});}
try{
 const classes=path.join(temp,'classes');await mkdir(classes);
 const sources=['Env','ActionJournal','ArenaController','ArenaOwnerGrant','Durability','OwnerFiles','OwnerInputs','OwnerDispatch','OwnerTriggers','OwnerLifetime','MaterialLinkage','TankRotationController','TankRotationPlan'];
 const testNames=['OwnerEnvSelfTest','OwnerFilesSelfTest','OwnerInputsSelfTest','OwnerDispatchSelfTest','OwnerTriggersSelfTest','OwnerLifetimeSelfTest','MaterialLinkageSelfTest','OwnerInputsInterop','TankRotationSelfTest','TankRotationPlanSelfTest','TankRotationFilesSelfTest'];
 run(executable('javac'),['--release','17','-proc:none','-cp',gson,'-d',classes,
  ...sources.map(n=>path.join(main,'KneekuraDebug'+n+'.java')),...testNames.map(n=>path.join(tests,'KneekuraDebug'+n+'.java'))]);
 const cp=classes+path.delimiter+gson;
 for(const name of testNames.filter(n=>n.endsWith('SelfTest')&&n!=='TankRotationPlanSelfTest'))run(executable('java'),['-cp',cp,packageName+'.KneekuraDebug'+name]);
 const jar=path.join(temp,'source-fixture.jar');run(executable('jar'),['--create','--file',jar,'-C',classes,'.']);
 run(executable('java'),['-cp',jar+path.delimiter+gson,packageName+'.KneekuraDebugMaterialLinkageSelfTest']);
 const ordinary=await ownerFixture({after(fn){cleanup.push(fn);}},{capture:true,triggerCapture:{enabled:true,triggerKinds:['ARENA_EXIT'],offsetsMs:[-1000,0],toleranceMs:200,cooldownMs:1000,maxWindows:1,captureBudget:1,timeoutMs:1000,captureIndices:[0]}});
 const tank=await maintenance({after(fn){cleanup.push(fn);}});
 for(const [index,fixture] of [ordinary,tank].entries()){
 const prepared=await prepareOwnerControl(fixture.options);
 const contextDir=path.join(temp,'interop-'+index);await mkdir(contextDir);
 if(prepared.tankRotation){
  const file=path.join(contextDir,'tank-plan-fixture.json');
  await writeFile(file,JSON.stringify({plan:prepared.tankRotation,grant:prepared.grant,request:prepared.request,world:prepared.worldRegistration,trigger:null,previousOwnerBytes:fixture.previousOwnerBytes.toString('base64')}));
  run(executable('java'),['-cp',cp,packageName+'.KneekuraDebugTankRotationPlanSelfTest',file]);
 }
 await writeFile(path.join(contextDir,'context.json'),JSON.stringify({runDir:fixture.runDir,identity:fixture.identity,envelopeHash:prepared.envelopeHash}));
 await new Promise((resolve,reject)=>{
  const child=spawn(executable('java'),['-cp',cp,packageName+'.KneekuraDebugOwnerInputsInterop',contextDir],{cwd:root,stdio:['pipe','pipe','pipe']});
  let output='',errors='',started=false,failed=null;
  const timer=setTimeout(()=>{failed=new Error('Owner source JVM deadline');child.kill('SIGKILL');},15000);
  child.on('error',error=>{clearTimeout(timer);reject(error);});
  child.stderr.on('data',b=>{errors+=b.toString();if(errors.length>65536){failed=new Error('Owner source JVM output limit');child.kill('SIGKILL');}});
  child.stdout.on('data',b=>{
   output+=b.toString();if(output.length>65536){failed=new Error('Owner source JVM output limit');child.kill('SIGKILL');return;}
   const match=output.match(/OWNER_SOURCE_JVM_PID=(\d+)/);if(!match||started)return;started=true;
   (async()=>{
    const i=fixture.identity;
    await writeImmutableRunSnapshot(path.join(fixture.runDir,'run-snapshot.json'),buildRunSnapshot({schemaVersion:1,
     snapshotId:i.runSnapshotId,debugSessionId:i.debugSessionId,runId:i.runId,processEpoch:i.processEpoch,
     worldName:'KNEEKURA_DEBUG_WORLD',runtime:{pid:Number(match[1]),attestation:{topology:'INTEGRATED_SERVER',sample:{2:'two',10:'ten'}}}},
     {...fixture.bridgeContext,ownerControlIntent:prepared.ownerControlIntent}));
    await readPreparedOwnerControl({runDir:fixture.runDir,envelopeHash:prepared.envelopeHash,requireSnapshot:true});
    child.stdin.end('snapshot-ready\n');
   })().catch(error=>{failed=error;child.kill('SIGKILL');});
  });
  child.on('close',code=>{clearTimeout(timer);if(failed||code!==0||!output.includes('NODE_JAVA_OWNER_INPUTS_VERIFIED')||!output.includes('tankRotation='+Boolean(prepared.tankRotation)))reject(failed??new Error('Node/Java owner fixture rejected'));else resolve();});
 });
 }
 console.log('Node/Java exact owner input linkage passed using actual parser PID; owner installation and Minecraft NOT_RUN; target attestation NOT_ESTABLISHED');
}finally{for(const fn of cleanup)await fn();await rm(temp,{recursive:true,force:true});}
