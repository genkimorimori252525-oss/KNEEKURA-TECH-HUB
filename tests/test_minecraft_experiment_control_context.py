"""Explicit scoped-control inputs stay inert and preserve completion uncertainty."""
import json
from pathlib import Path
import subprocess

import pytest

from kneekura_tech_hub.minecraft import task_context
from kneekura_tech_hub.minecraft.__main__ import main
from kneekura_tech_hub.minecraft.storage import ContractError, canonical
from test_minecraft_experiment_bridge import prepared, tree
from test_minecraft_experiment_control import control, api
from test_minecraft_experiment_export import exported, save_manifest
from test_minecraft_task_context import task_request


def test_control_registry_task_context_is_inert_and_never_live_ready(control, monkeypatch):
    store, req, registry, _ = control; before = tree(store.root)
    monkeypatch.setattr(subprocess, 'Popen', lambda *a, **k: pytest.fail('TaskContext spawned'))
    result = task_context.prepare_task_context(store, task_request(), index_id=req['target']['index_snapshot_id'],
                                               experiment_control_registry=registry)
    capability = next(c for c in result['capabilities'] if c['id']=='experimental_runtime')
    assert capability['readiness']=='BLOCKED' and 'loaded_runtime_attestation' in capability['missing']
    assert any(a['operation_id']=='experiment.inspect_owner' and a['mode']=='READ_ONLY' for a in result['next_actions'])
    assert all(a['operation_id'] not in ('experiment.submit_action','experiment.request_cleanup') for a in result['next_actions'])
    assert str(Path(registry['owner_file']).parent) not in json.dumps(result)
    assert tree(store.root)==before


@pytest.mark.parametrize('index', [True, False])
@pytest.mark.parametrize('unknown', [True, False])
def test_pending_or_uncertain_control_receipt_suppresses_all_mutation_advice(control, monkeypatch, index, unknown):
    store, req, registry, owner = control
    if unknown:
        monkeypatch.setattr(api(), 'run_process', lambda *a, **k: {'completed':False,'exit_code':-9,'timed_out':True,'stdout':b'private'})
    action_id=(req['initial_state']+req['actions'])[0]['action_id']
    receipt=api().submit_action(store,registry,owner['run']['identity']['requestHash'],action_id)
    before=tree(store.root)
    monkeypatch.setattr(subprocess,'Popen',lambda *a,**k:pytest.fail('TaskContext spawned'))
    result=task_context.prepare_task_context(store,task_request(),index_id=req['target']['index_snapshot_id'] if index else None,
        experiment_control_registry=registry,experiment_control_receipt_hash=receipt['receipt_hash'])
    capability=next(c for c in result['capabilities'] if c['id']=='experimental_runtime')
    assert capability['readiness']=='UNKNOWN'
    assert receipt['receipt_hash'] in capability['evidence']
    assert result['next_actions'][0]['operation_id']=='experiment.inspect_action'
    assert all(row['mode']=='READ_ONLY' for row in result['next_actions'])
    assert tree(store.root)==before


def test_corrupt_or_forged_control_receipt_cannot_fall_back(control):
    store,req,registry,owner=control
    action_id=(req['initial_state']+req['actions'])[0]['action_id']
    h=api().submit_action(store,registry,owner['run']['identity']['requestHash'],action_id)['receipt_hash']
    record=store.json(h);record['status']='VERIFIED';bad=store.put_json(record)
    with pytest.raises(ContractError):
        task_context.prepare_task_context(store,task_request(),experiment_control_receipt_hash=bad)
    store.blob_path(h).write_bytes(b'corrupt')
    with pytest.raises(ContractError):
        task_context.prepare_task_context(store,task_request(),experiment_control_receipt_hash=h)


def test_control_registry_cannot_replace_legacy_registry(control):
    store,_,registry,_=control
    with pytest.raises(ContractError):
        task_context.prepare_task_context(store,task_request(),experiment_registry=registry)


