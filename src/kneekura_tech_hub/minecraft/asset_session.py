"""Opt-in sealed Blockbench pilot. No install, launch, arbitrary script or path RPC.

The generated bundle and local session.json contain a secret. They must stay in
an isolated local editor directory, not the knowledge CAS, Git or CI artifacts.
The provider enforces project/command guards. This is not an OS sandbox and a
session response does not attest the editor's loaded source bytes.
"""
from __future__ import annotations

import argparse
import base64
import hashlib
import http.client
import os
from pathlib import Path
import re
import secrets
import socket
import tempfile
import threading
import time

from .asset_artifacts import (MAX_BYTES, _data_png, capture_exports, load_request,
                              texture_png, validate_blueprint)
from .asset_contract import PLUGIN_GIT_BLOB, decode_json, provider_pin
from .storage import ContractError, Store, canonical, digest, valid_hash

UPSTREAM_LICENSE = 'MIT License\n\nCopyright (c) 2026 sosadly\n\nPermission is hereby granted, free of charge, to any person obtaining a copy\nof this software and associated documentation files (the "Software"), to deal\nin the Software without restriction, including without limitation the rights\nto use, copy, modify, merge, publish, distribute, sublicense, and/or sell\ncopies of the Software, and to permit persons to whom the Software is\nfurnished to do so, subject to the following conditions:\n\nThe above copyright notice and this permission notice shall be included in all\ncopies or substantial portions of the Software.\n\nTHE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR\nIMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,\nFITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE\nAUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER\nLIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,\nOUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE\nSOFTWARE.\n'

SESSION_FIELDS = {'schema_version', 'provider', 'session_id', 'request_hash', 'blueprint_hash',
                  'token', 'port', 'bundle_sha256'}
DISPATCH = """async function dispatch(action, params) {
\tconst handler = commands[action];
\tif (!handler) throw new Error('Unknown command: ' + action);
\tconst start = Date.now();
\ttry {
\t\tconst result = await handler(params || {});
\t\tlogActivity(action, true, Date.now() - start);
\t\treturn result;
\t} catch (err) {
\t\tlogActivity(action, false, Date.now() - start);
\t\tthrow err;
\t}
}"""


def _regular(path: Path, limit: int) -> bytes:
    _scope(path)
    if not path.is_file():
        raise ContractError('Expected a regular local file')
    with path.open('rb') as stream:
        data = stream.read(limit + 1)
    if len(data) > limit:
        raise ContractError('Local file budget exceeded')
    return data


def _scope(path: Path):
    if any(p.is_symlink() for p in (path, *path.parents)):
        raise ContractError('Symlinked session paths are unsupported')


def _exclusive(path: Path, data: bytes):
    _scope(path)
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(fd, 'wb') as stream:
        stream.write(data); stream.flush(); os.fsync(stream.fileno())


def _compose(source: str, config: dict) -> bytes:
    """Private source transformation; caller MUST verify the complete Git blob first."""
    guard = Path(__file__).with_name('blockbench_guard.js').read_text(encoding='utf-8')
    host = Path(__file__).with_name('blockbench_host.js').read_text(encoding='utf-8')
    text = canonical(config).decode('utf-8').replace('\u2028', '\\u2028').replace('\u2029', '\\u2029')
    injected = (guard + '\n' + host + '\nconst kneekuraConfig = ' + text + ';\n'
        "const kneekuraDispatch = createAssetGuard(kneekuraConfig, createAssetHost(kneekuraConfig));\n"
        "for (const action of ['execute_script','install_plugin','uninstall_plugin',"
        "'save_project','export_project','export_model','load_project']) {\n"
        "  commands[action] = () => { throw new Error('Disabled in the sealed asset pilot'); };\n}\n"
        "async function dispatch(action, params) { return kneekuraDispatch(action, params); }")
    replacements = {
        DISPATCH: injected,
        "const PLUGIN_ID = 'blockbench_mcp';": "const PLUGIN_ID = 'kneekura_asset_pilot';",
        'const DEFAULT_PORT = 8787;': f"const DEFAULT_PORT = {config['port']};",
        'const MAX_BODY = 96 * 1024 * 1024;': 'const MAX_BODY = 8192;',
        'return !setting || setting.value !== false;': 'return false; /* sealed pilot: never allow scripts */',
    }
    for old, new in replacements.items():
        if source.count(old) != 1:
            raise ContractError('Pinned-source patch anchor is missing or ambiguous')
        source = source.replace(old, new)
    if source.count('__BLOCKBENCH_MCP__') != 2:
        raise ContractError('Unexpected shared upstream global')
    source = source.replace('__BLOCKBENCH_MCP__', '__KNEEKURA_ASSET_PILOT__')
    return ('/*\n' + UPSTREAM_LICENSE + '\n*/\n' + source).encode('utf-8')


