#!/usr/bin/env python3
"""Pinned DT_INIT scalar and byte-interval proofs; static models, not a native emulator."""
import hashlib,json
from pathlib import Path
from native_candidate_stack_guard_ysm_265 import signed
from native_return_file_candidate_ysm_265 import ror32,bswap32
M=(1<<64)-1

def first_predicate():
 rbp=(-0x953b89a2)&M;bp=(-(rbp&65535))&65535
 return dict(bp=bp,zf=int(bp==0),taken=bp!=0)

def saved_literal_slot():
 # Explicit stack adjustments in the 16 pinned direct-transfer prefixes.
 deltas=[-8,-8,-8,-8,8,16,-8,-8,-8,-8,-8,-8,8,-8,-8,-8,-8,-8,-8,-8,-8,-8,-8]
 q=sum(deltas)
 return dict(entry_rsp_delta=q,read_relative_offset=0x78,original_rsp_offset=q+0x78,value=0x162e9a61)

def second_predicate(saved_r15,load_bias):
 origin=64;stack=bytearray(256)
 def put(off,n,value):stack[origin+off:origin+off+n]=(value&((1<<(n*8))-1)).to_bytes(n,'little')
 def get(off,n):return int.from_bytes(stack[origin+off:origin+off+n],'little')
 put(0x78,4,saved_literal_slot()['value']);put(-8,8,saved_r15);put(-16,8,0x2c82613f)
 sar_input=get(-13,4);sar_carry=(sar_input>>6)&1;put(-13,4,signed(sar_input,32)>>7)
 rcx=0x613f;put(-24,8,rcx);put(-32,8,rcx);rsi=get(-32,8)
 put(24,8,load_bias-sar_carry)
 old=get(-20,1);put(-20,1,rsi);rsi=(rsi&~255)|old
 r11=get(0x78,4);old=get(-10,2);put(-10,2,rcx);rcx=old
 r11=ror32(r11,31);put(-32,8,rsi)
 old=get(-11,2);put(-11,2,old+(rsi&65535));rsi=(rsi&~65535)|old
 r11=(r11+1)&0xffffffff;rsi=(rsi&~65535)|(((rsi&65535)<<6)&65535)
 put(-32+rsi*2-0x17ff7,2,rcx)
 bit=rcx&31;rcx^=1<<bit
 r11=ror32(r11,rcx&31)^0x122f3f1d;r11^=rsi
 put(-32+rcx*2+0xe,8,-get(-32+rcx*2+0xe,8))
 r9=(rcx*9-0xfea66ca)&M;rsi=(r9*4-0x45ee6dc)&M;r11=(rcx+r11+0x5599e684)&0xffffffff
 cf=int(r9+rcx>M);r9=(r9+rcx)&M
 return dict(sar_input=sar_input,sar_carry=sar_carry,rcx=rcx,rsi=rsi,r9=r9,carry=cf,taken=cf==0,r11d_before_bswap=r11,relative_data_pointer=(bswap32(r11)-4)&M,post_shift_stack_store_offset=(rsi+0x44088278)&M)

def third_predicate():
 rdi=0x5ab23ca3*4+0x27b3ab35
 rdi=(rdi&~255)|((signed(rdi&255,8)>>5)&255)
 rdi=(rdi&~65535)|(((rdi&65535)<<12)&65535)
 edi=rdi&0xffffffff;ebx=(-0x7e7caada)&0xffffffff;bit=ebx&31;cf=(edi>>bit)&1
 return dict(edi_before_btc=edi,bit_index=bit,carry=cf,taken=cf==0,edi_after_btc=edi^(1<<bit))

def initial_key(load_bias):
 literal=signed(0xb499e897,32)&M;byte=(literal>>8)&255
 byte=((byte>>6)|(byte<<2))&255;literal=(literal&~0xff00)|(byte<<8)
 edi=literal&0xffffffff;carry=(edi>>(32-20))&1
 relative=bswap32(second_predicate(0,0)['r11d_before_bswap'])
 r11=(load_bias+relative)&M
 return dict(edi_before_shift=edi,shift_count=20,carry=carry,key=(r11-load_bias-carry)&M)

