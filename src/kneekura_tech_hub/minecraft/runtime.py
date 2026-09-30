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
import socket
import threading
import time
import uuid
import zipfile
from pathlib import Path
from urllib.parse import urlsplit

from . import index, verification, dependencies
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


def dedicated_registry(registry: dict, contract: dict | None = None):
    role = registry.get('runtime_role')
    if role is None:
        if any(k in registry for k in ('runtime_scope', 'dependency_inventory_hash', 'target_selection')):
            raise ContractError('Scoped runtime authority requires an explicit versioned role')
        if contract is not None and (contract.get('schema_version') in (2,3) or contract.get('session_role') is not None):
            raise ContractError('Dedicated runtime role must be explicitly registered')
        return None, None
    if not isinstance(role, str) or role not in (*verification.V2_ROLE_FIELDS, 'integrated_client'):
        raise ContractError('Unsupported registered runtime role')
    if registry.get('runtime_scope') != dependencies.RUNTIME_SCOPE:
        raise ContractError('Explicit registered target-code/dependency-byte scope required')
    valid_hash(registry.get('dependency_inventory_hash'))
    valid_hash(registry.get('export_receipt_hash'))
    if contract is not None and (contract.get('runtime_scope') != registry['runtime_scope']
            or contract.get('dependency_inventory_hash') != registry['dependency_inventory_hash']):
        raise ContractError('Contract dependency authority differs from registered scope/inventory')
    if role == 'integrated_client':
        from .target_selection import validate_shape
        selection = validate_shape(registry.get('target_selection'))
        if any(k in registry for k in verification.INTEGRATED_FORBIDDEN):
            raise ContractError('Integrated client cannot have dedicated connection authority')
        if contract is not None and (contract.get('schema_version') != 3
                or contract.get('session_role') != role or contract.get('target_selection_hash') != key_for(selection)
                or any(k in contract for k in verification.INTEGRATED_FORBIDDEN)):
            raise ContractError('Integrated contract differs from registered target selection')
        return role, None
    if 'target_selection' in registry:
        raise ContractError('Selected U04 targets require the schema3 integrated role')
    policy = verification.validate_connection_policy(registry.get('connection_policy'))
    if contract is not None:
        if contract.get('schema_version') != 2 or contract.get('session_role') != role:
            raise ContractError('Contract differs from registered dedicated role')
        if (contract.get('connection_policy') != policy
                or contract.get('connection_policy_hash') != key_for(policy)):
            raise ContractError('Contract connection policy differs from registered authority')
    if role == 'dedicated_client':
        player = verification._canonical_uuid(registry.get('player_uuid'))
        valid_hash(registry.get('server_contract_hash'))
        if player not in policy['player_uuids']:
            raise ContractError('Receiving player is outside registered policy')
        if contract is not None and (contract.get('player_uuid') != player
                or contract.get('server_contract_hash') != registry['server_contract_hash']):
            raise ContractError('Receiver server reference/player differs from registered authority')
    return role, policy


def _pinned_dedicated_profile(profile: dict):
    body = {k: v for k, v in profile.items() if k not in ('profile_id', 'profile_hash')}
    manifest = profile.get('manifest', {})
    if (profile.get('profile_id') != profile.get('profile_hash')
            or key_for(body) != profile.get('profile_id') or profile.get('identity_status') != 'PINNED_TARGET_CODE'
            or profile.get('coverage', {}).get('complete') is not False
            or profile.get('coverage', {}).get('target_complete') is not True
            or profile.get('coverage', {}).get('scope') != 'TARGET_CODE'
            or manifest.get('runtime_scope') != dependencies.RUNTIME_SCOPE
            or not isinstance(manifest.get('loader_version'), str)
            or not re.fullmatch(r'\d+(?:\.\d+)+', manifest['loader_version'])):
        raise ContractError('Dedicated runtime requires an exact pinned target-code scoped profile')
    valid_hash(manifest.get('dependency_inventory_hash'))
    roots = profile.get('roots'); coverage = profile['coverage']
    if (not isinstance(roots, list) or not roots
            or any(not isinstance(root, dict) or root.get('status') != 'OK'
                   or (str(root.get('id', '')).startswith('dependency:')
                       and root.get('id') not in coverage.get('selected_target_root_ids', []))
                   or root.get('role') not in ('source', 'resources', 'binary', 'configuration', 'dependency') for root in roots)
            or coverage.get('requested_roots') != [root['id'] for root in roots]
            or coverage.get('analyzed_roots') != coverage['requested_roots']
            or coverage.get('unresolved_roots') != [] or coverage.get('exclusions') != []
            or coverage.get('dependency_bytes_complete') is not True):
        raise ContractError('Scoped runtime cannot relabel incomplete or dependency-analysis roots')



