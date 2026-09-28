"""Strict no-path client for one guarded Blockbench asset session.

This module does not install or launch Blockbench and never accepts filesystem
destinations, arbitrary bridge actions, scripts, or retry policies. Captured
bytes stay in memory until the whole expected session finishes, then enter the
existing CAS as evidence. A successful capture is still NOT a visual/runtime
verdict and does not attest which plugin revision is loaded in Blockbench.
"""
from __future__ import annotations

import base64
import binascii
import http.client
import math
import re
import socket
import threading
import time
import uuid
from typing import Any

from .asset_contract import PROVIDER_ID, PROVIDER_REVISION, decode_json, provider_pin
from .asset_guard import load_request, validate_config
from .storage import ContractError, IntegrityError, Store, canonical, valid_hash


_PLAN_FIELDS = {'schema_version', 'request_hash', 'fill', 'cubes'}
_CUBE_FIELDS = {'name', 'from', 'to', 'uv'}
_REGISTRY_FIELDS = {'schema_version', 'provider', 'revision', 'port', 'allow_session',
                    'timeout_seconds', 'max_response_bytes'}
_CAPTURE_VIEWS = {'front', 'left', 'right', 'back', 'top', 'bottom', 'front_right'}
_GATES = {'structural': 'NOT_RUN', 'visual': 'NOT_RUN', 'runtime': 'NOT_RUN'}


def _detached(value: Any) -> Any:
    try:
        return decode_json(canonical(value), max_bytes=1024 * 1024)
    except (TypeError, ValueError, UnicodeError, RecursionError) as exc:
        raise ContractError('Expected finite bounded JSON') from exc


def _number(value: Any, lo: float, hi: float) -> float | int:
    if type(value) not in (int, float) or not math.isfinite(value) or value < lo or value > hi:
        raise ContractError('Plan coordinate is outside the guarded numeric range')
    return value


def validate_plan(store: Store, request_hash: str, value: dict) -> dict:
    """Validate the whole geometry plan before any network or CAS mutation."""
    valid_hash(request_hash)
    request, spec = load_request(store, request_hash)
    plan = _detached(value)
    if not isinstance(plan, dict) or set(plan) != _PLAN_FIELDS:
        raise ContractError('Expected exactly the asset-session plan fields')
    if type(plan['schema_version']) is not int or plan['schema_version'] != 1:
        raise ContractError('Asset-session plan requires schema_version=1')
    if plan['request_hash'] != request_hash:
        raise ContractError('Asset-session plan belongs to a different request')
    palette = {str(v).lower() for v in spec['style']['palette'].values()}
    if (not isinstance(plan['fill'], str) or not re.fullmatch(r'#[a-f0-9]{6}', plan['fill'])
            or plan['fill'] not in palette):
        raise ContractError('Plan fill must be one of the request palette colors')
    cubes = plan['cubes']
    if not isinstance(cubes, list) or not 1 <= len(cubes) <= 128:
        raise ContractError('Plan requires 1..128 explicit cubes')
    names: set[str] = set()
    width, height = spec['style']['texture_size']
    for cube in cubes:
        if not isinstance(cube, dict) or set(cube) != _CUBE_FIELDS:
            raise ContractError('Each planned cube has exactly name/from/to/uv')
        name = cube['name']
        if (not isinstance(name, str) or not re.fullmatch(r'[a-z][a-z0-9_]{0,63}', name)
                or name in names):
            raise ContractError('Planned cube names must be unique safe identifiers')
        names.add(name)
        for key in ('from', 'to'):
            vector = cube[key]
            if not isinstance(vector, list) or len(vector) != 3:
                raise ContractError('Cube positions must be three-vectors')
            for n in vector:
                _number(n, -16, 32)
        if any(cube['from'][i] >= cube['to'][i] for i in range(3)):
            raise ContractError('Planned cube has degenerate bounds')
        uv = cube['uv']
        if not isinstance(uv, list) or len(uv) != 4:
            raise ContractError('Cube UV must be a four-vector')
        for n in uv:
            _number(n, 0, 256)
        if uv[0] >= uv[2] or uv[1] >= uv[3] or uv[2] > width or uv[3] > height:
            raise ContractError('Planned cube UV is outside the request texture')
    if not set(request['required_views']) <= _CAPTURE_VIEWS:
        raise ContractError('Request contains a view not supported by guarded M2 capture')
    return plan


