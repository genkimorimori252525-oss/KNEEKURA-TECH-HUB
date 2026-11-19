"""Explicit finite watching cannot promote runtime or capture evidence."""
import copy
import json
from pathlib import Path
import subprocess

import pytest

from kneekura_tech_hub.minecraft import experiment_bridge as bridge, task_context
from kneekura_tech_hub.minecraft.__main__ import main
from kneekura_tech_hub.minecraft.storage import ContractError, canonical, digest
from test_minecraft_experiment_control import api, control
from test_minecraft_experiment_bridge import prepared, tree
from test_minecraft_task_context import task_request

CONFIG = {'enabled':True,'triggerKinds':['ARENA_EXIT'],'offsetsMs':[-1000,0,1000],
    'toleranceMs':200,'cooldownMs':1000,'maxWindows':1,'captureBudget':1,'timeoutMs':3000,'captureIndices':[0]}


def install(control, config=None):
    store, req, registry, owner = control
    control_dir = Path(owner['run']['runDir'])/'control'
    h = bridge.prepare_experiment(store, req)['request_hash']
    owner['run']['identity']['requestHash'] = h
    envelope = json.loads((control_dir/'owner-envelope.json').read_bytes())
    envelope['requestHash'] = h
    value = copy.deepcopy(CONFIG if config is None else config)
    (control_dir/'owner-trigger-config.json').write_bytes(canonical(value))
    (control_dir/'owner-experiment-request.json').write_bytes(canonical(req))
    envelope['triggerConfigHash'] = digest(canonical(value))
    (control_dir/'owner-envelope.json').write_bytes(canonical(envelope))
    owner['run']['ownerEnvelopeHash'] = digest(canonical(envelope))
    Path(registry['owner_file']).write_bytes(canonical(owner))
    registry['owner_hash'] = digest(canonical(owner))
    return control_dir


@pytest.fixture
def trigger_control(control):
    install(control)
    _, _, registry, _ = control
    entry = Path(registry['workspace'])/'debug-workspace/bridge/owner-control-cli.mjs'
    entry.write_text(entry.read_text().replace('console.log(JSON.stringify(out));', """
if(r.operation==='watch_triggers') Object.assign(out,{status:'WINDOWS_FINISHED',captureWindowIds:['window-1']});
console.log(JSON.stringify(out));
"""))
    registry['module_hashes']['debug-workspace/bridge/owner-control-cli.mjs'] = digest(entry.read_bytes())
    return control


def test_optional_trigger_registry_remains_inert_and_does_not_attest(trigger_control, monkeypatch):
    store, req, registry, _ = trigger_control
    before = tree(store.root)
    monkeypatch.setattr(subprocess, 'Popen', lambda *a, **k: pytest.fail('inert trigger registry spawned'))
    assert api().inspect_registry(registry)['execution'] == 'NOT_RUN'
    context = task_context.prepare_task_context(store, task_request(), index_id=req['target']['index_snapshot_id'],
        experiment_control_registry=registry)
    runtime = next(c for c in context['capabilities'] if c['id']=='experimental_runtime')
    assert runtime['readiness']=='BLOCKED' and runtime['reason_code']=='LAB_RUNTIME_ATTESTATION_REQUIRED'
    assert all(x['operation_id']!='experiment.watch_triggers' for x in context['next_actions'])
    assert tree(store.root)==before


@pytest.mark.parametrize('change', ['missing','tampered','symlink','request_hash','extra','disabled','kind','offset_bool',
    'offset_order','sample_rate','too_many_offsets','tolerance','cooldown','windows','budget','duplicate_slots',
    'foreign_slot','timeout','short_timeout'])
