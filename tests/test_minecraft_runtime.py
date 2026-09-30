"""Transport/identity tests. Java peer is a protocol fixture, not Minecraft."""
import base64
import copy
import hmac
import importlib
import json
import os
import shutil
import subprocess
import time
import uuid
from pathlib import Path

import pytest
from kneekura_tech_hub.minecraft.storage import Store, ContractError, canonical, key_for
from kneekura_tech_hub.minecraft.workspace import workspace_fingerprint, file_hash
from kneekura_tech_hub.minecraft.index import prepare_index
from test_minecraft_index import class_profile
from test_minecraft_verification import contract, observation, report


def mod():
    try: return importlib.import_module('kneekura_tech_hub.minecraft.runtime')
    except ImportError: pytest.fail('Authenticated runtime adapter is not implemented')


@pytest.fixture
def session(class_profile):
    store,p,root=class_profile
    from kneekura_tech_hub.minecraft.storage import capture_profile
    manifest=copy.deepcopy(p['manifest']); manifest['dirty_hash']=workspace_fingerprint(root)
    p=capture_profile(manifest,root,store)
    idx=prepare_index(p,store)['index_snapshot_id']; c=contract()
    c.update(profile_id=p['profile_id'],index_snapshot_id=idx,dirty_hash=workspace_fingerprint(root),
             build_artifact_hash=file_hash(root/'mod.jar'),config_hash=key_for([]),
             adapter_id='kneekura-forge-observer',adapter_version='1.0.0')
    receipt={'source_generation':c['dirty_hash'],'source_generation_after':c['dirty_hash'],
             'request':{'kind':'compile','workspace':str(root)},
             'outputs':[{'content_hash':c['build_artifact_hash']}],
             'result':{'outcome':'PASS','assertion_domain':'compile_only'}}
    reg={'workspace':str(root),'build_artifact':'mod.jar','build_receipt_hash':store.put_json(receipt),
         'runtime_config_files':[],'command_registry':{}}
    directory=root/'run-session'; directory.mkdir()
    return store,c,reg,directory


def test_session_refuses_unverified_or_wrong_build(session):
    store,c,reg,directory=session
    bad=copy.deepcopy(c); bad['build_artifact_hash']='a'*64
    with pytest.raises(ContractError): mod().create_session(store,reg,bad,directory=directory)
    result=mod().create_session(store,reg,c,directory=directory)
    cfg=json.loads(Path(result['path']).read_bytes())
    assert len(cfg['token'])==64 and cfg['contract']==c
    assert cfg['class_probes'] and cfg['expected_runtime']['minecraft']=='1.20.1'
    if os.name!='nt': assert Path(result['path']).stat().st_mode&0o077==0
    with pytest.raises(ContractError): mod().create_session(store,reg,c,directory=directory)


def test_authenticated_report_tamper_rejected(session):
    store,c,reg,directory=session; s=mod().create_session(store,reg,c,directory=directory)
    payload=canonical(report(c)); signed={'payload_b64':base64.b64encode(payload).decode(),
        'signature':hmac.digest(s['token'].encode(),b'gametest-report\n'+payload,'sha256').hex()}
    path=directory/'gametest-report.json'; path.write_bytes(canonical(signed))
    assert mod().read_signed_report(s,path)['tests'][0]['id']=='demo.attack'
    signed['payload_b64']=base64.b64encode(payload+b' ').decode(); path.write_bytes(canonical(signed))
    with pytest.raises(ContractError): mod().read_signed_report(s,path)


@pytest.mark.parametrize('url',['http://evil.test:123/','https://127.0.0.1:123','http://127.0.0.1:123@evil/','http://127.0.0.1:123/path','http://localhost:123'])
def test_client_only_literal_loopback_and_no_redirects(url):
    with pytest.raises(ContractError): mod().BridgeClient(url,'x'*64,contract())


