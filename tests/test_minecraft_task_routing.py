"""Readiness is local prerequisite information, never a launch or live attestation."""
import copy
import importlib
import json
import socket
import shutil
import subprocess
from pathlib import Path

import pytest

from kneekura_tech_hub.minecraft import execution, index, input_route, native_input, runtime, storage, task_context, verification
from kneekura_tech_hub.minecraft.storage import Store, canonical, key_for
from kneekura_tech_hub.minecraft.workspace import file_hash, workspace_fingerprint
from test_minecraft_storage import manifest
from test_minecraft_index import class_profile
from test_minecraft_blockbench import registry as blockbench_registry
from test_minecraft_dedicated_identity import dedicated_contract
from test_minecraft_task_context import task_request
from test_minecraft_verification import contract


IDS = ['source_search', 'bytecode_inspect', 'mappings', 'failure_history', 'core_context',
       'blockbench_asset', 'forge_build', 'gametest', 'server_observation', 'client_observation', 'native_input', 'experimental_runtime']


def api():
    try:
        return importlib.import_module('kneekura_tech_hub.minecraft.task_routing')
    except ImportError:
        pytest.fail('Minecraft task capability routing is not implemented')


def capabilities(store, *, request=None, **kwargs):
    inputs = task_context.load_task_inputs(store, **kwargs)
    evidence = task_context.summarize_evidence(store, inputs)
    result = api().evaluate_capabilities(store, request or task_request(), inputs, evidence)
    assert [c['id'] for c in result] == IDS
    assert all(set(c) == {'id', 'surface', 'readiness', 'reason_code', 'missing', 'evidence'} for c in result)
    assert all(c['surface'] in ('IMPLEMENTED', 'UNSUPPORTED') and
               c['readiness'] in ('READY', 'NOT_CONFIGURED', 'BLOCKED', 'UNKNOWN') for c in result)
    assert all(isinstance(c['missing'], list) and isinstance(c['evidence'], list) for c in result)
    assert all(storage.valid_hash(h) == h for c in result for h in c['evidence'])
    return {c['id']: c for c in result}


@pytest.fixture
def prepared(tmp_path):
    root = tmp_path / 'private-project'; root.mkdir()
    (root / 'src').mkdir(); (root / 'src/Example.java').write_text('class Example {}\n')
    wrapper = root / 'gradlew'; wrapper.write_text('#!/bin/sh\nexit 0\n'); wrapper.chmod(0o700)
    store = Store(tmp_path / 'private-cas')
    m = manifest(); m.update(workspace=str(root), dirty_hash=workspace_fingerprint(root))
    profile = storage.capture_profile(m, root, store)
    idx = index.prepare_index(profile, store)['index_snapshot_id']
    artifact = root / 'build/classes'; artifact.mkdir(parents=True)
    (artifact / 'Example.class').write_bytes(b'class-identity-fixture-not-executed')
    artifact_hash = store.put_json([{'path': 'Example.class', 'hash': store.put((artifact / 'Example.class').read_bytes())}])
    receipt = {'schema_version': 1, 'request': {'kind': 'compile', 'workspace': str(root)},
               'source_generation': m['dirty_hash'], 'source_generation_after': m['dirty_hash'],
               'outputs': [{'content_hash': artifact_hash}], 'result': {'outcome': 'PASS'}}
    registry = {'workspace': str(root), 'allow_gradle': True, 'wrapper_sha256': file_hash(wrapper),
                'allowed_kinds': ['compile', 'gametest', 'client', 'server'], 'remaining_launches': 1,
                'launch_budget_id': 'explicit-one-launch', 'build_artifact': 'build/classes',
                'build_receipt_hash': store.put_json(receipt), 'runtime_config_files': []}
    template = root / 'templates/empty'; template.mkdir(parents=True)
    registry['world_templates'] = [str(template)]
    world = execution.prepare_world(store, registry, template=str(template), request_id='fresh-world')
    return store, idx, registry, world, root


