#!/usr/bin/env python3
"""Conditional scalar proof after the stopped stack copy; never executes target code."""
import argparse,hashlib,json
from pathlib import Path
from itertools import groupby
from native_export_backing_ysm_265 import regions,data_at
from native_simulation_copy_frontier_ysm_265 import IMAGE_SHA
M32=(1<<32)-1

def decoded_delta(word,ebp):
    x=((word^ebp)+1)&M32
    x=((x<<1)|(x>>31))&M32
    x=(x-1)&M32
    x=((x>>1)|(x<<31))&M32
    x=(-x)&M32
    return (int.from_bytes(x.to_bytes(4,'little'),'big')-1)&M32

def fixed_predicates():
    # SHR DX,0xec uses count 12. For any DX the 16-bit sign flag is zero.
    js_values={((dx>>(0xec&31))>>15)&1 for dx in range(65536)}
    cx=0x9c26;bit=0x83&15;carry=(cx>>bit)&1;cx^=1<<bit
    # Later SHR CX,0xa7 uses 7, outgoing bit6 is zero.
    adc_carry=(cx>>(7-1))&1;cx>>=7
    # EBX=0, ADD BL,CH=>0x9c, XCHG BL,SIL (SIL=0)=>BL=0,SIL=0x9c.
    # SHL SIL,0x62 masks to 2, outgoing bit6=0. SBB DL,0x16 uses DL=0.
    shift_carry=(0x9c>>(8-(0x62&31)))&1
    before=0;sub=0x16+shift_carry;result=(before-sub)&255
    sf=(result>>7)&1;of=int(bool(((before^sub)&(before^result)&128)))
    return {'js_all_65536_dx_sign_flags':sorted(js_values),'js_taken':False,'jae_bit':bit,'jae_old_bit':carry,'jae_taken':not bool(carry),'cx_after_shift':cx,'adc_r11_carry':adc_carry,'sil_shift_carry':shift_carry,'sbb_dl_result':result,'sbb_sf':sf,'sbb_of':of,'jl_taken':sf!=of}

def analyze(image,original_trace,snapshot):
    b=image.read_bytes()
    if hashlib.sha256(b).hexdigest()!=IMAGE_SHA:raise ValueError('Wrong image')
    rows=snapshot.read_text().splitlines()
    if [x for x in rows if not x.startswith(('STOP_REGISTER\t','SOURCE_BYTE\t'))]!=original_trace.read_text().splitlines():raise ValueError('Changed snapshot path')
    regs={x.split('\t')[1]:int(x.split('\t')[2],16) for x in rows if x.startswith('STOP_REGISTER\t')}
    cells=[x.split('\t') for x in rows if x.startswith('SOURCE_BYTE\t')]
    if len(cells)!=328 or any(int(x[1],16)!=0x700000007d30+i for i,x in enumerate(cells)):raise ValueError('Wrong source interval')
    unknown=sum(x[2]=='UNKNOWN' for x in cells);intervals=[];offset=0
    for known,g in groupby(cells,lambda x:x[2]!='UNKNOWN'):
        size=len(list(g));intervals.append({'offset_start':offset,'offset_end':offset+size,'known':known});offset+=size
    if unknown!=80:raise ValueError('Changed knownness')
    rs=regions(b);segments=[(0x143beb0,29),(0x173afdb,3),(0x160cc74,32),(0x160cc94,40),(0x14fcf64,76)]
    word=int.from_bytes(data_at(b,rs,regs['R8']-4,4),'little');delta=decoded_delta(word,regs['RBP']&M32);signed=delta if delta<1<<31 else delta-(1<<32);flags=fixed_predicates()
    if flags['js_all_65536_dx_sign_flags']!=[0] or not flags['jae_taken'] or not flags['jl_taken']:raise ValueError('Predicate failure')
    return {'format':'kneekura.ysm-conditional-postcopy.v1','image_sha256':IMAGE_SHA,'target_execution_beyond_stopped_read':False,'snapshot_trace_preserved':True,'source_bytes':328,'source_known_bytes':328-unknown,'source_unknown_bytes':unknown,'source_knownness_intervals':intervals,'conditional_edges':[{'at':'0x143bec8','to':'0x173afdb','kind':'direct JMP'},{'at':'0x173afdb','to':hex(regs['R11']),'kind':'unchanged stopped R11, conditional on completed copy'},{'at':'0x160cc8e','to':'0x160cc94','kind':'JS untaken'},{'at':'0x160ccb6','to':'0x14fcf64','kind':'JAE taken'},{'at':'0x14fcfaa','to':'0x14cb406','kind':'JL taken'}],'flags':flags,'word_address':hex(regs['R8']-4),'file_word':hex(word),'ebp':hex(regs['RBP']&M32),'decoded_delta':hex(delta),'candidate_r11':hex(regs['R11']+signed),'segments':[{'address':hex(a),'size':n,'sha256':hashlib.sha256(data_at(b,rs,a,n)).hexdigest()} for a,n in segments],'snapshot_sha256':hashlib.sha256(snapshot.read_bytes()).hexdigest(),'assumptions':['Copy completes with opaque unknown bytes preserved; this is not claimed to have executed','Stopped R8/RBP/R11 retained and image bytes unchanged','Normal instruction completion; no external interference','Copied unknown bytes may be used later; no harmless-padding claim','Only listed scalar predicates and candidate are derived, not whole continuation or initializer effects'],'independent_semantic_review':'NOT_RUN'}

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--image',type=Path,required=True);p.add_argument('--original-trace',type=Path,required=True);p.add_argument('--snapshot',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args();r=analyze(a.image,a.original_trace,a.snapshot);a.out.write_text(json.dumps(r,indent=2)+'\n');print('POSTCOPY_CONDITIONAL_PROOF',r['source_unknown_bytes'],r['candidate_r11'])
if __name__=='__main__':main()
