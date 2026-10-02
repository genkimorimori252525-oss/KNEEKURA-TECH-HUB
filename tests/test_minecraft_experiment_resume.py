"""Retained experiment reports can be resumed without replay or live assertions."""
import json
import subprocess

import pytest

from kneekura_tech_hub.minecraft import experiment_bridge as bridge, task_context
from kneekura_tech_hub.minecraft.storage import IntegrityError
from test_minecraft_experiment_bridge import prepared, reported, tree
from test_minecraft_task_context import task_request


def saved_report(store,req,unknown=False):
    h=bridge.prepare_experiment(store,req)['request_hash']; report,_=reported(store,req)
    if unknown:
        report['execution'].update(status='UNKNOWN',cleanup='UNKNOWN')
        for row in report['assertions']: row.update(status='UNKNOWN',evidence_hashes=[])
    return bridge.import_experiment_result(store,h,report)['result_hash']


def test_resume_second_agent_exact_closure_inert_and_historical(prepared,monkeypatch):
    store,req=prepared; h=saved_report(store,req); before=tree(store.root)
    monkeypatch.setattr(subprocess,'Popen',lambda *a,**kw:pytest.fail('resume executed'))
    got=bridge.resume_experiment(store,h)
    assert got['result_hash']==h and got['request_hash']
    assert got['runtime_attestation']=='NOT_ESTABLISHED'
    assert got['can_replay'] is False and got['execution_authority']=='NONE'
    assert got['assertions'][0]['status']=='PASS' and got['assertion_basis']=='IMPORTED_LAB_REPORT'
    assert got['evidence'] and all(set(x)=={'content_hash','kind','size_bytes'} for x in got['evidence'])
    assert tree(store.root)==before


def test_resume_unknown_has_reconciliation_and_no_retry(prepared):
    store,req=prepared; got=bridge.resume_experiment(store,saved_report(store,req,True))
    assert got['next_operation']=='experiment.reconcile_unknown'
    assert 'EXECUTION_UNKNOWN' in got['open_gates'] and 'CLEANUP_UNKNOWN' in got['open_gates']
    assert got['can_replay'] is False


def test_task_context_report_exposes_safe_resume_not_runtime_authority(prepared,monkeypatch):
    store,req=prepared; h=saved_report(store,req); before=tree(store.root)
    monkeypatch.setattr(subprocess,'Popen',lambda *a,**kw:pytest.fail('TaskContext executed'))
    got=task_context.prepare_task_context(store,task_request(),index_id=req['target']['index_snapshot_id'],experiment_result_hash=h)
    c=next(c for c in got['capabilities'] if c['id']=='experimental_runtime')
    assert c['surface']=='IMPLEMENTED' and c['readiness']=='BLOCKED'
    assert h in c['evidence']
    assert any(a['operation_id']=='experiment.inspect_result' for a in got['next_actions'])
    assert not any(a['operation_id']=='experiment.execute' for a in got['next_actions'])
    assert tree(store.root)==before


def test_task_context_unknown_suppresses_mutation_advice(prepared):
    store,req=prepared; h=saved_report(store,req,True)
    got=task_context.prepare_task_context(store,task_request(),index_id=req['target']['index_snapshot_id'],experiment_result_hash=h)
    assert got['next_actions'][0]['operation_id']=='experiment.reconcile_unknown'
    assert all(a['mode']=='READ_ONLY' for a in got['next_actions'])


def test_task_context_corrupt_explicit_report_never_falls_back(prepared):
    store,req=prepared; h=saved_report(store,req); store.blob_path(h).write_bytes(b'corrupt')
    with pytest.raises(IntegrityError): task_context.prepare_task_context(store,task_request(),experiment_result_hash=h)


def test_cli_resume_and_task_explicit_report(prepared,tmp_path,capsys):
    from kneekura_tech_hub.minecraft.__main__ import main
    from kneekura_tech_hub.minecraft.storage import canonical
    store,req=prepared; h=saved_report(store,req)
    assert main(['--store',str(store.root),'experiment','resume','--result-hash',h])==0
    assert json.loads(capsys.readouterr().out)['can_replay'] is False
    file=tmp_path/'task.json';file.write_bytes(canonical(task_request()))
    assert main(['--store',str(store.root),'task','prepare','--request',str(file),'--experiment-result',h])==0
    assert any(c['id']=='experimental_runtime' and h in c['evidence'] for c in json.loads(capsys.readouterr().out)['capabilities'])


