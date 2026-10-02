"""Fixed before/use/after evidence controls; synthetic records are never a live test."""
from copy import deepcopy
import importlib.util
import json
from pathlib import Path

import pytest

from kneekura_tech_hub.minecraft import runtime_pair, verification
from kneekura_tech_hub.minecraft.storage import canonical, digest, key_for
from test_minecraft_runtime_pair import paired, PLAYER

FIXTURE = Path(__file__).resolve().parents[1]/'tools/ci/mod_ai_staff'

def checker():
    path=FIXTURE/'verify_client.py'
    spec=importlib.util.spec_from_file_location('fixed_staff_client_evidence',path)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    return module


def packet_trace():
    return {'schema_version':1,'supported':True,'scope':'SELECTED_VANILLA_RECEIPT_NOT_PROCESSING_ATTESTATION',
            'player_uuid':PLAYER,'channel_id':'client-channel','entity_id':3,'active':True,
            'sequence':0,'glowing_count':0,'cooldown_count':0,'unknown':0,'dropped':0,'limit':16,'records':[]}


def call_trace():
    return {'schema_version':1,'supported':True,'status':'CAPTURED','limit':16,
            'started':0,'completed':0,'unknown':0,'dropped':0,'records':[]}


@pytest.fixture
def use_records(paired):
    store,paths,sc,cc,samples,calls=paired
    fixed_hash=digest((FIXTURE/'assertions.json').read_bytes())
    for contract in (sc,cc):
        contract.update(expected_tests=[],expected_required={})
        contract['assertion_hash']=key_for({'assertion_domain':contract['assertion_domain'],
            'expected_tests':[],'expected_required':{}})
        contract['scenario_hash']=store.put_json({'fixed_assertions_sha256':fixed_hash,
            'assertion_domain':contract['assertion_domain']})
    cc['server_contract_hash']=store.put_json(sc)
    for side,contract in [('server',sc),('client',cc)]:
        path=Path(paths[side]); data=json.loads(path.read_bytes());data['contract']=contract;path.write_bytes(canonical(data))
    for sample,contract in zip(samples,(sc,cc,sc)):sample['identity']=contract
    samples[1]['staff_packet_trace']=packet_trace();samples[1]['staff_client_trace']=call_trace()
    before=runtime_pair.observe_pair(store,server_session=paths['server'],client_session=paths['client'],player_uuid=PLAYER)['artifact_hash']
    native_before=deepcopy(samples[1]);native_before.update(client_frame_start=102,client_frame_end=103)
    after_samples=deepcopy(samples)
    after_samples[0].update(server_tick_start=20,server_tick_end=21)
    after_samples[2].update(server_tick_start=22,server_tick_end=23)
    after_samples[1].update(client_frame_start=130,client_frame_end=131,client_tick_start=15,client_tick_end=15)
    for sample in after_samples:
        state=sample['entities'][0]['staff_state']
        state['glowing']={'amplifier':0,'duration_ticks':50}
        state['staff_cooldown'].update(active=True,fraction=0.9)
    after_packets=after_samples[1]['staff_packet_trace']
    after_packets.update(sequence=2,glowing_count=1,cooldown_count=1,records=[
        {'sequence':1,'player_uuid':PLAYER,'kind':'glowing','entity_id':3,'effect':'minecraft:glowing','amplifier':0,'duration_ticks':60},
        {'sequence':2,'player_uuid':PLAYER,'kind':'cooldown','item':'kneekura:celestial_staff','duration_ticks':100}])
    unchanged={'health':20.0,'main_hand':{'item':'kneekura:celestial_staff','count':1,'damage':0},
               'glowing':None,'staff_cooldown':{'active':False,'fraction':0.0}}
    after_samples[1]['staff_client_trace'].update(started=1,completed=1,records=[{
        'sequence':1,'player_uuid':PLAYER,'completed':True,'unchanged':True,
        'effect_mutation_attempts':0,'cooldown_mutation_attempts':0,
        'before':deepcopy(unchanged),'after':deepcopy(unchanged)}])
    samples[:]=after_samples;calls.clear()
    after=runtime_pair.observe_pair(store,server_session=paths['server'],client_session=paths['client'],player_uuid=PLAYER)['artifact_hash']
    native_after=deepcopy(after_samples[1]);native_after.update(client_frame_start=120,client_frame_end=121)
    identity={k:cc[k] for k in verification.identity_fields(cc)}
    native_target={'process_id':41,'process_start':'1000','window_id':'123','client_size':[640,480]}
    for raw in (native_before,native_after):
        raw['native_input']=dict(native_target,platform='linux-x11',foreground=True,cursor_mode='disabled')
        raw['screen']='none'
    target='x11:'+key_for({'identity':identity,'native':native_target,'connection':samples[1]['connection']})
    binding={'kind':'native-input-binding','backend':'linux-x11-send-event-v1',
             'identity':identity,'connection':samples[1]['connection'],'target_id':target,
             'target':native_target}
    request={'schema_version':1,'operation_id':'staff-first-use','identity':identity,'target_id':target,
             'control':'mouse:right','hold_ms':50,'position':[320,240]}
    receipt={'kind':'native-input-receipt','binding_hash':store.put_json(binding),'request_hash':store.put_json(request),
             'native_completion':{'pressed':True,'released':True},
             'result':{'identity':identity,'operation_id':request['operation_id'],'target_id':target,
                       'input_status':'COMPLETED','release_completed':True,'control':'mouse:right',
                       'outcome':'NOT_RUN','release_attempted':True,
                       'retry_allowed':False,'evidence_level':'NATIVE_INPUT_ATTEMPT_NOT_GAMEPLAY_ATTESTATION'},
             'before':{'artifact_hash':store.put_json(native_before)},'after':{'artifact_hash':store.put_json(native_after)}}
    return store,{'before_pair':before,'after_pair':after,'input_receipt':store.put_json(receipt)}


