"""The local LAB file adapter is explicit and cannot launch Minecraft."""
import copy
import hashlib
import importlib
import json
from pathlib import Path
import shutil
import subprocess

import pytest

from kneekura_tech_hub.minecraft.storage import ContractError, canonical, digest
from test_minecraft_experiment_bridge import prepared

MODULES = ('adapter-cli.mjs','adapter.mjs','registration.mjs','materials.mjs','json.mjs','action-journal.mjs','arena-contract.mjs')


def api():
    return importlib.import_module('kneekura_tech_hub.minecraft.experiment_adapter')


@pytest.fixture
def registry(tmp_path):
    root = tmp_path/'lab'; (root/'debug-workspace/bridge').mkdir(parents=True)
    # Actual paired source is optional locally; self-contained protocol fixture
    # tests the process boundary while the cross-repo check uses real LAB code.
    for name in MODULES:
        (root/'debug-workspace/bridge'/name).write_text('// retained fixture module\n')
    entry = root/'debug-workspace/bridge/adapter-cli.mjs'
    entry.write_text("import fs from 'node:fs'; const r=JSON.parse(fs.readFileSync(process.argv[5])); console.log(JSON.stringify({schemaVersion:1,status:'NEVER_SEEN',requestHash:r.requestHash,execution:'NOT_RUN',runtimeAttestation:'NOT_ESTABLISHED'}));\n")
    node = Path(shutil.which('node') or '')
    if not node.is_file(): pytest.skip('Node unavailable')
    node=node.resolve()
    inputs=tmp_path/'inputs'; inputs.mkdir(); runtime=tmp_path/'runtime'; runtime.mkdir()
    owner=tmp_path/'owner.json'; owner.write_bytes(canonical({'schemaVersion':1,'runtimeRoot':str(runtime),'inputRoot':str(inputs),'run':None}))
    return {'schema_version':1,'enabled':True,'backend':'kneekura.lab.local-bridge.v1','workspace':str(root),'source_revision':'a'*40,
      'executable':str(node),'executable_hash':hashlib.file_digest(node.open('rb'),'sha256').hexdigest(),
      'module_hashes':{name:digest((root/'debug-workspace/bridge'/name).read_bytes()) for name in MODULES},
      'owner_file':str(owner),'owner_hash':digest(owner.read_bytes()),'timeout_seconds':5}


def test_inspect_registry_is_inert_exact_and_redacted(registry,monkeypatch):
    monkeypatch.setattr(subprocess,'Popen',lambda *a,**k:pytest.fail('read-only registry inspection spawned'))
    result=api().inspect_registry(registry)
    assert result['status']=='REGISTERED' and result['execution']=='BLOCKED'
    assert result['identity_verification']=='PINNED_EXECUTABLE_AND_MODULE_BYTES'
    assert registry['workspace'] not in json.dumps(result)


@pytest.mark.parametrize('change',['module','owner','binary','extra','bool','symlink'])
def test_registry_integrity_denies_before_process(registry,monkeypatch,change):
    if change=='module': (Path(registry['workspace'])/'debug-workspace/bridge/json.mjs').write_text('changed')
    if change=='owner': Path(registry['owner_file']).write_text('{}')
    if change=='binary': registry['executable_hash']='0'*64
    if change=='extra': registry['args']=['--eval','x']
    if change=='bool': registry['schema_version']=True
    if change=='symlink':
        p=Path(registry['workspace'])/'debug-workspace/bridge/json.mjs'; p.unlink(); p.symlink_to('materials.mjs')
    monkeypatch.setattr(subprocess,'Popen',lambda *a,**k:pytest.fail('invalid registry spawned'))
    with pytest.raises((ContractError,OSError)): api().inspect_registry(registry)


def test_inspect_registration_invokes_only_pinned_local_tool(prepared,registry):
    store,req=prepared
    result=api().inspect_registration(store,registry,'b'*64)
    assert result['status']=='OK' and result['reported']['status']=='NEVER_SEEN'
    assert result['runtime_attestation']=='NOT_ESTABLISHED'
    receipt=store.json(result['receipt_hash'])
    assert receipt['operation']=='inspect_registration'
    assert registry['workspace'] not in json.dumps(receipt)
    assert 'stdout' not in receipt


def test_register_materializes_exact_canonical_request_and_never_claims_execution(prepared,registry):
    from kneekura_tech_hub.minecraft.experiment_bridge import prepare_experiment
    store,req=prepared; saved=prepare_experiment(store,req)
    result=api().register_request(store,registry,saved['request_hash'])
    owner=json.loads(Path(registry['owner_file']).read_bytes()); package=Path(owner['inputRoot'])/saved['request_hash']
    assert (package/'request.json').read_bytes()==canonical(req)
    assert digest((package/'assertions.json').read_bytes())==digest(canonical(req['assertions']))
    assert (package/'build.bin').read_bytes()==store.blob_path(req['target']['build_artifact_hash']).read_bytes()
    assert result['execution']=='NOT_RUN'


