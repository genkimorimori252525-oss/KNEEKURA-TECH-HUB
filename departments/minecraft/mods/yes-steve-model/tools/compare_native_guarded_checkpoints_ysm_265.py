#!/usr/bin/env python3
"""Compare complete isolated checkpoint state, excluding diagnostic history and unused engine pointers."""
import argparse,hashlib,json
from pathlib import Path
from native_guarded_checkpoint_ysm_265 import sanitize_context,unpack,ContextHeader
from native_unicorn_guarded_ysm_265 import STACK,STACK_SIZE,HEAP,HEAP_SIZE

def compare(a,b,allow_acceleration=False):
    def context(s):
        m=s['context'];return sanitize_context(unpack(m['bytes'],m['size']),m['size'],m['arch'],m['mode'])
    ignored={'rollback_count'}|({'accelerate_crc','crc_blocks','crc_iterations','crc_logical_steps'} if allow_acceleration else set())
    def fields(s):return {k:v for k,v in s['fields'].items() if k not in ignored}
    def count(s):
        actual=s['origin_completed']+s.get('prior_origin_completed',0)
        return actual+s['fields']['crc_logical_steps']-s['fields']['crc_blocks'] if allow_acceleration else actual
    checks={'format_and_engine_equal':(a['format'],a['engine'])==(b['format'],b['engine']),'cpu_context_equal_excluding_host_only_fields':context(a)==context(b),'model_state_equal_excluding_diagnostic_rollbacks':fields(a)==fields(b),'cumulative_completed_equal':count(a)==count(b)}
    if allow_acceleration:checks['logical_instruction_effects_equal']=checks.pop('cumulative_completed_equal')
    checks['environment_state_equal']=a.get('environment')==b.get('environment')
    checks['sparse_state_equal']=a.get('sparse')==b.get('sparse')
    for key in ('images','opaque','fixture','cpuid_leaf1','oracle_seen','shadow_ranges','patches','origin_stop'):checks[key+'_equal']=a[key]==b[key]
    legacy={'base':0x700000000000,'size':0x10000,'initial_sp':0x700000008008}
    layouts=[s.get('stack_layout',legacy) for s in (a,b)]
    checks['stack_layout_equal']=layouts[0]==layouts[1]
    checks['scenario_extensions_equal']=a.get('scenario_extensions',[])==b.get('scenario_extensions',[])
    checks['private_region_keys_equal']=set(a['private'])==set(b['private'])
    for base,n in ((layouts[0]['base'],layouts[0]['size']),(HEAP,HEAP_SIZE)):
        for field in ('bytes','known'):
            key=str(base)
            checks[f'{base:x}_{field}_equal']=(key in a['private'] and key in b['private'] and (base==HEAP or checks['stack_layout_equal']) and unpack(a['private'][key][field],n)==unpack(b['private'][key][field],n))
    return {'all_checks_pass':all(checks.values()),'acceleration_comparison':allow_acceleration,'excluded_model_fields':sorted(ignored),'checks':checks,'cumulative_completed':a['origin_completed']+a.get('prior_origin_completed',0),'diagnostic_rollback_counts':[a['fields']['rollback_count'],b['fields']['rollback_count']],'cpu_context_payload_sha256':hashlib.sha256(context(a)).hexdigest(),'normalization':'Unicorn2.1.4 CPU-only context; unused memory-snapshot header and pinned x86 host TCG retaddr zeroed. All remaining CPU payload bytes compared.'+(' Acceleration diagnostics/configuration excluded explicitly; compare completed+crc_logical_steps-crc_blocks.' if allow_acceleration else ''),'host_target_execution':False}
def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('full',type=Path);p.add_argument('resumed',type=Path);p.add_argument('--allow-acceleration',action='store_true');p.add_argument('--out',type=Path,required=True);a=p.parse_args()
    full=a.full.read_bytes();resumed=a.resumed.read_bytes();r=compare(json.loads(full),json.loads(resumed),a.allow_acceleration);r.update(full_checkpoint_sha256=hashlib.sha256(full).hexdigest(),resumed_checkpoint_sha256=hashlib.sha256(resumed).hexdigest());a.out.write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(r));raise SystemExit(0 if r['all_checks_pass'] else 1)
if __name__=='__main__':main()
