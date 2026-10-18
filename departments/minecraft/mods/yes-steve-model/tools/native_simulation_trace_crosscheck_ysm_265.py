#!/usr/bin/env python3
"""Read-only GNU address/length/byte cross-check of a completed bounded Ghidra trace."""
import argparse,hashlib,json,re,subprocess,tempfile
from pathlib import Path
from native_export_backing_ysm_265 import regions,data_at
from native_simulation_copy_frontier_ysm_265 import IMAGE_SHA

def instructions(text):
    ops=[];seen={};count=None;complete=False
    for line in text.splitlines():
        f=line.split('\t')
        if f[0]=='INS':
            if len(f)!=4:raise ValueError('Malformed instruction')
            a=int(f[1],16);b=bytes.fromhex(f[2])
            if not 1<=len(b)<=15:raise ValueError('Invalid x86 length')
            if a in seen and seen[a]!=b:raise ValueError('Conflicting bytes at reused address')
            seen[a]=b;ops.append((a,b))
        elif f[0]=='COUNTS':
            if count is not None:raise ValueError('Multiple trial counters')
            fields=dict(x.split('=',1) for x in f[1:]);count=int(fields['attempted'])
        elif f[0]=='BOUNDED_RESULT':
            if complete:raise ValueError('Duplicate completion')
            complete=True
    if not complete or count!=len(ops) or not ops:raise ValueError('Incomplete or count-mismatched trace')
    return ops,seen

def groups(seen):
    result=[]
    for a,b in sorted(seen.items()):
        if result and a==result[-1][-1][0]+len(result[-1][-1][1]):result[-1].append((a,b))
        else:result.append([(a,b)])
    return result

def capture(image,trace):
    b=image.read_bytes();sha=hashlib.sha256(b).hexdigest()
    if sha!=IMAGE_SHA:raise ValueError('Wrong image')
    ops,seen=instructions(trace.read_text());rs=regions(b);reports=[]
    with tempfile.TemporaryDirectory() as d:
        tmp=Path(d)/'bytes.bin'
        for g in groups(seen):
            a=g[0][0];expected=b''.join(v for _,v in g);actual=data_at(b,rs,a,len(expected))
            if actual!=expected:raise ValueError('Trace differs from pinned image')
            tmp.write_bytes(actual);out=subprocess.check_output(['objdump','-D','-b','binary','-m','i386:x86-64','-M','intel','--insn-width=16','--adjust-vma='+str(a),str(tmp)],text=True);decoded=[]
            for line in out.splitlines():
                m=re.match(r'\s*([0-9a-f]+):\s*((?:[0-9a-f]{2} )+)\s*\t(.*)',line)
                if m:decoded.append((int(m[1],16),bytes.fromhex(m[2])))
            if decoded!=g:raise ValueError(f'GNU boundary/bytes disagreement at {a:x}')
            reports.append({'address':hex(a),'size':len(expected),'instructions':len(g),'sha256':hashlib.sha256(actual).hexdigest()})
    return {'format':'kneekura.ysm-simulation-decoder-crosscheck.v1','image_sha256':sha,'trace_sha256':hashlib.sha256(trace.read_bytes()).hexdigest(),'instruction_occurrences':len(ops),'unique_addresses':len(seen),'range_count':len(reports),'ranges':reports,'all_address_length_bytes_match':True,'gnu_version':subprocess.check_output(['objdump','--version'],text=True).splitlines()[0],'target_executed_by_this_tool':False,'scope':'Decoder boundaries and original bytes only. Not p-code equivalence, whole native recovery, all caller-state proof, or emulator model semantic certification.'}

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--image',required=True,type=Path);p.add_argument('--trace',required=True,type=Path);p.add_argument('--out',required=True,type=Path);a=p.parse_args();r=capture(a.image,a.trace);a.out.write_text(json.dumps(r,indent=2)+'\n');print('TRACE_DECODER_MATCH',r['instruction_occurrences'],r['unique_addresses'],r['range_count'])
if __name__=='__main__':main()