def check(use_records):
    store,refs=use_records
    return checker().evaluate_client_use(store,**refs)


def alter_sample(use_records,change,*,index=1,before=False):
    store,refs=use_records;key='before_pair' if before else 'after_pair'
    pair=store.json(refs[key]);sample=pair['samples'][index]
    raw=store.json(sample['artifact_hash']);change(raw)
    sample['artifact_hash']=store.put_json(raw);refs[key]=store.put_json(pair)


def test_fixed_scoped_use_requires_both_receipts_and_independent_state(use_records):
    result=check(use_records)
    assert result['outcome']=='PASS'
    assert result['verdicts']['scoped_synchronization']=='PASS'
    assert result['verdicts']['client_handler_known_mutator_sites']=='PASS'
    assert result['product_acceptance']=='NOT_ESTABLISHED'
    assert result['evidence_level']=='RETAINED_RECORD_CONSISTENCY_NOT_LIVE_ATTESTATION'
    assert all(result['verdicts'][x]=='NOT_RUN' for x in ('visual','non_invoking_player','performance'))


@pytest.mark.parametrize('fault',['no_packet','wrong_packet_duration','wrong_packet_entity','packet_unknown',
    'packet_dropped','packet_replayed','packet_future_sequence','packet_float_entity','missing_client_effect','wrong_amplifier','late_server_sample',
    'stack_changed','no_trace','trace_unknown','trace_forged_unchanged','mutate_then_restore',
    'trace_missing_record','trace_future_sequence','empty_trace_state','null_trace_record','huge_health',
    'backwards_client_tick','backwards_client_log','wrong_thread_player','stale_epoch','fake_server_tick'])