def _profile_dependencies(store: Store, registry: dict, profile: dict, contract: dict | None = None):
    _pinned_dedicated_profile(profile)
    manifest = profile['manifest']
    bundle = dependencies.validate_target_profile(store, registry, profile)
    inventory = bundle['dependency_inventory']
    if (manifest.get('runtime_scope') != registry.get('runtime_scope')
            or manifest.get('dependency_inventory_hash') != bundle['dependency_inventory_hash']
            or manifest.get('compile_receipt_hash') != registry.get('build_receipt_hash')
            or manifest.get('workspace') != inventory['workspace']
            or manifest.get('dirty_hash') != inventory['source_generation']
            or manifest.get('configuration_fingerprint') != inventory['configuration_fingerprint']):
        raise ContractError('Target profile differs from registered dependency/export/build authority')
    if contract is not None and (contract.get('runtime_scope') != manifest['runtime_scope']
            or contract.get('dependency_inventory_hash') != bundle['dependency_inventory_hash']):
        raise ContractError('Contract differs from profile dependency scope/inventory')
    return bundle


def resolve_server_contract(store: Store, registry: dict, *, manifest: dict,
                            artifact_hash: str, source_revision: str) -> dict:
    """Resolve immutable peer authority without equating different runtime profiles/configs."""
    role, policy = dedicated_registry(registry)
    if role != 'dedicated_client': raise ContractError('Receiving-client registration required')
    server = store.json(valid_hash(registry.get('server_contract_hash')))
    if (not isinstance(server, dict) or server.get('schema_version') != 2
            or server.get('session_role') != 'dedicated_server'
            or server.get('adapter_id') != ADAPTER_ID or server.get('adapter_version') != ADAPTER_VERSION
            or verification._identity_errors(server, {'identity': server})):
        raise ContractError('Referenced contract is not a valid dedicated server')
    server_policy = verification.validate_connection_policy(server.get('connection_policy'))
    if key_for(server_policy) != server.get('connection_policy_hash') or server_policy != policy:
        raise ContractError('Referenced server uses a different connection policy')
    if server.get('build_artifact_hash') != artifact_hash or server.get('source_revision') != source_revision:
        raise ContractError('Referenced server build/source differs from the actual local runtime artifact')
    snapshot = index._load(store, server['index_snapshot_id']); profile = snapshot['profile']
    inventory = store.json(server['dependency_inventory_hash'])
    if not isinstance(inventory, dict): raise ContractError('Referenced dependency inventory is malformed')
    _profile_dependencies(store, dict(workspace=inventory.get('workspace'),
        runtime_scope=server['runtime_scope'], dependency_inventory_hash=server['dependency_inventory_hash'],
        export_receipt_hash=inventory.get('export_receipt_hash'),
        build_receipt_hash=profile['manifest'].get('compile_receipt_hash')), profile, server)
    body = {k: v for k, v in profile.items() if k not in ('profile_id', 'profile_hash')}
    if (profile.get('profile_id') != server['profile_id'] or profile.get('profile_hash') != server['profile_id']
            or key_for(body) != server['profile_id']):
        raise ContractError('Referenced server profile identity is unverified')
    other = profile['manifest']
    fields = ('minecraft', 'loader', 'loader_version', 'java_major')
    if (any(other.get(k) != manifest.get(k) for k in fields)
            or other.get('minecraft') != '1.20.1' or other.get('loader') != 'forge'
            or other.get('java_major') != 17 or other.get('physical_side') != 'server'
            or other.get('workspace_revision') != source_revision
            or other.get('dirty_hash') != server.get('dirty_hash')):
        raise ContractError('Referenced server target/profile is incompatible with receiver')
    return server


