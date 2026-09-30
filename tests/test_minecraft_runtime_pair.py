"""Dedicated pair composition fixtures; no Minecraft or native input is run."""
from copy import deepcopy
import hmac
import http.server
import importlib
import json
from pathlib import Path
import threading
import uuid

import pytest

from kneekura_tech_hub.minecraft import runtime
from kneekura_tech_hub.minecraft.storage import ContractError, Store, canonical, key_for

REAL_OBSERVE = runtime.observe_live

PLAYER = '57e9ec72-85ae-3dd2-8fb4-2672e58b0ffe'


def api():
    return importlib.import_module('kneekura_tech_hub.minecraft.runtime_pair')


@pytest.fixture
def paired(tmp_path, monkeypatch):
    store = Store(tmp_path / 'store')
    policy = {'host': '127.0.0.1', 'port': 25565, 'player_uuids': [PLAYER]}
    common = dict(schema_version=2, profile_id='1'*64, index_snapshot_id='2'*64,
                  build_artifact_hash='3'*64, source_revision='a'*40, dirty_hash='4'*64,
                  scenario_hash='5'*64, assertion_hash='6'*64, config_hash='7'*64,
                  adapter_id='kneekura-forge-observer', adapter_version='1.0.0',
                  runtime_scope='TARGET_CODE_AND_DEPENDENCY_BYTES',dependency_inventory_hash='f'*64,
                  connection_policy=policy, connection_policy_hash=key_for(policy))
    server = dict(common, session_role='dedicated_server', physical_side='server', logical_side='server',
                  run_id=str(uuid.uuid4()), session_epoch=str(uuid.uuid4()), world_id='server-world',
                  world_seed=0, world_template_hash='8'*64, assertion_domain='server_observation')
    server_hash = store.put_json(server)
    client = dict(common, session_role='dedicated_client', physical_side='client', logical_side='client',
                  run_id=str(uuid.uuid4()), session_epoch=str(uuid.uuid4()), run_directory_id='client-directory',
                  run_directory_template_hash='9'*64, server_contract_hash=server_hash,
                  player_uuid=PLAYER, assertion_domain='client_observation',
                  profile_id='b'*64, index_snapshot_id='c'*64, dirty_hash='d'*64, config_hash='e'*64)
    paths = {}
    for name, contract in [('server', server), ('client', client)]:
        directory = tmp_path / name; directory.mkdir()
        data = {'token': 'a'*64, 'directory': str(directory), 'contract': contract,
                'expected_runtime': {'minecraft':'1.20.1','forge':'47.4.6','java_major':17},
                'connection_policy': policy, 'endpoint_path': str(directory/'endpoint.json')}
        path = directory / 'session.json'; path.write_bytes(canonical(data)); path.chmod(0o600)
        paths[name] = str(path)
    def connection(side):
        local = {'host':'127.0.0.1','port':25565}
        remote = {'host':'127.0.0.1','port':32123}
        if side == 'client': local, remote = remote, local
        return {'player_uuid':PLAYER,'connected':True,'memory':False,'channel_id':side+'-channel',
                'local':local,'remote':remote}
    def row(side):
        return {'uuid':PLAYER,'dimension':'minecraft:overworld','position':[0,65,0],
                'velocity':[0,0,0],'health':20,'target_uuid':None,
                'staff_state':{'schema_version':1,'observation_side':'logical_'+side,'applicable':True,
                    'main_hand':{'item':'kneekura:celestial_staff','count':1,'damage':0},
                    'glowing':None,'staff_cooldown':{'item':'kneekura:celestial_staff','registered':True,
                                                   'active':False,'fraction':0.0}},
                'connection':connection(side)}
    before = {'identity':server,'entities':[row('server')], 'entities_truncated':False,
              'server_tick_start':10,'server_tick_end':11,'log_sequence_start':1,'log_sequence_end':1,
              'client_frame_start':None,'client_frame_end':None,'atomic':False}
    received = {'identity':client,'entities':[row('client')],'connection':connection('client'),
                'observation_side':'logical_client','server_tick_start':None,'server_tick_end':None,
                'server_tick_scope':'NOT_LOCALLY_OBSERVED','client_tick_start':8,'client_tick_end':8,
                'client_frame_start':100,'client_frame_end':101,'log_sequence_start':1,'log_sequence_end':1,
                'atomic':False}
    after = deepcopy(before); after.update(server_tick_start=12,server_tick_end=13)
    samples = [before, received, after]
    calls = []
    def observe(store, path, *, operation, query, timeout):
        calls.append({'path':path,'operation':operation,'query':query,'timeout':timeout})
        raw = samples[len(calls)-1]
        expected = server if len(calls) != 2 else client
        hello = {'ready':True,'identity':expected,'minecraft':'1.20.1','forge':'47.4.6','java_major':17}
        return {'status':'OK','outcome':'NOT_RUN','evidence_level':'AUTHENTICATED_LIVE_OBSERVER',
                'artifact_hash':store.put_json(raw),'handshake_hash':store.put_json(hello)}
    monkeypatch.setattr(runtime, 'observe_live', observe)
    return store, paths, server, client, samples, calls