def _registry(value: dict) -> dict:
    r = _detached(value)
    if not isinstance(r, dict) or set(r) != _REGISTRY_FIELDS:
        raise ContractError('Expected exactly the guarded-session registry fields')
    if (type(r['schema_version']) is not int or r['schema_version'] != 1
            or r['provider'] != PROVIDER_ID or r['revision'] != PROVIDER_REVISION
            or type(r['allow_session']) is not bool):
        raise ContractError('Pinned provider/revision and explicit allow_session are required')
    if type(r['port']) is not int or not 1 <= r['port'] <= 65535:
        raise ContractError('Guarded-session port must be 1..65535')
    if (type(r['timeout_seconds']) not in (int, float)
            or not math.isfinite(r['timeout_seconds'])
            or not 0.1 <= r['timeout_seconds'] <= 30):
        raise ContractError('Guarded-session timeout must be 0.1..30 seconds')
    if (type(r['max_response_bytes']) is not int
            or not 1024 <= r['max_response_bytes'] <= 2 * 1024 * 1024):
        raise ContractError('Guarded-session response budget must be 1KiB..2MiB')
    return r


def _read_http(registry: dict, body: bytes) -> bytes:
    """One POST, one response, one deadline. Never redirect or retry."""
    if len(body) > 1024 * 1024:
        raise ContractError('Guarded request exceeds one MiB')
    deadline = time.monotonic() + registry['timeout_seconds']
    connection = http.client.HTTPConnection('127.0.0.1', registry['port'],
                                             timeout=registry['timeout_seconds'])
    timer = None
    response = None
    try:
        connection.connect()
        sock = connection.sock
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            raise TimeoutError('Guarded-session deadline expired')

        def expire():
            try:
                sock.shutdown(socket.SHUT_RDWR)
            except OSError:
                pass

        timer = threading.Timer(remaining, expire)
        timer.daemon = True
        timer.start()
        connection.request('POST', '/command', body=body,
                           headers={'Content-Type': 'application/json', 'Connection': 'close'})
        response = connection.getresponse()
        if response.status != 200:
            raise ContractError(f'Guarded bridge HTTP status {response.status}; redirects are not followed')
        if response.getheader('Transfer-Encoding') is not None or response.getheader('Content-Encoding') is not None:
            raise ContractError('Encoded/chunked guarded responses are unsupported')
        if response.getheader('Content-Type', '').split(';')[0].strip().lower() != 'application/json':
            raise ContractError('Guarded bridge response is not JSON')
        sizes = response.headers.get_all('Content-Length', [])
        if (len(sizes) != 1 or len(sizes[0]) > 10 or not sizes[0].isascii()
                or not sizes[0].isdigit()):
            raise ContractError('One unambiguous Content-Length is required')
        size = int(sizes[0])
        if size > registry['max_response_bytes']:
            raise ContractError('Guarded bridge response exceeds byte budget')
        raw = response.read(size)
        if time.monotonic() >= deadline:
            raise TimeoutError('Guarded-session deadline expired')
        if len(raw) != size:
            raise ContractError('Truncated guarded bridge response')
        return raw
    finally:
        if timer is not None:
            timer.cancel()
            timer.join()
        if response is not None:
            response.close()
        connection.close()


def _command(registry: dict, action: str, params: dict) -> Any:
    request_id = str(uuid.uuid4())
    body = canonical({'id': request_id, 'action': action, 'params': params})
    raw = _read_http(registry, body)
    value = decode_json(raw, max_bytes=registry['max_response_bytes'])
    if not isinstance(value, dict) or value.get('ok') is not True:
        # Provider error/stack is untrusted and may contain sensitive/user data.
        raise ContractError('Guarded bridge rejected the request')
    if set(value) != {'ok', 'id', 'result'} or value['id'] != request_id:
        raise ContractError('Guarded bridge success envelope is ambiguous or mismatched')
    return value['result']


