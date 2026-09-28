"""Bounded static-item export capture. Structural evidence is not visual approval.

Only one texture, axis-aligned cubes and explicit display transforms are supported.
Bytes are validated before any CAS writes. This module never opens an editor,
loads a model into Blockbench, evaluates expressions, or writes resource paths.
"""
from __future__ import annotations

import base64
import math
import re
import struct
import zlib

from .asset_contract import (_detached, _profile, _resource_id, decode_json,
                             provider_pin, validate_spec)
from .storage import ContractError, Store, canonical, key_for

FACES = ('north', 'south', 'east', 'west', 'up', 'down')
PALETTE_DIGITS = '0123456789abcdefghijklmnopqrstuv'
DISPLAY_SLOTS = {'gui', 'ground', 'fixed', 'head', 'firstperson_righthand',
                 'firstperson_lefthand', 'thirdperson_righthand', 'thirdperson_lefthand'}
REQUIRED_DISPLAY = {'gui', 'firstperson_righthand', 'thirdperson_righthand'}
MAX_BYTES = 8 * 1024 * 1024


def _need(condition, message):
    if not condition:
        raise ContractError(message)


def _vector(value, count, low, high, *, integer=False):
    return (isinstance(value, list) and len(value) == count
            and all(type(n) in ((int,) if integer else (int, float))
                    and low <= n <= high and math.isfinite(n) for n in value))


def validate_blueprint(spec: dict, blueprint: dict) -> dict:
    """Pure sealed-plan validation; text never becomes script or path authority."""
    s, b = validate_spec(spec), _detached(blueprint)
    _need(isinstance(b, dict) and set(b) == {'schema_version', 'texture_rows', 'cubes', 'display'},
          'Expected exactly the static blueprint fields')
    _need(type(b['schema_version']) is int and b['schema_version'] == 1,
          'Expected blueprint schema 1')
    _need(len(canonical(b)) <= 256 * 1024, 'Blueprint byte budget exceeded')
    w, h = s['style']['texture_size']
    rows = b['texture_rows']; alphabet = PALETTE_DIGITS[:len(s['style']['palette'])]
    _need(isinstance(rows, list) and len(rows) == h and all(
        isinstance(row, str) and len(row) == w and set(row) <= set(alphabet) for row in rows),
        'Texture rows must contain exactly the declared palette pixels')
    cubes = b['cubes']
    _need(isinstance(cubes, list) and 1 <= len(cubes) <= 128, 'Expected 1..128 cubes')
    names = set()
    for c in cubes:
        _need(isinstance(c, dict) and set(c) == {'name', 'from', 'to', 'uv'},
              'Only named axis-aligned cubes with explicit UV are supported')
        name = c['name']
        _need(isinstance(name, str) and re.fullmatch(r'[a-z][a-z0-9_]{0,63}', name)
              and name not in names, 'Cube names must be safe and distinct')
        names.add(name)
        _need(_vector(c['from'], 3, -16, 32) and _vector(c['to'], 3, -16, 32)
              and all(a < z for a, z in zip(c['from'], c['to'])), 'Invalid cube bounds')
        uv = c['uv']
        _need(_vector(uv, 4, 0, max(w, h), integer=True)
              and 0 <= uv[0] < uv[2] <= w and 0 <= uv[1] < uv[3] <= h,
              'UV rectangle is outside the texture or degenerate')
    display = b['display']
    _need(isinstance(display, dict) and REQUIRED_DISPLAY <= set(display) <= DISPLAY_SLOTS,
          'Required display slots are missing or unsupported')
    for d in display.values():
        _need(isinstance(d, dict) and set(d) == {'rotation', 'translation', 'scale'}
              and _vector(d['rotation'], 3, -180, 180)
              and _vector(d['translation'], 3, -80, 80)
              and _vector(d['scale'], 3, 0.01, 4), 'Invalid display transform')
    return b