def return_candidate(word):
 if not 0<=word<=0xffffffff:raise ValueError('Word must be uint32')
 state=second_predicate(0,0);key=initial_key(0)['key']
 rbx=(-0x7e7caada)&M;r9=(rbx*5+0x7e0eb925)&M;w=r9&65535;r9=(r9&~65535)|(((w<<15)|(w>>1))&65535)
 eax=(~(word^key))&0xffffffff;eax^=0x34b015f4;eax^=r9&0xffffffff;eax=ror32(eax,3)^0x7f846882
 edi=third_predicate()['edi_after_btc'];setg=int(signed(edi,32)>0);pushed=(edi&~255)|setg
 byte5=(pushed>>40)&255;carry=(byte5>>6)&1
 return dict(data_address=state['relative_data_pointer'],relative_key=key,delta_u32=eax,delta_signed=signed(eax,32),pushed_rdi=pushed,shifted_stack_byte=byte5,adc_carry=carry,target=(0x16b059b+signed(eax,32)+carry)&M)

SEGMENTS=[(22211353, 5, '55607f898fa5db83c6e66d8d59d33c6d8fecc49032530c4b3721c812f5316113'), (22236372, 5, '5d2b4f2851604078e4e12a5b507fb40a96715d01273427d4be37ef09ed399b95'), (22606318, 5, 'c419b330049f05d680ccd120c588a7b63c996a8f1700a6eb78006130c1346f6d'), (23156036, 34, '330340f148da9533c21cdaa97285dafa185d119233377097833c8381f43f913d'), (24279834, 5, 'a757ec31ae5b4042cb506c0e740bfc413e9581386153ee33545391d286dc8f74'), (25374142, 5, '547b9b0e1c71d1a51710abb231c82b5a36da22d9ab083114bdfa2e9dccdc6fcc'), (24819948, 28, '0a4888952aad24d2e56276e2b4cd447950cf0e8eac024a2fff04590f3dfbbf8a'), (24620552, 10, '5470f0874db3c1ff5757a56c607f0ea6259ced0f1b8f2e9d9343fa3862f06691'), (24650151, 15, '73b5ea9c00aea743ff0f3d462d721f72f17d7682270bf30b1003e100f5e5b2df'), (22502330, 15, 'a1e59d7fbe2cb4645ac118780fb773e1c396adec61fdc2a04ab71c0e1fca1234'), (25014183, 13, 'bf25202b2c7f928698d4457f81c6cc1180e9d3f5ff307b7f2205abbcd5ddd4a7'), (23119311, 7, 'aeb076c1ee150041660bce53897e9b5cd101e5218081f5d0db99f71b32d72b96'), (24907853, 13, '941cdb2903a5ccb0cdaa9601afbc5d77db3fd89a33e935440ae050b2b497ab05'), (24479618, 20, 'bd29898c2f7737b99b0a7db063c4ce17f989651cac009fde7444547d1a25772a'), (24999011, 32, 'c6d16793bac6e14be01ccb877b8c17bed37213d07636bf70ba3fc5ad24e7e5ff'), (24432732, 25, '43c99885faf8a8cb70aa38b3ce56d90c32b21914c141931d86a76dc88d75da52'), (23488604, 169, '4d75aa8f72e229f1b95021f5e046b9c843a92bed20310189c975478231a2d605'), (24968286, 27, 'f2f2b9b31e5aac4a9cc68cab6fcf05cb2e08172a0516e0c2dfafd6050943bfab'), (23943577, 49, '0b9dbf219a302b45578c5fdd5a96e0714a0dbe18414fb96bdc9fd04fe00caeb7'), (23790929, 179, 'ba5f9f0d9ed0be90ecce58d4a725e00edeb10a6ce66da9c53f82d3755cc3b0ec'), (23571932, 67, '28d45025980682ce722e97c4394c3dbd8a2f2d80462bba06bd7b9f03b76738e8'), (24209751, 7, 'a80084aa5f3cdde79c2507e606927f9a4f3646906cfc93f4d8a1fbd80a352815'), (21599620, 73, '7bd8f15e9c94c5a0cbfb67e11b5c55f99198515939718a5b6527cf774938abcb')]
def validate_parts(parts):
 if len(parts)!=len(SEGMENTS) or any(len(p)!=n or hashlib.sha256(p).hexdigest()!=h for p,(_,n,h) in zip(parts,SEGMENTS)):raise ValueError('Changed fixed DT_INIT prefixes')