def test_predeclared_client_faults_cannot_become_scoped_pass(use_records,fault):
    def change(raw):
        packets=raw['staff_packet_trace'];trace=raw['staff_client_trace'];state=raw['entities'][0]['staff_state']
        if fault=='no_packet': packets.update(sequence=0,glowing_count=0,cooldown_count=0,records=[])
        if fault=='wrong_packet_duration':packets['records'][0]['duration_ticks']=61
        if fault=='wrong_packet_entity':packets['records'][0]['entity_id']=4
        if fault=='packet_unknown':packets['unknown']=1
        if fault=='packet_dropped':packets['dropped']=1
        if fault=='packet_replayed':packets['records'][1]['sequence']=1
        if fault=='packet_future_sequence':packets['records'][1]['sequence']=99
        if fault=='packet_float_entity':packets['records'][0]['entity_id']=3.0
        if fault=='missing_client_effect':state['glowing']=None
        if fault=='wrong_amplifier':state['glowing']['amplifier']=1
        if fault=='stack_changed':state['main_hand']['count']=2
        if fault=='no_trace':trace.update(started=0,completed=0,records=[])
        if fault=='trace_unknown':trace.update(status='UNKNOWN')
        if fault=='trace_forged_unchanged':trace['records'][0]['after']['health']=19.0
        if fault=='mutate_then_restore':trace['records'][0]['effect_mutation_attempts']=1
        if fault=='trace_missing_record':trace['records']=[]
        if fault=='trace_future_sequence':trace['records'][0]['sequence']=99
        if fault=='empty_trace_state':trace['records'][0].update(before={},after={})
        if fault=='null_trace_record':trace['records']=[None]
        if fault=='huge_health':trace['records'][0]['before']['health']=10**400
        if fault=='backwards_client_tick':raw['client_tick_start']=raw['client_tick_end']=0
        if fault=='backwards_client_log':raw['log_sequence_start']=raw['log_sequence_end']=0
        if fault=='wrong_thread_player':trace['records'][0]['player_uuid']='00000000-0000-0000-0000-000000000001'
        if fault=='stale_epoch':raw['identity']['session_epoch']='restarted'
        if fault=='fake_server_tick':raw['server_tick_start']=raw['server_tick_end']=1
    if fault=='late_server_sample':
        alter_sample(use_records,lambda raw:raw['entities'][0]['staff_state'].update(glowing=None),index=2)
    else:alter_sample(use_records,change)
    result=check(use_records)
    assert result['outcome']!='PASS',fault


@pytest.mark.parametrize('fault',['command_substitution','handler_substitution','unknown_release','stale_input',
                                   'wrong_binding','old_frame','wrong_control','wrong_hold','wrong_coordinate',
                                   'float_coordinate','numeric_completion','capture_connection','binding_target',
                                   'capture_target','blocked_outcome','no_release_attempt'])
def test_native_input_cannot_be_replaced_or_unbound(use_records,fault):
    store,refs=use_records;receipt=store.json(refs['input_receipt'])
    if fault=='command_substitution':receipt['kind']='registered-command-receipt'
    if fault=='handler_substitution':receipt['result']['evidence_level']='GAMETEST_HANDLER'
    if fault=='unknown_release':receipt['result']['release_completed']=False
    if fault=='numeric_completion':receipt['native_completion']={'pressed':1,'released':1}
    if fault=='blocked_outcome':receipt['result']['outcome']='BLOCKED'
    if fault=='no_release_attempt':receipt['result']['release_attempted']=False
    if fault=='binding_target':
        binding=store.json(receipt['binding_hash']);binding['target']['process_id']=42
        receipt['binding_hash']=store.put_json(binding)
    if fault in ('capture_connection','capture_target'):
        raw=store.json(receipt['before']['artifact_hash'])
        if fault=='capture_connection':
            raw['connection']['channel_id']='other-channel';raw['entities'][0]['connection']['channel_id']='other-channel'
        else:raw['native_input']['window_id']='321'
        receipt['before']['artifact_hash']=store.put_json(raw)
    if fault=='stale_input':receipt['result']['identity']['session_epoch']='old'
    if fault=='wrong_binding':
        binding=store.json(receipt['binding_hash']);binding['connection']['channel_id']='other'
        receipt['binding_hash']=store.put_json(binding)
    if fault=='old_frame':
        raw=store.json(receipt['after']['artifact_hash']);raw.update(client_frame_start=1,client_frame_end=2)
        receipt['after']['artifact_hash']=store.put_json(raw)
    if fault in ('wrong_control','wrong_hold','wrong_coordinate','float_coordinate'):
        request=store.json(receipt['request_hash'])
        if fault=='wrong_control':request['control']='mouse:left'
        if fault=='wrong_hold':request['hold_ms']=True
        if fault=='wrong_coordinate':request['position']=[0,0]
        if fault=='float_coordinate':request['position']=[320.0,240.0]
        receipt['request_hash']=store.put_json(request)
    refs['input_receipt']=store.put_json(receipt)
    assert check(use_records)['outcome']=='BLOCKED'