def load_request(store: Store, request_hash: str) -> dict:
    """Reconstruct all M1 bindings without writing/pinning anything on a read."""
    r = store.json(request_hash)
    _need(isinstance(r, dict), 'Expected an asset request')
    p = _profile(store.json(r.get('profile_record_hash')))
    s = validate_spec(store.json(r.get('spec_hash')))
    style = store.json(r.get('style_hash'))
    _need(style == s['style'], 'Style does not match the specification')
    ns, path = _resource_id(s['asset_id'])
    expected = dict(schema_version=1, record_type='asset_request', asset_id=s['asset_id'],
        asset_kind=s['asset_kind'], profile_id=p['profile_id'],
        profile_record_hash=key_for(p), spec_hash=key_for(s), style_hash=key_for(style),
        reference_hashes=s['reference_hashes'], provider=provider_pin(),
        target={k: p['manifest'][k] for k in ('minecraft', 'loader', 'loader_version', 'java_major', 'track')},
        exports={'native': f'source/{ns}/{path}.bbmodel',
                 'model': f'assets/{ns}/models/item/{path}.json',
                 'texture': f'assets/{ns}/textures/item/{path}.png'},
        required_views=s['required_views'])
    if 'index_snapshot_id' in r:
        ix = store.json(r['index_snapshot_id'])
        _need(isinstance(ix, dict) and type(ix.get('schema_version')) is int
              and ix['schema_version'] == 1 and ix.get('profile') == p and 'bytecode' in ix,
              'Index does not bind the captured profile')
        expected['index_snapshot_id'] = r['index_snapshot_id']
    _need(canonical(r) == canonical(expected), 'Request identity or derived fields were changed')
    for ref in s['reference_hashes']:
        store.read(ref)
    return {'request': r, 'spec': s, 'profile': p}


def png_rgba(data: bytes, *, max_dimension: int = 512) -> tuple[int, int, bytes]:
    """Decode bounded RGBA8 PNGs, checking CRC, framing and decompression budget.

    Browser canvas PNGs use RGBA8. Other color/interlace modes are deliberately
    unsupported rather than guessed. No image metadata is executed or retained.
    """
    _need(isinstance(data, bytes) and 0 < len(data) <= MAX_BYTES
          and data.startswith(b'\x89PNG\r\n\x1a\n'), 'Expected a bounded PNG')
    offset = 8; kinds = []; compressed = bytearray(); width = height = 0
    while offset < len(data):
        _need(offset + 12 <= len(data), 'Truncated PNG chunk')
        length = struct.unpack_from('>I', data, offset)[0]
        kind = data[offset + 4:offset + 8]; end = offset + 12 + length
        _need(end <= len(data), 'Truncated PNG payload')
        body = data[offset + 8:end - 4]
        crc = struct.unpack_from('>I', data, end - 4)[0]
        _need(zlib.crc32(kind + body) == crc, 'PNG CRC mismatch')
        if kind == b'IHDR':
            _need(not kinds and length == 13, 'Invalid PNG header order/size')
            width, height, depth, color, comp, filt, interlace = struct.unpack('>IIBBBBB', body)
            _need(0 < width <= max_dimension and 0 < height <= max_dimension
                  and (depth, color, comp, filt, interlace) == (8, 6, 0, 0, 0),
                  'Only bounded noninterlaced RGBA8 PNGs are supported')
        elif kind == b'IDAT':
            _need(kinds and kinds[0] == b'IHDR' and b'IEND' not in kinds,
                  'Invalid PNG data order')
            _need(not compressed or kinds[-1] == b'IDAT', 'Noncontiguous PNG data')
            compressed.extend(body)
        elif kind == b'IEND':
            _need(length == 0 and compressed and end == len(data), 'Invalid PNG end/trailing data')
        else:
            # Color-space hints from browser encoders are inert. No text/profile payloads.
            _need(kind in (b'sRGB', b'gAMA', b'cHRM', b'pHYs') and length <= 32
                  and kinds and b'IDAT' not in kinds, 'Unsupported PNG chunk')
        kinds.append(kind); offset = end
    _need(kinds and kinds[-1] == b'IEND', 'Missing PNG end')
    expected = height * (1 + width * 4)
    try:
        decoder = zlib.decompressobj()
        raw = decoder.decompress(bytes(compressed), expected + 1)
        _need(len(raw) == expected and decoder.eof and not decoder.unused_data
              and not decoder.unconsumed_tail, 'PNG decompression size/stream mismatch')
    except zlib.error as exc:
        raise ContractError('Invalid PNG compressed data') from exc
    stride = width * 4; previous = bytearray(stride); pixels = bytearray()
    for row in range(height):
        start = row * (stride + 1); mode = raw[start]
        _need(mode in range(5), 'Unsupported PNG filter')
        current = bytearray(raw[start + 1:start + 1 + stride])
        for x in range(stride):
            left = current[x - 4] if x >= 4 else 0
            up = previous[x]; ul = previous[x - 4] if x >= 4 else 0
            if mode == 1: predictor = left
            elif mode == 2: predictor = up
            elif mode == 3: predictor = (left + up) // 2
            elif mode == 4:
                p = left + up - ul; distances = (abs(p-left), abs(p-up), abs(p-ul))
                predictor = (left, up, ul)[distances.index(min(distances))]
            else: predictor = 0
            current[x] = (current[x] + predictor) & 255
        pixels.extend(current); previous = current
    return width, height, bytes(pixels)


