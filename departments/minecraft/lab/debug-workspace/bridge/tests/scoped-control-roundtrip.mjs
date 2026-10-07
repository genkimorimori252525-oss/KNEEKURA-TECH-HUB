/** Real Python↔Node source protocol check. Fixtures only; no JVM, game, or browser. */
import assert from 'node:assert/strict';
import {spawnSync} from 'node:child_process';
import {mkdtemp,mkdir,readFile,readdir,writeFile,rm,realpath} from 'node:fs/promises';
import os from 'node:os';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
import {preparedOwner} from './owner-action-fixture.mjs';
import {ownerTriggerIdentity} from '../owner-trigger-config.mjs';
import {captureSlotKey} from '../owner-action-adapter.mjs';
import {EvidenceStore} from '../../evidence/store.mjs';
import {finalizeEvidenceRun} from '../../evidence/finalize.mjs';
import {sha256,stableJson} from '../json.mjs';

const tech=process.env.KNEEKURA_TECH_HUB_SOURCE;
if(!tech||!path.isAbsolute(tech))throw new Error('KNEEKURA_TECH_HUB_SOURCE must identify the TECH source checkout');
const lab=await realpath(fileURLToPath(new URL('../../..',import.meta.url)));
const python=process.env.KNEEKURA_PYTHON??'python';
const temporary=await mkdtemp(path.join(os.tmpdir(),'lab-scoped-roundtrip-')),cleanup=[];