def test_trigger_config_is_pinned_exact_and_bounded_before_process(control, monkeypatch, change):
    config=copy.deepcopy(CONFIG)
    if change=='extra':config['callback']='arbitrary'
    if change=='disabled':config['enabled']=False
    if change=='kind':config['triggerKinds']=['DAMAGE']
    if change=='offset_bool':config['offsetsMs']=[False]
    if change=='offset_order':config['offsetsMs']=[0,-1000]
    if change=='sample_rate':config['offsetsMs']=[0,1]
    if change=='too_many_offsets':config['offsetsMs']=list(range(-10000,10001,250))
    if change=='tolerance':config['toleranceMs']=251
    if change=='cooldown':config['cooldownMs']=999
    if change=='windows':config['maxWindows']=9
    if change=='budget':config['captureBudget']=True
    if change=='duplicate_slots':config.update(captureBudget=2,captureIndices=[0,0])
    if change=='foreign_slot':config['captureIndices']=[1]
    if change=='timeout':config['timeoutMs']=20001
    if change=='short_timeout':config['timeoutMs']=999
    directory=install(control,config)
    file=directory/'owner-trigger-config.json'
    if change=='missing':file.unlink()
    if change=='tampered':file.write_text('{}')
    if change=='request_hash':(directory/'owner-experiment-request.json').write_text('{}')
    if change=='symlink':
        original=file.with_suffix('.original');file.rename(original);file.symlink_to(original.name)
    monkeypatch.setattr(subprocess,'Popen',lambda *a,**k:pytest.fail('invalid trigger scope spawned'))
    with pytest.raises((ContractError,OSError)):api().inspect_registry(control[2])


def test_trigger_config_cannot_exceed_retained_request_time(control):
    control[1]['budgets']['time_budget_ms']=2000
    install(control)
    with pytest.raises(ContractError):api().inspect_registry(control[2])


def test_watch_requires_explicit_opt_in_and_has_no_generic_arguments(control,monkeypatch):
    store,_,registry,owner=control
    monkeypatch.setattr(subprocess,'Popen',lambda *a,**k:pytest.fail('unconfigured watcher spawned'))
    with pytest.raises(ContractError):api().watch_triggers(store,registry,owner['run']['identity']['requestHash'])


def test_only_explicit_watch_uses_the_retained_time_budget(trigger_control,monkeypatch):
    store,req,registry,owner=trigger_control
    req['budgets']['time_budget_ms']=120000;install(trigger_control)
    registry['timeout_seconds']=10
    calls=[]
    def run(argv,*args,**kwargs):
        calls.append((argv,kwargs))
        command=json.loads(Path(argv[-1]).read_bytes())
        response={'schemaVersion':1,'operation':command['operation'],'requestHash':command['requestHash'],
                  'runtimeAttestation':'NOT_ESTABLISHED'}
        if command['operation']=='watch_triggers':response.update(status='WINDOWS_FINISHED',captureWindowIds=['window-1'])
        else:response.update(status='OWNER_RECORDED',ownerEnvelopeHash=owner['run']['ownerEnvelopeHash'])
        return {'completed':True,'exit_code':0,'stdout':canonical(response)}
    monkeypatch.setattr(api(),'run_process',run)
    h=owner['run']['identity']['requestHash']
    watched=api().watch_triggers(store,registry,h)
    assert watched['command']=={'schemaVersion':1,'operation':'watch_triggers','requestHash':h}
    assert watched['status']=='WINDOWS_FINISHED' and watched['next_operation']=='experiment.inspect_owner'
    assert 120 < calls[0][1]['timeout'] <= 130 and calls[0][1]['inherit_environment'] is False
    api().inspect_owner(store,registry,h)
    assert 0 < calls[1][1]['timeout'] <= 10
    registry['timeout_seconds']=11
    with pytest.raises(ContractError):api().watch_triggers(store,registry,h)


