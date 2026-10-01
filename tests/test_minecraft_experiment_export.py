"""LAB private transport imports a bounded complete inventory into existing CAS."""
import copy
import importlib
import json
from pathlib import Path

import pytest

from kneekura_tech_hub.minecraft import experiment_bridge as bridge
from kneekura_tech_hub.minecraft.storage import ContractError, canonical, digest
from test_minecraft_experiment_bridge import prepared, reported, tree
from test_minecraft_experiment_control import control


def api():
    spec = importlib.util.find_spec('kneekura_tech_hub.minecraft.experiment_export')
    assert spec is not None, 'bounded private export importer is not implemented'
    return importlib.import_module(spec.name)


@pytest.fixture
def exported(control):
    store, req, registry, owner = control
    request_hash = owner['run']['identity']['requestHash']
    report, snapshot = reported(store, req)
    report['execution'].update(status='UNKNOWN', cleanup='UNKNOWN')
    for row in report['assertions']: row.update(status='INCONCLUSIVE', evidence_hashes=[])
    raw = canonical(report); result_hash = digest(raw)
    blob_data = {row['content_hash']:store.read(row['content_hash']) for row in report['evidence']}
    blob_data[report['run_snapshot_content_hash']] = canonical(snapshot)
    for h in blob_data: store.blob_path(h).unlink()
    blob_data[result_hash] = raw
    manifest = {'schema_version':1,'kind':'lab_experiment_export','request_hash':request_hash,
        'result_hash':result_hash,'run_snapshot_content_hash':report['run_snapshot_content_hash'],
        'contains_private_evidence':True,'provenance':'FINALIZED_LAB_EVIDENCE_REPORT',
        'runtime_attestation':'NOT_ESTABLISHED','blobs':[
            {'content_hash':h,'size_bytes':len(b),'classification':'PRIVATE_EXPERIMENT_RESULT' if h == result_hash
             else 'PRIVATE_RUN_SNAPSHOT' if h == report['run_snapshot_content_hash'] else 'PRIVATE_RETAINED_EVIDENCE'}
            for h,b in blob_data.items()]}
    root = Path(owner['inputRoot'])/'exports'/request_hash
    (root/'blobs').mkdir(parents=True); (root/'manifests').mkdir()
    for h,b in blob_data.items(): (root/'blobs'/h).write_bytes(b)
    return store, registry, request_hash, report, manifest, root


def save_manifest(root, manifest):
    raw = canonical(manifest); h = digest(raw)
    (root/'manifests'/(h+'.json')).write_bytes(raw)
    return h


def test_import_verifies_and_retains_whole_private_inventory(exported):
    store, registry, request_hash, report, manifest, root = exported
    h = save_manifest(root, manifest)
    value = api().import_export(store, registry, request_hash, h)
    assert value['runtime_attestation'] == 'NOT_ESTABLISHED'
    assert value['provenance'] == 'IMPORTED_LAB_REPORT'
    assert value['export_provenance'] == 'FINALIZED_LAB_EVIDENCE_REPORT'
    assert value['export_manifest_hash'] == h
    assert value['reported_cleanup'] == 'UNKNOWN'
    assert 'private' not in json.dumps(value).lower()
    assert str(root) not in json.dumps(value)
    assert store.json(value['result_hash'])['result'] == report
    assert {h, *(row['content_hash'] for row in manifest['blobs'])} <= store.pinned_hashes()
    assert api().import_export(store, registry, request_hash, h) == value


@pytest.mark.parametrize('change', ['extra_field','bool_version','false_privacy','wrong_provenance','attestation',
    'foreign_request','missing','duplicate','extra_blob','classification','size','corrupt','symlink','ancestor_symlink',
    'snapshot_oversized','result_oversized','inventory_oversized','unknown_classification','result_path'])
def test_invalid_export_fails_before_cas_persistence(exported, change):
    store, registry, request_hash, report, manifest, root = exported
    if change == 'extra_field': manifest['source_path'] = '/private/unfollowable'
    if change == 'bool_version': manifest['schema_version'] = True
    if change == 'false_privacy': manifest['contains_private_evidence'] = False
    if change == 'wrong_provenance': manifest['provenance'] = 'CALLER_JSON'
    if change == 'attestation': manifest['runtime_attestation'] = 'PASS'
    if change == 'foreign_request': manifest['request_hash'] = 'f'*64
    if change == 'missing': manifest['blobs'].pop(0)
    if change == 'duplicate': manifest['blobs'].append(copy.deepcopy(manifest['blobs'][0]))
    if change == 'extra_blob':
        raw = b'unreferenced'; h = digest(raw); (root/'blobs'/h).write_bytes(raw)
        manifest['blobs'].append({'content_hash':h,'size_bytes':len(raw),'classification':'PRIVATE_RETAINED_EVIDENCE'})
    if change == 'classification': manifest['blobs'][0]['classification'] = 'PRIVATE_RUN_SNAPSHOT'
    if change == 'size': manifest['blobs'][0]['size_bytes'] += 1
    if change == 'corrupt': (root/'blobs'/manifest['blobs'][0]['content_hash']).write_bytes(b'changed')
    if change == 'symlink':
        file = root/'blobs'/manifest['blobs'][0]['content_hash']; original = file.with_suffix('.original')
        file.rename(original); file.symlink_to(original.name)
    if change == 'ancestor_symlink':
        original = root/'blobs-original'; (root/'blobs').rename(original); (root/'blobs').symlink_to(original.name)
    if change in ('snapshot_oversized','result_oversized'):
        h = manifest['run_snapshot_content_hash'] if change == 'snapshot_oversized' else manifest['result_hash']
        size = (2 if change == 'snapshot_oversized' else 1)*1024*1024+1
        next(row for row in manifest['blobs'] if row['content_hash']==h)['size_bytes'] = size
        with (root/'blobs'/h).open('wb') as f: f.truncate(size)
    if change == 'inventory_oversized':
        manifest['blobs'] = [{'content_hash':f'{i:064x}','size_bytes':16*1024*1024,
                              'classification':'PRIVATE_RETAINED_EVIDENCE'} for i in range(5)]
    if change == 'unknown_classification': manifest['blobs'][0]['classification'] = 'PUBLIC'
    if change == 'result_path': manifest['result_hash'] = '../secret'
    h = save_manifest(root, manifest); before = tree(store.root)
    with pytest.raises((ContractError, OSError)):
        api().import_export(store, registry, request_hash, h)
    assert tree(store.root) == before


