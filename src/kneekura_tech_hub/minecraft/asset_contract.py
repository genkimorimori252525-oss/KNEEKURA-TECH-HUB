"""Pure asset requests, bound to the existing captured profile and evidence CAS.

An asset request is a plan, not permission to execute an editor and not evidence
that geometry, rendering or game behavior works. No third-party code runs here.
"""
from __future__ import annotations

import json
import re
from typing import Any

from .storage import ContractError, IntegrityError, Store, canonical, key_for, valid_hash

PROVIDER_ID = 'sosadly/blockbench-mcp'
PROVIDER_REVISION = '028cdd76589de2e2cea51bfd79495b50a3c7d1d2'
PLUGIN_GIT_BLOB = '898f811f15c0bb6cb7eed08f9d994ba3b0131e74'
_SPEC_FIELDS = {'schema_version', 'asset_id', 'asset_kind', 'visual_brief', 'style',
                'reference_hashes', 'required_views'}
_STYLE_FIELDS = {'texture_size', 'palette', 'pixel_art', 'shading'}
_VIEWS = {'front', 'left', 'right', 'back', 'top', 'bottom', 'isometric'}
_DEVICES = {'con', 'prn', 'aux', 'nul'} | {f'{prefix}{i}' for prefix in ('com', 'lpt') for i in range(1, 10)}


def _detached(value: Any) -> Any:
    try:
        return json.loads(canonical(value))
    except (TypeError, ValueError, RecursionError) as exc:
        raise ContractError('Expected finite, serializable JSON data') from exc


def decode_json(data: bytes, *, max_bytes: int = 65536) -> Any:
    """Bound JSON input and reject duplicate keys and non-finite numbers."""
    if type(max_bytes) is not int or max_bytes <= 0 or not isinstance(data, bytes) or len(data) > max_bytes:
        raise ContractError('JSON byte limit exceeded or invalid byte input')

    def pairs(items):
        result = {}
        for k, v in items:
            if k in result:
                raise ContractError('Duplicate JSON object key')
            result[k] = v
        return result

    def constant(_):
        raise ContractError('Non-finite JSON number')

    try:
        value = json.loads(data.decode('utf-8'), object_pairs_hook=pairs, parse_constant=constant)
        return _detached(value)  # Also rejects overflowing exponents (1e999).
    except (UnicodeError, ValueError, TypeError, RecursionError) as exc:
        raise ContractError('Invalid, ambiguous or non-finite JSON') from exc


def provider_pin() -> dict:
    """Reviewed source identity; not attestation of the plugin loaded in an editor."""
    return {'id': PROVIDER_ID, 'revision': PROVIDER_REVISION,
            'plugin_git_blob': PLUGIN_GIT_BLOB}


def _resource_id(value: Any) -> tuple[str, str]:
    if not isinstance(value, str) or len(value) > 240 or value.count(':') != 1:
        raise ContractError('Expected a bounded namespaced asset ID')
    namespace, path = value.split(':')
    for component in [namespace, *path.split('/')]:
        if (not re.fullmatch(r'[a-z0-9_.-]+', component)
                or component in ('.', '..') or component.endswith('.')
                or component.split('.')[0] in _DEVICES):
            raise ContractError('Asset ID contains an unsafe or nonportable component')
    return namespace, path


def validate_spec(value: dict) -> dict:
    """Validate the v1 static Java-item scope, without IO or caller mutation."""
    s = _detached(value)
    if not isinstance(s, dict) or set(s) != _SPEC_FIELDS or len(canonical(s)) > 65536:
        raise ContractError('Expected exactly the bounded asset-spec v1 fields')
    if type(s['schema_version']) is not int or s['schema_version'] != 1 or s['asset_kind'] != 'java_item':
        raise ContractError('Only schema_version=1 and static java_item assets are supported')
    _resource_id(s['asset_id'])
    brief = s['visual_brief']
    if not isinstance(brief, str) or not brief.strip() or len(brief) > 8192:
        raise ContractError('A nonempty visual brief of at most 8192 characters is required')
    style = s['style']
    if not isinstance(style, dict) or set(style) != _STYLE_FIELDS:
        raise ContractError('Expected exactly the style profile fields')
    size = style['texture_size']
    if (not isinstance(size, list) or len(size) != 2
            or any(type(n) is not int or n < 16 or n > 256 or n & (n - 1) for n in size)):
        raise ContractError('Texture dimensions must be powers of two from 16 through 256')
    palette = style['palette']
    if (not isinstance(palette, dict) or not 1 <= len(palette) <= 32
            or any(not re.fullmatch(r'[a-z][a-z0-9_]{0,31}', k)
                   or not isinstance(v, str) or not re.fullmatch(r'#[0-9a-fA-F]{6}', v)
                   for k, v in palette.items())):
        raise ContractError('Palette requires 1..32 named six-digit RGB colors')
    if style['pixel_art'] is not True or style['shading'] not in ('minecraft', 'flat'):
        raise ContractError('Explicit pixel_art=true and minecraft/flat shading required')
    views = s['required_views']
    if (not isinstance(views, list) or not all(isinstance(v, str) for v in views)
            or len(views) != len(set(views)) or not set(views) <= _VIEWS
            or not {'front', 'left', 'back'} <= set(views)):
        raise ContractError('Distinct supported views including front, left and back required')
    refs = s['reference_hashes']
    if not isinstance(refs, list) or len(refs) > 8:
        raise ContractError('At most eight explicit CAS reference hashes are supported')
    for ref in refs:
        valid_hash(ref)
    if len(refs) != len(set(refs)):
        raise ContractError('Reference hashes must be distinct')
    return s