def capture(jar):
 import zipfile
 from native_initializer_inventory_ysm_265 import capture as inventory,rela_records,overlaps
 from native_image_metadata_ysm_265 import SHA,IMAGES
 from native_export_backing_ysm_265 import regions,data_at,backing
 inv=inventory(jar)
 with zipfile.ZipFile(jar) as z:b=z.read('META-INF/native/libysm-core.so')
 if hashlib.sha256(b).hexdigest()!=dict(IMAGES)['libysm-core.so']:raise ValueError('Wrong image')
 rs=regions(b);validate_parts([data_at(b,rs,a,n) for a,n,h in SEGMENTS])
 first=first_predicate();slot=saved_literal_slot();second=second_predicate(0,0);third=third_predicate()
 if slot['original_rsp_offset']!=-8 or not first['taken'] or not second['taken'] or not third['taken']:raise ValueError('Prologue proof failed')
 word=int.from_bytes(data_at(b,rs,second['relative_data_pointer'],4),'little');ret=return_candidate(word)
 d=dict(inv['dynamic_entries']);rel=rela_records(data_at(b,rs,d[7],d[8]))+rela_records(data_at(b,rs,d[23],d[2]))
 return dict(format='kneekura.ysm-native-init-prologue.v1',artifact_sha256=SHA,image_sha256=dict(IMAGES)['libysm-core.so'],entry=inv['dt_init'],segments=[dict(address=a,size=n,sha256=h) for a,n,h in SEGMENTS],first_branch=dict(address=0x174d06f,target=0x166685c,**first),saved_literal=slot,second_branch=dict(address=0x16668ff,target=0x17cfc5e,**second),third_branch=dict(address=0x16b05fe,target=0x167addc,**third),file_word=dict(address=ret['data_address'],value=word,backing=backing(rs,ret['data_address'],4),overlapping_relocations=overlaps(rel,ret['data_address'],4)),initial_key_proof=initial_key(0),first_return_candidate=ret,code_relocation_overlaps=[dict(address=a,size=n,overlaps=overlaps(rel,a,n)) for a,n,h in SEGMENTS if overlaps(rel,a,n)],return_instruction=dict(address=0x171695b,stored_register='RSI',store_offset=0,stack_advance=16),next_frontier=dict(start=ret['target'],conditional_branch=SEGMENTS[-1][0]+SEGMENTS[-1][1]-6,target=0x1603de3,condition_resolved=False),assumptions=['Pinned initial image/code bytes and normal memory completion without external interference','The new stack pointer is derived from the incoming stack pointer and aligned downward; normal stack availability is assumed','The data word at the derived image-relative address retains recorded bytes; initializer-wide invariance remains unproven'],target_executed=False,native_emulator_run=False,scalar_and_byte_interval_models_only=True,initializer_effects_resolved=False,watched_jni_data_immutability_proven=False,independent_semantic_review='NOT_RUN')
def main():
 import argparse
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--jar',required=True,type=Path);p.add_argument('--out',required=True,type=Path);p.add_argument('--check',action='store_true');a=p.parse_args();r=capture(a.jar)
 if a.check:
  if json.loads(a.out.read_text())!=r:raise SystemExit('DT_INIT prologue mismatch')
 else:a.out.write_text(json.dumps(r,indent=2)+'\n')
 print(json.dumps(dict(status='MATCH' if a.check else 'WRITTEN',taken_predicates=3,return_candidate=hex(r['first_return_candidate']['target']),initializer_effects_resolved=False)))
if __name__=='__main__':main()
