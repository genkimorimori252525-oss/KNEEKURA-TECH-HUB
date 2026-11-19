"""Explicit bounded LAB file transport; no runtime launch or action dispatch.

Registry bytes are operator-selected authority, never fields from an experiment.
The same source module closure and executable are rechecked on each invocation.
The declared Git revision is metadata; pinned byte identities are the proof.
"""
from __future__ import annotations

import hashlib
import math
import os
from pathlib import Path
import re
import stat
import time

from .asset_contract import decode_json
from .experiment_bridge import _read_bounded, load_experiment
from .experiment_contract import experiment_binding
from .process import run_process
from .storage import ContractError, IntegrityError, Store, canonical, digest, key_for, valid_hash

BACKEND = 'kneekura.lab.local-bridge.v1'
MODULES = ('adapter-cli.mjs', 'adapter.mjs', 'registration.mjs', 'materials.mjs',
           'json.mjs', 'action-journal.mjs', 'arena-contract.mjs')
_FIELDS = {'schema_version', 'enabled', 'backend', 'workspace', 'source_revision', 'executable',
           'executable_hash', 'module_hashes', 'owner_file', 'owner_hash', 'timeout_seconds'}

_BUILTIN_LAB_RELATIVE = Path('departments/minecraft/lab')


def builtin_lab_root() -> Path:
    """Return the vendored LAB source root when running from a Tech Hub checkout.

    This is source discovery only. It never grants runtime authority or launches
    Node, Forge, Minecraft, an owner, or an experiment.
    """
    return Path(__file__).resolve().parents[3] / _BUILTIN_LAB_RELATIVE


def inspect_builtin_source() -> dict:
    """Inspect the same-repository LAB source without executing it."""
    root = builtin_lab_root()
    bridge = root / 'debug-workspace' / 'bridge'
    available = root.is_dir() and all((bridge / name).is_file() for name in MODULES)
    return {
        'schema_version': 1,
        'status': 'AVAILABLE' if available else 'UNAVAILABLE',
        'backend': BACKEND,
        'source_location': _BUILTIN_LAB_RELATIVE.as_posix(),
        'source_identity': 'SAME_REPOSITORY_TREE',
        'module_count': len(MODULES) if available else 0,
        'execution': 'BLOCKED',
        'runtime_attestation': 'NOT_ESTABLISHED',
    }


def _resolve(path):
    try:
        return path.resolve()
    except (OSError, RuntimeError):
        raise IntegrityError('Registered path cannot be resolved safely') from None


def _directory(value):
    if not isinstance(value, str): raise ContractError('Explicit canonical directory required')
    p = Path(value)
    if not p.is_absolute() or p.is_symlink() or _resolve(p) != p or not p.is_dir():
        raise ContractError('Explicit canonical directory required')
    return p


def _file(path, limit, *, expected=None, retain=True, deadline=None):
    p = Path(path)
    if not p.is_absolute() or _resolve(p) != p or p.is_symlink():
        raise ContractError('Canonical nonsymlink file required')
    before = p.stat(follow_symlinks=False)
    if not stat.S_ISREG(before.st_mode) or before.st_size > limit:
        raise ContractError('Bounded regular file required')
    fd = os.open(p, os.O_RDONLY | getattr(os, 'O_NOFOLLOW', 0) | getattr(os, 'O_NONBLOCK', 0))
    hashed = hashlib.sha256(); chunks = []; total = 0
    with os.fdopen(fd, 'rb') as stream:
        opened = os.fstat(stream.fileno())
        if (before.st_dev, before.st_ino) != (opened.st_dev, opened.st_ino) or not stat.S_ISREG(opened.st_mode):
            raise IntegrityError('Registered file changed')
        while chunk := stream.read(65536):
            total += len(chunk)
            if total > limit or deadline is not None and time.monotonic() >= deadline:
                raise ContractError('Registered read budget exhausted')
            hashed.update(chunk)
            if retain: chunks.append(chunk)
        after = os.fstat(stream.fileno())
    named = p.stat(follow_symlinks=False)
    if (total != opened.st_size or (opened.st_size, opened.st_mtime_ns, opened.st_ctime_ns) !=
            (after.st_size, after.st_mtime_ns, after.st_ctime_ns) or
            (after.st_dev, after.st_ino) != (named.st_dev, named.st_ino) or _resolve(p) != p or p.is_symlink()):
        raise IntegrityError('Registered file changed')
    if expected is not None and hashed.hexdigest() != valid_hash(expected):
        raise IntegrityError('Registered content identity changed')
    return b''.join(chunks) if retain else hashed.hexdigest()