def create_session(store: Store,registry: dict,contract: dict,*,directory: Path):
    errors=verification._identity_errors(contract,{'identity':contract})
    if errors: raise ContractError('; '.join(errors))
    if contract['adapter_id']!=ADAPTER_ID or contract['adapter_version']!=ADAPTER_VERSION:
        raise ContractError('Wrong runtime observer version')
    role, policy = dedicated_registry(registry, contract)
    root=_workspace(registry.get('workspace')); directory=Path(directory)
    if directory.is_symlink() or not directory.is_dir() or not directory.resolve().is_relative_to(root):
        raise ContractError('Session directory must be inside the registered workspace')
    from .execution import _world_destination, _owned_client_directory, _owned_world
    directory=directory.resolve()
    if role == 'dedicated_client':
        marker, _ = _owned_client_directory(root, str(directory))
        if any(contract.get(k) != marker[k] for k in ('run_directory_id', 'run_directory_template_hash')):
            raise ContractError('Receiver contract differs from prepared client directory')
    else:
        world_layout=registry.get('world_layout','client' if role == 'integrated_client' else 'server')
        world=_world_destination(directory,registry.get('world_directory_name','gametestserver'),world_layout)
        if role in ('dedicated_server', 'integrated_client'):
            marker, _ = _owned_world(root, str(world), layout='client' if role == 'integrated_client' else 'server')
            if any(contract.get(k) != marker[k] for k in ('world_id', 'world_template_hash')):
                raise ContractError('Server contract differs from prepared world')
    snapshot=index._load(store,contract['index_snapshot_id']); p=snapshot['profile']; m=p['manifest']
    if role is None and any(k in m for k in ('runtime_scope', 'dependency_inventory_hash', 'target_selection')):
        raise ContractError('Scoped target profile cannot be downgraded to a legacy session')
    if p['profile_id']!=contract['profile_id'] or m['minecraft']!='1.20.1' or m['loader']!='forge' or m.get('java_major')!=17:
        raise ContractError('Runtime requires the pinned Forge 1.20.1 / Java17 profile')
    dependency_bundle = _profile_dependencies(store, registry, p, contract) if role else None
    if role and m.get('physical_side') != contract['physical_side']:
        raise ContractError('Dedicated profile physical side differs from contract')
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
    try: rows,original=_collect(artifact,artifact_kind,Limits(),problems,ignored,store.root)
    except (OSError, ValueError, zipfile.BadZipFile) as exc:
        raise ContractError('Build capture is incomplete') from exc
    if problems or ignored: raise ContractError('Build capture is incomplete')
    actual_hash=digest(original) if original is not None else key_for([{'path':n,'hash':digest(data)} for n,data in sorted(rows)])
    if actual_hash!=contract['build_artifact_hash']:
        raise ContractError('Packaged/compiled build artifact differs from run contract')
    receipt=store.json(valid_hash(registry.get('build_receipt_hash')))
    if (receipt.get('request',{}).get('kind')!='compile' or receipt['request'].get('workspace')!=str(root) or
        receipt.get('result',{}).get('outcome')!='PASS' or receipt.get('source_generation')!=current or
        receipt.get('source_generation_after')!=current or not any(o.get('content_hash')==contract['build_artifact_hash'] for o in receipt.get('outputs',[]))):
        raise ContractError('No successful same-source compile receipt for this build artifact')
    server_contract = None
    if role == 'dedicated_client':
        server_contract = resolve_server_contract(store, registry, manifest=m, artifact_hash=actual_hash,
                                                  source_revision=contract['source_revision'])
    probes=[]
    for name,data in rows:
        if name.endswith('.class'):
            if len(probes)>=20000: raise ContractError('Target class probe budget exceeded')
            probes.append({'resource':name,'sha256':digest(data)})
    if not probes: raise ContractError('Build JAR has no class resources to identify')
    commands=registry.get('command_registry',{})
    if not isinstance(commands,dict) or len(commands)>100 or any(not isinstance(k,str) or not re.fullmatch(r'[A-Za-z0-9_.-]{1,80}',k) or not isinstance(v,str) or not v or len(v)>2000 for k,v in commands.items()):
        raise ContractError('Command registry must map bounded IDs to explicit commands')
    session={'schema_version':contract['schema_version'],'token':secrets.token_hex(32),'contract':contract,
             'expected_runtime':{'minecraft':m['minecraft'],'forge':m['loader_version'],'java_major':17},
             'build_artifact':str(artifact.resolve()),'build_artifact_kind':artifact_kind,'build_receipt_hash':registry['build_receipt_hash'],
             'class_probes':probes,'config_files':config,'command_registry':commands,
             'directory':str(directory),
             'endpoint_path':str(directory/'endpoint.json'),'report_path':str(directory/'gametest-report.json')}
    if role:
        if policy is not None: session['connection_policy'] = policy
        session['dependency_inventory'] = dependency_bundle['dependency_inventory']
        session['dependency_files'] = dependency_bundle['dependency_files']
    if role == 'integrated_client':
        from .target_selection import validate_selection
        target = validate_selection(store, registry, dependency_bundle['dependency_inventory'])
        session.update(target_selection=target['target_selection'],
                       target_dependency_probes=target['target_dependency_probes'])
    if role == 'dedicated_client':
        session.update(server_contract=server_contract, server_contract_hash=registry['server_contract_hash'],
                       player_uuid=registry['player_uuid'])
    else:
        session.update(world=str(world), world_layout=world_layout)
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
        deadline=time.monotonic()+self.timeout
        conn=http.client.HTTPConnection('127.0.0.1',self.port,timeout=self.timeout)
        timer=None; response=None
        try:
            conn.connect()  # Numeric loopback only; this request owns the socket.
            sock=conn.sock
            remaining=deadline-time.monotonic()
            if remaining<=0: raise TimeoutError('Observer deadline expired')
            def expire():
                # Idle socket timeouts alone can be defeated by a byte drip.
                try: sock.shutdown(socket.SHUT_RDWR)
                except OSError: pass
            timer=threading.Timer(remaining,expire); timer.daemon=True; timer.start()
            conn.request(method,path,body=raw,headers=headers)
            response=conn.getresponse(); payload=response.read(MAX_RESPONSE+1)
            if time.monotonic()>=deadline: raise TimeoutError('Observer deadline expired')
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
        finally:
            if timer is not None:
                timer.cancel(); timer.join()
            if response is not None: response.close()
            conn.close()


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