def stage_session(store: Store, *, request_hash: str, blueprint: dict, upstream_plugin: Path,
                  parent: Path, port: int = 8790) -> dict:
    """Create a NEW local bundle only. Never installs, loads or starts Blockbench."""
    bound = load_request(store, request_hash)
    b = validate_blueprint(bound['spec'], blueprint)
    if type(port) is not int or not 1 <= port <= 65535:
        raise ContractError('Port must be an integer in 1..65535')
    parent = Path(parent).absolute(); _scope(parent)
    if not parent.is_dir():
        raise ContractError('An existing local staging parent is required')
    if parent.resolve().is_relative_to(store.root) or any(
            (directory / '.git').exists() for directory in (parent, *parent.parents)):
        raise ContractError('Credential-bearing sessions must stay outside Git and CAS')
    raw = _regular(Path(upstream_plugin), 2 * 1024 * 1024)
    git_blob = hashlib.sha1(b'blob ' + str(len(raw)).encode() + b'\0' + raw).hexdigest()
    if git_blob != PLUGIN_GIT_BLOB:
        raise ContractError('Full upstream plugin bytes do not match the selected Git blob')
    session_id, token = secrets.token_hex(16), secrets.token_hex(32)
    config = dict(session_id=session_id, token=token, request_hash=request_hash,
        asset_id=bound['spec']['asset_id'], texture_size=bound['spec']['style']['texture_size'],
        blueprint=b, texture_data_url='data:image/png;base64,' + base64.b64encode(texture_png(bound['spec'], b)).decode(),
        required_views=bound['spec']['required_views'], timeout_ms=30000, port=port)
    try:
        bundle = _compose(raw.decode('utf-8'), config)
    except UnicodeError as exc:
        raise ContractError('Pinned plugin is not UTF-8') from exc
    folder = Path(tempfile.mkdtemp(prefix='asset-', dir=parent))
    # This directory is new. On a partial failure retain it for inspection, never
    # remove another process's file or try the mutation again automatically.
    _exclusive(folder / 'guarded_blockbench.js', bundle)
    bh = store.put_json(b)
    descriptor = dict(schema_version=1, provider=provider_pin(), session_id=session_id,
        request_hash=request_hash, blueprint_hash=bh, token=token, port=port, bundle_sha256=digest(bundle))
    _exclusive(folder / 'session.json', canonical(descriptor))
    store.pin(bh, 'asset-session:' + session_id)
    return dict(status='OK', outcome='NOT_RUN', session_file=str(folder / 'session.json'),
                bundle_sha256=digest(bundle), session_id=session_id,
                warning='Local session files contain credentials. Do not publish or install in your normal editor.')


