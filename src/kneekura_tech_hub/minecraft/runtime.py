"""Authenticated loopback observation client and run-bound session preparation.

This module does not start Minecraft. The registered execution adapter may create
one private session file; a separately compiled Forge observer produces responses.
A matching imported JSON document is never labelled a live handshake.
"""
from __future__ import annotations

import base64
import hmac
import http.client
import json
import os
import re
import secrets
import uuid
import zipfile
from pathlib import Path
from urllib.parse import urlsplit

from . import index, verification
from .storage import ContractError, Store, canonical, digest, key_for, valid_hash, _collect, Limits
from .workspace import _workspace, file_hash, workspace_fingerprint

PATHS={'/v1/handshake','/v1/observe','/v1/logs','/v1/client','/v1/command','/v1/operation'}
ADAPTER_ID='kneekura-forge-observer'
ADAPTER_VERSION='1.0.0'
MAX_RESPONSE=16*1024*1024


def config_snapshot(registry: dict):
    root=_workspace(registry.get('workspace')); rows=[]
    files=registry.get('runtime_config_files',[])
    if not isinstance(files,list) or len(files)>1000: raise ContractError('Invalid runtime config file list')
    for name in files:
        p=Path(name); p=p if p.is_absolute() else root/p
        if p.is_symlink() or not p.is_file() or not p.resolve().is_relative_to(root): raise ContractError('Invalid registered runtime config file')
        rows.append({'path':p.resolve().as_posix(),'sha256':file_hash(p)})
    rows.sort(key=lambda row:row['path'])
    if len({r['path'] for r in rows})!=len(rows): raise ContractError('Duplicate runtime config file')
    return rows


def create_session(store: Store,registry: dict,contract: dict,*,directory: Path):
    errors=verification._identity_errors(contract,{'identity':contract})
    if errors: raise ContractError('; '.join(errors))
    if contract['adapter_id']!=ADAPTER_ID or contract['adapter_version']!=ADAPTER_VERSION:
        raise ContractError('Wrong runtime observer version')
    root=_workspace(registry.get('workspace')); directory=Path(directory)
    if directory.is_symlink() or not directory.is_dir() or not directory.resolve().is_relative_to(root):
        raise ContractError('Session directory must be inside the registered workspace')
    snapshot=index._load(store,contract['index_snapshot_id']); p=snapshot['profile']; m=p['manifest']
    if p['profile_id']!=contract['profile_id'] or m['minecraft']!='1.20.1' or m['loader']!='forge' or m.get('java_major')!=17:
        raise ContractError('Runtime requires the pinned Forge 1.20.1 / Java17 profile')
    current=workspace_fingerprint(root)
    if current!=contract['dirty_hash']: raise ContractError('Sources changed since the run contract was fixed')
    if m.get('dirty_hash') != current: raise ContractError('Index source generation is stale')
    if m.get('workspace_revision')!=contract['source_revision']:
        raise ContractError('Contract source revision differs from index profile')
    config=config_snapshot(registry)
    if key_for(config)!=contract['config_hash']: raise ContractError('Runtime config hash does not match registered files')
    artifact=Path(registry.get('build_artifact',''))
    artifact=artifact if artifact.is_absolute() else root/artifact
    if artifact.is_symlink() or not artifact.exists() or not artifact.resolve().is_relative_to(root):
        raise ContractError('Packaged/compiled build artifact unavailable')
    artifact_kind='directory' if artifact.is_dir() else 'jar'
    problems=[]; ignored=[]
    rows,original=_collect(artifact,artifact_kind,Limits(),problems,ignored,store.root)
    if problems or ignored: raise ContractError('Build capture is incomplete')
    actual_hash=digest(original) if original is not None else key_for([{'path':n,'hash':digest(data)} for n,data in sorted(rows)])
    if actual_hash!=contract['build_artifact_hash']:
        raise ContractError('Packaged/compiled build artifact differs from run contract')
    receipt=store.json(valid_hash(registry.get('build_receipt_hash')))
    if (receipt.get('request',{}).get('kind')!='compile' or receipt['request'].get('workspace')!=str(root) or
        receipt.get('result',{}).get('outcome')!='PASS' or receipt.get('source_generation')!=current or
        receipt.get('source_generation_after')!=current or not any(o.get('content_hash')==contract['build_artifact_hash'] for o in receipt.get('outputs',[]))):
        raise ContractError('No successful same-source compile receipt for this build artifact')
    probes=[]
    for name,data in rows:
        if name.endswith('.class'):
            if len(probes)>=20000: raise ContractError('Target class probe budget exceeded')
            probes.append({'resource':name,'sha256':digest(data)})
    if not probes: raise ContractError('Build JAR has no class resources to identify')
    commands=registry.get('command_registry',{})
    if not isinstance(commands,dict) or len(commands)>100 or any(not isinstance(k,str) or not re.fullmatch(r'[A-Za-z0-9_.-]{1,80}',k) or not isinstance(v,str) or not v or len(v)>2000 for k,v in commands.items()):
        raise ContractError('Command registry must map bounded IDs to explicit commands')
    session={'schema_version':1,'token':secrets.token_hex(32),'contract':contract,
             'expected_runtime':{'minecraft':m['minecraft'],'forge':m['loader_version'],'java_major':17},
             'build_artifact':str(artifact.resolve()),'build_artifact_kind':artifact_kind,'build_receipt_hash':registry['build_receipt_hash'],
             'class_probes':probes,'config_files':config,'command_registry':commands,
             'directory':str(directory.resolve()),'world':str(directory/registry.get('world_directory_name','gametestserver')),
             'endpoint_path':str(directory/'endpoint.json'),'report_path':str(directory/'gametest-report.json')}
    path=directory/'session.json'
    try:
        fd=os.open(path,os.O_CREAT|os.O_EXCL|os.O_WRONLY,0o600)
        with os.fdopen(fd,'wb') as out: out.write(canonical(session)); out.flush(); os.fsync(out.fileno())
    except FileExistsError: raise ContractError('A session already exists; never reuse an epoch after restart') from None
    # Never store or print the authentication secret in CAS / public receipts.
    return dict(session,path=str(path))