def test_explicit_control_cli_and_task_flags(control, tmp_path, capsys):
    store,req,registry,owner=control
    file=tmp_path/'control-registry.json';file.write_bytes(canonical(registry))
    base=['--store',str(store.root),'experiment']
    assert main([*base,'inspect-control','--registry',str(file)])==0
    assert json.loads(capsys.readouterr().out)['status']=='REGISTERED'
    action_id=(req['initial_state']+req['actions'])[0]['action_id']
    args=['--registry',str(file),'--request-hash',owner['run']['identity']['requestHash']]
    assert main([*base,'submit-action',*args,'--action-id',action_id])==0
    receipt=json.loads(capsys.readouterr().out)
    assert receipt['status']=='REQUESTED'
    assert main([*base,'inspect-control-receipt','--receipt-hash',receipt['receipt_hash']])==0
    assert json.loads(capsys.readouterr().out)['requires_reconciliation'] is True
    task=tmp_path/'task.json';task.write_bytes(canonical(task_request()))
    assert main(['--store',str(store.root),'task','prepare','--request',str(task),
        '--experiment-control-registry',str(file),'--experiment-control-receipt',receipt['receipt_hash']])==0
    result=json.loads(capsys.readouterr().out)
    assert result['next_actions'][0]['operation_id']=='experiment.inspect_action'
    assert all(row['mode']=='READ_ONLY' for row in result['next_actions'])


def test_explicit_import_export_cli(exported,tmp_path,capsys):
    store,registry,request_hash,_,manifest,root=exported
    h=save_manifest(root,manifest);file=tmp_path/'control-registry.json';file.write_bytes(canonical(registry))
    assert main(['--store',str(store.root),'experiment','import-export','--registry',str(file),
                 '--request-hash',request_hash,'--manifest-hash',h])==0
    result=json.loads(capsys.readouterr().out)
    assert result['export_manifest_hash']==h and result['runtime_attestation']=='NOT_ESTABLISHED'


@pytest.mark.parametrize('command',['inspect-control','task'])
def test_scoped_registry_cli_rejects_fifo_without_waiting(tmp_path,command):
    import os
    import sys
    if not hasattr(os,'mkfifo'):pytest.skip('FIFO unavailable')
    fifo=tmp_path/'private-owner-config.json';os.mkfifo(fifo)
    if command=='task':
        file=tmp_path/'task.json';file.write_bytes(canonical(task_request()))
        args=['task','prepare','--request',str(file),'--experiment-control-registry',str(fifo)]
    else:args=['experiment','inspect-control','--registry',str(fifo)]
    root=Path(__file__).resolve().parents[1]
    child=subprocess.run([sys.executable,'-m','kneekura_tech_hub.minecraft','--store',str(tmp_path/'cas'),*args],
        cwd=root,env={**os.environ,'PYTHONPATH':str(root/'src')},capture_output=True,timeout=5)
    assert child.returncode==2 and json.loads(child.stdout)['status']=='ERROR'
    assert str(tmp_path).encode() not in child.stdout+child.stderr


def test_failed_journal_summary_without_failure_phase_keeps_reconciliation(control, monkeypatch):
    store, request, registry, owner = control
    request_hash = owner['run']['identity']['requestHash']
    action_id = (request['initial_state'] + request['actions'])[0]['action_id']
    response = {'schemaVersion':1,'operation':'inspect_action','requestHash':request_hash,
      'status':'FAILED','runtimeAttestation':'NOT_ESTABLISHED','selectedActionId':action_id,
      'recordedStatus':'FAILED','evidenceHashes':[],'dispatchAllowed':False}
    monkeypatch.setattr(api(), 'run_process', lambda *a, **k: {'completed':True, 'exit_code':0, 'stdout':canonical(response)})
    receipt = api().inspect_action(store, registry, request_hash, action_id)
    checked = api().inspect_receipt(store, receipt['receipt_hash'])
    context = task_context.prepare_task_context(store, task_request(), experiment_control_receipt_hash=receipt['receipt_hash'])
    assert checked['requires_reconciliation'] is True, context['next_actions']
    assert all(row['mode'] == 'READ_ONLY' for row in context['next_actions'])