def client_session(prepared):
    store, idx, registry, world, root = prepared
    profile = index._load(store, idx)['profile']
    c = contract(); c.update(profile_id=profile['profile_id'], index_snapshot_id=idx,
        dirty_hash=profile['manifest']['dirty_hash'], physical_side='client',
        build_artifact_hash=store.json(registry['build_receipt_hash'])['outputs'][0]['content_hash'],
        world_id=world['world_id'], world_template_hash=world['world_template_hash'],
        config_hash=key_for([]), adapter_id=runtime.ADAPTER_ID, adapter_version=runtime.ADAPTER_VERSION)
    directory = root / 'retained-session'; directory.mkdir()
    value = {'contract': c, 'token': 'f' * 64, 'directory': str(directory),
             'endpoint_path': str(directory / 'endpoint.json')}
    path = directory / 'session.json'; path.write_bytes(canonical(value)); path.chmod(0o600)
    session = runtime.load_session(path)
    input_registry = {'schema_version': 1, 'backend': native_input.BACKEND_ID, 'enabled': True,
        'session_file': str(path), 'display': ':0', 'allowed_controls': ['mouse:right'], 'timeout_seconds': 5}
    return session, input_registry


def test_capabilities_missing_index_exposes_environment_capture(tmp_path):
    store = Store(tmp_path / 'absent')
    out = capabilities(store)
    for name in ('source_search', 'bytecode_inspect'):
        assert out[name]['readiness'] == 'NOT_CONFIGURED'
        assert out[name]['reason_code'] == 'PROFILE_MISSING'
        assert 'environment_capture' in out[name]['missing']
    assert not store.root.exists()


def test_capabilities_exact_index_has_source_search_but_no_prepared_bytecode(prepared):
    store, idx, _, _, _ = prepared
    out = capabilities(store, index_id=idx)
    assert out['source_search']['readiness'] == 'READY'
    assert out['source_search']['evidence'] == [idx]
    assert out['bytecode_inspect']['readiness'] == 'UNKNOWN'
    assert out['bytecode_inspect']['reason_code'] == 'EVIDENCE_SCOPE_INSUFFICIENT'


def test_capabilities_create_asset_needs_explicit_blockbench_registry(prepared):
    store, idx, _, _, _ = prepared
    c = capabilities(store, index_id=idx, request=task_request(intent='create_asset'))['blockbench_asset']
    assert (c['readiness'], c['reason_code']) == ('NOT_CONFIGURED', 'PROVIDER_NOT_REGISTERED')


def test_capabilities_successful_same_source_build_and_owned_world_allow_gametest_preparation(prepared):
    store, idx, reg, world, _ = prepared
    out = capabilities(store, index_id=idx, run_registry=reg, world=world['world'])
    assert out['forge_build']['readiness'] == 'READY'
    assert out['gametest']['readiness'] == 'READY'
    assert reg['build_receipt_hash'] in out['gametest']['evidence']


@pytest.mark.parametrize('kind,affected', [('native-input-receipt', ['native_input']),
    ('gametest', ['gametest', 'server_observation']), ('client', ['client_observation', 'native_input']),
    ('compile', ['forge_build', 'gametest']), ('run-receipt', ['gametest', 'server_observation', 'client_observation'])])
def test_capabilities_unknown_receipts_remain_unknown(prepared, kind, affected):
    store, idx, reg, world, _ = prepared
    h = store.put_json({'kind': kind, 'result': {'input_status': 'UNKNOWN'} if kind == 'native-input-receipt' else {'outcome': 'UNKNOWN'}})
    out = capabilities(store, index_id=idx, run_registry=reg, world=world['world'], evidence_hashes=(h,))
    for name in affected:
        assert (out[name]['readiness'], out[name]['reason_code']) == ('UNKNOWN', 'SESSION_UNKNOWN_COMPLETION')
        assert h in out[name]['evidence']


def test_capabilities_linux_registry_and_matching_session_still_require_live_probe(prepared):
    store, idx, reg, _, _ = prepared
    session, input_registry = client_session(prepared)
    out = capabilities(store, index_id=idx, session=session, input_registry=input_registry)
    for name in ('client_observation', 'native_input'):
        assert (out[name]['readiness'], out[name]['reason_code']) == ('UNKNOWN', 'LIVE_STATE_NOT_PROBED')
    assert out['server_observation']['readiness'] != 'READY'