def _load(store, session_file):
    path = Path(session_file).absolute()
    d = decode_json(_regular(path, 65536))
    if (not isinstance(d, dict) or set(d) != SESSION_FIELDS
            or type(d['schema_version']) is not int or d['schema_version'] != 1 or d['provider'] != provider_pin()
            or not isinstance(d['token'], str) or not re.fullmatch(r'[a-zA-Z0-9_-]{64}', d['token'])
            or not isinstance(d['session_id'], str) or not re.fullmatch(r'[a-zA-Z0-9_-]{32}', d['session_id'])
            or type(d['port']) is not int or not 1 <= d['port'] <= 65535):
        raise ContractError('Invalid local session descriptor')
    if digest(_regular(path.parent / 'guarded_blockbench.js', 4 * 1024 * 1024)) != valid_hash(d['bundle_sha256']):
        raise ContractError('Staged plugin bundle drifted')
    bound = load_request(store, d['request_hash'])
    b = validate_blueprint(bound['spec'], store.json(d['blueprint_hash']))
    for name in ('attempt.json', 'exports'):
        if (path.parent / name).exists() or (path.parent / name).is_symlink():
            raise ContractError('Session was attempted or output already exists; do not retry')
    return path.parent, d, b


def _rpc(port, action, params, *, timeout=35):
    if action not in ('kneekura_asset_status', 'kneekura_asset_build'):
        raise ContractError('Only sealed session RPCs are supported')
    rpc_id = secrets.token_hex(16)
    payload = canonical(dict(id=rpc_id, action=action, params=params))
    connection = http.client.HTTPConnection('127.0.0.1', port, timeout=timeout)
    timer = response = None; deadline = time.monotonic() + timeout
    try:
        connection.connect(); sock = connection.sock
        def expire():
            try: sock.shutdown(socket.SHUT_RDWR)
            except OSError: pass
        timer = threading.Timer(max(0, deadline-time.monotonic()), expire); timer.daemon=True; timer.start()
        connection.request('POST', '/command', body=payload,
            headers={'Content-Type':'application/json','Connection':'close'})
        response = connection.getresponse()
        lengths = response.headers.get_all('Content-Length', [])
        if (response.status != 200 or len(lengths) != 1 or not re.fullmatch(r'[0-9]{1,10}', lengths[0])
                or int(lengths[0]) > MAX_BYTES or response.getheader('Transfer-Encoding') is not None
                or response.getheader('Content-Encoding') is not None
                or response.getheader('Content-Type', '').split(';')[0].strip().lower() != 'application/json'):
            raise ContractError('Invalid bounded bridge response')
        size = int(lengths[0]); raw = response.read(size)
        if len(raw) != size or time.monotonic() >= deadline:
            raise ContractError('Truncated or timed-out bridge response')
        if params['token'].encode() in raw:
            raise ContractError('Bridge echoed credential material')
        value = decode_json(raw, max_bytes=MAX_BYTES)
        if (not isinstance(value, dict) or set(value) != {'ok', 'id', 'result'}
                or value['ok'] is not True or value['id'] != rpc_id or not isinstance(value['result'], dict)):
            raise ContractError('Invalid or rejected bridge envelope')
        return value['result']
    finally:
        if timer is not None: timer.cancel(); timer.join()
        if response is not None: response.close()
        connection.close()


def _identity(result, d, epoch=None, operation_id=None):
    if (result.get('session_id') != d['session_id'] or result.get('request_hash') != d['request_hash']
            or not isinstance(result.get('epoch'), str) or not re.fullmatch(r'[a-zA-Z0-9_-]{32,64}', result['epoch'])
            or (epoch is not None and result['epoch'] != epoch) or result.get('operation_id') != operation_id):
        raise ContractError('Session/generation/operation identity mismatch')