// Independently traverse actual static and literal dynamic imports. The paired
// Python test requires this closure to equal its fixed 36-file allowlist.
async function moduleClosure(relative='debug-workspace/bridge/owner-control-cli.mjs',files={}){
 if(Object.hasOwn(files,relative))return files;
 assert(!relative.startsWith('../')&&!path.isAbsolute(relative));
 const bytes=await readFile(path.join(lab,relative));assert(bytes.length<=1024*1024);files[relative]=sha256(bytes);
 const imports=bytes.toString('utf8').matchAll(/(?:\bfrom\s*|\bimport\s*(?:\(\s*)?)["']([^"']+)["']/g);
 for(const [,specifier] of imports){
  if(specifier.startsWith('node:'))continue;
  assert(specifier.startsWith('.'),'Unexpected non-builtin dependency');
  await moduleClosure(path.posix.normalize(path.posix.join(path.posix.dirname(relative),specifier)),files);
 }
 return files;
}

const script=String.raw`
import datetime,json,os,subprocess,sys,time,threading
from pathlib import Path
from kneekura_tech_hub.minecraft import storage,index,experiment_bridge,experiment_control,task_context
root=Path(sys.argv[1]); mode=sys.argv[2]; lab=Path(sys.argv[3]); node=Path(sys.argv[4]).resolve()
store=storage.Store(root/'cas')
def command(*args,selected_store=store,refresh_fixture=False,expect_unknown=False):
    if refresh_fixture: fixture_status()
    completed=subprocess.run([sys.executable,'-m','kneekura_tech_hub.minecraft','--store',str(selected_store.root),*args],
        capture_output=True,timeout=15,check=False,env=os.environ)
    if completed.returncode!=0 and (root/'owner-context.json').exists():
        pinned=json.loads((root/'owner-context.json').read_text())['moduleHashes']
        changed=[name for name,h in pinned.items() if storage.digest((lab/name).read_bytes())!=h]
        assert not changed,('paired source changed during the fixture',changed)
    assert completed.returncode==0,(args,completed.returncode,completed.stdout.decode(),completed.stderr.decode())
    value=json.loads(completed.stdout)
    assert completed.stderr==b''
    assert str(root).encode() not in completed.stdout and b'private-source-fixture' not in completed.stdout
    if (root/'owner-context.json').exists():
        fixture=json.loads((root/'owner-context.json').read_text())
        selected=json.loads(Path(fixture['ownerFile']).read_text())
        for private in (fixture['ownerFile'],selected['runtimeRoot'],selected['inputRoot'],selected['run']['runDir'],str(Path(selected['runtimeRoot']).parent),'n'*32):
            assert private.encode() not in completed.stdout
    if mode=='controls' and not expect_unknown and value.get('status')=='OUTCOME_UNKNOWN':
        fixture=json.loads((root/'owner-context.json').read_text())
        selected=json.loads(Path(fixture['ownerFile']).read_text())
        changed=[name for name,h in fixture['moduleHashes'].items() if storage.digest((lab/name).read_bytes())!=h]
        assert not changed,('paired source changed during the fixture',changed)
        observed=json.loads((Path(selected['run']['runDir'])/'control/owner-status.json').read_text())['observedAt']
        age=int((time.time()-datetime.datetime.fromisoformat(observed.replace('Z','+00:00')).timestamp())*1000)
        raise AssertionError(('source fixture control unavailable',args[:2],'status_age_ms',age))
    return value
task={'schema_version':1,'intent':'investigate','goal':'Inspect source-only protocol evidence','constraints':[],'acceptance':[]}
if mode=='prepare':
    source=root/'source';(source/'src').mkdir(parents=True);(source/'src/Example.java').write_text('class Example {}\n')
    m={'schema_version':1,'minecraft':'1.20.1','loader':'forge','loader_version':'47.4.0','java_major':17,'namespace':'mojmap',
       'physical_side':'server','logical_side':'server','track':'ANCHOR','workspace_revision':'a'*40,'dirty_hash':'b'*64,
       'toolchain':{'gradle':'8.8','forgegradle':'6.0.24'},'roots':[{'id':'own','path':'src','kind':'directory','scope':'runtime',
       'role':'source','namespace':'mojmap','stage':'workspace','classloader':'unknown','track':'ANCHOR'}]}
    profile=storage.capture_profile(m,source,store);idx=index.prepare_index(profile,store)['index_snapshot_id']
    req={'schema_version':1,'experiment_id':'experiment','generation':1,'target':{'profile_id':profile['profile_id'],
      'index_snapshot_id':idx,'source_revision':m['workspace_revision'],'dirty_hash':m['dirty_hash'],
      'build_artifact_hash':store.put(b'build'),'config_hash':store.put(b'config'),'resource_hash':store.put(b'resources')},
      'arena':{'arena_id':'arena','preset':'normal','baseline_hash':'e'*64,'bounds':{'min':[0,0,0],'max':[8,8,8]}},
      'subjects':[{'subject_id':'pig','uuid':'00000000-0000-0000-0000-000000000001','entity_type':'minecraft:pig'}],
      'initial_state':[],'actions':[{'action_id':'wait','operation':'wait_ticks','ticks':1}],
      'observation_scopes':[{'kind':'ENTITY_UUID','subject_id':'pig','lanes':['SERVER_ENTITY_STATE'],'level':'L1'}],
      'visual_rig':{'mode':'cardinal-4-snapshot-v1','fov':60,'viewport':[64,64]},
      'assertions':[{'assertion_id':'health','subject_id':'pig','kind':'structured','field':'health','operator':'equals','expected':20}],
      'budgets':{'time_budget_ms':120000,'max_actions':1,'max_captures':8}}
    h=experiment_bridge.prepare_experiment(store,req)['request_hash']
    (root/'request.json').write_bytes(storage.canonical(req));(root/'assertions.json').write_bytes(storage.canonical(req['assertions']))
    (root/'task.json').write_bytes(storage.canonical(task))
    print(json.dumps({'requestHash':h}))
else:
    metadata=json.loads((root/'owner-context.json').read_text());req=json.loads((root/'request.json').read_text())
    h=storage.key_for(req);owner_file=Path(metadata['ownerFile'])
    assert set(metadata['moduleHashes'])==set(experiment_control.MODULES) and len(experiment_control.MODULES)==36
    registry={'schema_version':1,'enabled':True,'backend':'kneekura.lab.scoped-control.v1','workspace':str(lab),
      'source_revision':metadata['sourceRevision'],'executable':str(node),'executable_hash':storage.digest(node.read_bytes()),
      'module_hashes':metadata['moduleHashes'],'owner_file':str(owner_file),'owner_hash':storage.digest(owner_file.read_bytes()),'timeout_seconds':10}
    registry_file=root/'registry.json';registry_file.write_bytes(storage.canonical(registry))
    options=['--registry',str(registry_file),'--request-hash',h]
    def fixture_status(age_ms=0):
        # This is a source-only simulated producer heartbeat, never JVM evidence.
        # Keep the production five-second freshness check unchanged.
        selected=json.loads(owner_file.read_text());file=Path(selected['run']['runDir'])/'control/owner-status.json'
        status=json.loads(file.read_text())
        status['observedAt']=(datetime.datetime.now(datetime.timezone.utc)-datetime.timedelta(milliseconds=age_ms)).isoformat().replace('+00:00','Z')
        file.write_bytes(storage.canonical(status))
    if mode=='controls':
        inspected=command('experiment','inspect-control','--registry',str(registry_file));assert inspected['status']=='REGISTERED'
        fixture_status(6000)
        stale=command('experiment','inspect-owner',*options,expect_unknown=True);assert stale['status']=='OUTCOME_UNKNOWN'
        owner=command('experiment','inspect-owner',*options,refresh_fixture=True);assert owner['status']=='OWNER_RECORDED',owner
        unseen=command('experiment','inspect-action',*options,'--action-id','wait');assert unseen['status']=='NEVER_SEEN',unseen
        submitted=command('experiment','submit-action',*options,'--action-id','wait',refresh_fixture=True);assert submitted['status']=='REQUESTED',submitted
        pending=command('experiment','inspect-action',*options,'--action-id','wait');assert pending['status']=='REQUESTED',pending
        assert pending['reported']['recordedStatus']=='REQUESTED' and pending['reported']['dispatchAllowed'] is False
        captured=command('experiment','request-capture',*options,'--capture-index','0',refresh_fixture=True)
        assert captured['status']=='REQUESTED',captured
        # A fresh TECH Store cannot replay a LAB journaled action.
        second=storage.Store(root/'second-cas')
        for field in ('index_snapshot_id','build_artifact_hash','config_hash','resource_hash'):
            assert second.put(store.read(req['target'][field]))==req['target'][field]
        experiment_bridge.prepare_experiment(second,req)
        repeated=command('experiment','submit-action',*options,'--action-id','wait',selected_store=second,refresh_fixture=True)
        assert repeated['status']=='ALREADY_RECORDED',repeated
        repeated_capture=command('experiment','request-capture',*options,'--capture-index','0',refresh_fixture=True)
        assert repeated_capture['status']=='ALREADY_RECORDED',repeated_capture
        # Publish a fixture producer row only after the explicit watcher is armed.
        selected=json.loads(owner_file.read_text());run_dir=Path(selected['run']['runDir'])
        writer_errors=[]
        def producer():
            try:
                deadline=time.monotonic()+10
                while not (run_dir/'control/owner-trigger-watch.json').exists():
                    assert time.monotonic()<deadline,'explicit source watch did not arm'
                    time.sleep(.02)
                time.sleep(.03)
                row=json.loads((root/'trigger-row.json').read_text())
                row['observedAt']=datetime.datetime.now(datetime.timezone.utc).isoformat().replace('+00:00','Z')
                raw=run_dir/'evidence/raw';raw.mkdir(parents=True,exist_ok=True)
                temporary_row=raw/'fixture-trigger.tmp'
                temporary_row.write_bytes(storage.canonical(row)+b'\n')
                temporary_row.replace(raw/'fixture-trigger.jsonl')
            except BaseException as error:writer_errors.append(error)
        writer=threading.Thread(target=producer);writer.start()
        watched=command('experiment','watch-triggers',*options,refresh_fixture=True)
        writer.join(timeout=10);assert not writer.is_alive() and not writer_errors,writer_errors
        assert watched['status']=='WINDOWS_FINISHED',watched
        window_id,=watched['reported']['captureWindowIds']
        window=json.loads((run_dir/'evidence/captures'/('trigger-'+window_id+'.json')).read_text())
        assert window['outcome']=='PARTIAL' and window['semantics']['visualVerdict']=='NOT_RUN'
        assert [slot['status'] for slot in window['slots']]==['MISSING','OUTCOME_UNKNOWN','MISSING'],window
        marker_file=run_dir/'control/captures'/metadata['triggerCaptureKey']/'request.json'
        marker=marker_file.read_bytes();intent=json.loads(marker)
        assert intent['captureIndex']==1 and intent['trigger']['observationId']=='fixture:trigger:1'
        assert intent['trigger']['windowId']==window_id and intent['trigger']['offsetMs']==0
        assert intent['trigger']['deadline']==intent['trigger']['triggerAt']+1500
        repeated_watch=command('experiment','watch-triggers',*options,selected_store=second,refresh_fixture=True,expect_unknown=True)
        assert repeated_watch['status']=='OUTCOME_UNKNOWN' and marker_file.read_bytes()==marker
        assert len(list((run_dir/'evidence/captures').glob('trigger-*.json')))==1
        watch_context=command('task','prepare','--request',str(root/'task.json'),'--index',req['target']['index_snapshot_id'],
            '--experiment-control-registry',str(registry_file),'--experiment-control-receipt',watched['receipt_hash'])
        assert watch_context['next_actions'][0]['operation_id']=='experiment.inspect_owner'
        assert all(x['mode']=='READ_ONLY' for x in watch_context['next_actions'])
        cleanup_unseen=command('experiment','inspect-cleanup',*options)
        assert cleanup_unseen['status']=='NEVER_SEEN' and cleanup_unseen['reported']['recordedStatus'] is None
        cleanup_requested=command('experiment','request-cleanup',*options,refresh_fixture=True)
        assert cleanup_requested['status']=='REQUESTED',cleanup_requested
        cleanup_inspected=command('experiment','inspect-cleanup',*options,expect_unknown=True)
        assert cleanup_inspected['status']=='OUTCOME_UNKNOWN' and cleanup_inspected['reported']['recordedStatus'] is None
        assert cleanup_inspected['reported']['evidenceHashes']==[] and cleanup_inspected['reported']['dispatchAllowed'] is False
        repeated_cleanup=command('experiment','request-cleanup',*options,selected_store=second,refresh_fixture=True)
        assert repeated_cleanup['status']=='ALREADY_RECORDED',repeated_cleanup
        cleanup_context=command('task','prepare','--request',str(root/'task.json'),'--index',req['target']['index_snapshot_id'],
            '--experiment-control-registry',str(registry_file),'--experiment-control-receipt',cleanup_inspected['receipt_hash'])
        assert cleanup_context['next_actions'][0]['operation_id']=='experiment.inspect_cleanup'
        assert all(x['mode']=='READ_ONLY' and x['operation_id']!='experiment.request_cleanup' for x in cleanup_context['next_actions'])
        context=command('task','prepare','--request',str(root/'task.json'),'--index',req['target']['index_snapshot_id'],
            '--experiment-control-registry',str(registry_file),'--experiment-control-receipt',submitted['receipt_hash'])
        assert context['next_actions'][0]['operation_id']=='experiment.inspect_action'
        assert all(x['mode']=='READ_ONLY' for x in context['next_actions'])
        for value in (owner,submitted,pending,captured,repeated,repeated_capture,watched,repeated_watch,cleanup_requested,cleanup_inspected,repeated_cleanup):
            assert value['runtime_attestation']=='NOT_ESTABLISHED' and value['can_replay'] is False
        (root/'submitted.json').write_bytes(storage.canonical(submitted))
        print(json.dumps({'staleOwner':stale['status'],'owner':owner['status'],'action':submitted['status'],'inspection':pending['status'],
          'capture':captured['status'],'freshStoreReplay':repeated['status'],'repeatedCapture':repeated_capture['status'],
          'triggerWatch':watched['status'],'triggerWindow':window['outcome'],'repeatedWatch':repeated_watch['status'],
          'cleanup':cleanup_requested['status'],'cleanupInspection':cleanup_inspected['status'],'repeatedCleanup':repeated_cleanup['status'],'moduleCount':36}))
    else:
        exported=command('experiment','export-result',*options,'--observation-id','fixture:state:1','--observation-id','fixture:trigger:1','--timeline-observation-id','fixture:state:1','--timeline-observation-id','fixture:trigger:1')
        assert exported['status']=='EXPORTED',exported
        manifest_hash=exported['reported']['manifestHash'];owner=json.loads(owner_file.read_text())
        transport=Path(owner['inputRoot'])/'exports'/h
        manifest=json.loads((transport/'manifests'/(manifest_hash+'.json')).read_text())
        assert manifest['contains_private_evidence'] is True and manifest['provenance']=='FINALIZED_LAB_EVIDENCE_REPORT'
        assert all(set(x)=={'content_hash','size_bytes','classification'} for x in manifest['blobs'])
        assert str(Path(owner['run']['runDir'])) not in json.dumps(exported)
        imported=command('experiment','import-export',*options,'--manifest-hash',manifest_hash)
        assert imported['runtime_attestation']=='NOT_ESTABLISHED' and imported['provenance']=='IMPORTED_LAB_REPORT'
        assert imported['export_provenance']=='FINALIZED_LAB_EVIDENCE_REPORT' and imported['reported_cleanup']=='UNKNOWN'
        assert imported['reported_execution'] in ('UNKNOWN','PARTIAL')
        assert all(x['status'] in ('INCONCLUSIVE','NOT_RUN','UNKNOWN') for x in imported['reported_assertions'])
        resumed=command('experiment','resume','--result-hash',imported['result_hash'])
        assert resumed['can_replay'] is False and resumed['execution_authority']=='NONE'
        assert resumed['next_operation']=='experiment.reconcile_unknown'
        assert all(x['status']!='PASS' for x in resumed['assertions'])
        retained=store.json(imported['result_hash'])['result']
        assert retained['observations']['structured_summary'] and retained['observations']['timeline_summary']
        assert retained['observations']['visual_bundle'] is None
        selection=store.json(retained['observations']['structured_summary'])
        trigger_ref=next(x for x in selection['observations'] if x['observationId']=='fixture:trigger:1')
        assert store.json(trigger_ref['contentHash'])['payload']['kind']=='owner_trigger_event'
        assert {manifest_hash,*(x['content_hash'] for x in manifest['blobs'])}<=store.pinned_hashes()
        context=command('task','prepare','--request',str(root/'task.json'),'--experiment-result',imported['result_hash'])
        assert context['next_actions'][0]['operation_id']=='experiment.reconcile_unknown'
        assert all(x['mode']=='READ_ONLY' for x in context['next_actions'])
        print(json.dumps({'export':'EXPORTED','import':'IMPORTED_LAB_REPORT','execution':imported['reported_execution'],
          'cleanup':'UNKNOWN','assertions':[x['status'] for x in resumed['assertions']],
          'evidenceCount':len(retained['evidence']),'runtimeAttestation':'NOT_ESTABLISHED','canReplay':False}))
`;
function run(mode){
 const child=spawnSync(python,['-c',script,temporary,mode,lab,process.execPath],{encoding:'utf8',timeout:60000,maxBuffer:2*1024*1024,
  env:{...process.env,PYTHONDONTWRITEBYTECODE:'1',PYTHONPATH:path.join(tech,'src')}});
 if(child.error||child.status!==0)throw new Error('Scoped source roundtrip failed: '+mode+'\n'+child.stderr,{cause:child.error});
 return JSON.parse(child.stdout.trim());
}
async function tree(root){
 const entries=[];
 async function visit(dir){for(const e of await readdir(dir,{withFileTypes:true})){const f=path.join(dir,e.name);if(e.isDirectory())await visit(f);else {assert(e.isFile());entries.push([path.relative(root,f),sha256(await readFile(f))]);}}}
 await visit(root);return entries.sort(([a],[b])=>a.localeCompare(b));
}
try{
 const prepared=run('prepare'),requestBytes=await readFile(path.join(temporary,'request.json')),assertionsBytes=await readFile(path.join(temporary,'assertions.json'));
 const f=await preparedOwner({after:fn=>cleanup.push(fn)},{capture:true,triggerCapture:{enabled:true,triggerKinds:['ARENA_EXIT'],offsetsMs:[-500,0,500],toleranceMs:100,cooldownMs:1000,maxWindows:1,captureBudget:1,timeoutMs:1500,captureIndices:[1]},requestBytesOverride:requestBytes,assertionsBytesOverride:assertionsBytes});
 assert.equal(f.prepared.envelope.requestHash,prepared.requestHash,'owner fixture must preserve exact TECH canonical request bytes');
 const identity={...Object.fromEntries(['debugSessionId','runId','runSnapshotId','processEpoch'].map(k=>[k,f.identity[k]])),
  experimentId:f.prepared.request.experiment_id,requestHash:prepared.requestHash};
 const ownerFile=path.join(temporary,'owner.json');
 await writeFile(ownerFile,stableJson({schemaVersion:1,runtimeRoot:f.runtimeRoot,inputRoot:f.inputs,
  run:{runDir:f.runDir,identity,ownerEnvelopeHash:f.prepared.envelopeHash}}),{mode:0o600});
 const source=spawnSync('git',['rev-parse','HEAD'],{cwd:lab,encoding:'utf8'});assert.equal(source.status,0);
 const moduleHashes=await moduleClosure();assert.equal(Object.keys(moduleHashes).length,36);
 await writeFile(path.join(temporary,'owner-context.json'),stableJson({ownerFile,sourceRevision:source.stdout.trim(),moduleHashes,triggerCaptureKey:captureSlotKey(f.prepared.grant,1)}));
 await writeFile(path.join(temporary,'trigger-row.json'),stableJson({v:1,kind:'observation',observationId:'fixture:trigger:1',
  ...Object.fromEntries(['debugSessionId','runId','runSnapshotId','processEpoch'].map(k=>[k,f.identity[k]])),arenaEpoch:0,resourceEpoch:0,
  writerId:'source_trigger_fixture',writerSeq:1,observedAt:null,level:'L1',lane:'SERVER_ENTITY_STATE',
  scope:{kind:'ENTITY_UUID',entityUuid:f.prepared.grant.subjects[0].uuid},source:{side:'SERVER',method:'KneekuraDebugOwnerConnection.arena_exit'},
  epistemicStatus:'OBSERVED',completeness:{complete:true},payload:{kind:'owner_trigger_event',triggerKind:'ARENA_EXIT',
   identity:ownerTriggerIdentity(f.prepared),ownerEnvelopeHash:f.prepared.envelopeHash,triggerConfigHash:f.prepared.envelope.triggerConfigHash,
   subjectId:'pig',uuid:f.prepared.grant.subjects[0].uuid,transition:'INSIDE_TO_OUTSIDE',previousPosition:[1,1,1],position:[9,1,1],
   basis:'SOURCE_FIXTURE_NOT_RUNTIME'}}));
 const controls=run('controls');
 const store=new EvidenceStore({runDir:f.runDir,...identity});await store.init();
 await store.appendObservation({observationId:'fixture:state:1',processEpoch:identity.processEpoch,arenaEpoch:0,resourceEpoch:0,
  writerId:'source_fixture',writerSeq:1,level:'L1',lane:'SERVER_ENTITY_STATE',observedAt:new Date().toISOString(),gameTime:1,
  scope:{kind:'ENTITY_UUID',entityUuid:f.prepared.request.subjects[0].uuid},source:{side:'SERVER',method:'source_fixture'},
  epistemicStatus:'OBSERVED',completeness:{complete:true},payload:{health:20,basis:'SOURCE_FIXTURE_NOT_RUNTIME'}});
 await writeFile(path.join(f.runDir,'process.log'),'private-source-fixture: raw process log must never appear in public results');
 const sealed=await finalizeEvidenceRun({...identity,runDir:f.runDir,live:false,status:'STOPPED',runSnapshotHash:f.prepared.snapshot.snapshotHash},
  {cleanShutdown:false,shutdownMode:'UNKNOWN'});
 assert(['EVIDENCE_COMPLETE','EVIDENCE_PARTIAL'].includes(sealed.manifest.status));
 const before=await tree(f.runDir),imported=run('import');
 assert.deepEqual(await tree(f.runDir),before,'export/import must not mutate the sealed run');
 console.log(JSON.stringify({scope:'SOURCE_PROTOCOL_FIXTURE_ONLY',controls,...imported}));
}finally{
 for(const fn of cleanup)await fn();
 await rm(temporary,{recursive:true,force:true});
}
