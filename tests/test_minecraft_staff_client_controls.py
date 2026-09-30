"""Fixed control/repeat/expiry records; all game observations here are synthetic."""
from copy import deepcopy
import importlib.util
import json
from pathlib import Path

import pytest

from kneekura_tech_hub.minecraft import verification
from kneekura_tech_hub.minecraft.storage import canonical, key_for
from test_minecraft_runtime_pair import paired, PLAYER
from test_minecraft_staff_client_evidence import use_records as first_use_fixture, packet_trace, call_trace, checker

CONTROL='00000000-0000-4000-8000-000000000002'
MODULE=Path(__file__).resolve().parents[1]/'tools/ci/mod_ai_staff/verify_controls.py'


def module():
    spec=importlib.util.spec_from_file_location('fixed_staff_controls',MODULE)
    result=importlib.util.module_from_spec(spec);spec.loader.exec_module(result);return result


def clone_pair(store, ref, tick, frame, mode='active', control=False):
    pair=store.json(ref);sc=store.json(pair['server_contract_hash']);cc=store.json(pair['client_contract_hash'])
    if control:
        cc.update(player_uuid=CONTROL,run_id='control-run',session_epoch='control-epoch',run_directory_id='control-directory')
        pair.update(player_uuid=CONTROL,client_directory_id=cc['run_directory_id'],client_contract_hash=store.put_json(cc))
    for index,sample in enumerate(pair['samples']):
        raw=store.json(sample['artifact_hash']);row=raw['entities'][0]
        observed=tick+(2 if index==2 else 1 if index==1 else 0)
        if index==1:raw.update(client_frame_start=frame,client_frame_end=frame+1,client_tick_start=frame//5,client_tick_end=frame//5)
        else:raw.update(server_tick_start=observed,server_tick_end=observed+1)
        state=row['staff_state'];remaining=max(0,81-frame//5) if index==1 else max(0,76-observed)
        cool=max(0,121-frame//5)/100 if index==1 else max(0,116-observed)/100
        state['glowing']=dict(amplifier=0,duration_ticks=remaining) if mode=='active' and remaining else None
        state['staff_cooldown'].update(active=cool>0 and mode!='neutral',fraction=cool if mode!='neutral' else 0.0)
        if control:
            raw['identity']=cc if index==1 else sc;row['uuid']=CONTROL
            conn=row['connection'];conn['player_uuid']=CONTROL;conn['channel_id']=('client' if index==1 else 'server')+'-control'
            conn['local' if index==1 else 'remote']['port']=32124
            if index==1:
                raw['connection']=deepcopy(conn);raw['staff_packet_trace']=dict(packet_trace(),player_uuid=CONTROL,channel_id='client-control')
                raw['staff_client_trace']=call_trace()
            hello=store.json(sample['handshake_hash']);hello['identity']=raw['identity'];sample['handshake_hash']=store.put_json(hello)
        sample['artifact_hash']=store.put_json(raw)
    return store.put_json(pair)


def edit_pair(store,refs,key,change,index=1):
    pair=store.json(refs[key]);sample=pair['samples'][index];raw=store.json(sample['artifact_hash']);change(raw)
    sample['artifact_hash']=store.put_json(raw);refs[key]=store.put_json(pair)


def repeat_receipt(store, first, before_ref, after_ref):
    receipt=store.json(first);request=store.json(receipt['request_hash']);request['operation_id']='staff-repeat-use'
    receipt['request_hash']=store.put_json(request);receipt['result']['operation_id']=request['operation_id']
    for key,ref,frame in [('before',before_ref,160),('after',after_ref,170)]:
        pair=store.json(ref);raw=store.json(pair['samples'][1]['artifact_hash']);original=store.json(receipt[key]['artifact_hash'])
        raw.update(native_input=original['native_input'],screen='none',client_frame_start=frame,client_frame_end=frame+1,
                   client_tick_start=frame//5,client_tick_end=frame//5)
        state=raw['entities'][0]['staff_state'];tick=frame//5
        state['glowing']={'amplifier':0,'duration_ticks':max(0,81-tick)}
        state['staff_cooldown'].update(active=True,fraction=(121-tick)/100)
        receipt[key]['artifact_hash']=store.put_json(raw)
    return store.put_json(receipt)


@pytest.fixture
def records(paired):
    store,paths,sc,cc,*_=paired
    sc['connection_policy']['player_uuids'].append(CONTROL)
    for contract in (sc,cc):contract['connection_policy_hash']=key_for(sc['connection_policy'])
    for path in paths.values():
        data=json.loads(Path(path).read_text());data['connection_policy']=sc['connection_policy'];Path(path).write_bytes(canonical(data))
    store,refs=first_use_fixture.__wrapped__(paired)
    refs['after_pair']=clone_pair(store,refs['after_pair'],20,130)
    receipt=store.json(refs['input_receipt']);raw=store.json(receipt['after']['artifact_hash'])
    raw.update(client_tick_start=22,client_tick_end=22)
    raw['entities'][0]['staff_state']['glowing']['duration_ticks']=59
    raw['entities'][0]['staff_state']['staff_cooldown']['fraction']=.99
    receipt['after']['artifact_hash']=store.put_json(raw);refs['input_receipt']=store.put_json(receipt)
    refs['control_before_pair']=clone_pair(store,refs['before_pair'],2,50,'neutral',True)
    refs['control_after_pair']=clone_pair(store,refs['before_pair'],26,200,'neutral',True)
    refs['repeat_before_pair']=clone_pair(store,refs['after_pair'],30,150)
    refs['repeat_after_pair']=clone_pair(store,refs['after_pair'],40,180)
    refs['repeat_input_receipt']=repeat_receipt(store,refs['input_receipt'],refs['repeat_before_pair'],refs['repeat_after_pair'])
    refs['effect_expiry_pair']=clone_pair(store,refs['after_pair'],85,500)
    refs['cooldown_expiry_pair']=clone_pair(store,refs['after_pair'],125,700)
    def end_packet(raw):
        trace=raw['staff_packet_trace'];trace.update(sequence=3,cooldown_count=2)
        trace['records'].append(dict(sequence=3,player_uuid=PLAYER,kind='cooldown',item='kneekura:celestial_staff',duration_ticks=0))
    edit_pair(store,refs,'cooldown_expiry_pair',end_packet)
    refs['native_receipts']=[refs['input_receipt']]
    assert checker().evaluate_client_use(store,**{k:refs[k] for k in ('before_pair','after_pair','input_receipt')})['outcome']=='PASS'
    return store,refs


FIELDS={'non_invoking':('control_before_pair','control_after_pair','native_receipts'),
        'cooldown_repeat':('repeat_before_pair','repeat_after_pair','repeat_input_receipt'),
        'expiry':('effect_expiry_pair','cooldown_expiry_pair')}


def evaluate(records,kind):
    store,refs=records
    return getattr(module(),'evaluate_'+kind)(store,**{k:refs[k] for k in ('before_pair','after_pair','input_receipt',*FIELDS[kind])})


@pytest.mark.parametrize('kind',FIELDS)
def test_fixed_controls_can_establish_only_retained_record_consistency(records,kind):
    result=evaluate(records,kind)
    assert result['outcome']=='PASS',result
    assert result['evidence_level']=='RETAINED_RECORD_CONSISTENCY_NOT_LIVE_ATTESTATION'
    assert result['live_attestation']=='NOT_ESTABLISHED'
    assert result['product_acceptance']=='NOT_ESTABLISHED'


@pytest.mark.parametrize('fault',['same_player','glow','cooldown','health','damage','wrong_epoch','early_after','late_before','unbounded_input','missing_input','client_use'])
def test_non_invoking_controls_reject_contamination_or_wrong_window(records,fault):
    store,refs=records
    if fault=='same_player':refs['control_after_pair']=refs['after_pair']
    elif fault=='late_before':refs['control_before_pair']=clone_pair(store,refs['control_before_pair'],15,50,'neutral')
    elif fault=='unbounded_input':refs['native_receipts'].append(refs['repeat_input_receipt'])
    elif fault=='missing_input':refs['native_receipts']=[]
    else:
        def change(raw):
            state=raw['entities'][0]['staff_state']
            if fault=='glow':state['glowing']={'amplifier':0,'duration_ticks':60}
            if fault=='cooldown':state['staff_cooldown'].update(active=True,fraction=1.0)
            if fault=='health':raw['entities'][0]['health']=19
            if fault=='damage':state['main_hand']['damage']=1
            if fault=='wrong_epoch':raw['identity']['session_epoch']='other'
            if fault=='early_after':raw.update(server_tick_start=21,server_tick_end=22)
            if fault=='client_use':raw['staff_client_trace'].update(started=1,completed=1)
        edit_pair(store,refs,'control_after_pair',change,0 if fault=='early_after' else 1)
    assert evaluate(records,'non_invoking')['outcome']!='PASS'


@pytest.mark.parametrize('fault',['replayed_receipt','command_receipt','new_glow','new_cooldown','refresh_glow','refresh_cooldown','expired_before','health','stack','wrong_epoch','backwards_tick','old_prefix','unknown_trace'])
def test_repeat_controls_reject_refresh_or_unbound_native_input(records,fault):
    store,refs=records
    if fault=='replayed_receipt':refs['repeat_input_receipt']=refs['input_receipt']
    elif fault=='command_receipt':
        rec=store.json(refs['repeat_input_receipt']);rec['kind']='registered-command-receipt';refs['repeat_input_receipt']=store.put_json(rec)
    else:
        def change(raw):
            state=raw['entities'][0]['staff_state'];trace=raw.get('staff_packet_trace')
            if fault in ('new_glow','new_cooldown'):
                new=deepcopy(trace['records'][0 if fault=='new_glow' else 1]);new['sequence']=3;trace['records'].append(new);trace['sequence']=3
                trace['glowing_count' if fault=='new_glow' else 'cooldown_count']+=1
            if fault=='refresh_glow':state['glowing']['duration_ticks']=60
            if fault=='refresh_cooldown':state['staff_cooldown']['fraction']=1.0
            if fault=='expired_before':state['staff_cooldown'].update(active=False,fraction=0.0)
            if fault=='health':raw['entities'][0]['health']=19
            if fault=='stack':state['main_hand']['count']=2
            if fault=='wrong_epoch':raw['identity']['session_epoch']='other'
            if fault=='backwards_tick':raw.update(server_tick_start=1,server_tick_end=2)
            if fault=='old_prefix':trace['records'][0]['duration_ticks']=59
            if fault=='unknown_trace':trace['unknown']=1
        server_fault=fault in ('refresh_glow','refresh_cooldown','expired_before','backwards_tick')
        edit_pair(store,refs,'repeat_before_pair' if fault=='expired_before' else 'repeat_after_pair',change,0 if server_fault else 1)
    assert evaluate(records,'cooldown_repeat')['outcome']!='PASS'


@pytest.mark.parametrize('fault',['too_early_effect','too_early_cooldown','remaining_effect','remaining_cooldown','wrong_epoch','health','late_refresh','missing_pair'])
def test_expiry_requires_elapsed_server_ticks_and_same_identity(records,fault):
    store,refs=records
    if fault=='missing_pair':refs['effect_expiry_pair']='0'*64
    else:
        def change(raw):
            state=raw['entities'][0]['staff_state']
            if fault=='too_early_effect':raw.update(server_tick_start=30,server_tick_end=31)
            if fault=='too_early_cooldown':raw.update(server_tick_start=90,server_tick_end=91)
            if fault=='remaining_effect':state['glowing']={'amplifier':0,'duration_ticks':1}
            if fault=='remaining_cooldown':state['staff_cooldown'].update(active=True,fraction=.01)
            if fault=='wrong_epoch':raw['identity']['session_epoch']='other'
            if fault=='health':raw['entities'][0]['health']=19
            if fault=='late_refresh':
                trace=raw['staff_packet_trace'];new=deepcopy(trace['records'][0]);new['sequence']=4
                trace['records'].append(new);trace['sequence']=4;trace['glowing_count']+=1
        key='effect_expiry_pair' if fault in ('too_early_effect','remaining_effect') else 'cooldown_expiry_pair'
        edit_pair(store,refs,key,change,0 if fault.startswith('too_early') else 1)
    assert evaluate(records,'expiry')['outcome']!='PASS'


def test_expiry_cannot_forget_a_previously_retained_packet(records):
    store,refs=records
    def terminal(raw):
        trace=raw['staff_packet_trace'];trace.update(sequence=3,cooldown_count=2)
        trace['records'].append(dict(sequence=3,player_uuid=PLAYER,kind='cooldown',item='kneekura:celestial_staff',duration_ticks=0))
    edit_pair(store,refs,'effect_expiry_pair',terminal)
    def forget(raw):
        trace=raw['staff_packet_trace'];trace.update(sequence=2,cooldown_count=1);trace['records'].pop()
    edit_pair(store,refs,'cooldown_expiry_pair',forget)
    assert evaluate(records,'expiry')['outcome']!='PASS'


@pytest.mark.parametrize('kind',FIELDS)
def test_controls_reject_missing_instrumentation(records,kind):
    store,refs=records;key={'non_invoking':'control_after_pair','cooldown_repeat':'repeat_after_pair','expiry':'cooldown_expiry_pair'}[kind]
    edit_pair(store,refs,key,lambda raw:raw.pop('staff_packet_trace'))
    assert evaluate(records,kind)['outcome']=='BLOCKED'


def test_control_cannot_relabel_the_invoking_game_connection(records):
    store,refs=records
    for key in ('control_before_pair','control_after_pair'):
        for index in (0,1,2):
            def same_socket(raw):
                conn=raw['entities'][0]['connection'];side='client' if index==1 else 'server'
                conn['channel_id']=side+'-channel';conn['local' if index==1 else 'remote']['port']=32123
                if index==1:
                    raw['connection']=deepcopy(conn);raw['staff_packet_trace']['channel_id']=conn['channel_id']
            edit_pair(store,refs,key,same_socket,index)
    assert evaluate(records,'non_invoking')['outcome']!='PASS'


@pytest.mark.parametrize('fault',['client_amplifier','client_glow_refresh','client_cooldown_refresh'])
def test_repeat_rejects_receiver_only_state_faults(records,fault):
    store,refs=records
    def change(raw):
        state=raw['entities'][0]['staff_state']
        if fault=='client_amplifier':state['glowing']['amplifier']=100
        if fault=='client_glow_refresh':state['glowing']['duration_ticks']=60
        if fault=='client_cooldown_refresh':state['staff_cooldown']['fraction']=1.0
    edit_pair(store,refs,'repeat_after_pair',change)
    assert evaluate(records,'cooldown_repeat')['outcome']!='PASS'


@pytest.mark.parametrize('fault',['impossible_packets','known_mutation','rewritten_call','missing_trace'])
def test_intermediate_native_repeat_captures_cannot_contradict_retained_history(records,fault):
    store,refs=records;receipt=store.json(refs['repeat_input_receipt'])
    raw=store.json(receipt['before']['artifact_hash'])
    if fault=='impossible_packets':raw['staff_packet_trace']['sequence']=102
    if fault=='known_mutation':raw['staff_client_trace']['records'][0]['effect_mutation_attempts']=1
    if fault=='rewritten_call':raw['staff_client_trace']['records'][0]['before']['health']=19
    if fault=='missing_trace':raw.pop('staff_client_trace')
    receipt['before']['artifact_hash']=store.put_json(raw);refs['repeat_input_receipt']=store.put_json(receipt)
    assert evaluate(records,'cooldown_repeat')['outcome']!='PASS'


@pytest.mark.parametrize('kind',FIELDS)
def test_controls_reject_backwards_server_logs(records,kind):
    store,refs=records;key={'non_invoking':'control_after_pair','cooldown_repeat':'repeat_after_pair','expiry':'cooldown_expiry_pair'}[kind]
    edit_pair(store,refs,key,lambda raw:raw.update(log_sequence_start=0,log_sequence_end=0),0)
    assert evaluate(records,kind)['outcome']!='PASS'


@pytest.mark.parametrize('fault',['health','amplifier','glow_refresh','cooldown_refresh','missing_state'])
def test_repeat_native_snapshots_are_part_of_observed_state_bounds(records,fault):
    store,refs=records;receipt=store.json(refs['repeat_input_receipt']);raw=store.json(receipt['before']['artifact_hash'])
    state=raw['entities'][0]['staff_state']
    if fault=='health':raw['entities'][0]['health']=1
    if fault=='amplifier':state['glowing']['amplifier']=100
    if fault=='glow_refresh':state['glowing']['duration_ticks']=60
    if fault=='cooldown_refresh':state['staff_cooldown']['fraction']=1.0
    if fault=='missing_state':raw['entities'][0].pop('staff_state')
    receipt['before']['artifact_hash']=store.put_json(raw);refs['repeat_input_receipt']=store.put_json(receipt)
    assert evaluate(records,'cooldown_repeat')['outcome']!='PASS'
