import fs from 'node:fs/promises';
import path from 'node:path';
import assert from 'node:assert/strict';
import {spawn,execFileSync} from 'node:child_process';
import {randomUUID} from 'node:crypto';
import {fileURLToPath,pathToFileURL} from 'node:url';
import {parseArgs} from 'node:util';
import {hash,versions,regularPath,inventory,inventoryHash,verifyProfile} from './profile.mjs';
import {validateTerminalAck} from './shutdown.mjs';
import {validateBootstrap,validateBootstrapProcess} from './bootstrap.mjs';

const here=path.dirname(fileURLToPath(import.meta.url));
const read=file=>fs.readFile(file,'utf8').then(JSON.parse);
const write=(file,value)=>fs.writeFile(file,JSON.stringify(value,null,2)+'\n',{flag:'wx'});
const within=(root,file)=>file!==root&&!path.relative(root,file).startsWith('..')&&!path.isAbsolute(path.relative(root,file));
export const defaultRoot=()=>path.join(process.env.LOCALAPPDATA||path.join(process.env.USERPROFILE,'AppData/Local'),'Kneekura/TechHub/Tank');

async function filesUnder(root,relative=''){
 const rows=[];for(const entry of await fs.readdir(path.join(root,relative),{withFileTypes:true})){assert(!entry.isSymbolicLink(),'TANK_INSTALL_REPARSE');const file=path.join(relative,entry.name);if(entry.isDirectory()){if(!['build','.gradle','node_modules','run'].includes(entry.name))rows.push(...await filesUnder(root,file));}else if(entry.isFile())rows.push(file);else throw Error('TANK_INSTALL_FILE_KIND');}return rows.sort();
}
async function snapshot(root,prefix){const result=[];for(const file of await filesUnder(root))result.push({file:path.join(prefix,file).replaceAll('\\','/'),sha256:hash(await fs.readFile(path.join(root,file)))});return result;}
export async function verifyImportClosure(root){
 for(const file of await filesUnder(root)){if(!file.endsWith('.mjs')||file.endsWith('.test.mjs'))continue;const text=await fs.readFile(path.join(root,file),'utf8');for(const match of text.matchAll(/\b(?:from\s*|import\s*\()\s*['"](\.[^'"]+)['"]/g)){const target=path.resolve(root,path.dirname(file),match[1]);assert(within(root,target),'TANK_IMPORT_ESCAPE');await regularPath(target);}}
}
async function verifyJava(javaHome){await regularPath(path.join(javaHome,'bin/java.exe'));const child=spawn(path.join(javaHome,'bin/java.exe'),['-version'],{windowsHide:true});let data='';child.stderr.on('data',b=>data+=b);const code=await new Promise((resolve,reject)=>{child.once('error',reject);child.once('exit',resolve);});assert.equal(code,0,'TANK_JAVA_FAILED');assert(/version "17[.\"]/.test(data),'TANK_JAVA_17_REQUIRED');return data.trim();}

/** Snapshot source and wrapper only. No downloads, compilation, world writes or native launch. */
export async function install({root=defaultRoot(),javaHome}){
 root=path.resolve(root);await fs.mkdir(root,{recursive:true});await regularPath(root,true);await verifyJava(javaHome);
 const lab=path.resolve(here,'..');const sourceRevision=execFileSync('git',['rev-parse','HEAD'],{cwd:lab,encoding:'utf8',windowsHide:true}).trim();
 const rows=[...await snapshot(here,'native-host'),...await snapshot(path.join(lab,'debug-workspace'),'debug-workspace')];
 // Pure libraries required by canonical evidence modules; no legacy viewer/server is installed.
 for(const file of ['simlab/motion-trace.mjs','simlab/trace-age-style.mjs','simlab/golden/png.mjs'])rows.push({file,sha256:hash(await fs.readFile(path.join(lab,file)))});
 const bundleHash=hash(Buffer.from(JSON.stringify(rows)));const installed=path.join(root,'hosts','forge-1.20.1-47.4.10-'+bundleHash);
 await fs.mkdir(path.dirname(installed),{recursive:true});
 if(await fs.stat(installed).catch(()=>null)){await verifyInstallation(installed);return {status:'EXISTING_VERIFIED',installed,bundleHash};}
 await fs.mkdir(installed); // Exclusive: an interrupted installation remains visible and fails verification.
 for(const row of rows){const source=path.join(lab,row.file);const dest=path.join(installed,row.file);await fs.mkdir(path.dirname(dest),{recursive:true});const bytes=await fs.readFile(source);assert.equal(hash(bytes),row.sha256,'TANK_SOURCE_CHANGED_DURING_INSTALL');await fs.writeFile(dest,bytes,{flag:'wx'});}
 await write(path.join(installed,'install.json'),{schema:'kneekura.tank-install/v1',bundleHash,sourceRevision,versions,files:rows,javaHome:await fs.realpath(javaHome),installedAt:new Date().toISOString()});
 await verifyInstallation(installed);return {status:'INSTALLED_NOT_WARMED',installed,bundleHash,command:`node "${path.join(installed,'native-host/tank.mjs')}" doctor --installation "${installed}"`};
}
export async function verifyInstallation(installed){
 installed=await regularPath(path.resolve(installed),true);const manifest=await read(path.join(installed,'install.json'));
 assert.equal(manifest.schema,'kneekura.tank-install/v1');assert.deepEqual(manifest.versions,versions);assert.equal(hash(Buffer.from(JSON.stringify(manifest.files))),manifest.bundleHash,'TANK_INSTALL_MANIFEST_HASH');
 assert.equal(path.basename(installed),'forge-1.20.1-47.4.10-'+manifest.bundleHash,'TANK_INSTALL_DIRECTORY_IDENTITY');
 for(const row of manifest.files){const file=path.resolve(installed,row.file);assert(within(installed,file),'TANK_INSTALL_ESCAPE');await regularPath(file);assert.equal(hash(await fs.readFile(file)),row.sha256,'TANK_INSTALL_TAMPERED_'+row.file);}
 await verifyImportClosure(installed);await verifyJava(manifest.javaHome);return {installed,manifest};
}
async function lockHost(installed,operation){const token=randomUUID();const file=path.join(installed,'host-lock.json');await write(file,{token,operation,pid:process.pid,at:new Date().toISOString()});return {file,token};}
async function unlock(lock){assert.equal((await read(lock.file)).token,lock.token,'TANK_LOCK_REPLACED');await fs.unlink(lock.file);}
async function runTool(command,args,{cwd,env,log}){const output=await fs.open(log,'wx');try{const child=spawn(command,args,{cwd,env,windowsHide:true,stdio:['ignore',output.fd,output.fd]});const code=await new Promise((resolve,reject)=>{child.once('error',reject);child.once('exit',resolve);});assert.equal(code,0,'TANK_TOOL_FAILED_SEE_'+log);}finally{await output.close();}}
function gradleEnvironment(installed,manifest,extra={}){return {...process.env,JAVA_HOME:manifest.javaHome,KNEEKURA_TANK_WRAPPER:path.join(installed,'native-host/host/gradlew.bat'),...extra};}
async function gradle(installed,manifest,tasks,extra,log){await runTool('powershell.exe',['-NoProfile','-NonInteractive','-File',path.join(installed,'native-host/gradle.ps1'),...tasks],{cwd:path.join(installed,'native-host/host'),env:gradleEnvironment(installed,manifest,extra),log});}

/** Explicit online dependency preparation. A failed warm is retained, never reported ready. */
export async function warm(installed,{online=false}={}){
 const state=await verifyInstallation(installed);const lock=await lockHost(state.installed,'warm');
 const preparations=path.join(state.installed,'preparations');await fs.mkdir(preparations,{recursive:true});const dir=path.join(preparations,randomUUID());await fs.mkdir(dir);
 try{await gradle(state.installed,state.manifest,['classes','prepareRunClient','writeTankClasspath',...(online?[]:['--offline']),'--console=plain','-Dnet.minecraftforge.gradle.check.certs=false'],{KNEEKURA_TANK_PROFILE:'',KNEEKURA_TANK_CLASSPATH:path.join(dir,'classpath.txt')},path.join(dir,'gradle.log'));
  const cp=(await fs.readFile(path.join(dir,'classpath.txt'),'utf8')).trim();assert(cp&&!/[\r\n"]/.test(cp),'TANK_CLASSPATH_FORMAT');const runtimeCp=(await fs.readFile(path.join(dir,'runtime-classpath.txt'),'utf8')).trim();assert(runtimeCp&&!/[\r\n"]/.test(runtimeCp),'TANK_RUNTIME_CLASSPATH_FORMAT');const dependencies=[];for(const file of new Set([...cp.split(path.delimiter),...runtimeCp.split(path.delimiter)])){await regularPath(file);dependencies.push({file,sha256:hash(await fs.readFile(file))});}
  const classes=path.join(dir,'classes');await fs.mkdir(classes);const bridge=path.join(state.installed,'debug-workspace/forge-bridge/src/main/java/com/github/tartaricacid/touhoulittlemaid/sim/debug');const native=path.join(state.installed,'debug-workspace/bridge/manual-native');
  const sources=['KneekuraDebugEnv.java','KneekuraDebugReadyWriter.java'].map(x=>path.join(bridge,x)).concat(['ManualRequest.java','ManualRequestSelfTest.java','ManualShutdown.java','ManualNativeAdapter.java'].map(x=>path.join(native,x)));
  const args=['--release','17','-encoding','UTF-8','-proc:none','-cp',cp,'-d',classes,...sources];const argFile=path.join(dir,'javac.args');await fs.writeFile(argFile,args.map(x=>'"'+x.replaceAll('\\','/')+'"').join('\n'),{flag:'wx'});
  await runTool(path.join(state.manifest.javaHome,'bin/javac.exe'),['-J-Duser.language=en','@'+argFile],{cwd:dir,env:process.env,log:path.join(dir,'javac.log')});
  await runTool(path.join(state.manifest.javaHome,'bin/java.exe'),['-ea','-cp',classes+path.delimiter+cp,'kneekura.manual.ManualRequestSelfTest'],{cwd:dir,env:process.env,log:path.join(dir,'guards.log')});
  const resource=path.join(dir,'resources');await fs.mkdir(path.join(resource,'META-INF'),{recursive:true});await fs.writeFile(path.join(resource,'META-INF/mods.toml'),'modLoader="javafml"\nloaderVersion="[47,)"\nlicense="Private verification"\n[[mods]]\nmodId="kneekura_manual_adapter"\nversion="1"\ndisplayName="TechHub bounded native observer"\n',{flag:'wx'});
  await write(path.join(resource,'pack.mcmeta'),{pack:{pack_format:15,description:'TechHub finite native event observer'}});
  const jar=path.join(dir,'manual-adapter.jar');await runTool(path.join(state.manifest.javaHome,'bin/jar.exe'),['--create','--file',jar,'-C',classes,'.','-C',resource,'.'],{cwd:dir,env:process.env,log:path.join(dir,'jar.log')});
  const receipt={schema:'kneekura.tank-warm/v1',bundleHash:state.manifest.bundleHash,adapter:jar,adapterHash:hash(await fs.readFile(jar)),classpath:cp,dependencies,completedAt:new Date().toISOString()};await write(path.join(dir,'warm.json'),receipt);
  // Atomic pointer selects only a completed warm; older preparations are retained.
  const pointer=path.join(state.installed,'warm-current.'+randomUUID()+'.json');await write(pointer,{receipt:path.join(dir,'warm.json'),sha256:hash(await fs.readFile(path.join(dir,'warm.json')))});await fs.rename(pointer,path.join(state.installed,'warm-current.json'));
  const root=path.resolve(state.installed,'../..');await fs.mkdir(path.join(root,'registrations'),{recursive:true});const selection={schema:'kneekura.tank-active-host/v1',installed:state.installed,bundleHash:state.manifest.bundleHash,warmReceipt:path.join(dir,'warm.json'),registeredAt:new Date().toISOString(),nativeAcceptance:'NOT_ESTABLISHED_BY_WARM'};
  await write(path.join(root,'registrations',randomUUID()+'.json'),selection);const next=path.join(root,'active-host.'+randomUUID()+'.json');await write(next,selection);await fs.rename(next,path.join(root,'active-host.json'));
  return {status:'WARMED_NOT_LAUNCHED',preparation:dir};
 }finally{await unlock(lock);}
}
async function warmed(state){const pointer=await read(path.join(state.installed,'warm-current.json'));assert(within(state.installed,path.resolve(pointer.receipt)),'TANK_WARM_ESCAPE');assert.equal(hash(await fs.readFile(pointer.receipt)),pointer.sha256);const r=await read(pointer.receipt);assert.equal(r.bundleHash,state.manifest.bundleHash);for(const entry of [{file:r.adapter,sha256:r.adapterHash},...r.dependencies]){await regularPath(entry.file);assert.equal(hash(await fs.readFile(entry.file)),entry.sha256,'TANK_WARM_DEPENDENCY_CHANGED');}return r;}

/** Copy an already prepared fixture; this function never interprets or modifies NBT. */
export async function prepare(installed,profile){
 const state=await verifyInstallation(installed),warmState=await warmed(state);const checked=await verifyProfile(profile);const root=path.resolve(state.installed,'../..');const runs=path.join(root,'runs');await fs.mkdir(runs,{recursive:true});const trial=path.join(runs,profile.id+'-'+randomUUID());await fs.mkdir(trial);const inputs=path.join(trial,'inputs');await fs.mkdir(inputs);const game=path.join(trial,'game');const world=path.join(game,'saves/KNEEKURA_DEBUG_WORLD');await fs.mkdir(path.dirname(world),{recursive:true});
 await write(path.join(inputs,'profile.json'),profile);await write(path.join(inputs,'world-inventory.json'),checked.worldInventory);await fs.cp(profile.world.directory,world,{recursive:true,force:false,errorOnExist:true});assert.equal(inventoryHash(await inventory(world)),profile.world.inventorySha256,'TANK_COPY_CHANGED');
 const mods=[];for(const entry of profile.mods){const file=path.join(inputs,entry.id+'-'+entry.sha256+'.jar');await fs.copyFile(entry.file,file,fs.constants.COPYFILE_EXCL);assert.equal(hash(await fs.readFile(file)),entry.sha256,'TANK_COPY_MOD_CHANGED');mods.push({...entry,file});}
 const adapter=path.join(inputs,'manual-adapter.jar');await fs.copyFile(warmState.adapter,adapter,fs.constants.COPYFILE_EXCL);
 const runtimeProfile={gameDir:game,worldDir:world,materialDir:inputs,adapter,mods,playerUuid:profile.playerUuid};await write(path.join(inputs,'runtime-profile.json'),runtimeProfile);
 const {validateManualSession}=await import(pathToFileURL(path.join(state.installed,'debug-workspace/bridge/manual-session.mjs')));
 // Resolve production-to-development remapping during preparation, not launch.
 const lock=await lockHost(state.installed,'prepare:'+trial);const resolvedFile=path.join(inputs,'resolved-materials.json');
 try{await gradle(state.installed,state.manifest,['writeTankResolved','--offline','--console=plain','-Dnet.minecraftforge.gradle.check.certs=false'],{KNEEKURA_TANK_PROFILE:path.join(inputs,'runtime-profile.json'),KNEEKURA_TANK_RESOLVED:resolvedFile},path.join(trial,'resolve.log'));}finally{await unlock(lock);}
 const resolved=await read(resolvedFile);assert.equal(resolved.length,mods.length,'TANK_RESOLVED_MATERIAL_COUNT');for(const m of resolved){assert(mods.some(x=>x.id===m.id),'TANK_RESOLVED_FOREIGN_MOD');await regularPath(m.file);assert.equal(hash(await fs.readFile(m.file)),m.sha256,'TANK_RESOLVED_MATERIAL_CHANGED');}
 const request=validateManualSession({v:1,purpose:'MANUAL_INTERACTION',mode:profile.mode,nonce:randomUUID(),playerUuid:profile.playerUuid,subjectUuid:profile.subjectUuid,trialDir:trial,worldDir:world,maxTicks:profile.maxTicks,maxWallMs:profile.maxWallMs,maxEvents:profile.maxEvents,captures:0,grants:['MANUAL_EVENT_OBSERVATION'],sourceRevisions:{target:profile.sourceRevision??'ARTIFACT_ONLY',techHub:state.manifest.sourceRevision},productHash:hash(Buffer.from(JSON.stringify(profile.mods))),adapterHash:warmState.adapterHash,installHash:state.manifest.bundleHash,materials:resolved.map(({id,sha256})=>({id,sha256}))});await write(path.join(inputs,'manual-request.json'),request);const requestHash=hash(await fs.readFile(path.join(inputs,'manual-request.json')));
 const config={schemaVersion:1,workspaceId:'tank-'+request.nonce,workspaceDir:path.join(state.installed,'native-host/host'),runtimeRoot:path.join(trial,'runtime'),worldName:'KNEEKURA_DEBUG_WORLD',gameDir:game,requireExistingWorld:true,requireGitIdentity:false,decisionHooks:false,motionOverlay:false,readyTimeoutMs:180000,launch:{command:process.execPath,args:[path.join(state.installed,'native-host/launch-gradle.mjs')],env:{JAVA_HOME:state.manifest.javaHome,KNEEKURA_TANK_WRAPPER:path.join(state.installed,'native-host/host/gradlew.bat'),KNEEKURA_TANK_PROFILE:path.join(inputs,'runtime-profile.json'),KNEEKURA_TANK_INSTALL_SHA256:state.manifest.bundleHash,KNEEKURA_MANUAL_ENABLED:'1',KNEEKURA_MANUAL_REQUEST:path.join(inputs,'manual-request.json'),KNEEKURA_MANUAL_REQUEST_SHA256:requestHash,KNEEKURA_DEBUG_MOD_PROFILE:'TANK_CORE'}}};await write(path.join(trial,'config.json'),config);
 const files=await snapshot(inputs,'inputs');files.push({file:'config.json',sha256:hash(await fs.readFile(path.join(trial,'config.json')))});
 await write(path.join(trial,'prepared.json'),{schema:'kneekura.tank-prepared/v1',installed:state.installed,bundleHash:state.manifest.bundleHash,profileHash:hash(Buffer.from(JSON.stringify(profile))),files,worldHash:profile.world.inventorySha256,status:'PREPARED_NOT_RUN'});
 assert.equal(inventoryHash(await inventory(profile.world.directory)),profile.world.inventorySha256,'TANK_SOURCE_WORLD_CHANGED');return {status:'PREPARED_NOT_RUN',trial};
}
async function prepared(trial){trial=await regularPath(path.resolve(trial),true);const seal=await read(path.join(trial,'prepared.json'));assert.equal(seal.schema,'kneekura.tank-prepared/v1');const state=await verifyInstallation(seal.installed);assert.equal(seal.bundleHash,state.manifest.bundleHash);for(const row of seal.files){const file=path.resolve(trial,row.file);assert(within(trial,file),'TANK_PREPARED_ESCAPE');await regularPath(file);assert.equal(hash(await fs.readFile(file)),row.sha256,'TANK_PREPARED_TAMPERED');}return {trial,seal,state,config:await read(path.join(trial,'config.json'))};}
async function cleanupFailedLaunch(p,core){
 const current=await core.readCurrent(p.config,p.state.installed);assert(current.runDir,'TANK_NO_RUN_TO_RECONCILE');
 const requestFile=path.join(p.trial,'inputs/manual-request.json'),request=await read(requestFile),binding=await read(path.join(p.trial,'manual-claim.json'));assert.equal(binding.requestHash,hash(await fs.readFile(requestFile)),'TANK_BOOTSTRAP_REQUEST_HASH');
 const java=path.join(p.state.manifest.javaHome,'bin/java.exe');const record=validateBootstrap(request,binding,current,java,hash(await fs.readFile(requestFile)));
 let observed=await core.inspectProcess(record.pid);let alive=validateBootstrapProcess(request,binding,observed,java);let forced=false;
 if(alive){
  const stop={v:1,debugSessionId:current.debugSessionId,runId:current.runId,runSnapshotId:current.runSnapshotId,processEpoch:current.processEpoch,requestedAt:new Date().toISOString()};const stopFile=path.join(current.runDir,'control/shutdown-request.json');await fs.mkdir(path.dirname(stopFile),{recursive:true});
  try{await write(stopFile,stop);}catch(error){if(error.code!=='EEXIST')throw error;const old=await read(stopFile);for(const key of ['v','debugSessionId','runId','runSnapshotId','processEpoch'])assert.equal(old[key],stop[key],'TANK_EXISTING_STOP_IDENTITY');}
  const deadline=Date.now()+5000;do{await new Promise(resolve=>setTimeout(resolve,100));observed=await core.inspectProcess(record.pid);alive=validateBootstrapProcess(request,binding,observed,java);}while(alive&&Date.now()<deadline);
  if(alive){observed=await core.inspectProcess(record.pid);if(validateBootstrapProcess(request,binding,observed,java)){await core.stopProcessTree(record.pid);forced=true;}}
 }
 const {verifyProcessesExited}=await import(pathToFileURL(path.join(p.state.installed,'debug-workspace/process-stop.mjs')));const nativeExit=await verifyProcessesExited([record],{inspect:core.inspectProcess});assert.equal(nativeExit.status,'VERIFIED_EXIT');const launcher=await core.stopCurrent(p.config,p.state.installed);assert.equal(launcher.cleanup?.status,'VERIFIED_EXIT');
 const result={status:'FAILED_RUN_NATIVE_AND_LAUNCHER_EXIT_VERIFIED',nativeExit,launcherExit:launcher.cleanup,forced,cleanShutdown:false,worldAcceptance:'NOT_ESTABLISHED',bootstrapScope:'CLEANUP_ONLY_NEVER_READY'};
 const output=path.join(p.trial,'failed-run-cleanup.json');if(!(await fs.stat(output).catch(()=>null)))await write(output,result);
 const lock=await read(path.join(p.trial,'host-lock.json'));assert.equal(path.resolve(lock.file).toLowerCase(),path.join(p.state.installed,'host-lock.json').toLowerCase());if(await fs.stat(lock.file).catch(()=>null))await unlock(lock);return result;
}
export async function commandRun(command,trial){
 assert(['start','status','stop','abort','evidence'].includes(command));const p=await prepared(trial);const lab=p.state.installed;const core=await import(pathToFileURL(path.join(lab,'debug-workspace/core.mjs')));
 if(command==='abort')return cleanupFailedLaunch(p,core);
 if(command==='start'){
  assert.equal(inventoryHash(await inventory(path.join(p.trial,'game/saves/KNEEKURA_DEBUG_WORLD'))),p.seal.worldHash,'TANK_PRESTART_WORLD_CHANGED');await warmed(p.state);for(const m of await read(path.join(p.trial,'inputs/resolved-materials.json'))){await regularPath(m.file);assert.equal(hash(await fs.readFile(m.file)),m.sha256,'TANK_RESOLVED_MATERIAL_CHANGED');}const lock=await lockHost(lab,'run:'+p.trial);await write(path.join(p.trial,'host-lock.json'),lock);
  const began=Date.now();try{
   const result=await core.launchDebugRun(p.config,lab);const startupMs=Date.now()-began;await write(path.join(p.trial,'startup.json'),{status:result.status,startupMs,bundleHash:p.seal.bundleHash});console.log(JSON.stringify({event:'TANK_NATIVE_READY',trial:p.trial,runDir:result.runDir,runtimePid:result.runtimePid,startupMs}));
   const request=await read(path.join(p.trial,'inputs/manual-request.json'));const endFile=path.join(result.runDir,'evidence/derived/manual-interaction/window-end.json');const deadline=Date.now()+request.maxWallMs+5000;let end;
   do{end=await read(endFile).catch(error=>{if(error.code==='ENOENT')return null;throw error;});if(end)break;await new Promise(resolve=>setTimeout(resolve,100));}while(Date.now()<deadline);
   assert(end,'TANK_WINDOW_END_MISSING');return {status:'LIFECYCLE_ONLY_NOT_GAMEPLAY_ACCEPTANCE',startupMs,windowEnd:end,closure:await commandRun('stop',p.trial)};
  }catch(error){let cleanup;try{cleanup=await cleanupFailedLaunch(p,core);}catch(failure){cleanup={status:'UNKNOWN',error:failure.message};}await write(path.join(p.trial,'launch-failure.json'),{error:error.message,cleanup,at:new Date().toISOString()});throw error;} // Uncertain ownership keeps its lock; never synthesize readiness or a clean ACK.
 }
 if(command==='status'){const c=await core.readCurrent(p.config,lab);return {status:c.status,live:c.live,runDir:c.runDir,pid:c.pid,runtimePid:c.runtimePid,cleanup:c.cleanup,failedRunCleanup:await read(path.join(p.trial,'failed-run-cleanup.json')).catch(()=>null)};}
 if(command==='stop'){
  const before=await core.readCurrent(p.config,lab);if(before.runtimePid==null)return cleanupFailedLaunch(p,core);
  const completed=await read(path.join(p.trial,'closed.json')).catch(error=>{if(error.code==='ENOENT')return null;throw error;});if(completed)return completed;
  try{await write(path.join(p.trial,'closure-claim.json'),{pid:process.pid,at:new Date().toISOString()});}catch(error){if(error.code!=='EEXIST')throw error;const deadline=Date.now()+15000;do{const result=await read(path.join(p.trial,'closed.json')).catch(()=>null);if(result)return result;await new Promise(resolve=>setTimeout(resolve,100));}while(Date.now()<deadline);throw Error('TANK_CLOSURE_IN_PROGRESS_OR_INTERRUPTED');}
  const stopped=await core.stopCurrent(p.config,lab);const current=await core.readCurrent(p.config,lab);assert.equal(stopped.cleanup?.status,'VERIFIED_EXIT','TANK_EXIT_UNVERIFIED');const ack=validateTerminalAck({...current,cleanup:stopped.cleanup},await read(path.join(current.runDir,'control/shutdown-ack.json')));
  const native=await read(path.join(current.runDir,'evidence/derived/manual-interaction/result.json'));assert.equal(native.requestHash,hash(await fs.readFile(path.join(p.trial,'inputs/manual-request.json'))));assert.equal(native.worldStopped,true);assert.deepEqual(native.errors,[]);assert.equal(native.dropped,0);
  const {finalizeEvidenceRun}=await import(pathToFileURL(path.join(lab,'debug-workspace/evidence/finalize.mjs')));const finalized=await finalizeEvidenceRun(current,{cleanShutdown:true});assert.equal(finalized.manifest.status,'EVIDENCE_COMPLETE');
  const profile=await read(path.join(p.trial,'inputs/profile.json'));assert.equal(inventoryHash(await inventory(profile.world.directory)),profile.world.inventorySha256,'TANK_SOURCE_WORLD_CHANGED');const result={status:'VERIFIED_EXIT',shutdownSource:current.evidenceShutdown?.clean?'SUPERVISOR_STOP_ACK':'RETAINED_NATIVE_ACK_AFTER_VERIFIED_EXIT',ack,native,finalization:finalized.manifest};await write(path.join(p.trial,'closed.json'),result);await unlock(await read(path.join(p.trial,'host-lock.json')));return result;
 }
 const current=await core.readCurrent(p.config,lab);return {status:current.status,runDir:current.runDir,live:current.live,closure:path.join(p.trial,'closed.json'),startup:path.join(p.trial,'startup.json'),nativeEvents:current.runDir?path.join(current.runDir,'evidence/derived/manual-interaction'):null,manualAcceptance:'NOT_ESTABLISHED_BY_LIFECYCLE'};
}
export async function doctor(installed){try{const state=await verifyInstallation(installed);const receipt=await warmed(state).catch(error=>({error:error.message}));return {status:receipt.error?'NOT_WARMED':'VERIFIED_INSTALLATION',installed:state.installed,versions,bundleHash:state.manifest.bundleHash,warmError:receipt.error??null,lock:await read(path.join(state.installed,'host-lock.json')).catch(()=>null),nativeAcceptance:'NOT_ESTABLISHED_BY_DOCTOR'};}catch(error){return {status:'INVALID_INSTALLATION',error:error.message};}}

if(process.argv[1]&&import.meta.url===pathToFileURL(path.resolve(process.argv[1])).href){
 const {values,positionals}=parseArgs({allowPositionals:true,options:{root:{type:'string'},'java-home':{type:'string'},installation:{type:'string'},profile:{type:'string'},trial:{type:'string'},online:{type:'boolean',default:false}}});const command=positionals[0];
 try{let result;if(command==='install'){assert(values['java-home'],'--java-home required');result=await install({root:values.root,javaHome:path.resolve(values['java-home'])});}else if(['doctor','warm','prepare'].includes(command)){assert(values.installation,'--installation required');result=command==='doctor'?await doctor(values.installation):command==='warm'?await warm(values.installation,{online:values.online}):await prepare(values.installation,await read(values.profile));}else{assert(values.trial,'--trial required');result=await commandRun(command,values.trial);}
  const output=result.closure?{status:result.status,trial:values.trial,startupMs:result.startupMs,windowEnd:result.windowEnd,exit:result.closure.status,evidence:result.closure.finalization.status,counts:result.closure.finalization.counts,details:path.join(values.trial,'closed.json')}:command==='stop'&&result.finalization?{status:result.status,trial:values.trial,shutdownSource:result.shutdownSource,evidence:result.finalization.status,counts:result.finalization.counts,details:path.join(values.trial,'closed.json')}:result;
  console.log(JSON.stringify(output));if(result.status==='INVALID_INSTALLATION')process.exitCode=1;
 }catch(error){console.error(JSON.stringify({status:'FAIL',error:error.message,trial:values.trial}));process.exitCode=1;}
}
