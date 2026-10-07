/** Explicit finite native acceptance. Original saves are raw-byte inputs only. */
import assert from 'node:assert/strict';
import * as fs from 'node:fs/promises';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
import {execFileSync} from 'node:child_process';
import {sha256,stableJson} from '../json.mjs';
import {registerBridgeRequest} from '../registration.mjs';
import {launchDebugRun,readCurrent,stopCurrent} from '../../core.mjs';
import {evidenceRuntimeFromCurrent} from '../../evidence/runtime.mjs';
import {finalizeEvidenceRun} from '../../evidence/finalize.mjs';
import {publishTankRoster,inspectTankRoster} from '../tank-roster.mjs';
import {requestDeclaredCapture} from '../owner-action-adapter.mjs';
import {cameraPlan} from '../camera-plan.mjs';
import {captureBundle} from '../capture-bundle.mjs';
import {prepareTankResourceFile} from '../../tank-cli.mjs';
import {finalizeNativeTrial} from './trial-finalization.mjs';

const option=name=>{const i=process.argv.indexOf('--'+name);if(i<0||!process.argv[i+1])throw Error('Missing --'+name);return path.resolve(process.argv[i+1]);};
const templateFile=option('template'),original=option('original'),classpathFile=option('classpath-file'),javaHome=option('java-home'),parent=option('private-parent'),fixtureRoot=option('fixture-source-root'),acceptedJar=option('accepted-jar');
const lab=fileURLToPath(new URL('../../../',import.meta.url)),repository=path.resolve(lab,'../../..'),template=JSON.parse(await fs.readFile(templateFile));
assert.equal(template.launch.env.KNEEKURA_DEBUG_MOD_PROFILE,'TANK_CORE');
const host=path.dirname(template.launch.command),git=(root,...args)=>execFileSync('git',args,{cwd:root,encoding:'utf8',windowsHide:true}).trim();
assert.equal(git(repository,'status','--porcelain'),'','Commit LAB source before native verification');
assert.equal(git(host,'status','--porcelain'),'','Clean host required');
assert.equal(git(template.workspaceDir,'status','--porcelain'),'','Clean product checkout required');
const acceptedHash='6c5d2156e9ad83d437d3106721221c13e5221531c1518a069274564364ab3bca';
assert.equal(sha256(await fs.readFile(acceptedJar)),acceptedHash,'Preserve the user-accepted product JAR');
await fs.mkdir(parent,{recursive:true});const trial=await fs.mkdtemp(path.join(parent,'observation-'));
const write=(file,value)=>fs.writeFile(file,JSON.stringify(value)+'\n',{flag:'wx'}),json=async file=>JSON.parse(await fs.readFile(file,'utf8'));
const sleep=ms=>new Promise(resolve=>setTimeout(resolve,ms)),hashJson=v=>sha256(Buffer.from(stableJson(v)));
const report={schema:'kneekura.tank-observation-native/v1',trial,profile:'TANK_CORE',labRevision:git(repository,'rev-parse','HEAD'),hostRevision:git(host,'rev-parse','HEAD'),productWorkspaceRevision:git(template.workspaceDir,'rev-parse','HEAD'),acceptedProductSource:'182fcb7ee88084c5dc1aecaba6cfa870cefa13b0',acceptedJarHash:acceptedHash,failures:[],
 limitations:['One fresh survival Player/active Ghast fixture; displacement is reported, not a moving-camera acceptance claim; death/unload/multiplayer NOT_RUN.',
 'Roster and paused sequential frames have independent ticks; visibility/AI perception NOT_ESTABLISHED.',
 'Mob observe v2 is not enabled by this pilot. Class-resource linkage is not transformed-definition attestation.']};
