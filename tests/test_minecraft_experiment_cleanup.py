"""One explicitly requested owner cleanup, with no automatic reset or replay."""
import json
from pathlib import Path
import subprocess

import pytest

from kneekura_tech_hub.minecraft import task_context
from kneekura_tech_hub.minecraft.__main__ import main
from kneekura_tech_hub.minecraft.storage import ContractError, canonical, digest
from test_minecraft_experiment_bridge import prepared, tree
from test_minecraft_experiment_control import api, control
from test_minecraft_task_context import task_request


@pytest.fixture
def cleanup_control(control):
    store, request, registry, owner = control
    entry = Path(registry['workspace'])/'debug-workspace/bridge/owner-control-cli.mjs'
    text = entry.read_text().replace('console.log(JSON.stringify(out));', """
if(r.operation==='request_cleanup') Object.assign(out,{status:'REQUESTED'});
if(r.operation==='inspect_cleanup') Object.assign(out,{status:'REQUESTED',recordedStatus:'REQUESTED',evidenceHashes:[],dispatchAllowed:false});
console.log(JSON.stringify(out));
""")
    entry.write_text(text)
    registry['module_hashes']['debug-workspace/bridge/owner-control-cli.mjs'] = digest(entry.read_bytes())
    return store, request, registry, owner


def test_cleanup_is_an_explicit_fixed_request_and_stays_pending(cleanup_control):
    store, _, registry, owner = cleanup_control
    h = owner['run']['identity']['requestHash']
    value = api().request_cleanup(store, registry, h)
    assert value['status'] == 'REQUESTED' and value['runtime_attestation'] == 'NOT_ESTABLISHED'
    assert value['command'] == {'schemaVersion':1, 'operation':'request_cleanup', 'requestHash':h}
    assert value['next_operation'] == 'experiment.inspect_cleanup' and value['can_replay'] is False
    assert 'COMPLETED' not in json.dumps(value) and 'CONFIRMED' not in json.dumps(value)
    queried = api().inspect_cleanup(store, registry, h)
    assert queried['status'] == 'REQUESTED' and queried['reported']['dispatchAllowed'] is False
    assert queried['command'] == {'schemaVersion':1, 'operation':'inspect_cleanup', 'requestHash':h}


@pytest.mark.parametrize('failure', ['timeout','exit','exception','foreign','extra_payload','completed'])
def test_ambiguous_cleanup_retains_unknown_without_retry(cleanup_control, monkeypatch, failure):
    store, _, registry, owner = cleanup_control; calls = []
    h = owner['run']['identity']['requestHash']
    def invoke(*args, **kwargs):
        calls.append(args)
        if failure == 'exception': raise OSError('private source failure after possible publication')
        response = {'schemaVersion':1,'operation':'request_cleanup','requestHash':h,
                    'status':'REQUESTED','runtimeAttestation':'NOT_ESTABLISHED'}
        if failure == 'foreign': response['requestHash'] = '0'*64
        if failure == 'extra_payload': response['resetArgs'] = {'bounds':'unregistered'}
        if failure == 'completed': response['status'] = 'CONFIRMED'
        return {'completed':failure!='timeout','exit_code':2 if failure=='exit' else 0,
                'timed_out':failure=='timeout','stdout':canonical(response)}
    monkeypatch.setattr(api(), 'run_process', invoke)
    got = api().request_cleanup(store, registry, h)
    assert len(calls) == 1 and got['status'] == 'OUTCOME_UNKNOWN'
    assert got['reported'] is None and got['next_operation'] == 'experiment.inspect_cleanup'
    assert got['can_replay'] is False and got['receipt_hash'] in store.pinned_hashes()
    assert 'private source' not in json.dumps(store.json(got['receipt_hash']))


@pytest.mark.parametrize('status,recorded,evidence', [('REQUESTED','REQUESTED',[]),
    ('OUTCOME_UNKNOWN',None,[]), ('OUTCOME_UNKNOWN','ACCEPTED',[]),
    ('PARTIAL_APPLY','PARTIAL_APPLY',['1'*64]), ('FAILED','FAILED',[]),
    ('VERIFIED','VERIFIED',['1'*64]), ('NOT_RUN','NOT_RUN',[]), ('NEVER_SEEN',None,[])])