def _status(value: Any, request_hash: str) -> dict:
    expected = {'guard_protocol','state','next_sequence','project_uuid','busy',
                'request_hash','loaded_revision','last_receipt'}
    if (not isinstance(value, dict) or set(value) != expected
            or value['guard_protocol'] != 1 or value['state'] != 'READY'
            or value['next_sequence'] != 0 or value['project_uuid'] is not None
            or value['busy'] is not False or value['request_hash'] != request_hash
            or value['loaded_revision'] != 'UNATTESTED' or value['last_receipt'] is not None):
        raise ContractError('Guarded editor is not a fresh unattested READY session')
    return value


def _receipt(value: Any, *, request_hash: str, seq: int, operation: str,
             project_uuid: str | None) -> dict:
    expected = {'seq','operation','completion','project_uuid','request_hash',
                'assertion_domain','verification','result'}
    if not isinstance(value, dict) or set(value) != expected:
        raise ContractError('Guard operation receipt shape is invalid')
    if (value['seq'] != seq or value['operation'] != operation
            or value['completion'] != 'CONFIRMED'
            or value['request_hash'] != request_hash
            or value['assertion_domain'] != 'asset_editor_operation'
            or value['verification'] != _GATES):
        raise ContractError('Guard operation was not exactly confirmed')
    actual = value['project_uuid']
    if not isinstance(actual, str) or not actual:
        raise ContractError('Guard did not bind an editor project')
    if project_uuid is not None and actual != project_uuid:
        raise ContractError('Guard project identity changed during session')
    return value


def _capture_bytes(value: Any, kind: str, view: str | None) -> tuple[bytes, dict]:
    if not isinstance(value, dict) or value.get('kind') != kind:
        raise ContractError('Capture kind mismatch')
    if kind == 'model':
        if (set(value) != {'kind','mime','encoding','content'}
                or value.get('mime') != 'application/json' or value.get('encoding') != 'utf8'
                or not isinstance(value.get('content'), str)):
            raise ContractError('Model capture envelope is invalid')
        raw = value['content'].encode('utf-8')
        parsed = decode_json(raw, max_bytes=512 * 1024)
        if not isinstance(parsed, dict):
            raise ContractError('Model capture must be a JSON object')
        return raw, {}
    if kind == 'texture':
        expected = {'kind','mime','encoding','content'}
    elif kind == 'view':
        expected = {'kind','mime','encoding','view','looking_at','model_right_on','note','content'}
    else:
        raise ContractError('Unsupported capture kind')
    if (set(value) != expected or value.get('mime') != 'image/png'
            or value.get('encoding') != 'base64' or not isinstance(value.get('content'), str)):
        raise ContractError('PNG capture envelope is invalid')
    if kind == 'view':
        if value.get('view') != view:
            raise ContractError('View capture does not match the requested view')
        for field in ('looking_at','model_right_on','note'):
            if not isinstance(value.get(field), str) or len(value[field]) > 512:
                raise ContractError('View metadata is invalid')
    try:
        raw = base64.b64decode(value['content'], validate=True)
    except (ValueError, binascii.Error) as exc:
        raise ContractError('Capture contains invalid base64') from exc
    if len(raw) > 512 * 1024 or not raw.startswith(b'\x89PNG\r\n\x1a\n'):
        raise ContractError('Capture is not a bounded PNG')
    meta = ({k:value[k] for k in ('view','looking_at','model_right_on','note')}
            if kind == 'view' else {})
    return raw, meta


