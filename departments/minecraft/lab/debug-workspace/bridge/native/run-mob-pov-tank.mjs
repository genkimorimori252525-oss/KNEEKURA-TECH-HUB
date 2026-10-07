/** Finite source-bound pilot. New private save/config only; no original-world writes or extra MOD. */
import assert from 'node:assert/strict';
import * as fs from 'node:fs/promises';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
import {execFileSync} from 'node:child_process';
import {sha256,stableJson} from '../json.mjs';
import {registerBridgeRequest} from '../registration.mjs';
import {launchDebugRun,readCurrent,stopCurrent} from '../../core.mjs';
import {setTargetControl} from '../../evidence/target-control.mjs';
import {evidenceRuntimeFromCurrent} from '../../evidence/runtime.mjs';
import {finalizeEvidenceRun} from '../../evidence/finalize.mjs';
import {publishMobPovCommand,inspectMobPovCommand,readMobPovImage} from '../mob-pov.mjs';

const option=name=>{const i=process.argv.indexOf('--'+name);if(i<0||!process.argv[i+1])throw Error('Missing --'+name);return path.resolve(process.argv[i+1]);};
const templateFile=option('template'),original=option('original'),classpathFile=option('classpath-file'),javaHome=option('java-home'),parent=option('private-parent');
const lab=fileURLToPath(new URL('../../../',import.meta.url)),repository=path.resolve(lab,'../../..'),template=JSON.parse(await fs.readFile(templateFile));
assert.equal(template.launch.env.KNEEKURA_DEBUG_MOD_PROFILE,'TANK_CORE');
const host=template.workspaceDir;
const git=(root,...args)=>execFileSync('git',args,{cwd:root,encoding:'utf8',windowsHide:true}).trim();
assert.equal(git(repository,'status','--porcelain'),'','Commit LAB source before native verification');
assert.equal(git(host,'status','--porcelain'),'','Clean registered host required');
await fs.mkdir(parent,{recursive:true});const trial=await fs.mkdtemp(path.join(parent,'mob-pov-'));
const write=(file,value)=>fs.writeFile(file,JSON.stringify(value)+'\n',{flag:'wx'}),json=async file=>JSON.parse(await fs.readFile(file,'utf8'));
const sleep=ms=>new Promise(resolve=>setTimeout(resolve,ms)),hashJson=v=>sha256(Buffer.from(stableJson(v)));
const report={schema:'kneekura.mob-pov-tank/v1',trial,profile:'TANK_CORE',labRevision:git(repository,'rev-parse','HEAD'),hostRevision:git(host,'rev-parse','HEAD'),failures:[],
 limitations:['Static frozen saved Reimu fixture: moving/dead/unloaded mob and external-camera native cases NOT_RUN.',
  'RAW_SCENE_RGB before post effects/hand/HUD; independent server sample does not prove same-tick pairing or AI perception.',
  'Observed class-resource/container linkage is not resident transformed-class attestation.']};
