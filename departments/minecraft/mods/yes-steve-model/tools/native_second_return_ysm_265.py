#!/usr/bin/env python3
"""Fixed second stack-rewritten return, with an explicitly conditional file-state destination."""
from native_return_file_candidate_ysm_265 import ror32,bswap32
from native_candidate_stack_guard_ysm_265 import known_stack_inputs,signed

def return_registers(si_entry):
 mask64=(1<<64)-1
 rsi=((si_entry+1)<<14)&mask64
 rsi=ror32(rsi,24)
 rsi=(rsi&~255)|(((rsi&255)<<6)&255)
 r10d=(0xba3d8b24^0x35bc6e94)&0xab13c900
 rsi=(rsi&~255)|(r10d&255)
 final=(rsi&~65535)|((~rsi)&65535)
 return dict(r10d_masked=r10d,r10b_for_exchange=r10d&255,rsi_before_not_word=rsi,rsi_final=final,store_offset=final*2-0x4501fffe)

def second_delta(word,key):
 mask32=(1<<32)-1;mask64=(1<<64)-1
 cx0=(0x541c1c25*5+0x6ebfbc28)&mask64
 cl=cx0&255
 r11=known_stack_inputs()['eax_before_ax_shift']
 x=((word^key)+r11-0x2c4edbe3)&mask32
 x=ror32(bswap32(x),3)
 x=(x+cl*2+0x17aad749)&mask32
 cx1=cx0|(1<<(cx0%64))
 cx2=(cx1+signed(0x9886e9a4,32))&mask64
 r9=cl*3+0x3fb98fa2
 carry=int(cx2+r9>mask64)
 return dict(initial_cl=cl,r11_for_word_transform=r11,delta_u32=x,delta_signed=signed(x,32),adc_carry=carry)

import hashlib
SEGMENTS=[(0x12c463e,13,'e69607d590c4a0359c6cb454e620df83d265df2c6cb66181ae07610a294c3980'),(0xf9cc3c,69,'c5ba46617ad712389f5f1c9637a1e3d3cbbb62aa5578e1b893dc212243cf0a26'),(0x1060bbd,137,'e8b66fda0032d563d67312ed6ee64b46cd278212d563438214c0355aff119fb0')]
def validate_parts(parts):
 if len(parts)!=len(SEGMENTS) or any(len(p)!=n or hashlib.sha256(p).hexdigest()!=h for p,(_,n,h) in zip(parts,SEGMENTS)):raise ValueError('Changed fixed second-return prefixes')

def capture(jar):
 import json,zipfile
 from native_image_metadata_ysm_265 import SHA,IMAGES
 from native_export_backing_ysm_265 import regions,data_at,backing
 from native_candidate_stack_guard_ysm_265 import capture as parent_capture
 parent=parent_capture(jar)
 with zipfile.ZipFile(jar) as z:b=z.read('META-INF/native/libysm-core.so')
 if hashlib.sha256(b).hexdigest()!=dict(IMAGES)['libysm-core.so']:raise ValueError('Wrong image')
 rs=regions(b);parts=[data_at(b,rs,a,n) for a,n,_ in SEGMENTS];validate_parts(parts)
 regs=return_registers(0x89)
 if regs['store_offset']!=0:raise ValueError('Return store is not stack top')
 word_bytes=data_at(b,rs,0xd2cd4c,4);word=int.from_bytes(word_bytes,'little')
 key=0xd2cd48^0x2040f8;delta=second_delta(word,key)
 candidate=(0x12c3a51+delta['delta_signed']+delta['adc_carry'])&((1<<64)-1)
 if parts[-1][-3:]!=bytes.fromhex('c20800'):raise ValueError('Unexpected return encoding')
 return dict(format='kneekura.ysm-native-second-return.v1',artifact_sha256=SHA,image_sha256=dict(IMAGES)['libysm-core.so'],dependency_guard_sha256=hashlib.sha256(json.dumps(parent,sort_keys=True).encode()).hexdigest(),segments=[dict(address=a,size=n,sha256=h) for a,n,h in SEGMENTS],register_proof=regs,return_instruction=dict(address=0x1060c43,immediate=8,pop_bytes=8,total_stack_advance=16,stored_register='RDI',store_offset=0),symbolic_destination='RDI = load_bias + 0x12c3a51 + sign_extend_32(decoded_second_word) + carry',file_state=dict(word_address=0xd2cd4c,word_hex=word_bytes.hex(),key=key,delta=delta,candidate_relative_address=candidate,backing=backing(rs,candidate,1)),assumptions=['Both earlier file-state data words at 0xd2cd48 and 0xd2cd4c retain the recorded file bytes','The preceding fixed candidate and untaken guard are reached under their recorded assumptions','Unmodified instructions, normal memory completion and no external interference','RDI remains unchanged between its ADC at 0x12c3ac6 and the final stack store'],second_word_relocation_overlap_checked=False,target_executed=False,native_machine_emulator_run=False,runtime_reachability_verified=False,native_implementations_resolved=False,java_native_bindings_resolved=False,independent_semantic_review='NOT_RUN')

def main():
 import argparse,json
 from pathlib import Path
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--jar',required=True);p.add_argument('--out',required=True);p.add_argument('--check',action='store_true');a=p.parse_args();r=capture(Path(a.jar));out=Path(a.out)
 if a.check:
  if json.loads(out.read_text())!=r:raise SystemExit('Second-return mismatch')
 else:out.write_text(json.dumps(r,indent=2)+'\n')
 print(json.dumps({'status':'MATCH' if a.check else 'WRITTEN','candidate':hex(r['file_state']['candidate_relative_address']),'runtime_verified':False}))
if __name__=='__main__':main()