def run_session(store: Store, registry: dict, private_config: dict, plan: dict) -> dict:
    """Run one fresh guarded session and retain evidence only after all calls finish."""
    r = _registry(registry)
    if not r['allow_session']:
        raise ContractError('Guarded session is not enabled in the registry')
    config = validate_config(private_config)
    if config['allow_write'] is not True:
        raise ContractError('Private guard configuration has writes disabled')
    request_hash = valid_hash(config['request_hash'])
    candidate = _detached(plan)
    if not isinstance(candidate, dict) or candidate.get('request_hash') != request_hash:
        raise ContractError('Private configuration and plan request hashes differ')
    p = validate_plan(store, request_hash, candidate)
    request, _ = load_request(store, request_hash)

    initial = _status(_command(r, 'kneekura_asset_status',
                               {'token': config['token'], 'request_hash': request_hash}),
                      request_hash)
    loaded_revision = initial['loaded_revision']
    seq = 0
    project_uuid: str | None = None

    def call(operation: str, arguments: dict) -> dict:
        nonlocal seq, project_uuid
        params = {'token': config['token'], 'request_hash': request_hash, 'seq': seq,
                  'project_uuid': project_uuid, 'operation': operation, 'arguments': arguments}
        receipt = _receipt(_command(r, 'kneekura_asset', params),
                           request_hash=request_hash, seq=seq, operation=operation,
                           project_uuid=project_uuid)
        if project_uuid is None:
            project_uuid = receipt['project_uuid']
        seq += 1
        return receipt

    call('begin', {})
    call('texture', {'fill': p['fill']})
    for cube in p['cubes']:
        call('cube', cube)
    inspection = call('inspect', {})['result']

    captured: list[tuple[str, str | None, bytes, dict]] = []
    for kind, view in [('model', None), ('texture', None)]:
        result = call('capture', {'kind': kind, 'view': view})['result']
        raw, meta = _capture_bytes(result, kind, view)
        captured.append((kind, view, raw, meta))
    for view in request['required_views']:
        result = call('capture', {'kind': 'view', 'view': view})['result']
        raw, meta = _capture_bytes(result, 'view', view)
        captured.append(('view', view, raw, meta))
    if sum(len(item[2]) for item in captured) > 4 * 1024 * 1024:
        raise ContractError('Whole session capture exceeds four MiB')

    # Only now does evidence persistence begin. The secret token/request bodies
    # and base64 transport envelopes are never stored.
    plan_hash = store.put_json(p)
    inspection_record = {
        'schema_version': 1, 'record_type': 'asset_editor_inspection',
        'request_hash': request_hash, 'project_uuid': project_uuid,
        'loaded_revision': loaded_revision, 'result': inspection,
        'verification': dict(_GATES),
    }
    inspection_hash = store.put_json(inspection_record)
    artifacts = []
    for kind, view, raw, meta in captured:
        content_hash = store.put(raw)
        item = {'kind': kind, 'mime': 'application/json' if kind == 'model' else 'image/png',
                'content_hash': content_hash, 'size_bytes': len(raw)}
        if view is not None:
            item['view'] = view
            item.update(meta)
        artifacts.append(item)
    receipt = {
        'schema_version': 1, 'record_type': 'asset_session_capture',
        'request_hash': request_hash, 'plan_hash': plan_hash,
        'provider': provider_pin(), 'guard_protocol': 1,
        'loaded_revision': loaded_revision, 'project_uuid': project_uuid,
        'inspection_hash': inspection_hash, 'artifacts': artifacts,
        'verification': dict(_GATES), 'outcome': 'NOT_RUN',
    }
    receipt_hash = store.put_json(receipt)
    for key in [receipt_hash, request_hash, plan_hash, inspection_hash,
                *(item['content_hash'] for item in artifacts)]:
        store.pin(key, 'asset-session:' + receipt_hash)
    return {
        'schema_version': 1, 'status': 'OK', 'outcome': 'NOT_RUN',
        'assertion_domain': 'asset_session_capture', 'request_hash': request_hash,
        'loaded_revision': loaded_revision, 'project_uuid': project_uuid,
        'artifacts': artifacts, 'inspection_hash': inspection_hash,
        'receipt_hash': receipt_hash, 'verification': dict(_GATES),
    }