def test_task_cli_missing_report_redacts_private_store_path(tmp_path,capsys):
    from kneekura_tech_hub.minecraft.__main__ import main
    from kneekura_tech_hub.minecraft.storage import canonical
    file=tmp_path/'task.json';file.write_bytes(canonical(task_request()))
    assert main(['--store',str(tmp_path/'private-secret-cas'),'task','prepare','--request',str(file),'--experiment-result','a'*64])==2
    out=capsys.readouterr().out
    assert 'private-secret-cas' not in out and str(tmp_path) not in out


def test_resume_preserves_typed_retained_gaps(prepared):
    store, req = prepared
    request_hash = bridge.prepare_experiment(store, req)['request_hash']
    report, _ = reported(store, req)
    report['assertions'][0].update(status='NOT_LOADED', evidence_hashes=[])
    report['gaps'] = [{'code': 'NOT_LOADED', 'assertion_id': report['assertions'][0]['assertion_id']}]
    result_hash = bridge.import_experiment_result(store, request_hash, report)['result_hash']
    before = tree(store.root)
    resumed = bridge.resume_experiment(store, result_hash)
    assert resumed['gaps'] == report['gaps']
    assert resumed['can_replay'] is False
    assert tree(store.root) == before


def test_task_context_marks_retained_report_from_other_index_stale(prepared, tmp_path):
    from kneekura_tech_hub.minecraft import index, storage
    from test_minecraft_storage import manifest
    store, req = prepared
    result_hash = saved_report(store, req)
    current = manifest()
    current['workspace_revision'] = 'd' * 40
    profile = storage.capture_profile(current, tmp_path, store)
    other_index = index.prepare_index(profile, store)['index_snapshot_id']
    before = tree(store.root)
    inputs = task_context.load_task_inputs(store, index_id=other_index, experiment_result_hash=result_hash)
    report = inputs['experiment_report']
    assert report['currentness'] == 'REVERIFY_REQUIRED'
    assert 'CURRENT_TARGET_CHANGED' in report['open_gates']
    assert {'index_snapshot_id', 'source_revision'} <= set(report['changed_target_fields'])
    context = task_context.prepare_task_context(store, task_request(), index_id=other_index,
                                                 experiment_result_hash=result_hash)
    capability = next(row for row in context['capabilities'] if row['id'] == 'experimental_runtime')
    assert capability['readiness'] == 'BLOCKED'
    assert capability['reason_code'] == 'EXPERIMENT_TARGET_CHANGED'
    assert tree(store.root) == before


@pytest.mark.parametrize('command', ['resume', 'task'])
def test_cyclic_retained_cas_parent_returns_redacted_cli_error(prepared, tmp_path, capsys, command):
    from kneekura_tech_hub.minecraft.__main__ import main
    from kneekura_tech_hub.minecraft.storage import canonical
    store, req = prepared
    result_hash = saved_report(store, req)
    parent = store.blob_path(result_hash).parent
    parent.rename(parent.with_name(parent.name + '-original'))
    try:
        parent.symlink_to(parent.name, target_is_directory=True)
    except OSError:
        pytest.skip('Symlink creation unavailable on this platform')
    if command == 'resume':
        arguments = ['experiment', 'resume', '--result-hash', result_hash]
    else:
        request = tmp_path / 'task.json'
        request.write_bytes(canonical(task_request()))
        arguments = ['task', 'prepare', '--request', str(request), '--experiment-result', result_hash]
    assert main(['--store', str(store.root), *arguments]) == 2
    captured = capsys.readouterr()
    assert json.loads(captured.out)['status'] == 'ERROR'
    assert str(tmp_path) not in captured.out + captured.err


def test_resume_current_target_fifo_is_rejected_without_blocking(prepared, tmp_path):
    import os
    from pathlib import Path
    import sys
    if not hasattr(os, 'mkfifo'):
        pytest.skip('FIFO unavailable on this platform')
    store, req = prepared
    result_hash = saved_report(store, req)
    fifo = tmp_path / 'private-current-target.json'
    os.mkfifo(fifo)
    root = Path(__file__).resolve().parents[1]
    child = subprocess.run([sys.executable, '-m', 'kneekura_tech_hub.minecraft', '--store',
        str(store.root), 'experiment', 'resume', '--result-hash', result_hash,
        '--current-target', str(fifo)], cwd=root,
        env={**os.environ, 'PYTHONPATH': str(root / 'src')}, capture_output=True, timeout=5)
    assert child.returncode == 2
    assert json.loads(child.stdout)['status'] == 'ERROR'
    assert str(tmp_path).encode() not in child.stdout + child.stderr
