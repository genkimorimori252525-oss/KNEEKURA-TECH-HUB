#!/usr/bin/env python3
"""Compare complete isolated checkpoint state, excluding diagnostic history and unused engine pointers."""
import argparse,hashlib,json
from pathlib import Path
from native_guarded_checkpoint_ysm_265 import sanitize_context,unpack,ContextHeader
from native_unicorn_guarded_ysm_265 import STACK,STACK_SIZE,HEAP,HEAP_SIZE

def compare(a,b):
    def context(s):
        m=s['context'];return sanitize_context(unpack(m['bytes'],m['size']),m['size'],m['arch'],m['mode'])
    def fields(s):return {k:v for k,v in s['fields'].items() if k!='rollback_count'}
    checks={'format_and_engine_equal':(a['format'],a['engine'])==(b['format'],b['engine']),'cpu_context_equal_excluding_unused_memory_snapshot_header':context(a)==context(b),'model_state_equal_excluding_diagnostic_rollbacks':fields(a)==fields(b),'cumulative_completed_equal':a['origin_completed']+a.get('prior_origin_completed',0)==b['origin_completed']+b.get('prior_origin_completed',0)}
    for key in ('images','opaque','fixture','cpuid_leaf1','oracle_seen','shadow_ranges','patches','origin_stop'):checks[key+'_equal']=a[key]==b[key]
    for base,n in ((STACK,STACK_SIZE),(HEAP,HEAP_SIZE)):
        for field in ('bytes','known'):checks[f'{base:x}_{field}_equal']=unpack(a['private'][str(base)][field],n)==unpack(b['private'][str(base)][field],n)
    return {'all_checks_pass':all(checks.values()),'checks':checks,'cumulative_completed':a['origin_completed']+a.get('prior_origin_completed',0),'diagnostic_rollback_counts':[a['fields']['rollback_count'],b['fields']['rollback_count']],'cpu_context_payload_sha256':hashlib.sha256(context(a)).hexdigest(),'normalization':'Unicorn2.1.4 CPU-only context; unused memory-snapshot header fields zeroed. All CPU payload bytes compared.','host_target_execution':False}
def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('full',type=Path);p.add_argument('resumed',type=Path);p.add_argument('--out',type=Path,required=True);a=p.parse_args()
    full=a.full.read_bytes();resumed=a.resumed.read_bytes();r=compare(json.loads(full),json.loads(resumed));r.update(full_checkpoint_sha256=hashlib.sha256(full).hexdigest(),resumed_checkpoint_sha256=hashlib.sha256(resumed).hexdigest());a.out.write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(r));raise SystemExit(0 if r['all_checks_pass'] else 1)
if __name__=='__main__':main()
