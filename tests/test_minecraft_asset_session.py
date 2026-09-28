"""Guarded M2 session/capture contract tests. Local HTTP fixture, not Blockbench."""
from __future__ import annotations

import base64
import importlib
import importlib.util
import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
import threading

import pytest

from kneekura_tech_hub.minecraft.asset_contract import PROVIDER_ID, PROVIDER_REVISION, prepare_request
from kneekura_tech_hub.minecraft.asset_guard import guard_config
from kneekura_tech_hub.minecraft.storage import ContractError, Store, capture_profile, canonical


PNG = b'\x89PNG\r\n\x1a\nfixture-png'


def api():
    name = 'kneekura_tech_hub.minecraft.asset_session'
    assert importlib.util.find_spec(name) is not None, 'guarded asset session client is not implemented'
    return importlib.import_module(name)


def files(root: Path):
    return {str(p.relative_to(root)): p.read_bytes() for p in root.rglob('*') if p.is_file()}


@pytest.fixture
def prepared(tmp_path):
    workspace = tmp_path / 'workspace'; workspace.mkdir()
    (workspace / 'Source.java').write_text('class Source {}\n')
    manifest = dict(schema_version=1, minecraft='1.20.1', loader='forge',
                    loader_version='47.4.0', java_major=17, namespace='mojmap',
                    physical_side='client', logical_side='client', track='ANCHOR',
                    workspace_revision='a'*40, dirty_hash='b'*64, toolchain={'gradle': '8.8'},
                    roots=[dict(id='own', path=str(workspace), kind='directory', scope='client',
                                role='source', namespace='mojmap', stage='workspace',
                                classloader='unknown', track='ANCHOR')])
    store = Store(tmp_path / 'cas')
    profile = capture_profile(manifest, tmp_path, store)
    spec = dict(schema_version=1, asset_id='kneekura:celestial_staff', asset_kind='java_item',
                visual_brief='Golden celestial staff with a purple accent.',
                style=dict(texture_size=[32,32], palette={'metal':'#d4af37','accent':'#864fc7'},
                           pixel_art=True, shading='minecraft'),
                reference_hashes=[], required_views=['front','left','back'])
    request = prepare_request(store, profile=profile, spec=spec)
    config = guard_config(store, request['request_hash'], allow_write=True)
    plan = dict(schema_version=1, request_hash=request['request_hash'], fill='#d4af37',
                cubes=[
                    {'name':'handle','from':[7,0,7],'to':[9,16,9],'uv':[0,0,4,4]},
                    {'name':'head','from':[5,16,6],'to':[11,20,10],'uv':[4,0,12,8]},
                ])
    return store, request['request_hash'], config, plan


class Fixture:
    def __init__(self, request_hash, token):
        self.request_hash=request_hash; self.token=token; self.requests=[]
        self.mode='ok'; self.counts={}; self.server=None; self.thread=None

    def start(self):
        state=self
        class Handler(BaseHTTPRequestHandler):
            protocol_version='HTTP/1.1'
            def log_message(self,*args): pass
            def do_POST(self):
                length=int(self.headers.get('Content-Length','0'))
                raw=self.rfile.read(length)
                payload=json.loads(raw)
                state.requests.append(payload)
                state.counts[payload.get('action')]=state.counts.get(payload.get('action'),0)+1
                if state.mode=='drop' and payload.get('action')=='kneekura_asset' and payload.get('params',{}).get('operation')=='cube':
                    self.connection.shutdown(2); self.connection.close(); return
                if state.mode=='redirect':
                    self.send_response(302); self.send_header('Location','http://example.invalid/'); self.send_header('Content-Length','0'); self.end_headers(); return
                request_id=payload.get('id')
                if state.mode=='wrong_id': request_id='wrong-id'
                try:
                    result=state.result(payload)
                    envelope={'ok':True,'id':request_id,'result':result}
                except Exception:
                    envelope={'ok':False,'id':request_id,'error':'fixture secret error'}
                data=canonical(envelope)
                self.send_response(200); self.send_header('Content-Type','application/json')
                self.send_header('Content-Length',str(len(data))); self.end_headers(); self.wfile.write(data)
        self.server=ThreadingHTTPServer(('127.0.0.1',0),Handler)
        self.thread=threading.Thread(target=self.server.serve_forever,daemon=True); self.thread.start()
        return self.server.server_address[1]

    def stop(self):
        if self.server: self.server.shutdown(); self.server.server_close()
        if self.thread: self.thread.join(timeout=2)

    def result(self,payload):
        action=payload['action']; params=payload.get('params') or {}
        if action=='kneekura_asset_status':
            return dict(guard_protocol=1,state='READY',next_sequence=0,project_uuid=None,busy=False,
                        request_hash=self.request_hash,loaded_revision='UNATTESTED',last_receipt=None)
        assert action=='kneekura_asset'
        assert params['token']==self.token and params['request_hash']==self.request_hash
        seq=params['seq']; op=params['operation']; project='project-1'
        if self.mode=='unknown' and op=='cube':
            completion='UNKNOWN'
        else:
            completion='CONFIRMED'
        if op=='begin': inner={'name':'celestial_staff','format':'java_block'}
        elif op=='texture': inner={'uuid':'tex-1'}
        elif op=='cube': inner={'uuid':'cube-'+str(seq)}
        elif op=='inspect': inner={'issue_count':0}
        elif op=='capture':
            kind=params['arguments']['kind']; view=params['arguments']['view']
            if kind=='model':
                inner=dict(kind='model',mime='application/json',encoding='utf8',
                           content='{"parent":"minecraft:item/handheld","textures":{"layer0":"kneekura:item/celestial_staff"}}')
            elif kind=='native':
                inner=dict(kind='native',mime='application/json',encoding='utf8',
                           content='{"meta":{"format_version":"4.10"},"name":"celestial_staff"}')
            elif kind=='texture':
                content=base64.b64encode(PNG).decode()
                if self.mode=='bad_png': content=base64.b64encode(b'not png').decode()
                inner=dict(kind='texture',mime='image/png',encoding='base64',content=content)
            else:
                inner=dict(kind='view',mime='image/png',encoding='base64',view=view,
                           looking_at='fixture',model_right_on='fixture',note='fixture',
                           content=base64.b64encode(PNG).decode())
        else: raise AssertionError(op)
        return dict(seq=seq,operation=op,completion=completion,project_uuid=project,
                    request_hash=self.request_hash,assertion_domain='asset_editor_operation',
                    verification=dict(structural='NOT_RUN',visual='NOT_RUN',runtime='NOT_RUN'),
                    result=inner)