def blueprint_pixels(spec: dict, blueprint: dict) -> bytes:
    palette = [bytes.fromhex(color[1:]) + b'\xff'
               for _, color in sorted(spec['style']['palette'].items())]
    return b''.join(palette[PALETTE_DIGITS.index(c)] for row in blueprint['texture_rows'] for c in row)


def texture_png(spec: dict, blueprint: dict) -> bytes:
    """Encode the sealed pixel grid; no generative image or hidden palette changes."""
    b = validate_blueprint(spec, blueprint); w, h = spec['style']['texture_size']
    pixels = blueprint_pixels(spec, b); stride = w * 4
    def chunk(kind, body):
        return struct.pack('>I', len(body)) + kind + body + struct.pack('>I', zlib.crc32(kind + body))
    raw = b''.join(b'\0' + pixels[y * stride:(y + 1) * stride] for y in range(h))
    return (b'\x89PNG\r\n\x1a\n' + chunk(b'IHDR', struct.pack('>IIBBBBB', w, h, 8, 6, 0, 0, 0))
            + chunk(b'IDAT', zlib.compress(raw)) + chunk(b'IEND', b''))


def _data_png(value):
    prefix = 'data:image/png;base64,'
    _need(isinstance(value, str) and value.startswith(prefix) and len(value) <= 12 * 1024 * 1024,
          'Expected an embedded PNG, not a path or URL')
    try:
        return base64.b64decode(value[len(prefix):], validate=True)
    except (ValueError, UnicodeError) as exc:
        raise ContractError('Invalid embedded PNG encoding') from exc