@pytest.mark.parametrize('failure',['timeout','exit','exception','extra','duplicate','too_many','pass','foreign'])
def test_watch_failures_retain_unknown_without_retry(trigger_control,monkeypatch,failure):
    store,_,registry,owner=trigger_control;h=owner['run']['identity']['requestHash'];calls=[]
    def run(*a,**k):
        calls.append(1)
        if failure=='exception':raise OSError('/private/raw/path')
        response={'schemaVersion':1,'operation':'watch_triggers','requestHash':h,'status':'WINDOWS_FINISHED',
            'runtimeAttestation':'NOT_ESTABLISHED','captureWindowIds':['window-1']}
        if failure=='extra':response['captures']=[{'path':'/private/raw/path'}]
        if failure=='duplicate':response['captureWindowIds']=['same','same']
        if failure=='too_many':response['captureWindowIds']=[str(i) for i in range(9)]
        if failure=='pass':response['status']='PASS'
        if failure=='foreign':response['requestHash']='0'*64
        return {'completed':failure!='timeout','timed_out':failure=='timeout','exit_code':2 if failure=='exit' else 0,'stdout':canonical(response)}
    monkeypatch.setattr(api(),'run_process',run)
    got=api().watch_triggers(store,registry,h)
    assert calls==[1] and got['status']=='OUTCOME_UNKNOWN' and got['reported'] is None
    assert got['can_replay'] is False and got['receipt_hash'] in store.pinned_hashes()
    assert '/private' not in json.dumps(got)


@pytest.mark.parametrize('status',['WINDOWS_FINISHED','OWNER_WATCH_DEADLINE','OWNER_NOT_ACTIVE'])
def test_even_finished_watch_preserves_inert_read_only_reconciliation(trigger_control,monkeypatch,status):
    store,req,registry,owner=trigger_control;h=owner['run']['identity']['requestHash']
    response={'schemaVersion':1,'operation':'watch_triggers','requestHash':h,'status':status,
        'runtimeAttestation':'NOT_ESTABLISHED','captureWindowIds':['window-1']}
    monkeypatch.setattr(api(),'run_process',lambda *a,**k:{'completed':True,'exit_code':0,'stdout':canonical(response)})
    got=api().watch_triggers(store,registry,h)
    assert got['status']==status and api().inspect_receipt(store,got['receipt_hash'])['requires_reconciliation'] is True
    before=tree(store.root)
    monkeypatch.setattr(subprocess,'Popen',lambda *a,**k:pytest.fail('TaskContext watched triggers'))
    context=task_context.prepare_task_context(store,task_request(),index_id=req['target']['index_snapshot_id'],
        experiment_control_registry=registry,experiment_control_receipt_hash=got['receipt_hash'])
    assert context['next_actions'][0]['operation_id']=='experiment.inspect_owner'
    assert all(a['mode']=='READ_ONLY' for a in context['next_actions']) and tree(store.root)==before


def test_watch_cli_requires_only_registered_request(trigger_control,tmp_path,capsys):
    store,_,registry,owner=trigger_control
    file=tmp_path/'registry.json';file.write_bytes(canonical(registry))
    args=['--store',str(store.root),'experiment','watch-triggers','--registry',str(file),
          '--request-hash',owner['run']['identity']['requestHash']]
    assert main(args)==0
    assert json.loads(capsys.readouterr().out)['status']=='WINDOWS_FINISHED'
    with pytest.raises(SystemExit):main([*args,'--watch-ms','100000'])


@pytest.mark.parametrize('name', [
    'bridge/owner-trigger-config.mjs', 'bridge/owner-trigger-source.mjs', 'bridge/owner-tank-rotation.mjs',
    'evidence/broker.mjs', 'evidence/capture.mjs', 'evidence/ingest.mjs',
    'evidence/runtime.mjs', 'evidence/trigger-capture.mjs', 'evidence/watchpoints.mjs',
    'bridge/tank-preflight.mjs', 'bridge/tank-resource.mjs', 'evidence/tank-contract.mjs'])
