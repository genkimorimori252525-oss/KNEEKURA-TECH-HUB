"""Contract tests use real files; no downloaded code or Minecraft execution."""
import copy
import importlib
import json
import zipfile
from pathlib import Path

import pytest


def api():
    return importlib.import_module('kneekura_tech_hub.minecraft.storage')


def manifest(path='src', kind='directory'):
    return {
        'schema_version': 1, 'minecraft': '1.20.1', 'loader': 'forge',
        'loader_version': '47.4.0', 'java_major': 17, 'namespace': 'mojmap',
        'physical_side': 'server', 'logical_side': 'server', 'track': 'ANCHOR',
        'workspace_revision': 'a' * 40, 'dirty_hash': 'b' * 64,
        'toolchain': {'gradle': '8.8', 'forgegradle': '6.0.24'},
        'roots': [{'id': 'own', 'path': path, 'kind': kind, 'scope': 'runtime',
                   'role': 'source', 'namespace': 'mojmap', 'stage': 'workspace',
                   'classloader': 'unknown', 'track': 'ANCHOR'}],
    }


@pytest.fixture
def setup(tmp_path):
    src = tmp_path / 'src'
    src.mkdir()
    (src / 'Example.java').write_text('class Example { int damage = 1; }\n')
    return tmp_path


def test_capture_pins_original_and_does_not_mutate_manifest(setup):
    s = api(); m = manifest(); original = copy.deepcopy(m)
    store = s.Store(setup / 'cache')
    p = s.capture_profile(m, setup, store)
    assert m == original
    assert p['coverage']['complete'] is True
    d = p['documents'][0]
    (setup / 'src/Example.java').write_text('class Changed {}')
    assert b'damage' in store.read(d['content_hash'])
    assert p['profile_id'] == p['profile_hash']
    assert d['source_binary_match'] == 'UNRESOLVED'
    assert p['resolution'] == 'CAPTURED_NOT_RUNTIME_VERIFIED'


@pytest.mark.parametrize('change', ['version', 'classpath', 'bytes', 'config', 'namespace'])
def test_input_changes_invalidate_profile(setup, change):
    s = api(); m = manifest(); store = s.Store(setup / 'cache')
    p = s.capture_profile(m, setup, store)
    if change == 'version': m['loader_version'] = '47.4.6'
    if change == 'namespace': m['namespace'] = 'srg'
    if change == 'classpath':
        m['roots'].append(dict(m['roots'][0], id='duplicate'))
        m['roots'].reverse()
    if change == 'bytes': (setup / 'src/Example.java').write_text('class Example { int damage=2; }')
    if change == 'config': (setup / 'src/config.toml').write_text('damage=2\n')
    assert s.capture_profile(m, setup, store)['profile_id'] != p['profile_id']


def test_unknown_version_never_becomes_resolved(setup):
    s = api(); m = manifest(); m['loader_version'] = '47.4.x'
    p = s.capture_profile(m, setup, s.Store(setup / 'cache'))
    assert p['identity_status'] == 'UNKNOWN'
    assert any('loader_version' in x for x in p['warnings'])


def test_buildscript_scope_and_namespace_not_merged(setup):
    s = api(); m = manifest(); m['roots'][0]['scope'] = 'buildscript'
    m['roots'][0]['namespace'] = 'official'
    m['namespace_aliases'] = {'official': 'mojmap'}
    p = s.capture_profile(m, setup, s.Store(setup / 'cache'))
    assert p['documents'][0]['scope'] == 'buildscript'
    assert p['documents'][0]['namespace'] == 'mojmap'
    assert p['manifest']['namespace_aliases'] == m['namespace_aliases']


def test_missing_root_is_partial_and_present_root_retained(setup):
    s = api(); m = manifest()
    m['roots'].append(dict(m['roots'][0], id='missing', path='does-not-exist'))
    p = s.capture_profile(m, setup, s.Store(setup / 'cache'))
    assert len(p['documents']) == 1
    assert not p['coverage']['complete']
    assert p['coverage']['unresolved_roots'][0]['root_id'] == 'missing'


@pytest.mark.parametrize('entry', ['../evil.java', '/evil.java', 'C:/evil.java', 'a\\b.java', 'a/./b.java'])
def test_zip_paths_rejected_without_outside_write(tmp_path, entry):
    s = api(); jar = tmp_path / 'bad.jar'
    with zipfile.ZipFile(jar, 'w') as z: z.writestr(entry, 'bad')
    p = s.capture_profile(manifest('bad.jar', 'jar'), tmp_path, s.Store(tmp_path / 'cache'))
    assert not p['documents']
    assert not p['coverage']['complete']
    assert not (tmp_path / 'evil.java').exists()


def test_archive_size_limits_are_fail_closed(tmp_path):
    s = api()
    with zipfile.ZipFile(tmp_path / 'big.jar', 'w', zipfile.ZIP_DEFLATED) as z:
        z.writestr('big.txt', 'a' * 20000)
    p = s.capture_profile(manifest('big.jar', 'jar'), tmp_path, s.Store(tmp_path / 'cache'),
                          limits=s.Limits(max_file_bytes=1000))
    assert not p['coverage']['complete']
    assert not p['documents']