def registry(port, allow=True):
    return dict(schema_version=1,provider=PROVIDER_ID,revision=PROVIDER_REVISION,port=port,
                allow_session=allow,timeout_seconds=2,max_response_bytes=1024*1024)


def run_fixture(prepared, mode='ok', allow=True):
    store,h,config,plan=prepared; server=Fixture(h,config['token']); server.mode=mode; port=server.start()
    try:
        return api().run_session(store,registry(port,allow),config,plan),server
    finally:
        server.stop()


def test_plan_validation_is_exact_request_bound_and_read_only(prepared):
    store,h,_,plan=prepared; before=files(store.root)
    out=api().validate_plan(store,h,plan)
    assert out==plan and files(store.root)==before
    for injected in [
        {**plan,'path':'../evil'},
        {**plan,'request_hash':'0'*64},
        {**plan,'fill':'#ffffff'},
        {**plan,'schema_version':True},
        {**plan,'cubes':[]},
    ]:
        with pytest.raises(ContractError): api().validate_plan(store,h,injected)
    assert files(store.root)==before


@pytest.mark.parametrize('cube',[
    {'name':'../bad','from':[0,0,0],'to':[1,1,1],'uv':[0,0,1,1]},
    {'name':'bad','from':[0,0,0],'to':[0,1,1],'uv':[0,0,1,1]},
    {'name':'bad','from':[-17,0,0],'to':[1,1,1],'uv':[0,0,1,1]},
    {'name':'bad','from':[0,0,0],'to':[1,1,1],'uv':[0,0,99,1]},
])
def test_bad_geometry_is_rejected_before_network_or_cas(prepared,cube):
    store,h,_,plan=prepared; bad={**plan,'cubes':[cube]}; before=files(store.root)
    with pytest.raises(ContractError): api().validate_plan(store,h,bad)
    assert files(store.root)==before


def test_successful_session_captures_inline_artifacts_to_existing_cas(prepared):
    store,h,config,plan=prepared; result,server=run_fixture(prepared)
    assert result['status']=='OK' and result['outcome']=='NOT_RUN'
    assert result['request_hash']==h and result['loaded_revision']=='UNATTESTED'
    assert result['verification']=={'structural':'NOT_RUN','visual':'NOT_RUN','runtime':'NOT_RUN'}
    artifacts=result['artifacts']
    assert [(a['kind'],a.get('view')) for a in artifacts]==[
        ('model',None),('native',None),('texture',None),('view','front'),('view','left'),('view','back')]
    for item in artifacts:
        raw=store.read(item['content_hash']); assert len(raw)==item['size_bytes']
        if item['kind'] in ('model','native'): assert json.loads(raw)
        else: assert raw.startswith(b'\x89PNG\r\n\x1a\n')
    receipt=store.json(result['receipt_hash'])
    assert receipt['request_hash']==h and receipt['verification']==result['verification']
    assert config['token'] not in json.dumps(receipt)
    for p in store.root.rglob('*'):
        if p.is_file(): assert config['token'].encode() not in p.read_bytes()
    operations=[r.get('params',{}).get('operation') for r in server.requests if r.get('action')=='kneekura_asset']
    assert operations==['begin','texture','cube','cube','inspect','capture','capture','capture','capture','capture','capture']
    def walk(value):
        if isinstance(value,dict):
            for k,v in value.items():
                assert k not in {'path','code','data_url'}
                walk(v)
        elif isinstance(value,list):
            for v in value: walk(v)
    for request in server.requests: walk(request)


@pytest.mark.parametrize('mode',['wrong_id','redirect','drop','unknown','bad_png'])
def test_failure_is_fail_closed_no_retry_and_no_new_evidence(prepared,mode):
    store,h,config,plan=prepared; before=files(store.root)
    server=Fixture(h,config['token']);server.mode=mode;port=server.start()
    try:
        with pytest.raises((ContractError,OSError)):
            api().run_session(store,registry(port),config,plan)
    finally: server.stop()
    assert files(store.root)==before
    if mode=='drop':
        cube=[r for r in server.requests if r.get('params',{}).get('operation')=='cube']
        assert len(cube)==1


def test_permission_and_private_config_are_checked_before_network(prepared):
    store,h,config,plan=prepared; before=files(store.root)
    with pytest.raises(ContractError): api().run_session(store,registry(9,False),config,plan)
    disabled={**config,'allow_write':False}
    with pytest.raises(ContractError): api().run_session(store,registry(9),disabled,plan)
    mismatched={**config,'request_hash':'0'*64}
    with pytest.raises(ContractError): api().run_session(store,registry(9),mismatched,plan)
    assert files(store.root)==before
