#!/usr/bin/env python3
"""Validate read-only Spore G09-G13 evidence companion traces.

This does not assert Forge/GameTest PASS: only controlled run-scoped observation
coverage, even when a trace looks valid. Synthetic fixtures never authorize
runtime conclusions. Evidence attestation belongs to KNEEKURA-LAB registry.
"""
from __future__ import annotations
import argparse
from collections import defaultdict
import hashlib
import json
import math
from pathlib import Path
import statistics
import sys

TARGET_SHA='d20c4be6606f9752ecfd964eba625363eb76a28e327d67fe6dda4be748401489'
MAX_SIZE=8_000_000
MAX_ROWS=50_000
SCENARIOS={'G09','G10','G11','G12','G13'}

class InvalidTrace(ValueError):
    pass


def require(cond, text):
    if not cond: raise InvalidTrace(text)


def number(v):
    return isinstance(v,(float,int)) and not isinstance(v,bool) and math.isfinite(v)


def read_trace(path:Path):
    require(path.stat().st_size < MAX_SIZE, 'trace exceeds 8 MB cap')
    with path.open('rt',encoding='utf-8') as f:
        lines=f.readlines()
    require(1 < len(lines) <= MAX_ROWS, 'truncated or oversized trace')
    try:
        rows=[json.loads(line) for line in lines]
    except (json.JSONDecodeError,UnicodeDecodeError) as exc:
        raise InvalidTrace('JSONL parse failure') from exc
    require(all(isinstance(row,dict) for row in rows), 'all rows must be objects')
    require(rows[0].get('ch')=='spore_meta', 'first record must be spore_meta')
    require(rows[-1].get('ch')=='spore_end', 'last record must be spore_end')
    require(sum(row.get('ch')=='spore_meta' for row in rows)==1, 'exactly one meta')
    require(sum(row.get('ch')=='spore_end' for row in rows)==1, 'exactly one end')
    meta,end=rows[0],rows[-1]
    required_meta=['schema','run_id','scenario','jar_sha256','minecraft','loader','seed','world_id','origin','physical_side','observer_identity']
    for k in required_meta: require(k in meta, 'missing meta.'+k)
    require(meta['schema']=='kneekura.spore.observation.v1','schema mismatch')
    require(meta['scenario'] in SCENARIOS,'unknown scenario')
    require(meta['jar_sha256']==TARGET_SHA,'wrong artifact identity')
    require(meta['minecraft']=='1.20.1' and meta['loader']=='Forge', 'wrong version/loader')
    require(meta['physical_side']=='DEDICATED_SERVER', 'server-side run required')
    require(meta['origin'] in {'synthetic_fixture','runtime_claim_unattested'}, 'unsupported provenance')
    for key in ['run_id','world_id','observer_identity']:
        require(isinstance(meta[key],str) and 1<=len(meta[key])<=128,key+' missing or too long')
    require(type(meta['seed']) is int, 'seed integer required')
    require(meta.get('world_disposable') is True, 'disposable-world declaration missing')
    require(isinstance(meta.get('dimension'), str) and meta['dimension'], 'missing dimension/scope')
    require(end.get('run_id')==meta['run_id'] and end.get('scenario')==meta['scenario'], 'end run/scenario mismatch')
    require(end.get('reason') in {'completed','aborted','timeout','error'},'unknown end reason')
    require(type(end.get('observation_count')) is int and end['observation_count']>=0,'invalid observation count')
    require(end['observation_count']==len(rows)-2,'mismatched declared row count')
    events=rows[1:-1]
    seq=-1; tick=-1
    for ix,e in enumerate(events):
        require(e.get('ch')=='spore_observation', f'row {ix} unsupported channel')
        require(e.get('run_id')==meta['run_id'] and e.get('scenario')==meta['scenario'], f'row {ix} cross-run/scenario')
        require(e.get('world_id')==meta['world_id'], f'row {ix} cross-world')
        require(e.get('dimension')==meta['dimension'] or meta['dimension']=='MULTI_DIMENSION', f'row {ix} dimension mismatch')
        require(type(e.get('seq')) is int and e['seq']>seq, f'row {ix} duplicate/non-increasing sequence')
        require(type(e.get('tick')) is int and e['tick']>=tick, f'row {ix} decreasing tick')
        require(isinstance(e.get('kind'),str) and len(e['kind'])<=64, f'row {ix} invalid event kind')
        require(isinstance(e.get('data'),dict),f'row {ix} invalid event body')
        require(len(json.dumps(e['data'],ensure_ascii=False))<=4096,'payload too large')
        seq,tick=e['seq'],e['tick']
    return meta,events,end


