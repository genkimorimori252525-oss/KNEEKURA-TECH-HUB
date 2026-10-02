"""Pure, independently checked deltas for retained guarded static-item captures.

These contracts grant no editor, path, retry, plugin or runtime authority.
Snapshots preserve complete native/model fields; only an operation-derived
allowlist may differ. PNG pixels are decoded independently of the editor.
"""
from __future__ import annotations

import base64
import binascii
from copy import deepcopy
import math
import os
import stat
import re
import struct
import zlib

from .asset_contract import decode_json
from .storage import ArtifactUnavailable, ContractError, IntegrityError, Store, canonical, digest, valid_hash

FACES = ('north', 'south', 'east', 'west', 'up', 'down')
MUTATION_FIELDS = {'schema_version', 'request_hash', 'project_uuid', 'expected_generation',
                   'expected_snapshot_hash', 'operation', 'target', 'expected', 'value'}
SNAPSHOT_FIELDS = {'schema_version', 'request_hash', 'project_uuid', 'generation', 'parts',
                   'texture', 'native', 'model'}
MAX_GENERATIONS = 32


def require(value, message):
    if not value:
        raise ContractError(message)



def json_equal(a, b):
    """JSON-type-aware equality: numeric 1/1.0 agree, booleans never equal numbers."""
    if type(a) in (int,float) and type(b) in (int,float):
        return math.isfinite(a) and math.isfinite(b) and a == b
    if type(a) is not type(b):
        return False
    if isinstance(a,dict):
        return set(a)==set(b) and all(json_equal(a[k],b[k]) for k in a)
    if isinstance(a,list):
        return len(a)==len(b) and all(json_equal(x,y) for x,y in zip(a,b))
    return a == b


class BoundedStoreView:
    """Read-only bounded access to the same CAS or preloaded evidence bundle.

    Legacy request validators retain their existing decoding limits. Their
    backing reads are capped at the largest supported profile/index size;
    newer receipts, snapshots, plans and captures keep their smaller limits.
    Persistence must continue through the original Store, never this view.
    """
    def __init__(self, store):
        self._store = store._store if isinstance(store, BoundedStoreView) else store

    def read(self, key):
        return bounded_read(self._store, key, 16 * 1024 * 1024)

    def json(self, key, *, max_bytes=16 * 1024 * 1024):
        return decode_json(bounded_read(self._store, key, max_bytes), max_bytes=max_bytes)


def bounded_read(store: Store, key: str, max_bytes: int) -> bytes:
    """Bound reads, reject special files/races, and verify exact content identity."""
    valid_hash(key)
    require(type(max_bytes) is int and 0 < max_bytes <= 16 * 1024 * 1024, 'Invalid evidence byte budget')
    if isinstance(store, BoundedStoreView):
        store = store._store
    if not hasattr(store, 'blob_path'):
        # The original evidence importer supplies an already bounded in-memory
        # read-only bundle. Preserve that protocol without filesystem access.
        raw = store.read(key)
        require(isinstance(raw, bytes) and len(raw) <= max_bytes, 'Evidence exceeds bounded read')
    else:
        path = store.blob_path(key)
        try:
            if path.is_symlink() or not path.resolve().is_relative_to(store.root):
                raise IntegrityError('CAS path escapes managed storage')
            metadata = path.lstat()
            require(stat.S_ISREG(metadata.st_mode) and metadata.st_size <= max_bytes,
                    'Evidence is not a bounded regular file')
            descriptor = os.open(path, os.O_RDONLY | getattr(os, 'O_NOFOLLOW', 0)
                                 | getattr(os, 'O_NONBLOCK', 0))
            with os.fdopen(descriptor, 'rb') as stream:
                opened = os.fstat(stream.fileno())
                if (not stat.S_ISREG(opened.st_mode) or opened.st_size > max_bytes
                        or (opened.st_dev, opened.st_ino) != (metadata.st_dev, metadata.st_ino)
                        or path.is_symlink() or not path.resolve().is_relative_to(store.root)):
                    raise IntegrityError('Evidence changed before bounded reading')
                raw = stream.read(max_bytes + 1)
                after = os.fstat(stream.fileno())
            current = path.lstat()
            if (len(raw) > max_bytes or len(raw) != opened.st_size or after.st_size != opened.st_size
                    or after.st_mtime_ns != opened.st_mtime_ns or after.st_ctime_ns != opened.st_ctime_ns
                    or not stat.S_ISREG(current.st_mode)
                    or (current.st_dev, current.st_ino) != (opened.st_dev, opened.st_ino)):
                raise IntegrityError('Evidence changed during bounded reading')
        except OSError as exc:
            raise ArtifactUnavailable(f'Unavailable artifact {key}') from exc
    if digest(raw) != key:
        raise IntegrityError(f'Artifact hash mismatch: {key}')
    return raw

