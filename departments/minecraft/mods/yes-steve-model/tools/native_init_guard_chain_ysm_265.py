#!/usr/bin/env python3
"""Fixed post-return DT_INIT predicates, without executing or emulating the target."""
import hashlib,json
from pathlib import Path
from native_candidate_stack_guard_ysm_265 import signed
M=(1<<64)-1

def fixed_flags():
 edi=0xd19e3936;r9=edi&255;r10=signed(edi&65535,16)&0xffffffff
 rax=(r9+edi*8-0x5d6fa273)&M;rax=signed(rax&65535,16)&0xffffffff
 edi=(edi&~65535)|(((edi&65535)+1)&65535);r10=(r10-1)&M
 rdx=M if rax&(1<<63) else 0
 rax=(rax&~255)|((rax&255)>>1);rax=(rax&~65535)|(signed(rax&255,8)&65535);rax=(rax&~255)|((rax&255)|0xa3)
 # OR AL clears CF; the later NOT BL preserves all flags.
 before=r10&0xffffffff;borrow=int(before<edi);result=(before-edi)&0xffffffff;sf=(result>>31)&1
 return dict(r10d_before_sbb=before,edi_at_sbb=edi,r10d_after_sbb=result,borrow=borrow,sign=sf,jb_taken=bool(borrow),jns_taken=not bool(sf),rdx_at_push=rdx,rax_before_second_cqo=rax,second_cqo_rdx=M if rax&(1<<63) else 0)

def final_ja(bts_carry):
 if bts_carry not in (0,1):raise ValueError('Carry must be zero or one')
 # PUSH known-zero RDX, XADD byte offset4 with R9B=0x36 returns zero into R9B.
 pushed=bytearray(8);old=pushed[4];pushed[4]=(old+0x36)&255;r9=old
 # Later CQO overwrites the intervening DL arithmetic with zero.
 rdx=fixed_flags()['second_cqo_rdx'];borrow32=int(rdx<0x462fd526+bts_carry);rdx=(rdx-0x462fd526-bts_carry)&0xffffffff
 borrow64=int(rdx<r9+borrow32);rdx=(rdx-r9-borrow32)&M;zf=int(rdx==0)
 return dict(r9_after_xadd=r9,rdx=rdx,carry=borrow64,zero=zf,taken=not bool(borrow64 or zf))

SEGMENTS=[(21599620, 73, '7bd8f15e9c94c5a0cbfb67e11b5c55f99198515939718a5b6527cf774938abcb'), (23084515, 6, '314b69d37d5c580226be8a8a83204cb2eaf0f3aea292ec99439af8db9b40d98d'), (21251296, 61, '042c72b2a189595b01f970991b61a17987772b69a9cded02f5903934870e6aed'), (24426736, 49, '825b4e8908af553979b78237684761ab5b9461c943078850deec11936e318c49'), (24375835, 37, '7622833454466e52714a4268014fc92e7b2e770d4ba06de1a4f1efe100658dd6'), (22471511, 124, 'c37c573ba10216089d416836a251062a45fd73949e12b62c75cce89d11890787'), (21617655, 20, 'b50cf58fed713e38f8901a7552deec141492f6a9e211f972d18acaeee1845b6b'), (22254606, 21, '0892c3e6f8a8e5c023915e7c301d33e0520f04362ab8b23d3cd2c76ede8f7fde')]
FRONTIER={'address': 22254624, 'bytes': 'c21800', 'assembly': 'ret    0x18'}
def validate_parts(parts):
 if len(parts)!=len(SEGMENTS) or any(len(p)!=n or hashlib.sha256(p).hexdigest()!=h for p,(_,n,h) in zip(parts,SEGMENTS)):raise ValueError('Changed fixed init guard prefixes')
def capture(jar):
 import zipfile
 from native_init_prologue_ysm_265 import capture as parent_capture
 from native_image_metadata_ysm_265 import SHA,IMAGES
 from native_export_backing_ysm_265 import regions,data_at
 parent=parent_capture(jar)
 with zipfile.ZipFile(jar) as z:b=z.read('META-INF/native/libysm-core.so')
 if hashlib.sha256(b).hexdigest()!=dict(IMAGES)['libysm-core.so']:raise ValueError('Wrong image')
 rs=regions(b);validate_parts([data_at(b,rs,a,n) for a,n,h in SEGMENTS]);flags=fixed_flags();cases=[final_ja(c) for c in (0,1)]
 if not flags['jb_taken'] or not flags['jns_taken'] or flags['rdx_at_push'] or any(not c['taken'] for c in cases):raise ValueError('Guard proof failed')
 return dict(format='kneekura.ysm-native-init-guard-chain.v1',artifact_sha256=SHA,image_sha256=dict(IMAGES)['libysm-core.so'],dependency_prologue_sha256=hashlib.sha256(json.dumps(parent,sort_keys=True).encode()).hexdigest(),segments=[dict(address=a,size=n,sha256=h) for a,n,h in SEGMENTS],flags=flags,branches=[dict(address=0x14995c7,target=0x1603de3,condition='JB',taken=True),dict(address=0x1603de3,target=0x14444e0,condition='JNS',taken=True),dict(address=0x1444517,target=0x174b8f0,condition='JA',taken=True)],ja_both_carry_cases=cases,additional_file_byte_values_needed_for_these_predicates=False,next_frontier=dict(**FRONTIER,destination_resolved=False),assumptions=['Prior conditional DT_INIT candidate is reached under its recorded assumptions','Pinned instructions and normal memory completion without external interference','No assumption is made that decoded byte values or later indirect stores are harmless'],target_executed=False,native_emulator_run=False,initializer_effects_resolved=False,independent_semantic_review='NOT_RUN')
def main():
 import argparse
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--jar',required=True,type=Path);p.add_argument('--out',required=True,type=Path);p.add_argument('--check',action='store_true');a=p.parse_args();r=capture(a.jar)
 if a.check:
  if json.loads(a.out.read_text())!=r:raise SystemExit('Init guard chain mismatch')
 else:a.out.write_text(json.dumps(r,indent=2)+'\n')
 print(json.dumps(dict(status='MATCH' if a.check else 'WRITTEN',additional_taken_predicates=3,next_return=hex(r['next_frontier']['address']),destination_resolved=False)))
if __name__=='__main__':main()