console.log('TRIAL '+trial);let current,originalRows;
async function inventory(root,relative=''){
 const rows=[];for(const e of await fs.readdir(path.join(root,relative),{withFileTypes:true})){assert(!e.isSymbolicLink());const file=path.join(relative,e.name);
  if(e.isDirectory())rows.push(...await inventory(root,file));else if(e.isFile())rows.push({file,sha256:sha256(await fs.readFile(path.join(root,file)))});
 }return rows.sort((a,b)=>a.file.localeCompare(b.file));
}
const exec=(tool,args)=>execFileSync(path.join(javaHome,'bin',tool+'.exe'),args,{cwd:trial,windowsHide:true,maxBuffer:16*1024*1024});
async function javaArgs(name,args){const file=path.join(trial,name);await fs.writeFile(file,args.map(s=>'"'+s.replaceAll('\\','/')+'"').join('\n'),{flag:'wx'});return '@'+file;}
try{
 originalRows=await inventory(original);await write(path.join(trial,'original-hashes.json'),originalRows);
 const world=path.join(trial,'game/saves/KNEEKURA_DEBUG_WORLD');await fs.mkdir(path.dirname(world),{recursive:true});await fs.cp(original,world,{recursive:true,errorOnExist:true,force:false});
 await fs.writeFile(path.join(trial,'game/options.txt'),'fullscreen:false\noverrideWidth:640\noverrideHeight:480\npauseOnLostFocus:false\n',{flag:'wx'});
 const classpath=(await fs.readFile(classpathFile,'utf8')).split(/\r?\n/)[1].replace(/^"|"$/g,'')+';'+path.join(host,'build/classes/java/kneekuraDebug')+';'+acceptedJar;
 const classes=path.join(trial,'classes');await fs.mkdir(classes);
 const fixtureSources=['TankSeedEntities.java','PrepareFlightTank.java'].map(n=>path.join(fixtureRoot,n));
 report.fixtureSources=await Promise.all(fixtureSources.map(async file=>({file,sha256:sha256(await fs.readFile(file))})));
 exec('javac',[await javaArgs('javac.args',['--release','17','-proc:none','-cp',classpath,'-d',classes,...fixtureSources])]);
 exec('java',[await javaArgs('java.args',['-cp',classes+';'+classpath,'com.github.tartaricacid.touhoulittlemaid.sim.debug.PrepareFlightTank',trial,parent])]);
 const fixture=await json(path.join(trial,'fixture.json')),saved=await json(path.join(world,'kneekura-tank-owner.json')),inputs=path.join(trial,'inputs'),privateDir=path.join(trial,'private');await fs.mkdir(inputs);await fs.mkdir(privateDir);
 const artifact=path.join(inputs,'naturalghast-accepted.jar');await fs.copyFile(acceptedJar,artifact,fs.constants.COPYFILE_EXCL);
 const profileFile=path.join(trial,'presentation.json');await write(profileFile,{kind:'OBSERVE_GRID',grid:true,brightness:true,motion:false,decisionChannels:['SERVER_ENTITY_STATE']});
 await prepareTankResourceFile({savedFile:path.join(trial,'tank-owner.json'),profileFile,output:path.join(inputs,'resources.zip')});
 const configMaterial=Buffer.from(stableJson({profile:'TANK_CORE',scope:'BOUNDED_ROOM_AND_CARDINAL_V2',acceptedJarHash:acceptedHash}));await fs.writeFile(path.join(inputs,'config.bin'),configMaterial,{flag:'wx'});
 const target={profile_id:hashJson({profile:'TANK_CORE'}),index_snapshot_id:hashJson({hostRevision:report.hostRevision,labRevision:report.labRevision}),build_artifact_hash:acceptedHash,
  source_revision:report.productWorkspaceRevision,dirty_hash:sha256(Buffer.alloc(0)),config_hash:sha256(configMaterial),resource_hash:sha256(await fs.readFile(path.join(inputs,'resources.zip')))};
 const experiment=path.basename(trial),request={schema_version:1,experiment_id:experiment,generation:1,target,
  arena:{arena_id:experiment,baseline_hash:fixture.baselineHash,bounds:{min:[7,224,6],max:[13,235,13]},preset:'private-observation-v2'},
  subjects:[{subject_id:'ghast',uuid:fixture.subjectUuid,entity_type:'soutou_ghast:soutou_ghast'}],initial_state:[],actions:[],
  observation_scopes:[{kind:'ENTITY_UUID',subject_id:'ghast',lanes:['SERVER_ENTITY_STATE'],level:'L1'}],visual_rig:{mode:'tank-cardinal-4-snapshot-v2',fov:70,viewport:[640,480]},
  assertions:[{assertion_id:'health',kind:'structured',subject_id:'ghast',field:'health',operator:'equals',expected:10}],budgets:{time_budget_ms:120000,max_actions:0,max_captures:4}};
 await write(path.join(inputs,'request.json'),request);await write(path.join(inputs,'assertions.json'),request.assertions);const requestHash=sha256(await fs.readFile(path.join(inputs,'request.json')));
 await write(path.join(inputs,'binding.json'),{schema_version:1,experiment_id:experiment,generation:1,request_hash:requestHash,target,arena_id:experiment,arena_baseline_hash:fixture.baselineHash,assertions_hash:sha256(await fs.readFile(path.join(inputs,'assertions.json')))});
 const classResources=[{className:'com.genki.soutoughast.SoutouGhastMod',sha256:sha256(await fs.readFile(path.join(template.workspaceDir,'build/classes/java/main/com/genki/soutoughast/SoutouGhastMod.class')))}];
 for(const name of ['TankObservation','TankRosterOwner','CaptureOwner','CaptureSession','CardinalCapture','EvidenceWriter','CameraOwnership']){
  const className='com.github.tartaricacid.touhoulittlemaid.sim.debug.KneekuraDebug'+name;
  classResources.push({className,sha256:sha256(await fs.readFile(path.join(host,'build/classes/java/kneekuraDebug',className.replaceAll('.','/')+'.class')))});
 }
 const operator={schemaVersion:1,requestHash,materialDescriptor:{schemaVersion:1,targetModId:'soutou_ghast',linkageMode:'OBSERVED_CLASS_RESOURCE_AND_CONTAINER_LINKAGE',buildArtifactHash:acceptedHash,configArtifactHash:target.config_hash,resourceArtifactHash:target.resource_hash,classResources},
  selection:{grantId:experiment,leaseId:experiment+'-120s',arenaEpoch:8,expectedArenaRevision:0,allowedActions:[]},
  worldRegistration:{schemaVersion:1,registrationId:experiment,canonicalWorldRoot:world,worldName:'KNEEKURA_DEBUG_WORLD',dimensionId:'minecraft:overworld',permissions:['BOUNDED_DIAGNOSTIC_CONTROL','CARDINAL_CAPTURE_PAUSE_CAMERA','TANK_OBSERVATION_READ']},
  tankObservation:{schemaVersion:1,scope:'TANK_OBSERVATION_READ',dimensionId:'minecraft:overworld',min:[0,224,0],max:[52,248,52],recipeHash:saved.recipeHash.replace(/^sha256:/,''),maxEntities:64,maxSamples:2}};
 await write(path.join(privateDir,'operator.json'),operator);
 const init=path.join(trial,'native.init.gradle');await fs.writeFile(init,`gradle.beforeProject { p -> p.plugins.withId('net.minecraftforge.gradle') {
 p.dependencies.add('runtimeOnly',p.files('${artifact.replaceAll('\\','/')}'))
 p.afterEvaluate {
  p.minecraft.runs.client.workingDirectory p.file('${path.join(trial,'game').replaceAll('\\','/')}')
  p.tasks.matching { it.name == 'runClient' }.configureEach { task ->
   task.environment System.getenv().findAll { k,v -> k.startsWith('KNEEKURA_DEBUG_') }
   task.doFirst {
    def context=[enabled:task.environment['KNEEKURA_DEBUG_ENABLED'],runId:task.environment['KNEEKURA_DEBUG_RUN_ID'],bridgeSource:task.environment['KNEEKURA_DEBUG_FORGE_BRIDGE_SRC'],modClasses:task.environment['MOD_CLASSES'],debugClasspath:task.classpath.files.findAll { it.path.contains('kneekuraDebug') }.collect { it.path }]
    java.nio.file.Files.writeString(java.nio.file.Path.of('${path.join(trial,'launcher-debug-context.json').replaceAll('\\','/')}'),groovy.json.JsonOutput.toJson(context),java.nio.file.StandardOpenOption.CREATE_NEW)
   }
  }
 }
} }\n`,{flag:'wx'});
 const config=structuredClone(template);config.workspaceId=experiment;config.runtimeRoot=path.join(trial,'runtime');config.gameDir=path.join(trial,'game');config.readyTimeoutMs=240000;config.motionOverlay=true;
 config.launch.args=[...template.launch.args.slice(0,-2),'--init-script',init];config.launch.env={JAVA_HOME:javaHome,KNEEKURA_DEBUG_MOD_PROFILE:'TANK_CORE'};
 config.ownerControl={requestHash,operatorRegistration:{trustedRoot:privateDir,relativePath:'operator.json',sha256:sha256(await fs.readFile(path.join(privateDir,'operator.json')))}};await write(path.join(trial,'config.json'),config);
 await registerBridgeRequest({runtimeRoot:config.runtimeRoot,registration:{schemaVersion:1,trustedRoot:inputs,requestFile:'request.json',bindingFile:'binding.json',assertionsFile:'assertions.json',materials:{buildArtifact:{relativePath:'naturalghast-accepted.jar'},configArtifact:{relativePath:'config.bin'},resourceArtifact:{relativePath:'resources.zip'}}}});
 await launchDebugRun(config,lab);current=await readCurrent(config,lab);assert(current.live&&current.runtimeOwnership?.owned);report.runDir=current.runDir;
 const runtime=evidenceRuntimeFromCurrent(current);await runtime.init();
 const options={runDir:current.runDir,envelopeHash:sha256(await fs.readFile(path.join(current.runDir,'control/owner-envelope.json')))};
 async function until(check,ms=15000){const deadline=Date.now()+ms;while(Date.now()<deadline){await runtime.ingestAvailable();const result=await check();if(result)return result;await sleep(150);}throw Error('PILOT_DEADLINE');}
 await until(async()=>{const s=await json(path.join(current.runDir,'control/owner-status.json'));if(['BLOCKED','OWNER_CLOSED','OUTCOME_UNKNOWN'].includes(s.status))throw Error(s.status+':'+s.error);return s.status==='ACTIVE_SCOPED_CONTROL'&&s;});
 await publishTankRoster({...options,sampleIndex:0});report.roster=await until(async()=>{const r=await inspectTankRoster({...options,sampleIndex:0});return r.status!=='UNKNOWN'&&r;});
 assert.equal(report.roster.status,'COMPLETE');assert.equal(report.roster.roster.entities.some(e=>e.entityType==='touhou_little_maid:reimu'),false);
 assert(report.roster.roster.entities.some(e=>e.uuid===fixture.subjectUuid));assert(report.roster.roster.entities.some(e=>e.player));
 report.cameraPlan=await cameraPlan(options);assert.equal(report.cameraPlan.artifactRole,'DERIVED_PLANNING');
 await requestDeclaredCapture({...options,captureIndex:0});report.capture=await until(async()=>{const r=await captureBundle({...options,captureIndex:0});return r.bundle&&r;},20000);
 assert.equal(report.capture.status,'COMPLETE');assert.equal(report.capture.bundle.restoration,'RESTORED');assert.equal(report.capture.bundle.views.length,4);
 await publishTankRoster({...options,sampleIndex:1});report.secondRoster=await until(async()=>{const r=await inspectTankRoster({...options,sampleIndex:1});return r.status!=='UNKNOWN'&&r;});assert.equal(report.secondRoster.status,'COMPLETE');
 const before=report.roster.roster.entities.find(e=>e.uuid===fixture.subjectUuid),after=report.secondRoster.roster.entities.find(e=>e.uuid===fixture.subjectUuid);
 report.movingSubject={before:before.world,after:after.world,distance:Math.hypot(...after.world.map((v,i)=>v-before.world[i]))};
 assert.equal((await requestDeclaredCapture({...options,captureIndex:0})).status,'ALREADY_RECORDED');
 report.status='CHECKS_PASSED_FINALIZATION_PENDING';
}catch(error){report.status='FAIL';report.failures.push(error.stack??error.message);process.exitCode=1;}
finally{
 if(current)try{
  const config=await json(path.join(trial,'config.json'));
  const finish=await finalizeNativeTrial({current,stop:()=>stopCurrent(config,lab),read:()=>readCurrent(config,lab),finalize:finalizeEvidenceRun});
  report.shutdown=finish.shutdown;report.exit=finish.stopped.cleanup;report.finalization=finish.finalization;
  if(finish.status==='FAIL'){report.failures.push(finish.reason);report.status='FAIL';process.exitCode=1;}
  else if(report.status==='CHECKS_PASSED_FINALIZATION_PENDING')report.status='PASS';
 }catch(error){report.failures.push('cleanup: '+error.message);report.status='FAIL';process.exitCode=1;}
 if(originalRows)try{assert.deepEqual(await inventory(original),originalRows);report.originalWorld={status:'UNCHANGED',files:originalRows.length};}catch(error){report.failures.push('original audit: '+error.message);report.status='FAIL';process.exitCode=1;}
 assert.equal(sha256(await fs.readFile(acceptedJar)),acceptedHash);assert.equal(git(repository,'rev-parse','HEAD'),report.labRevision);
 await write(path.join(trial,'report.json'),report);console.log(report.status+' '+path.join(trial,'report.json'));
}
