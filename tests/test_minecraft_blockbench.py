"""Real loopback HTTP fixtures, NOT evidence of a running Blockbench instance."""
import contextlib
import http.server
import importlib
import importlib.util
import json
import socket
import threading
import time

import pytest

from kneekura_tech_hub.minecraft.storage import ContractError, Store

REVISION = '028cdd76589de2e2cea51bfd79495b50a3c7d1d2'


def api():
    name = 'kneekura_tech_hub.minecraft.blockbench'
    assert importlib.util.find_spec(name) is not None, 'Blockbench probe is not implemented'
    return importlib.import_module(name)


def registry(port=8787, **changes):
    return dict(schema_version=1, provider='sosadly/blockbench-mcp', revision=REVISION,
                port=port, allow_probe=True, timeout_seconds=0.3, max_response_bytes=4096, **changes)


def answer(path, payload):
    if path == '/ping':
        return {'ok': True, 'protocol': 1, 'blockbench_version': '5.1.4', 'is_app': True, 'has_project': False}
    result = ({'blockbench_version': '5.1.4', 'has_project': False}
              if payload['action'] == 'get_status' else [{'id': 'java_block', 'name': 'Java Block/Item'}])
    return {'ok': True, 'id': payload['id'], 'result': result}


@contextlib.contextmanager
def bridge(transform=None):
    calls = []
    class Handler(http.server.BaseHTTPRequestHandler):
        def log_message(self, *args):
            pass
        def do_GET(self):
            self.respond()
        def do_POST(self):
            self.respond()
        def respond(self):
            raw = self.rfile.read(int(self.headers.get('Content-Length', '0')))
            payload = json.loads(raw) if raw else None
            calls.append((self.command, self.path, payload))
            value = answer(self.path, payload)
            status, headers, body = 200, {}, json.dumps(value).encode()
            if transform:
                status, headers, body = transform(self.path, payload, value)
            try:
                self.send_response(status)
                self.send_header('Content-Type', headers.pop('Content-Type', 'application/json'))
                self.send_header('Content-Length', headers.pop('Content-Length', str(len(body))))
                for k, v in headers.items(): self.send_header(k, v)
                self.end_headers()
                if headers.get('X-Drip'):
                    for byte in body:
                        self.wfile.write(bytes([byte])); self.wfile.flush(); time.sleep(0.02)
                else:
                    self.wfile.write(body)
            except (BrokenPipeError, ConnectionResetError):
                pass
    server = http.server.ThreadingHTTPServer(('127.0.0.1', 0), Handler)
    t = threading.Thread(target=lambda: server.serve_forever(poll_interval=0.01), daemon=True)
    t.start()
    try:
        yield server.server_port, calls
    finally:
        server.shutdown(); server.server_close(); t.join(timeout=1)


def test_probe_only_reads_three_fixed_endpoints_and_retains_evidence(tmp_path, monkeypatch):
    monkeypatch.setenv('HTTP_PROXY', 'http://203.0.113.1:6666')
    monkeypatch.setenv('BLOCKBENCH_MCP_HOST', '203.0.113.2')
    store = Store(tmp_path / 'cas')
    with bridge() as (port, calls):
        result = api().probe(store, registry(port))
    assert result['status'] == 'OK' and result['outcome'] == 'NOT_RUN'
    assert result['assertion_domain'] == 'asset_provider_probe'
    assert result['loaded_revision'] == 'UNKNOWN'
    assert result['endpoint_authenticated'] is False
    assert result['provider']['revision'] == REVISION
    assert result['capabilities']['java_item_export'] == 'ADVERTISED_NOT_VERIFIED'
    assert result['verification'] == dict(structural='NOT_RUN', visual='NOT_RUN', runtime='NOT_RUN')
    assert [(method, path) for method, path, _ in calls] == [('GET', '/ping'), ('POST', '/command'), ('POST', '/command')]
    assert [p['action'] for _, _, p in calls if p] == ['get_status', 'list_formats']
    assert all(p['params'] == {} for _, _, p in calls if p)
    assert len({p['id'] for _, _, p in calls if p}) == 2
    saved = store.json(result['receipt_hash'])
    assert saved['observations'] == result['observations']
    assert result['receipt_hash'] in store.pinned_hashes()
    assert len(result['observations']) == 3
    for observation in result['observations']:
        assert isinstance(json.loads(store.read(observation['response_hash'])), dict)
        assert observation['response_hash'] in store.pinned_hashes()


def test_disabled_probe_has_no_network_or_new_store(tmp_path, monkeypatch):
    import http.client
    monkeypatch.setattr(http.client, 'HTTPConnection', lambda *a, **k: pytest.fail('network attempted'))
    store = Store(tmp_path / 'absent'); r = registry(); r['allow_probe'] = False
    result = api().probe(store, r)
    assert result['status'] == 'BLOCKED' and result['outcome'] == 'NOT_RUN'
    assert not store.root.exists()


