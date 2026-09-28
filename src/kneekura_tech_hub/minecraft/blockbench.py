"""Explicit read-only probe of the pinned sosadly bridge wire protocol.

This is not a generic MCP client or a sandbox for Blockbench. It cannot submit
model edits, scripts, plugin installs, file imports or exports. Loopback alone
is not authentication, and bridge replies do not attest a loaded source commit.
"""
from __future__ import annotations

import http.client
import math
import socket
import threading
import time
import uuid

from .asset_contract import PROVIDER_ID, PROVIDER_REVISION, decode_json, provider_pin
from .storage import ContractError, Store, canonical

_REGISTRY_FIELDS = {'schema_version', 'provider', 'revision', 'port', 'allow_probe',
                    'timeout_seconds', 'max_response_bytes'}


def _registry(value: dict) -> dict:
    if not isinstance(value, dict) or set(value) != _REGISTRY_FIELDS:
        raise ContractError('Expected exactly the read-only provider registry fields')
    r = dict(value)
    if (type(r['schema_version']) is not int or r['schema_version'] != 1
            or r['provider'] != PROVIDER_ID or r['revision'] != PROVIDER_REVISION
            or type(r['allow_probe']) is not bool):
        raise ContractError('Pinned provider/revision and explicit boolean allow_probe required')
    if type(r['port']) is not int or not 1 <= r['port'] <= 65535:
        raise ContractError('Port must be an integer from 1 through 65535')
    if (type(r['timeout_seconds']) not in (int, float) or not 0.1 <= r['timeout_seconds'] <= 30
            or not math.isfinite(r['timeout_seconds'])):
        raise ContractError('Per-request timeout must be 0.1..30 seconds')
    if type(r['max_response_bytes']) is not int or not 1 <= r['max_response_bytes'] <= 8 * 1024 * 1024:
        raise ContractError('Response budget must be 1..8388608 bytes')
    return r


def _read_response(r: dict, action: str, request_id: str | None) -> bytes:
    # This function itself only supports the three fixed probe operations.
    if action not in ('ping', 'get_status', 'list_formats'):
        raise ContractError('Only read-only probe operations are supported')
    method, path, body = 'GET', '/ping', None
    if action != 'ping':
        method, path = 'POST', '/command'
        body = canonical({'id': request_id, 'action': action, 'params': {}})
    deadline = time.monotonic() + r['timeout_seconds']
    connection = http.client.HTTPConnection('127.0.0.1', r['port'], timeout=r['timeout_seconds'])
    timer = None
    response = None
    try:
        connection.connect()  # Numeric loopback; no proxy/environment host overrides.
        sock = connection.sock
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            raise TimeoutError('Probe deadline expired')

        def expire():
            # Socket shutdown interrupts a slow header/body even if each byte
            # arrives before the idle timeout. It owns only this connection.
            try:
                sock.shutdown(socket.SHUT_RDWR)
            except OSError:
                pass

        timer = threading.Timer(remaining, expire)
        timer.daemon = True
        timer.start()
        connection.request(method, path, body=body,
                           headers={'Content-Type': 'application/json', 'Connection': 'close'})
        response = connection.getresponse()
        if response.status != 200:
            raise ContractError(f'Bridge HTTP status {response.status}; redirects are not followed')
        if response.getheader('Transfer-Encoding') is not None or response.getheader('Content-Encoding') is not None:
            raise ContractError('Encoded/chunked bridge responses are unsupported')
        if response.getheader('Content-Type', '').split(';')[0].strip().lower() != 'application/json':
            raise ContractError('Bridge response is not JSON')
        sizes = response.headers.get_all('Content-Length', [])
        if len(sizes) != 1 or len(sizes[0]) > 10 or not sizes[0].isascii() or not sizes[0].isdigit():
            raise ContractError('One unambiguous Content-Length is required')
        size = int(sizes[0])
        if size > r['max_response_bytes']:
            raise ContractError('Bridge response exceeds byte budget')
        raw = response.read(size)
        if time.monotonic() >= deadline:
            raise TimeoutError('Probe deadline expired')
        if len(raw) != size:
            raise ContractError('Truncated bridge response')
        return raw
    finally:
        if timer is not None:
            timer.cancel()
            timer.join()
        if response is not None:
            response.close()
        connection.close()


