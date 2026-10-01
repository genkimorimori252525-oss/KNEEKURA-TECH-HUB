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
from .storage import ContractError, IntegrityError, Store, canonical, digest, valid_hash


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
    if not isinstance(plan, dict) or set(plan) not in (_PLAN_FIELDS, _PLAN_FIELDS | {'texture_regions'}):
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
    regions = plan.get('texture_regions', [])
    if not isinstance(regions, list) or len(regions) > 32:
        raise ContractError('Plan allows at most 32 texture regions')
    for region in regions:
        if not isinstance(region, dict) or set(region) != {'rect', 'color'}:
            raise ContractError('Each texture region has exactly rect/color')
        if not isinstance(region['color'], str) or region['color'] not in palette:
            raise ContractError('Texture region color must be in the request palette')
        rect = region['rect']
        if (not isinstance(rect, list) or len(rect) != 4
                or any(type(n) is not int for n in rect)
                or not 0 <= rect[0] < rect[2] <= width
                or not 0 <= rect[1] < rect[3] <= height):
            raise ContractError('Texture region must be an integer rectangle within the request texture')
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
            or type(value['guard_protocol']) is not int or value['guard_protocol'] != 1 or value['state'] != 'READY'
            or type(value['next_sequence']) is not int or value['next_sequence'] != 0 or value['project_uuid'] is not None
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
    if (type(value['seq']) is not int or value['seq'] != seq or value['operation'] != operation
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
    if kind in ('model', 'native'):
        if (set(value) != {'kind','mime','encoding','content'}
                or value.get('mime') != 'application/json' or value.get('encoding') != 'utf8'
                or not isinstance(value.get('content'), str)):
            raise ContractError('JSON capture envelope is invalid')
        raw = value['content'].encode('utf-8')
        parsed = decode_json(raw, max_bytes=512 * 1024)
        if not isinstance(parsed, dict):
            raise ContractError('JSON capture must be an object')
        return raw, {}
    if kind == 'texture':
        expected = {'kind','mime','encoding','content'}
    elif kind == 'view':
        expected = {'kind','mime','encoding','view','looking_at','model_right_on','note','content'}
        if 'frame' in value or 'generation' in value:
            expected |= {'frame','generation'}
            if (not isinstance(value.get('frame'),dict) or type(value.get('generation')) is not int
                    or not 0 <= value['generation'] <= 32 or len(canonical(value['frame'])) > 8192):
                raise ContractError('Invalid generation/frame capture metadata')
            _detached(value['frame'])
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
    if kind == 'view' and 'frame' in value:
        meta.update(frame=value['frame'],generation=value['generation'])
    return raw, meta


def run_session(store: Store, registry: dict, private_config: dict, plan: dict, *, retain_generation: bool = False) -> dict:
    """Run one fresh guarded session and retain evidence only after all calls finish."""
    if type(retain_generation) is not bool:
        raise ContractError('retain_generation requires an explicit boolean')
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
    from .asset_mutation import BoundedStoreView
    evidence = BoundedStoreView(store) if retain_generation else store
    p = validate_plan(evidence, request_hash, candidate)
    request, _ = load_request(evidence, request_hash)
    if retain_generation and request['asset_id'] != 'kneekura:celestial_staff':
        raise ContractError('Repair pilot is restricted to the owned Celestial Staff')

    initial = _status(_command(r, 'kneekura_asset_status',
                               {'token': config['token'], 'request_hash': request_hash}),
                      request_hash)
    loaded_revision = initial['loaded_revision']
    call = _caller(r, config, 0, None)
    call('begin', {})
    call('texture', {'fill': p['fill']})
    for region in p.get('texture_regions', []):
        call('texture_region', region)
    for cube in p['cubes']:
        call('cube', cube)
    snapshot = _snapshot_result(call('snapshot', {})['result'], request_hash, generation=0) if retain_generation else None
    inspection_receipt, captured = _capture_all(call, request)
    project_uuid = inspection_receipt['project_uuid']
    if snapshot is not None:
        _snapshot_matches_captures(snapshot[1], captured, project_uuid)
    return _persist_capture(store, request_hash, p, loaded_revision, project_uuid,
                            inspection_receipt['result'], captured, snapshot=snapshot)


def _caller(registry, config, seq, project_uuid):
    def call(operation, arguments):
        nonlocal seq, project_uuid
        params = {'token':config['token'], 'request_hash':config['request_hash'], 'seq':seq,
                  'project_uuid':project_uuid, 'operation':operation, 'arguments':arguments}
        label = 'capture:'+arguments['kind'] if operation == 'capture' else operation
        try:
            value = _command(registry, 'kneekura_asset', params)
            receipt = _receipt(value, request_hash=config['request_hash'], seq=seq,
                               operation=operation, project_uuid=project_uuid)
        except (ContractError, OSError, http.client.HTTPException):
            raise ContractError(f'Guarded operation {label} failed; completion may be UNKNOWN, do not retry') from None
        if project_uuid is None:
            project_uuid = receipt['project_uuid']
        seq += 1
        return receipt
    return call


def _snapshot_result(value, request_hash, *, generation):
    from .asset_mutation import validate_snapshot
    if (not isinstance(value,dict) or set(value) != {'kind','generation','snapshot_hash','encoding','content'}
            or value['kind'] != 'snapshot' or value['encoding'] != 'utf8' or not isinstance(value['content'],str)
            or type(value['generation']) is not int or value['generation'] != generation):
        raise ContractError('Invalid sealed snapshot response')
    raw = value['content'].encode('utf8')
    if digest(raw) != valid_hash(value['snapshot_hash']):
        raise IntegrityError('Sealed snapshot hash differs from exact response bytes')
    snapshot = validate_snapshot(decode_json(raw,max_bytes=786432))
    if snapshot['request_hash'] != request_hash or snapshot['generation'] != generation:
        raise ContractError('Sealed snapshot identity differs')
    return raw, snapshot


def _capture_all(call, request):
    inspection = call('inspect', {})
    captured = []
    for kind, view in [('model',None),('native',None),('texture',None)]+[('view',v) for v in request['required_views']]:
        result = call('capture', {'kind':kind,'view':view})['result']
        raw, meta = _capture_bytes(result,kind,view)
        captured.append((kind,view,raw,meta))
    if sum(len(item[2]) for item in captured) > 4*1024*1024:
        raise ContractError('Whole session capture exceeds four MiB')
    return inspection, captured


def _snapshot_matches_captures(snapshot, captured, project_uuid):
    from .asset_mutation import decode_png_rgba, json_equal
    if snapshot['project_uuid'] != project_uuid:
        raise ContractError('Snapshot project differs from capture')
    for kind,view,raw,meta in captured:
        if kind in ('model','native') and not json_equal(decode_json(raw,max_bytes=512*1024),snapshot[kind]):
            raise ContractError('Snapshot differs from complete captured document')
        if kind == 'texture':
            if (decode_png_rgba(raw,[snapshot['texture']['width'],snapshot['texture']['height']]) !=
                    base64.b64decode(snapshot['texture']['rgba'],validate=True) or
                    snapshot['native']['textures'][0]['source'] != 'data:image/png;base64,'+base64.b64encode(raw).decode('ascii')):
                raise ContractError('Snapshot/native/captured PNG pixels or bytes differ')
        if kind == 'view':
            if meta.get('generation') != snapshot['generation'] or not isinstance(meta.get('frame'),dict):
                raise ContractError('Sealed view lacks generation/frame metadata')
            from .asset_comparison import validate_frame
            validate_frame(meta['frame'],view)
            decode_png_rgba(raw,meta['frame']['output'])


def _persist_capture(store, request_hash, plan, loaded_revision, project_uuid, inspection,
                     captured, *, snapshot=None, parent_receipt_hash=None, mutation=None):
    # All provider calls and independent checks finish before persistence starts.
    plan_hash = store.put_json(plan)
    inspection_hash = store.put_json({'schema_version':1,'record_type':'asset_editor_inspection',
        'request_hash':request_hash,'project_uuid':project_uuid,'loaded_revision':loaded_revision,
        'result':inspection,'verification':dict(_GATES)})
    artifacts = []
    for kind,view,raw,meta in captured:
        item = {'kind':kind,'mime':'application/json' if kind in ('model','native') else 'image/png',
                'content_hash':store.put(raw),'size_bytes':len(raw)}
        if view is not None:
            item['view']=view
            item.update(meta)
        artifacts.append(item)
    receipt = {'schema_version':1,'record_type':'asset_session_capture','request_hash':request_hash,
        'plan_hash':plan_hash,'provider':provider_pin(),'guard_protocol':1,'loaded_revision':loaded_revision,
        'project_uuid':project_uuid,'inspection_hash':inspection_hash,'artifacts':artifacts,
        'verification':dict(_GATES),'outcome':'NOT_RUN'}
    extra_keys=[]
    if snapshot is not None:
        snapshot_hash=store.put(snapshot[0]); mutation_hash=store.put_json(mutation) if mutation is not None else None
        receipt.update(schema_version=2,generation=snapshot[1]['generation'],snapshot_hash=snapshot_hash,
                       parent_receipt_hash=parent_receipt_hash,mutation_hash=mutation_hash)
        extra_keys=[snapshot_hash]+([mutation_hash,parent_receipt_hash] if mutation_hash else [])
    receipt_hash=store.put_json(receipt)
    for key in [receipt_hash,request_hash,plan_hash,inspection_hash,*extra_keys,*(a['content_hash'] for a in artifacts)]:
        store.pin(key,'asset-session:'+receipt_hash)
    result={'schema_version':1,'status':'OK','outcome':'NOT_RUN','assertion_domain':'asset_session_capture',
        'request_hash':request_hash,'loaded_revision':loaded_revision,'project_uuid':project_uuid,
        'artifacts':artifacts,'inspection_hash':inspection_hash,'receipt_hash':receipt_hash,'verification':dict(_GATES)}
    if snapshot is not None:
        result.update({k:receipt[k] for k in ('generation','snapshot_hash','parent_receipt_hash','mutation_hash')})
    return result


def run_mutation(store: Store, registry: dict, private_config: dict,
                 base_receipt_hash: str, mutation: dict) -> dict:
    """One existing-project edit with exact baseline checks and no automatic retry."""
    from .asset_mutation import BoundedStoreView, MUTATION_FIELDS, json_equal, load_snapshot, validate_mutation, verify_delta
    r=_registry(registry); config=validate_config(private_config)
    if not r['allow_session'] or config['allow_write'] is not True:
        raise ContractError('Guarded mutation is not enabled')
    from .asset_export import _validate_capture
    evidence = BoundedStoreView(store)
    _validate_capture(evidence,base_receipt_hash)
    prepared=validate_mutation(evidence,base_receipt_hash,mutation)
    base,before=load_snapshot(evidence,base_receipt_hash)
    if config['request_hash'] != base['request_hash']:
        raise ContractError('Private configuration belongs to another retained request')
    request,_=load_request(evidence,base['request_hash'])
    plan=validate_plan(evidence,base['request_hash'],evidence.json(base['plan_hash'],max_bytes=1024*1024))
    status=_command(r,'kneekura_asset_status',{'token':config['token'],'request_hash':config['request_hash']})
    expected={'guard_protocol','state','next_sequence','project_uuid','busy','request_hash','loaded_revision','last_receipt'}
    if (not isinstance(status,dict) or set(status)!=expected or type(status['guard_protocol']) is not int
            or status['guard_protocol']!=1
            or status['state']!='OPEN' or status['busy'] is not False
            or type(status['next_sequence']) is not int or not 0 < status['next_sequence'] < 512
            or status['request_hash']!=base['request_hash'] or status['project_uuid']!=base['project_uuid']
            or status['loaded_revision']!='UNATTESTED' or not isinstance(status['last_receipt'],dict)
            or status['last_receipt'].get('completion')!='CONFIRMED'
            or status['last_receipt'].get('request_hash')!=base['request_hash']
            or status['last_receipt'].get('project_uuid')!=base['project_uuid']):
        raise ContractError('Retained editor is not the same confirmed OPEN project; do not retry UNKNOWN work')
    call=_caller(r,config,status['next_sequence'],base['project_uuid'])
    live=_snapshot_result(call('snapshot',{})['result'],base['request_hash'],generation=base['generation'])
    if digest(live[0])!=base['snapshot_hash'] or not json_equal(live[1],before):
        raise ContractError('Retained snapshot no longer matches the editor; no mutation sent')
    call(prepared['operation'],{k:prepared[k] for k in MUTATION_FIELDS})
    after=_snapshot_result(call('snapshot',{})['result'],base['request_hash'],generation=base['generation']+1)
    verify_delta(before,after[1],prepared)
    inspection,captured=_capture_all(call,request)
    _snapshot_matches_captures(after[1],captured,base['project_uuid'])
    return _persist_capture(store,base['request_hash'],plan,base['loaded_revision'],
        base['project_uuid'],inspection['result'],captured,snapshot=after,parent_receipt_hash=base_receipt_hash,mutation=prepared)