def _geometry(elements, b, *, native, texture_id, size):
    _need(isinstance(elements, list) and len(elements) == len(b['cubes']), 'Cube count changed')
    ids = []
    for e, c in zip(elements, b['cubes']):
        _need(isinstance(e, dict), 'Expected cube object')
        allowed = {'from', 'to', 'faces', 'name', 'shade'}
        if native:
            allowed |= {'type', 'uuid', 'origin', 'rotation', 'inflate', 'box_uv', 'uv_offset',
                        'autouv', 'visibility', 'locked', 'export', 'render_order', 'color', 'mirror_uv', 'rescale', 'light_emission'}
        _need(set(e) <= allowed and _vector(e.get('from'), 3, -16, 32) and _vector(e.get('to'), 3, -16, 32)
              and e.get('from') == c['from'] and e.get('to') == c['to'],
              'Unexpected geometry or exporter feature')
        _need(e.get('shade', True) is True, 'Unexpected shading override')
        if native:
            _need(e.get('type') == 'cube' and e.get('name') == c['name']
                  and isinstance(e.get('uuid'), str) and 0 < len(e['uuid']) <= 128,
                  'Native element identity is invalid')
            _need(e.get('rotation', [0, 0, 0]) == [0, 0, 0]
                  and e.get('inflate', 0) == 0 and not e.get('box_uv', False)
                  and e.get('export', True) is True and e.get('visibility', True) is True
                  and e.get('mirror_uv', False) is False and e.get('rescale', False) is False
                  and e.get('light_emission', 0) == 0,
                  'Native cube has unsupported transforms or visibility')
            ids.append(e['uuid'])
        faces = e.get('faces')
        _need(isinstance(faces, dict) and set(faces) == set(FACES), 'All six faces are required')
        uv = c['uv'] if native else [c['uv'][i] * 16 / size[i % 2] for i in range(4)]
        for f in faces.values():
            _need(isinstance(f, dict) and set(f) <= {'uv', 'texture', 'rotation', 'cullface', 'tintindex', 'enabled'}
                  and _vector(f.get('uv'), 4, 0, max(size) if native else 16)
                  and f.get('uv') == uv and type(f.get('texture')) is type(texture_id)
                  and f.get('texture') == texture_id
                  and f.get('rotation', 0) == 0 and f.get('cullface', '') == ''
                  and f.get('tintindex', -1) == -1 and f.get('enabled', True) is True,
                  'Face texture/UV or rendering flags differ from the blueprint')
    _need(len(ids) == len(set(ids)), 'Duplicate native cube identity')
    return ids


def _display(value, expected):
    _need(isinstance(value, dict) and set(value) == set(expected), 'Display slots changed')
    for slot, d in value.items():
        _need(isinstance(d, dict) and set(d) <= {'rotation', 'translation', 'scale'}, 'Unsupported display field')
        # Vanilla/Blockbench codecs omit default transforms.
        normalized = dict(rotation=d.get('rotation', [0, 0, 0]),
                          translation=d.get('translation', [0, 0, 0]), scale=d.get('scale', [1, 1, 1]))
        _need(normalized == expected[slot], 'Display transform differs from the blueprint')