def replace_blob(root, manifest, old_hash, value):
    raw = canonical(value); h = digest(raw); (root/'blobs'/h).write_bytes(raw)
    row = next(row for row in manifest['blobs'] if row['content_hash']==old_hash)
    row.update(content_hash=h, size_bytes=len(raw))
    return h


@pytest.mark.parametrize('change', ['request','snapshot_binding','evidence_size','evidence_kind','unknown_field'])
def test_invalid_report_or_snapshot_never_partially_imports(exported, change):
    store, registry, request_hash, report, manifest, root = exported
    if change == 'request': report['request_hash'] = '0'*64
    if change == 'snapshot_binding':
        snapshot = json.loads((root/'blobs'/manifest['run_snapshot_content_hash']).read_bytes())
        snapshot['techHub']['request_hash'] = '0'*64
        h = replace_blob(root, manifest, manifest['run_snapshot_content_hash'], snapshot)
        report['run_snapshot_content_hash'] = h; manifest['run_snapshot_content_hash'] = h
    if change == 'evidence_size': report['evidence'][0]['size_bytes'] += 1
    if change == 'evidence_kind': report['evidence'][0]['kind'] = 'invalid'
    if change == 'unknown_field': report['private_path'] = '/private/leak'
    manifest['result_hash'] = replace_blob(root, manifest, manifest['result_hash'], report)
    h = save_manifest(root, manifest); before = tree(store.root)
    with pytest.raises(ContractError): api().import_export(store, registry, request_hash, h)
    assert tree(store.root) == before


def test_import_never_spawns_and_validates_manifest_hash(exported, monkeypatch):
    import subprocess
    store, registry, request_hash, _, manifest, root = exported
    h = save_manifest(root, manifest)
    monkeypatch.setattr(subprocess, 'Popen', lambda *a, **k: pytest.fail('import spawned'))
    (root/'manifests'/(h+'.json')).write_bytes(b'{}')
    before = tree(store.root)
    with pytest.raises(ContractError): api().import_export(store, registry, request_hash, h)
    assert tree(store.root) == before


@pytest.mark.parametrize('field', ['runId','debugSessionId','snapshotId','processEpoch'])
def test_export_from_different_run_of_same_request_fails_closed(exported, field):
    store, registry, request_hash, report, manifest, root = exported
    old = manifest['run_snapshot_content_hash']
    snapshot = json.loads((root/'blobs'/old).read_bytes())
    snapshot[field] = 2 if field == 'processEpoch' else 'other-run'
    if field == 'snapshotId': report['run_snapshot_id'] = snapshot[field]
    report['run_snapshot_content_hash'] = replace_blob(root, manifest, old, snapshot)
    manifest['run_snapshot_content_hash'] = report['run_snapshot_content_hash']
    manifest['result_hash'] = replace_blob(root, manifest, manifest['result_hash'], report)
    h = save_manifest(root, manifest); before = tree(store.root)
    with pytest.raises(ContractError): api().import_export(store, registry, request_hash, h)
    assert tree(store.root) == before


def test_import_record_collision_checked_before_any_new_cas_bytes(exported):
    store, registry, request_hash, report, manifest, root = exported
    snapshot = json.loads((root/'blobs'/manifest['run_snapshot_content_hash']).read_bytes())
    record_hash = digest(canonical(bridge._record(request_hash, report, snapshot)))
    collision = store.blob_path(record_hash)
    collision.parent.mkdir(parents=True, exist_ok=True)
    collision.write_bytes(b'corrupt prior retained import record')
    manifest_hash = save_manifest(root, manifest)
    before = tree(store.root)
    with pytest.raises(ContractError):
        api().import_export(store, registry, request_hash, manifest_hash)
    assert tree(store.root) == before, 'new export blobs persisted before detecting corrupt derived import record'
