"""Check the fixed staff use evidence; never launch, connect, or mutate a game.

This is retained-record consistency, not live attestation of an arbitrary
importer. A scoped PASS does not establish visuals or general network correctness.
"""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

from kneekura_tech_hub.minecraft import input_contract, native_input, runtime_pair, verification
from kneekura_tech_hub.minecraft.storage import ContractError, Store, canonical, digest, key_for, valid_hash

FIXED = Path(__file__).with_name('assertions.json')


def require(condition, message):
    if not condition: raise ContractError(message)


def count(value, minimum=0):
    require(type(value) is int and value >= minimum, 'Invalid integer counter')
    return value


def finite(value, minimum=0, maximum=1e9):
    require(type(value) in (int,float) and math.isfinite(value) and minimum <= value <= maximum,
            'Finite bounded number required')
    return value


def read_pair(store, ref):
    pair = store.json(valid_hash(ref))
    require(isinstance(pair,dict) and type(pair.get('schema_version')) is int
            and pair['schema_version'] == 1 and pair.get('kind') == 'dedicated-observer-pair'
            and pair.get('atomic') is False, 'Dedicated non-atomic pair required')
    server, client = (store.json(pair[k+'_contract_hash']) for k in ('server','client'))
    require(server.get('session_role') == 'dedicated_server' and client.get('session_role') == 'dedicated_client'
            and client.get('server_contract_hash') == key_for(server), 'Dedicated role/reference mismatch')
    require(server['build_artifact_hash'] == client['build_artifact_hash']
            and server['source_revision'] == client['source_revision']
            and server['connection_policy_hash'] == client['connection_policy_hash']
            and pair['player_uuid'] == client['player_uuid'], 'Pair target mismatch')
    require(pair.get('connection_policy_hash') == server['connection_policy_hash']
            and pair.get('client_directory_id') == client['run_directory_id']
            and pair.get('target_build_binding') == 'MATCHING_RUNTIME_ARTIFACT_AND_REVISION'
            and pair.get('evidence_level') == 'AUTHENTICATED_PAIRED_OBSERVATIONS'
            and pair.get('world_binding') == {'source':'authenticated_server_contract','world_id':server['world_id'],
                'world_seed':server['world_seed'],'world_template_hash':server['world_template_hash']}, 'Pair metadata differs')
    samples = pair['samples']
    require(isinstance(samples,list) and len(samples) == 3 and all(isinstance(s,dict) for s in samples), 'Malformed pair samples')
    require([s.get('role') for s in samples] == ['server_before','client','server_after'], 'Bracketing set is incomplete')
    frames=[];previous_end=0;fixed=json.loads(FIXED.read_bytes())
    for sample, contract in zip(samples,(server,client,server)):
        raw=store.json(sample['artifact_hash']); hello=store.json(sample['handshake_hash'])
        begin=finite(sample.get('controller_elapsed_start'),maximum=30)
        end=finite(sample.get('controller_elapsed_end'),maximum=30)
        require(previous_end <= begin <= end, 'Controller bracketing moved backwards');previous_end=end
        require(isinstance(raw,dict) and isinstance(hello,dict), 'Malformed captured object')
        require(hello.get('ready') is True and not verification._identity_errors(contract,hello), 'Stale pair handshake')
        require(hello.get('minecraft') == fixed['minecraft'] and hello.get('forge') == fixed['forge']
                and type(hello.get('java_major')) is int and hello['java_major'] == fixed['java_major'], 'Wrong fixed target version')
        row=runtime_pair._row(contract,raw,pair['player_uuid'],pair['dimension'])
        frames.append((raw,row))
    left=frames[0][1]['connection'];right=frames[1][1]['connection']
    require(left == frames[2][1]['connection'] and right == frames[1][0]['connection']
            and left['local'] == right['remote'] and left['remote'] == right['local'], 'Unpaired game sockets')
    require(frames[0][0]['server_tick_end'] <= frames[2][0]['server_tick_start'], 'Reversed server interval')
    require(frames[0][0]['log_sequence_end'] <= frames[2][0]['log_sequence_start'], 'Reversed server log history')
    for contract in (server,client):
        scenario=store.json(contract['scenario_hash'])
        domain='server_observation' if contract['session_role'] == 'dedicated_server' else 'client_observation'
        assertions={'assertion_domain':contract.get('assertion_domain'), 'expected_tests':contract.get('expected_tests'),
                    'expected_required':contract.get('expected_required',{})}
        if 'negative_controls' in contract:assertions['negative_controls']=contract['negative_controls']
        require(isinstance(scenario,dict) and scenario.get('fixed_assertions_sha256') == digest(FIXED.read_bytes())
                and scenario.get('assertion_domain') == domain == contract.get('assertion_domain')
                and key_for(assertions) == contract.get('assertion_hash'), 'Fixed scenario/assertion binding differs')
    return pair,server,client,frames


