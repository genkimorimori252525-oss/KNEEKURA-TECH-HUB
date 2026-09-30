"""Dedicated role/connection fixtures; no Minecraft or network operations."""
from copy import deepcopy
import uuid

import pytest

from kneekura_tech_hub.minecraft import verification as api, input_contract
from kneekura_tech_hub.minecraft.storage import ContractError, key_for
from test_minecraft_verification import contract as legacy_contract, observation

PLAYER='11111111-1111-4111-8111-111111111111'
OTHER='22222222-2222-4222-8222-222222222222'
COMMON=('schema_version','session_role','run_id','session_epoch','profile_id','index_snapshot_id',
        'build_artifact_hash','source_revision','dirty_hash','scenario_hash','assertion_hash','config_hash',
        'physical_side','logical_side','adapter_id','adapter_version','connection_policy_hash',
        'runtime_scope','dependency_inventory_hash')
ROLES={'dedicated_server':('world_id','world_template_hash','world_seed'),
       'dedicated_client':('run_directory_id','run_directory_template_hash','server_contract_hash','player_uuid')}


def policy(): return {'host':'127.0.0.1','port':25565,'player_uuids':[PLAYER,OTHER]}


def dedicated_contract(role='dedicated_client'):
    c=legacy_contract(); c.update(schema_version=2,session_role=role,connection_policy=policy(),
                                 connection_policy_hash=key_for(policy()), runtime_scope='TARGET_CODE_AND_DEPENDENCY_BYTES',
                                 dependency_inventory_hash='d'*64)
    if role=='dedicated_client':
        for key in ('world_id','world_template_hash','world_seed'): c.pop(key)
        c.update(run_directory_id='client-run',run_directory_template_hash='a'*64,
                 server_contract_hash='b'*64,player_uuid=PLAYER,physical_side='client',logical_side='client',
                 assertion_domain='client_observation',expected_tests=[])
    else: c.update(assertion_domain='server_observation',expected_tests=[])
    c['assertion_hash']=key_for({'assertion_domain':c['assertion_domain'],'expected_tests':[], 'expected_required':{}})
    return c


def connection(role='dedicated_client',player=PLAYER):
    client={'player_uuid':player,'connected':True,'memory':False,'channel_id':'fixture-channel',
            'local':{'host':'127.0.0.1','port':40123},'remote':{'host':'127.0.0.1','port':25565}}
    if role=='dedicated_server': client['local'],client['remote']=client['remote'],client['local']
    return client


def dedicated_observation(c=None):
    c=c or dedicated_contract(); out=observation(c)
    out['identity']={k:c[k] for k in COMMON+ROLES[c['session_role']]}
    row=out['entities'][0]; row['uuid']=c.get('player_uuid',PLAYER); row['connection']=connection(c['session_role'])
    if c['session_role']=='dedicated_client':
        out.update(observation_side='logical_client',client_tick_start=30,client_tick_end=32,
                   client_frame_start=60,client_frame_end=65,server_tick_start=None,server_tick_end=None,
                   server_tick_scope='NOT_LOCALLY_OBSERVED',connection=connection())
    return out


def test_v1_identity_fields_and_validation_remain_unchanged():
    c=legacy_contract()
    assert api.identity_fields(c)==api.IDENTITY_FIELDS
    assert api._identity_errors(c,{'identity':{k:c[k] for k in api.IDENTITY_FIELDS}})==[]


@pytest.mark.parametrize('role',ROLES)
def test_v2_has_exact_role_fields(role):
    c=dedicated_contract(role)
    assert set(api.identity_fields(c))==set(COMMON+ROLES[role])
    assert api._identity_errors(c,{'identity':{k:c[k] for k in api.identity_fields(c)}})==[]


@pytest.mark.parametrize('role',ROLES)
def test_each_v2_identity_field_is_bound(role):
    c=dedicated_contract(role)
    for field in COMMON+ROLES[role]:
        actual={k:c[k] for k in COMMON+ROLES[role]}; actual[field]='tampered'
        assert api._identity_errors(c,{'identity':actual}),field


@pytest.mark.parametrize('fault',['schema','bool_schema','role','wrong_side','fake_world','fake_world_null','bad_uuid','bad_hash','downgrade'])
def test_wrong_role_or_fake_remote_world_is_rejected(fault):
    c=dedicated_contract()
    if fault=='schema': c['schema_version']=3
    if fault=='bool_schema': c['schema_version']=True
    if fault=='role': c['session_role']='integrated_client'
    if fault=='wrong_side': c['logical_side']='server'
    if fault=='fake_world': c['world_seed']=0
    if fault=='fake_world_null': c['world_id']=None
    if fault=='bad_uuid': c['player_uuid']='not-uuid'
    if fault=='bad_hash': c['server_contract_hash']='unknown'
    if fault=='downgrade': c['schema_version']=1
    assert api._identity_errors(c,{'identity':c})