@pytest.mark.parametrize('backend', ['windows', 'windows-send-input-v1'])
def test_capabilities_explicit_windows_backend_unsupported_even_on_linux(prepared, backend):
    store, idx, _, _, _ = prepared
    out = capabilities(store, index_id=idx, input_registry={'backend': backend})
    c = out['native_input']
    assert (c['surface'], c['readiness'], c['reason_code']) == ('UNSUPPORTED', 'BLOCKED', 'WINDOWS_INPUT_UNSUPPORTED')


def test_capabilities_windows_host_is_unsupported(tmp_path, monkeypatch):
    module = api(); monkeypatch.setattr(module.sys, 'platform', 'win32')
    c = capabilities(Store(tmp_path / 'store'))['native_input']
    assert (c['surface'], c['readiness'], c['reason_code']) == ('UNSUPPORTED', 'BLOCKED', 'WINDOWS_INPUT_UNSUPPORTED')


def test_capabilities_mapping_and_history_require_recognized_explicit_pointers(prepared):
    store, idx, _, _, _ = prepared
    mapping = store.put_json({'kind': 'mapping-table', 'format': 'tiny', 'text_hash': 'c'*64})
    history = store.put_json({'format': 'kneekura.failure-history.v1', 'private_cases': ['secret']})
    out = capabilities(store, index_id=idx, evidence_hashes=(mapping, history))
    assert out['mappings']['readiness'] == out['failure_history']['readiness'] == 'READY'
    assert out['mappings']['evidence'] == [mapping]
    assert out['failure_history']['evidence'] == [history]
    without = capabilities(store, index_id=idx)
    assert without['mappings']['reason_code'] == 'MAPPING_NOT_CONFIGURED'
    assert without['failure_history']['readiness'] == 'NOT_CONFIGURED'


@pytest.mark.parametrize('configured', [False, True])
def test_capabilities_core_only_uses_strict_explicit_flag(tmp_path, monkeypatch, configured):
    monkeypatch.setenv('DATABASE_URL', 'postgresql://private-secret@localhost/core')
    monkeypatch.setenv('KNEEKURA_CORE_CONFIGURED', 'true')
    c = capabilities(Store(tmp_path / 'store'), core_configured=configured)['core_context']
    assert c['readiness'] == ('UNKNOWN' if configured else 'NOT_CONFIGURED')
    assert 'private-secret' not in json.dumps(c)


@pytest.mark.parametrize('damage', ['denied', 'kind', 'wrapper', 'unowned_world', 'changed_world',
    'used_world', 'budget_zero', 'budget_exhausted', 'lock', 'missing_receipt', 'wrong_receipt',
    'changed_artifact', 'changed_source', 'client_directory', 'wrong_runtime_role'])
def test_capabilities_gametest_fails_closed_on_existing_prerequisite_guards(prepared, damage):
    store, idx, reg, world, root = prepared
    kwargs = dict(index_id=idx, run_registry=reg, world=world['world'])
    if damage == 'denied': reg['allow_gradle'] = False
    elif damage == 'kind': reg['allowed_kinds'] = ['compile']
    elif damage == 'wrapper': (root / 'gradlew').write_text('private tampered wrapper')
    elif damage == 'unowned_world': kwargs['world'] = str(root / 'templates/empty')
    elif damage == 'changed_world': (Path(world['world']) / 'new-file').write_text('changed')
    elif damage == 'used_world':
        path = Path(world['directory']) / '.kneekura-run.json'
        marker = json.loads(path.read_bytes()); marker['fresh'] = False; path.write_bytes(canonical(marker))
    elif damage == 'budget_zero': reg['remaining_launches'] = 0
    elif damage == 'budget_exhausted':
        path = store.root / 'launches' / key_for({'workspace': str(root), 'budget': reg['launch_budget_id']})
        path.mkdir(parents=True); (path / 'used.json').write_text('{}')
    elif damage == 'lock': (store.root / ('workspace-' + key_for(str(root)) + '.lock')).write_text('uncertain')
    elif damage == 'missing_receipt': reg.pop('build_receipt_hash')
    elif damage == 'wrong_receipt':
        receipt = store.json(reg['build_receipt_hash']); receipt['source_generation_after'] = '0'*64
        reg['build_receipt_hash'] = store.put_json(receipt)
    elif damage == 'changed_artifact': (root / 'build/classes/Example.class').write_bytes(b'changed')
    elif damage == 'changed_source': (root / 'src/Example.java').write_text('class Changed {}')
    elif damage == 'client_directory': kwargs['run_directory'] = world['directory']
    elif damage == 'wrong_runtime_role': reg['runtime_role'] = 'dedicated_server'
    out = capabilities(store, **kwargs)
    assert out['gametest']['readiness'] in ('BLOCKED', 'UNKNOWN', 'NOT_CONFIGURED')
    assert str(root) not in json.dumps(out) and 'tampered wrapper' not in json.dumps(out)
    if damage in ('denied', 'wrapper', 'lock'):
        assert out['forge_build']['readiness'] != 'READY'
    if damage == 'changed_source': assert out['gametest']['reason_code'] == 'INDEX_STALE'