def _envelope(value, request_id: str | None):
    if not isinstance(value, dict) or value.get('ok') is not True:
        # Provider error/stack text is untrusted, retained only as local raw
        # evidence, never interpreted as instructions or echoed as trusted help.
        raise ContractError('Bridge rejected the request or returned an invalid success envelope')
    if request_id is not None and value.get('id') != request_id:
        raise ContractError('Bridge response request ID mismatch')


def probe(store: Store, registry: dict) -> dict:
    """Observe advertised capabilities; never launch, mutate, retry or mark quality PASS."""
    r = _registry(registry)
    result = {
        'schema_version': 1, 'assertion_domain': 'asset_provider_probe',
        'provider': provider_pin(), 'loaded_revision': 'UNKNOWN',
        'endpoint_authenticated': False, 'outcome': 'NOT_RUN',
        'verification': dict(structural='NOT_RUN', visual='NOT_RUN', runtime='NOT_RUN'),
        'capabilities': {'java_item_export': 'UNKNOWN'}, 'observations': [],
    }
    if not r['allow_probe']:
        return dict(result, status='BLOCKED', error='Read-only probe is not enabled in the registry')
    probe_id = str(uuid.uuid4())
    result.update(probe_id=probe_id, status='OK', error=None)
    result['endpoint'] = {'host': '127.0.0.1', 'port': r['port']}
    ping_version = None
    for number, action in enumerate(('ping', 'get_status', 'list_formats')):
        request_id = None if action == 'ping' else f'{probe_id}-{number}'
        try:
            raw = _read_response(r, action, request_id)
        except (ContractError, OSError, http.client.HTTPException) as exc:
            result['status'] = 'PARTIAL' if number > 0 else 'UNAVAILABLE'
            result['error'] = str(exc) if isinstance(exc, ContractError) else f'Bridge transport failed: {type(exc).__name__}'
            break
        # Storage failures belong to the local evidence layer, not the provider.
        raw_hash = store.put(raw)
        result['observations'].append({'action': action, 'request_id': request_id,
                                       'response_hash': raw_hash})
        try:
            value = decode_json(raw, max_bytes=r['max_response_bytes'])
            _envelope(value, request_id)
            if action == 'ping':
                if (type(value.get('protocol')) is not int or value['protocol'] != 1
                        or value.get('is_app') is not True
                        or not isinstance(value.get('blockbench_version'), str)
                        or not value['blockbench_version']):
                    raise ContractError('Expected desktop bridge protocol 1')
                ping_version = value['blockbench_version']
            elif action == 'get_status':
                state = value.get('result')
                if (not isinstance(state, dict) or type(state.get('has_project')) is not bool
                        or state.get('blockbench_version') != ping_version):
                    raise ContractError('Bridge status is invalid or changed version during probe')
            else:
                formats = value.get('result')
                if (not isinstance(formats, list) or len(formats) > 1024
                        or any(not isinstance(f, dict) or not isinstance(f.get('id'), str)
                               or not f['id'] or len(f['id']) > 128 for f in formats)):
                    raise ContractError('Bridge formats must be a bounded array of named format records')
                java = any(f['id'] == 'java_block' for f in formats)
                result['capabilities']['java_item_export'] = 'ADVERTISED_NOT_VERIFIED' if java else 'NOT_ADVERTISED'
        except ContractError as exc:
            result['status'] = 'PARTIAL' if number > 0 else 'UNAVAILABLE'
            result['error'] = str(exc)
            break
    h = store.put_json(result)
    for ref in [h, *(row['response_hash'] for row in result['observations'])]:
        store.pin(ref, 'asset-probe:' + h)
    return dict(result, receipt_hash=h)