def test_cleanup_receipt_only_recommends_readonly_reconciliation(cleanup_control, monkeypatch, status, recorded, evidence):
    store, req, registry, owner = cleanup_control
    h = owner['run']['identity']['requestHash']
    response = {'schemaVersion':1,'operation':'inspect_cleanup','requestHash':h,'status':status,
        'runtimeAttestation':'NOT_ESTABLISHED','recordedStatus':recorded,'evidenceHashes':evidence,'dispatchAllowed':False}
    monkeypatch.setattr(api(),'run_process',lambda *a,**k:{'completed':True,'exit_code':0,'stdout':canonical(response)})
    got = api().inspect_cleanup(store, registry, h)
    assert got['status'] == status
    assert api().inspect_receipt(store,got['receipt_hash'])['requires_reconciliation'] is True
    before = tree(store.root)
    monkeypatch.setattr(subprocess,'Popen',lambda *a,**k:pytest.fail('TaskContext started cleanup or inspection'))
    context = task_context.prepare_task_context(store,task_request(),index_id=req['target']['index_snapshot_id'],
        experiment_control_registry=registry,experiment_control_receipt_hash=got['receipt_hash'])
    assert context['next_actions'][0]['operation_id']=='experiment.inspect_cleanup'
    assert all(x['mode']=='READ_ONLY' and x['operation_id']!='experiment.request_cleanup' for x in context['next_actions'])
    assert tree(store.root)==before


@pytest.mark.parametrize('status,recorded,evidence', [('VERIFIED','VERIFIED',[]),
    ('VERIFIED','OUTCOME_UNKNOWN',['1'*64]), ('NEVER_SEEN',None,['1'*64])])
def test_cleanup_inspection_rejects_contradictory_or_unbacked_result(cleanup_control,monkeypatch,status,recorded,evidence):
    store,_,registry,owner=cleanup_control;h=owner['run']['identity']['requestHash']
    response={'schemaVersion':1,'operation':'inspect_cleanup','requestHash':h,'status':status,
        'runtimeAttestation':'NOT_ESTABLISHED','recordedStatus':recorded,'evidenceHashes':evidence,'dispatchAllowed':False}
    monkeypatch.setattr(api(),'run_process',lambda *a,**k:{'completed':True,'exit_code':0,'stdout':canonical(response)})
    got=api().inspect_cleanup(store,registry,h)
    assert got['status']=='OUTCOME_UNKNOWN' and got['reported'] is None


def test_cleanup_cli_has_no_raw_arguments(cleanup_control,tmp_path,capsys):
    store,_,registry,owner=cleanup_control;h=owner['run']['identity']['requestHash']
    file=tmp_path/'registry.json';file.write_bytes(canonical(registry))
    prefix=['--store',str(store.root),'experiment']
    options=['--registry',str(file),'--request-hash',h]
    assert main([*prefix,'request-cleanup',*options])==0
    got=json.loads(capsys.readouterr().out)
    assert got['status']=='REQUESTED' and got['next_operation']=='experiment.inspect_cleanup'
    assert main([*prefix,'inspect-cleanup',*options])==0
    assert json.loads(capsys.readouterr().out)['reported']['dispatchAllowed'] is False
    with pytest.raises(SystemExit): main([*prefix,'request-cleanup',*options,'--reset-command','anything'])


def test_cleanup_does_not_expand_legacy_authority(cleanup_control,monkeypatch):
    store,_,registry,owner=cleanup_control
    registry['backend']='kneekura.lab.local-bridge.v1'
    monkeypatch.setattr(subprocess,'Popen',lambda *a,**k:pytest.fail('legacy registry dispatched cleanup'))
    with pytest.raises(ContractError): api().request_cleanup(store,registry,owner['run']['identity']['requestHash'])


def test_cleanup_inspection_without_marker_or_journal_is_never_seen(cleanup_control,monkeypatch):
    store,_,registry,owner=cleanup_control;h=owner['run']['identity']['requestHash']
    response={'schemaVersion':1,'operation':'inspect_cleanup','requestHash':h,'status':'NEVER_SEEN',
        'runtimeAttestation':'NOT_ESTABLISHED','recordedStatus':None,'evidenceHashes':[],'dispatchAllowed':False}
    monkeypatch.setattr(api(),'run_process',lambda *a,**k:{'completed':True,'exit_code':0,'stdout':canonical(response)})
    got=api().inspect_cleanup(store,registry,h)
    assert got['status']=='NEVER_SEEN' and got['reported']==response and got['can_replay'] is False
