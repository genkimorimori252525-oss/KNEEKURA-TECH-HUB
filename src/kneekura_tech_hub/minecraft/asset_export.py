"""Materialize a validated capture into a fresh, no-overwrite resource package.

This is an explicit local export, never an editor command or Forge installation.
Captured source bytes remain immutable in the existing CAS. Exported texture
references are derived solely from the already validated request's resource ID.
Structure checks do not establish visual quality, game behavior, or loaded code.
"""
from __future__ import annotations

import base64
import binascii
from copy import deepcopy
import math
import os
from pathlib import Path
import stat
import struct
import zlib

from .asset_contract import decode_json, provider_pin
from .asset_guard import ITEM_DISPLAY, JAVA_BLOCK_VERSION, load_request
from .asset_session import validate_plan
from .asset_mutation import BoundedStoreView, bounded_read, json_equal
from .storage import ContractError, Store, canonical, digest, safe_entry, valid_hash


_FACES = {'north', 'south', 'east', 'west', 'up', 'down'}
_GATES = {'structural': 'NOT_RUN', 'visual': 'NOT_RUN', 'runtime': 'NOT_RUN'}


def _require(condition, message):
    if not condition:
        raise ContractError(message)


def _numbers(value, length):
    return (isinstance(value, list) and len(value) == length and all(
        type(n) in (int, float) and math.isfinite(n) for n in value))


def _json(store, key):
    return decode_json(bounded_read(store,key,1024*1024), max_bytes=1024 * 1024)


def _png(raw: bytes, dimensions: list[int]) -> None:
    """Check complete bounded PNG framing, CRCs and decompressed scanline size."""
    _require(raw.startswith(b'\x89PNG\r\n\x1a\n') and len(raw) <= 512 * 1024, 'Invalid bounded texture PNG')
    offset = 8
    chunks = []
    payload = bytearray()
    while offset < len(raw):
        _require(offset + 12 <= len(raw), 'Truncated PNG chunk')
        size = struct.unpack('>I', raw[offset:offset + 4])[0]
        kind = raw[offset + 4:offset + 8]
        end = offset + 12 + size
        _require(end <= len(raw), 'Truncated PNG payload')
        data = raw[offset + 8:offset + 8 + size]
        crc = struct.unpack('>I', raw[offset + 8 + size:end])[0]
        _require(zlib.crc32(kind + data) & 0xffffffff == crc, 'PNG chunk CRC mismatch')
        chunks.append(kind)
        if kind == b'IHDR':
            _require(len(chunks) == 1 and size == 13, 'PNG requires one initial IHDR')
            width, height, depth, color, compression, filtering, interlace = struct.unpack('>IIBBBBB', data)
            _require([width, height] == dimensions and depth == 8 and color in (2, 6)
                     and compression == filtering == interlace == 0, 'Texture PNG format/dimensions mismatch')
        elif kind == b'IDAT':
            payload.extend(data)
        elif kind == b'IEND':
            _require(size == 0 and end == len(raw), 'PNG has trailing data or malformed IEND')
        else:
            _require(kind[:1].islower(), 'Unsupported critical PNG chunk')
        offset = end
    _require(chunks and chunks[0] == b'IHDR' and chunks[-1] == b'IEND' and b'IDAT' in chunks,
             'Incomplete PNG texture')
    expected = dimensions[1] * (1 + dimensions[0] * (4 if color == 6 else 3))
    inflater = zlib.decompressobj()
    try:
        pixels = inflater.decompress(bytes(payload), expected + 1)
    except zlib.error as exc:
        raise ContractError('Invalid compressed PNG pixels') from exc
    _require(len(pixels) == expected and inflater.eof and not inflater.unused_data and not inflater.unconsumed_tail,
             'PNG pixel size mismatch or decompression overflow')
    stride = expected // dimensions[1]
    _require(all(pixels[i] <= 4 for i in range(0, expected, stride)), 'Invalid PNG scanline filter')


