"""Explicit registered native input, reusing authenticated Observer and existing CAS.

Bindings authorize no executable paths or commands. Every invocation rechecks the
same observer run and native process/window, consumes an operation ID exactly once,
and records screenshots/logs separately from the native attempt. A native completion
is never a visual, synchronization, right-click gameplay, or server assertion PASS.
"""
from __future__ import annotations

import base64
import math
import json
import os
from pathlib import Path
import time

from . import input_contract, native_input, runtime
from .storage import ContractError, Store, atomic_write, canonical, digest, key_for, valid_hash
from .verification import identity_fields, _identity_errors, validate_connection

_REGISTRY_FIELDS = {'schema_version', 'backend', 'enabled', 'session_file', 'display',
                    'allowed_controls', 'timeout_seconds'}


def _registry(registry):
    value = input_contract._detached(registry)
    if (set(value) != _REGISTRY_FIELDS or type(value['schema_version']) is not int
            or value['schema_version'] != 1 or value['enabled'] is not True
            or value['backend'] != native_input.BACKEND_ID
            or value['allowed_controls'] != ['mouse:right']):
        raise ContractError('Explicit enabled Linux X11 right-button registry required')
    native_input.validate_display(value['display'])
    timeout = value['timeout_seconds']
    if type(timeout) not in (int, float) or not 0 < timeout <= 5 or not math.isfinite(timeout):
        raise ContractError('Registered input deadline must be finite and at most five seconds')
    path = value['session_file']
    if not isinstance(path, str) or not Path(path).is_absolute():
        raise ContractError('Existing absolute private observer session path required')
    session = runtime.load_session(path)
    directory = Path(session.get('directory', ''))
    endpoint = Path(session.get('endpoint_path', ''))
    if (not directory.is_absolute() or directory.is_symlink() or not directory.is_dir()
            or directory != directory.resolve()
            or Path(session['path']) != directory/'session.json'
            or endpoint != directory/'endpoint.json'):
        raise ContractError('Input requires the canonical owned session/run directory; relocated copies are forbidden')
    contract = session['contract']
    if _identity_errors(contract, {'identity':contract}) or contract.get('physical_side') != 'client':
        raise ContractError('Native input requires an authenticated physical-client run')
    return value, session


def _capture(store, registry, contract, deadline, *, operation='client'):
    remaining = deadline-time.monotonic()
    if remaining <= 0: raise ContractError('Input observation deadline expired')
    query = {'screenshot':True} if operation == 'client' else {}
    if operation == 'client' and contract.get('session_role') == 'dedicated_client':
        # This dedicated native route serves the fixed overworld staff fixture.
        # The real StaffStateQuery requires an explicit dimension; the receiver
        # also rejects a changed dimension rather than following a player there.
        query.update(entity_uuids=[contract['player_uuid']], dimension='minecraft:overworld',
                     limit=1, staff_state=True)
    result = runtime.observe_live(store, registry['session_file'], operation=operation,
                   query=query, timeout=min(remaining, 5))
    if (result.get('evidence_level') != 'AUTHENTICATED_LIVE_OBSERVER'
            or result.get('status') != 'OK'):
        raise ContractError('Authenticated same-run observer capture required')
    raw = store.json(valid_hash(result['artifact_hash']))
    if _identity_errors(contract, raw): raise ContractError('Input observation identity changed')
    if time.monotonic() >= deadline: raise ContractError('Input observation exceeded deadline')
    evidence = {'artifact_hash':result['artifact_hash'], 'handshake_hash':result['handshake_hash']}
    if operation == 'client':
        try: image = base64.b64decode(raw['png_b64'], validate=True)
        except (KeyError, ValueError, TypeError) as exc: raise ContractError('Client screenshot required') from exc
        if len(image) > 8*1024*1024 or not image.startswith(b'\x89PNG\r\n\x1a\n') or digest(image) != raw.get('png_sha256'):
            raise ContractError('Client screenshot hash/format invalid')
        evidence['screenshot_hash'] = store.put(image)
    for h in evidence.values(): store.pin(h, 'input:'+contract['run_id'])
    return raw, evidence


