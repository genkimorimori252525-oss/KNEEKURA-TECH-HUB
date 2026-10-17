#!/usr/bin/env python3
"""Two fixed post-return predicates and a symbolic return; static scalar models only."""
import hashlib
from native_candidate_stack_guard_ysm_265 import signed
SEGMENTS=[(0xee9a3d,163,'994988bacb9f6a24f7c0a63b0cf14c2c7f9a6f23604984a8f7e22eb4e998c79f'),(0x10d1774,44,'c0732fe8f0e0cd5780dc426912274b2c94241440c3dcf785728ab444417a26d7'),(0xf0ae94,56,'fdf0617561bffa85df604d9fcefbdbd404435f6e99264074b4ebc350b3ec4c4e')]
def validate_parts(parts):
 if len(parts)!=len(SEGMENTS) or any(len(p)!=n or hashlib.sha256(p).hexdigest()!=h for p,(_,n,h) in zip(parts,SEGMENTS)):raise ValueError('Changed fixed post-return prefixes')
def neg_jbe(value,width):
 value&=(1<<width)-1;result=(-value)&((1<<width)-1)
 cf=int(value!=0);zf=int(result==0)
 return dict(result=result,cf=cf,zf=zf,taken=bool(cf or zf))
def or_jg(left,right):
 result=(left|right)&((1<<64)-1);sf=(result>>63)&1;zf=int(result==0);of=0
 return dict(result=result,sf=sf,zf=zf,of=of,taken=not zf and sf==of)
def fixed_registers():
 rax=0x7d8ea0b6
 rdx=(1<<64)-1 if rax&(1<<63) else 0 # CQO before CWDE
 eax=signed(rax&65535,16)&0xffffffff
 r10=rdx&65535
 # Exchange DL/R10B is zero/zero; SUB AX,R10W preserves negative AX.
 ax=((eax&65535)-r10)&65535
 dx=65535 if ax&32768 else 0
 rdx=(rdx&~65535)|dx
 dx=((dx>>4)|(dx<<12))&65535 # ROR DX,0x24
 rdx=(rdx&~65535)|dx
 r11=rdx&255
 return dict(ax_at_cwd=ax,rdx=rdx,r11_before_or=r11,or_stack_offset=rdx-0xffff,return_store_offset=rdx*4-0x3fffc)
def capture(jar):
 import json,zipfile,struct
 from native_image_metadata_ysm_265 import SHA,IMAGES
 from native_export_backing_ysm_265 import regions,data_at,backing
 from native_second_return_ysm_265 import capture as parent_capture
 parent=parent_capture(jar)
 with zipfile.ZipFile(jar) as z:b=z.read('META-INF/native/libysm-core.so')
 if hashlib.sha256(b).hexdigest()!=dict(IMAGES)['libysm-core.so']:raise ValueError('Wrong image')
 rs=regions(b);parts=[data_at(b,rs,a,n) for a,n,_ in SEGMENTS];validate_parts(parts)
 targets=[a+n+struct.unpack_from('<i',p,len(p)-4)[0] for (a,n,_),p in zip(SEGMENTS[:2],parts[:2])]
 if targets!=[0x10d1774,0xf0ae94]:raise ValueError('Unexpected branch targets')
 regs=fixed_registers();jg=or_jg(regs['rdx'],regs['r11_before_or'])
 if not jg['taken'] or regs['or_stack_offset'] or regs['return_store_offset']:raise ValueError('Local guard proof failed')
 if not all(neg_jbe(x,16)['taken'] for x in range(65536)):raise ValueError('NEG/JBE identity failed')
 return dict(format='kneekura.ysm-native-post-return-guards.v1',artifact_sha256=SHA,image_sha256=dict(IMAGES)['libysm-core.so'],dependency_second_return_sha256=hashlib.sha256(json.dumps(parent,sort_keys=True).encode()).hexdigest(),segments=[dict(address=a,size=n,sha256=h) for a,n,h in SEGMENTS],neg_jbe=dict(address=0xee9ada,operand_bits=16,all_65536_inputs_checked=True,taken=True,target=targets[0]),fixed_registers=regs,or_jg=dict(address=0x10d179a,flags=jg,taken=True,target=targets[1]),symbolic_return=dict(address=0xf0aecb,stack_store_address=0xf0aec3,store_offset=0,destination='RDI after ADD at 0xee9aaf',stack_advance=8,concrete_destination_resolved=False),next_unresolved='Third decoded data word and carried key feeding R11D, then MOVSXD R11 and ADD RDI,R11 at 0xee9aaf',assumptions=['The preceding second file-state candidate is reached under its recorded assumptions','Fixed unmodified prefixes execute in x86-64 mode without external interference or memory faults','PUSH RDX writes its ordinary eight-byte stack value before the OR'],target_executed=False,native_machine_emulator_run=False,runtime_reachability_verified=False,native_implementations_resolved=False,java_native_bindings_resolved=False,independent_semantic_review='NOT_RUN')
def main():
 import argparse,json
 from pathlib import Path
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--jar',required=True);p.add_argument('--out',required=True);p.add_argument('--check',action='store_true');a=p.parse_args();r=capture(Path(a.jar));out=Path(a.out)
 if a.check:
  if json.loads(out.read_text())!=r:raise SystemExit('Post-return proof mismatch')
 else:out.write_text(json.dumps(r,indent=2)+'\n')
 print(json.dumps({'status':'MATCH' if a.check else 'WRITTEN','taken_predicates':2,'next_return':'0xf0aecb','concrete_destination_resolved':False}))
if __name__=='__main__':main()