def _profile(value: dict) -> dict:
    p = _detached(value)
    if not isinstance(p, dict):
        raise ContractError('A captured ProjectProfile object is required')
    identity = valid_hash(p.get('profile_id'))
    if p.get('profile_hash') != identity:
        raise IntegrityError('Profile identity aliases disagree')
    payload = {k: v for k, v in p.items() if k not in ('profile_id', 'profile_hash')}
    if key_for(payload) != identity:
        raise IntegrityError('Captured profile bytes do not match their identity')
    manifest = p.get('manifest')
    coverage = p.get('coverage')
    if (type(p.get('schema_version')) is not int or p['schema_version'] != 1
            or p.get('identity_status') != 'PINNED'
            or not isinstance(coverage, dict) or coverage.get('complete') is not True
            or not isinstance(manifest, dict)):
        raise ContractError('A complete pinned ProjectProfile is required')
    if (manifest.get('track') != 'ANCHOR' or manifest.get('minecraft') != '1.20.1'
            or manifest.get('loader') != 'forge' or type(manifest.get('java_major')) is not int
            or manifest['java_major'] != 17
            or not isinstance(manifest.get('loader_version'), str)
            or not re.fullmatch(r'47\.\d+\.\d+', manifest['loader_version'])):
        raise ContractError('Exact Forge 47.x.y / Minecraft 1.20.1 / Java 17 ANCHOR required')
    return p


def prepare_request(store: Store, *, profile: dict, spec: dict, index_id: str | None = None) -> dict:
    """Pin an inert, deterministic request using existing storage, not a second DB."""
    s = validate_spec(spec)
    p = _profile(profile)
    if index_id is not None:
        snapshot = store.json(index_id)
        if (not isinstance(snapshot, dict) or type(snapshot.get('schema_version')) is not int
                or snapshot['schema_version'] != 1 or 'profile' not in snapshot
                or 'bytecode' not in snapshot):
            raise ContractError('Artifact is not an index snapshot')
        if snapshot['profile'] != p:
            raise IntegrityError('Index belongs to a different captured profile')
    # Preflight all reference bytes before any new request data is written.
    for ref in s['reference_hashes']:
        store.read(ref)
    namespace, path = _resource_id(s['asset_id'])
    m = p['manifest']
    r = {
        'schema_version': 1, 'record_type': 'asset_request',
        'asset_id': s['asset_id'], 'asset_kind': s['asset_kind'],
        'profile_id': p['profile_id'], 'profile_record_hash': store.put_json(p),
        'spec_hash': store.put_json(s), 'style_hash': store.put_json(s['style']),
        'reference_hashes': s['reference_hashes'], 'provider': provider_pin(),
        'target': {k: m[k] for k in ('minecraft', 'loader', 'loader_version', 'java_major', 'track')},
        'exports': {
            'native': f'source/{namespace}/{path}.bbmodel',
            'model': f'assets/{namespace}/models/item/{path}.json',
            'texture': f'assets/{namespace}/textures/item/{path}.png',
        },
        'required_views': s['required_views'],
    }
    if index_id is not None:
        r['index_snapshot_id'] = index_id
    h = store.put_json(r)
    for ref in [h, r['profile_record_hash'], r['spec_hash'], r['style_hash'], *s['reference_hashes'], *([index_id] if index_id else [])]:
        store.pin(ref, 'asset-request:' + h)
    return {'schema_version': 1, 'status': 'OK', 'outcome': 'NOT_RUN',
            'assertion_domain': 'asset_request_preparation', 'request_hash': h, 'request': r,
            'verification': dict(structural='NOT_RUN', visual='NOT_RUN', runtime='NOT_RUN')}
