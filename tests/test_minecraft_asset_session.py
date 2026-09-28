"""Authenticated loopback and file fixtures; not real Blockbench acceptance."""
from __future__ import annotations
import base64
import importlib
import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
import subprocess
import threading

import pytest
from kneekura_tech_hub.minecraft.asset_contract import provider_pin
from kneekura_tech_hub.minecraft.storage import ContractError, canonical, digest
from test_minecraft_asset_artifacts import request, blueprint, exports


def api():
    name='kneekura_tech_hub.minecraft.asset_session'
    assert importlib.util.find_spec(name), 'The asset-session path has not been implemented'
    return importlib.import_module(name)


def local_session(tmp_path, store, rh, port):
    """Trusted local registry fixture, never represented as a generated/live bundle."""
    folder=tmp_path/'session'; folder.mkdir(mode=0o700)
    raw=b'// protocol fixture, not a real editor plugin\n'
    (folder/'guarded_blockbench.js').write_bytes(raw)
    b=blueprint(); bh=store.put_json(b)
    descriptor=dict(schema_version=1,provider=provider_pin(),session_id='s'*32,request_hash=rh,
                    blueprint_hash=bh,token='t'*64,port=port,bundle_sha256=digest(raw))
    (folder/'session.json').write_bytes(canonical(descriptor))
    return folder/'session.json', descriptor


class Bridge:
    def __init__(self, rh, behavior='normal'):
        self.calls=[]; self.rh=rh; self.behavior=behavior
        outer=self
        class Handler(BaseHTTPRequestHandler):
            def log_message(self, *args): pass
            def do_POST(self):
                body=json.loads(self.rfile.read(int(self.headers['Content-Length'])))
                outer.calls.append(body)
                p=body['params']; action=body['action']
                response=dict(session_id=p['session_id'],request_hash=outer.rh,epoch='e'*32,
                              operation_id=None,phase='READY',verification=dict(structural='NOT_RUN',visual='NOT_RUN',runtime='NOT_RUN'))
                if action=='kneekura_asset_build':
                    if outer.behavior=='disconnect': self.connection.close(); return
                    data=exports()
                    response.update(phase='EXPORTED_NOT_REVIEWED',operation_id=p['operation_id'],
                        model=data['model'].decode(),native=data['native'].decode(),
                        texture='data:image/png;base64,'+base64.b64encode(data['texture']).decode(),
                        views={k:'data:image/png;base64,'+base64.b64encode(v).decode() for k,v in data['views'].items()})
                    if outer.behavior=='wrong_operation': response['operation_id']='wrong'
                    if outer.behavior=='invalid_export': response['model']='{}'
                    if outer.behavior=='token_echo': response['model']=p['token']
                if outer.behavior=='wrong_epoch': response['epoch']='wrong'
                if outer.behavior=='wrong_request': response['request_hash']='f'*64
                envelope=dict(ok=True,id=body['id'],result=response)
                if outer.behavior=='wrong_id': envelope['id']='wrong'
                raw=canonical(envelope)
                self.send_response(302 if outer.behavior=='redirect' else 200)
                self.send_header('Content-Type','application/json'); self.send_header('Content-Length',str(len(raw)))
                self.end_headers(); self.wfile.write(raw)
        self.server=ThreadingHTTPServer(('127.0.0.1',0),Handler)
        self.thread=threading.Thread(target=self.server.serve_forever,daemon=True)
    def __enter__(self): self.thread.start(); return self
    def __exit__(self,*args): self.server.shutdown(); self.server.server_close(); self.thread.join()
    @property
    def port(self): return self.server.server_address[1]


def test_default_off_never_contacts_the_editor(tmp_path):
    store,rh,_=request(tmp_path)
    with Bridge(rh) as bridge:
        path,d=local_session(tmp_path,store,rh,bridge.port)
        out=api().execute_session(store,path)
        assert out['status']=='BLOCKED' and bridge.calls==[]
        assert not (path.parent/'attempt.json').exists()


