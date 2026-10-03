import {mkdtemp, mkdir, rm, realpath, writeFile} from 'node:fs/promises';
import os from 'node:os';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
import {spawnSync} from 'node:child_process';
import {beginAction,readActionOutcome} from './action-journal.mjs';
import assert from 'node:assert/strict';
import {buildOwnerGrantIntent} from './owner-grant.mjs';
const root=fileURLToPath(new URL('../../',import.meta.url));
const main=path.join(root,'debug-workspace/forge-bridge/src/main/java/com/github/tartaricacid/touhoulittlemaid/sim/debug');
const test=path.join(root,'debug-workspace/forge-bridge/src/test/java/com/github/tartaricacid/touhoulittlemaid/sim/debug');
const gson=process.env.KNEEKURA_GSON_JAR;
if(!gson||!path.isAbsolute(gson))throw new Error('KNEEKURA_GSON_JAR must name the absolute genuine Gson jar used by the source build');
const executable=name=>process.env[name==='java'?'KNEEKURA_JAVA':'KNEEKURA_JAVAC']||(process.env.JAVA_HOME?path.join(process.env.JAVA_HOME,'bin',name+(process.platform==='win32'?'.exe':'')):name);
const temp=await realpath(await mkdtemp(path.join(os.tmpdir(),'kneekura-java-source-')));
function run(command,args){const result=spawnSync(command,args,{cwd:root,encoding:'utf8',timeout:60000,maxBuffer:4*1024*1024});if(result.stdout)process.stdout.write(result.stdout);if(result.stderr)process.stderr.write(result.stderr);if(result.error||result.status!==0)throw new Error('Source verification failed: '+command+' '+args.join(' '),{cause:result.error});}
try {
 const classes=path.join(temp,'classes');await mkdir(classes);
 const sources=['KneekuraDebugEnv','KneekuraDebugReadyWriter','KneekuraDebugActionJournal','KneekuraDebugArenaController','KneekuraDebugArenaOwnerGrant','KneekuraDebugDurability','KneekuraDebugDecisionBurstBudget','KneekuraDebugDecisionBurstRequest','KneekuraDebugTerrainQueryRequest','KneekuraDebugAdapterSourceProof'].map(n=>path.join(main,n+'.java'));
 const tests=['KneekuraDebugReadyWriterSelfTest','KneekuraDebugActionJournalSelfTest','KneekuraDebugArenaControllerSelfTest','KneekuraDebugArenaOwnerGrantSelfTest','KneekuraDebugDurabilitySelfTest','KneekuraDebugDecisionBurstBudgetSelfTest','KneekuraDebugDecisionBurstRequestSelfTest','KneekuraDebugTerrainQueryRequestSelfTest','KneekuraDebugAdapterSourceProofSelfTest','KneekuraDebugActionJournalInterop','KneekuraDebugOwnerGrantInterop'].map(n=>path.join(test,n+'.java'));
 run(executable('javac'),['--release','17','-proc:none','-cp',gson,'-d',classes,...sources,...tests]);
 const cp=classes+path.delimiter+gson;
 for(const name of ['KneekuraDebugReadyWriterSelfTest','KneekuraDebugActionJournalSelfTest','KneekuraDebugArenaControllerSelfTest','KneekuraDebugArenaOwnerGrantSelfTest','KneekuraDebugDurabilitySelfTest','KneekuraDebugDecisionBurstBudgetSelfTest','KneekuraDebugDecisionBurstRequestSelfTest','KneekuraDebugTerrainQueryRequestSelfTest','KneekuraDebugAdapterSourceProofSelfTest'])run(executable('java'),['-cp',cp,'com.github.tartaricacid.touhoulittlemaid.sim.debug.'+name]);
 const runDir=path.join(temp,'run');await mkdir(runDir);
 const identity={debugSessionId:'session',runId:'run',runSnapshotId:'snapshot',processEpoch:1,experimentId:'experiment',subjects:{subject:'00000000-0000-0000-0000-000000000001'}};
 const arena={schemaVersion:1,arenaId:'arena',arenaEpoch:1,arenaRevision:0,baselineHash:'a'.repeat(64),bounds:{min:[0,0,0],max:[8,8,8]},allowedMutationBounds:{min:[0,0,0],max:[8,8,8]},resetClasses:{blocks:'RESETTABLE',entities:'UNKNOWN'}};
 for(const [key,type,args] of [['integers','wait_ticks',{ticks:2}],['numbers','teleport_subject',{subject_id:'subject',position:[1e-7,2.5,2],rotation:[-0,1e-7]}]]){
  const action={schemaVersion:1,debugSessionId:'session',runId:'run',runSnapshotId:'snapshot',processEpoch:1,experimentId:'experiment',arenaId:'arena',arenaEpoch:1,expectedArenaRevision:0,actionId:key,idempotencyKey:key,type,args};
  await beginAction({runDir,arena,identity,action});run(executable('java'),['-cp',cp,'com.github.tartaricacid.touhoulittlemaid.sim.debug.KneekuraDebugActionJournalInterop',runDir,key]);
  const receipt=await readActionOutcome({runDir,identity,idempotencyKey:key});assert.equal(receipt.status,'VERIFIED');assert.equal(receipt.dispatchAllowed,false);
 }
 const binding={schema_version:1,experiment_id:'experiment',generation:1,request_hash:'a'.repeat(64),target:{profile_id:'b'.repeat(64),index_snapshot_id:'c'.repeat(64),build_artifact_hash:'d'.repeat(64),source_revision:'e'.repeat(40),dirty_hash:'f'.repeat(64),config_hash:'1'.repeat(64),resource_hash:'2'.repeat(64)},arena_id:'arena',arena_baseline_hash:'3'.repeat(64),assertions_hash:'4'.repeat(64)};
 for(const captureOnly of [false,true]) {
  const request={experiment_id:'experiment',generation:1,target:binding.target,arena:{arena_id:'arena',baseline_hash:binding.arena_baseline_hash,bounds:{min:[0,64,0],max:[4,68,4]}},subjects:[{subject_id:'subject',uuid:'00000000-0000-0000-0000-000000000001',entity_type:'minecraft:armor_stand'}],budgets:{time_budget_ms:1000,max_actions:captureOnly?0:2,max_captures:4},initial_state:[],actions:captureOnly?[]:[{operation:'wait_ticks',action_id:'wait',ticks:1}]};
  const grant=buildOwnerGrantIntent({binding,request,identity:{debugSessionId:'session',runId:'run',runSnapshotId:'snapshot',processEpoch:1,handshakeNonce:'nonce-0000000000000001',dimensionId:'minecraft:overworld',disposableWorldName:'KNEEKURA_DEBUG_WORLD'},selection:{grantId:'grant',leaseId:'lease',arenaEpoch:1,expectedArenaRevision:0,allowedActions:captureOnly?[]:['wait_ticks']}});
  const file=path.join(temp,'owner-grant.json');await writeFile(file,JSON.stringify(grant));run(executable('java'),['-cp',cp,'com.github.tartaricacid.touhoulittlemaid.sim.debug.KneekuraDebugOwnerGrantInterop',file]);
 }
 console.log('All Java/source receipt tests passed; no Minecraft was launched; runtime attestation remains NOT_ESTABLISHED');
}finally{await rm(temp,{recursive:true,force:true});}
