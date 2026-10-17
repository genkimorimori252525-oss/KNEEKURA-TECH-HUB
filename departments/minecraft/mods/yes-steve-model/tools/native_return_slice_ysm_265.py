#!/usr/bin/env python3
"""Fixed register/stack-address constant slice at one RET frontier; not a native emulator."""
import argparse,hashlib,json,struct,zipfile
from pathlib import Path
from native_image_metadata_ysm_265 import SHA,IMAGES
from native_export_backing_ysm_265 import regions,data_at
from native_load_flag_chain_ysm_265 import capture as flags_capture
SEGMENTS=[(0x10bf959,30,'9f43224331dae68099adb5845f11860c2c8728f856412d7df204252837125f36'),(0x12de5ac,64,'e8c486f6312581a33b1cb94e0a5da9a5fd5979047f6b0d1e4fe269df4e0be998'),(0x11a3a95,74,'967855e68d2114ccb3ba1c50a61a42d839d2f9a7dab7f27bf128e6720c09125b'),(0xfa14d0,22,'26a8ae1ac185e6277ee5c3bbec6ee30165581bf2adf787efceb330a331f7b617')]
def validate_parts(parts):
 if len(parts)!=len(SEGMENTS) or any(len(p)!=n or hashlib.sha256(p).hexdigest()!=sha for p,(_,n,sha) in zip(parts,SEGMENTS)):raise ValueError('Changed fixed return-slice bytes')
def register_slice(initial_r11d,initial_r10d,bit_index):
 r10_after_btc=(initial_r10d^(1<<(bit_index%32)))&0xffffffff
 r11_after_swap=r10_after_btc;r10_after_swap=initial_r11d&0xffffffff
 cx=r10_after_swap&255;shr_carry=((r10_after_swap&0xffff)>>13)&1
 r11_after_adc=(r11_after_swap&0xffff0000)|(((r11_after_swap&0xffff)+cx+shr_carry)&0xffff)
 final=(~r11_after_adc)&0xffffffff
 return dict(r10_after_btc=r10_after_btc,r10_after_swap=r10_after_swap,r11_after_swap=r11_after_swap,cx=cx,shr14_carry=shr_carry,r11_after_adc_word=r11_after_adc,r11_after_not_dword=final)
def symbolic_return(load_bias,decoded_esi,relative_anchor=0x10bf959):
 x=decoded_esi&0xffffffff;signed=x-(1<<32) if x&0x80000000 else x
 return (load_bias+relative_anchor+signed)&((1<<64)-1)
def capture(jar):
 parent=flags_capture(jar)
 with zipfile.ZipFile(jar) as z:b=z.read('META-INF/native/libysm-core.so')
 if hashlib.sha256(b).hexdigest()!=dict(IMAGES)['libysm-core.so']:raise ValueError('Wrong image')
 rs=regions(b);parts=[data_at(b,rs,a,n) for a,n,_ in SEGMENTS];validate_parts(parts)
 tail=parts[0];s=register_slice(struct.unpack_from('<I',tail,2)[0],struct.unpack_from('<I',tail,8)[0],tail[16]);disp=struct.unpack_from('<i',parts[3],17)[0];effective=s['r11_after_not_dword']+disp
 anchor=SEGMENTS[0][0]+24+struct.unpack_from('<i',tail,20)[0]
 callee=SEGMENTS[2][0]+len(parts[2])+struct.unpack_from('<i',parts[2],70)[0]
 if effective!=0 or anchor!=0x10bf959 or callee!=0xfa14d0:raise ValueError('Unexpected return-slice result')
 return dict(format='kneekura.ysm-native-return-slice.v1',artifact_sha256=SHA,image_sha256=dict(IMAGES)['libysm-core.so'],dependency_flag_chain_sha256=hashlib.sha256(json.dumps(parent,sort_keys=True).encode()).hexdigest(),segments=[dict(address=a,size=n,sha256=sha) for a,n,sha in SEGMENTS],register_constants=s,return_store=dict(instruction_address=0xfa14dd,index_register='r11',signed_displacement=disp,effective_offset_from_current_rsp=effective),stack_transition=dict(pop_r10_address=0xfa14d8,nearest_call_return_removed=True,add_rdi_rsi_address=0xfa14da,ret_address=0xfa14e5),return_target_expression='(load_bias + 0x10bf959 + sign_extend_32(decoded_ESI)) mod 2^64',relative_anchor=anchor,return_expression_resolved_under_assumptions=True,decoded_esi_value_resolved=False,concrete_return_address_resolved=False,assumptions=parent['assumptions']+['The explicit RSI/RDI/R11 slices remain within the captured unmodified prefixes through RET','No interference changes the stack after the final store and before RET'],target_executed=False,native_emulation_run=False,constant_and_address_analysis_only=True,native_implementations_resolved=False,java_native_bindings_resolved=False,independent_semantic_review='NOT_RUN')
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--jar',required=True);p.add_argument('--out',required=True);p.add_argument('--check',action='store_true');a=p.parse_args();r=capture(Path(a.jar));out=Path(a.out)
 if a.check:
  if json.loads(out.read_text())!=r:raise SystemExit('Return-slice mismatch')
 else:out.write_text(json.dumps(r,indent=2)+'\n')
 print(json.dumps({'status':'MATCH' if a.check else 'WRITTEN','return_store_offset':r['return_store']['effective_offset_from_current_rsp'],'concrete_return_address_resolved':False,'target_executed':False}))
if __name__=='__main__':main()