def test_one_correlated_build_captures_and_writes_exports_without_token_leak(tmp_path):
    store,rh,_=request(tmp_path)
    with Bridge(rh) as bridge:
        path,d=local_session(tmp_path,store,rh,bridge.port)
        out=api().execute_session(store,path,allow_run=True)
        assert out['status']=='OK' and out['verification']['structural']=='PASS'
        assert out['verification']['visual']=='NOT_RUN' and out['verification']['runtime']=='NOT_RUN'
        assert out['loaded_code_attestation']=='UNKNOWN'
        assert [v['action'] for v in bridge.calls]==['kneekura_asset_status','kneekura_asset_build']
        assert (path.parent/'exports/assets/probe/models/item/celestial_staff.json').is_file()
        assert (path.parent/'attempt.json').is_file()
        for p in store.root.rglob('*'):
            if p.is_file(): assert d['token'].encode() not in p.read_bytes()
        with pytest.raises(ContractError): api().execute_session(store,path,allow_run=True)
        assert len(bridge.calls)==2


@pytest.mark.parametrize('behavior',['disconnect','wrong_operation','invalid_export','token_echo'])
def test_ambiguous_or_invalid_write_never_retries(tmp_path,behavior):
    store,rh,_=request(tmp_path)
    with Bridge(rh,behavior) as bridge:
        path,d=local_session(tmp_path,store,rh,bridge.port)
        out=api().execute_session(store,path,allow_run=True)
        assert out['status']=='UNKNOWN' and out['verification']['visual']=='NOT_RUN'
        assert (path.parent/'attempt.json').exists() and not (path.parent/'exports').exists()
        with pytest.raises(ContractError): api().execute_session(store,path,allow_run=True)
        assert len(bridge.calls)==2
        for p in store.root.rglob('*'):
            if p.is_file(): assert d['token'].encode() not in p.read_bytes()


@pytest.mark.parametrize('behavior',['wrong_id','wrong_request','wrong_epoch','redirect'])
def test_bad_status_never_sends_a_write(tmp_path,behavior):
    store,rh,_=request(tmp_path)
    with Bridge(rh,behavior) as bridge:
        path,_=local_session(tmp_path,store,rh,bridge.port)
        out=api().execute_session(store,path,allow_run=True)
        assert out['status']=='UNAVAILABLE' and len(bridge.calls)==1
        assert not (path.parent/'attempt.json').exists()


@pytest.mark.parametrize('change',['bundle','symlink','extra_key','provider','invalid_port','existing_export'])
def test_local_scope_and_identity_are_checked_before_network(tmp_path,change):
    store,rh,_=request(tmp_path)
    with Bridge(rh) as bridge:
        path,d=local_session(tmp_path,store,rh,bridge.port)
        if change=='bundle': (path.parent/'guarded_blockbench.js').write_text('drift')
        if change=='symlink':
            moved=path.with_suffix('.saved'); path.rename(moved); path.symlink_to(moved)
        if change=='extra_key': d['path']='../oops'; path.write_bytes(canonical(d))
        if change=='provider': d['provider']={}; path.write_bytes(canonical(d))
        if change=='invalid_port': d['port']=True; path.write_bytes(canonical(d))
        if change=='existing_export': (path.parent/'exports').mkdir()
        with pytest.raises(ContractError): api().execute_session(store,path,allow_run=True)
        assert bridge.calls==[]


def test_wrong_source_pin_does_not_create_a_session_or_cas_data(tmp_path):
    store,rh,_=request(tmp_path); source=tmp_path/'wrong.js'; source.write_text('untrusted')
    parent=tmp_path/'editors'; parent.mkdir()
    before=set(store.root.rglob('*'))
    with pytest.raises(ContractError):
        api().stage_session(store,request_hash=rh,blueprint=blueprint(),upstream_plugin=source,parent=parent,port=8790)
    assert list(parent.iterdir())==[] and set(store.root.rglob('*'))==before


def test_node_provider_guard_regressions():
    import shutil
    node=shutil.which('node')
    if node is None: pytest.skip('Node is unavailable: provider-side guard tests NOT_RUN')
    testfile=Path(__file__).parent/'fixtures/blockbench_guard.test.cjs'
    run=subprocess.run([node,'--test',str(testfile)],capture_output=True,text=True,timeout=15)
    assert run.returncode==0,run.stdout+run.stderr


