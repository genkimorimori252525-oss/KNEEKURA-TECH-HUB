"""End-to-end CLI subprocess tests; no editor or Minecraft process involved."""
import copy
import json
import os
from pathlib import Path
import subprocess
import sys

import pytest

from kneekura_tech_hub.minecraft.storage import Store, capture_profile


def run(*args):
    env = dict(os.environ, PYTHONPATH=str(Path(__file__).resolve().parents[1] / 'src'))
    return subprocess.run([sys.executable, '-m', 'kneekura_tech_hub.minecraft.assets', *map(str, args)],
                          env=env, capture_output=True, text=True, timeout=5)


@pytest.fixture
def inputs(tmp_path):
    (tmp_path / 'workspace').mkdir()
    (tmp_path / 'workspace' / 'Item.java').write_text('class Item {}\n')
    spec = {
        'schema_version': 1, 'asset_id': 'kneekura:celestial_staff', 'asset_kind': 'java_item',
        'visual_brief': '金色の杖',
        'style': {'texture_size': [32, 32], 'palette': {'metal': '#d4af37'},
                  'pixel_art': True, 'shading': 'minecraft'},
        'reference_hashes': [], 'required_views': ['front', 'left', 'back'],
    }
    (tmp_path / 'spec.json').write_text(json.dumps(spec), encoding='utf-8')
    manifest = {
        'schema_version': 1, 'minecraft': '1.20.1', 'loader': 'forge', 'loader_version': '47.4.0',
        'java_major': 17, 'namespace': 'mojmap', 'physical_side': 'server', 'logical_side': 'server',
        'track': 'ANCHOR', 'workspace_revision': 'a'*40, 'dirty_hash': 'b'*64,
        'toolchain': {'java': '17'},
        'roots': [{'id': 'own', 'path': 'workspace', 'kind': 'directory', 'scope': 'runtime',
                   'role': 'source', 'namespace': 'mojmap', 'stage': 'workspace',
                   'classloader': 'unknown', 'track': 'ANCHOR'}],
    }
    store = Store(tmp_path / 'cas')
    profile = capture_profile(manifest, tmp_path, store)
    (tmp_path / 'profile.json').write_text(json.dumps(profile))
    index_id = store.put_json({'schema_version': 1, 'profile': profile, 'bytecode': {},
                               'bytecode_unresolved': [], 'provider': None})
    return tmp_path, store, profile, index_id


def test_check_is_usable_without_store_and_does_not_claim_asset_quality(inputs):
    path, _, _, _ = inputs
    result = run('check', '--spec', path / 'spec.json')
    assert result.returncode == 0, result.stderr
    report = json.loads(result.stdout)
    assert report['status'] == 'OK' and report['outcome'] == 'NOT_RUN'
    assert report['assertion_domain'] == 'asset_spec_validation'


def test_prepare_reads_existing_index_without_running_build_or_reindex(inputs):
    path, store, profile, index_id = inputs
    result = run('--store', store.root, 'prepare', '--index', index_id, '--spec', path / 'spec.json')
    assert result.returncode == 0, result.stderr
    report = json.loads(result.stdout)
    assert report['request']['index_snapshot_id'] == index_id
    assert report['request']['profile_id'] == profile['profile_id']
    assert store.json(report['request_hash']) == report['request']
    assert sorted(p.name for p in (path / 'workspace').iterdir()) == ['Item.java']


def test_prepare_accepts_profile_json(inputs):
    path, store, profile, _ = inputs
    result = run('--store', store.root, 'prepare', '--profile', path / 'profile.json', '--spec', path / 'spec.json')
    assert result.returncode == 0, result.stderr
    assert json.loads(result.stdout)['request']['profile_id'] == profile['profile_id']


def test_disabled_probe_exits_distinctly_without_creating_cache(inputs):
    path, _, _, _ = inputs
    reg = dict(schema_version=1, provider='sosadly/blockbench-mcp',
               revision='028cdd76589de2e2cea51bfd79495b50a3c7d1d2', port=8787,
               allow_probe=False, timeout_seconds=2, max_response_bytes=1048576)
    (path / 'registry.json').write_text(json.dumps(reg))
    result = run('--store', path / 'absent', 'probe', '--registry', path / 'registry.json')
    assert result.returncode == 3, result.stderr
    assert json.loads(result.stdout)['status'] == 'BLOCKED'
    assert not (path / 'absent').exists()


@pytest.mark.parametrize('case', ['no_store', 'unknown_flag', 'no_profile', 'both_profiles',
                                 'missing_file', 'duplicate_json', 'not_index', 'stale_profile'])
def test_invalid_input_is_json_error_not_traceback(inputs, case):
    path, store, profile, index_id = inputs
    args = ['--store', store.root, 'prepare', '--index', index_id, '--spec', path / 'spec.json']
    if case == 'no_store': args = args[2:]
    if case == 'unknown_flag': args += ['--allow-script']
    if case == 'no_profile': args = ['--store', store.root, 'prepare', '--spec', path / 'spec.json']
    if case == 'both_profiles': args += ['--profile', path / 'profile.json']
    if case == 'missing_file': (path / 'spec.json').unlink()
    if case == 'duplicate_json': (path / 'spec.json').write_text('{"x":1,"x":2}')
    if case == 'not_index': args[4] = store.put_json([])
    if case == 'stale_profile':
        p = copy.deepcopy(profile); p['manifest']['loader_version'] = '47.4.6'
        (path / 'profile.json').write_text(json.dumps(p))
        args = ['--store', store.root, 'prepare', '--profile', path / 'profile.json', '--spec', path / 'spec.json']
    result = run(*args)
    assert result.returncode == 2, result.stderr
    assert json.loads(result.stdout)['status'] == 'ERROR'
    assert 'Traceback' not in result.stderr


def test_help_documents_only_preparation_and_probe():
    result = run('--help')
    assert result.returncode == 0, result.stderr
    assert 'prepare' in result.stdout and 'probe' in result.stdout
    assert 'execute_script' not in result.stdout
