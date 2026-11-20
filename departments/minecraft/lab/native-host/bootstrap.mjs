import assert from 'node:assert/strict';
import path from 'node:path';

/** Early native binding grants cleanup only. It never establishes world/Player readiness. */
export function validateBootstrap(request,binding,current,javaExecutable,expectedRequestHash){
 assert.equal(binding.v,1);for(const key of ['debugSessionId','runId','runSnapshotId','processEpoch'])assert(current[key]!=null&&binding[key]===current[key],'TANK_BOOTSTRAP_'+key);
 for(const key of ['nonce','installHash','adapterHash'])assert.equal(binding[key],request[key],'TANK_BOOTSTRAP_'+key);
 assert(Number.isSafeInteger(binding.pid)&&binding.pid>0);assert(Number.isFinite(binding.jvmStartedAtEpochMs)&&binding.jvmStartedAtEpochMs>=current.spawnedAtEpochMs-2000,'TANK_BOOTSTRAP_START_TIME');
 assert.equal(path.resolve(binding.commandHint).toLowerCase(),path.resolve(javaExecutable).toLowerCase(),'TANK_BOOTSTRAP_EXECUTABLE');
 assert(/^[a-f0-9]{64}$/.test(binding.requestHash),'TANK_BOOTSTRAP_REQUEST_HASH');
 assert.equal(binding.requestHash,expectedRequestHash,'TANK_BOOTSTRAP_REQUEST_HASH');
 return {pid:binding.pid,spawnedAtEpochMs:binding.jvmStartedAtEpochMs,launchCommand:javaExecutable};
}
/**
 * A launch that died before the native adapter wrote its claim has no bound runtime PID.
 * Cleanup may proceed only after positively observing that neither the recorded launcher, its descendants,
 * nor any java/node carrying this trial's identity (request hash or trial path, including @argfiles) remains.
 * Rows: {pid,parentPid,name,commandLine|null,startedAtEpochMs,argFiles?:[{file,text|null}]}.
 */
export function findTrialProcesses(rows,{launcherPid,launcherSpawnedAtEpochMs,markers,selfPid,javaExecutable}){
 assert(Array.isArray(rows)&&rows.length>0,'TANK_PROCESS_LIST_EMPTY');assert(Number.isSafeInteger(launcherPid)&&launcherPid>0&&Number.isFinite(launcherSpawnedAtEpochMs),'TANK_LAUNCHER_IDENTITY');
 const norm=value=>String(value).toLowerCase().replaceAll('/','\\');const needles=markers.filter(Boolean).map(norm);assert(needles.length>0,'TANK_TRIAL_MARKERS');
 const byPid=new Map(rows.map(row=>[row.pid,row]));const self=new Set();for(let row=byPid.get(selfPid);row&&!self.has(row.pid);row=byPid.get(row.parentPid))self.add(row.pid);
 const after=row=>!Number.isFinite(row.startedAtEpochMs)||row.startedAtEpochMs>=launcherSpawnedAtEpochMs-2000;
 const tree=new Set([launcherPid]);for(let grew=true;grew;){grew=false;for(const row of rows)if(!tree.has(row.pid)&&tree.has(row.parentPid)&&after(row)){tree.add(row.pid);grew=true;}}
 const runtime=row=>/^(java|javaw|node)(\.exe)?$/i.test(row.name??'');const java=norm(javaExecutable??'');
 const present=[],unknown=[];
 for(const row of rows){
  if(self.has(row.pid))continue;const summary={pid:row.pid,parentPid:row.parentPid,name:row.name};
  if(row.pid===launcherPid){if(!Number.isFinite(row.startedAtEpochMs)||Math.abs(row.startedAtEpochMs-launcherSpawnedAtEpochMs)<=2000)present.push({...summary,reason:'RECORDED_LAUNCHER'});continue;}
  if(tree.has(row.pid)){present.push({...summary,reason:'LAUNCHER_DESCENDANT'});continue;}
  if(!runtime(row))continue;
  const texts=[row.commandLine,...(row.argFiles??[]).map(file=>file.text)];const known=texts.filter(text=>typeof text==='string').map(norm).join('\n');
  if(needles.some(needle=>known.includes(needle))){present.push({...summary,reason:'TRIAL_IDENTITY_ARGUMENT'});continue;}
  const ours=!java||norm(row.commandLine??'').replaceAll('"','').startsWith(java)||norm(row.executablePath??'')===java;
  if(texts.some(text=>typeof text!=='string')&&(row.commandLine==null||ours))unknown.push({...summary,reason:row.commandLine==null?'COMMAND_LINE_UNREADABLE':'ARGFILE_UNREADABLE'});
 }
 return {status:present.length?'PRESENT':unknown.length?'UNKNOWN':'NONE',present,unknown};
}
export function validateBootstrapProcess(request,binding,observed,javaExecutable){
 assert.equal(observed.pid,binding.pid);assert(!observed.inspectionError&&typeof observed.exists==='boolean','TANK_BOOTSTRAP_INSPECTION_UNKNOWN');
 if(!observed.exists)return false;
 assert(Number.isFinite(observed.startedAtEpochMs)&&Math.abs(observed.startedAtEpochMs-binding.jvmStartedAtEpochMs)<=2000,'TANK_BOOTSTRAP_PID_REUSED');
 const line=observed.commandLine.toLowerCase();const exe=javaExecutable.toLowerCase();assert(line.startsWith('"'+exe+'" ')||line.startsWith(exe+' '),'TANK_BOOTSTRAP_WRONG_EXECUTABLE');
 const args=(line.match(/(?:[^\s"]+|"[^"]*")+/g)||[]).map(value=>value.replaceAll('"',''));
 for(const text of ['-Dkneekura.tank.requestSha256='+binding.requestHash,'-Dkneekura.tank.installSha256='+request.installHash,'-Dkneekura.tank.world='+request.worldDir])assert(args.includes(text.toLowerCase()),'TANK_BOOTSTRAP_LAUNCH_ARGUMENT');
 return true;
}
