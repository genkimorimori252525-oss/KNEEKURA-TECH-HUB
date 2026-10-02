"""X1 CAS linkage is checked independently of any real runtime attestation."""
import copy
import importlib
import importlib.util
import json

import pytest

from kneekura_tech_hub.minecraft import index, storage
from kneekura_tech_hub.minecraft.experiment_contract import experiment_binding
from kneekura_tech_hub.minecraft.storage import ContractError, IntegrityError, Store, canonical, key_for
from test_minecraft_experiment_contract import request, result
from test_minecraft_storage import manifest


def api():
    name = 'kneekura_tech_hub.minecraft.experiment_bridge'
    assert importlib.util.find_spec(name) is not None, 'experiment CAS bridge is not implemented'
    return importlib.import_module(name)


def tree(root):
    return {str(p.relative_to(root)): p.read_bytes() for p in root.rglob('*') if p.is_file()}


@pytest.fixture
def prepared(tmp_path):
    (tmp_path / 'src').mkdir(); (tmp_path / 'src/Example.java').write_text('class Example {}')
    store = Store(tmp_path / 'cas'); p = storage.capture_profile(manifest(), tmp_path, store)
    idx = index.prepare_index(p, store)['index_snapshot_id']
    req = request()
    req['target'].update(profile_id=p['profile_id'], index_snapshot_id=idx,
        source_revision=p['manifest']['workspace_revision'], dirty_hash=p['manifest']['dirty_hash'],
        build_artifact_hash=store.put(b'fixture-build-not-a-runtime'),
        config_hash=store.put(b'fixture-config'), resource_hash=store.put(b'fixture-resources'))
    # This fixture's profile revision may be a short non-Git string. Pin an
    # actual Git-shaped revision at capture time instead of weakening contracts.
    if len(req['target']['source_revision']) != 40:
        m = manifest(); m['workspace_revision'] = 'b' * 40
        p = storage.capture_profile(m, tmp_path, store)
        idx = index.prepare_index(p, store)['index_snapshot_id']
        req['target'].update(profile_id=p['profile_id'], index_snapshot_id=idx,
                            source_revision=p['manifest']['workspace_revision'])
    return store, req


def reported(store, req):
    response = result(req)
    mapping = {}
    for row in response['evidence']:
        raw = ('fixture-' + row['kind']).encode()
        mapping[row['content_hash']] = store.put(raw)
        row.update(content_hash=mapping[row['content_hash']], size_bytes=len(raw))
    for row in response['assertions']:
        row['evidence_hashes'] = [mapping[h] for h in row['evidence_hashes']]
    for row in response['execution']['action_receipts']:
        row['evidence_hash'] = mapping[row['evidence_hash']]
    response['observations']['structured_summary'] = mapping[response['observations']['structured_summary']]
    snapshot = {'schemaVersion': 1, 'snapshotId': response['run_snapshot_id'],
        'debugSessionId': 'session-01', 'runId': 'run-01', 'processEpoch': 1,
        'createdAt': '2026-10-01T00:00:00.000Z', 'debugProfile': 'fixture',
        'workspaceId': 'fixture', 'worldName': 'fixture-only',
        'source': {'before': {}, 'ready': {}, 'stableDuringStartup': True},
        'observer': {'before': {}, 'ready': {}, 'stableDuringStartup': True,
                     'forgeBridgeSourceDir': 'fixture', 'observationSchemaVersion': 1},
        'build': {}, 'runtime': {'pid': 1, 'startedAtEpochMs': 1, 'ownership': {}, 'attestation': {}},
        'techHub': experiment_binding(req), 'snapshotHash': 'sha256:' + '4' * 64}
    response['run_snapshot_content_hash'] = store.put(canonical(snapshot))
    return response, snapshot


def test_prepare_freezes_validated_request_and_binding_in_existing_store(prepared):
    store, req = prepared
    saved = api().prepare_experiment(store, req)
    assert saved['request_hash'] == key_for(req)
    assert api().load_experiment(store, saved['request_hash']) == req
    assert store.json(saved['binding_hash']) == experiment_binding(req)
    assert saved['execution'] == 'NOT_RUN' and saved['runtime_attestation'] == 'NOT_ESTABLISHED'
    assert saved['binding_hash'] in store.pinned_hashes()


@pytest.mark.parametrize('field', ['profile_id','source_revision','dirty_hash','index_snapshot_id',
                                   'build_artifact_hash','config_hash','resource_hash'])