def _exchange_live(store: Store,session_path: str,*,operation='observe',query=None,timeout=10):
    s=load_session(session_path)
    if s['contract'].get('session_role') == 'dedicated_client' and operation in ('client', 'observe'):
        if query is not None and not isinstance(query, dict): raise ContractError('Selected-player query must be an object')
        query = dict(query or {})
        player = s['contract']['player_uuid']
        if query.get('entity_uuids', [player]) != [player]:
            raise ContractError('Receiver may query only its selected local player UUID')
        if type(query.get('limit', 1)) is not int or query.get('limit', 1) != 1:
            raise ContractError('Receiver selected-player limit must be exactly one')
        query.update(entity_uuids=[player], limit=1)
    endpoint=Path(s['endpoint_path'])
    if endpoint.is_symlink() or endpoint.stat().st_size>65536: raise ContractError('Invalid observer endpoint file')
    e=json.loads(endpoint.read_bytes())
    client=BridgeClient(e['url'],s['token'],s['contract'],timeout=timeout)
    deadline=time.monotonic()+timeout
    hello=client.request('/v1/handshake')
    if hello.get('ready') is not True or verification._identity_errors(s['contract'],hello):
        raise ContractError('Live handshake did not verify the expected build/session/world')
    if operation not in ('observe','logs','client','command','operation'): raise ContractError('Unknown observer operation')
    client.timeout=deadline-time.monotonic()
    if client.timeout<=0:
        raise ContractError('Observer deadline expired; do not retry writes')
    raw=client.request('/v1/'+operation,query or {})
    if verification._identity_errors(s['contract'],raw): raise ContractError('Observation belongs to another run')
    h=store.put_json(raw); hello_hash=store.put_json(hello)
    for item in (h,hello_hash): store.pin(item,'live:'+s['contract']['run_id'])
    if operation in ('observe','client'):
        result=verification.evaluate_observation(s['contract'],raw)
    elif operation in ('command','operation'):
        result=verification.evaluate_operation_receipt(s['contract'],raw,
            expected_request_id=(query or {}).get('operation_id'),
            expected_command_id=(query or {}).get('command_id'))
    else: result={'status':'OK','outcome':'NOT_RUN','results':raw.get('logs',[])}
    result.update(artifact_hash=h,handshake_hash=hello_hash,evidence_level='AUTHENTICATED_LIVE_OBSERVER',
                  note='Observation is not itself a passing behaviour/rendering assertion')
    return result


def observe_live(store: Store, session_path: str, *, operation='observe', query=None, timeout=10):
    if operation not in ('observe', 'logs', 'client', 'operation'):
        raise ContractError('Observe is a read-only operation surface')
    return _exchange_live(store, session_path, operation=operation, query=query, timeout=timeout)


def execute_registered_command(store: Store, session_path: str, *, command_id: str, request_id: str):
    """Explicit mutation path, separate from observation. Never retry automatically."""
    session = load_session(session_path)
    if command_id not in session.get('command_registry', {}):
        raise ContractError('Command ID is not in the explicitly trusted registry')
    if not isinstance(request_id, str) or not re.fullmatch(r'[A-Za-z0-9_.-]{1,128}', request_id):
        raise ContractError('Bounded operation ID required')
    return _exchange_live(store, session_path, operation='command',
                          query={'command_id': command_id, 'operation_id': request_id})
