"""Receiver input bindings on authenticated-observation fixtures, never real input."""
import base64
from copy import deepcopy
import os
from pathlib import Path
import time

import pytest

from kneekura_tech_hub.minecraft import input_route, runtime, native_input, verification
from kneekura_tech_hub.minecraft.storage import ContractError, Store, canonical, digest, key_for
from test_minecraft_dedicated_identity import dedicated_contract, dedicated_observation, PLAYER, OTHER, COMMON, ROLES
from test_minecraft_input_route import request


@pytest.fixture
def receiver(tmp_path,monkeypatch):
    c=dedicated_contract(); raw=dedicated_observation(c)
    raw.update(native_input={'platform':'linux-x11','process_id':os.getpid(), 'process_start':native_input.process_start(os.getpid()),
                             'window_id':'42','client_size':[640,480],'foreground':True,'cursor_mode':'disabled'},screen='none')
    image=b'\x89PNG\r\n\x1a\nfixture'; raw.update(png_b64=base64.b64encode(image).decode(),png_sha256=digest(image))
    session={'token':'a'*64,'contract':c,'directory':str(tmp_path),'endpoint_path':str(tmp_path/'endpoint.json'),
             'connection_policy':c['connection_policy']}
    path=tmp_path/'session.json'; path.write_bytes(canonical(session)); path.chmod(0o600)
    reg={'schema_version':1,'backend':native_input.BACKEND_ID,'enabled':True,'session_file':str(path),
         'display':':0','allowed_controls':['mouse:right'],'timeout_seconds':5}
    store=Store(tmp_path/'cas'); calls=[]
    def observer(store,path,*,operation,query=None,timeout=10):
        calls.append(('observe',operation,query))
        data=deepcopy(raw)
        if operation=='logs': data={'identity':data['identity'],'logs':[]}
        evaluated=verification.evaluate_observation(c,data) if operation=='client' else {'status':'OK'}
        return dict(evaluated,artifact_hash=store.put_json(data),handshake_hash=store.put_json({'ready':True,'identity':data['identity']}),
                    evidence_level='AUTHENTICATED_LIVE_OBSERVER')
    def native(display,target,*,deadline,position=None,hold_ms=None):
        calls.append(('native',position))
        return {'pressed':True,'released':True} if position is not None else {'client_size':[640,480],'foreground':True}
    monkeypatch.setattr(runtime,'observe_live',observer); monkeypatch.setattr(native_input,'native_exchange',native)
    return store,reg,c,raw,calls


def test_receiver_binding_retains_full_role_identity_and_connection_scope(receiver):
    store,reg,c,raw,calls=receiver; binding=input_route.bind(store,reg)
    assert set(binding['identity'])==set(COMMON+ROLES['dedicated_client'])
    record=store.json(binding['binding_hash'])
    assert record['connection']==raw['connection']
    assert calls[0][2]['entity_uuids']==[PLAYER]
    first_target=binding['target_id']
    raw['connection']['channel_id']='second-channel'; raw['entities'][0]['connection']=deepcopy(raw['connection'])
    assert input_route.bind(store,reg)['target_id']!=first_target


@pytest.mark.parametrize('fault',['channel','port','player','memory','disconnected','epoch','policy_hash','directory','server_ref'])
def test_receiver_changes_block_before_any_native_press(receiver,fault):
    store,reg,c,raw,calls=receiver; binding=input_route.bind(store,reg)
    if fault=='channel': raw['connection']['channel_id']='new-connection'
    if fault=='port': raw['connection']['local']['port']=40124
    if fault=='player': raw['connection']['player_uuid']=OTHER
    if fault=='memory': raw['connection']['memory']=True
    if fault=='disconnected': raw['connection']['connected']=False
    if fault=='epoch': raw['identity']['session_epoch']='new-epoch'
    if fault=='policy_hash': raw['identity']['connection_policy_hash']='e'*64
    if fault=='directory': raw['identity']['run_directory_id']='other'
    if fault=='server_ref': raw['identity']['server_contract_hash']='e'*64
    raw['entities'][0]['connection']=deepcopy(raw['connection'])
    result=input_route.dispatch_registered(store,reg,binding['binding_hash'],request(binding))
    assert result['input_status']=='BLOCKED'
    assert not any(row[0]=='native' and row[1] is not None for row in calls)


def test_receiver_valid_dispatch_reuses_existing_no_gameplay_pass_boundary(receiver):
    store,reg,c,raw,calls=receiver; binding=input_route.bind(store,reg)
    result=input_route.dispatch_registered(store,reg,binding['binding_hash'],request(binding))
    assert result['input_status']=='COMPLETED' and result['outcome']=='NOT_RUN'
    assert all(value=='NOT_RUN' for value in result['verification'].values())


def test_receiver_query_for_another_player_is_rejected_before_transport(tmp_path,monkeypatch):
    c=dedicated_contract(); session=tmp_path/'session.json'
    session.write_bytes(canonical({'token':'a'*64,'contract':c,'endpoint_path':str(tmp_path/'absent.json')})); session.chmod(0o600)
    with pytest.raises(ContractError,match='selected|player|UUID'):
        runtime.observe_live(Store(tmp_path/'cas'),str(session),operation='client',query={'entity_uuids':[OTHER]})


def test_receiver_native_capture_requests_independent_staff_state(receiver):
    store,reg,c,raw,calls=receiver
    input_route.bind(store,reg)
    assert calls[0][2].get('staff_state') is True
