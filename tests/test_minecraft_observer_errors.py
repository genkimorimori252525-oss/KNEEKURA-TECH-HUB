"""Authenticated error diagnostics only; these local peers never start Minecraft."""
import hmac
import http.client
import http.server
import json
from pathlib import Path
import shutil
import subprocess
import threading

import pytest

from kneekura_tech_hub.minecraft import runtime
from kneekura_tech_hub.minecraft.storage import ContractError, Store, canonical, digest, key_for
from test_minecraft_verification import contract

TOKEN='a'*64
SENSITIVE='DO_NOT_LEAK /private/world/session.json password=private-token'
SCOPE='ALLOWLISTED_EXCEPTION_CATEGORY_NOT_ROOT_CAUSE'


def envelope(category='TIMEOUT'):
    return dict(schema_version=1,kind='observer-error',http_status=409,status='ERROR',outcome='UNKNOWN',
        retry_allowed=False,category=category,diagnostic_scope=SCOPE)


@pytest.fixture(scope='module')
def java_peer(tmp_path_factory):
    folder=tmp_path_factory.mktemp('error-java');mode=folder/'mode.txt';mode.write_text('timeout')
    source=Path('departments/minecraft/mod-ai/forge-observer/src/main/java/org/kneekura/observer/BridgeTransport.java')
    main=folder/'ErrorPeer.java'
    main.write_text('''import org.kneekura.observer.BridgeTransport;
import java.nio.file.*;import java.util.concurrent.*;
public final class ErrorPeer {
 public static void main(String[] a) throws Exception {
  var server=new BridgeTransport(a[0],a[1],a[2],(path,body,nonce)-> {
   String secret="DO_NOT_LEAK /private/world/session.json password=private-token";
   switch(Files.readString(Path.of(a[3]))) {
    case "timeout":throw new TimeoutException(secret);
    case "request":throw new IllegalArgumentException(secret);
    case "state":throw new IllegalStateException(secret);
    case "wrapped_timeout":throw new ExecutionException(new TimeoutException(secret));
    case "wrapped_state":throw new java.lang.reflect.InvocationTargetException(new IllegalStateException(secret));
    case "deep":Exception e=new TimeoutException(secret);for(int i=0;i<12;i++)e=new ExecutionException(e);throw e;
    default:throw new NullPointerException(secret);
   }
  });System.out.println(server.start());System.out.flush();System.in.read();server.close();
 }
}''')
    result=subprocess.run([shutil.which('javac'),'--release','17','-d',str(folder),str(source),str(main)],capture_output=True,text=True,timeout=30)
    assert result.returncode==0,result.stderr
    c=contract();process=subprocess.Popen([shutil.which('java'),'-cp',str(folder),'ErrorPeer',TOKEN,c['run_id'],c['session_epoch'],str(mode)],stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
    port=int(process.stdout.readline())
    yield port,mode,c
    process.terminate();process.wait(timeout=5)


@pytest.mark.parametrize('mode,category',[('timeout','TIMEOUT'),('request','REQUEST_REJECTED'),('state','STATE_OR_IDENTITY_REJECTED'),('wrapped_timeout','TIMEOUT'),('wrapped_state','STATE_OR_IDENTITY_REJECTED'),('deep','INTERNAL_ERROR'),('internal','INTERNAL_ERROR')])
def test_java_returns_only_signed_allowlisted_error_families(java_peer,mode,category):
    port,mode_path,c=java_peer;mode_path.write_text(mode);nonce='b'*32
    conn=http.client.HTTPConnection('127.0.0.1',port,timeout=3)
    conn.request('POST','/v1/observe',body=b'{}',headers={'Authorization':'Bearer '+TOKEN,'X-Kneekura-Run':c['run_id'],
        'X-Kneekura-Epoch':c['session_epoch'],'X-Kneekura-Nonce':nonce})
    response=conn.getresponse();body=response.read();signature=response.getheader('X-Kneekura-Signature');conn.close()
    assert response.status==409 and len(body)<=1024
    assert hmac.compare_digest(signature,hmac.digest(TOKEN.encode(),('POST\n/v1/observe\n'+nonce+'\n').encode()+body,'sha256').hex())
    assert json.loads(body)==envelope(category)
    assert SENSITIVE not in body.decode() and 'session.json' not in body.decode()


@pytest.fixture
def error_peer(tmp_path):
    c=contract();settings={'payload':canonical(envelope()),'signature':'valid','status':409,'fail_handshake':False};calls=[]
    class Peer(http.server.BaseHTTPRequestHandler):
        def do_GET(self):self.respond()
        def do_POST(self):self.respond()
        def respond(self):
            calls.append((self.command,self.path))
            self.rfile.read(int(self.headers.get('Content-Length','0')))
            failure=self.command!='GET' or settings['fail_handshake']
            body=settings['payload'] if failure else settings.get('hello_payload',canonical(dict({'ready':True,'identity':c},**settings.get('hello_extra',{}))))
            status=settings['status'] if failure else 200
            signature=hmac.digest(TOKEN.encode(),(self.command+'\n'+self.path+'\n'+self.headers['X-Kneekura-Nonce']+'\n').encode()+body,'sha256').hex()
            self.send_response(status);self.send_header('Content-Length',str(len(body)))
            if not failure or settings['signature']!='absent':self.send_header('X-Kneekura-Signature',signature if not failure or settings['signature']=='valid' else '0'*64)
            self.end_headers()
            try:self.wfile.write(body)
            except (BrokenPipeError,ConnectionResetError):pass
        def log_message(self,*args):pass
    server=http.server.ThreadingHTTPServer(('127.0.0.1',0),Peer)
    thread=threading.Thread(target=lambda:server.serve_forever(poll_interval=.01),daemon=True);thread.start()
    endpoint=tmp_path/'endpoint.json';endpoint.write_text(json.dumps({'url':f'http://127.0.0.1:{server.server_port}'}))
    session=tmp_path/'session.json';session.write_bytes(canonical({'token':TOKEN,'contract':c,'endpoint_path':str(endpoint),'command_registry':{'fixed':'say fixture'}}));session.chmod(0o600)
    store=Store(tmp_path/'cas')
    yield store,session,c,settings,calls,server.server_port
    server.shutdown();server.server_close();thread.join(timeout=2)


@pytest.mark.parametrize('handshake',[False,True])
def test_authenticated_error_is_retained_without_retry_or_observation_pass(error_peer,handshake):
    store,session,c,settings,calls,_=error_peer;settings['fail_handshake']=handshake
    with pytest.raises(ContractError) as failure:runtime.observe_live(store,str(session))
    assert getattr(failure.value,'category',None)=='TIMEOUT'
    ref=getattr(failure.value,'diagnostic_hash',None);assert ref
    record=store.json(ref)
    assert record['kind']=='authenticated-observer-error' and record['outcome']=='UNKNOWN' and record['retry_allowed'] is False
    assert record['evidence_level']=='AUTHENTICATED_OBSERVER_ERROR_NOT_OBSERVATION'
    assert record['error']==envelope() and record['http_status']==409
    assert record['request_path']==('/v1/handshake' if handshake else '/v1/observe')
    assert record['expected_identity']['session_epoch']==c['session_epoch']
    assert store.read(record['payload_hash'])==settings['payload']
    assert record['handshake_summary_hash'] is None if handshake else store.json(record['handshake_summary_hash'])['ready'] is True
    assert ref in store.pinned_hashes() and record['payload_hash'] in store.pinned_hashes()
    assert len(calls)==(1 if handshake else 2)
    assert ref in str(failure.value) and SENSITIVE not in str(failure.value)
    assert TOKEN not in json.dumps(record) and str(session) not in json.dumps(record)


@pytest.mark.parametrize('fault',['unsigned','wrong_signature','malformed','extra_message','extra_path','unknown_category','bool_schema','float_status',
    'numeric_retry','pass_outcome','wrong_kind','wrong_scope','duplicate_key','oversized','legacy_body','wrong_http_status'])
def test_untrusted_or_malformed_error_is_never_retained(error_peer,fault):
    store,session,_,settings,calls,_=error_peer;body=envelope()
    if fault=='unsigned':settings['signature']='absent'
    if fault=='wrong_signature':settings['signature']='wrong'
    if fault=='extra_message':body['message']=SENSITIVE
    if fault=='extra_path':body['path']='/private/world/session.json'
    if fault=='unknown_category':body['category']=SENSITIVE
    if fault=='bool_schema':body['schema_version']=True
    if fault=='float_status':body['http_status']=409.0
    if fault=='numeric_retry':body['retry_allowed']=0
    if fault=='pass_outcome':body['outcome']='PASS'
    if fault=='wrong_kind':body['kind']='observation'
    if fault=='wrong_scope':body['diagnostic_scope']='ROOT_CAUSE_PROVEN'
    if fault=='wrong_http_status':settings['status']=500
    settings['payload']=canonical(body)
    if fault=='malformed':settings['payload']=('{'+SENSITIVE).encode()
    if fault=='duplicate_key':settings['payload']=settings['payload'][:-1]+b',"category":"TIMEOUT"}'
    if fault=='oversized':settings['payload']+=b' '*1024
    if fault=='legacy_body':settings['payload']=canonical({'status':'ERROR','outcome':'UNKNOWN','retry_allowed':False})
    with pytest.raises(ContractError) as failure:runtime.observe_live(store,str(session))
    assert not getattr(failure.value,'diagnostic_hash',None)
    assert SENSITIVE not in str(failure.value) and '/private/' not in str(failure.value)
    assert not list((store.root/'blobs').rglob('*'))
    assert len(calls)==2


def test_command_rejection_retains_unknown_completion_and_does_not_repeat(error_peer):
    store,session,_,_,calls,_=error_peer
    with pytest.raises(ContractError) as failure:
        runtime.execute_registered_command(store,str(session),command_id='fixed',request_id='only-once')
    assert getattr(failure.value,'diagnostic_hash',None)
    assert calls==[('GET','/v1/handshake'),('POST','/v1/command')]
    record=store.json(failure.value.diagnostic_hash)
    assert record['outcome']=='UNKNOWN' and record['retry_allowed'] is False


def test_diagnostic_does_not_retain_free_form_prior_handshake_fields(error_peer):
    store,session,_,settings,_,_=error_peer;settings['hello_extra']={'message':SENSITIVE,'token':TOKEN}
    with pytest.raises(ContractError):runtime.observe_live(store,str(session))
    assert all(SENSITIVE.encode() not in store.read(h) and TOKEN.encode() not in store.read(h) for h in store.pinned_hashes())


def test_diagnostic_storage_failure_does_not_leak_path_or_allow_retry(error_peer,monkeypatch):
    store,session,_,_,calls,_=error_peer
    def full(*args):raise OSError(SENSITIVE)
    monkeypatch.setattr(Store,'put',full)
    with pytest.raises(ContractError) as failure:runtime.observe_live(store,str(session))
    assert getattr(failure.value,'category',None)=='TIMEOUT'
    assert getattr(failure.value,'diagnostic_status',None)=='UNAVAILABLE'
    assert not getattr(failure.value,'diagnostic_hash',None)
    assert SENSITIVE not in str(failure.value) and 'do not retry' in str(failure.value)
    assert len(calls)==2


def test_actual_java_error_is_understood_by_python_without_retry(java_peer):
    port,mode,c=java_peer;mode.write_text('wrapped_timeout')
    with pytest.raises(ContractError) as failure:runtime.BridgeClient(f'http://127.0.0.1:{port}',TOKEN,c).request('/v1/observe')
    assert getattr(failure.value,'category',None)=='TIMEOUT'
    assert getattr(failure.value,'diagnostic_status',None)=='NOT_RETAINED'
    assert SENSITIVE not in str(failure.value)


def test_sanitized_summary_keeps_distinct_exact_original_payload_hash(error_peer):
    store,session,c,settings,_,_=error_peer
    decoded={'ready':True,'identity':c,'message':SENSITIVE}
    settings['hello_payload']=b' \n'+canonical(decoded)+b' \n'
    with pytest.raises(ContractError) as failure:runtime.observe_live(store,str(session))
    record=store.json(failure.value.diagnostic_hash)
    summary=store.json(record['handshake_summary_hash'])
    assert record['handshake_response_payload_hash']==digest(settings['hello_payload'])
    assert summary['decoded_content_hash']==key_for(decoded)
    assert summary['decoded_content_hash']!=record['handshake_response_payload_hash']
    assert summary['raw_payload_retained'] is False
    assert not store.blob_path(record['handshake_response_payload_hash']).exists()
    assert SENSITIVE not in json.dumps(summary)


def test_error_envelope_cannot_be_smuggled_as_successful_http_observation(error_peer):
    store,session,c,settings,calls,_=error_peer
    settings['status']=200;settings['payload']=canonical(dict(envelope(),identity=c))
    with pytest.raises(ContractError):runtime.observe_live(store,str(session))
    assert not list((store.root/'blobs').rglob('*'))
    assert len(calls)==2