def execute_session(store: Store, session_file: Path, *, allow_run: bool = False) -> dict:
    """One explicit authenticated attempt; persistent marker prevents blind replay."""
    verification = dict(structural='NOT_RUN', visual='NOT_RUN', runtime='NOT_RUN')
    if allow_run is not True:
        return dict(status='BLOCKED', outcome='NOT_RUN', verification=verification)
    folder, d, b = _load(store, session_file)
    auth = {k:d[k] for k in ('token','session_id','request_hash')}
    try:
        ready = _rpc(d['port'], 'kneekura_asset_status', auth, timeout=5)
        _identity(ready, d)
        if ready.get('phase') != 'READY': raise ContractError('Session is not ready')
    except (ContractError, OSError, http.client.HTTPException):
        return dict(status='UNAVAILABLE', outcome='NOT_RUN', verification=verification)
    operation_id = secrets.token_hex(16)
    attempt = dict(schema_version=1, session_id=d['session_id'], request_hash=d['request_hash'],
                   epoch=ready['epoch'], operation_id=operation_id, outcome='UNKNOWN',
                   bundle_sha256=d['bundle_sha256'], blueprint_hash=d['blueprint_hash'])
    # Exclusive creation is the inter-process claim and survives an uncertain HTTP result.
    _exclusive(folder / 'attempt.json', canonical(attempt))
    result = dict(attempt, status='UNKNOWN', verification=verification, loaded_code_attestation='UNKNOWN')
    try:
        reply = _rpc(d['port'], 'kneekura_asset_build', dict(auth, epoch=ready['epoch'], operation_id=operation_id))
        _identity(reply, d, ready['epoch'], operation_id)
        if reply.get('phase') != 'EXPORTED_NOT_REVIEWED': raise ContractError('No completed byte export')
        if not isinstance(reply.get('model'), str) or not isinstance(reply.get('native'), str) or not isinstance(reply.get('views'), dict):
            raise ContractError('Missing export bytes')
        data = dict(model=reply['model'].encode('utf-8'), native=reply['native'].encode('utf-8'),
                    texture=_data_png(reply.get('texture')), views={k:_data_png(v) for k,v in reply['views'].items()})
        captured = capture_exports(store, request_hash=d['request_hash'], blueprint=b, exports=data)
        record = store.json(captured['artifact_hash'])
        root = folder / 'exports'; root.mkdir(mode=0o700)
        for role, row in record['files'].items():
            dest = root / row['path']; _scope(dest)
            dest.parent.mkdir(parents=True, exist_ok=True)
            _exclusive(dest, store.read(row['content_hash']))
        review = root / 'review'; review.mkdir()
        for view, row in record['views'].items():
            _exclusive(review / (view + '.png'), store.read(row['content_hash']))
        result.update(status='OK', outcome='EXPORTED_NOT_REVIEWED', artifact_hash=captured['artifact_hash'],
                      verification=captured['verification'])
    except (ContractError, OSError, UnicodeError, http.client.HTTPException):
        result['error'] = 'Write completion/export validation is unknown; inspect this session; never retry automatically'
    receipt = store.put_json(result)
    store.pin(receipt, 'asset-session:' + d['session_id'])
    _exclusive(folder / 'result.json', canonical(dict(result, receipt_hash=receipt)))
    return dict(result, receipt_hash=receipt)


def main(argv=None):
    parser = argparse.ArgumentParser(description='Stage or explicitly execute one sealed Blockbench asset session.')
    parser.add_argument('--store', required=True)
    subs = parser.add_subparsers(dest='operation', required=True)
    stage = subs.add_parser('stage'); stage.add_argument('--request', required=True)
    stage.add_argument('--blueprint', required=True); stage.add_argument('--upstream-plugin', required=True)
    stage.add_argument('--parent', required=True); stage.add_argument('--port', type=int, default=8790)
    run = subs.add_parser('run'); run.add_argument('--session', required=True)
    run.add_argument('--allow-run', action='store_true')
    try:
        args = parser.parse_args(argv); store = Store(args.store)
        if args.operation == 'stage':
            result = stage_session(store, request_hash=args.request,
                blueprint=decode_json(_regular(Path(args.blueprint), 256*1024), max_bytes=256*1024),
                upstream_plugin=Path(args.upstream_plugin), parent=Path(args.parent), port=args.port)
        else:
            result = execute_session(store, Path(args.session), allow_run=args.allow_run)
        print(canonical(result).decode()); return 0 if result['status']=='OK' else 3
    except (ContractError, OSError, UnicodeError):
        print(canonical(dict(status='ERROR', outcome='NOT_RUN', error='Local asset-session input/storage error')).decode())
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
