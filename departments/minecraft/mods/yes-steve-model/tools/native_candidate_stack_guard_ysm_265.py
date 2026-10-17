#!/usr/bin/env python3
"""Fixed candidate-prefix constant/stack proof; no target execution."""
def signed(value,width):
 value&=(1<<width)-1
 return value-(1<<width) if value&(1<<(width-1)) else value

def known_stack_inputs():
 mask32=(1<<32)-1;mask64=(1<<64)-1
 cx0=(0x541c1c25*5+0x6ebfbc28)&mask64
 r11=signed(cx0&255,8)&mask32
 r11=(r11&~65535)|((signed(r11&65535,16)>>1)&65535)
 r11=(r11&~255)|(-(r11&255)&255)
 eax_before=signed(r11&65535,16)&mask32
 cx1=cx0|(1<<(cx0%64))
 cx2=(cx1+signed(0x9886e9a4,32))&mask64
 r10d=(eax_before<<(cx2&31))&mask32
 r10b=((r10d&255)<<(cx2&31))&255
 r9=(cx1&255)*3+0x3fb98fa2
 dec_byte=((r9&255)-1)&255
 ror_byte=((r10b>>1)|((r10b&1)<<7))&255
 sf=(dec_byte>>7)&1;zf=dec_byte==0;of=((ror_byte>>7)^(ror_byte>>6))&1
 setg=int(not zf and sf==of)
 ax=((eax_before&65535)<<9)&65535
 ax=(ax&0xff00)|setg
 dx=0xffff if ax&0x8000 else 0
 eax_after=signed(ax,16)&mask32
 rax_before_cbw=(eax_after-dx)&mask64
 # MOVZX EDX plus only 16/8-bit updates leave its upper bits zero.
 rdx_at_store=(dx&~255)|((dx&255)&(rax_before_cbw&255))
 rax_after_cbw=(rax_before_cbw&~65535)|(signed(rax_before_cbw&255,8)&65535)
 return dict(eax_before_ax_shift=eax_before,dec_r9b_result=dec_byte,ror_r10b_result=ror_byte,setg_result=setg,ax_before_cwd=ax,dx_after_cwd=dx,rax_before_cbw=rax_before_cbw,rax_after_cbw=rax_after_cbw,rdx_at_zero_store=rdx_at_store)

import hashlib
SEGMENTS=[(0x12c3a51,207,'6ecb584c49329a0e33a0e4c53e947d1e7e49e4042fb8d0cb6f40d60a675d76b2'),(0x12c4601,61,'9681f378beff3ac8b1ebbcbd55b959f5b30c2c17d75ad35c87cd3513f485b91f')]
def validate_parts(parts):
 if len(parts)!=len(SEGMENTS) or any(len(p)!=n or hashlib.sha256(p).hexdigest()!=h for p,(_,n,h) in zip(parts,SEGMENTS)):raise ValueError('Changed fixed stack-guard prefixes')

def stack_shift_word(cl,r10w,saved_value,stored_u64):
 if not 0<=cl<=255:raise ValueError('CL must be one byte')
 stack=bytearray(b'\xaa'*272)
 stack[:8]=(stored_u64&((1<<64)-1)).to_bytes(8,'little')
 offset=cl+8
 stack[offset:offset+8]=(saved_value&((1<<64)-1)).to_bytes(8,'little')
 stack[1:3]=(r10w&65535).to_bytes(2,'little')
 word=int.from_bytes(stack[6:8],'little')
 return dict(unknown_store_offset=offset,shift_word=word,carry_after_shr15=(word>>14)&1)

def capture(jar):
 import json,struct,zipfile
 from native_image_metadata_ysm_265 import SHA,IMAGES
 from native_export_backing_ysm_265 import regions,data_at,backing
 from native_return_file_candidate_ysm_265 import capture as parent_capture
 parent=parent_capture(jar)
 with zipfile.ZipFile(jar) as z:b=z.read('META-INF/native/libysm-core.so')
 if hashlib.sha256(b).hexdigest()!=dict(IMAGES)['libysm-core.so']:raise ValueError('Wrong image')
 rs=regions(b);parts=[data_at(b,rs,a,n) for a,n,_ in SEGMENTS];validate_parts(parts)
 known=known_stack_inputs()
 if known['rax_after_cbw']!=1 or known['rdx_at_zero_store']!=0:raise ValueError('Stack-input proof failed')
 cases=[stack_shift_word(cl,0xffff,(1<<64)-1,known['rdx_at_zero_store']) for cl in range(256)]
 if any(c['shift_word'] or c['carry_after_shr15'] for c in cases):raise ValueError('Guard not proven across CL domain')
 call=SEGMENTS[0][0]+len(parts[0])+struct.unpack_from('<i',parts[0],len(parts[0])-4)[0]
 fallthrough=SEGMENTS[1][0]+len(parts[1]);taken=fallthrough+struct.unpack_from('<i',parts[1],len(parts[1])-4)[0]
 if call!=0x12c4601 or taken!=0x1186a8d or fallthrough!=0x12c463e:raise ValueError('Unexpected fixed edge')
 return dict(format='kneekura.ysm-native-candidate-stack-guard.v1',artifact_sha256=SHA,image_sha256=dict(IMAGES)['libysm-core.so'],dependency_candidate_sha256=hashlib.sha256(json.dumps(parent,sort_keys=True).encode()).hexdigest(),segments=[dict(address=a,size=n,sha256=h) for a,n,h in SEGMENTS],known_inputs=known,stack_intervals=dict(zero_store=[0,7],unknown_store_start_range=[8,263],word_exchange=[1,2],shift_word=[6,7],shift_word_value=0),all_256_cl_values_checked=True,local_loaded_word_and_byte_values_required=False,branch=dict(address=0x12c4638,instruction='JB',carry_flag=0,taken_under_assumptions=False,fallthrough=fallthrough,taken_target=taken,fallthrough_backing=backing(rs,fallthrough,1)),assumptions=['Unmodified fixed candidate prefix is entered at its start in x86-64 mode','The captured memory operations complete normally and no external interference changes bytes/flags','Reachability of this candidate from the earlier JNI path still depends on the separately recorded file-state assumption'],target_executed=False,native_machine_emulator_run=False,scalar_and_byte_interval_model_only=True,runtime_reachability_verified=False,native_implementations_resolved=False,java_native_bindings_resolved=False,independent_semantic_review='NOT_RUN')

def main():
 import argparse,json
 from pathlib import Path
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--jar',required=True);p.add_argument('--out',required=True);p.add_argument('--check',action='store_true');a=p.parse_args();r=capture(Path(a.jar));out=Path(a.out)
 if a.check:
  if json.loads(out.read_text())!=r:raise SystemExit('Candidate stack-guard mismatch')
 else:out.write_text(json.dumps(r,indent=2)+'\n')
 print(json.dumps({'status':'MATCH' if a.check else 'WRITTEN','branch_taken':False,'fallthrough':hex(r['branch']['fallthrough']),'runtime_verified':False}))
if __name__=='__main__':main()