console.log('TRIAL '+trial);
let current,runtime,originalRows;
async function inventory(root,relative=''){
 const rows=[];for(const e of await fs.readdir(path.join(root,relative),{withFileTypes:true})){assert(!e.isSymbolicLink());const file=path.join(relative,e.name);
  if(e.isDirectory())rows.push(...await inventory(root,file));else if(e.isFile())rows.push({file,sha256:sha256(await fs.readFile(path.join(root,file)))});
 }return rows.sort((a,b)=>a.file.localeCompare(b.file));
}
const exec=(tool,args)=>execFileSync(path.join(javaHome,'bin',tool+'.exe'),args,{cwd:trial,windowsHide:true,maxBuffer:8*1024*1024});
async function javaArgs(name,args){const file=path.join(trial,name);await fs.writeFile(file,args.map(s=>'"'+s.replaceAll('\\','/')+'"').join('\n'),{flag:'wx'});return '@'+file;}
async function pngCount(){return (await fs.readdir(path.join(current.runDir,'evidence/raw/visual')).catch(e=>{if(e.code==='ENOENT')return [];throw e;})).filter(n=>n.endsWith('.png')).length;}
try{
 originalRows=await inventory(original);await write(path.join(trial,'original-hashes.json'),originalRows);
 const world=path.join(trial,'game/saves/KNEEKURA_DEBUG_WORLD');await fs.mkdir(path.dirname(world),{recursive:true});await fs.cp(original,world,{recursive:true,errorOnExist:true,force:false});
 // New presentation configuration, no copied accounts/credentials and no existing config overwritten.
 await fs.writeFile(path.join(trial,'game/options.txt'),'fullscreen:false\noverrideWidth:640\noverrideHeight:480\npauseOnLostFocus:false\n',{flag:'wx'});
 const classpath=(await json(classpathFile)).compile.map(r=>r.path).join(';')+';'+path.join(host,'build/classes/java/main')+';'+path.join(host,'build/classes/java/kneekuraDebug');
 const classes=path.join(trial,'classes');await fs.mkdir(classes);
 exec('javac',[await javaArgs('javac.args',['--release','17','-proc:none','-cp',classpath,'-d',classes,path.join(fileURLToPath(new URL('.',import.meta.url)),'PrepareMobPovTank.java')])]);
 exec('java',[await javaArgs('java.args',['-cp',classes+';'+classpath,'com.github.tartaricacid.touhoulittlemaid.sim.debug.PrepareMobPovTank',trial,parent])]);
 const fixture=await json(path.join(trial,'fixture.json')),inputs=path.join(trial,'inputs'),privateDir=path.join(trial,'private');await fs.mkdir(inputs);await fs.mkdir(privateDir);
 const artifact=path.join(inputs,'host-dev.jar');exec('jar',['--create','--file',artifact,'-C',path.join(host,'build/classes/java/main'),'.','-C',path.join(host,'build/resources/main'),'.']);
 await fs.copyFile(path.join(path.dirname(templateFile),'inputs/resources.zip'),path.join(inputs,'resources.zip'));
 const configMaterial=Buffer.from(stableJson({profile:'TANK_CORE',scope:'MOB_POV_OPT_IN_SINGLE_IMAGE'}));await fs.writeFile(path.join(inputs,'config.bin'),configMaterial,{flag:'wx'});
 const target={profile_id:hashJson({profile:'TANK_CORE'}),index_snapshot_id:hashJson({hostRevision:report.hostRevision,labRevision:report.labRevision}),build_artifact_hash:sha256(await fs.readFile(artifact)),
  source_revision:report.hostRevision,dirty_hash:sha256(Buffer.alloc(0)),config_hash:sha256(configMaterial),resource_hash:sha256(await fs.readFile(path.join(inputs,'resources.zip')))};
 const experiment=path.basename(trial),request={schema_version:1,experiment_id:experiment,generation:1,target,
  arena:{arena_id:experiment,baseline_hash:fixture.baselineHash,bounds:{min:[7,224,7],max:[12,227,12]},preset:'original-tank-static-mob-pov'},
  subjects:[{subject_id:'reimu',uuid:fixture.subjectUuid,entity_type:'touhou_little_maid:reimu'}],initial_state:[],actions:[],
  observation_scopes:[{kind:'ENTITY_UUID',subject_id:'reimu',lanes:['SERVER_ENTITY_STATE'],level:'L1'}],visual_rig:{mode:'mob-eye-live-v1',fov:60,viewport:[640,480]},
  assertions:[{assertion_id:'health',kind:'structured',subject_id:'reimu',field:'health',operator:'equals',expected:20}],budgets:{time_budget_ms:120000,max_actions:0,max_captures:1}};
 await write(path.join(inputs,'request.json'),request);await write(path.join(inputs,'assertions.json'),request.assertions);const requestHash=sha256(await fs.readFile(path.join(inputs,'request.json')));
 await write(path.join(inputs,'binding.json'),{schema_version:1,experiment_id:experiment,generation:1,request_hash:requestHash,target,arena_id:experiment,arena_baseline_hash:fixture.baselineHash,assertions_hash:sha256(await fs.readFile(path.join(inputs,'assertions.json')))});
 const names=['com.github.tartaricacid.touhoulittlemaid.TouhouLittleMaid',...['MobPovCamera','MobPovOwner','MobPovCommands','CameraOwnership','MobPovSession','MotionOverlay','EvidenceWriter'].map(n=>'com.github.tartaricacid.touhoulittlemaid.sim.debug.KneekuraDebug'+n)];
 const classResources=[];for(const className of names){const output=className.endsWith('.TouhouLittleMaid')?'main':'kneekuraDebug';classResources.push({className,sha256:sha256(await fs.readFile(path.join(host,'build/classes/java',output,className.replaceAll('.','/')+'.class')))});}
 const operator={schemaVersion:1,requestHash,materialDescriptor:{schemaVersion:1,targetModId:'touhou_little_maid',linkageMode:'OBSERVED_CLASS_RESOURCE_AND_CONTAINER_LINKAGE',buildArtifactHash:target.build_artifact_hash,configArtifactHash:target.config_hash,resourceArtifactHash:target.resource_hash,classResources},
  selection:{grantId:experiment,leaseId:experiment+'-120s',arenaEpoch:8,expectedArenaRevision:0,allowedActions:[]},
  worldRegistration:{schemaVersion:1,registrationId:experiment,canonicalWorldRoot:world,worldName:'KNEEKURA_DEBUG_WORLD',dimensionId:'minecraft:overworld',permissions:['BOUNDED_DIAGNOSTIC_CONTROL','MOB_POV_CAMERA']}};
 await write(path.join(privateDir,'operator.json'),operator);
 const init=path.join(trial,'native.init.gradle');await fs.writeFile(init,`gradle.beforeProject { p -> p.plugins.withId('net.minecraftforge.gradle') { p.afterEvaluate { p.minecraft.runs.client.workingDirectory p.file('${path.join(trial,'game').replaceAll('\\','/')}') } } }\n`,{flag:'wx'});
 const config=structuredClone(template);config.workspaceId=experiment;config.runtimeRoot=path.join(trial,'runtime');config.gameDir=path.join(trial,'game');config.readyTimeoutMs=240000;config.motionOverlay=true;report.motionOverlayEnabled=true;
 config.launch.args=[...template.launch.args.slice(0,-2),'--init-script',init];config.launch.env={JAVA_HOME:javaHome,KNEEKURA_DEBUG_MOD_PROFILE:'TANK_CORE'};
 config.ownerControl={requestHash,operatorRegistration:{trustedRoot:privateDir,relativePath:'operator.json',sha256:sha256(await fs.readFile(path.join(privateDir,'operator.json')))}};await write(path.join(trial,'config.json'),config);
 await registerBridgeRequest({runtimeRoot:config.runtimeRoot,registration:{schemaVersion:1,trustedRoot:inputs,requestFile:'request.json',bindingFile:'binding.json',assertionsFile:'assertions.json',materials:{buildArtifact:{relativePath:'host-dev.jar'},configArtifact:{relativePath:'config.bin'},resourceArtifact:{relativePath:'resources.zip'}}}});
 await launchDebugRun(config,lab);current=await readCurrent(config,lab);assert(current.live&&current.runtimeOwnership?.owned);report.runDir=current.runDir;
 runtime=evidenceRuntimeFromCurrent(current);await runtime.init();await setTargetControl(current,fixture.subjectUuid,{decisionSnapshot:false});
 const options={runDir:current.runDir,envelopeHash:sha256(await fs.readFile(path.join(current.runDir,'control/owner-envelope.json')))};
 async function until(check,ms=15000){const deadline=Date.now()+ms;while(Date.now()<deadline){await runtime.ingestAvailable();const result=await check();if(result)return result;await sleep(150);}throw Error('PILOT_DEADLINE');}
 await until(async()=>{const s=await json(path.join(current.runDir,'control/owner-status.json'));if(['BLOCKED','OWNER_CLOSED','OUTCOME_UNKNOWN'].includes(s.status))throw Error(s.status+':'+s.error);return s.status==='ACTIVE_SCOPED_CONTROL'&&s;});
 async function command(commandIndex,operation,extra={}){await publishMobPovCommand({...options,commandIndex,operation,...extra});const receipt=await until(async()=>inspectMobPovCommand({...options,commandIndex}).catch(e=>{if(e.code==='ENOENT')return null;throw e;}));
  assert.equal(receipt.status,{attach:'ATTACHED',snapshot:'CAPTURED',return:'RETURNED'}[operation]);return receipt;}
 report.attach=await command(0,'attach',{subjectUuid:fixture.subjectUuid,durationMs:20000});
 const before=await until(async()=>(await runtime.store.readObservations()).filter(r=>r.lane==='SERVER_TICK'&&Number.isInteger(r.payload?.localServerTick)).at(-1));
 const after=await until(async()=>{const row=(await runtime.store.readObservations()).filter(r=>r.lane==='SERVER_TICK').at(-1);return row?.payload?.localServerTick>before.payload.localServerTick+10&&row;});
 assert.equal(await pngCount(),0);assert(after.gameTime>before.gameTime,'Server game time must continue');
 assert.equal((await json(path.join(current.runDir,'control/owner-status.json'))).mobPov.active,true);
 report.viewOnly={imageCount:0,serverTickBefore:before.payload.localServerTick,serverTickAfter:after.payload.localServerTick,gameTimeBefore:before.gameTime,gameTimeAfter:after.gameTime};
 report.snapshot=await command(1,'snapshot');await readMobPovImage({...options,commandIndex:1});assert.equal(await pngCount(),1);
 report.return=await command(2,'return');assert.equal(report.return.restoration,'RESTORED');
 await command(3,'attach',{subjectUuid:fixture.subjectUuid,durationMs:1500});
 await until(async()=>{const s=await json(path.join(current.runDir,'control/owner-status.json'));return s.mobPov?.active===false&&s.mobPov?.restoration==='RESTORED';});
 assert.equal(await pngCount(),1);await runtime.ingestAvailable();const rows=await runtime.store.readObservations();
 assert(rows.some(r=>r.payload?.kind==='mob_pov_return'&&r.payload.reason==='EXPIRED'&&r.payload.restoration==='RESTORED'));
 report.expiry={restoration:'RESTORED',imageCount:1};report.frame=(await json(path.join(current.runDir,'control/mob-pov/01/receipt.json'))).result;
 report.status='PASS';
}catch(error){report.status='FAIL';report.failures.push(error.message);process.exitCode=1;}
finally{
 if(current){try{const config=await json(path.join(trial,'config.json'));await stopCurrent(config,lab);const stopped=await readCurrent(config,lab);report.shutdown=stopped.evidenceShutdown?.ack;
  report.finalization=await finalizeEvidenceRun(stopped,{cleanShutdown:stopped.evidenceShutdown?.status==='ACKNOWLEDGED'});
 }catch(e){report.failures.push('cleanup: '+e.message);report.status='FAIL';process.exitCode=1;}}
 if(originalRows){try{assert.deepEqual(await inventory(original),originalRows);report.originalWorld={status:'UNCHANGED',files:originalRows.length};}catch(e){report.failures.push('original verification: '+e.message);report.status='FAIL';process.exitCode=1;}}
 assert.equal(git(repository,'rev-parse','HEAD'),report.labRevision);assert.equal(git(host,'rev-parse','HEAD'),report.hostRevision);
 await write(path.join(trial,'report.json'),report);console.log(report.status+' '+path.join(trial,'report.json'));
}