def load_session(path: str | Path):
    p=Path(path)
    if p.is_symlink() or not p.is_file() or p.stat().st_size>4*1024*1024: raise ContractError('Invalid local session file')
    if os.name!='nt' and p.stat().st_mode & 0o077: raise ContractError('Session file must be private (mode 600)')
    obj=json.loads(p.read_bytes())
    if not isinstance(obj,dict) or not re.fullmatch(r'[a-f0-9]{64}',str(obj.get('token',''))): raise ContractError('Invalid local session secret')
    return dict(obj,path=str(p.resolve()))


class BridgeClient:
    def __init__(self,url: str,token: str,contract: dict,*,timeout=10):
        u=urlsplit(url)
        try: port=u.port
        except ValueError: raise ContractError('Invalid local port') from None
        if (u.scheme!='http' or u.hostname!='127.0.0.1' or not port or u.username or u.password or
            u.path not in ('','/') or u.query or u.fragment or not re.fullmatch('[a-f0-9]{64}',token) or
            type(timeout) not in (int,float) or not 0<timeout<=30):
            raise ContractError('Only explicit literal loopback HTTP endpoints are supported')
        self.port,self.token,self.contract,self.timeout=port,token,contract,timeout

    def request(self,path: str,body: dict | None=None):
        if path not in PATHS: raise ContractError('Unknown observer operation')
        method='GET' if path=='/v1/handshake' else 'POST'
        raw=canonical(body or {})
        if len(raw)>16384: raise ContractError('Observation query exceeds request budget')
        nonce=uuid.uuid4().hex
        headers={'Authorization':'Bearer '+self.token,'Content-Type':'application/json',
                 'X-Kneekura-Run':self.contract['run_id'],'X-Kneekura-Epoch':self.contract['session_epoch'],
                 'X-Kneekura-Nonce':nonce}
        conn=http.client.HTTPConnection('127.0.0.1',self.port,timeout=self.timeout)
        try:
            conn.request(method,path,body=raw,headers=headers)
            response=conn.getresponse(); payload=response.read(MAX_RESPONSE+1)
            if len(payload)>MAX_RESPONSE: raise ContractError('Observer response exceeds budget')
            expected=hmac.digest(self.token.encode(),(method+'\n'+path+'\n'+nonce+'\n').encode()+payload,'sha256').hex()
            if not hmac.compare_digest(expected,response.getheader('X-Kneekura-Signature','')):
                raise ContractError('Unauthenticated or replayed observer response')
            if response.status!=200: raise ContractError('Observer rejected request (HTTP '+str(response.status)+')')
            value=json.loads(payload)
            if not isinstance(value,dict): raise ContractError('Observer response must be an object')
            return value
        except (OSError,http.client.HTTPException):
            raise ContractError('Observer connection interrupted; operation completion is unknown, do not retry writes') from None
        finally: conn.close()