def _validate_legacy_capture(store: Store, receipt: dict, *, effective_plan=None, effective_display=None):
    fields = {'schema_version', 'record_type', 'request_hash', 'plan_hash', 'provider', 'guard_protocol',
              'loaded_revision', 'project_uuid', 'inspection_hash', 'artifacts', 'verification', 'outcome'}
    _require(isinstance(receipt, dict) and set(receipt) == fields
             and type(receipt['schema_version']) is int and receipt['schema_version'] == 1
             and receipt['record_type'] == 'asset_session_capture' and receipt['provider'] == provider_pin()
             and type(receipt['guard_protocol']) is int and receipt['guard_protocol'] == 1
             and receipt['loaded_revision'] == 'UNATTESTED' and receipt['verification'] == _GATES
             and receipt['outcome'] == 'NOT_RUN' and isinstance(receipt['project_uuid'], str)
             and bool(receipt['project_uuid']), 'Invalid guarded capture receipt')
    request, spec = load_request(store, receipt['request_hash'])
    plan = validate_plan(store, receipt['request_hash'], _json(store, receipt['plan_hash']))
    if effective_plan is not None:
        plan = effective_plan
    inspection = _json(store, receipt['inspection_hash'])
    _require(isinstance(inspection, dict) and inspection.get('record_type') == 'asset_editor_inspection'
             and inspection.get('request_hash') == receipt['request_hash']
             and inspection.get('project_uuid') == receipt['project_uuid'], 'Inspection capture identity mismatch')
    inventory = receipt['artifacts']
    expected = [('model', None), ('native', None), ('texture', None)] + [('view', v) for v in request['required_views']]
    _require(isinstance(inventory, list) and len(inventory) == len(expected), 'Captured artifact inventory mismatch')
    captured = {}
    for item, pair in zip(inventory, expected):
        _require(isinstance(item, dict) and (item.get('kind'), item.get('view')) == pair,
                 'Duplicate, missing or unexpected capture')
        raw = bounded_read(store,item.get('content_hash'),512*1024)
        _require(type(item.get('size_bytes')) is int and item['size_bytes'] == len(raw) and len(raw) <= 512 * 1024,
                 'Capture size mismatch')
        expected_mime = 'application/json' if pair[0] in ('model', 'native') else 'image/png'
        _require(item.get('mime') == expected_mime, 'Capture media type mismatch')
        captured[pair] = raw
    model = decode_json(captured[('model', None)], max_bytes=512 * 1024)
    native = decode_json(captured[('native', None)], max_bytes=512 * 1024)
    texture = captured[('texture', None)]
    dimensions = spec['style']['texture_size']
    _png(texture, dimensions)
    _require(isinstance(model, dict) and model.get('format_version') == JAVA_BLOCK_VERSION
             and model.get('texture_size', [16, 16]) == dimensions, 'Export model is not the pinned 1.20.1 format')
    _require(set(model) <= {'format_version', 'credit', 'texture_size', 'textures', 'elements', 'display',
                            'gui_light', 'ambientocclusion', 'groups'}, 'Unsupported model fields')
    _require(model.get('gui_light', 'side') in ('front', 'side')
             and type(model.get('ambientocclusion', True)) is bool, 'Invalid runtime model lighting fields')
    textures = model.get('textures')
    _require(isinstance(textures, dict) and set(textures) == {'0'} and isinstance(textures['0'], str),
             'Expected one captured model texture')
    _require(isinstance(native, dict) and isinstance(native.get('meta'), dict)
             and native['meta'].get('model_format') == 'java_block'
             and native['meta'].get('box_uv', False) is False
             and native.get('java_block_version') == JAVA_BLOCK_VERSION
             and native.get('resolution') == {'width': dimensions[0], 'height': dimensions[1]},
             'Native source format/resolution mismatch')
    _require(native.get('parent', '') == '' and native.get('unhandled_root_fields', {}) == {}
             and not native.get('animations') and not native.get('variable_placeholders'),
             'Unsupported native source behavior or parent')
    nt = native.get('textures')
    _require(isinstance(nt, list) and len(nt) == 1 and isinstance(nt[0], dict)
             and nt[0].get('width') == dimensions[0] and nt[0].get('height') == dimensions[1]
             and nt[0].get('id') == '0' and not nt[0].get('path')
             and nt[0].get('uv_width', dimensions[0]) == dimensions[0]
             and nt[0].get('uv_height', dimensions[1]) == dimensions[1],
             'Native texture inventory mismatch')
    try:
        encoded = nt[0].get('source', '')
        _require(isinstance(encoded, str) and encoded.startswith('data:image/png;base64,'), 'Native texture is not embedded')
        native_texture = base64.b64decode(encoded.split(',', 1)[1], validate=True)
    except (ValueError, binascii.Error) as exc:
        raise ContractError('Invalid native texture bytes') from exc
    _require(native_texture == texture, 'Native and exported texture bytes differ')
    elements = model.get('elements')
    ne = native.get('elements')
    _require(isinstance(elements, list) and isinstance(ne, list)
             and len(elements) == len(ne) == len(plan['cubes']), 'Captured geometry count mismatch')
    uuids = [e.get('uuid') for e in ne if isinstance(e, dict)]
    _require(len(uuids) == len(ne) and all(isinstance(u, str) and u for u in uuids)
             and len(set(uuids)) == len(uuids) and native.get('groups') == []
             and native.get('outliner') == uuids, 'Native outliner must contain exactly the ungrouped captured cubes')
    for element, source, cube in zip(elements, ne, plan['cubes']):
        _require(isinstance(element, dict) and isinstance(source, dict), 'Invalid captured cube')
        for key in ('name', 'from', 'to'):
            _require(element.get(key) == source.get(key) == cube[key], 'Captured geometry differs from plan')
        for item in (element, source):
            for key in ('from', 'to'):
                _require(isinstance(item.get(key), list) and len(item[key]) == 3 and all(
                    type(n) in (int, float) and math.isfinite(n) for n in item[key]),
                    'Captured geometry must contain finite numbers')
        _require(source.get('type') == 'cube', 'Only static cube elements are supported')
        rotation = source.get('rotation', [0, 0, 0])
        _require(_numbers(rotation, 3) and rotation == [0, 0, 0]
                 and type(source.get('inflate', 0)) in (int, float) and source.get('inflate', 0) == 0
                 and source.get('rescale', False) is False and source.get('box_uv', False) is False
                 and source.get('export', True) is True
                 and source.get('shade', True) == element.get('shade', True)
                 and source.get('render_order', 'default') == 'default'
                 and source.get('light_emission', 0) == 0 and not source.get('shade_direction_override'),
                 'Native cube transforms or rendering differ from the runtime model')
        native_faces = source.get('faces')
        _require(isinstance(native_faces, dict) and set(native_faces) == _FACES, 'Native cube faces are incomplete')
        for side, face in native_faces.items():
            expected_uv = cube.get('face_uv', {}).get(side, cube['uv'])
            _require(isinstance(face, dict) and set(face) <= {'uv', 'texture', 'rotation'}
                     and _numbers(face.get('uv'), 4) and face['uv'] == expected_uv
                     and type(face.get('texture')) is int and face['texture'] == 0
                     and type(face.get('rotation', 0)) in (int, float) and face.get('rotation', 0) == 0,
                     'Native face UV or texture differs from the captured plan')
        _require(set(element) <= {'name', 'from', 'to', 'rotation', 'faces', 'shade'}, 'Unsupported cube properties')
        _require(type(element.get('shade', True)) is bool, 'Invalid runtime cube shade')
        rotation = element.get('rotation', {'angle': 0})
        _require(isinstance(rotation, dict) and rotation.get('angle') == 0, 'Unexpected cube rotation')
        faces = element.get('faces')
        _require(isinstance(faces, dict) and set(faces) == _FACES, 'All six cube faces must be captured')
        for side, face in faces.items():
            source_uv = cube.get('face_uv', {}).get(side, cube['uv'])
            uv = [source_uv[i] * 16 / dimensions[i % 2] for i in range(4)]
            _require(isinstance(face, dict) and set(face) <= {'texture', 'uv', 'rotation'}
                     and face.get('texture') == '#0' and _numbers(face.get('uv'), 4) and face['uv'] == uv
                     and face.get('rotation', 0) == 0, 'Texture reference or UV differs from plan')
    # Display fields, if present, remain bounded and must match editable source.
    display = model.get('display', {})
    _require(isinstance(display, dict) and display == native.get('display', {}) == (ITEM_DISPLAY if effective_display is None else effective_display),
             'Native/export display must match the pinned pilot transforms')
    allowed_slots = {'gui', 'ground', 'fixed', 'firstperson_righthand', 'firstperson_lefthand',
                     'thirdperson_righthand', 'thirdperson_lefthand', 'head'}
    _require(set(display) <= allowed_slots, 'Unsupported display slot')
    for transform in display.values():
        _require(isinstance(transform, dict) and set(transform) <= {'rotation', 'translation', 'scale'}, 'Invalid display transform')
        for key, vector in transform.items():
            limit = 4 if key == 'scale' else 180 if key == 'rotation' else 80
            _require(isinstance(vector, list) and len(vector) == 3 and all(
                type(n) in (int, float) and math.isfinite(n) and (-limit <= n <= limit)
                and (n > 0 if key == 'scale' else True) for n in vector), 'Unbounded display transform')
    exported = deepcopy(model)
    for key in ('format_version', 'texture_size', 'credit', 'groups'):
        exported.pop(key, None)
    namespace, path = request['asset_id'].split(':', 1)
    exported['textures'] = {'0': f'{namespace}:item/{path}'}
    for element in exported['elements']:
        element.pop('rotation', None)  # Zero-angle editor metadata has no game transform.
        for face in element['faces'].values():
            face.pop('rotation', None)
    return receipt, request, {'model': canonical(exported), 'native': captured[('native', None)], 'texture': texture}