def test_timeout_retains_unknown_without_retry(prepared,registry,monkeypatch):
    store,_=prepared; calls=[]
    def timeout(*a,**k):
        calls.append(a); return {'completed':False,'exit_code':-9,'timed_out':True,'output_limited':False,'stdout':b'private-log'}
    monkeypatch.setattr(api(),'run_process',timeout)
    got=api().inspect_registration(store,registry,'b'*64)
    assert len(calls)==1 and got['status']=='UNKNOWN'
    assert got['next_operation']=='experiment.inspect_registration'
    assert 'private-log' not in json.dumps(store.json(got['receipt_hash']))


def test_foreign_request_response_does_not_become_success(prepared,registry,monkeypatch):
    store,_=prepared
    monkeypatch.setattr(api(),'run_process',lambda *a,**k:{'completed':True,'exit_code':0,'stdout':canonical({'schemaVersion':1,'status':'NEVER_SEEN','requestHash':'c'*64,'execution':'NOT_RUN','runtimeAttestation':'NOT_ESTABLISHED'}),'timed_out':False,'output_limited':False})
    got=api().inspect_registration(store,registry,'b'*64)
    assert got['status']=='UNKNOWN'


def test_adapter_child_does_not_inherit_loader_hooks_or_private_environment(prepared, registry, monkeypatch):
    entry = Path(registry['workspace']) / 'debug-workspace/bridge/adapter-cli.mjs'
    entry.write_text("""import fs from 'node:fs';
const forbidden = ['LD_PRELOAD', 'LD_LIBRARY_PATH', 'DYLD_INSERT_LIBRARIES', 'DYLD_LIBRARY_PATH', 'X7_PRIVATE_ENV'];
if (forbidden.some(key => process.env[key])) throw new Error('INHERITED_ENVIRONMENT');
const r = JSON.parse(fs.readFileSync(process.argv[5]));
console.log(JSON.stringify({schemaVersion:1,status:'NEVER_SEEN',requestHash:r.requestHash,execution:'NOT_RUN',runtimeAttestation:'NOT_ESTABLISHED'}));
""")
    registry['module_hashes']['adapter-cli.mjs'] = digest(entry.read_bytes())
    for key in ('LD_PRELOAD', 'LD_LIBRARY_PATH', 'DYLD_INSERT_LIBRARIES', 'DYLD_LIBRARY_PATH', 'X7_PRIVATE_ENV'):
        monkeypatch.setenv(key, '/private/unregistered-loader-or-secret')
    monkeypatch.setenv('NODE_OPTIONS', '--require=/private/unregistered-node-hook')
    monkeypatch.setenv('NODE_PATH', '/private/unregistered-node-modules')
    store, _ = prepared
    result = api().inspect_registration(store, registry, 'b' * 64)
    assert result['status'] == 'OK'
    assert '/private/' not in json.dumps(store.json(result['receipt_hash']))


@pytest.mark.parametrize('command', ['experiment', 'task'])
def test_registry_fifo_rejects_without_blocking_cli(tmp_path, command):
    import os
    import sys
    from test_minecraft_task_context import task_request
    if not hasattr(os, 'mkfifo'):
        pytest.skip('FIFO unavailable on this platform')
    fifo = tmp_path / 'private-registry.json'
    os.mkfifo(fifo)
    root = Path(__file__).resolve().parents[1]
    if command == 'experiment':
        arguments = ['experiment', 'inspect-adapter', '--registry', str(fifo)]
    else:
        request = tmp_path / 'task.json'
        request.write_bytes(canonical(task_request()))
        arguments = ['task', 'prepare', '--request', str(request), '--experiment-registry', str(fifo)]
    child = subprocess.run([sys.executable, '-m', 'kneekura_tech_hub.minecraft', '--store',
        str(tmp_path / 'cas'), *arguments], cwd=root,
        env={**os.environ, 'PYTHONPATH': str(root / 'src')}, capture_output=True, timeout=5)
    assert child.returncode == 2
    assert json.loads(child.stdout)['status'] == 'ERROR'
    assert str(tmp_path).encode() not in child.stdout + child.stderr


def test_cyclic_module_symlink_returns_redacted_cli_error(registry, tmp_path, capsys):
    from kneekura_tech_hub.minecraft.__main__ import main
    module = Path(registry['workspace']) / 'debug-workspace/bridge/json.mjs'
    module.unlink()
    try:
        module.symlink_to('json.mjs')
    except OSError:
        pytest.skip('Symlink creation unavailable on this platform')
    file = tmp_path / 'registry.json'
    file.write_bytes(canonical(registry))
    assert main(['--store', str(tmp_path / 'cas'), 'experiment', 'inspect-adapter',
                 '--registry', str(file)]) == 2
    captured = capsys.readouterr()
    assert json.loads(captured.out)['status'] == 'ERROR'
    assert str(tmp_path) not in captured.out + captured.err