def read_signed_report(session: dict,path: Path):
    path=Path(path)
    if path.is_symlink() or path.stat().st_size>MAX_RESPONSE*2: raise ContractError('Unsafe or oversized report')
    wrapped=json.loads(path.read_bytes()); raw=base64.b64decode(wrapped['payload_b64'],validate=True)
    if len(raw)>MAX_RESPONSE: raise ContractError('Report exceeds budget')
    expected=hmac.digest(session['token'].encode(),b'gametest-report\n'+raw,'sha256').hex()
    if not hmac.compare_digest(expected,wrapped.get('signature','')): raise ContractError('Invalid GameTest report signature')
    report=json.loads(raw)
    if verification._identity_errors(session['contract'],report): raise ContractError('Signed report belongs to a different run')
    return report


def _exchange_live(store: Store,session_path: str,*,operation='observe',query=None):
    s=load_session(session_path); endpoint=Path(s['endpoint_path'])
    if endpoint.is_symlink() or endpoint.stat().st_size>65536: raise ContractError('Invalid observer endpoint file')
    e=json.loads(endpoint.read_bytes())
    client=BridgeClient(e['url'],s['token'],s['contract'])
    hello=client.request('/v1/handshake')
    if hello.get('ready') is not True or verification._identity_errors(s['contract'],hello):
        raise ContractError('Live handshake did not verify the expected build/session/world')
    if operation not in ('observe','logs','client','command','operation'): raise ContractError('Unknown observer operation')
    raw=client.request('/v1/'+operation,query or {})
    if verification._identity_errors(s['contract'],raw): raise ContractError('Observation belongs to another run')
    h=store.put_json(raw); hello_hash=store.put_json(hello)
    for item in (h,hello_hash): store.pin(item,'live:'+s['contract']['run_id'])
    if operation in ('observe','client'):
        result=verification.evaluate_observation(s['contract'],raw)
    elif operation in ('command','operation'):
        result=verification.evaluate_operation_receipt(s['contract'],raw)
    else: result={'status':'OK','outcome':'NOT_RUN','results':raw.get('logs',[])}
    result.update(artifact_hash=h,handshake_hash=hello_hash,evidence_level='AUTHENTICATED_LIVE_OBSERVER',
                  note='Observation is not itself a passing behaviour/rendering assertion')
    return result


def observe_live(store: Store, session_path: str, *, operation='observe', query=None):
    if operation not in ('observe', 'logs', 'client', 'operation'):
        raise ContractError('Observe is a read-only operation surface')
    return _exchange_live(store, session_path, operation=operation, query=query)


def execute_registered_command(store: Store, session_path: str, *, command_id: str, request_id: str):
    """Explicit mutation path, separate from observation. Never retry automatically."""
    session = load_session(session_path)
    if command_id not in session.get('command_registry', {}):
        raise ContractError('Command ID is not in the explicitly trusted registry')
    if not isinstance(request_id, str) or not re.fullmatch(r'[A-Za-z0-9_.-]{1,128}', request_id):
        raise ContractError('Bounded operation ID required')
    return _exchange_live(store, session_path, operation='command',
                          query={'command_id': command_id, 'operation_id': request_id})
