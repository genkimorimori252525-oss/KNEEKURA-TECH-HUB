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
export function validateBootstrapProcess(request,binding,observed,javaExecutable){
 assert.equal(observed.pid,binding.pid);assert(!observed.inspectionError&&typeof observed.exists==='boolean','TANK_BOOTSTRAP_INSPECTION_UNKNOWN');
 if(!observed.exists)return false;
 assert(Number.isFinite(observed.startedAtEpochMs)&&Math.abs(observed.startedAtEpochMs-binding.jvmStartedAtEpochMs)<=2000,'TANK_BOOTSTRAP_PID_REUSED');
 const line=observed.commandLine.toLowerCase();const exe=javaExecutable.toLowerCase();assert(line.startsWith('"'+exe+'" ')||line.startsWith(exe+' '),'TANK_BOOTSTRAP_WRONG_EXECUTABLE');
 const args=(line.match(/(?:[^\s"]+|"[^"]*")+/g)||[]).map(value=>value.replaceAll('"',''));
 for(const text of ['-Dkneekura.tank.requestSha256='+binding.requestHash,'-Dkneekura.tank.installSha256='+request.installHash,'-Dkneekura.tank.world='+request.worldDir])assert(args.includes(text.toLowerCase()),'TANK_BOOTSTRAP_LAUNCH_ARGUMENT');
 return true;
}