def staff_state(row):
    state=row['staff_state'];hand=state.get('main_hand');cooldown=state.get('staff_cooldown')
    require(isinstance(hand,dict) and hand.get('item') == 'kneekura:celestial_staff', 'Expected main-hand staff missing')
    count(hand.get('count'));count(hand.get('damage'))
    health=row.get('health')
    require(type(health) in (int,float) and math.isfinite(health), 'Invalid player health')
    require(isinstance(cooldown,dict) and cooldown.get('registered') is True
            and cooldown.get('item') == 'kneekura:celestial_staff' and type(cooldown.get('active')) is bool,
            'Staff cooldown is not independently observed')
    fraction=cooldown.get('fraction')
    require(type(fraction) in (int,float) and math.isfinite(fraction) and 0 <= fraction <= 1, 'Invalid cooldown fraction')
    effect=state.get('glowing')
    if effect is not None:
        require(isinstance(effect,dict), 'Malformed Glowing effect')
        count(effect.get('amplifier'));count(effect.get('duration_ticks'),1)
    return dict(health=health,main_hand=hand,glowing=effect,staff_cooldown=cooldown)


def client_state_bounds(raws, fixed, *, require_active=False):
    """Consistency of the selected client's independently sampled remaining ticks."""
    states=[staff_state(raw['entities'][0]) for raw in raws]
    require(all(s['health']==states[0]['health'] and s['main_hand']==states[0]['main_hand'] for s in states),
            'Native/client health, stack or damage changed')
    result={}
    for name,duration in (('glowing',fixed['effect_ticks']),('staff_cooldown',fixed['cooldown_ticks'])):
        lower=None;upper=None
        for raw,state in zip(raws,states):
            value=state[name];start=raw['client_tick_start'];end=raw['client_tick_end']
            if name=='glowing':
                active=value is not None
                if active:
                    require(value['amplifier']==fixed['effect_amplifier'] and value['duration_ticks']<=duration, 'Wrong native/client Glowing value')
                    remaining=value['duration_ticks'];epsilon=0
            else:
                active=value['active']
                require(active==(value['fraction']>0), 'Contradictory native/client cooldown')
                if require_active:require(active,'Repeat native capture lies outside prior cooldown')
                if active:remaining=value['fraction']*duration;epsilon=.0001
            if not active:
                if upper is not None:upper=min(upper,end+1)
                continue
            low=start+remaining-epsilon;high=end+remaining+1+epsilon
            lower=low if lower is None else max(lower,low);upper=high if upper is None else min(upper,high)
        result[name]={'lower':lower,'upper':upper,'consistent':lower is None or lower<=upper}
    require(all(v['consistent'] for v in result.values()), 'Native/client remaining-tick history is inconsistent')
    return result


def trace_shape(trace, fields):
    require(isinstance(trace,dict) and type(trace.get('schema_version')) is int
            and trace['schema_version'] == 1 and trace.get('supported') is True,
            'Opt-in instrumentation unavailable')
    require(type(trace.get('limit')) is int and trace['limit'] == 16
            and isinstance(trace.get('records'),list) and len(trace['records']) <= 16
            and all(isinstance(r,dict) for r in trace['records']), 'Malformed or unbounded trace')
    for field in (*fields,'unknown','dropped'): count(trace.get(field))
    require(trace['unknown'] == 0 and trace['dropped'] == 0, 'Incomplete trace')


def sequences(trace, total):
    require(0 <= total <= 16 and total == len(trace['records']), 'Counter exceeds retained complete trace')
    require([count(r.get('sequence'),1) for r in trace['records']] == list(range(1,total+1)),
            'Trace records do not exactly match cumulative counters')


