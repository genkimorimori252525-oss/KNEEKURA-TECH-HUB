import {mkdtemp,rm} from 'node:fs/promises';
import path from 'node:path';
import os from 'node:os';
import {fileURLToPath} from 'node:url';
import {spawnSync} from 'node:child_process';
import {writeFileSync} from 'node:fs';
import assert from 'node:assert/strict';
import {validOriginalDecisionEvent,originalDecisionData} from '../evidence/original-decision-events.mjs';
const root=fileURLToPath(new URL('../../',import.meta.url));
const main=path.join(root,'debug-workspace/forge-bridge/src/main/java/com/github/tartaricacid/touhoulittlemaid/sim/debug');
const test=path.join(root,'debug-workspace/forge-bridge/src/test/java/com/github/tartaricacid/touhoulittlemaid/sim/debug');
const classpath=process.env.KNEEKURA_FORGE_CLASSPATH;
if(!classpath)throw new Error('KNEEKURA_FORGE_CLASSPATH must contain genuine official-mapped Forge1.20.1, Gson, LogUtils/SLF4J and annotation dependencies; no API stubs');
const executable=n=>process.env[n==='java'?'KNEEKURA_JAVA':'KNEEKURA_JAVAC']||(process.env.JAVA_HOME?path.join(process.env.JAVA_HOME,'bin',n+(process.platform==='win32'?'.exe':'')):n);
const output=await mkdtemp(path.join(os.tmpdir(),'kneekura-real-api-'));
function run(command,args,env={},cwd=root){
 // Genuine Windows dependency paths can exceed CreateProcess's argument limit.
 const argFile=path.join(output,'java.args');
 if(args.some(a=>/[\r\n]/.test(a)))throw new Error('Invalid Java argument line break');
 writeFileSync(argFile,args.map(a=>'"'+a.replaceAll('\\','\\\\').replaceAll('"','\\"')+'"').join('\n'));
 const result=spawnSync(command,['@'+argFile],{cwd,encoding:'utf8',timeout:120000,maxBuffer:4*1024*1024,windowsHide:true,env:{...process.env,...env}});
 if(result.stdout)process.stdout.write(result.stdout);if(result.stderr)process.stderr.write(result.stderr);
 if(result.error||result.status!==0)throw new Error('Real API source check failed '+command,{cause:result.error});
 return result.stdout;
}
try {
 const names=['Env','ActionJournal','ArenaController','ArenaOwnerGrant','ForgeArenaBackend','ArenaRuntime','Durability','EvidenceWriter',
  'OwnerFiles','OwnerInputs','OwnerDispatch','OwnerTriggers','OwnerLifetime','MaterialLinkage','ScopedOwnerGate','OwnerConnection',
  'CaptureSession','CaptureBarrier','CaptureRestoration','ImageArtifact','CardinalCapture','CapturePolicy','CaptureOwner','CaptureEvidenceSink','CaptureClock',
  'TankPresentationRecipe','TankPresentation','TankView','DecisionSnapshot','DecisionBurstBudget','DecisionHooks','TerrainField','SynchedCached',
  'DecisionAdapter','DecisionBurstRequest','AdapterSourceProof','TwilightForestDescriptor','TwilightForestReturnDescriptor','TwilightForestAdapter',
  'MotionTraceCache','MotionOverlayRuntime','MotionOverlayGeometry','MotionOverlay'];
 const sources=names.map(n=>path.join(main,'KneekuraDebug'+n+'.java'));
 const checks=['EvidenceClaim','CaptureWriter','RegisteredWorld','TankPresentation','DecisionSnapshot','DecisionHooks','PathNeighbors','EffectiveMalus','TeleportReturn','ProjectileResult','TerrainField','SynchedCached','MotionTraceCache','MotionOverlayGeometry','MotionWriter'];
 run(executable('javac'),['--release','17','-proc:none','-cp',classpath,'-d',output,...sources,...checks.map(n=>path.join(test,'KneekuraDebug'+n+'SelfTest.java')),path.join(test,'KneekuraDebugDecisionIdentityInterop.java')]);
 for(const name of checks.filter(n=>n!=='MotionWriter')){
  // Vanilla bootstrap can create logs; keep this new check's artifacts in its disposable output.
  const bootstrap=['PathNeighbors','EffectiveMalus','TeleportReturn','ProjectileResult'].includes(name);
  const cp=bootstrap?classpath.split(path.delimiter).map(p=>path.resolve(root,p)).join(path.delimiter):classpath;
  const stdout=run(executable('java'),['-cp',output+path.delimiter+cp,'com.github.tartaricacid.touhoulittlemaid.sim.debug.KneekuraDebug'+name+'SelfTest'],{},bootstrap?output:root);
  if(name==='PathNeighbors') {
   const line=stdout.split(/\r?\n/).find(l=>l.startsWith('NEIGHBOR_INTEROP:'));
   assert.ok(line,'production neighbor/Gson interop output required');
   const payload=JSON.parse(line.slice('NEIGHBOR_INTEROP:'.length));
   assert.equal(validOriginalDecisionEvent({source:{side:'SERVER'},payload}),true,payload.kind);
  }
  if(name==='EffectiveMalus') {
   const line=stdout.split(/\r?\n/).find(l=>l.startsWith('MALUS_INTEROP:'));
   assert.ok(line,'production custom malus/Gson interop output required');
   const payload=JSON.parse(line.slice('MALUS_INTEROP:'.length));
   assert.equal(validOriginalDecisionEvent({source:{side:'SERVER'},scope:{kind:'ENTITY_UUID',entityUuid:'00000000-0000-0000-0000-000000000001'},payload}),true,payload.kind);
  }
  if(name==='ProjectileResult') {
   const line=stdout.split(/\r?\n/).find(l=>l.startsWith('PROJECTILE_INTEROP:'));
   assert.ok(line,'production projectile/Gson interop output required');
   const interop=JSON.parse(line.slice('PROJECTILE_INTEROP:'.length));assert.equal(interop.rows.length,7);
   for(const payload of interop.rows)assert.equal(validOriginalDecisionEvent({source:{side:'SERVER'},scope:{kind:'ENTITY_UUID',entityUuid:interop.subjectUuid},payload}),true,payload.kind);
  }
 }
 for(const mode of ['OFF','ON'])run(executable('java'),['-cp',output+path.delimiter+classpath,'com.github.tartaricacid.touhoulittlemaid.sim.debug.KneekuraDebugMotionWriterSelfTest',mode],{KNEEKURA_DEBUG_MOTION_OVERLAY:mode==='ON'?'1':'0'});
 const identityOutput=run(executable('java'),['-cp',output+path.delimiter+classpath,'com.github.tartaricacid.touhoulittlemaid.sim.debug.KneekuraDebugDecisionIdentityInterop']);
 const identityLine=identityOutput.split(/\r?\n/).find(line=>line.startsWith('INTEROP:'));
 assert.ok(identityLine,'genuine identity-cap/Gson interop output required');
 const identityPayloads=JSON.parse(identityLine.slice(8));assert.equal(identityPayloads.length,4);
 for(const payload of identityPayloads){
  const row={source:{side:'SERVER'},payload};assert.equal(validOriginalDecisionEvent(row),true,payload.kind);
  const data=originalDecisionData(row);assert.equal(data.instanceIdentity,null);assert.equal(data.instanceIdentityStatus,'NOT_EXPOSED');
 }
 console.log('Genuine component128/Goal256 limits + production Gson omitted-null output preserve four original kinds as unknown identity');
 console.log('Combined owner/Arena/camera actual Forge API compilation and writer/world source tests passed; no game process launched; full pinned mod compile remains separate');
}finally{await rm(output,{recursive:true,force:true});}