def capture_exports(store: Store, *, request_hash: str, blueprint: dict, exports: dict) -> dict:
    """Capture an independently supplied export; no origin/aesthetic/runtime attestation."""
    bound = load_request(store, request_hash); r, s = bound['request'], bound['spec']
    b = validate_blueprint(s, blueprint)
    _need(isinstance(exports, dict) and set(exports) == {'model', 'native', 'texture', 'views'},
          'Exactly three export roles and required views must be supplied')
    m = decode_json(exports['model'], max_bytes=MAX_BYTES)
    n = decode_json(exports['native'], max_bytes=MAX_BYTES)
    image = png_rgba(exports['texture'], max_dimension=256)
    _need(image == (*s['style']['texture_size'], blueprint_pixels(s, b)), 'Exported pixels differ from the plan')
    ns, path = _resource_id(r['asset_id']); texture_link = ns + ':item/' + path
    _need(isinstance(m, dict) and set(m) <= {'textures', 'elements', 'display', 'texture_size', 'gui_light', 'credit'}
          and m.get('gui_light', 'side') == 'side', 'Unsupported Java model root')
    tex = m.get('textures')
    _need(isinstance(tex, dict) and set(tex) in ({'0'}, {'0', 'particle'})
          and all(v == texture_link for v in tex.values()), 'Java texture references are inconsistent')
    _need(m.get('texture_size', s['style']['texture_size']) == s['style']['texture_size'], 'Java texture size changed')
    _display(m.get('display'), b['display'])
    _geometry(m.get('elements'), b, native=False, texture_id='#0', size=s['style']['texture_size'])
    _need(isinstance(n, dict) and set(n) <= {'meta', 'name', 'model_identifier', 'visible_box', 'resolution',
          'elements', 'outliner', 'textures', 'display', 'variable_placeholders', 'credit', 'box_uv',
          'groups', 'overrides', 'parent', 'front_gui_light', 'ambientocclusion', 'unhandled_root_fields'},
          'Unsupported native model root')
    _need(isinstance(n.get('meta'), dict) and n['meta'].get('model_format') == 'java_block'
          and not n.get('variable_placeholders', '') and n.get('box_uv', False) is False
          and n['meta'].get('box_uv', False) is False
          and isinstance(n['meta'].get('format_version'), str)
          and re.fullmatch(r'[45]\.\d{1,2}', n['meta']['format_version'])
          and n.get('groups', []) == [] and n.get('overrides', []) == [] and n.get('parent', '') == ''
          and n.get('front_gui_light', False) is False and n.get('ambientocclusion', True) is True
          and n.get('unhandled_root_fields', {}) == {},
          'Native model must be a static Java item')
    w, h = s['style']['texture_size']
    _need(n.get('resolution') == {'width': w, 'height': h}, 'Native texture size changed')
    textures = n.get('textures')
    _need(isinstance(textures, list) and len(textures) == 1 and isinstance(textures[0], dict),
          'Native model needs exactly one embedded texture')
    t = textures[0]
    _need(t.get('render_mode', 'default') == 'default' and not t.get('layers')
          and t.get('uv_width', w) == w and t.get('uv_height', h) == h
          and t.get('width', w) == w and t.get('height', h) == h,
          'Native texture rendering/layers/resolution differ from the plan')
    _need(not t.get('path') and not t.get('relative_path') and t.get('namespace') == ns
          and t.get('folder') == 'item' + ('/' + path.rsplit('/', 1)[0] if '/' in path else '')
          and t.get('name') == path.rsplit('/', 1)[-1] + '.png', 'Native texture path/identity is unsafe')
    _need(png_rgba(_data_png(t.get('source')), max_dimension=256) == image,
          'Native and exported texture pixels differ')
    _display(n.get('display'), b['display'])
    ids = _geometry(n.get('elements'), b, native=True, texture_id=0, size=s['style']['texture_size'])
    _need(n.get('outliner') == ids, 'Unexpected native hierarchy/element order')
    views = exports['views']
    _need(isinstance(views, dict) and set(views) == set(r['required_views']), 'Required views do not match')
    for data in views.values():
        width, height, _ = png_rgba(data)
        _need(16 <= width <= 512 and 16 <= height <= 512, 'Invalid screenshot dimensions')
    # All parsing/consistency checks above precede the first write below.
    record = dict(schema_version=1, record_type='asset_artifact', request_hash=request_hash,
        blueprint_hash=store.put_json(b), provider=r['provider'],
        origin_verification='UNVERIFIED_EXPORT_BYTES',
        verification=dict(structural='PASS', visual='NOT_RUN', runtime='NOT_RUN'),
        files={role: dict(path=path, content_hash=store.put(exports[role]), size=len(exports[role]))
               for role, path in r['exports'].items()},
        views={view: dict(content_hash=store.put(data), size=len(data)) for view, data in views.items()})
    artifact_hash = store.put_json(record)
    for h in [artifact_hash, request_hash, record['blueprint_hash'],
              *(x['content_hash'] for x in record['files'].values()),
              *(x['content_hash'] for x in record['views'].values())]:
        store.pin(h, 'asset-artifact:' + artifact_hash)
    return dict(status='OK', artifact_hash=artifact_hash, verification=record['verification'],
                origin_verification=record['origin_verification'])