def eval_g09(events):
    rows=[]
    for e in events:
        if e['kind']!='signal_dispatch':continue
        d=e['data']; candidates=d.get('candidates'); recipient=d.get('recipient_uuid')
        if not isinstance(candidates,list) or len(candidates)<2 or len(candidates)>32 or not isinstance(recipient,str):continue
        if any(not isinstance(c,dict) or not isinstance(c.get('uuid'),str) or not number(c.get('distance_sq')) or c['distance_sq']<0 for c in candidates):continue
        ids=[c['uuid'] for c in candidates]
        if len(set(ids))!=len(ids) or recipient not in ids:continue
        first,near=ids[0],min(candidates,key=lambda c:c['distance_sq'])['uuid']
        if first==near:continue  # undiscriminating setup
        rows.append({'signal_id':d.get('signal_id'), 'first':first,'closest':near,'chosen':recipient,'chosen_first':recipient==first,'chosen_closest':recipient==near})
    return {'state':'OBSERVED_CONTRAST' if rows else 'INCONCLUSIVE','qualified_events':len(rows),'examples':rows[:4]}


def eval_g10(events):
    counts=defaultdict(lambda:{'attempts':0,'redirect':0,'womb_attempt':0,'womb_spawn_success':0})
    for e in events:
        if e['kind']!='signal_resolution':continue
        d=e['data']; n=d.get('eligible'); decision=d.get('decision')
        if type(n) is not int or n<0 or n>10000 or decision not in {'redirect','womb_attempt'}:continue
        a=counts[n];a['attempts']+=1;a[decision]+=1
        if decision=='womb_attempt' and d.get('spawn_success') is True:a['womb_spawn_success']+=1
    required={0,1,2,4}
    coverage=all(counts[n]['attempts']>0 for n in required)
    return {'state':'OBSERVED_CONTRAST' if coverage else 'INCONCLUSIVE','qualified_counts':dict(sorted(counts.items())),'needed_eligible_groups':sorted(required),'covered_groups':sorted(n for n,c in counts.items() if c['attempts']>0)}


def eval_g11(events):
    groups=defaultdict(list)
    for e in events:
        if e['kind'] not in {'wave_award','wave_spawn_attempt','wave_spawn_result','vigil_retire','vigil_penalty'}:continue
        uid=e['data'].get('vigil_uuid')
        if not isinstance(uid,str) or not uid:continue
        groups[uid].append((e['seq'],e['kind'],e['data']))
    complete=[]
    for uid,events_for_vigil in groups.items():
        kinds=[x[1] for x in events_for_vigil]
        required=('wave_award','wave_spawn_attempt','wave_spawn_result','vigil_retire','vigil_penalty')
        if all(k in kinds for k in required):
            first=[next(x[0] for x in events_for_vigil if x[1]==kind) for kind in required]
            if first==sorted(first) and len(set(first))==len(first):
                complete.append(uid)
    return {'state':'OBSERVED_CHAIN' if complete else 'INCONCLUSIVE','vigil_count':len(groups),'fully_observed_vigils':complete[:12]}


def eval_g12(events):
    near_search=[];far_search=[];follow_near=[];follow_far=[]
    for e in events:
        d=e['data']
        if e['kind']=='search_goal_step' and number(d.get('distance_to_block_center')):
            dist=d['distance_to_block_center']
            if 8.5<=dist<9.0 and type(d.get('search_pos_cleared')) is bool:near_search.append(d)
            if 9.0<=dist<=9.5 and type(d.get('search_pos_cleared')) is bool:far_search.append(d)
        if e['kind']=='follow_goal_step' and number(d.get('distance_sq')):
            dist=d['distance_sq']
            if 0<=dist<=9 and type(d.get('navigation_stopped')) is bool:follow_near.append(d)
            if 9<dist<=16 and type(d.get('navigation_stopped')) is bool:follow_far.append(d)
    return {'state':'OBSERVED_BOUNDARIES' if all((near_search,far_search,follow_near,follow_far)) else 'INCONCLUSIVE','sample_counts':{'search_lt_9':len(near_search),'search_gte_9':len(far_search),'follower_sq_lte_9':len(follow_near),'follower_sq_gt_9':len(follow_far)}}