def test_prepare_rejects_unbacked_target_before_persistence(prepared, field):
    store, req = prepared; before = tree(store.root)
    req['target'][field] = '9' * (40 if field == 'source_revision' else 64)
    with pytest.raises((ContractError, OSError)): api().prepare_experiment(store, req)
    assert tree(store.root) == before


def test_import_preserves_report_and_never_claims_authenticated_runtime(prepared):
    store, req = prepared; saved = api().prepare_experiment(store, req)
    response, snapshot = reported(store, req)
    imported = api().import_experiment_result(store, saved['request_hash'], response)
    assert imported['runtime_attestation'] == 'NOT_ESTABLISHED'
    assert imported['provenance'] == 'IMPORTED_LAB_REPORT'
    assert imported['reported_execution'] == 'COMPLETED'
    retained = store.json(imported['result_hash'])
    assert retained['result'] == response
    assert retained['snapshot_content_hash'] == response['run_snapshot_content_hash']
    assert retained['lab_snapshot_hash'] == snapshot['snapshotHash']
    assert retained['lab_snapshot_hash_verification'] == 'NOT_ESTABLISHED'
    assert imported == api().import_experiment_result(store, saved['request_hash'], response)


@pytest.mark.parametrize('change', ['request_hash','snapshot_id','missing_binding','target','request_binding',
 'snapshot_hash','snapshot_schema','snapshot_epoch','evidence_size','missing_evidence','corrupt_evidence'])
def test_import_rejects_wrong_or_unreadable_linkage_without_new_persistence(prepared, change):
    store, req = prepared; h = api().prepare_experiment(store, req)['request_hash']
    response, snapshot = reported(store, req)
    if change == 'request_hash': response['request_hash'] = '8' * 64
    if change == 'snapshot_id': snapshot['snapshotId'] = 'other'
    if change == 'missing_binding': del snapshot['techHub']
    if change == 'target': snapshot['techHub']['target']['build_artifact_hash'] = '8' * 64
    if change == 'request_binding': snapshot['techHub']['request_hash'] = '8' * 64
    if change == 'snapshot_hash': snapshot['snapshotHash'] = 'unbound'
    if change == 'snapshot_schema': snapshot['schemaVersion'] = True
    if change == 'snapshot_epoch': snapshot['processEpoch'] = True
    if change == 'evidence_size': response['evidence'][0]['size_bytes'] += 1
    if change == 'missing_evidence': store.blob_path(response['evidence'][0]['content_hash']).unlink()
    if change == 'corrupt_evidence': store.blob_path(response['evidence'][0]['content_hash']).write_bytes(b'bad')
    response['run_snapshot_content_hash'] = store.put(canonical(snapshot))
    before = tree(store.root)
    with pytest.raises((ContractError, OSError)): api().import_experiment_result(store, h, response)
    assert tree(store.root) == before


def test_changed_dependency_reports_reverify_without_rewriting_historical_claim(prepared):
    store, req = prepared; h = api().prepare_experiment(store, req)['request_hash']
    response, _ = reported(store, req)
    imported = api().import_experiment_result(store, h, response)
    changed = dict(req['target'], config_hash='9' * 64)
    before = tree(store.root)
    view = api().inspect_experiment_result(store, imported['result_hash'], current_target=changed)
    assert view['currentness'] == 'REVERIFY_REQUIRED' and view['changed_target_fields'] == ['config_hash']
    assert view['reported_assertions'][0]['status'] == 'PASS'
    assert view['runtime_attestation'] == 'NOT_ESTABLISHED'
    assert tree(store.root) == before


def test_unknown_result_preserves_status_and_recommends_only_reconciliation(prepared):
    store, req = prepared; h = api().prepare_experiment(store, req)['request_hash']
    response, _ = reported(store, req)
    response['execution'].update(status='UNKNOWN', cleanup='UNKNOWN')
    for row in response['assertions']: row.update(status='UNKNOWN', evidence_hashes=[])
    imported = api().import_experiment_result(store, h, response)
    view = api().inspect_experiment_result(store, imported['result_hash'])
    assert view['next_operation'] == 'experiment.reconcile_unknown'
    assert view['reported_execution'] == 'UNKNOWN'
    assert view['currentness'] == 'NOT_CHECKED'


