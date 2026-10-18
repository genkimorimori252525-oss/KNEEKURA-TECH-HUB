#!/usr/bin/env python3
"""Summarize retained clock scenarios and resolve the blocked ELF import; read-only."""
import argparse,hashlib,json,struct
from pathlib import Path
from native_export_backing_ysm_265 import regions,data_at
from native_initializer_inventory_ysm_265 import dynamic_records,rela_records
from native_image_metadata_ysm_265 import header
from native_simulation_copy_frontier_ysm_265 import IMAGE_SHA
from native_simulation_trace_crosscheck_ysm_265 import instructions

def import_slot(b,slot):
    if hashlib.sha256(b).hexdigest()!=IMAGE_SHA:raise ValueError('Wrong native image')
    h=header(b);rs=regions(b);ph=[struct.unpack_from('<IIQQQQQQ',b,h['program_header_offset']+i*56) for i in range(h['program_header_count'])];dynph=[p for p in ph if p[0]==2]
    if len(dynph)!=1:raise ValueError('Missing unique PT_DYNAMIC')
    p=dynph[0];dyn=dict(dynamic_records(b[p[2]:p[2]+p[5]]));rel=rela_records(data_at(b,rs,dyn[7],dyn[8]))+rela_records(data_at(b,rs,dyn[23],dyn[2]));hits=[x for x in rel if x[0]==slot]
    if len(hits)!=1:raise ValueError('Missing unique relocation')
    _,info,addend=hits[0];sym=info>>32;name,kind,other,section,value,size=struct.unpack('<IBBHQQ',data_at(b,rs,dyn[6]+sym*24,24))
    if section!=0 or name>=dyn[10]:raise ValueError('Not an undefined named import')
    symbol=data_at(b,rs,dyn[5]+name,dyn[10]-name).split(b'\0')[0].decode('ascii')
    return {'slot':hex(slot),'raw_value':hex(int.from_bytes(data_at(b,rs,slot,8),'little')),'relocation_type':info&0xffffffff,'symbol_index':sym,'symbol_name':symbol,'addend':addend,'actual_runtime_binding_verified':False}

def trace(path):
    text=path.read_text();ops,seen=instructions(text);lines=text.splitlines();stops=[x.split('\t') for x in lines if x.startswith('STOP\t')];counts=[x.split('\t') for x in lines if x.startswith('COUNTS\t')];regs={x.split('\t')[1]:int(x.split('\t')[2],16) for x in lines if x.startswith('STOP_REGISTER\t')};oracles=[x.split('\t') for x in lines if x.startswith('ORACLE\t')]
    if len(stops)!=1 or len(counts)!=1 or not all(x[3][7:]==x[4][9:] for x in oracles):raise ValueError('Invalid stop/count/oracle record')
    return ops,{'trace_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'stop':stops[0][1:],'counts':{k:int(v) for k,v in (x.split('=',1) for x in counts[0][1:])},'unique_instruction_addresses':len(seen),'oracles_matched':len(oracles),'clock_reads':[x.split('\t')[1:] for x in lines if x.startswith('VIRTUAL_TSC\t')],'registers':{k:hex(v) for k,v in regs.items()},'preservation_confirmed':'PRESERVATION\tfile_and_seven_program_segments_unchanged=true' in lines}

def capture(image,out):
    b=image.read_bytes();resolved=import_slot(b,0x184d828)
    if resolved['symbol_name']!='malloc' or resolved['relocation_type']!=6:raise ValueError('Unexpected stopped import')
    seeds=['0','100000000','1122334455667788'];traces=[];reports=[]
    for seed in seeds:
        ops,r=trace(out/f'bounded-init-clock-{seed}.tsv');traces.append(ops);reports.append({'seed_hex':seed,'stride_hex':'3e8',**r})
    if traces[0]!=traces[1]:raise ValueError('Low-seed instruction paths changed')
    k=next((i for i,(a,b2) in enumerate(zip(traces[0],traces[2])) if a!=b2),min(len(traces[0]),len(traces[2])))
    source=(out/'bounded-init-clock-1122334455667788.tsv').read_text().splitlines();snapshot=(out/'bounded-init-clock-mixed-stack.tsv').read_text().splitlines()
    if source!=[x for x in snapshot if not x.startswith('STOP_STACK_BYTE\t')]:raise ValueError('Stack observer altered trial')
    cells=[x.split('\t')[2] for x in snapshot if x.startswith('STOP_STACK_BYTE\t')];ra=int.from_bytes(bytes.fromhex(''.join(cells[:8])),'little')
    original,pre=trace(out/'bounded-init-100k-trial.tsv')
    if any(t[:len(original)]!=original for t in traces):raise ValueError('Pre-clock instruction path changed')
    return {'format':'kneekura.ysm-virtual-clock-frontier.v1','image_sha256':IMAGE_SHA,'clock_disabled_100k_trial':pre,'scenarios':reports,'low_seed_paths_identical':True,'first_mixed_seed_instruction_difference_step':k+1,'divergence_branch':hex(traces[0][k-1][0]),'low_successor':hex(traces[0][k][0]),'mixed_successor':hex(traces[2][k][0]),'blocked_import':resolved,'sysv_malloc_size_argument':int(reports[2]['registers']['RDI'],16),'caller_return_candidate':hex(ra),'clock_is_explicit_synthetic_input':True,'host_clock_used_as_target_input':False,'host_native_or_import_execution':False,'heap_allocation_or_nonstack_write_performed':False,'proof_scope':'Three synthetic clock samples only, not all clocks or actual runtime. ELF name resolves metadata, not a live loader binding.','independent_semantic_review':'NOT_RUN','target_executed_by_this_summary_tool':False}

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--image',type=Path,required=True);p.add_argument('--trace-directory',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args();r=capture(a.image,a.trace_directory);a.out.write_text(json.dumps(r,indent=2)+'\n');print('CLOCK_SCENARIOS',len(r['scenarios']),'IMPORT',r['blocked_import']['symbol_name'],'SIZE',r['sysv_malloc_size_argument'])
if __name__=='__main__':main()