def test_capabilities_validation_plan_argv_is_not_readiness_authority(prepared):
    store, idx, reg, world, _ = prepared
    reg.update(allow_gradle=False, test_worlds=[world['world']])
    assert verification.validation_plan('gametest', reg, world=world['world'])['argv']
    out = capabilities(store, index_id=idx, run_registry=reg, world=world['world'])
    assert out['gametest']['readiness'] == 'BLOCKED'


def test_capabilities_opaque_build_receipt_is_never_positive_readiness(prepared):
    store, idx, reg, world, _ = prepared
    raw = b'{"kind":"compile","result":{"outcome":"PASS"},"padding":"' + b'x' * (1024*1024) + b'"}'
    h = store.put(raw); reg['build_receipt_hash'] = h
    out = capabilities(store, index_id=idx, run_registry=reg, world=world['world'], evidence_hashes=(h,))
    assert out['gametest']['readiness'] == 'UNKNOWN'
    assert out['gametest']['reason_code'] == 'EVIDENCE_SCOPE_INSUFFICIENT'
    assert out['mappings']['readiness'] == out['failure_history']['readiness'] == 'NOT_CONFIGURED'


@pytest.mark.parametrize('damage', ['missing_identity', 'changed_epoch', 'foreign_registry_session', 'disabled', 'input_lock'])
def test_capabilities_native_input_keeps_current_identity_and_quarantine_guards(prepared, damage):
    store, idx, _, _, _ = prepared
    session, reg = client_session(prepared)
    if damage in ('missing_identity', 'changed_epoch'):
        path = Path(reg['session_file']); retained = json.loads(path.read_bytes())
        if damage == 'missing_identity': retained['contract'].pop('world_id')
        else: retained['contract']['session_epoch'] = 'different-epoch'
        path.write_bytes(canonical(retained))
    elif damage == 'foreign_registry_session': reg['session_file'] = '/private/other/session.json'
    elif damage == 'disabled': reg['enabled'] = False
    elif damage == 'input_lock':
        attempts = Path(session['directory']) / '.input-attempts'; attempts.mkdir()
        (attempts / ('active-' + key_for({'display': reg['display']}))).write_text('{}')
    c = capabilities(store, index_id=idx, session=session, input_registry=reg)['native_input']
    assert c['readiness'] in ('BLOCKED', 'UNKNOWN')
    assert c['reason_code'] != 'LIVE_STATE_NOT_PROBED'
    if damage == 'input_lock': assert c['reason_code'] == 'SESSION_UNKNOWN_COMPLETION'


