"""Production route fixtures: no real Minecraft, native display, or input acceptance."""
import base64
import copy
import importlib
import os
from pathlib import Path
import time

import pytest

from kneekura_tech_hub.minecraft import native_input, runtime
from kneekura_tech_hub.minecraft.storage import ContractError, Store, canonical, digest
from kneekura_tech_hub.minecraft.verification import IDENTITY_FIELDS
from test_minecraft_verification import contract
from test_minecraft_cli import run_cli


def api():
    try: return importlib.import_module('kneekura_tech_hub.minecraft.input_route')
    except ImportError: pytest.fail('Registered native input route is not implemented')


@pytest.fixture
def route(tmp_path, monkeypatch):
    c = contract(); c.update(physical_side='client', assertion_domain='client_observation')
    identity = {k: c[k] for k in IDENTITY_FIELDS}
    session_path = tmp_path/'session.json'
    session_path.write_bytes(canonical({'token': 'a'*64, 'contract': c, 'directory':str(tmp_path), 'endpoint_path':str(tmp_path/'endpoint.json')})); session_path.chmod(0o600)
    registry = {'schema_version': 1, 'backend': native_input.BACKEND_ID, 'enabled': True,
                'session_file': str(session_path), 'display': ':0',
                'allowed_controls': ['mouse:right'], 'timeout_seconds': 5}
    native = {'platform': 'linux-x11', 'process_id': os.getpid(), 'window_id': '42',
              'process_start': native_input.process_start(os.getpid()),
              'client_size': [640, 480], 'foreground': True, 'cursor_mode':'disabled'}
    calls = []
    store = Store(tmp_path/'cas')
    def observer(store, session, *, operation, query=None, timeout=10):
        calls.append(('observe', operation))
        raw = {'identity': copy.deepcopy(identity), 'native_input': copy.deepcopy(native), 'screen':'none',
               'client_frame_start': 1, 'client_frame_end': 1, 'logs': []}
        if operation == 'client':
            image = b'\x89PNG\r\n\x1a\nsynthetic-fixture'
            raw.update(png_b64=base64.b64encode(image).decode(), png_sha256=digest(image))
        return {'status':'OK', 'outcome':'NOT_RUN', 'artifact_hash':store.put_json(raw),
                'handshake_hash':store.put_json({'identity':identity, 'ready':True}),
                'evidence_level':'AUTHENTICATED_LIVE_OBSERVER'}
    def native_call(display, target, *, deadline, position=None, hold_ms=None):
        calls.append(('native', position))
        if position is None: return {'client_size': [640, 480], 'foreground': True}
        return {'pressed':True, 'released':True}
    monkeypatch.setattr(runtime, 'observe_live', observer)
    monkeypatch.setattr(native_input, 'native_exchange', native_call)
    return store, registry, identity, native, calls


def request(binding):
    return {'schema_version':1, 'operation_id':'staff-use-1', 'identity':binding['identity'],
            'target_id':binding['target_id'], 'control':'mouse:right', 'position':[320,240], 'hold_ms':10}


def test_registered_bind_is_read_only_and_dispatch_persists_separate_evidence(route):
    store, registry, identity, native, calls = route
    binding = api().bind(store, registry)
    assert binding['identity'] == identity
    assert not any(c[0] == 'native' and c[1] is not None for c in calls)
    result = api().dispatch_registered(store, registry, binding['binding_hash'], request(binding))
    assert result['input_status'] == 'COMPLETED' and result['outcome'] == 'NOT_RUN'
    assert all(v == 'NOT_RUN' for v in result['verification'].values())
    receipt = store.json(result['receipt_hash'])
    assert receipt['binding_hash'] == binding['binding_hash']
    assert receipt['before']['screenshot_hash'] and receipt['after']['screenshot_hash']
    assert receipt['logs']['artifact_hash'] and receipt['request_hash']
    assert 'a'*64 not in str(receipt)
    with pytest.raises(ContractError, match='attempt'):
        api().dispatch_registered(store, registry, binding['binding_hash'], request(binding))
    assert sum(c == ('native', [320,240]) for c in calls) == 1


@pytest.mark.parametrize('field,value', [('process_id',42), ('process_start','0'), ('window_id','43'), ('client_size',[800,600]), ('foreground',False)])
def test_changed_authenticated_target_blocks_before_native_press(route, field, value):
    store, registry, identity, native, calls = route
    binding = api().bind(store, registry)
    native[field] = value
    result = api().dispatch_registered(store, registry, binding['binding_hash'], request(binding))
    assert result['input_status'] == 'BLOCKED'
    assert ('native',[320,240]) not in calls


@pytest.mark.parametrize('change', [{'enabled':False}, {'display':'evil:0'}, {'backend':'windows'},
                                  {'allowed_controls':['key:E']}, {'timeout_seconds':True}, {'command':'xdotool'}])
def test_invalid_registration_rejected_before_observation(route, change):
    store, registry, identity, native, calls = route
    registry.update(change)
    with pytest.raises(ContractError): api().bind(store, registry)
    assert calls == []


def test_registry_edit_cannot_reauthorize_existing_binding(route):
    store, registry, _, _, calls = route
    binding = api().bind(store, registry); before = len(calls)
    registry['display'] = ':1'
    with pytest.raises(ContractError):
        api().dispatch_registered(store, registry, binding['binding_hash'], request(binding))
    assert len(calls) == before