def test_nonmatching_fixed_assertion_file_is_not_silently_used(use_records):
    store,refs=use_records
    current=store.json(refs['after_pair']);cc=store.json(current['client_contract_hash'])
    cc['scenario_hash']=store.put_json({'fixed_assertions_sha256':'0'*64})
    current['client_contract_hash']=store.put_json(cc);refs['after_pair']=store.put_json(current)
    assert check(use_records)['outcome']=='BLOCKED'


@pytest.mark.parametrize('field,value',[('minecraft','1.19.4'),('forge','47.4.0'),('java_major',21),('java_major',17.0)])
def test_each_pair_handshake_must_match_fixed_target_versions(use_records,field,value):
    store,refs=use_records;record=store.json(refs['after_pair'])
    for sample in record['samples']:
        hello=store.json(sample['handshake_hash']);hello[field]=value
        sample['handshake_hash']=store.put_json(hello)
    refs['after_pair']=store.put_json(record)
    assert check(use_records)['outcome']=='BLOCKED'


@pytest.mark.parametrize('fault',['float_schema','wrong_world','backwards_controller','wrong_domain'])
def test_pair_metadata_is_revalidated_in_retained_reader(use_records,fault):
    store,refs=use_records;record=store.json(refs['after_pair'])
    if fault=='float_schema':record['schema_version']=1.0
    if fault=='wrong_world':record['world_binding']['world_id']='different-world'
    if fault=='backwards_controller':record['samples'][2]['controller_elapsed_start']=-1
    if fault=='wrong_domain':
        cc=store.json(record['client_contract_hash'])
        scenario=store.json(cc['scenario_hash']);scenario['assertion_domain']='server_behavior'
        cc['scenario_hash']=store.put_json(scenario);record['client_contract_hash']=store.put_json(cc)
    refs['after_pair']=store.put_json(record)
    assert check(use_records)['outcome']=='BLOCKED'


def test_retained_native_shape_check_never_reads_a_live_process(monkeypatch):
    from kneekura_tech_hub.minecraft import native_input
    def forbidden(*args): raise AssertionError('A retained record must not probe a live PID')
    monkeypatch.setattr(native_input,'process_start',forbidden)
    target={'process_id':41,'process_start':'1000','window_id':'123','client_size':[640,480]}
    assert native_input.validate_target_shape(target)==target


@pytest.mark.parametrize('field',['glowing_count','cooldown_count'])
def test_cumulative_packet_counts_must_equal_complete_retained_history(use_records,field):
    for before in (True,False):
        alter_sample(use_records,lambda raw:raw['staff_packet_trace'].__setitem__(field,raw['staff_packet_trace'][field]+100),before=before)
    assert check(use_records)['outcome']=='BLOCKED'


@pytest.mark.parametrize('trace_name',['staff_packet_trace','staff_client_trace'])
def test_later_trace_cannot_rewrite_a_completed_baseline_record(use_records,trace_name):
    store,refs=use_records;module=checker()
    before=store.json(store.json(refs['before_pair'])['samples'][1]['artifact_hash'])[trace_name]
    after=store.json(store.json(refs['after_pair'])['samples'][1]['artifact_hash'])[trace_name]
    old=deepcopy(after['records'][0]);before['records']=[old]
    for record in after['records']:record['sequence']+=1
    after['records'].insert(0,deepcopy(old))
    if trace_name=='staff_packet_trace':
        before.update(sequence=1,glowing_count=1);after['sequence']+=1;after['glowing_count']+=1
        after['records'][0]['duration_ticks']=59
        call=lambda:module.packets(before,after,PLAYER,'client-channel',json.loads((FIXTURE/'assertions.json').read_bytes()))
    else:
        before.update(started=1,completed=1);after['started']+=1;after['completed']+=1
        after['records'][0]['before']['health']=19.0;after['records'][0]['after']['health']=19.0
        call=lambda:module.client_calls(before,after,PLAYER)
    with pytest.raises(module.ContractError,match='history'):
        call()