def patch_fixture():
    # Exact inspected anchors embedded in a synthetic container, NOT the full upstream blob.
    return ("(function(){\nconst PLUGIN_ID = 'blockbench_mcp';\nconst DEFAULT_PORT = 8787;\n"
            "const MAX_BODY = 96 * 1024 * 1024;\n"
            "const G = (globalThis.__BLOCKBENCH_MCP__ = globalThis.__BLOCKBENCH_MCP__ || {});\n"
            "const commands = {};\nfunction scriptsAllowed(){ const setting=null; return !setting || setting.value !== false; }\n"
            + api().DISPATCH + '\n})();\n')


def test_inspected_patch_anchors_produce_valid_guarded_javascript(tmp_path):
    import shutil
    config=dict(port=8790,session_id='a'*32,token='b'*64,request_hash='c'*64,timeout_ms=30000)
    compiled=api()._compose(patch_fixture(),config)
    assert b'__BLOCKBENCH_MCP__' not in compiled and b'__KNEEKURA_ASSET_PILOT__' in compiled
    assert b"const PLUGIN_ID = 'kneekura_asset_pilot';" in compiled
    assert b'Copyright (c) 2026 sosadly' in compiled
    target=tmp_path/'composed.js'; target.write_bytes(compiled)
    node=shutil.which('node')
    if node is None: pytest.skip('Node syntax check NOT_RUN')
    syntax=subprocess.run([node,'--check',str(target)],capture_output=True,text=True,timeout=10)
    assert syntax.returncode==0,syntax.stderr


@pytest.mark.parametrize('change',['missing','duplicate','global_drift'])
def test_patch_anchor_drift_is_rejected(change):
    source=patch_fixture()
    if change=='missing': source=source.replace(api().DISPATCH,'')
    if change=='duplicate': source+=api().DISPATCH
    if change=='global_drift': source+='\n// __BLOCKBENCH_MCP__'
    with pytest.raises(ContractError): api()._compose(source,dict(port=8790))


def test_session_cli_is_default_off_even_with_missing_paths(tmp_path):
    import os,sys
    env=dict(os.environ,PYTHONPATH=str(Path(__file__).parents[1]/'src'))
    command=[sys.executable,'-m','kneekura_tech_hub.minecraft.asset_session','--store',str(tmp_path/'not-created'),
             'run','--session',str(tmp_path/'absent.json')]
    run=subprocess.run(command,capture_output=True,text=True,env=env,timeout=10)
    assert run.returncode==3 and json.loads(run.stdout)['status']=='BLOCKED'
    assert not (tmp_path/'not-created').exists()
    run=subprocess.run(command+['--allow-run'],capture_output=True,text=True,env=env,timeout=10)
    assert run.returncode==2 and json.loads(run.stdout)['status']=='ERROR'
    assert not (tmp_path/'not-created').exists()


def test_receipt_binds_the_local_bundle_and_exposes_review_pngs(tmp_path):
    store,rh,_=request(tmp_path)
    with Bridge(rh) as bridge:
        path,d=local_session(tmp_path,store,rh,bridge.port)
        out=api().execute_session(store,path,allow_run=True)
        receipt=store.json(out['receipt_hash'])
        assert receipt.get('bundle_sha256')==d['bundle_sha256']
        assert receipt.get('blueprint_hash')==d['blueprint_hash']
        for view in ('front','left','back'):
            assert (path.parent/'exports/review'/f'{view}.png').read_bytes()==exports()['views'][view]


@pytest.mark.parametrize('destination',['git','cas'])
def test_secret_bundles_are_not_staged_in_git_or_evidence_storage(tmp_path,destination):
    store,rh,_=request(tmp_path); source=tmp_path/'irrelevant.js'; source.write_text('not reached')
    if destination=='git':
        parent=tmp_path/'worktree'; parent.mkdir(); (parent/'.git').write_text('gitdir: elsewhere')
    else: parent=store.root
    with pytest.raises(ContractError,match='outside Git and CAS'):
        api().stage_session(store,request_hash=rh,blueprint=blueprint(),upstream_plugin=source,parent=parent)