@pytest.mark.parametrize('change',[{'host':'localhost'},{'host':'0.0.0.0'},{'port':True},{'port':25565.0},
                                  {'port':0},{'port':65536},{'port':'*'},{'player_uuids':[]},
                                  {'player_uuids':[PLAYER,PLAYER]},{'player_uuids':[PLAYER,OTHER,str(uuid.uuid4())]},
                                  {'player_uuids':['11111111111141118111111111111111']},{'unknown':1}])
def test_policy_rejects_unbounded_or_nonliteral_authority(change):
    with pytest.raises(ContractError): api.validate_connection_policy(dict(policy(),**change))


def test_valid_policy_is_detached_and_exact():
    p=policy(); validated=api.validate_connection_policy(p)
    assert validated==p
    p['player_uuids'].clear(); assert validated['player_uuids']==[PLAYER,OTHER]


@pytest.mark.parametrize('role',ROLES)
def test_role_observation_preserves_independent_intervals_without_success(role):
    c=dedicated_contract(role); raw=dedicated_observation(c)
    result=api.evaluate_observation(c,raw)
    assert result['status']=='OK' and result['outcome']=='NOT_RUN' and result['atomic'] is False
    if role=='dedicated_client':
        assert result['observation_interval']['client_tick_start']==30
        assert result['observation_interval']['client_tick_end']==32
        assert result['observation_interval']['server_tick_start'] is None
        assert result['server_tick_scope']=='NOT_LOCALLY_OBSERVED'
    else: assert result['observation_interval']['server_tick_start']==10


@pytest.mark.parametrize('fault',['server_tick','server_scope','client_tick_missing','frame_missing','client_tick_reverse',
                                 'client_tick_bool','observation_side','wrong_player','extra_player','connection_absent',
                                 'connection_changed','connection_memory','connection_disconnected','connection_wrong_port',
                                 'connection_nonloopback','connection_bool_port','connection_bad_channel'])
def test_receiver_observation_never_invents_server_or_other_player_evidence(fault):
    c=dedicated_contract(); raw=dedicated_observation(c)
    if fault=='server_tick': raw['server_tick_start']=raw['server_tick_end']=1
    if fault=='server_scope': raw['server_tick_scope']='LOCAL'
    if fault=='client_tick_missing': raw['client_tick_start']=None
    if fault=='frame_missing': raw['client_frame_start']=raw['client_frame_end']=None
    if fault=='client_tick_reverse': raw['client_tick_end']=0
    if fault=='client_tick_bool': raw['client_tick_start']=True
    if fault=='observation_side': raw['observation_side']='logical_server'
    if fault=='wrong_player': raw['entities'][0]['uuid']=OTHER
    if fault=='extra_player': raw['entities'].append(deepcopy(raw['entities'][0]))
    if fault=='connection_absent': raw.pop('connection')
    if fault=='connection_changed': raw['entities'][0]['connection']['channel_id']='other'
    if fault=='connection_memory': raw['connection']['memory']=True
    if fault=='connection_disconnected': raw['connection']['connected']=False
    if fault=='connection_wrong_port': raw['connection']['remote']['port']=25566
    if fault=='connection_nonloopback': raw['connection']['local']['host']='::1'
    if fault=='connection_bool_port': raw['connection']['local']['port']=True
    if fault=='connection_bad_channel': raw['connection']['channel_id']=''
    assert api.evaluate_observation(c,raw)['status']!='OK'


def test_server_selected_connection_must_bind_actual_policy_port():
    c=dedicated_contract('dedicated_server'); raw=dedicated_observation(c)
    raw['entities'][0]['connection']['local']['port']=25566
    assert api.evaluate_observation(c,raw)['status']!='OK'


def test_input_v2_requires_all_role_fields_and_rejects_world_substitution():
    c=dedicated_contract(); identity={k:c[k] for k in COMMON+ROLES['dedicated_client']}
    request={'schema_version':1,'operation_id':'fixture','identity':identity,'target_id':'window:1',
             'control':'mouse:right','position':[1,1],'hold_ms':1}
    assert input_contract._validate(c,request,'window:1',['mouse:right'],2)==request
    for field in ROLES['dedicated_client']+('connection_policy_hash',):
        bad=deepcopy(request); bad['identity'].pop(field)
        with pytest.raises(ContractError): input_contract._validate(c,bad,'window:1',['mouse:right'],2)
    bad=deepcopy(request); bad['identity']['world_seed']=0
    with pytest.raises(ContractError): input_contract._validate(c,bad,'window:1',['mouse:right'],2)


@pytest.mark.parametrize('bad',[[],{},None,1,True])
def test_nonstr_role_is_rejected_as_contract_error(bad):
    c=dedicated_contract(); c['session_role']=bad
    assert api._identity_errors(c,{'identity':c})