def _target(raw):
    value = raw.get('native_input')
    if (not isinstance(value, dict) or set(value) != {'platform','process_id','process_start','window_id','client_size','foreground','cursor_mode'}
            or value['platform'] != 'linux-x11' or value['foreground'] is not True):
        raise ContractError('Authenticated foreground Linux X11 native scope required')
    if raw.get('screen') != 'none' or value['cursor_mode'] != 'disabled':
        raise ContractError('Selected input driver requires gameplay crosshair with the GLFW cursor disabled')
    target = {k:value[k] for k in ('process_id','process_start','window_id','client_size')}
    return native_input.validate_target(target)


def bind(store: Store, registry: dict):
    registry, session = _registry(registry); contract = session['contract']
    deadline = time.monotonic()+registry['timeout_seconds']
    raw, evidence = _capture(store, registry, contract, deadline)
    target = _target(raw)
    native = native_input.native_exchange(registry['display'], target, deadline=deadline)
    if native != {'client_size':target['client_size'], 'foreground':True}:
        raise ContractError('Native target differs from authenticated observer scope')
    identity = {k:contract[k] for k in identity_fields(contract)}
    scope = {'identity':identity, 'native':target}
    if contract.get('session_role') == 'dedicated_client':
        scope['connection'] = validate_connection(contract, raw.get('connection'))
    target_id = 'x11:'+key_for(scope)
    record = {'schema_version':1, 'kind':'native-input-binding', 'backend':native_input.BACKEND_ID,
              'registry_hash':key_for(registry), 'identity':identity, 'target':target,
              'target_id':target_id, 'evidence':evidence}
    if 'connection' in scope: record['connection'] = scope['connection']
    h = store.put_json(record); store.pin(h, 'input-binding:'+contract['run_id'])
    return {'status':'OK', 'outcome':'NOT_RUN', 'binding_hash':h, 'target_id':target_id,
            'identity':identity, 'backend':native_input.BACKEND_ID,
            'client_size':target['client_size'], 'input_mode':'gameplay-crosshair',
            'position':[n//2 for n in target['client_size']],
            'note':'Read-only target binding; no input or gameplay acceptance'}


class LinuxX11Backend:
    """Production InputBackend; all native mutation is isolated in its owned helper."""
    def __init__(self, store, registry, contract, binding):
        self.store, self.registry, self.contract, self.binding = store, registry, contract, binding
        self.observations = []; self.completion = None; self.owner = None

    def snapshot(self, *, deadline):
        raw, evidence = _capture(self.store, self.registry, self.contract, deadline)
        # Keep authenticated failure snapshots too; a changed scope is evidence,
        # even though it cannot authorize input or establish success.
        self.observations.append(evidence)
        target = _target(raw)
        if self.contract.get('session_role') == 'dedicated_client':
            connection = validate_connection(self.contract, raw.get('connection'))
            if connection != self.binding.get('connection'):
                raise ContractError('Bound receiving-client connection changed')
        if target != self.binding['target']: raise ContractError('Bound native target changed')
        current = native_input.native_exchange(self.registry['display'], target, deadline=deadline)
        if current != {'client_size':target['client_size'], 'foreground':True}:
            raise ContractError('Current native target differs from authenticated scope')
        return {'identity':self.binding['identity'], 'target_id':self.binding['target_id'],
                'foreground':True, 'client_size':target['client_size']}

    def press(self, request, scope, *, deadline):
        if self.owner is not None: raise ContractError('A native backend cannot replay an operation')
        if self.snapshot(deadline=deadline) != scope: raise ContractError('Scope changed before native dispatch')
        self.owner = (request['operation_id'], request['target_id'], request['control'])
        self.completion = native_input.native_exchange(self.registry['display'], self.binding['target'],
            deadline=deadline, position=request['position'], hold_ms=request['hold_ms'])
        if self.completion != {'pressed':True, 'released':True}:
            raise ContractError('Native gesture completion is uncertain')

    def release(self, *, operation_id, target_id, control, deadline):
        # The helper already owns its bounded release. Never inject a fresh global
        # release after a parent timeout, changed foreground, or helper failure.
        if (time.monotonic() >= deadline or self.owner != (operation_id,target_id,control)
                or self.completion != {'pressed':True, 'released':True}):
            raise ContractError('Owned native release is unconfirmed')


def _claim(path, value):
    try:
        fd = os.open(path, os.O_WRONLY|os.O_CREAT|os.O_EXCL, 0o600)
        with os.fdopen(fd, 'wb') as stream:
            stream.write(canonical(value)); stream.flush(); os.fsync(stream.fileno())
    except FileExistsError:
        raise ContractError('Input attempt already exists or another native operation is active; inspect before continuing') from None


def dispatch_registered(store: Store, registry: dict, binding_hash: str, request: dict):
    registry, session = _registry(registry); contract = session['contract']
    binding = store.json(valid_hash(binding_hash))
    if (binding.get('kind') != 'native-input-binding' or binding.get('backend') != native_input.BACKEND_ID
            or binding.get('registry_hash') != key_for(registry)
            or _identity_errors(contract, {'identity':binding.get('identity')})):
        raise ContractError('Native binding differs from registered session/authority')
    request = input_contract._validate(contract, request, binding['target_id'],
                                      registry['allowed_controls'], registry['timeout_seconds'])
    if request['position'] != [n//2 for n in binding['target']['client_size']]:
        raise ContractError('Selected driver only accepts the gameplay crosshair center, not UI point clicks')
    # The session owns replay state, so changing --store cannot replay a gesture.
    attempt_dir = Path(session['directory'])/'.input-attempts'
    if attempt_dir.is_symlink(): raise ContractError('Unsafe input attempt directory')
    attempt_dir.mkdir(exist_ok=True)
    owner = attempt_dir/'owner.json'
    expected_owner = {'identity_hash':key_for(binding['identity'])}
    if owner.exists() or owner.is_symlink():
        if owner.is_symlink() or owner.stat().st_size > 1024 or json.loads(owner.read_bytes()) != expected_owner:
            raise ContractError('Input replay ledger belongs to a different run identity')
    else:
        _claim(owner, expected_owner)
    attempt = key_for({'run_id':contract['run_id'], 'session_epoch':contract['session_epoch'],
                       'operation_id':request['operation_id']})
    lock = attempt_dir/('active-'+key_for({'display':registry['display']}))
    attempt_path = attempt_dir/attempt
    _claim(lock, {'attempt':attempt})
    backend = LinuxX11Backend(store, registry, contract, binding)
    release_lock = True
    try:
        request_hash = store.put_json(request)
        _claim(attempt_path, {'status':'STARTED', 'request_hash':request_hash})
        release_lock = False
        try:
            result = input_contract.dispatch_input(contract, request, target_id=binding['target_id'],
                        allowed_controls=tuple(registry['allowed_controls']), backend=backend,
                        timeout_seconds=registry['timeout_seconds'])
        except BaseException:
            # A durable consumed attempt remains even when cancellation interrupts
            # receipt completion. It must never be automatically resumed/replayed.
            atomic_write(attempt_path, canonical({'status':'UNKNOWN', 'request_hash':request_hash}))
            raise
        result['evidence_level'] = 'NATIVE_INPUT_ATTEMPT_NOT_GAMEPLAY_ATTESTATION'
        if result['input_status'] == 'COMPLETED':
            result['reasons'] = ['Native input gesture completed; gameplay/visual/synchronization assertions remain separate']
        logs = None
        try:
            _, logs = _capture(store, registry, contract, time.monotonic()+registry['timeout_seconds'], operation='logs')
        except (ContractError, OSError, ValueError, KeyError):
            result['reasons'].append('Post-input log capture unavailable')
        evidence = backend.observations
        receipt = {'schema_version':1, 'kind':'native-input-receipt', 'binding_hash':binding_hash,
                   'request_hash':request_hash, 'result':result, 'native_completion':backend.completion,
                   'before':evidence[1] if len(evidence)>1 else evidence[0] if evidence else None,
                   'after':evidence[-1] if len(evidence)>2 else None, 'logs':logs}
        h = store.put_json(receipt)
        for value in (h, request_hash, binding_hash): store.pin(value, 'input:'+contract['run_id'])
        atomic_write(attempt_path, canonical({'status':result['input_status'], 'receipt_hash':h}))
        release_lock = result['input_status'] != 'UNKNOWN'
        return dict(result, status='OK', receipt_hash=h, binding_hash=binding_hash)
    finally:
        # UNKNOWN/cancellation remains quarantined until an operator inspects the
        # helper, native button state and target. A new ID is not a safe retry.
        if release_lock: lock.unlink()
