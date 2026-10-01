"""Public offline bridge routes remain inert with respect to LAB/runtime."""
import copy
import json
import socket
import subprocess

import pytest

from kneekura_tech_hub.minecraft.__main__ import main
from kneekura_tech_hub.minecraft import task_context
from kneekura_tech_hub.minecraft.storage import Store, canonical
from test_minecraft_experiment_bridge import prepared, reported
from test_minecraft_experiment_contract import request
from test_minecraft_task_context import task_request


def call(capsys, store, *args):
    status = main(['--store', str(store.root), 'experiment', *args])
    return status, json.loads(capsys.readouterr().out)


def test_cli_validate_is_inert_and_exposes_no_execute_command(tmp_path, capsys, monkeypatch):
    store = Store(tmp_path / 'unused')
    path = tmp_path / 'request.json'; path.write_bytes(canonical(request()))
    def forbidden(*args, **kwargs): pytest.fail('offline experiment validation executed/contacted something')
    monkeypatch.setattr(subprocess, 'Popen', forbidden); monkeypatch.setattr(socket, 'socket', forbidden)
    code, value = call(capsys, store, 'validate', '--request', str(path))
    assert code == 0 and value['execution'] == 'NOT_RUN'
    assert value['runtime_attestation'] == 'NOT_ESTABLISHED'
    assert not store.root.exists()
    with pytest.raises(SystemExit): call(capsys, store, 'execute', '--request', str(path))


def test_cli_prepare_import_inspect_preserves_reported_scope(prepared, tmp_path, capsys):
    store, req = prepared; path = tmp_path / 'request.json'; path.write_bytes(canonical(req))
    code, saved = call(capsys, store, 'prepare', '--request', str(path)); assert code == 0
    code, loaded = call(capsys, store, 'inspect-request', '--request-hash', saved['request_hash'])
    assert code == 0 and loaded['request'] == req
    response, _ = reported(store, req); file = tmp_path / 'result.json'; file.write_bytes(canonical(response))
    code, imported = call(capsys, store, 'import-result', '--request-hash', saved['request_hash'], '--result', str(file))
    assert code == 0 and imported['provenance'] == 'IMPORTED_LAB_REPORT'
    code, view = call(capsys, store, 'inspect-result', '--result-hash', imported['result_hash'])
    assert code == 0 and view['runtime_attestation'] == 'NOT_ESTABLISHED'


def test_cli_comparison_requires_declared_changed_build(tmp_path, capsys):
    store = Store(tmp_path / 'unused'); before = request(); after = copy.deepcopy(before)
    after['generation'] = 2; after['target']['build_artifact_hash'] = '9' * 64
    a = tmp_path / 'before.json'; b = tmp_path / 'after.json'
    a.write_bytes(canonical(before)); b.write_bytes(canonical(after))
    _, result = call(capsys, store, 'compare', '--before', str(a), '--after', str(b))
    assert result['status'] == 'NON_COMPARABLE'
    code, result = call(capsys, store, 'compare', '--before', str(a), '--after', str(b),
                        '--changed-target', 'build_artifact_hash')
    assert code == 0 and result['status'] == 'COMPARABLE'
    assert not store.root.exists()


def test_cli_private_bad_input_path_and_content_are_redacted(tmp_path, capsys):
    store = Store(tmp_path / 'cas'); private = tmp_path / 'private-secret-identity.json'
    code, result = call(capsys, store, 'validate', '--request', str(private))
    assert code == 2 and str(private) not in json.dumps(result)
    private.write_text('{"secret-password":1,"secret-password":2}')
    code, result = call(capsys, store, 'validate', '--request', str(private))
    assert code == 2 and 'secret-password' not in json.dumps(result)


def test_task_context_does_not_advertise_unimplemented_lab_execution(tmp_path):
    store = Store(tmp_path / 'cas')
    value = task_context.prepare_task_context(store, task_request())
    c = next((c for c in value['capabilities'] if c['id'] == 'experimental_runtime'), None)
    assert c == {'id': 'experimental_runtime', 'surface': 'UNSUPPORTED', 'readiness': 'BLOCKED',
                 'reason_code': 'LAB_RUNTIME_BACKEND_UNAVAILABLE',
                 'missing': ['registered_lab_execution', 'arena_typed_actions', 'capture_barrier'], 'evidence': []}
    assert not any(a['operation_id'].startswith('experiment.execute') for a in value['next_actions'])
