#!/usr/bin/env python3
"""Fixed scalar/stack-interval continuation proofs; no native execution or emulator."""
import hashlib,json
from pathlib import Path
from native_candidate_stack_guard_ysm_265 import signed,known_stack_inputs
from native_return_file_candidate_ysm_265 import ror32,bswap32
M64=(1<<64)-1

def rol8(x,n):
 n%=8;return ((x<<n)|(x>>(8-n)))&255

def fixed_inputs():
 cx0=(0x541c1c25*5+0x6ebfbc28)&M64;cx1=cx0|(1<<(cx0%64));cx2=(cx1+signed(0x9886e9a4,32))&M64
 r9=(cx1&255)*3+0x3fb98fa2;cx3=(cx2+r9)&M64
 r10=(known_stack_inputs()['eax_before_ax_shift']<<(cx2&31))&0xffffffff
 r10=(r10&~255)|(((r10&255)<<(cx2&31))&255);carry=(r10>>11)&1
 r9=(r9&~255)|(((r9&255)-1)&255);n=cx3&63;r9=((r9>>n)|(r9<<(64-n)))&M64
 r9^=0xc2a4;r9=(-r9)&M64;r9=(r9&~65535)|((r9&65535)&0xfcb9);r9=(r9<<59)&M64
 return dict(rcx_before_byte_load=cx3,r10d_before_word_shift=r10,shl_r10w_carry=carry,r9_after_shift=r9)

def third_candidate(cl_byte,dl_byte,word):
 if not 0<=cl_byte<=255 or not 0<=dl_byte<=255 or not 0<=word<=0xffffffff:raise ValueError('Invalid data width')
 fixed=fixed_inputs();key=0xf28db0^0xffc25fec
 cl=cl_byte^(key&255);cl=(cl-0x8f)&255;cl=(-cl)&255;cl=(cl-0x21-fixed['shl_r10w_carry'])&255;cl=rol8(cl,7);cl=(cl+1)&255
 key^=cl
 dl=dl_byte^(key&255);dl=(dl-0xaf)&255;dl=rol8(dl,1);dl=(dl-1)&255;dl^=0x83^0x24;dl=(-dl)&255;key^=dl
 x=((word^key)+0xffffa0b6-0x2c4e7d89)&0xffffffff;x=ror32(bswap32(x),3);x=(x+0xffff+0x17a9d90c)&0xffffffff
 return dict(cl_decoded=cl,dl_decoded=dl,key=key,delta_u32=x,delta_signed=signed(x,32),target=(0xee9a3d+signed(x,32))&M64)

def fourth_candidate(byte_value,word,third):
 if not 0<=byte_value<=255 or not 0<=word<=0xffffffff:raise ValueError('Invalid data width')
 key=third['key']^third['delta_u32'];x=byte_value^(key&255);x=(x-255)&255;x=rol8(x,1);x=(x+1)&255;x=rol8(x,1);key^=x
 delta=((word^key)+0xa2bbce07+0x30f55526)&0xffffffff;delta=ror32(bswap32(delta),3);delta=(delta+0x17aad90b)&0xffffffff
 return dict(key=key,delta_u32=delta,delta_signed=signed(delta,32),target=(third['target']+signed(delta,32))&M64)

def stack_jump(prior_write_offset,load_bias):
 if not 0<=prior_write_offset<=255:raise ValueError('Prior write offset must be a byte')
 # Byte-interval model relative to RSP before two CALLs and PUSH zero.
 # Earlier unknown eight-byte store starts at nonnegative offset; return slot is [-8,-1].
 origin=24;stack=bytearray(288)
 stack[origin+prior_write_offset:origin+prior_write_offset+8]=b'\xff'*8
 outer=(load_bias+0x12db690)&M64;inner=(load_bias+0x108c505)&M64
 stack[16:24]=outer.to_bytes(8,'little');stack[8:16]=inner.to_bytes(8,'little');stack[:8]=bytes(8)
 stack[8:16]=(0x0c1129aa).to_bytes(8,'little')
 returned=int.from_bytes(stack[16:24],'little')
 # AND ESI with a memory dword has ESI=0 and clears CF; XCHG preserves CF.
 return dict(saved_outer_return=returned,carry=0,target=(returned+signed(0xffc2372f,32))&M64)

def parity_guard():
 cx=(0xce07-1)&65535;cx>>=2;cx=(cx&~255)|rol8(cx&255,2) # ROR CL,6
 ax=(cx+0x3b4)&65535;pf=int((ax&255).bit_count()%2==0)
 return dict(cx_before_exchange=cx,bit_test_si_zero_carry=0,ax_after_adc=ax,parity_flag=pf,taken=not bool(pf))