def _registry(value, *, deadline=None):
    if (not isinstance(value, dict) or set(value) != _FIELDS or type(value['schema_version']) is not int
            or value['schema_version'] != 1 or value['enabled'] is not True or value['backend'] != BACKEND):
        raise ContractError('Explicit enabled LAB adapter registry required')
    timeout = value['timeout_seconds']
    if type(timeout) not in (int, float) or not math.isfinite(timeout) or not 0 < timeout <= 10:
        raise ContractError('LAB adapter deadline must be at most ten seconds')
    if not isinstance(value['source_revision'], str) or not re.fullmatch('[a-f0-9]{40}|[a-f0-9]{64}', value['source_revision']):
        raise ContractError('Declared exact LAB revision required')
    root = _directory(value['workspace'])
    modules = value['module_hashes']
    if not isinstance(modules, dict) or set(modules) != set(MODULES):
        raise ContractError('Exact fixed LAB module closure required')
    for name in MODULES:
        _file(root/'debug-workspace/bridge'/name, 1024*1024, expected=modules[name], retain=False, deadline=deadline)
    _file(value['executable'], 256*1024*1024, expected=value['executable_hash'], retain=False, deadline=deadline)
    owner = decode_json(_file(value['owner_file'], 65536, expected=value['owner_hash'], deadline=deadline), max_bytes=65536)
    if (not isinstance(owner, dict) or set(owner) != {'schemaVersion', 'runtimeRoot', 'inputRoot', 'run'}
            or type(owner['schemaVersion']) is not int or owner['schemaVersion'] != 1):
        raise ContractError('Exact owner configuration required')
    _directory(owner['runtimeRoot']); _directory(owner['inputRoot'])
    return root, owner


def inspect_registry(registry):
    try:
        _registry(registry)
    except OSError:
        raise IntegrityError('Registered LAB adapter inputs are unavailable') from None
    return {'schema_version': 1, 'status': 'REGISTERED', 'backend': BACKEND,
            'registry_hash': key_for(registry), 'declared_source_revision': registry['source_revision'],
            'identity_verification': 'PINNED_EXECUTABLE_AND_MODULE_BYTES',
            'execution': 'BLOCKED', 'runtime_attestation': 'NOT_ESTABLISHED'}


def _exclusive(path, raw):
    try:
        fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    except FileExistsError:
        if _file(path, len(raw)) != raw: raise IntegrityError('Conflicting transport input') from None
        return
    with os.fdopen(fd, 'wb') as stream:
        stream.write(raw); stream.flush(); os.fsync(stream.fileno())


def _package(store, request_hash, owner):
    request = load_experiment(store, request_hash)
    root = _directory(owner['inputRoot'])/request_hash
    root.mkdir(mode=0o700, exist_ok=True); _directory(str(root))
    rows = {'request.json': canonical(request), 'assertions.json': canonical(request['assertions']),
            'binding.json': canonical(experiment_binding(request))}
    for name, field, limit in (('build.bin', 'build_artifact_hash', 64*1024*1024),
                               ('config.bin', 'config_hash', 1024*1024),
                               ('resource.bin', 'resource_hash', 16*1024*1024)):
        rows[name] = _read_bounded(store, request['target'][field], limit)
    for name, raw in rows.items(): _exclusive(root/name, raw)


def _response(raw, request):
    r = decode_json(raw, max_bytes=65536)
    common = {'schemaVersion', 'status', 'requestHash', 'execution', 'runtimeAttestation'}
    registered = common | {'registrationHash', 'experimentId', 'generation', 'capabilityReadiness'}
    reconciled = {'schemaVersion', 'status', 'recordedStatus', 'requestHash', 'idempotencyKey',
                  'evidenceHashes', 'dispatchAllowed', 'runtimeAttestation'}
    if not isinstance(r, dict) or type(r.get('schemaVersion')) is not int or r['schemaVersion'] != 1 or r.get('requestHash') != request['requestHash'] or r.get('runtimeAttestation') != 'NOT_ESTABLISHED':
        raise IntegrityError('LAB response linkage invalid')
    if request['operation'] == 'reconcile_action':
        if (set(r) != reconciled or r['idempotencyKey'] != request['idempotencyKey'] or r['dispatchAllowed'] is not False
                or r['status'] not in ('NEVER_SEEN', 'REQUESTED', 'NOT_RUN', 'VERIFIED', 'FAILED', 'PARTIAL_APPLY', 'OUTCOME_UNKNOWN')
                or r['recordedStatus'] not in (None, 'REQUESTED', 'ACCEPTED', 'APPLIED', 'NOT_RUN', 'VERIFIED', 'FAILED', 'PARTIAL_APPLY', 'OUTCOME_UNKNOWN')
                or not isinstance(r['evidenceHashes'], list) or len(r['evidenceHashes']) > 32):
            raise IntegrityError('LAB reconciliation response invalid')
        for h in r['evidenceHashes']: valid_hash(h)
    elif r['status'] == 'REGISTERED':
        if (set(r) != registered or r['execution'] != 'NOT_RUN'
                or not isinstance(r['experimentId'], str) or not re.fullmatch('[a-zA-Z0-9][a-zA-Z0-9._:-]{0,159}', r['experimentId'])
                or type(r['generation']) is not int or not 1 <= r['generation'] <= 1000000
                or r['capabilityReadiness'] != {'execution': 'BLOCKED', 'arena': 'BLOCKED', 'capture': 'BLOCKED'}):
            raise IntegrityError('LAB registration response invalid')
        valid_hash(r['registrationHash'])
    elif request['operation'] != 'inspect_registration' or r['status'] != 'NEVER_SEEN' or set(r) != common or r['execution'] != 'NOT_RUN':
        raise IntegrityError('LAB response operation mismatch')
    return r