@pytest.mark.parametrize('change', ['missing', 'tampered'])
def test_every_new_imported_leaf_remains_pinned(control, monkeypatch, name, change):
    store,_,registry,owner=control
    assert len(api().MODULES)==31
    relative='debug-workspace/'+name
    assert relative in api().MODULES
    if change=='missing':registry['module_hashes'].pop(relative)
    else:(Path(registry['workspace'])/relative).write_text('// changed imported leaf\n')
    monkeypatch.setattr(subprocess,'Popen',lambda *a,**k:pytest.fail('changed source closure dispatched'))
    with pytest.raises(ContractError):api().inspect_owner(store,registry,owner['run']['identity']['requestHash'])


def test_optional_tank_plan_and_predecessor_are_pinned_without_dispatch(control, monkeypatch):
    store,_,registry,owner=control
    root=Path(owner['run']['runDir'])/'control'
    envelope=json.loads((root/'owner-envelope.json').read_bytes())
    previous=canonical({'status':'GEOMETRY_VERIFIED','arenaEpoch':8})
    plan={'schemaVersion':1,'scope':'PRE_EXPERIMENT_TANK_ROTATION','rotationId':'rotation',
        **{key:envelope[key] for key in ('debugSessionId','runId','runSnapshotId','processEpoch','handshakeNonce','requestHash')},
        'grantId':'grant','leaseId':'lease','arenaId':'arena','expectedArenaEpoch':0,'expectedArenaRevision':0,
        'previousOwnerFileSha256':digest(previous),'previousRecipeHash':'a'*64,'previousTankEpoch':8,
        'nextRecipeHash':'b'*64,'nextRecipe':{}}
    # This fixture tests local closure pins only; actual Node/Java parsing rejects its non-native recipe.
    (root/'owner-tank-rotation.json').write_bytes(canonical(plan))
    (root/'owner-tank-predecessor.json').write_bytes(previous)
    envelope['tankRotationHash']=digest(canonical(plan));(root/'owner-envelope.json').write_bytes(canonical(envelope))
    owner['run']['ownerEnvelopeHash']=digest(canonical(envelope));Path(registry['owner_file']).write_bytes(canonical(owner));registry['owner_hash']=digest(canonical(owner))
    monkeypatch.setattr(subprocess,'Popen',lambda *a,**k:pytest.fail('read-only Tank pin inspection dispatched'))
    before=tree(store.root);result=api().inspect_registry(registry)
    assert result['execution']=='NOT_RUN' and result['runtime_attestation']=='NOT_ESTABLISHED' and tree(store.root)==before
    (root/'owner-tank-predecessor.json').write_bytes(b'changed')
    with pytest.raises(ContractError):api().inspect_registry(registry)


@pytest.mark.parametrize('bad_hash',[None,'',True,'not-a-hash'])
def test_optional_tank_pin_cannot_be_null_or_malformed(control,bad_hash):
    _,_,registry,owner=control
    file=Path(owner['run']['runDir'])/'control/owner-envelope.json'
    envelope=json.loads(file.read_bytes());envelope['tankRotationHash']=bad_hash
    file.write_bytes(canonical(envelope));owner['run']['ownerEnvelopeHash']=digest(canonical(envelope))
    Path(registry['owner_file']).write_bytes(canonical(owner));registry['owner_hash']=digest(canonical(owner))
    with pytest.raises(ContractError):api().inspect_registry(registry)


@pytest.mark.parametrize('bad_hash', [None, '', True, 'not-a-hash'])
def test_optional_trigger_pin_cannot_be_null_or_malformed(trigger_control, bad_hash):
    _,_,registry,owner=trigger_control
    file=Path(owner['run']['runDir'])/'control/owner-envelope.json'
    envelope=json.loads(file.read_bytes());envelope['triggerConfigHash']=bad_hash
    file.write_bytes(canonical(envelope));owner['run']['ownerEnvelopeHash']=digest(file.read_bytes())
    Path(registry['owner_file']).write_bytes(canonical(owner));registry['owner_hash']=digest(canonical(owner))
    with pytest.raises(ContractError):api().inspect_registry(registry)
