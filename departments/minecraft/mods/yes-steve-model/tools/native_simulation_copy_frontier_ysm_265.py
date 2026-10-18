#!/usr/bin/env python3
"""Check the existing bounded trace and derive the stack-copy frontier; no target execution."""
import argparse, hashlib, json
from pathlib import Path
from native_export_backing_ysm_265 import regions, data_at
IMAGE_SHA='15d0379718c5a293fc2f36fe17f2f95d5a031b8d5564f06355e08640f22b4c22'

def copy_contract():
    esi=0xfd9f2338
    esi &= ~(1 << (esi & 31))
    count=(esi & 255)+0x110
    # SUB RSI,RSI clears carry; SBB therefore subtracts count with no extra borrow.
    # BTS SI,5 gives 32; SHR RSI,0xb1 masks to 49, yielding 0 with carry 0.
    return {'count':count,'source':'old RSP','destination':'align_down(incoming RDI - 0x1c8, 16)','direction':'forward','source_offset_after_96_completed':96}

def analyze(image, original, diagnostic):
    b=image.read_bytes()
    if hashlib.sha256(b).hexdigest()!=IMAGE_SHA: raise ValueError('Wrong original native image')
    rs=regions(b)
    if data_at(b,rs,0x143beae,2)!=bytes.fromhex('f3a4'): raise ValueError('Changed REP MOVSB')
    old=original.read_text().splitlines(); new=diagnostic.read_text().splitlines()
    if old!=[x for x in new if not x.startswith('STOP_REGISTER\t')]: raise ValueError('Diagnostic replay changed prior trace')
    registers={x.split('\t')[1]:int(x.split('\t')[2],16) for x in new if x.startswith('STOP_REGISTER\t')}
    if set(registers)!={'RSP','RBP','RSI','RDI','RCX','R10','DF'}: raise ValueError('Missing stop registers')
    ins=[x.split('\t') for x in new if x.startswith('INS\t')]
    copies=[x for x in ins if x[1]=='143beae']
    if len(copies)!=97 or registers['DF']!=0: raise ValueError('Unexpected copy path')
    stop=[x for x in new if x.startswith('STOP\t')]
    if stop!=['STOP\tUNINITIALIZED_READ\tstate\tpc=143beae\taddress=700000007d90\tsize=1']: raise ValueError('Wrong stopped read')
    count=copy_contract()['count'];completed=len(copies)-1
    # Ghidra SLEIGH rep/eseDI1/dseSI1 update RCX/RDI/RSI before the LOAD.
    # A stopped micro-op snapshot is NOT an x86 architectural fault snapshot.
    source=registers['RSI']-len(copies);dest=registers['RDI']-len(copies)
    if registers['RCX']+len(copies)!=count or registers['R10']!=source: raise ValueError('Count/source mismatch')
    if source+completed!=0x700000007d90: raise ValueError('Read position mismatch')
    if not (0x700000000000<=dest<source<source+count<=0x700000010000): raise ValueError('Not private stack copy')
    segments=[(0x15ebcb3,93),(0x143beae,26)]
    return {'format':'kneekura.ysm-native-copy-frontier.v1','image_sha256':IMAGE_SHA,'static_contract':copy_contract(),'replay_trace_unchanged':True,'stop_registers':{k:hex(v) for k,v in registers.items()},'source_range':[hex(source),hex(source+count)],'destination_range':[hex(dest),hex(dest+count)],'completed_byte_copies':completed,'next_unknown_source':hex(source+completed),'next_unwritten_destination':hex(dest+completed),'overlap_bytes':max(0,dest+count-source),'direction_compatible_with_overlap':dest<source,'initial_rsp_minus_unknown_address':hex(0x700000008008-(source+completed)),'unknown_bytes_filled':False,'target_run_by_this_tool':False,'segments':[{'address':hex(a),'size':n,'sha256':hashlib.sha256(data_at(b,rs,a,n)).hexdigest()} for a,n in segments],'input_hashes':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in (original,diagnostic)},'limitations':['Single synthetic caller-state path only','Actual caller stack content and why copied byte is uninitialized remain unresolved','No skip, zero-fill or continued execution after guard','SLEIGH partial micro-op registers are not committed architectural state','No proof of native initializer completeness or decoder-word immutability']}

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--image',required=True,type=Path);p.add_argument('--original-trace',required=True,type=Path);p.add_argument('--diagnostic-trace',required=True,type=Path);p.add_argument('--out',required=True,type=Path);a=p.parse_args();r=analyze(a.image,a.original_trace,a.diagnostic_trace);a.out.write_text(json.dumps(r,indent=2)+'\n');print('COPY_FRONTIER_VERIFIED',r['completed_byte_copies'],r['source_range'],r['destination_range'])
if __name__=='__main__':main()