def test_unknown_completion_consumes_attempt_and_never_retries(route, monkeypatch):
    store, registry, _, _, calls = route
    binding = api().bind(store, registry)
    original = native_input.native_exchange
    def uncertain(*args, **kwargs):
        if kwargs.get('position') is not None: raise ContractError('private helper failure')
        return original(*args, **kwargs)
    monkeypatch.setattr(native_input, 'native_exchange', uncertain)
    result = api().dispatch_registered(store, registry, binding['binding_hash'], request(binding))
    assert result['input_status'] == 'UNKNOWN' and result['retry_allowed'] is False
    assert 'private helper failure' not in str(result)
    with pytest.raises(ContractError): api().dispatch_registered(store, registry, binding['binding_hash'], request(binding))


def test_cli_input_route_exists_and_off_registration_does_not_contact_display(tmp_path):
    import json
    registry = tmp_path/'disabled.json'; registry.write_text(json.dumps({'enabled':False}))
    process, result = run_cli(tmp_path/'cas','input','bind','--registry',str(registry))
    assert result is not None and process.returncode == 2
    assert result['status'] == 'ERROR'


def test_unconfirmed_native_release_blocks_new_operation_ids(route, monkeypatch):
    store, registry, _, _, _ = route
    binding = api().bind(store, registry)
    original = native_input.native_exchange
    def uncertain(*args, **kwargs):
        if kwargs.get('position') is not None: raise ContractError('unknown')
        return original(*args, **kwargs)
    monkeypatch.setattr(native_input, 'native_exchange', uncertain)
    result = api().dispatch_registered(store, registry, binding['binding_hash'], request(binding))
    assert result['input_status'] == 'UNKNOWN'
    other = request(binding); other['operation_id'] = 'not-a-safe-retry'
    with pytest.raises(ContractError, match='active'):
        api().dispatch_registered(store, registry, binding['binding_hash'], other)


def test_attempt_consumption_survives_a_different_cas_directory(route, tmp_path):
    store, registry, _, _, _ = route
    binding = api().bind(store, registry)
    api().dispatch_registered(store, registry, binding['binding_hash'], request(binding))
    different = Store(tmp_path/'different-cas')
    binding_hash = different.put(store.read(binding['binding_hash']))
    with pytest.raises(ContractError, match='attempt'):
        api().dispatch_registered(different, registry, binding_hash, request(binding))


def test_cancelled_parent_keeps_attempt_and_active_marker(route, monkeypatch):
    store, registry, _, _, _ = route
    binding = api().bind(store, registry)
    original = native_input.native_exchange
    def cancelled(*args, **kwargs):
        if kwargs.get('position') is not None: raise KeyboardInterrupt()
        return original(*args, **kwargs)
    monkeypatch.setattr(native_input, 'native_exchange', cancelled)
    with pytest.raises(KeyboardInterrupt):
        api().dispatch_registered(store, registry, binding['binding_hash'], request(binding))
    other = request(binding); other['operation_id'] = 'after-cancel'
    with pytest.raises(ContractError, match='active'):
        api().dispatch_registered(store, registry, binding['binding_hash'], other)


def test_changed_post_capture_is_retained_as_failure_evidence(route, monkeypatch):
    store, registry, _, native, _ = route
    binding = api().bind(store, registry)
    original = native_input.native_exchange
    def change_after_press(*args, **kwargs):
        result = original(*args, **kwargs)
        if kwargs.get('position') is not None: native['window_id'] = '43'
        return result
    monkeypatch.setattr(native_input, 'native_exchange', change_after_press)
    result = api().dispatch_registered(store, registry, binding['binding_hash'], request(binding))
    assert result['input_status'] == 'UNKNOWN'
    receipt = store.json(result['receipt_hash'])
    assert receipt['after'] is not None
    assert store.json(receipt['after']['artifact_hash'])['native_input']['window_id'] == '43'


def test_copied_private_session_cannot_relocate_replay_ledger(route, tmp_path):
    import shutil
    store, registry, _, _, calls = route
    binding = api().bind(store, registry)
    api().dispatch_registered(store, registry, binding['binding_hash'], request(binding))
    copied_dir = tmp_path/'copied-session'; copied_dir.mkdir()
    copied_file = copied_dir/'session.json'
    shutil.copyfile(registry['session_file'], copied_file); copied_file.chmod(0o600)
    copied_registry = dict(registry, session_file=str(copied_file))
    with pytest.raises(ContractError, match='canonical'):
        api().bind(store, copied_registry)
    assert sum(c == ('native',[320,240]) for c in calls) == 1


def test_crosshair_driver_rejects_arbitrary_viewport_clicks_before_input(route):
    store, registry, _, _, calls = route
    binding = api().bind(store, registry)
    value=request(binding); value['position']=[10,20]
    before=len(calls)
    with pytest.raises(ContractError,match='crosshair'):
        api().dispatch_registered(store,registry,binding['binding_hash'],value)
    assert len(calls)==before


def test_ui_or_ungrabbed_cursor_cannot_bind_gameplay_driver(route):
    store, registry, _, native, calls = route
    native['cursor_mode']='normal'
    with pytest.raises(ContractError,match='gameplay'):
        api().bind(store,registry)
    assert not any(c[0]=='native' for c in calls)