def test_archive_duplicate_paths_are_ambiguous_input(tmp_path):
    s = api()
    with zipfile.ZipFile(tmp_path / 'dupe.jar', 'w') as z:
        z.writestr('a.java', 'a')
        with pytest.warns(UserWarning): z.writestr('a.java', 'b')
    p = s.capture_profile(manifest('dupe.jar', 'jar'), tmp_path, s.Store(tmp_path / 'cache'))
    assert not p['coverage']['complete']


def test_symlinks_do_not_read_outside_scope(setup):
    s = api(); (setup / 'secret').write_text('secret')
    (setup / 'src/link.txt').symlink_to(setup / 'secret')
    p = s.capture_profile(manifest(), setup, s.Store(setup / 'cache'))
    assert not p['coverage']['complete']
    assert all(d['path'] != 'link.txt' for d in p['documents'])


def test_store_corruption_is_not_silently_replaced(tmp_path):
    s = api(); store = s.Store(tmp_path / 'cache'); key = store.put(b'original')
    store.blob_path(key).write_bytes(b'changed')
    with pytest.raises(s.IntegrityError): store.read(key)
    with pytest.raises(s.IntegrityError): store.put(b'original')


def test_passive_read_never_creates_store(tmp_path):
    s = api(); store = s.Store(tmp_path / 'missing')
    with pytest.raises(s.ArtifactUnavailable): store.read('0' * 64)
    assert not store.root.exists()


def test_pin_is_durable_and_original_stays_readable(tmp_path):
    s = api(); store = s.Store(tmp_path / 'cache'); key = store.put(b'evidence')
    store.pin(key, 'claim:one')
    assert key in store.pinned_hashes()
    assert s.Store(store.root).read(key) == b'evidence'


def test_duplicate_root_ids_and_invalid_scope_rejected(setup):
    s = api(); m = manifest(); m['roots'].append(dict(m['roots'][0]))
    with pytest.raises(s.ContractError): s.capture_profile(m, setup, s.Store(setup / 'cache'))
    m = manifest(); m['roots'][0]['scope'] = 'anything'
    with pytest.raises(s.ContractError): s.capture_profile(m, setup, s.Store(setup / 'cache'))


def test_outer_jar_remains_addressable_after_original_is_deleted(tmp_path):
    s = api(); jar = tmp_path / 'source.jar'
    with zipfile.ZipFile(jar, 'w') as z: z.writestr('A.java', 'class A {}')
    original = jar.read_bytes(); store = s.Store(tmp_path / 'cache')
    profile = s.capture_profile(manifest('source.jar', 'jar'), tmp_path, store)
    jar.unlink()
    assert store.read(profile['roots'][0]['artifact_hash']) == original


def test_directory_artifact_hash_resolves_to_captured_inventory(setup):
    s = api(); store = s.Store(setup / 'cache')
    profile = s.capture_profile(manifest(), setup, store)
    inventory = store.json(profile['roots'][0]['artifact_hash'])
    assert inventory == [{'path': 'Example.java', 'hash': profile['documents'][0]['content_hash']}]


def test_capture_cannot_use_cache_itself_as_input(tmp_path):
    s = api(); store = s.Store(tmp_path / 'cache'); store.put(b'not input')
    profile = s.capture_profile(manifest('cache'), tmp_path, store)
    assert not profile['coverage']['complete']
    assert profile['documents'] == []


def test_cas_write_cannot_follow_parent_symlink(tmp_path):
    s = api(); store = s.Store(tmp_path / 'cache'); outside = tmp_path / 'outside'
    outside.mkdir(); (store.root / 'blobs').mkdir(parents=True)
    data = b'evidence'; key = s.digest(data)
    (store.root / 'blobs' / key[:2]).symlink_to(outside, target_is_directory=True)
    with pytest.raises(s.IntegrityError): store.put(data)
    assert not list(outside.iterdir())


@pytest.mark.parametrize('mutation', ['root_is_integer', 'schema_bool', 'root_string_too_long'])
def test_malformed_manifest_has_contract_error(setup, mutation):
    s = api(); m = manifest()
    if mutation == 'root_is_integer': m['roots'] = [7]
    if mutation == 'schema_bool': m['schema_version'] = True
    if mutation == 'root_string_too_long': m['roots'][0]['id'] = 'x' * 5000
    with pytest.raises(s.ContractError): s.capture_profile(m, setup, s.Store(setup / 'cache'))


def test_unavailable_root_does_not_claim_fully_pinned_identity(setup):
    s = api(); m = manifest(); m['roots'][0]['path'] = 'absent'
    profile = s.capture_profile(m, setup, s.Store(setup / 'cache'))
    assert profile['identity_status'] == 'UNKNOWN'


def test_unreadable_directory_is_reported_in_coverage(setup, monkeypatch):
    s = api(); hidden = setup / 'src/hidden'; hidden.mkdir()
    (hidden / 'Unseen.java').write_text('class Unseen {}')
    original = s.os.scandir
    def denied(path):
        if Path(path) == hidden: raise PermissionError('fixture directory unreadable')
        return original(path)
    monkeypatch.setattr(s.os, 'scandir', denied)
    profile = s.capture_profile(manifest(), setup, s.Store(setup / 'cache'))
    assert not profile['coverage']['complete']
    assert profile['documents']  # Keep unrelated readable files.