def percentile(xs,p):
    ordered=sorted(xs)
    if len(ordered)==1:return ordered[0]
    at=(len(ordered)-1)*p
    i=math.floor(at); t=at-i
    return ordered[i]*(1-t)+ordered[min(i+1,len(ordered)-1)]*t


def eval_g13(events):
    cells=defaultdict(list)
    for e in events:
        if e['kind']!='server_tick_sample':continue
        d=e['data']; n=d.get('proto_count');signals=d.get('signal_count'); infected=d.get('infected_count');value=d.get('tick_ms')
        if type(n) is not int or n not in (1,4,16) or type(signals) is not int or signals not in (0,1,10) or type(infected) is not int or infected not in (0,100,1000) or not number(value) or value<0 or value>10000:continue
        cells[(n,signals,infected)].append(float(value))
    summaries=[]
    for (n,s,i),values in sorted(cells.items()):
        summaries.append({'proto_count':n,'signal_count':s,'infected_count':i,'samples':len(values),'mean_ms':round(statistics.mean(values),4),'p95_ms':round(percentile(values,.95),4),'p99_ms':round(percentile(values,.99),4)})
    covered={n for n,s,i in cells if s==0 and i==0 and len(cells[(n,s,i)])>=200}
    return {'state':'OBSERVED_BASELINE_COMPARISON' if covered=={1,4,16} else 'INCONCLUSIVE','qualified_baseline_proto_counts':sorted(covered),'summaries':summaries[:30],'performance_pass':'NOT_EVALUATED_WITHOUT_REGISTERED_THRESHOLD'}

EVALS={'G09':eval_g09,'G10':eval_g10,'G11':eval_g11,'G12':eval_g12,'G13':eval_g13}


def evaluate(path:Path):
    digest=hashlib.sha256(path.read_bytes()).hexdigest() if path.stat().st_size<MAX_SIZE else None
    try:
        meta,rows,end=read_trace(path)
    except (InvalidTrace,KeyError,TypeError,ValueError) as exc:
        return {'schema':'kneekura.spore.observation-review.v1','status':'BLOCKED_INVALID_TRACE','error':str(exc),'trace_sha256':digest,'runtime_pass':False}
    r=EVALS[meta['scenario']](rows)
    if meta['origin']=='synthetic_fixture':status='SYNTHETIC_FIXTURE_ONLY'
    elif end['reason']!='completed':status='INCONCLUSIVE_INCOMPLETE_RUN'
    elif r['state']=='INCONCLUSIVE':status='INCONCLUSIVE_INSUFFICIENT_EVIDENCE'
    else:status='IMPORTED_UNATTESTED_OBSERVATIONS'
    return {'schema':'kneekura.spore.observation-review.v1',
            'status':status,'run_id':meta['run_id'],'scenario':meta['scenario'],'source_kind':meta['origin'],
            'trace_sha256':digest,'observation_count':len(rows),'end_reason':end['reason'],
            'observation_coverage':r,'runtime_pass':False,
            'warning':'LAB authenticated run/world/cleanup receipts, independent code-path attestation and actual GameTest assertions are required before runtime PASS. A JSONL text file cannot grant this.'}


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('jsonl',type=Path);p.add_argument('--out',type=Path)
    o=p.parse_args()
    if not o.jsonl.is_file():p.error('No trace')
    result=evaluate(o.jsonl)
    blob=json.dumps(result,sort_keys=True,indent=2,ensure_ascii=False)+'\n'
    if o.out:o.out.write_text(blob,encoding='utf-8')
    else:print(blob,end='')
    return 2 if result['status']=='BLOCKED_INVALID_TRACE' else 0

if __name__=='__main__':sys.exit(main())