def _detach(value):
    try:
        return decode_json(canonical(value), max_bytes=786432)
    except (TypeError, ValueError, RecursionError) as exc:
        raise ContractError('Expected bounded finite mutation JSON') from exc


def _number(value, low, high):
    require(type(value) in (int, float) and math.isfinite(value) and low <= value <= high,
            'Mutation numeric value is outside its finite range')
    return value


def _vector(value, length, low, high):
    require(isinstance(value, list) and len(value) == length, 'Invalid mutation vector')
    for n in value:
        _number(n, low, high)
    return value


def _b64(value, length=None):
    require(isinstance(value, str) and len(value) <= 700000, 'Invalid bounded base64 data')
    try:
        raw = base64.b64decode(value, validate=True)
    except (ValueError, binascii.Error) as exc:
        raise ContractError('Invalid base64 data') from exc
    require(length is None or len(raw) == length, 'RGBA byte count mismatch')
    return raw


def decode_png_rgba(raw: bytes, dimensions: list[int]) -> bytes:
    """Decode bounded RGB/RGBA PNG filters 0..4 with complete framing/CRC checks."""
    require(isinstance(raw, bytes) and len(raw) <= 512 * 1024 and raw.startswith(b'\x89PNG\r\n\x1a\n'),
            'Invalid bounded PNG')
    require(isinstance(dimensions, list) and len(dimensions) == 2 and
            all(type(n) is int and 1 <= n <= 512 for n in dimensions), 'Invalid PNG dimensions')
    offset = 8; kinds = []; compressed = bytearray(); channels = None; ended_idat = False
    while offset < len(raw):
        require(offset + 12 <= len(raw), 'Truncated PNG framing')
        size = struct.unpack('>I', raw[offset:offset + 4])[0]
        kind = raw[offset + 4:offset + 8]; end = offset + size + 12
        require(end <= len(raw), 'Truncated PNG payload')
        data = raw[offset + 8:end - 4]
        require(zlib.crc32(kind + data) & 0xffffffff == struct.unpack('>I', raw[end - 4:end])[0],
                'PNG chunk CRC mismatch')
        require(re.fullmatch(b'[A-Za-z]{4}', kind) is not None, 'Invalid PNG chunk type')
        if kind == b'IHDR':
            require(not kinds and size == 13, 'PNG must have one initial IHDR')
            width, height, depth, color, compression, filtering, interlace = struct.unpack('>IIBBBBB', data)
            require([width, height] == dimensions and depth == 8 and color in (2, 6) and
                    compression == filtering == interlace == 0, 'Unsupported PNG format/dimensions')
            channels = 3 if color == 2 else 4
        elif kind == b'IDAT':
            require(channels is not None and not ended_idat, 'Invalid PNG IDAT ordering')
            compressed.extend(data)
        elif kind == b'IEND':
            require(size == 0 and end == len(raw), 'PNG trailing data or invalid IEND')
        elif kind == b'tRNS':
            raise ContractError('Unsupported PNG tRNS transparency')
        else:
            require(kind[:1].islower(), 'Unsupported critical PNG chunk')
            if b'IDAT' in kinds:
                ended_idat = True
        kinds.append(kind); offset = end
    require(kinds and kinds[0] == b'IHDR' and kinds[-1] == b'IEND' and b'IDAT' in kinds,
            'Incomplete PNG')
    width, height = dimensions; stride = width * channels; expected = height * (stride + 1)
    inflater = zlib.decompressobj()
    try:
        scan = inflater.decompress(bytes(compressed), expected + 1)
    except zlib.error as exc:
        raise ContractError('Invalid PNG compression') from exc
    require(len(scan) == expected and inflater.eof and not inflater.unused_data and not inflater.unconsumed_tail,
            'PNG decompression size mismatch')
    prior = bytearray(stride); output = bytearray()
    for y in range(height):
        start = y * (stride + 1); mode = scan[start]; require(mode <= 4, 'Invalid PNG filter')
        row = bytearray(scan[start + 1:start + 1 + stride])
        for i in range(stride):
            a = row[i - channels] if i >= channels else 0
            b = prior[i]; c = prior[i - channels] if i >= channels else 0
            p = a + b - c; pa, pb, pc = abs(p - a), abs(p - b), abs(p - c)
            predictor = (0, a, b, (a + b) // 2, a if pa <= pb and pa <= pc else b if pb <= pc else c)[mode]
            row[i] = (row[i] + predictor) & 255
        if channels == 4:
            output.extend(row)
        else:
            for i in range(0, stride, 3):
                output.extend(row[i:i + 3]); output.append(255)
        prior = row
    return bytes(output)


def validate_snapshot(value: dict) -> dict:
    s = _detach(value)
    require(isinstance(s, dict) and set(s) == SNAPSHOT_FIELDS and type(s['schema_version']) is int
            and s['schema_version'] == 1, 'Invalid full asset snapshot')
    valid_hash(s['request_hash'])
    require(isinstance(s['project_uuid'], str) and 1 <= len(s['project_uuid']) <= 128,
            'Invalid snapshot project identity')
    require(type(s['generation']) is int and 0 <= s['generation'] <= MAX_GENERATIONS, 'Invalid asset generation')
    parts = s['parts']; native = s['native']; model = s['model']; texture = s['texture']
    require(isinstance(parts, list) and 1 <= len(parts) <= 128 and isinstance(native, dict) and
            isinstance(model, dict), 'Invalid snapshot documents')
    require(isinstance(texture, dict) and set(texture) == {'texture_id','native_uuid','width','height','rgba'}
            and texture['texture_id'] == 'atlas' and isinstance(texture['native_uuid'], str)
            and 1 <= len(texture['native_uuid']) <= 128, 'Invalid owned texture identity')
    dims = [texture['width'], texture['height']]
    require(all(type(n) is int and 16 <= n <= 256 and n & (n - 1) == 0 for n in dims),
            'Invalid snapshot texture dimensions')
    pixels = _b64(texture['rgba'], dims[0] * dims[1] * 4)
    ne, me = native.get('elements'), model.get('elements')
    require(isinstance(ne, list) and isinstance(me, list) and len(ne) == len(me) == len(parts),
            'Snapshot part count differs')
    ids = []; uuids = []
    for part, element, exported in zip(parts, ne, me):
        require(isinstance(part, dict) and set(part) == {'part_id','native_uuid'} and
                isinstance(part['part_id'], str) and re.fullmatch(r'[a-z][a-z0-9_]{0,63}', part['part_id'])
                and isinstance(part['native_uuid'], str) and 1 <= len(part['native_uuid']) <= 128,
                'Invalid stable part binding')
        require(isinstance(element, dict) and isinstance(exported, dict) and
                element.get('uuid') == part['native_uuid'] and element.get('name') == exported.get('name') == part['part_id']
                and element.get('type') == 'cube', 'Native part identity mismatch')
        ids.append(part['part_id']); uuids.append(part['native_uuid'])
    require(len(set(ids)) == len(ids) and len(set(uuids)) == len(uuids) and native.get('outliner') == uuids,
            'Duplicate/reordered/missing part identity')
    nt = native.get('textures')
    require(isinstance(nt, list) and len(nt) == 1 and isinstance(nt[0], dict) and
            nt[0].get('uuid') == texture['native_uuid'] and [nt[0].get('width'),nt[0].get('height')] == dims,
            'Native texture identity mismatch')
    source = nt[0].get('source')
    require(isinstance(source, str) and source.startswith('data:image/png;base64,'), 'Missing native embedded PNG')
    require(decode_png_rgba(_b64(source.split(',',1)[1]), dims) == pixels, 'Native PNG and snapshot pixels differ')
    return s


def load_snapshot(store: Store, receipt_hash: str) -> tuple[dict, dict]:
    r = decode_json(bounded_read(store,receipt_hash,1024*1024), max_bytes=1024 * 1024)
    require(isinstance(r, dict) and type(r.get('schema_version')) is int and r['schema_version'] == 2
            and r.get('record_type') == 'asset_session_capture', 'A sealed schema-2 capture is required')
    require(type(r.get('generation')) is int and 0 <= r['generation'] <= MAX_GENERATIONS,
            'Invalid capture generation')
    snapshot = validate_snapshot(decode_json(bounded_read(store,r.get('snapshot_hash'),786432), max_bytes=786432))
    require(all(json_equal(r.get(k), snapshot[k]) for k in ('request_hash','project_uuid','generation')),
            'Capture and snapshot identity mismatch')
    require(r.get('verification') == {'structural':'NOT_RUN','visual':'NOT_RUN','runtime':'NOT_RUN'}
            and r.get('outcome') == 'NOT_RUN', 'Invalid capture verification claim')
    inventory = r.get('artifacts'); require(isinstance(inventory, list) and len(inventory) <= 10, 'Invalid capture inventory')
    found = {}
    for item in inventory:
        require(isinstance(item, dict), 'Invalid capture entry')
        pair = (item.get('kind'),item.get('view')); require(pair not in found, 'Duplicate capture artifact')
        raw = bounded_read(store,item.get('content_hash'),512*1024)
        require(type(item.get('size_bytes')) is int and len(raw) == item['size_bytes'] and len(raw) <= 512*1024,
                'Captured artifact size mismatch')
        found[pair] = raw
    for kind in ('native','model'):
        require((kind,None) in found and json_equal(decode_json(found[(kind,None)], max_bytes=512*1024), snapshot[kind]),
                'Full snapshot differs from captured document')
    require(('texture',None) in found and decode_png_rgba(found[('texture',None)],
            [snapshot['texture']['width'],snapshot['texture']['height']]) == _b64(snapshot['texture']['rgba']),
            'Full snapshot differs from captured texture')
    require(snapshot['native']['textures'][0]['source'] == 'data:image/png;base64,'+
            base64.b64encode(found[('texture',None)]).decode('ascii'), 'Native and captured PNG bytes differ')
    return r, snapshot


def _part(snapshot, part_id):
    matches = [i for i,p in enumerate(snapshot['parts']) if p['part_id'] == part_id]
    require(len(matches) == 1, 'Missing or duplicate stable part')
    return matches[0]


def _region(snapshot, rect):
    texture = snapshot['texture']; width, height = texture['width'], texture['height']
    require(isinstance(rect, list) and len(rect) == 4 and all(type(n) is int for n in rect)
            and 0 <= rect[0] < rect[2] <= width and 0 <= rect[1] < rect[3] <= height,
            'Invalid bounded texture rectangle')
    pixels = _b64(texture['rgba'], width*height*4)
    return b''.join(pixels[(y*width+rect[0])*4:(y*width+rect[2])*4] for y in range(rect[1],rect[3]))


def _checked_edit(before, value, palette=None):
    m = _detach(value)
    require(isinstance(m, dict) and set(m) == MUTATION_FIELDS and type(m['schema_version']) is int
            and m['schema_version'] == 1, 'Invalid exact mutation fields')
    valid_hash(m['expected_snapshot_hash'])
    require(m['request_hash'] == before['request_hash'] and m['project_uuid'] == before['project_uuid']
            and type(m['expected_generation']) is int and m['expected_generation'] == before['generation']
            and before['generation'] < MAX_GENERATIONS, 'Stale/wrong mutation identity')
    target = m['target']; op = m['operation']; val = m['value']
    require(isinstance(target, dict), 'Invalid mutation target')
    if op == 'part_edit':
        require(set(target) == {'part_id','property','axis'} and target['property'] in ('from','to')
                and type(target['axis']) is int and target['axis'] in (0,1,2), 'Invalid part field')
        i = _part(before,target['part_id']); prop = target['property']; axis = target['axis']
        _number(val,-16,32); old = before['native']['elements'][i][prop][axis]
        changed = deepcopy(before['native']['elements'][i]); changed[prop][axis] = val
        require(all(changed['from'][j] < changed['to'][j] for j in range(3)), 'Degenerate repaired cube')
        allowed = [f'parts/{target["part_id"]}/{prop}/{axis}']
    elif op == 'uv_edit':
        require(set(target) == {'part_id','face','texture_id'} and target['face'] in FACES
                and target['texture_id'] == 'atlas', 'Invalid owned face/texture')
        i = _part(before,target['part_id']); _vector(val,4,0,256)
        require(val[0] < val[2] <= before['texture']['width'] and val[1] < val[3] <= before['texture']['height'],
                'Invalid repaired UV rectangle')
        old = before['native']['elements'][i]['faces'][target['face']]['uv']
        allowed = [f'parts/{target["part_id"]}/faces/{target["face"]}/uv']
    elif op == 'texture_edit':
        require(set(target) == {'texture_id','rect'} and target['texture_id'] == 'atlas', 'Invalid texture region target')
        old = digest(_region(before,target['rect']))
        require(isinstance(val,str) and re.fullmatch(r'#[0-9a-f]{6}',val) and
                (palette is None or val in palette), 'Texture fill must use the request palette')
        new_color = bytes.fromhex(val[1:])+b'\xff'
        require(_region(before,target['rect']) != new_color*((target['rect'][2]-target['rect'][0])*(target['rect'][3]-target['rect'][1])),
                'No-op repair is not a new generation')
        allowed = ['texture/atlas/rgba/'+','.join(str(n) for n in target['rect'])]
    elif op == 'display_edit':
        require(set(target) == {'slot','property','axis'} and target['slot'] in before['native'].get('display',{})
                and target['property'] in ('rotation','translation','scale') and
                type(target['axis']) is int and target['axis'] in (0,1,2), 'Invalid existing display component')
        prop = target['property']; limit = {'rotation':180,'translation':80,'scale':4}[prop]
        _number(val,-limit,limit); require(prop != 'scale' or val > 0, 'Display scale must be positive')
        old = before['native']['display'][target['slot']].get(prop,[1,1,1] if prop=='scale' else [0,0,0])[target['axis']]
        allowed = [f'display/{target["slot"]}/{prop}/{target["axis"]}']
    else:
        raise ContractError('Mutation operation is not allowlisted')
    require(type(m['expected']) is not bool and json_equal(m['expected'],old), 'Expected old value/hash differs')
    require(val != old, 'No-op repair is not a new generation')
    return m, allowed


def validate_mutation(store: Store, base_receipt_hash: str, value: dict) -> dict:
    from .asset_guard import load_request
    store = BoundedStoreView(store)
    r, before = load_snapshot(store,base_receipt_hash)
    request, spec = load_request(store,r['request_hash'])
    require(request['asset_id'] == 'kneekura:celestial_staff', 'Repair pilot is restricted to the owned Celestial Staff')
    m, allowed = _checked_edit(before,value,{c.lower() for c in spec['style']['palette'].values()})
    require(m['expected_snapshot_hash'] == r['snapshot_hash'], 'Expected snapshot hash differs')
    return dict(m, record_type='asset_mutation', base_receipt_hash=base_receipt_hash,
                allowed_delta=allowed, resulting_generation=before['generation']+1)


def expected_snapshot(before: dict, mutation: dict) -> dict:
    """Derive the only permitted effective change; PNG encoding is checked separately."""
    source = {k:mutation[k] for k in MUTATION_FIELDS if k in mutation}
    m, allowed = _checked_edit(before,source)
    require('allowed_delta' not in mutation or mutation['allowed_delta'] == allowed, 'Expanded mutation allowlist')
    out = deepcopy(before); out['generation'] += 1; t = m['target']; op = m['operation']; val = m['value']
    if op == 'part_edit':
        i = _part(out,t['part_id'])
        for kind in ('native','model'):
            out[kind]['elements'][i][t['property']][t['axis']] = val
    elif op == 'uv_edit':
        i = _part(out,t['part_id']); out['native']['elements'][i]['faces'][t['face']]['uv'] = list(val)
        out['model']['elements'][i]['faces'][t['face']]['uv'] = [n*16/[out['texture']['width'],out['texture']['height']][j%2] for j,n in enumerate(val)]
    elif op == 'texture_edit':
        pixels = bytearray(_b64(out['texture']['rgba'])); width=out['texture']['width']; x0,y0,x1,y1=t['rect']
        color=bytes.fromhex(val[1:])+b'\xff'
        for y in range(y0,y1):
            pixels[(y*width+x0)*4:(y*width+x1)*4] = color*(x1-x0)
        out['texture']['rgba'] = base64.b64encode(pixels).decode('ascii')
    else:
        prop=t['property']; default=[1,1,1] if prop=='scale' else [0,0,0]
        for kind in ('native','model'):
            slot=out[kind]['display'][t['slot']]; vector=list(slot.get(prop,default))
            vector[t['axis']] = (val+180*15)%360-180 if prop=='rotation' else val
            if vector == default: slot.pop(prop,None)
            else: slot[prop]=vector
    return out


def verify_delta(before: dict, after: dict, mutation: dict) -> dict:
    before = validate_snapshot(before); after = validate_snapshot(after)
    expected = expected_snapshot(before,mutation)
    if mutation['operation'] == 'texture_edit':
        # validate_snapshot already independently decoded the full embedded PNG.
        # Only this pixel-verified encoding field may change with a rectangle edit.
        expected['native']['textures'][0]['source'] = after['native']['textures'][0]['source']
    require(json_equal(expected,after), 'Snapshot changed outside the exact allowed delta')
    return {'structural':'PASS','visual':'NOT_RUN','runtime':'NOT_RUN'}