def test_capabilities_no_side_effects_or_private_output(prepared, monkeypatch):
    store, idx, reg, world, root = prepared
    session, input_registry = client_session(prepared)
    inputs = task_context.load_task_inputs(store, index_id=idx, run_registry=reg, world=world['world'],
        session=session, input_registry=input_registry, core_configured=True)
    evidence = task_context.summarize_evidence(store, inputs)
    before_inputs = copy.deepcopy(inputs)
    def snapshot(directory):
        return {str(p.relative_to(directory)): p.read_bytes() for p in directory.rglob('*') if p.is_file()}
    before_store, before_workspace = snapshot(store.root), snapshot(root)
    def forbidden(*args, **kwargs):
        pytest.fail('Capability evaluation attempted a mutation, process, network or live probe')
    for owner, name in [(Store, 'put'), (Store, 'put_json'), (Store, 'pin'),
        (subprocess, 'Popen'), (subprocess, 'run'), (socket, 'create_connection'), (socket.socket, 'connect'),
        (execution, 'execute'), (execution, 'prepare_world'), (execution, 'prepare_client_directory'),
        (runtime, 'create_session'), (runtime, 'observe_live'), (runtime.BridgeClient, 'request'),
        (native_input, 'native_exchange'), (native_input, 'process_start'), (input_route, 'bind'),
        (input_route, 'dispatch_registered')]: monkeypatch.setattr(owner, name, forbidden)
    result = api().evaluate_capabilities(store, task_request(), inputs, evidence)
    assert inputs == before_inputs
    assert snapshot(store.root) == before_store and snapshot(root) == before_workspace
    public = json.dumps(result)
    for private in (str(root), str(store.root), session['token'], input_registry['session_file'], ':0'):
        assert private not in public
    assert len(public) < 16*1024
    assert result == api().evaluate_capabilities(store, task_request(goal='Launch on Windows now'), inputs, evidence)


def test_capabilities_prepared_bytecode_requires_complete_scope(class_profile):
    store, profile, _ = class_profile
    idx = index.prepare_index(profile, store, javap=shutil.which('javap'))['index_snapshot_id']
    out = capabilities(store, index_id=idx)
    assert out['bytecode_inspect']['readiness'] == 'READY'
    inputs = task_context.load_task_inputs(store, index_id=idx)
    evidence = task_context.summarize_evidence(store, inputs)
    evidence['index']['unresolved_bytecode'] = 1
    by_id = {row['id']: row for row in api().evaluate_capabilities(store, task_request(), inputs, evidence)}
    assert by_id['bytecode_inspect']['readiness'] == 'UNKNOWN'


def test_capabilities_registered_blockbench_remains_unprobed(prepared):
    store, idx, _, _, _ = prepared
    out = capabilities(store, index_id=idx, blockbench_registry=blockbench_registry())
    assert (out['blockbench_asset']['readiness'], out['blockbench_asset']['reason_code']) == ('UNKNOWN', 'LIVE_STATE_NOT_PROBED')


def test_capabilities_gametest_cannot_downgrade_dedicated_session_to_legacy_registry(prepared):
    store, idx, reg, world, _ = prepared
    profile = index._load(store, idx)['profile']
    c = dedicated_contract('dedicated_server')
    c.update(profile_id=profile['profile_id'], index_snapshot_id=idx,
        dirty_hash=profile['manifest']['dirty_hash'], source_revision=profile['manifest']['workspace_revision'],
        build_artifact_hash=store.json(reg['build_receipt_hash'])['outputs'][0]['content_hash'],
        world_id=world['world_id'], world_template_hash=world['world_template_hash'],
        config_hash=key_for([]), adapter_id=runtime.ADAPTER_ID, adapter_version=runtime.ADAPTER_VERSION)
    out = capabilities(store, index_id=idx, run_registry=reg, world=world['world'], session={'contract': c})
    assert out['gametest']['readiness'] == 'BLOCKED'


def test_capabilities_unknown_registry_compile_receipt_blocks_new_build_readiness(prepared):
    store, idx, reg, world, _ = prepared
    receipt = store.json(reg['build_receipt_hash']); receipt['result']['outcome'] = 'UNKNOWN'
    h = store.put_json(receipt); reg['build_receipt_hash'] = h
    out = capabilities(store, index_id=idx, run_registry=reg, world=world['world'])
    for name in ('forge_build', 'gametest'):
        assert (out[name]['readiness'], out[name]['reason_code']) == ('UNKNOWN', 'SESSION_UNKNOWN_COMPLETION')
        assert h in out[name]['evidence']


