#!/usr/bin/env python3
"""Fixed 21-byte local constant/flag proof; Python arithmetic only, never executes native code."""
import argparse,hashlib,json,struct,zipfile
from pathlib import Path
from native_image_metadata_ysm_265 import SHA,IMAGES
from native_export_backing_ysm_265 import regions,data_at,backing
START=0x129ea79
EXPECTED=bytes.fromhex('6890cb14ad66ff4c24034c897424000f8ab6571100')
def parity_after_dec(imm32):
 signed=imm32 if imm32<0x80000000 else imm32-(1<<32)
 raw=(signed&((1<<64)-1)).to_bytes(8,'little');before=int.from_bytes(raw[3:5],'little');after=(before-1)&0xffff;low=after&255
 return dict(pushed_u64_hex=raw[::-1].hex(),word_before=before,word_after=after,low_byte=low,low_byte_set_bits=low.bit_count(),parity_flag=(low.bit_count()%2)==0)
def prove(code):
 if code!=EXPECTED:raise ValueError('Fixed instruction sequence differs; no proof applied')
 imm=struct.unpack_from('<I',code,1)[0];p=parity_after_dec(imm);target=START+len(code)+struct.unpack_from('<i',code,17)[0]
 if not p['parity_flag'] or target!=0x13b4244:raise ValueError('Unexpected proof result')
 return dict(sequence_start=START,sequence_length=len(code),sequence_sha256=hashlib.sha256(code).hexdigest(),push_immediate_u32=imm,stack_word_byte_offset=3,**p,mov_preserves_flags=True,conditional_instruction='JP rel32',branch_address=START+15,branch_taken_under_assumptions=True,target_address=target,fallthrough_address=START+len(code))
def capture(jar):
 if hashlib.sha256(jar.read_bytes()).hexdigest()!=SHA:raise ValueError('Wrong artifact')
 with zipfile.ZipFile(jar) as z:b=z.read('META-INF/native/libysm-core.so')
 if hashlib.sha256(b).hexdigest()!=dict(IMAGES)['libysm-core.so']:raise ValueError('Wrong image')
 rs=regions(b);r=prove(data_at(b,rs,START,len(EXPECTED)));r['target_file_backing']=backing(rs,r['target_address'],1)
 return dict(format='kneekura.ysm-native-load-parity-proof.v1',artifact_sha256=SHA,image_sha256=dict(IMAGES)['libysm-core.so'],proof=r,assumptions=['Unmodified fixed bytes are entered at the sequence start in 64-bit x86 mode','The PUSH/DEC/MOV memory operations complete normally on the current stack','No external interference changes stack bytes or flags during this sequence'],proof_scope='One local constant parity predicate only; no runtime reachability or JNI method binding proof',target_executed=False,native_emulation_run=False,constant_arithmetic_only=True,native_implementations_resolved=False,independent_semantic_review='NOT_RUN')
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--jar',required=True);p.add_argument('--out',required=True);p.add_argument('--check',action='store_true');a=p.parse_args();r=capture(Path(a.jar));out=Path(a.out)
 if a.check:
  if json.loads(out.read_text())!=r:raise SystemExit('Proof mismatch')
 else:out.write_text(json.dumps(r,indent=2)+'\n')
 print(json.dumps({'status':'MATCH' if a.check else 'WRITTEN','branch_taken_under_assumptions':r['proof']['branch_taken_under_assumptions'],'target_executed':False}))
if __name__=='__main__':main()