def test_inspect_revalidates_retained_record_instead_of_trusting_metadata(prepared):
    store, req = prepared; h = api().prepare_experiment(store, req)['request_hash']
    response, _ = reported(store, req)
    imported = api().import_experiment_result(store, h, response)
    record = store.json(imported['result_hash']); record['runtime_attestation'] = 'PASS'
    bad = store.put_json(record)
    with pytest.raises(ContractError): api().inspect_experiment_result(store, bad)


def test_snapshot_binding_bool_generation_is_not_integer_identity(prepared):
    store, req = prepared; h = api().prepare_experiment(store, req)['request_hash']
    response, snapshot = reported(store, req)
    snapshot['techHub']['generation'] = True
    response['run_snapshot_content_hash'] = store.put(canonical(snapshot))
    with pytest.raises(ContractError): api().import_experiment_result(store, h, response)


def test_declared_small_evidence_cannot_cause_unbounded_blob_read(prepared, monkeypatch):
    store, req = prepared; h = api().prepare_experiment(store, req)['request_hash']
    response, _ = reported(store, req)
    evidence = response['evidence'][0]
    # A real oversized file at a declared small identity must be rejected before
    # reading its complete contents through Store.read.
    with store.blob_path(evidence['content_hash']).open('wb') as stream:
        stream.truncate(16 * 1024 * 1024 + 1)
    original = store.read
    def bounded_only(key):
        assert key != evidence['content_hash'], 'unbounded Store.read on oversized evidence'
        return original(key)
    monkeypatch.setattr(store, 'read', bounded_only)
    with pytest.raises(ContractError): api().import_experiment_result(store, h, response)


def test_prepare_retains_exact_assertion_bytes_for_cross_language_registration(prepared):
    store, req = prepared
    saved = api().prepare_experiment(store, req)
    binding = store.json(saved['binding_hash'])
    assert store.read(binding['assertions_hash']) == canonical(req['assertions'])
    assert binding['assertions_hash'] in store.pinned_hashes()


def test_prepare_rejects_non_forge_target_even_with_self_consistent_profile(tmp_path):
    (tmp_path / 'src').mkdir(); (tmp_path / 'src/Example.java').write_text('class Example {}')
    store = Store(tmp_path / 'cas'); m = manifest(); m['workspace_revision'] = 'b' * 40; m['loader'] = 'fabric'; m['track'] = 'FRONTIER'
    p = storage.capture_profile(m, tmp_path, store); idx = index.prepare_index(p, store)['index_snapshot_id']
    req = request(); req['target'].update(profile_id=p['profile_id'], index_snapshot_id=idx,
        source_revision=p['manifest']['workspace_revision'], dirty_hash=p['manifest']['dirty_hash'],
        build_artifact_hash=store.put(b'build'), config_hash=store.put(b'config'), resource_hash=store.put(b'resources'))
    with pytest.raises(ContractError): api().prepare_experiment(store, req)


def test_import_record_boolean_schema_cannot_alias_integer_schema(prepared):
    store, req = prepared; h = api().prepare_experiment(store, req)['request_hash']
    response, _ = reported(store, req)
    imported = api().import_experiment_result(store, h, response)
    record = store.json(imported['result_hash']); record['schema_version'] = True
    with pytest.raises(ContractError): api().inspect_experiment_result(store, store.put_json(record))


def test_nonregular_cas_blob_is_rejected_without_blocking(tmp_path):
    import os
    import subprocess
    import sys
    if not hasattr(os, 'mkfifo'):
        pytest.skip('POSIX FIFO regression')
    store = Store(tmp_path / 'cas'); key = '8' * 64
    path = store.blob_path(key); path.parent.mkdir(parents=True); os.mkfifo(path)
    child = '''from kneekura_tech_hub.minecraft.experiment_bridge import _read_bounded
from kneekura_tech_hub.minecraft.storage import Store, ContractError
import sys
try:
    _read_bounded(Store(sys.argv[1]), sys.argv[2], 16)
except ContractError:
    raise SystemExit(0)
raise SystemExit(1)
'''
    try:
        completed = subprocess.run([sys.executable, '-c', child, str(store.root), key],
            capture_output=True, text=True, timeout=2,
            env={**os.environ, 'PYTHONPATH': str(__import__('pathlib').Path(__file__).resolve().parents[1] / 'src')})
    except subprocess.TimeoutExpired:
        pytest.fail('bounded CAS read blocked on a FIFO')
    assert completed.returncode == 0, completed.stderr
