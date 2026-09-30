"""Fixed staff control/repeat/expiry checks over retained paired observations.

No game process, input device, or network is accessed. PASS means consistency of
these supplied records; it does not attest a live run or completeness of an input
history. Invoke with ``python -m tools.ci.mod_ai_staff.verify_controls``.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from tools.ci.mod_ai_staff import verify_client as base
from kneekura_tech_hub.minecraft.storage import ContractError, Store, canonical, valid_hash

ERRORS=(ContractError,KeyError,ValueError,TypeError,OSError,AttributeError,OverflowError,RecursionError)
require=base.require


def _result(kind, refs):
    return dict(schema_version=1,kind='fixed-staff-'+kind+'-evidence-check',references=refs,
        evidence_level='RETAINED_RECORD_CONSISTENCY_NOT_LIVE_ATTESTATION',
        live_attestation='NOT_ESTABLISHED',product_acceptance='NOT_ESTABLISHED',
        verdicts={},reasons=[])


def _finish(out):
    out['outcome']='PASS' if out['verdicts'] and set(out['verdicts'].values())=={'PASS'} else 'FAIL'
    return out


def _blocked(out, exc):
    out['outcome']='BLOCKED';out['reasons'].append(str(exc));return out


def _first(store, refs):
    first={key:refs[key] for key in ('before_pair','after_pair','input_receipt')}
    checked=base.evaluate_client_use(store,**first)
    require(checked['outcome']=='PASS','Validated fixed first-use evidence is required')
    return base.read_pair(store,refs['before_pair']),base.read_pair(store,refs['after_pair'])


def _same(left, right):
    require(left[1]==right[1] and left[2]==right[2]
        and left[0]['player_uuid']==right[0]['player_uuid'] and left[0]['dimension']==right[0]['dimension'],
        'Paired run/player/dimension identity changed')
    require(left[3][0][1]['connection']==right[3][0][1]['connection']
        and left[3][1][0]['connection']==right[3][1][0]['connection'],'Paired game connection changed')


def _later(left, right):
    _same(left,right)
    require(left[3][2][0]['server_tick_end'] <= right[3][0][0]['server_tick_start'],'Server windows overlap or reverse')
    require(left[3][2][0]['log_sequence_end'] <= right[3][0][0]['log_sequence_start'],'Server log history moved backwards')
    for interval in ('client_frame','client_tick','log_sequence'):
        require(left[3][1][0][interval+'_end'] <= right[3][1][0][interval+'_start'],'Client chronology moved backwards')


def _states(pair):
    states=[base.staff_state(row) for _,row in pair[3]]
    for state in states:
        base.finite(state['health']);base.count(state['main_hand']['count'],1)
        cool=state['staff_cooldown'];require(cool['active']==(cool['fraction']>0),'Inconsistent cooldown active/fraction')
    return states


def _unchanged(pairs):
    states=[state for pair in pairs for state in _states(pair)];first=states[0]
    return all(state['health']==first['health'] and state['main_hand']==first['main_hand'] for state in states)


def _packet(pair, fixed):
    raw=pair[3][1][0];trace=raw.get('staff_packet_trace');player=pair[2]['player_uuid']
    base.trace_shape(trace,('sequence','glowing_count','cooldown_count'));base.sequences(trace,trace['sequence'])
    require(trace.get('scope')=='SELECTED_VANILLA_RECEIPT_NOT_PROCESSING_ATTESTATION'
        and trace.get('active') is True and trace.get('player_uuid')==player
        and trace.get('channel_id')==raw['connection']['channel_id'],'Packet scope changed')
    entity=base.count(trace.get('entity_id'));glow=cool=0
    for row in trace['records']:
        require(row.get('player_uuid')==player,'Wrong packet player')
        duration=base.count(row.get('duration_ticks'))
        if row.get('kind')=='glowing':
            require(type(row.get('entity_id')) is int and row['entity_id']==entity
                and row.get('effect')==fixed['effect'] and type(row.get('amplifier')) is int
                and row['amplifier']==fixed['effect_amplifier'] and duration==fixed['effect_ticks'],'Malformed fixed Glowing receipt')
            glow+=1
        else:
            require(row.get('kind')=='cooldown' and row.get('item')==fixed['asset_id']
                and duration in (0,fixed['cooldown_ticks']),'Malformed fixed cooldown receipt');cool+=1
    require((glow,cool)==(trace['glowing_count'],trace['cooldown_count']),'Packet counters disagree with retained records')
    return trace


def _packet_delta(before,after,fixed,allow_end=False):
    first,last=_packet(before,fixed),_packet(after,fixed)
    require(first['entity_id']==last['entity_id'] and last['sequence']>=first['sequence']
        and canonical(last['records'][:first['sequence']])==canonical(first['records']),'Packet history changed or was truncated')
    new=last['records'][first['sequence']:]
    if not allow_end:return not new
    return len(new)<=1 and all(row['kind']=='cooldown' and row['duration_ticks']==0 for row in new)


def _calls(before,after):
    first=before[3][1][0].get('staff_client_trace');last=after[3][1][0].get('staff_client_trace')
    result=base.client_calls(first,last,before[2]['player_uuid'])
    require(canonical(last['records'][:first['started']])==canonical(first['records']),'Client-call history changed')
    return result


def evaluate_non_invoking(store: Store, *, before_pair, after_pair, input_receipt,
                          control_before_pair, control_after_pair, native_receipts):
    refs=dict(before_pair=before_pair,after_pair=after_pair,input_receipt=input_receipt,
              control_before_pair=control_before_pair,control_after_pair=control_after_pair,native_receipts=native_receipts)
    out=_result('non-invoking-control',refs)
    out['input_absence_scope']='Supplied native receipts and retained fixture calls only; unrecorded OS input is not excluded'
    try:
        before,after=_first(store,refs);cb=base.read_pair(store,control_before_pair);ca=base.read_pair(store,control_after_pair)
        _later(cb,ca)
        require(cb[1]==before[1] and cb[0]['dimension']==before[0]['dimension']
            and cb[2]['player_uuid']!=before[2]['player_uuid']
            and cb[2]['run_id']!=before[2]['run_id'] and cb[2]['session_epoch']!=before[2]['session_epoch']
            and cb[2]['run_directory_id']!=before[2]['run_directory_id'],'Control must be a distinct receiving player/run on the same server')
        control_socket=cb[3][0][1]['connection'];invoking_socket=before[3][0][1]['connection']
        require(control_socket['remote']!=invoking_socket['remote']
            and control_socket['channel_id']!=invoking_socket['channel_id'],
            'Control cannot relabel the invoking server connection')
        require(cb[3][2][0]['server_tick_end']<=before[3][0][0]['server_tick_start']
            and after[3][2][0]['server_tick_end']<=ca[3][0][0]['server_tick_start'],'Control observations do not bracket the complete first-use window')
        require(cb[3][2][0]['log_sequence_end'] <= before[3][0][0]['log_sequence_start']
            and after[3][2][0]['log_sequence_end'] <= ca[3][0][0]['log_sequence_start'], 'Control bracket server log history moved backwards')
        require(isinstance(native_receipts,list) and native_receipts==[input_receipt],
            'Fixed control window requires exactly its invoking-player native receipt')
        out['verdicts']['declared_native_input_targets_invoker']='PASS'
        calls=_calls(cb,ca);require(calls=='NOT_RUN' and cb[3][1][0]['staff_client_trace']['started']==0,
            'Control client has recorded staff-use calls')
        fixed=json.loads(base.FIXED.read_bytes())
        out['verdicts']['no_control_receipt_delta']='PASS' if _packet_delta(cb,ca,fixed) else 'FAIL'
        out['verdicts']['control_neutral']='PASS' if all(state['glowing'] is None
            and not state['staff_cooldown']['active'] and state['staff_cooldown']['fraction']==0
            for pair in (cb,ca) for state in _states(pair)) else 'FAIL'
        out['verdicts']['health_stack_damage']='PASS' if _unchanged((cb,ca)) else 'FAIL'
        return _finish(out)
    except ERRORS as exc:return _blocked(out,exc)


def _expiry_bounds(first,repeat,fixed,*,client=False):
    """Intersect server sample/tick bounds, allowing one tick of update-phase ambiguity.

    Cooldown float conversion additionally has 1e-4 tick rounding tolerance.
    This cannot rule out sub-boundary changes hidden by the retained sampling.
    """
    result={}
    for name,duration in (('glowing',fixed['effect_ticks']),('staff_cooldown',fixed['cooldown_ticks'])):
        lower=float('-inf');upper=float('inf')
        for pair in (first,*repeat):
            for index in ((1,) if client else (0,2)):
                raw,row=pair[3][index];state=base.staff_state(row);value=state[name]
                interval='client_tick' if client else 'server_tick'
                start,end=raw[interval+'_start'],raw[interval+'_end']
                if name=='glowing':
                    if value is None:upper=min(upper,end+1);continue
                    require(value['amplifier']==fixed['effect_amplifier'],'Wrong Glowing amplifier')
                    remaining=base.count(value['duration_ticks'],1);epsilon=0
                else:
                    require(value['active'] and value['fraction']>0,'Repeat window is not inside the existing cooldown')
                    remaining=value['fraction']*duration;epsilon=0.0001
                lower=max(lower,start+remaining-epsilon);upper=min(upper,end+remaining+1+epsilon)
        result[name]=dict(lower=lower,upper=upper,consistent=lower<=upper)
    return result


def evaluate_cooldown_repeat(store: Store, *, before_pair, after_pair, input_receipt,
                             repeat_before_pair, repeat_after_pair, repeat_input_receipt):
    refs=dict(before_pair=before_pair,after_pair=after_pair,input_receipt=input_receipt,
        repeat_before_pair=repeat_before_pair,repeat_after_pair=repeat_after_pair,repeat_input_receipt=repeat_input_receipt)
    out=_result('cooldown-repeat',refs)
    out['timing_scope']='Independent server/client sample expiry-bound consistency with one update-phase tick and 1e-4 cooldown-tick rounding allowance'
    try:
        before,after=_first(store,refs);rb=base.read_pair(store,repeat_before_pair);ra=base.read_pair(store,repeat_after_pair)
        _later(after,rb);_later(rb,ra)
        require(valid_hash(repeat_input_receipt)!=valid_hash(input_receipt),'First native receipt cannot stand in for repeat')
        first_receipt=store.json(input_receipt);receipt=store.json(repeat_input_receipt)
        require(first_receipt['result']['operation_id']!=receipt['result']['operation_id'],'Repeated native operation identity')
        native_frames=base.native_use(store,repeat_input_receipt,rb[2],rb[3][1][0],ra[3][1][0])
        out['verdicts']['native_repeat']='PASS'
        fixed=json.loads(base.FIXED.read_bytes())
        out['verdicts']['no_new_application_receipts']='PASS' if _packet_delta(after,rb,fixed) and _packet_delta(rb,ra,fixed) else 'FAIL'
        out['verdicts']['client_handler_known_mutator_sites']='FAIL' if 'FAIL' in (_calls(after,rb),_calls(rb,ra)) else 'PASS'
        require(all(state['staff_cooldown']['active'] for pair in (rb,ra) for state in _states(pair)),
            'Repeat must be captured while the prior cooldown remains active on both sides')
        bounds=_expiry_bounds(after,(rb,ra),fixed);out['server_expiry_bounds']=bounds
        client_bounds=base.client_state_bounds([after[3][1][0],rb[3][1][0],*native_frames,ra[3][1][0]],fixed,require_active=True)
        out['client_expiry_bounds']=client_bounds
        out['verdicts']['no_refresh_client_bounds']='PASS' if all(bound['consistent'] for bound in client_bounds.values()) else 'FAIL'
        out['verdicts']['no_refresh_server_bounds']='PASS' if all(bound['consistent'] for bound in bounds.values()) else 'FAIL'
        out['verdicts']['health_stack_damage']='PASS' if _unchanged((before,after,rb,ra)) else 'FAIL'
        return _finish(out)
    except ERRORS as exc:return _blocked(out,exc)


def evaluate_expiry(store: Store, *, before_pair, after_pair, input_receipt, effect_expiry_pair, cooldown_expiry_pair):
    refs=dict(before_pair=before_pair,after_pair=after_pair,input_receipt=input_receipt,
        effect_expiry_pair=effect_expiry_pair,cooldown_expiry_pair=cooldown_expiry_pair)
    out=_result('expiry',refs)
    try:
        before,after=_first(store,refs);effect=base.read_pair(store,effect_expiry_pair);cooldown=base.read_pair(store,cooldown_expiry_pair)
        _later(after,effect)
        if effect_expiry_pair!=cooldown_expiry_pair:_later(effect,cooldown)
        fixed=json.loads(base.FIXED.read_bytes());origin_upper=after[3][0][0]['server_tick_end']
        require(effect[3][0][0]['server_tick_start']>=origin_upper+fixed['effect_ticks']
            and cooldown[3][0][0]['server_tick_start']>=origin_upper+fixed['cooldown_ticks'],
            'Expiry captures precede the conservative first-use server-tick deadline')
        out['deadline_server_ticks']=dict(effect=origin_upper+fixed['effect_ticks'],cooldown=origin_upper+fixed['cooldown_ticks'])
        out['verdicts']['effect_expired']='PASS' if all(s['glowing'] is None for pair in (effect,cooldown) for s in _states(pair)) else 'FAIL'
        out['verdicts']['cooldown_expired']='PASS' if all(not s['staff_cooldown']['active']
            and s['staff_cooldown']['fraction']==0 for s in _states(cooldown)) else 'FAIL'
        out['verdicts']['no_reapplication_receipts']='PASS' if _packet_delta(after,effect,fixed,True) and _packet_delta(after,cooldown,fixed,True) and _packet_delta(effect,cooldown,fixed,True) else 'FAIL'
        out['verdicts']['no_further_recorded_client_use']='PASS' if _calls(after,effect)=='NOT_RUN' and _calls(after,cooldown)=='NOT_RUN' else 'FAIL'
        out['verdicts']['health_stack_damage']='PASS' if _unchanged((before,after,effect,cooldown)) else 'FAIL'
        return _finish(out)
    except ERRORS as exc:return _blocked(out,exc)


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--store',required=True);parser.add_argument('--kind',required=True,choices=['non_invoking','cooldown_repeat','expiry'])
    parser.add_argument('--references',required=True,help='Local JSON object containing the exact function arguments')
    args=parser.parse_args();refs=json.loads(Path(args.references).read_bytes())
    result=globals()['evaluate_'+args.kind](Store(Path(args.store)),**refs)
    print(json.dumps(result,sort_keys=True));raise SystemExit(0 if result['outcome']=='PASS' else 2)