def test_capabilities_windows_unsupported_retains_unknown_reconciliation_evidence(prepared):
    store, idx, _, _, _ = prepared
    h = store.put_json({'kind': 'native-input-receipt', 'result': {'input_status': 'UNKNOWN'}})
    out = capabilities(store, index_id=idx, input_registry={'backend': 'windows'}, evidence_hashes=(h,))
    c = out['native_input']
    assert (c['surface'], c['readiness'], c['reason_code']) == ('UNSUPPORTED', 'BLOCKED', 'WINDOWS_INPUT_UNSUPPORTED')
    assert h in c['evidence'] and 'completion_reconciliation' in c['missing']


ACTION_FIELDS = {'operation_id', 'primary', 'mode', 'authorization_required',
                 'reason_code', 'required_inputs'}


def next_actions(store, *, request=None, **kwargs):
    request = request or task_request()
    inputs = task_context.load_task_inputs(store, **kwargs)
    evidence = task_context.summarize_evidence(store, inputs)
    evaluated = api().evaluate_capabilities(store, request, inputs, evidence)
    result = api().derive_next_actions(request, inputs, evaluated)
    assert len(result) <= 5
    assert all(set(action) == ACTION_FIELDS for action in result)
    assert all(type(action['primary']) is bool and type(action['authorization_required']) is bool
               and action['mode'] in ('READ_ONLY', 'SIDE_EFFECTING') for action in result)
    assert all(isinstance(action['required_inputs'], list) for action in result)
    return result


def test_next_action_without_index_requires_authorized_profile_resolution(tmp_path):
    actions = next_actions(Store(tmp_path / 'absent'))
    assert actions == [{'operation_id': 'profile.resolve', 'primary': True,
        'mode': 'SIDE_EFFECTING', 'authorization_required': True,
        'reason_code': 'PROFILE_MISSING', 'required_inputs': ['environment_capture']}]


@pytest.mark.parametrize('intent', ['investigate', 'edit_code', 'compatibility_research'])
def test_next_actions_index_allows_read_only_research_without_inventing_a_winner(prepared, intent):
    store, idx, _, _, _ = prepared
    history = store.put_json({'format': 'kneekura.failure-history.v1'})
    actions = next_actions(store, index_id=idx, request=task_request(intent=intent), evidence_hashes=(history,))
    assert {a['operation_id'] for a in actions} == {'research.search', 'history.query'}
    assert all(a['mode'] == 'READ_ONLY' and a['authorization_required'] is False for a in actions)
    assert all(a['primary'] is False for a in actions)


def test_next_action_asset_preparation_does_not_require_or_mutate_a_provider(prepared):
    store, idx, _, _, _ = prepared
    actions = next_actions(store, index_id=idx, request=task_request(intent='create_asset'))
    assert [a['operation_id'] for a in actions] == ['asset.prepare']
    assert actions[0]['mode'] == 'SIDE_EFFECTING' and actions[0]['authorization_required'] is True
    assert actions[0]['required_inputs'] == ['asset_spec']


def test_next_action_asset_requires_existing_supported_exact_target(prepared):
    from test_minecraft_task_context import replace_snapshot
    store, idx, _, _, _ = prepared
    idx = replace_snapshot(store, idx, lambda s: s['profile']['manifest'].update(loader='fabric'))
    assert next_actions(store, index_id=idx, request=task_request(intent='create_asset')) == []


def test_next_actions_proven_build_and_gametest_offer_authorized_preparation(prepared):
    store, idx, reg, world, _ = prepared
    actions = next_actions(store, index_id=idx, run_registry=reg, world=world['world'],
                           request=task_request(intent='verify_server'))
    assert {a['operation_id'] for a in actions} == {'build.registered', 'gametest.prepare'}
    assert all(a['mode'] == 'SIDE_EFFECTING' and a['authorization_required'] for a in actions)


@pytest.mark.parametrize('kind', ['native-input-receipt', 'compile', 'gametest', 'run-receipt', 'asset_export'])
def test_unknown_next_action_reconciles_before_any_mutation_or_replay(prepared, kind):
    store, idx, reg, world, _ = prepared
    receipt = {'record_type': kind} if kind == 'asset_export' else {'kind': kind}
    receipt['result'] = {'outcome': 'UNKNOWN'}
    h = store.put_json(receipt)
    intent = 'create_asset' if kind == 'asset_export' else 'edit_code'
    actions = next_actions(store, index_id=idx, run_registry=reg, world=world['world'],
        request=task_request(intent=intent), evidence_hashes=(h,))
    assert actions[0] == {'operation_id': 'runtime.reconcile_unknown', 'primary': True,
        'mode': 'READ_ONLY', 'authorization_required': False,
        'reason_code': 'SESSION_UNKNOWN_COMPLETION',
        'required_inputs': ['operation_identity', 'retained_receipt']}
    assert all(a['mode'] == 'READ_ONLY' for a in actions)
    assert sum(a['primary'] for a in actions) == 1