def capture(paired, **kwargs):
    store, paths, *_ = paired
    return api().observe_pair(store, server_session=paths['server'], client_session=paths['client'],
                              player_uuid=PLAYER, **kwargs)


def test_pair_preserves_distinct_identities_and_bracketed_nonatomic_evidence(paired):
    store, paths, server, client, samples, calls = paired
    result = capture(paired)
    assert result['status'] == 'OK' and result['outcome'] == 'NOT_RUN'
    record = store.json(result['artifact_hash'])
    assert record['atomic'] is False
    assert record['server_contract_hash'] == key_for(server)
    assert record['client_contract_hash'] == key_for(client)
    assert record['target_build_binding'] == 'MATCHING_RUNTIME_ARTIFACT_AND_REVISION'
    assert record['world_binding'] == {'source':'authenticated_server_contract',
                                     'world_id':server['world_id'],'world_seed':0,
                                     'world_template_hash':server['world_template_hash']}
    assert record['client_directory_id'] == client['run_directory_id']
    assert [s['role'] for s in record['samples']] == ['server_before','client','server_after']
    assert [store.json(s['artifact_hash']) for s in record['samples']] == samples
    assert [c['path'] for c in calls] == [paths['server'],paths['client'],paths['server']]
    assert [c['operation'] for c in calls] == ['observe','client','observe']
    assert all(c['query']['entity_uuids'] == [PLAYER] and c['query']['limit'] == 1 for c in calls)
    assert 0 < calls[-1]['timeout'] <= calls[0]['timeout'] <= 10
    assert record['synchronization_verdict'] == 'NOT_RUN'
    assert not any(k in record for k in ('token','session_file','directory'))


@pytest.mark.parametrize('fault', ['wrong_tuple','wrong_port','wildcard','bool_port','memory',
    'disconnected','wrong_player','changed_server_channel','changed_server_endpoint',
    'stale_server_epoch','wrong_client_build','missing_entity','truncated','copied_server_state',
    'invented_server_tick','backwards_server_tick'])
def test_pair_rejects_wrong_connection_identity_or_capture_without_retry(paired, fault):
    store, _, _, _, samples, calls = paired
    client = samples[1]
    if fault == 'wrong_tuple': client['connection']['local']['port'] = 32124
    if fault == 'wrong_port': client['connection']['remote']['port'] = 25566
    if fault == 'wildcard': client['connection']['local']['host'] = '0.0.0.0'
    if fault == 'bool_port': client['connection']['local']['port'] = True
    if fault == 'memory': client['connection']['memory'] = True
    if fault == 'disconnected': client['connection']['connected'] = False
    if fault == 'wrong_player': client['entities'][0]['uuid'] = str(uuid.uuid4())
    if fault == 'changed_server_channel': samples[2]['entities'][0]['connection']['channel_id'] = 'new-channel'
    if fault == 'changed_server_endpoint': samples[2]['entities'][0]['connection']['remote']['port'] = 32124
    if fault == 'stale_server_epoch': samples[2]['identity'] = dict(samples[2]['identity'],session_epoch=str(uuid.uuid4()))
    if fault == 'wrong_client_build': client['identity'] = dict(client['identity'],build_artifact_hash='f'*64)
    if fault == 'missing_entity': client['entities'] = []
    if fault == 'truncated': samples[0]['entities_truncated'] = True
    if fault == 'copied_server_state': client['entities'][0]['staff_state']['observation_side'] = 'logical_server'
    if fault == 'invented_server_tick': client['server_tick_start'] = client['server_tick_end'] = 12
    if fault == 'backwards_server_tick': samples[2]['server_tick_start'] = samples[2]['server_tick_end'] = 9
    with pytest.raises(ContractError): capture(paired)
    assert len(calls) <= 3
    assert not any(store.json(h).get('kind') == 'dedicated-observer-pair' for h in store.pinned_hashes())