def test_real_java17_transport_hmac_and_wrong_auth(tmp_path):
    runtime=mod()
    java=Path('departments/minecraft/mod-ai/forge-observer/src/main/java/org/kneekura/observer/BridgeTransport.java')
    assert java.is_file(), 'JDK transport must exist'
    c=contract(); data=canonical(observation(c)).decode(); cfg=tmp_path/'response.json'; cfg.write_text(data)
    main=tmp_path/'Peer.java'; main.write_text('''import org.kneekura.observer.BridgeTransport;
import java.nio.file.*;
public class Peer { public static void main(String[] a) throws Exception {
  var server = new BridgeTransport(a[0], a[1], a[2], (path,body,nonce)->Files.readString(Path.of(a[3])));
  System.out.println(server.start()); System.out.flush(); Thread.sleep(30000); server.close();
}}''')
    subprocess.run([shutil.which('javac'),'--release','17','-d',str(tmp_path),str(java),str(main)],check=True,capture_output=True)
    token='a'*64
    peer=subprocess.Popen([shutil.which('java'),'-cp',str(tmp_path),'Peer',token,c['run_id'],c['session_epoch'],str(cfg)],stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
    try:
        port=int(peer.stdout.readline().strip())
        client=runtime.BridgeClient(f'http://127.0.0.1:{port}',token,c)
        result=client.request('/v1/observe',{'limit':1})
        assert result['identity']['session_epoch']==c['session_epoch']
        wrong=runtime.BridgeClient(f'http://127.0.0.1:{port}','b'*64,c)
        with pytest.raises(ContractError): wrong.request('/v1/observe',{})
        with pytest.raises(ContractError): client.request('/v1/arbitrary',{})
    finally:
        peer.terminate(); peer.wait(timeout=5)


def test_nonliving_entity_null_health_is_not_fabricated():
    from kneekura_tech_hub.minecraft.verification import evaluate_observation
    c=contract(); o=observation(c); o['entities'][0].update(health=None,health_applicable=False)
    assert evaluate_observation(c,o)['status']=='OK'


def test_config_hash_is_exact_files_not_an_unsupported_promise(session):
    store,c,reg,directory=session
    (Path(reg['workspace'])/'settings.toml').write_text('x=1')
    reg['runtime_config_files']=['settings.toml']
    with pytest.raises(ContractError,match='config'): mod().create_session(store,reg,c,directory=directory)

def test_real_java_ledger_does_not_collapse_retries_or_invent_completeness(tmp_path):
    source=Path('departments/minecraft/mod-ai/forge-observer/src/main/java/org/kneekura/observer/RunLedger.java')
    assert source.is_file(), 'A concrete GameTest ledger must exist'
    test=tmp_path/'LedgerTest.java'; test.write_text('''import org.kneekura.observer.RunLedger;
import java.util.Map;
public class LedgerTest { public static void main(String[] args) {
 RunLedger x=new RunLedger(); x.detect("target",false); x.detect("other",true);
 x.record("target",false,false,"optional failure");
 if (x.snapshot(Map.of()).get("completed")!=Boolean.FALSE) throw new AssertionError("invented completion");
 x.complete(); if (x.snapshot(Map.of()).get("executed_count").equals(1)==false) throw new AssertionError("wrong count");
 x.record("target",false,true,"");
 if (x.snapshot(Map.of()).get("completed")!=Boolean.FALSE) throw new AssertionError("collapsed retry");
 System.out.print("LEDGER_OK");
}}''')
    subprocess.run([shutil.which('javac'),'--release','17','-d',str(tmp_path),str(source),str(test)],check=True,capture_output=True)
    got=subprocess.run([shutil.which('java'),'-cp',str(tmp_path),'LedgerTest'],check=True,capture_output=True,text=True)
    assert got.stdout=='LEDGER_OK'


def test_forge_binding_and_init_script_are_present_for_actual_userdev_build():
    root=Path('departments/minecraft/mod-ai/forge-observer')
    java=root/'src/main/java/org/kneekura/observer/ForgeObserver.java'
    assert java.is_file(), 'Forge-specific binding not yet implemented'
    s=java.read_text()
    assert 'ServerStartedEvent' in s and 'getWorldPath' in s and 'getSeed' in s
    assert 'onTestSuccess' in s and 'onTestFailed' in s and 'replaceWith' in s
    assert 'server.submit' in s and 'class_probes' in s
    client=root/'src/main/java/org/kneekura/observer/ClientProbe.java'
    assert client.is_file() and 'takeScreenshot' in client.read_text()
    script=Path('src/kneekura_tech_hub/minecraft/resources/kneekura-run.init.gradle')
    assert script.is_file() and 'workingDir' in script.read_text()

def test_userdev_compiled_classes_can_identify_build_without_reobfuscated_jar(session):
    store,c,reg,directory=session; root=Path(reg['workspace'])
    # The fixture has real --release17 classes in this directory.
    reg['build_artifact']='classes'
    listing=[{'path':p.relative_to(root/'classes').as_posix(),'hash':file_hash(p)} for p in sorted((root/'classes').rglob('*')) if p.is_file()]
    c['build_artifact_hash']=store.put_json(listing)
    receipt={'source_generation':c['dirty_hash'],'source_generation_after':c['dirty_hash'],
             'request':{'kind':'compile','workspace':str(root)},'outputs':[{'content_hash':c['build_artifact_hash']}],
             'result':{'outcome':'PASS','assertion_domain':'compile_only'}}
    reg['build_receipt_hash']=store.put_json(receipt)
    s=mod().create_session(store,reg,c,directory=directory)
    assert s['build_artifact_kind']=='directory' and s['class_probes']


@pytest.mark.parametrize('layout,relative', [('server','proof-world'), ('client','saves/proof-world')])
def test_session_world_binding_uses_explicit_save_layout(session,layout,relative):
    store,c,reg,directory=session
    reg.update(world_layout=layout,world_directory_name='proof-world')
    c['physical_side']='client' if layout=='client' else 'server'
    result=mod().create_session(store,reg,c,directory=directory)
    cfg=json.loads(Path(result['path']).read_bytes())
    assert Path(cfg['world'])==directory/relative
    assert cfg['world_layout']==layout
    assert Path(cfg['directory'])==directory


@pytest.mark.parametrize('config', [
    {'world_layout':'unknown'}, {'world_directory_name':'../production'},
    {'world_directory_name':'saves/production'}, {'world_directory_name':'/production'},
])
def test_session_rejects_invalid_world_layout_or_name_before_writing(session,config):
    store,c,reg,directory=session; reg.update(config)
    with pytest.raises(ContractError): mod().create_session(store,reg,c,directory=directory)
    assert not (directory/'session.json').exists()


def test_session_rejects_client_saves_symlink(session):
    store,c,reg,directory=session
    target=directory/'other-saves'; target.mkdir()
    (directory/'saves').symlink_to(target,target_is_directory=True)
    reg.update(world_layout='client')
    with pytest.raises(ContractError): mod().create_session(store,reg,c,directory=directory)
    assert not (directory/'session.json').exists()


@pytest.mark.parametrize('timeout,expected', [(1.0,'OK'), (0.01,'timeout'), (0.075,'timeout')])
def test_live_observation_honors_explicit_transport_timeout(tmp_path,timeout,expected):
    import http.server
    import threading
    runtime=mod(); c=contract(); token='a'*64; requests=[]
    class Peer(http.server.BaseHTTPRequestHandler):
        def do_GET(self): self.respond({'ready':True,'identity':report(c)['identity']})
        def do_POST(self): self.respond(observation(c))
        def respond(self,data):
            requests.append((self.command,self.path))
            time.sleep(0.05)
            raw=canonical(data)
            nonce=self.headers['X-Kneekura-Nonce']
            signature=hmac.digest(token.encode(),(self.command+'\n'+self.path+'\n'+nonce+'\n').encode()+raw,'sha256').hex()
            self.send_response(200); self.send_header('X-Kneekura-Signature',signature)
            self.end_headers()
            try: self.wfile.write(raw)
            except (BrokenPipeError,ConnectionResetError): pass
        def log_message(self,*args): pass
    server=http.server.ThreadingHTTPServer(('127.0.0.1',0),Peer)
    thread=threading.Thread(target=server.serve_forever,daemon=True); thread.start()
    endpoint=tmp_path/'endpoint.json'; endpoint.write_text(json.dumps({'url':f'http://127.0.0.1:{server.server_port}'}))
    session_path=tmp_path/'session.json'
    session_path.write_bytes(canonical({'token':token,'contract':c,'endpoint_path':str(endpoint)})); session_path.chmod(0o600)
    store=Store(tmp_path/'store')
    try:
        if expected=='timeout':
            with pytest.raises(ContractError,match='interrupted|deadline expired'):
                runtime.observe_live(store,str(session_path),timeout=timeout)
            assert len(requests)<=2  # One handshake and at most one operation; no retries.
            assert not list((store.root/'blobs').rglob('*'))
        else:
            out=runtime.observe_live(store,str(session_path),timeout=timeout)
            assert out['status']=='OK' and out['evidence_level']=='AUTHENTICATED_LIVE_OBSERVER'
    finally: server.shutdown(); server.server_close(); thread.join(timeout=2)


@pytest.mark.parametrize('slow_stage', ['headers', 'body'])
def test_live_bridge_total_deadline_stops_slow_stream_without_retry(slow_stage):
    """Per-recv timeouts must not let one-byte drip streams overrun input budgets."""
    import socketserver
    import threading

    seen = []
    class Peer(socketserver.BaseRequestHandler):
        def handle(self):
            self.request.recv(16384)
            seen.append(True)
            payload = b'{}'
            headers = b'HTTP/1.1 200 OK\r\nContent-Length: 32\r\nX-Slow: '
            try:
                self.request.sendall(headers)
                if slow_stage == 'headers':
                    for _ in range(30):
                        self.request.sendall(b'x'); time.sleep(.02)
                    self.request.sendall(b'\r\n\r\n'+payload)
                else:
                    self.request.sendall(b'x\r\n\r\n')
                    # Keep each recv below the configured timeout for > total budget.
                    for _ in range(32):
                        self.request.sendall(b' '); time.sleep(.02)
            except OSError:
                pass
    class Server(socketserver.ThreadingTCPServer):
        allow_reuse_address = True
        daemon_threads = True
    with Server(('127.0.0.1', 0), Peer) as server:
        thread = threading.Thread(target=server.serve_forever, daemon=True); thread.start()
        client = mod().BridgeClient(f'http://127.0.0.1:{server.server_address[1]}', 'a'*64, contract(), timeout=.06)
        started = time.monotonic()
        try:
            with pytest.raises(ContractError): client.request('/v1/observe')
            elapsed = time.monotonic()-started
            assert elapsed < .20, f'Observer stream exceeded total deadline: {elapsed}'
            assert len(seen) == 1
        finally:
            server.shutdown(); thread.join(timeout=1)