def test_unknown_next_action_preserves_windows_unsupported_reconciliation(prepared):
    store, idx, _, _, _ = prepared
    h = store.put_json({'kind': 'native-input-receipt', 'result': {'input_status': 'UNKNOWN'}})
    actions = next_actions(store, index_id=idx, input_registry={'backend': 'windows'}, evidence_hashes=(h,))
    assert actions[0]['operation_id'] == 'runtime.reconcile_unknown'
    assert actions[0]['primary'] is True
    assert all(a['mode'] == 'READ_ONLY' for a in actions)


def test_unknown_next_action_from_registry_receipt_never_reoffers_build(prepared):
    store, idx, reg, world, _ = prepared
    receipt = store.json(reg['build_receipt_hash']); receipt['result']['outcome'] = 'UNKNOWN'
    reg['build_receipt_hash'] = store.put_json(receipt)
    actions = next_actions(store, index_id=idx, run_registry=reg, world=world['world'])
    assert actions[0]['operation_id'] == 'runtime.reconcile_unknown'
    assert all(a['mode'] == 'READ_ONLY' for a in actions)


def test_next_actions_remain_bounded_deterministic_and_never_copy_caller_strings(prepared):
    store, idx, _, _, root = prepared
    inputs = task_context.load_task_inputs(store, index_id=idx)
    rows = [dict(id=name, surface='IMPLEMENTED', readiness='READY', reason_code='PREREQUISITES_SATISFIED',
                 missing=['/private/path', 'https://provider.invalid', 'sh -c secret'], evidence=[]) for name in IDS]
    original = copy.deepcopy((inputs, rows))
    actions = api().derive_next_actions(task_request(), inputs, rows)
    assert {a['operation_id'] for a in actions} == {'research.search', 'research.inspect', 'history.query',
                                                  'build.registered', 'gametest.prepare'}
    assert len(actions) == 5 and all(set(a) == ACTION_FIELDS for a in actions)
    assert not any(a['primary'] for a in actions)
    changed = task_request(goal=f'Execute sh -c secret; use {root} and https://provider.invalid')
    assert canonical(actions) == canonical(api().derive_next_actions(changed, inputs, list(reversed(rows))))
    assert (inputs, rows) == original
    public = canonical(actions)
    for forbidden in (b'/private', b'https://', b'sh -c', b'secret', str(root).encode()):
        assert forbidden not in public


@pytest.mark.parametrize('intent', ['verify_client', 'verify_server'])
def test_next_action_retained_session_offers_only_explicit_live_observation(prepared, intent):
    store, idx, _, _, _ = prepared
    session, _ = client_session(prepared)
    actions = next_actions(store, index_id=idx, session=session, request=task_request(intent=intent))
    assert actions == [{'operation_id': 'runtime.observe', 'primary': False,
        'mode': 'READ_ONLY', 'authorization_required': False,
        'reason_code': 'LIVE_STATE_NOT_PROBED', 'required_inputs': ['observation_query']}]


@pytest.mark.parametrize('outcome', ['FAIL', 'BLOCKED', 'NOT_RUN'])
def test_capabilities_unsuccessful_compile_requires_success_without_claiming_identity_corruption(prepared, outcome):
    store, idx, registry, world, _ = prepared
    receipt = store.json(registry['build_receipt_hash'])
    receipt['result']['outcome'] = outcome
    registry['build_receipt_hash'] = store.put_json(receipt)
    rows = capabilities(store, index_id=idx, run_registry=registry, world=world['world'])
    assert rows['gametest']['readiness'] == 'BLOCKED'
    assert rows['gametest']['missing'] == ['successful_compile_receipt']
    assert rows['forge_build']['readiness'] == 'READY'