@pytest.mark.parametrize('fault', ['reference','policy','same_run','same_epoch','same_file','artifact','revision','version','relocated'])
def test_pair_prerequisites_reject_before_live_requests(paired, fault):
    store, paths, server, client, samples, calls = paired
    path = Path(paths['client']); data = __import__('json').loads(path.read_bytes())
    if fault == 'reference': data['contract']['server_contract_hash'] = 'f'*64
    if fault == 'policy': data['contract']['connection_policy']['port'] = 25566
    if fault == 'same_run': data['contract']['run_id'] = server['run_id']
    if fault == 'same_epoch': data['contract']['session_epoch'] = server['session_epoch']
    if fault == 'same_file': paths['client'] = paths['server']
    if fault == 'artifact': data['contract']['build_artifact_hash'] = 'f'*64
    if fault == 'revision': data['contract']['source_revision'] = 'f'*40
    if fault == 'version': data['expected_runtime']['forge'] = '47.4.0'
    if fault == 'relocated': data['directory'] = str(path.parent/'other')
    path.write_bytes(canonical(data))
    with pytest.raises(ContractError): capture(paired)
    assert not calls


def test_pair_deadline_does_not_retry_or_publish_partial_pair(paired, monkeypatch):
    _, _, _, _, _, calls = paired
    clock = iter([0.0, 0.0, 0.0, 0.1, 0.1, 2.0, 2.0, 2.0])
    monkeypatch.setattr(api().time, 'monotonic', lambda: next(clock, 2.0))
    with pytest.raises(ContractError, match='deadline'):
        capture(paired, timeout=1)
    assert len(calls) < 3


@pytest.mark.parametrize('timeout', [True, 0, -1, 31, float('inf')])
def test_pair_timeout_is_bounded(paired, timeout):
    with pytest.raises(ContractError): capture(paired, timeout=timeout)


@pytest.mark.parametrize('tamper_client', [False, True])
def test_pair_uses_both_real_http_hmac_sessions_without_retry(paired, monkeypatch, tamper_client):
    store, paths, server_contract, client_contract, samples, _ = paired
    monkeypatch.setattr(runtime, 'observe_live', REAL_OBSERVE)
    servers = []; threads = []; requests = []; server_reads = []
    def handler(side, contract):
        class Peer(http.server.BaseHTTPRequestHandler):
            def do_GET(self): self.respond(True)
            def do_POST(self): self.respond(False)
            def respond(self, handshake):
                assert self.headers['Authorization'] == 'Bearer '+'a'*64
                assert self.headers['X-Kneekura-Run'] == contract['run_id']
                assert self.headers['X-Kneekura-Epoch'] == contract['session_epoch']
                requests.append((side, self.command, self.path))
                body = json.loads(self.rfile.read(int(self.headers.get('Content-Length', 0))) or b'{}')
                if handshake:
                    value = {'ready':True,'identity':contract,'minecraft':'1.20.1','forge':'47.4.6','java_major':17}
                else:
                    assert body['entity_uuids'] == [PLAYER] and body['staff_state'] is True
                    if side == 'server':
                        value = samples[0 if not server_reads else 2]; server_reads.append(True)
                    else: value = samples[1]
                raw = canonical(value)
                signature = hmac.digest(('a'*64).encode(),
                    (self.command+'\n'+self.path+'\n'+self.headers['X-Kneekura-Nonce']+'\n').encode()+raw,
                    'sha256').hex()
                if tamper_client and side == 'client' and not handshake: signature = '0'*64
                self.send_response(200); self.send_header('Content-Length', str(len(raw)))
                self.send_header('X-Kneekura-Signature',signature); self.end_headers(); self.wfile.write(raw)
            def log_message(self, *args): pass
        return Peer
    try:
        for side, contract in [('server',server_contract),('client',client_contract)]:
            peer = http.server.ThreadingHTTPServer(('127.0.0.1',0), handler(side, contract))
            servers.append(peer)
            thread = threading.Thread(target=peer.serve_forever,daemon=True); thread.start(); threads.append(thread)
            (Path(paths[side]).parent/'endpoint.json').write_text(json.dumps({'url':f'http://127.0.0.1:{peer.server_port}'}))
        if tamper_client:
            with pytest.raises(ContractError, match='Unauthenticated'):
                capture(paired)
            assert len(requests) == 4 and len(server_reads) == 1
        else:
            result = capture(paired)
            assert result['status'] == 'OK' and result['outcome'] == 'NOT_RUN'
            assert len(requests) == 6 and len(server_reads) == 2
    finally:
        for peer in servers: peer.shutdown(); peer.server_close()
        for thread in threads: thread.join(timeout=2)
