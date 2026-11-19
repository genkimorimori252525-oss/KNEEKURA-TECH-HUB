import {mkdtemp,rm,readFile} from 'node:fs/promises';
import path from 'node:path';
import os from 'node:os';
import {fileURLToPath} from 'node:url';
import {spawnSync} from 'node:child_process';
import {writeFileSync} from 'node:fs';
import assert from 'node:assert/strict';
import {validDecisionSnapshot} from '../evidence/debug-workspace-decision-adapter.mjs';
import {validOriginalDecisionEvent,originalDecisionData,appendOriginalDecisionEvents} from '../evidence/original-decision-events.mjs';
import {buildTankStatus} from '../evidence/tank-status.mjs';
import {buildTankPresentationResource} from './tank-resource.mjs';
import {sha256,stableJson} from './json.mjs';
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
 const mixins=JSON.parse(await readFile(path.join(root,'debug-workspace/forge-bridge/src/main/resources/kneekura-decision.mixins.json'),'utf8'));
 for(const name of ['OneShot','GateBehavior'])assert.ok(mixins.mixins.includes('KneekuraDebug'+name+'DecisionMixin'),'known-control mixin resource registration');
 assert.ok(mixins.mixins.includes('KneekuraDebugScheduledActivityMixin'),'original activity call-site mixin registration');
 assert.ok(mixins.mixins.includes('KneekuraDebugNavigationResultMixin'),'base Navigation normal-return mixin registration');
 assert.ok(mixins.mixins.includes('KneekuraDebugBrainNavigationMixin'),'original Brain/Navigation call-site mixin registration');
 const names=['Env','ActionJournal','ArenaController','ArenaOwnerGrant','ForgeArenaBackend','ArenaRuntime','Durability','EvidenceWriter','ClientBootstrap','ReadyWriter','ServerObserver','TargetTracker','ShutdownCoordinator',
  'OwnerFiles','OwnerInputs','OwnerDispatch','OwnerTriggers','OwnerLifetime','MaterialLinkage','ScopedOwnerGate','OwnerConnection',
  'CaptureSession','CaptureBarrier','CaptureRestoration','ImageArtifact','CardinalCapture','CapturePolicy','CaptureOwner','CaptureEvidenceSink','CaptureClock',
  'TankPresentationRecipe','TankPresentation','TankStatus','TankView','TankRotationController','TankRotationPlan','ForgeTankRotationBackend','DecisionSnapshot','DecisionBurstBudget','DecisionHooks','TerrainField','SynchedCached',
  'DecisionAdapter','DecisionBurstRequest','AdapterSourceProof','TwilightForestDescriptor','TwilightForestReturnDescriptor','TwilightForestAdapter',
  'MotionTraceCache','RelatedProjectileTraceCache','MotionOverlayRuntime','MotionOverlayGeometry','MotionOverlay',
  'TerrainQueryRequest','TerrainRuntime','LoadedGroundSource','DecisionBurstRuntime','DecisionAdapterRegistry'];
 const sources=[...names.map(n=>path.join(main,'KneekuraDebug'+n+'.java')),...['Path','Brain','Behavior','OneShot','GateBehavior'].map(n=>path.join(main,'decisionmixin/KneekuraDebug'+n+'DecisionMixin.java')),path.join(main,'decisionmixin/KneekuraDebugScheduledActivityMixin.java'),path.join(main,'decisionmixin/KneekuraDebugNavigationResultMixin.java'),path.join(main,'decisionmixin/KneekuraDebugBrainNavigationMixin.java')];
 const checks=['EvidenceClaim','CaptureWriter','RegisteredWorld','TankPresentation','TankStatus','TankStatusWriter','TankPreflight','TankRotation','TankRotationFiles','TankRotationBackend','DecisionSnapshot','TypedMemory','BehaviorControl','BrainActivity','NavigationResult','BrainNavigation','BrainMemorySource','ActivityRequirement','BrainStartLoop','BrainMemoryCheck','BrainStart','BrainComputeCondition','BrainCompute','BrainTickStop','BrainStop','DecisionHooks','PathNeighbors','PathHeap','PathClosed','PathNodes','PathGWrite','PathDistance','EffectiveMalus','GhastReach','TeleportReturn','ProjectileResult','TerrainField','SynchedCached','MotionTraceCache','RelatedProjectileTrace','MotionOverlayGeometry','MotionWriter'];
 const selected=process.env.KNEEKURA_API_SELFTEST_FILTER?.split(',');
 if(selected?.some(n=>!checks.includes(n)))throw new Error('UNKNOWN_API_SELFTEST_FILTER');
 run(executable('javac'),['--release','17','-proc:none','-cp',classpath,'-d',output,...sources,...checks.map(n=>path.join(test,'KneekuraDebug'+n+'SelfTest.java')),path.join(test,'KneekuraDebugDecisionIdentityInterop.java')]);
 for(const name of checks.filter(n=>n!=='MotionWriter'&&(!selected||selected.includes(n)))){
  // Vanilla bootstrap can create logs; keep this new check's artifacts in its disposable output.
  const bootstrap=['BrainMemorySource','ActivityRequirement','BrainStartLoop','BrainMemoryCheck','BrainStart','BrainComputeCondition','BrainCompute','BrainTickStop','BrainStop','BrainNavigation','NavigationResult','BrainActivity','BehaviorControl','TypedMemory','PathNeighbors','PathHeap','PathClosed','PathNodes','PathGWrite','PathDistance','EffectiveMalus','GhastReach','TeleportReturn','ProjectileResult'].includes(name);
  const cp=bootstrap?classpath.split(path.delimiter).map(p=>path.resolve(root,p)).join(path.delimiter):classpath;
  const extra=[];
  if(name==='TankPreflight') {
   const recipe={v:1,kind:'tank_recipe',dimension:'minecraft:overworld',origin:{x:0,y:64,z:0},dimensions:{width:16,height:8,depth:16},presentation:{gridSpacing:1,mode:'NATIVE'}};
   const saved={status:'GEOMETRY_VERIFIED',recipe,recipeHash:sha256(stableJson(recipe)),displayMode:'NATIVE'};
   const capsule=path.join(output,'tank-resource.zip');
   writeFileSync(capsule,buildTankPresentationResource({saved,profile:{kind:'OBSERVE_GRID',grid:true,brightness:false,motion:false,decisionChannels:[]}}));extra.push(capsule);
  }
  const stdout=run(executable('java'),['-cp',output+path.delimiter+cp,'com.github.tartaricacid.touhoulittlemaid.sim.debug.KneekuraDebug'+name+'SelfTest',...extra],{},bootstrap?output:root);
   if(name==='TankStatus') {
    const identity={debugSessionId:'s',runId:'r',runSnapshotId:'snap',processEpoch:1,arenaEpoch:0};
    const payloads=stdout.split(/\r?\n/).filter(l=>l.startsWith('TANK_STATUS_INTEROP:')).map(l=>JSON.parse(l.slice('TANK_STATUS_INTEROP:'.length)));
    assert.equal(payloads.length,2);
    for(const [index,payload] of payloads.entries()) {
     const packet=buildTankStatus({identity,observations:[{kind:'observation',...identity,lane:'TANK_PRESENTATION_STATUS',
      observationId:'obs:java:'+index,writerSeq:index+1,gameTime:100,scope:{kind:'GLOBAL_HEALTH'},source:{side:'CLIENT'},
      epistemicStatus:'OBSERVED',completeness:{complete:true},payload}]});
     assert.equal(packet.presentation.pixelEvidence.status,'NOT_CAPTURED');
     assert.equal(packet.presentation.drawSubmitted.value,index===0);
     assert.equal(packet.presentation.freshness.status,'STORED');
    }
    console.log('Native Tank status Gson / strict Node consumer: drawn and unavailable cases passed');
   }
   if(name==='BrainMemorySource') {
    const lines=stdout.split(/\r?\n/).filter(l=>l.startsWith('BRAIN_MEMORY_SOURCE_INTEROP:'));
    assert.equal(lines.length,26,'genuine base branches, both parents, source/base/virtual separation, caps, nested and eight-check prefix');
    const records=lines.map((line,index)=>({source:{side:'SERVER'},observationId:'brain-memory-source-gson:'+index,gameTime:100,payload:JSON.parse(line.slice('BRAIN_MEMORY_SOURCE_INTEROP:'.length))}));
    assert.ok(records.every(validOriginalDecisionEvent),'actual original Map/presence/base/virtual Gson satisfies strict consumer');
    assert.equal(records[0].payload.data.slotStatus,'NULL');assert.equal(records[0].payload.data.presenceStatus,'NOT_CALLED');
    for(const index of [1,2,7,8])assert.equal(records[index].payload.data.presenceStatus,'NOT_CALLED');
    for(let index=3;index<7;index++){const data=records[index].payload.data;assert.equal(data.presenceStatus,'NORMAL_RETURN');assert.equal(data.presenceResult,index%2===0);assert.equal(data.presenceSite,index<5?'VALUE_PRESENT':'VALUE_ABSENT');}
    assert.equal(records[9].payload.data.baseResult,false);assert.equal(records[9].payload.data.result,true);assert.equal(records[10].payload.kind,'BRAIN_ACTIVITY_MEMORY_SOURCE_RETURN');
    for(const index of [11,12])assert.equal(records[index].payload.data.memoryModuleStatus,'NOT_EXPOSED');assert.equal(records[13].payload.data.memorySourceInvocationId,'memory-source:7:256');assert.equal(records[14].payload.data.instanceIdentityStatus,'NOT_EXPOSED');
    assert.equal(records[15].payload.data.memorySourceInvocationId,'memory-source:7:2');assert.equal(records[16].payload.data.memorySourceInvocationId,'memory-source:7:1');assert.equal(records[17].payload.kind,'BRAIN_ACTIVITY_MEMORY_SOURCE_RETURN');
    assert.deepEqual(records.slice(-8).map(r=>r.payload.data.checkIndex),[1,2,3,4,5,6,7,8]);
    const stages={},capabilities={},timeline=[];appendOriginalDecisionEvents(records,stages,capabilities,timeline);assert.equal(stages.EVALUATION.facts.length,26);assert.equal(capabilities.brain_navigation.status,'PARTIAL');assert.equal(capabilities.brain_activity.status,'PARTIAL');
    for(const stage of ['CANDIDATE','SELECTION','EXECUTION','RESULT'])assert.equal(stages[stage],undefined);
    console.log('Twenty-six actual Brain memory source/Gson cases preserve original Map/presence and base/virtual returns');
   }
   if(name==='ActivityRequirement') {
    const lines=stdout.split(/\r?\n/).filter(l=>l.startsWith('ACTIVITY_REQUIREMENT_INTEROP:'));
    assert.equal(lines.length,17,'actual predicate/two callers, missing/empty/source checks, caps, unknowns and nested scopes');
    const records=lines.map((line,index)=>({source:{side:'SERVER'},observationId:'activity-requirement-gson:'+index,gameTime:100,payload:JSON.parse(line.slice('ACTIVITY_REQUIREMENT_INTEROP:'.length))}));
    assert.ok(records.every(validOriginalDecisionEvent),'actual Activity requirement Gson satisfies strict consumer');
    assert.equal(records[0].payload.data.mapContains,false);assert.equal(records[0].payload.data.checks.length,0);assert.equal(records[1].payload.data.mapContains,true);assert.equal(records[1].payload.data.result,true);assert.equal(records[1].payload.data.checks.length,0);
    assert.equal(records[2].payload.data.checks.length,2);assert.equal(records[4].payload.data.callerSite,'FIRST_VALID');assert.equal(records[5].payload.data.callerSite,'FIRST_VALID');assert.equal(records[6].payload.data.callerSite,'IF_POSSIBLE');
    assert.equal(records[11].payload.data.checks.length,8);assert.equal(records[11].payload.data.checksTruncated,true);
    assert.equal(records.at(-2).payload.data.requirementInvocationId,'activity-requirement:7:256');assert.equal(records.at(-1).payload.data.instanceIdentityStatus,'NOT_EXPOSED');
    const stages={},capabilities={},timeline=[];appendOriginalDecisionEvents(records,stages,capabilities,timeline);assert.equal(stages.EVALUATION.facts.length,17);assert.equal(capabilities.brain_activity.status,'PARTIAL');
    for(const stage of ['CANDIDATE','SELECTION','EXECUTION','RESULT'])assert.equal(stages[stage],undefined);
    console.log('Seventeen actual Activity requirement/Gson cases preserve original map/check calls and both caller branches');
   }
   if(name==='BrainStartLoop') {
    const lines=stdout.split(/\r?\n/).filter(l=>l.startsWith('BRAIN_START_LOOP_INTEROP:'));
    assert.equal(lines.length,16,'original source Activity/control normal returns, branches, caps and nested scopes');
    const records=lines.map((line,index)=>({source:{side:'SERVER'},observationId:'brain-start-loop-gson:'+index,gameTime:100,payload:JSON.parse(line.slice('BRAIN_START_LOOP_INTEROP:'.length))}));
    assert.ok(records.every(validOriginalDecisionEvent),'actual original start-loop Gson satisfies strict consumer');
    assert.equal(records[0].payload.data.activities.length,2);assert.equal(records[0].payload.data.activities[0].controls.length,3);
    assert.equal(records[1].payload.data.sourceGameTimeStatus,'NOT_CAPTURED');assert.equal(records[4].payload.data.activitiesTruncated,true);
    assert.equal(records[5].payload.data.activities[0].controlsTruncated,true);assert.equal(records[10].payload.data.loopInvocationId,'start-loop:7:2');
    assert.equal(records[12].payload.data.activities[0].controls[0].capturedTryStartInvocationId,'try-start:7:1');
    assert.equal(records.at(-2).payload.data.loopInvocationId,'start-loop:7:256');assert.equal(records.at(-1).payload.data.instanceIdentityStatus,'NOT_EXPOSED');
    const stages={},capabilities={},timeline=[];appendOriginalDecisionEvents(records,stages,capabilities,timeline);assert.equal(stages.EVALUATION.facts.length,16);assert.equal(capabilities.brain_navigation.status,'PARTIAL');
    for(const stage of ['CANDIDATE','SELECTION','EXECUTION','RESULT'])assert.equal(stages[stage],undefined);
    console.log('Sixteen actual Brain start-loop/Gson cases preserve original calls and bounded prefixes');
   }
   if(name==='BrainMemoryCheck') {
    const lines=stdout.split(/\r?\n/).filter(l=>l.startsWith('BRAIN_MEMORY_CHECK_INTEROP:'));
    assert.equal(lines.length,16,'original source memory check returns, unknowns, explicit prefix tail and nested scopes');
    const records=lines.map((line,index)=>({source:{side:'SERVER'},observationId:'brain-memory-check-gson:'+index,gameTime:100,payload:JSON.parse(line.slice('BRAIN_MEMORY_CHECK_INTEROP:'.length))}));
    assert.ok(records.every(validOriginalDecisionEvent),'actual original memory requirement Gson satisfies strict consumer');
    assert.equal(records[0].payload.data.result,false);assert.equal(records[1].payload.data.result,true);assert.equal(records[1].payload.data.checks.length,3);
    assert.equal(records[9].payload.data.checks.length,8);assert.equal(records[9].payload.data.checksTruncated,true);
    assert.equal(records.at(-2).payload.data.requirementInvocationId,'memory-requirement:7:256');assert.equal(records.at(-1).payload.data.instanceIdentityStatus,'NOT_EXPOSED');
    const stages={},capabilities={},timeline=[];appendOriginalDecisionEvents(records,stages,capabilities,timeline);assert.equal(stages.EVALUATION.facts.length,16);assert.equal(capabilities.brain_navigation.status,'PARTIAL');
    for(const stage of ['CANDIDATE','SELECTION','EXECUTION','RESULT'])assert.equal(stages[stage],undefined);
    console.log('Sixteen actual Brain memory requirement/Gson cases preserve original checks and bounded prefixes');
   }
   if(name==='BrainStart') {
    const lines=stdout.split(/\r?\n/).filter(l=>l.startsWith('BRAIN_START_INTEROP:'));
    assert.equal(lines.length,42,'original short circuit, duration RNG, direct compute/start scopes, capped children and unknowns');
    const records=lines.map((line,index)=>({source:{side:'SERVER'},observationId:'brain-start-gson:'+index,gameTime:100,payload:JSON.parse(line.slice('BRAIN_START_INTEROP:'.length))}));
    assert.ok(records.every(validOriginalDecisionEvent),'actual original start Gson satisfies strict consumer');
    assert.equal(records[0].payload.data.condition,'HAS_REQUIRED_MEMORIES');assert.equal(records[0].payload.data.result,false);
    assert.equal(records[3].payload.data.condition,'CHECK_EXTRA_START');assert.equal(records[3].payload.data.result,false);
    assert.equal(records[6].payload.data.capturedComputeInvocationIds.length,1);assert.equal(records[7].payload.data.capturedSinkInvocationIds.length,1);assert.equal(records[8].payload.data.result,true);
    const stages={},capabilities={},timeline=[];appendOriginalDecisionEvents(records,stages,capabilities,timeline);
    assert.equal(stages.EVALUATION.facts.length,40);assert.equal(stages.EXECUTION.facts.length,2);assert.equal(capabilities.brain_navigation.status,'PARTIAL');
    for(const stage of ['CANDIDATE','SELECTION','RESULT'])assert.equal(stages[stage],undefined);
    console.log('Forty-two actual Brain start/Gson cases preserve original conditions, duration RNG and direct child scopes');
   }
     if(name==='BrainComputeCondition') {
    const lines=stdout.split(/\r?\n/).filter(l=>l.startsWith('BRAIN_COMPUTE_CONDITION_INTEROP:'));
    assert.equal(lines.length,35,'original reached/Path predicate booleans, signed operands and bounded unknowns');
    const records=lines.map((line,index)=>({source:{side:'SERVER'},observationId:'brain-compute-condition-gson:'+index,gameTime:100,payload:JSON.parse(line.slice('BRAIN_COMPUTE_CONDITION_INTEROP:'.length))}));
    assert.ok(records.every(validOriginalDecisionEvent),'actual original compute condition Gson satisfies strict consumer');
    console.log('Thirty-five actual Brain compute predicate/Gson cases preserve original booleans and returned operands');
   }
   if(name==='BrainCompute') {
    const lines=stdout.split(/\r?\n/).filter(l=>l.startsWith('BRAIN_COMPUTE_INTEROP:'));
    assert.equal(lines.length,59,'original private branch, source return/write order, direct IDs, finite operands and capped unknowns');
    const records=lines.map((line,index)=>({source:{side:'SERVER'},observationId:'brain-compute-gson:'+index,gameTime:100,payload:JSON.parse(line.slice('BRAIN_COMPUTE_INTEROP:'.length))}));
    assert.ok(records.every(validOriginalDecisionEvent),'actual original compute Gson satisfies strict consumer');
    console.log('Fifty-nine actual Brain compute/Gson cases preserve source call returns, field writes and unknown adoption');
   }
   if(name==='BrainTickStop') {
   const lines=stdout.split(/\r?\n/).filter(l=>l.startsWith('BRAIN_TICK_STOP_INTEROP:'));
   assert.equal(lines.length,17,'original short circuit, branch, completed-condition-before-throw and capped component cases');
   const records=lines.map((line,index)=>({source:{side:'SERVER'},observationId:'brain-tick-stop-gson:'+index,gameTime:100,payload:JSON.parse(line.slice('BRAIN_TICK_STOP_INTEROP:'.length))}));
   assert.ok(records.every(validOriginalDecisionEvent),'actual original condition/dispatch Gson satisfies strict consumer');
   assert.deepEqual(records.slice(3,5).map(r=>r.payload.kind),['BRAIN_PATH_CONDITION_RETURN','BRAIN_PATH_DISPATCH_RETURN'],'timedOut true never invents canStillUse');
   assert.equal(records[3].payload.data.condition,'TIMED_OUT');assert.equal(records[3].payload.data.result,true);assert.equal(records[4].payload.data.branch,'STOP');
   assert.equal(records[7].payload.data.branch,'TICK');assert.equal(records[14].payload.data.instanceIdentityStatus,'NOT_EXPOSED');
   const stages={},capabilities={},timeline=[];appendOriginalDecisionEvents(records,stages,capabilities,timeline);
   assert.equal(stages.EVALUATION.facts.length,12);assert.equal(stages.EXECUTION.facts.length,5);assert.equal(capabilities.brain_navigation.status,'PARTIAL');
   for(const stage of ['CANDIDATE','SELECTION','RESULT'])assert.equal(stages[stage],undefined);
   console.log('Seventeen actual Brain tick-or-stop/Gson cases preserve virtual booleans, short circuit and direct concrete scopes');
  }
  if(name==='BrainStop') {
   const lines=stdout.split(/\r?\n/).filter(l=>l.startsWith('BRAIN_STOP_INTEROP:'));
   assert.equal(lines.length,39,'genuine stop, custom retained state, absent/malformed slots and caps');
   const records=lines.map((line,index)=>({source:{side:'SERVER'},observationId:'brain-stop-gson:'+index,gameTime:100,payload:JSON.parse(line.slice('BRAIN_STOP_INTEROP:'.length))}));
   assert.ok(records.every(validOriginalDecisionEvent),'actual production stop Gson satisfies consumer contract');
   assert.deepEqual(records.slice(1,5).map(r=>r.payload.kind),['BRAIN_PATH_NAVIGATION_STOP_RETURN','BRAIN_PATH_MEMORY_ERASE_RETURN','BRAIN_PATH_MEMORY_ERASE_RETURN','BRAIN_PATH_SINK_RETURN']);
   assert.equal(new Set(records.slice(1,5).map(r=>r.payload.data.sinkInvocationId)).size,1,'same original concrete stop invocation');
   assert.equal(records[5].payload.data.cachedPath.present,true,'normal custom stop can retain cached Path');
   assert.equal(records[6].payload.data.slotAtReturn.present,true,'normal custom erase can retain Optional slot');
   const stages={},capabilities={},timeline=[];appendOriginalDecisionEvents(records,stages,capabilities,timeline);
   assert.equal(timeline.length,39);assert.equal(stages.EXECUTION.facts.length,39);assert.equal(capabilities.brain_navigation.status,'PARTIAL');
   for(const stage of ['CANDIDATE','SELECTION','RESULT'])assert.equal(stages[stage],undefined);
   console.log('Thirty-nine actual Brain stop/Gson cases preserve original void returns, cached slot scope and unknown arrival');
  }
  if(name==='BrainNavigation') {
   const lines=stdout.split(/\r?\n/).filter(l=>l.startsWith('BRAIN_NAVIGATION_INTEROP:'));
   assert.equal(lines.length,24,'genuine sink call, original virtual return, cached references and explicit unknown cases');
   const records=lines.map((line,index)=>({source:{side:'SERVER'},observationId:'brain-navigation-gson:'+index,gameTime:100,payload:JSON.parse(line.slice('BRAIN_NAVIGATION_INTEROP:'.length))}));
   assert.ok(records.every(validOriginalDecisionEvent),'actual production Brain/Navigation Gson satisfies consumer contract');
   assert.deepEqual(records.slice(0,3).map(r=>r.payload.kind),['BRAIN_PATH_MEMORY_WRITE_RETURN','BRAIN_PATH_NAVIGATION_RETURN','BRAIN_PATH_SINK_RETURN']);
   assert.equal(new Set(records.slice(0,3).map(r=>r.payload.data.sinkInvocationId)).size,1,'same original concrete invocation');
   assert.equal(records[4].payload.data.result,false,'final virtual return can differ from the base Navigation true');
   const stages={},capabilities={},timeline=[];appendOriginalDecisionEvents(records,stages,capabilities,timeline);
   assert.equal(timeline.length,24);assert.equal(stages.EXECUTION.facts.length,24);assert.equal(capabilities.brain_navigation.status,'PARTIAL');
   for(const stage of ['CANDIDATE','SELECTION','RESULT'])assert.equal(stages[stage],undefined);
   console.log('Twenty-four actual Brain/Navigation/Gson cases preserve call scope, final virtual return and unknown arrival');
  }
  if(name==='NavigationResult') {
   const lines=stdout.split(/\r?\n/).filter(l=>l.startsWith('NAVIGATION_RESULT_INTEROP:'));
   assert.equal(lines.length,11,'genuine Navigation original boolean, cached/reference and cap cases');
   const records=lines.map((line,index)=>({source:{side:'SERVER'},observationId:'navigation-gson:'+index,gameTime:100,payload:JSON.parse(line.slice('NAVIGATION_RESULT_INTEROP:'.length))}));
   assert.ok(records.every(validOriginalDecisionEvent),'actual production Navigation Gson satisfies consumer contract');
   assert.equal(records[1].payload.data.requestedMatchesCachedPath,false,'true can retain an equal-route distinct Path');
   assert.equal(records[2].payload.data.requestedPath.cachedFields.data.canReach,false,'true does not imply reachable target');
   assert.equal(Object.hasOwn(records.at(-1).payload.data.requestedPath.identity,'token'),false,'Gson omits capped Path token');
   const stages={},capabilities={},timeline=[];appendOriginalDecisionEvents(records,stages,capabilities,timeline);
   assert.equal(timeline.length,11);assert.equal(stages.EXECUTION.facts.length,11);assert.equal(capabilities.navigation_move_to.status,'PARTIAL');
   for(const stage of ['CANDIDATE','SELECTION','RESULT'])assert.equal(stages[stage],undefined);
   console.log('Eleven actual navigation-result/Gson cases separate original boolean, cached Path and unknown arrival');
  }
  if(name==='BrainActivity') {
   const lines=stdout.split(/\r?\n/).filter(l=>l.startsWith('BRAIN_ACTIVITY_INTEROP:'));
   assert.equal(lines.length,14,'genuine original activity and compiled-fixture inner returns');
   const records=lines.map((line,index)=>({source:{side:'SERVER'},observationId:'activity-gson:'+index,gameTime:100,payload:JSON.parse(line.slice('BRAIN_ACTIVITY_INTEROP:'.length))}));
   assert.ok(records.every(validOriginalDecisionEvent),'actual production activity Gson satisfies consumer contract');
   assert.equal(Object.hasOwn(records.at(-1).payload.data,'scheduleInstanceIdentity'),false,'Gson omits capped schedule token');
   const stages={},capabilities={},timeline=[];appendOriginalDecisionEvents(records,stages,capabilities,timeline);
   assert.equal(timeline.length,14);assert.equal(capabilities.brain_activity.status,'PARTIAL');
   for(const stage of ['CANDIDATE','SELECTION','RESULT'])assert.equal(stages[stage],undefined);
   console.log('Fourteen actual activity-call/Gson cases preserve original scope and unknown outcomes');
  }
  if(name==='BehaviorControl') {
   const lines=stdout.split(/\r?\n/).filter(l=>l.startsWith('BEHAVIOR_CONTROL_INTEROP:'));
   assert.equal(lines.length,13,'genuine independent-control normal returns and capped identity required');
   const records=lines.map((line,index)=>({source:{side:'SERVER'},observationId:'control-gson:'+index,gameTime:100,payload:JSON.parse(line.slice('BEHAVIOR_CONTROL_INTEROP:'.length))}));
   assert.ok(records.every(validOriginalDecisionEvent),'actual production Gson control facts satisfy existing event contract');
   const cap=records.at(-1);assert.equal(Object.hasOwn(cap.payload.data,'instanceIdentity'),false,'production Gson omits capped token');
   assert.equal(originalDecisionData(cap).instanceIdentityStatus,'NOT_EXPOSED');
   const stages={},capabilities={},timeline=[];appendOriginalDecisionEvents(records,stages,capabilities,timeline);
   assert.equal(timeline.length,13);assert.equal(stages.CANDIDATE,undefined);assert.equal(stages.SELECTION,undefined);assert.equal(stages.RESULT,undefined);
   assert.ok(stages.EVALUATION.facts.every(f=>f.value.reasonStatus==='NOT_EXPOSED'));
   console.log('Thirteen actual independent-control/Gson cases retain parent-only returns and unknown identities without causal selection/result');
  }
  if(name==='TypedMemory') {
   const line=stdout.split(/\r?\n/).find(l=>l.startsWith('MEMORY_INTEROP:'));
   assert.ok(line,'genuine cached memory/Gson interop output required');
   const values=JSON.parse(line.slice(15)); assert.equal(values.length,9);
   const payload={schema:'kneekura.vanilla-decision-snapshot/v1',targetRevision:19,semantics:'MOB_COMPONENT_SNAPSHOT_ONLY',sections:{}};
   for(const name of ['goal_scheduler','brain_memory','brain_activities','navigation_path','movement_control'])payload.sections[name]={status:'NOT_EXPOSED'};
   for(const value of values){
    const revision=value.data?.instanceIdentity?.targetRevision ?? 19;payload.targetRevision=revision;
    payload.sections.brain_memory={status:'AVAILABLE',data:{entries:[{registered:true,present:true,key:'minecraft:fixture',value}],truncated:false}};
    assert.equal(validDecisionSnapshot(payload),true,value.kind ?? value.className ?? value.detail);
   }
   const capped=values[3]; assert.equal(Object.hasOwn(capped.data.instanceIdentity,'token'),false,'production Gson omits unavailable reference token');
   console.log('Nine actual typed-memory/Gson cases preserve cached state and explicit unknowns across Java/JS');
  }
  if(name==='PathNeighbors') {
   const line=stdout.split(/\r?\n/).find(l=>l.startsWith('NEIGHBOR_INTEROP:'));
   assert.ok(line,'production neighbor/Gson interop output required');
   const payload=JSON.parse(line.slice('NEIGHBOR_INTEROP:'.length));
   assert.equal(validOriginalDecisionEvent({source:{side:'SERVER'},payload}),true,payload.kind);
  }
  if(name==='PathHeap') {
   const lines=stdout.split(/\r?\n/).filter(l=>l.startsWith('HEAP_INTEROP:'));
   assert.equal(lines.length,8,'bounded heap/Gson interop returns required');
   for(const line of lines){const payload=JSON.parse(line.slice('HEAP_INTEROP:'.length));
    assert.equal(validOriginalDecisionEvent({source:{side:'SERVER'},payload}),true,payload.kind);}
  }
  if(name==='PathClosed') {
   const lines=stdout.split(/\r?\n/).filter(l=>l.startsWith('CLOSED_INTEROP:'));
   assert.equal(lines.length,2,'actual-reference and identity-limit checkpoint/Gson interop required');
   for(const line of lines){const payload=JSON.parse(line.slice('CLOSED_INTEROP:'.length));
    assert.equal(validOriginalDecisionEvent({source:{side:'SERVER'},payload}),true,payload.kind);}
  }
  if(name==='PathNodes') {
   const lines=stdout.split(/\r?\n/).filter(l=>l.startsWith('PATH_NODES_INTEROP:'));
   assert.equal(lines.length,7,'actual partial/full/null/custom/empty/max-prefix Path/Gson interop required');
   for(const line of lines){const payload=JSON.parse(line.slice('PATH_NODES_INTEROP:'.length));
    assert.equal(validOriginalDecisionEvent({source:{side:'SERVER'},payload}),true,payload.kind);}
  }
  if(name==='PathGWrite') {
   const lines=stdout.split(/\r?\n/).filter(l=>l.startsWith('G_WRITE_INTEROP:'));
   assert.equal(lines.length,5,'actual written argument/cached field/predecessor/unknown/capture-gate Gson interop required');
   for(const line of lines){const payload=JSON.parse(line.slice('G_WRITE_INTEROP:'.length));
    assert.equal(validOriginalDecisionEvent({source:{side:'SERVER'},payload}),true,payload.kind);}
  }
  if(name==='PathDistance') {
   const lines=stdout.split(/\r?\n/).filter(l=>l.startsWith('DISTANCE_INTEROP:'));
   assert.equal(lines.length,4,'actual protected override/base/null/nonfinite/later-cache Gson interop required');
   for(const line of lines){const payload=JSON.parse(line.slice('DISTANCE_INTEROP:'.length));
    assert.equal(validOriginalDecisionEvent({source:{side:'SERVER'},payload}),true,payload.kind);}
  }
  if(name==='EffectiveMalus') {
   const line=stdout.split(/\r?\n/).find(l=>l.startsWith('MALUS_INTEROP:'));
   assert.ok(line,'production custom malus/Gson interop output required');
   const payload=JSON.parse(line.slice('MALUS_INTEROP:'.length));
   assert.equal(validOriginalDecisionEvent({source:{side:'SERVER'},scope:{kind:'ENTITY_UUID',entityUuid:'00000000-0000-0000-0000-000000000001'},payload}),true,payload.kind);
  }
  if(name==='GhastReach') {
   const line=stdout.split(/\r?\n/).find(l=>l.startsWith('GHAST_REACH_INTEROP:'));
   assert.ok(line,'production Ghast reach/Gson interop output required');
   const payload=JSON.parse(line.slice('GHAST_REACH_INTEROP:'.length));
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
 console.log('Actual Forge API compilation and '+(selected?'selected tests '+selected.join(','):'all source tests')+' passed; no game process launched; full pinned mod compile remains separate');
}finally{await rm(output,{recursive:true,force:true});}