def _invoke(store, registry, request, *, materialize=False):
    started = time.monotonic()
    # Validate the scalar deadline before using it for any computation.
    timeout = registry.get('timeout_seconds') if isinstance(registry, dict) else None
    if type(timeout) not in (int, float) or not math.isfinite(timeout) or not 0 < timeout <= 10:
        raise ContractError('LAB adapter deadline must be at most ten seconds')
    deadline = started + timeout
    root, owner = _registry(registry, deadline=deadline)
    if materialize: _package(store, request['requestHash'], owner)
    command_file = _directory(owner['inputRoot'])/('adapter-'+key_for(request)+'.json')
    _exclusive(command_file, canonical(request))
    _registry(registry, deadline=deadline)
    remaining = deadline-time.monotonic()
    if remaining <= 0: raise ContractError('LAB adapter deadline exhausted before invocation')
    result = run_process([registry['executable'], str(root/'debug-workspace/bridge/adapter-cli.mjs'),
        '--owner', registry['owner_file'], '--request', str(command_file)], root,
        timeout=remaining, max_output_bytes=65536, env={'NODE_OPTIONS': '', 'NODE_PATH': ''}, inherit_environment=False)
    response = None
    try:
        if not result['completed'] or result['exit_code'] != 0: raise ContractError('Local adapter incomplete')
        _registry(registry, deadline=deadline)
        response = _response(result['stdout'], request)
    except (OSError, ContractError, ValueError, TypeError, KeyError):
        pass
    status = 'OK' if response is not None else 'UNKNOWN'
    record = {'schema_version': 1, 'record_type': 'experiment_adapter_receipt',
        'registry_hash': key_for(registry), 'request_hash': request['requestHash'],
        'operation': request['operation'], 'status': status, 'reported': response,
        'execution': 'NOT_RUN', 'runtime_attestation': 'NOT_ESTABLISHED',
        'timed_out': result.get('timed_out') is True, 'output_limited': result.get('output_limited') is True}
    receipt = store.put_json(record); store.pin(receipt, 'experiment-adapter:'+request['requestHash'])
    return dict(record, receipt_hash=receipt, next_operation='experiment.reconcile_unknown' if request['operation'] == 'reconcile_action' else 'experiment.inspect_registration')


def register_request(store: Store, registry: dict, request_hash: str):
    return _invoke(store, registry, {'schemaVersion': 1, 'operation': 'register', 'requestHash': valid_hash(request_hash)}, materialize=True)


def inspect_registration(store: Store, registry: dict, request_hash: str):
    return _invoke(store, registry, {'schemaVersion': 1, 'operation': 'inspect_registration', 'requestHash': valid_hash(request_hash)})


def reconcile_action(store: Store, registry: dict, request_hash: str, idempotency_key: str):
    if not isinstance(idempotency_key, str) or not re.fullmatch('[a-zA-Z0-9][a-zA-Z0-9._:-]{0,159}', idempotency_key):
        raise ContractError('Bounded action identity required')
    return _invoke(store, registry, {'schemaVersion': 1, 'operation': 'reconcile_action',
        'requestHash': valid_hash(request_hash), 'idempotencyKey': idempotency_key})


def read_registry_file(path):
    """Bounded regular-file registry read; never use an unbounded CLI JSON loader."""
    return decode_json(_file(Path(path).absolute(), 128*1024), max_bytes=128*1024)


def read_input_json(path, *, max_bytes=2*1024*1024):
    """Finite experiment CLI data; no FIFO, symlink or unbounded read."""
    return decode_json(_file(Path(path).absolute(), max_bytes), max_bytes=max_bytes)