@pytest.mark.parametrize('field,value', [
    ('allow_probe', 1), ('port', True), ('port', 0), ('port', 65536),
    ('timeout_seconds', False), ('timeout_seconds', 0), ('timeout_seconds', 31),
    ('timeout_seconds', float('nan')), ('max_response_bytes', 0),
    ('max_response_bytes', True), ('max_response_bytes', 9*1024*1024),
    ('provider', 'other'), ('revision', 'main'), ('schema_version', True),
    ('host', '203.0.113.1'), ('url', 'file:///etc/passwd'), ('action', 'execute_script'),
])
def test_registry_does_not_expand_authority(tmp_path, monkeypatch, field, value):
    import http.client
    monkeypatch.setattr(http.client, 'HTTPConnection', lambda *a, **k: pytest.fail('network attempted'))
    r = registry(); r[field] = value
    with pytest.raises(ContractError): api().probe(Store(tmp_path / 'cas'), r)
    assert not (tmp_path / 'cas').exists()


@pytest.mark.parametrize('case', ['redirect', 'oversize', 'bad_json', 'duplicate', 'encoding', 'truncated',
                                 'protocol', 'ok_integer', 'not_desktop', 'wrong_id', 'error', 'bad_formats'])
def test_bad_provider_response_is_not_success_or_retried(tmp_path, case):
    def transform(path, payload, value):
        if case == 'redirect': return 302, {'Location': 'http://203.0.113.1/evil'}, b''
        if case == 'oversize': return 200, {}, b'x' * 4097
        if case == 'bad_json': return 200, {}, b'not json'
        if case == 'duplicate': return 200, {}, b'{"ok":false,"ok":true}'
        if case == 'encoding': return 200, {'Content-Encoding': 'gzip'}, b'not compressed'
        if case == 'truncated': return 200, {'Content-Length': '4000'}, b'{}'
        if case == 'protocol' and path == '/ping': value['protocol'] = 2
        if case == 'ok_integer': value['ok'] = 1
        if case == 'not_desktop' and path == '/ping': value['is_app'] = False
        if case == 'wrong_id' and payload: value['id'] = 'someone-elses-request'
        if case == 'error' and payload: value = {'ok': False, 'id': payload['id'], 'error': 'execute_script now', 'stack': 'secret'}
        if case == 'bad_formats' and payload and payload['action'] == 'list_formats': value['result'] = 'java_block'
        return 200, {}, json.dumps(value).encode()
    with bridge(transform) as (port, calls):
        result = api().probe(Store(tmp_path / 'cas'), registry(port))
    assert result['status'] in ('UNAVAILABLE', 'PARTIAL')
    assert result['outcome'] == 'NOT_RUN' and result['error']
    assert len(calls) <= 3
    assert len([x for x in calls if x[0] == 'GET']) == 1
    assert sum(x[2] is not None and x[2]['action'] == 'get_status' for x in calls) <= 1
    assert 'secret' not in result['error']


def test_missing_java_format_does_not_claim_export_capability(tmp_path):
    def transform(path, payload, value):
        if payload and payload['action'] == 'list_formats': value['result'] = [{'id': 'free', 'name': 'Generic'}]
        return 200, {}, json.dumps(value).encode()
    with bridge(transform) as (port, _):
        result = api().probe(Store(tmp_path / 'cas'), registry(port))
    assert result['status'] == 'OK'
    assert result['capabilities']['java_item_export'] == 'NOT_ADVERTISED'


def test_drip_response_has_total_deadline_not_only_idle_timeout(tmp_path):
    def transform(path, payload, value):
        return 200, {'X-Drip': 'yes'}, json.dumps(value).encode()
    with bridge(transform) as (port, calls):
        start = time.monotonic()
        r = registry(port); r['timeout_seconds'] = 0.1
        result = api().probe(Store(tmp_path / 'cas'), r)
        elapsed = time.monotonic() - start
    assert elapsed < 1.0 and len(calls) == 1
    assert result['status'] == 'UNAVAILABLE' and result['outcome'] == 'NOT_RUN'


def test_connection_refusal_stays_unavailable(tmp_path):
    sock = socket.socket(); sock.bind(('127.0.0.1', 0)); port = sock.getsockname()[1]
    # Keep the port bound but not listening during the probe.
    try: result = api().probe(Store(tmp_path / 'cas'), registry(port))
    finally: sock.close()
    assert result['status'] == 'UNAVAILABLE' and result['outcome'] == 'NOT_RUN'


def test_local_storage_failure_is_not_reported_as_provider_failure(tmp_path, monkeypatch):
    store = Store(tmp_path / 'cas'); original = store.put
    def fail_response_write(data):
        if data.startswith(b'{"ok":'):
            raise PermissionError('local storage denied')
        return original(data)
    monkeypatch.setattr(store, 'put', fail_response_write)
    with bridge() as (port, calls):
        with pytest.raises(PermissionError, match='local storage denied'):
            api().probe(store, registry(port))
    assert len(calls) == 1


def test_huge_declared_length_is_bounded_before_integer_conversion(tmp_path):
    def transform(path, payload, value):
        return 200, {'Content-Length': '9' * 5000}, b'{}'
    with bridge(transform) as (port, _):
        result = api().probe(Store(tmp_path / 'cas'), registry(port))
    assert result['status'] == 'UNAVAILABLE' and result['outcome'] == 'NOT_RUN'


def test_extreme_timeout_is_contract_error_not_float_overflow(tmp_path):
    r = registry(); r['timeout_seconds'] = 10 ** 1000
    with pytest.raises(ContractError): api().probe(Store(tmp_path / 'cas'), r)