_V2_FIELDS = {'generation','snapshot_hash','parent_receipt_hash','mutation_hash'}


def _legacy_projection(receipt):
    projected={k:v for k,v in receipt.items() if k not in _V2_FIELDS}
    projected['schema_version']=1
    return projected


def _validate_capture(store: Store, receipt_hash: str):
    receipt=_json(store,receipt_hash)
    if not isinstance(receipt,dict) or receipt.get('schema_version')!=2:
        return _validate_legacy_capture(store,receipt)
    store = BoundedStoreView(store)
    from .asset_mutation import MAX_GENERATIONS, MUTATION_FIELDS, load_snapshot, validate_mutation, verify_delta
    expected_fields={'schema_version','record_type','request_hash','plan_hash','provider','guard_protocol',
        'loaded_revision','project_uuid','inspection_hash','artifacts','verification','outcome'}|_V2_FIELDS
    chain=[];seen=set();current=receipt_hash
    for _ in range(MAX_GENERATIONS+1):
        _require(current not in seen,'Cyclic asset generation lineage');seen.add(current)
        r,snapshot=load_snapshot(store,current)
        _require(set(r)==expected_fields and type(r['schema_version']) is int and r['schema_version']==2,
                 'Invalid exact generation capture fields')
        _require(r['provider']==provider_pin() and type(r['guard_protocol']) is int and r['guard_protocol']==1
                 and r['loaded_revision']=='UNATTESTED','Generation provider identity mismatch')
        chain.append((current,r,snapshot))
        if r['generation']==0:
            _require(r['parent_receipt_hash'] is None and r['mutation_hash'] is None,'Initial generation has unexpected parent')
            _validate_legacy_capture(store,_legacy_projection(r))
            request,spec=load_request(store,r['request_hash'])
            _require(request['asset_id']=='kneekura:celestial_staff','Repair pilot is restricted to the owned Celestial Staff')
            root_plan=validate_plan(store,r['request_hash'],_json(store,r['plan_hash']))
            width,height=spec['style']['texture_size']
            expected_pixels=bytearray((bytes.fromhex(root_plan['fill'][1:])+b'\xff')*width*height)
            for region in root_plan.get('texture_regions',[]):
                x0,y0,x1,y1=region['rect'];color=bytes.fromhex(region['color'][1:])+b'\xff'
                for y in range(y0,y1):expected_pixels[(y*width+x0)*4:(y*width+x1)*4]=color*(x1-x0)
            _require(bytes(expected_pixels)==base64.b64decode(snapshot['texture']['rgba'],validate=True),
                     'Initial pixels differ from the declared plan')
            break
        valid_hash(r['parent_receipt_hash']);valid_hash(r['mutation_hash'])
        current=r['parent_receipt_hash']
    else:
        raise ContractError('Asset generation lineage exceeds the bound')
    chain.reverse()
    for (parent_hash,parent,before),(child_hash,child,after) in zip(chain,chain[1:]):
        _require(child['generation']==parent['generation']+1 and child['plan_hash']==parent['plan_hash']
                 and child['parent_receipt_hash']==parent_hash,'Stale or changed generation lineage')
        mutation=_json(store,child['mutation_hash'])
        _require(isinstance(mutation,dict),'Invalid mutation record')
        intent={k:mutation[k] for k in MUTATION_FIELDS if k in mutation}
        prepared=validate_mutation(store,parent_hash,intent)
        _require(json_equal(mutation,prepared),'Mutation record/allowlist differs from exact validated intent')
        verify_delta(before,after,prepared)
    final=chain[-1][2]
    effective=deepcopy(root_plan)
    for cube,element in zip(effective['cubes'],final['native']['elements']):
        for key in ('name','from','to'):cube[key]=deepcopy(element[key])
        cube['face_uv']={side:deepcopy(face['uv']) for side,face in element['faces'].items()}
    _,request,content=_validate_legacy_capture(store,_legacy_projection(receipt),
        effective_plan=effective,effective_display=final['native']['display'])
    return receipt,request,content