def call_state(value):
    require(isinstance(value,dict) and set(value) == {'health','main_hand','glowing','staff_cooldown'}, 'Malformed call state')
    finite(value['health'])
    hand=value['main_hand'];cool=value['staff_cooldown'];effect=value['glowing']
    require(isinstance(hand,dict) and set(hand) == {'item','count','damage'}
            and hand['item'] == 'kneekura:celestial_staff', 'Wrong call item')
    count(hand['count']);count(hand['damage'])
    require(isinstance(cool,dict) and set(cool) == {'active','fraction'} and type(cool['active']) is bool, 'Malformed call cooldown')
    finite(cool['fraction'],maximum=1)
    if effect is not None:
        require(isinstance(effect,dict) and set(effect) == {'amplifier','duration_ticks'}, 'Malformed call effect')
        count(effect['amplifier']);count(effect['duration_ticks'],1)


def packets(before, after, player, channel, fixed):
    for trace in (before,after):
        trace_shape(trace,('sequence','glowing_count','cooldown_count'))
        require(trace.get('scope') == 'SELECTED_VANILLA_RECEIPT_NOT_PROCESSING_ATTESTATION'
                and trace.get('active') is True and trace.get('player_uuid') == player
                and trace.get('channel_id') == channel, 'Packet trace scope differs')
        count(trace.get('entity_id'))
        sequences(trace,trace['sequence'])
        require(trace['glowing_count'] == sum(r.get('kind') == 'glowing' for r in trace['records'])
                and trace['cooldown_count'] == sum(r.get('kind') == 'cooldown' for r in trace['records'])
                and trace['glowing_count'] + trace['cooldown_count'] == trace['sequence'], 'Packet history counts disagree')
    require(before['entity_id'] == after['entity_id'] and all(after[k] >= before[k]
            for k in ('sequence','glowing_count','cooldown_count')), 'Packet scope/counters changed')
    require(canonical(after['records'][:len(before['records'])]) == canonical(before['records']), 'Packet history was rewritten')
    new=[r for r in after['records'] if count(r.get('sequence'),1) > before['sequence']]
    require(len(new) == after['sequence']-before['sequence'] and len({r['sequence'] for r in new}) == len(new),
            'Packet receipt sequence is incomplete')
    require(all(r.get('player_uuid') == player for r in new), 'Wrong packet player')
    glow=[r for r in new if r.get('kind') == 'glowing'];cool=[r for r in new if r.get('kind') == 'cooldown']
    require(len(glow)+len(cool) == len(new) and len(glow) == after['glowing_count']-before['glowing_count']
            and len(cool) == after['cooldown_count']-before['cooldown_count'], 'Packet counts disagree')
    if not glow or not cool: return 'NOT_RUN'
    if any(type(r.get('entity_id')) is not int or r['entity_id'] != after['entity_id'] or r.get('effect') != fixed['effect']
           or type(r.get('amplifier')) is not int or r['amplifier'] != fixed['effect_amplifier']
           or type(r.get('duration_ticks')) is not int or r['duration_ticks'] != fixed['effect_ticks'] for r in glow): return 'FAIL'
    if any(r.get('item') != fixed['asset_id'] or type(r.get('duration_ticks')) is not int
           or r['duration_ticks'] not in (0,fixed['cooldown_ticks']) for r in cool): return 'FAIL'
    return 'PASS' if any(r['duration_ticks'] == fixed['cooldown_ticks'] for r in cool) else 'NOT_RUN'


def client_calls(before, after, player):
    for trace in (before,after):
        trace_shape(trace,('started','completed'))
        require(trace.get('status') == 'CAPTURED' and trace['started'] == trace['completed'], 'Incomplete client call')
        sequences(trace,trace['started'])
    require(canonical(after['records'][:len(before['records'])]) == canonical(before['records']), 'Client call history was rewritten')
    delta=after['started']-before['started']
    require(0 <= delta <= 4, 'Unexpected number of client calls in one bounded gesture window')
    rows=[r for r in after['records'] if count(r.get('sequence'),1) > before['started']]
    require(len(rows) == delta and len({r['sequence'] for r in rows}) == delta, 'Missing client call sequence')
    if not rows: return 'NOT_RUN'
    for row in rows:
        require(row.get('player_uuid') == player and row.get('completed') is True and type(row.get('unchanged')) is bool
                and isinstance(row.get('before'),dict) and isinstance(row.get('after'),dict), 'Invalid client call scope')
        effect=count(row.get('effect_mutation_attempts'));cooldown=count(row.get('cooldown_mutation_attempts'))
        call_state(row['before']);call_state(row['after'])
        if effect or cooldown or not row['unchanged'] or canonical(row['before']) != canonical(row['after']): return 'FAIL'
    return 'PASS'