SEGMENTS=[(16161888, 73, '24a816009b91e8e84dff992ae3460864cbbf3cb95efce2b05a16c5a3ce22fd37'), (19988144, 10, '475ddcdd3c2a4d02d3b492b9fee85aa37b9110958bb6495d709de68c2f670ae7'), (17460252, 9, 'aa4784f5e89ae058e6c4aa2373338a42c7977dffa3845ad7f1b311448fa5cadf'), (15847166, 9, '56193ea668147e17a016f0c93bfd0777efd482ed9c9eee0148f70b0af959a011'), (19773042, 30, '5baa6f19ba375fe33a91deceaf7b8599a75c68e7a95d7a9d0b5924902b329424'), (17351933, 8, 'a105e21a7784844b9f4715e72660bba6015e960d91698106f25efaf8eb399f3e'), (15761391, 75, 'b81e89d65a542cdfbcf693f7fd6b527c3ecfa2236e0dd3969f276111c744bd6c'), (15723967, 97, 'c4e8fd750f06a5e1d6f11a617ffbdc9871db1c47775ae300ee39456f583453b1'), (15842229, 36, '56a85d340606a13e5f582ee435c0cc94846625ad8d6eb141adadd48125ae47fb'), (17828269, 20, '43503ae28355d4c07fd593d1ac94e491fc81b74ac2b420d5b462d16fcfe3aaca')]
def validate_parts(parts):
 if len(parts)!=len(SEGMENTS) or any(len(p)!=n or hashlib.sha256(p).hexdigest()!=h for p,(_,n,h) in zip(parts,SEGMENTS)):raise ValueError('Changed continuation prefixes')

def capture(jar):
 import zipfile
 from native_post_return_guards_ysm_265 import capture as parent_capture
 from native_image_metadata_ysm_265 import SHA,IMAGES
 from native_export_backing_ysm_265 import regions,data_at,backing
 parent=parent_capture(jar)
 with zipfile.ZipFile(jar) as z:b=z.read('META-INF/native/libysm-core.so')
 if hashlib.sha256(b).hexdigest()!=dict(IMAGES)['libysm-core.so']:raise ValueError('Wrong image')
 rs=regions(b);validate_parts([data_at(b,rs,a,n) for a,n,h in SEGMENTS]);data=data_at(b,rs,0xd2cd50,11)
 third=third_candidate(data[0],data[1],int.from_bytes(data[2:6],'little'));fourth=fourth_candidate(data[6],int.from_bytes(data[7:11],'little'),third)
 fixed=fixed_inputs();guard=parity_guard()
 if fixed['r9_after_shift'] or not guard['taken']:raise ValueError('Fixed scalar proof failed')
 if any(stack_jump(x,0)['target']!=0xefedbf for x in range(256)):raise ValueError('Stack alias proof failed')
 return dict(format='kneekura.ysm-native-continuation.v1',artifact_sha256=SHA,image_sha256=dict(IMAGES)['libysm-core.so'],dependency_post_return_sha256=hashlib.sha256(json.dumps(parent,sort_keys=True).encode()).hexdigest(),segments=[dict(address=a,size=n,sha256=h) for a,n,h in SEGMENTS],additional_file_data=dict(address=0xd2cd50,bytes=data.hex(),size=len(data)),fixed_inputs=fixed,third_file_candidate=third,fourth_file_candidate=fourth,computed_jumps=[dict(address=0x130feb8,target=0xf69ca9+0x13cf73,basis='POP nearest CALL return, then ADD fixed displacement'),dict(address=0xf08037,target=stack_jump(0,0)['target'],basis='XCHG saved outer return, then ADC with zero carry')],stack_alias_offsets_checked=256,parity_guard=dict(address=0xf1bbd3,target=0x11009ad,**guard),fourth_return=dict(address=0x11009be,stored_register='RDI',store_offset=0,stack_advance=16),candidate_backing=[backing(rs,t,1) for t in (third['target'],fourth['target'])],assumptions=['All preceding candidate assumptions remain in force','Additional file bytes at 0xd2cd50 through 0xd2cd5a retain recorded values','All fixed memory accesses complete normally; no external interference or modified instructions','Unknown byte at 0xd2cd5b affects other state but is not used to claim a concrete successor beyond this fourth return'],target_executed=False,native_emulator_run=False,scalar_and_byte_interval_models_only=True,runtime_reachability_verified=False,initializer_effects_resolved=False,independent_semantic_review='NOT_RUN',native_bindings_resolved=False)

def main():
 import argparse
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--jar',type=Path,required=True);p.add_argument('--out',type=Path,required=True);p.add_argument('--check',action='store_true');a=p.parse_args();r=capture(a.jar)
 if a.check:
  if json.loads(a.out.read_text())!=r:raise SystemExit('Continuation mismatch')
 else:a.out.write_text(json.dumps(r,indent=2)+'\n')
 print(json.dumps(dict(status='MATCH' if a.check else 'WRITTEN',third=hex(r['third_file_candidate']['target']),fourth=hex(r['fourth_file_candidate']['target']),runtime_verified=False)))
if __name__=='__main__':main()