def _check_parent(parent: Path):
    path = Path(parent).absolute()
    for part in (path, *path.parents):
        mode = part.lstat()
        _require(stat.S_ISDIR(mode.st_mode) and not stat.S_ISLNK(mode.st_mode)
                 and not getattr(mode, 'st_file_attributes', 0) & 0x400, 'Export parent must contain only real directories')
    return path


def materialize_asset(store: Store, receipt_hash: str, *, parent: Path) -> dict:
    """Export only into a new generated directory under an explicit existing parent."""
    receipt_hash = valid_hash(receipt_hash)
    receipt, request, content = _validate_capture(store, receipt_hash)
    parent = _check_parent(parent)
    destination = parent / ('asset-' + receipt_hash)
    _require(not destination.exists() and not destination.is_symlink(), 'Export destination exists; overwrite prohibited')
    entries = [{'kind': kind, 'path': safe_entry(request['exports'][kind]),
                'content_hash': digest(data), 'size_bytes': len(data)} for kind, data in content.items()]
    manifest = {'schema_version': 1, 'record_type': 'asset_export', 'capture_receipt_hash': receipt_hash,
                'request_hash': receipt['request_hash'], 'profile_id': request['profile_id'], 'asset_id': request['asset_id'],
                'target': request['target'], 'loaded_revision': 'UNATTESTED', 'files': entries,
                'source_model_hash': receipt['artifacts'][0]['content_hash'],
                'derivation': 'texture_resource_id_qualified_for_exact_request',
                'verification': {'structural': 'PASS', 'visual': 'NOT_RUN', 'runtime': 'NOT_RUN'}, 'outcome': 'NOT_RUN'}
    # Validate every byte before creating the new directory. Exclusive no-follow
    # file creation never merges or replaces an existing export. Concurrent
    # hostile same-user manipulation of directory ancestors is outside this guard.
    destination.mkdir(mode=0o700, exist_ok=False)
    for item in entries:
        target = destination / item['path']
        target.parent.mkdir(parents=True, exist_ok=True)
        descriptor = os.open(target, os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, 'O_NOFOLLOW', 0), 0o600)
        with os.fdopen(descriptor, 'wb') as stream:
            stream.write(content[item['kind']]); stream.flush(); os.fsync(stream.fileno())
    with (destination / 'manifest.json').open('xb') as stream:
        stream.write(canonical(manifest)); stream.flush(); os.fsync(stream.fileno())
    for data in content.values():
        store.put(data)
    manifest_hash = store.put_json(manifest)
    for key in [manifest_hash, receipt_hash, receipt['request_hash'], *(e['content_hash'] for e in entries)]:
        store.pin(key, 'asset-export:' + manifest_hash)
    return dict(status='OK', directory=str(destination), manifest_hash=manifest_hash, files=entries,
                outcome='NOT_RUN', loaded_revision='UNATTESTED', verification=manifest['verification'])
