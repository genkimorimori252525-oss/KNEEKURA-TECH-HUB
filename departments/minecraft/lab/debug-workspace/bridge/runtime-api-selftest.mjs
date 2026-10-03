import {mkdtemp,rm} from 'node:fs/promises';
import path from 'node:path';
import os from 'node:os';
import {fileURLToPath} from 'node:url';
import {spawnSync} from 'node:child_process';
import {writeFileSync} from 'node:fs';
const root=fileURLToPath(new URL('../../',import.meta.url));
const main=path.join(root,'debug-workspace/forge-bridge/src/main/java/com/github/tartaricacid/touhoulittlemaid/sim/debug');
const test=path.join(root,'debug-workspace/forge-bridge/src/test/java/com/github/tartaricacid/touhoulittlemaid/sim/debug');
const classpath=process.env.KNEEKURA_FORGE_CLASSPATH;
if(!classpath)throw new Error('KNEEKURA_FORGE_CLASSPATH must contain genuine official-mapped Forge1.20.1, Gson, LogUtils/SLF4J and annotation dependencies; no API stubs');
const executable=n=>process.env[n==='java'?'KNEEKURA_JAVA':'KNEEKURA_JAVAC']||(process.env.JAVA_HOME?path.join(process.env.JAVA_HOME,'bin',n+(process.platform==='win32'?'.exe':'')):n);
const output=await mkdtemp(path.join(os.tmpdir(),'kneekura-real-api-'));
function run(command,args){
 // Genuine Windows dependency paths can exceed CreateProcess's argument limit.
 const argFile=path.join(output,'java.args');
 if(args.some(a=>/[\r\n]/.test(a)))throw new Error('Invalid Java argument line break');
 writeFileSync(argFile,args.map(a=>'"'+a.replaceAll('\\','\\\\').replaceAll('"','\\"')+'"').join('\n'));
 const result=spawnSync(command,['@'+argFile],{cwd:root,encoding:'utf8',timeout:120000,maxBuffer:4*1024*1024,windowsHide:true});
 if(result.stdout)process.stdout.write(result.stdout);if(result.stderr)process.stderr.write(result.stderr);
 if(result.error||result.status!==0)throw new Error('Real API source check failed '+command,{cause:result.error});
}
try {
 const names=['Env','ActionJournal','ArenaController','ArenaOwnerGrant','ForgeArenaBackend','ArenaRuntime','Durability','EvidenceWriter',
  'OwnerFiles','OwnerInputs','OwnerDispatch','OwnerTriggers','OwnerLifetime','MaterialLinkage','ScopedOwnerGate','OwnerConnection',
  'CaptureSession','CaptureBarrier','CaptureRestoration','ImageArtifact','CardinalCapture','CapturePolicy','CaptureOwner','CaptureEvidenceSink','CaptureClock',
  'TankPresentationRecipe','TankPresentation','TankView','DecisionSnapshot','DecisionBurstBudget','DecisionHooks'];
 const sources=names.map(n=>path.join(main,'KneekuraDebug'+n+'.java'));
 const checks=['EvidenceClaim','CaptureWriter','RegisteredWorld','TankPresentation','DecisionSnapshot','DecisionHooks'];
 run(executable('javac'),['--release','17','-proc:none','-cp',classpath,'-d',output,...sources,...checks.map(n=>path.join(test,'KneekuraDebug'+n+'SelfTest.java'))]);
 for(const name of checks)run(executable('java'),['-cp',output+path.delimiter+classpath,'com.github.tartaricacid.touhoulittlemaid.sim.debug.KneekuraDebug'+name+'SelfTest']);
 console.log('Combined owner/Arena/camera actual Forge API compilation and writer/world source tests passed; no game process launched; full pinned mod compile remains separate');
}finally{await rm(output,{recursive:true,force:true});}