def native_use(store, ref, contract, before, after):
    receipt=store.json(valid_hash(ref));result=receipt.get('result',{})
    require(receipt.get('kind') == 'native-input-receipt' and result.get('input_status') == 'COMPLETED'
            and result.get('release_completed') is True and result.get('release_attempted') is True
            and result.get('retry_allowed') is False and result.get('outcome') == 'NOT_RUN'
            and result.get('control') == 'mouse:right'
            and result.get('evidence_level') == 'NATIVE_INPUT_ATTEMPT_NOT_GAMEPLAY_ATTESTATION'
            and isinstance(receipt.get('native_completion'),dict) and set(receipt['native_completion']) == {'pressed','released'}
            and all(receipt['native_completion'][key] is True for key in ('pressed','released'))
            and not verification._identity_errors(contract,{'identity':result.get('identity')}), 'Missing completed same-client native gesture')
    request=store.json(receipt['request_hash']);binding=store.json(receipt['binding_hash'])
    target=native_input.validate_target_shape(binding['target'])
    identity={key:contract[key] for key in verification.identity_fields(contract)}
    expected_target='x11:'+key_for({'identity':identity,'native':target,'connection':before['connection']})
    request=input_contract._validate(contract,request,expected_target,('mouse:right',),5)
    input_contract._identity(contract,binding.get('identity'))
    require(binding.get('kind') == 'native-input-binding' and binding.get('backend') == 'linux-x11-send-event-v1'
            and binding.get('connection') == before['connection'] == after['connection']
            and request.get('operation_id') == result.get('operation_id')
            and binding.get('target_id') == request.get('target_id') == result.get('target_id') == expected_target
            and request.get('control') == 'mouse:right' and type(request.get('hold_ms')) is int and request['hold_ms'] == 50
            and not verification._identity_errors(contract,{'identity':request.get('identity')})
            and not verification._identity_errors(contract,{'identity':binding.get('identity')}), 'Native request/binding differs')
    size=binding['target']['client_size']
    require(isinstance(size,list) and len(size) == 2 and all(type(x) is int and 0 < x <= 32768 for x in size)
            and isinstance(request.get('position'),list) and all(type(x) is int for x in request['position'])
            and request['position'] == [x//2 for x in size], 'Gesture is not the fixed gameplay crosshair')
    frames=[]
    for point in ('before','after'):
        raw=store.json(receipt[point]['artifact_hash'])
        require(verification.evaluate_observation(contract,raw)['status'] == 'OK', 'Invalid native capture')
        require(raw.get('connection') == before['connection'] and len(raw['entities']) == 1
                and raw['entities'][0]['uuid'] == contract['player_uuid']
                and raw['entities'][0]['dimension'] == before['entities'][0]['dimension'], 'Native connection/player differs')
        scope=raw.get('native_input')
        require(isinstance(scope,dict) and set(scope) == {*target,'platform','foreground','cursor_mode'}
                and scope['platform'] == 'linux-x11' and scope['foreground'] is True
                and scope['cursor_mode'] == 'disabled' and raw.get('screen') == 'none'
                and {k:scope[k] for k in target} == target, 'Native capture target differs')
        native_input.validate_target_shape({k:scope[k] for k in target})
        frames.append(raw)
    require(before['client_frame_end'] <= frames[0]['client_frame_start'] <= frames[0]['client_frame_end']
            <= frames[1]['client_frame_start'] <= frames[1]['client_frame_end'] <= after['client_frame_start'],
            'Native input is outside the paired observation window')
    fixed=json.loads(FIXED.read_bytes())
    ordered=[before,*frames,after]
    for left,right in zip(ordered,ordered[1:]):
        require(packets(left.get('staff_packet_trace'),right.get('staff_packet_trace'),contract['player_uuid'],
                        before['connection']['channel_id'],fixed) != 'FAIL', 'Native capture packet history contradicts fixed values')
        require(client_calls(left.get('staff_client_trace'),right.get('staff_client_trace'),contract['player_uuid']) != 'FAIL',
                'Native capture client-call history records mutation')
    for interval in ('client_tick','log_sequence'):
        ordered=[before,*frames,after]
        require(all(a[interval+'_end'] <= b[interval+'_start'] for a,b in zip(ordered,ordered[1:])),
                'Receiving-client tick/log chronology moved backwards')
    client_state_bounds(ordered,fixed)
    return frames


def evaluate_client_use(store: Store, *, before_pair: str, after_pair: str, input_receipt: str) -> dict:
    verdicts={k:'NOT_RUN' for k in ('native_input','server_state','client_state','packet_receipts',
        'client_handler_known_mutator_sites','health_stack_damage','scoped_synchronization','visual','non_invoking_player','performance')}
    out={'schema_version':1,'kind':'fixed-staff-client-evidence-check',
         'evidence_level':'RETAINED_RECORD_CONSISTENCY_NOT_LIVE_ATTESTATION','verdicts':verdicts,
         'references':{'before_pair':before_pair,'after_pair':after_pair,'input_receipt':input_receipt},
         'reasons':[],'product_acceptance':'NOT_ESTABLISHED',
         'scope':'Selected vanilla packet/state correlation and verified fixture mutator-site execution only'}
    try:
        fixed=json.loads(FIXED.read_bytes())
        bp,sc,cc,before=read_pair(store,before_pair);ap,asc,acc,after=read_pair(store,after_pair)
        require(sc == asc and cc == acc and bp['player_uuid'] == ap['player_uuid'] and bp['dimension'] == ap['dimension'],
                'Before/after run identity differs')
        require(before[2][0]['server_tick_end'] <= after[0][0]['server_tick_start'], 'Reversed use window')
        require(before[2][0]['log_sequence_end'] <= after[0][0]['log_sequence_start'], 'Reversed use server log history')
        native_use(store,input_receipt,cc,before[1][0],after[1][0]);verdicts['native_input']='PASS'
        states=[staff_state(row) for _,row in (*before,*after)]
        require(all(s['glowing'] is None and not s['staff_cooldown']['active'] and s['staff_cooldown']['fraction'] == 0
                    for s in states[:3]), 'Fresh baseline is missing')
        for key,selected in [('server_state',(states[3],states[5])),('client_state',(states[4],))]:
            if any(s['glowing'] is None or not s['staff_cooldown']['active'] for s in selected): continue
            verdicts[key]='FAIL' if any(s['glowing']['amplifier'] != fixed['effect_amplifier']
                or s['glowing']['duration_ticks'] > fixed['effect_ticks'] or not 0 < s['staff_cooldown']['fraction'] <= 1
                for s in selected) else 'PASS'
        verdicts['health_stack_damage']='PASS' if all(s['health'] == states[0]['health']
            and s['main_hand'] == states[0]['main_hand'] for s in states) else 'FAIL'
        verdicts['packet_receipts']=packets(before[1][0].get('staff_packet_trace'),after[1][0].get('staff_packet_trace'),
            cc['player_uuid'],before[1][0]['connection']['channel_id'],fixed)
        verdicts['client_handler_known_mutator_sites']=client_calls(before[1][0].get('staff_client_trace'),
            after[1][0].get('staff_client_trace'),cc['player_uuid'])
        required=[verdicts[k] for k in ('native_input','server_state','client_state','packet_receipts',
                                       'client_handler_known_mutator_sites','health_stack_damage')]
        verdicts['scoped_synchronization']='FAIL' if 'FAIL' in required else 'PASS' if set(required) == {'PASS'} else 'NOT_RUN'
        out['outcome']=verdicts['scoped_synchronization']
    except (ContractError,KeyError,ValueError,TypeError,OSError,AttributeError,OverflowError,RecursionError) as exc:
        out['outcome']='BLOCKED';out['reasons'].append(str(exc))
    return out


if __name__ == '__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    for arg in ('store','before-pair','after-pair','input-receipt'):parser.add_argument('--'+arg,required=True)
    args=parser.parse_args();result=evaluate_client_use(Store(Path(args.store)),before_pair=args.before_pair,
        after_pair=args.after_pair,input_receipt=args.input_receipt)
    print(json.dumps(result,sort_keys=True));raise SystemExit(0 if result['outcome']=='PASS' else 2)
