#!/usr/bin/env python3
"""Static stack accounting and file-state candidate for one computed RET; no target execution or unpacking."""
import argparse,collections,hashlib,json,re,subprocess,tempfile,zipfile
from pathlib import Path
from native_image_metadata_ysm_265 import SHA,IMAGES
from native_export_backing_ysm_265 import regions,data_at,backing
from native_return_slice_ysm_265 import capture as return_capture
MASK=(1<<32)-1
# Stack delta events through the EBX load at 0x10bf8ba. Q is entry RSP.
STACK_EVENTS=[('entry_push_r12',-8),('call_1189f87',-8),('push_flags',-8),('copy_flags_push',-8),('restore_flags_pop',8),('lea_rsp_plus_16',16),('call_129ea6d',-8),('push_constant',-8),('push_flags',-8),('pop_stack_operand',8),('push_r15',-8),('push_ad_constant',-8),('push_be_constant',-8),('push_rsi',-8),('call_f28339',-8),('call_11f977a',-8),('push_r13',-8),('push_r8',-8),('push_rdx',-8),('push_rcx',-8),('push_rbp',-8),('call_10bf89a',-8),('push_r10',-8),('push_rdi',-8)]
def ror32(x,n):
 n%=32;x&=MASK
 return ((x>>n)|(x<<((32-n)%32)))&MASK

def bswap32(x):return int.from_bytes((x&MASK).to_bytes(4,'little'),'big')
def rsi_before_exchange():
 x=0xcd171f81;x=(x&~255)|((x-1)&255);x=(x&~255)|((x-0x22)&255);x=(x&~0xffff)|((x<<13)&0xffff);return (x<<(0xd8&31))&MASK

def relative_word_address(seed=0x8f9ba402):
 x=ror32(seed,1);x=(-x)&MASK;x=bswap32(x);return (-x)&MASK

def decode_offset(word,key):
 x=word^key;x=(x-0xf62a1a38)&MASK;x=ror32(x,3);x^=0x47b30ba1;x^=3;x=bswap32(x);return (x+4-0x7e0b3727)&MASK

def capture(jar):
 parent=return_capture(jar)
 with zipfile.ZipFile(jar) as z:b=z.read('META-INF/native/libysm-core.so')
 if hashlib.sha256(b).hexdigest()!=dict(IMAGES)['libysm-core.so']:raise ValueError('Wrong image')
 rs=regions(b);delta=sum(n for _,n in STACK_EVENTS);before=rsi_before_exchange();after=0xc000;slot=delta+after*2-0x17f80
 if (delta,before,slot)!=(-136,0,-8):raise ValueError('Stack accounting mismatch')
 key=relative_word_address();raw=data_at(b,rs,key,4);word=int.from_bytes(raw,'little');decoded=decode_offset(word,key);signed=decoded-(1<<32) if decoded&0x80000000 else decoded;target=0x10bf959+signed
 if (key,word,decoded,target)!=(0xd2cd48,0xdc51ec52,0x2040f8,0x12c3a51):raise ValueError('Fixed file-state result changed')
 with tempfile.TemporaryDirectory() as td:
  p=Path(td)/'libysm-core.so';p.write_bytes(b);out=subprocess.check_output(['readelf','-rDW',str(p)],text=True)
 reloc=[]
 for line in out.splitlines():
  m=re.match(r'\s*([0-9a-fA-F]+)\s+([0-9a-fA-F]+)\s+(R_X86_64_\S+)',line)
  if m:reloc.append((int(m.group(1),16),m.group(3)))
 allowed={'R_X86_64_RELATIVE','R_X86_64_JUMP_SLOT','R_X86_64_GLOB_DAT','R_X86_64_64','R_X86_64_DTPMOD64'}
 if len(reloc)!=9114 or set(t for _,t in reloc)!=allowed:raise ValueError('Unexpected relocation table scope')
 overlaps=[dict(address=a,type=t) for a,t in reloc if a<key+4 and key<a+8]
 if overlaps:raise ValueError('Listed relocation overlaps candidate word')
 return dict(format='kneekura.ysm-native-return-file-candidate.v1',artifact_sha256=SHA,image_sha256=dict(IMAGES)['libysm-core.so'],dependency_return_slice_sha256=hashlib.sha256(json.dumps(parent,sort_keys=True).encode()).hexdigest(),stack_accounting=dict(entry_rsp_symbol='Q',events=[dict(event=e,delta=n) for e,n in STACK_EVENTS],rsp_at_ebx_load_relative_to_Q=delta,rsi_before_exchange=before,rsi_after_exchange=after,seed_load_slot_relative_to_Q=slot,seed_slot_value_low32=0x8f9ba402),word=dict(relative_address=key,file_backing=backing(rs,key,4),file_bytes=raw.hex(),u32=word),decode_constants=dict(key=key,rotation_count=3,post_exchange_ecx=3,setge_r10b=1,decoded_esi=decoded,signed_offset=signed),candidate=dict(relative_address=target,file_backing=backing(rs,target,1),runtime_expression='load_bias + 0x12c3a51',runtime_destination_verified=False),relocation_check=dict(command='readelf -rDW',rows=len(reloc),types=dict(collections.Counter(t for _,t in reloc)),eight_byte_write_overlaps=overlaps,scope='Listed dynamic RELA/JMPREL metadata only; no runtime init-write proof'),assumptions=parent['assumptions']+['The earlier saved constant at Q-8 is not modified before the captured load','The addressed data word retains the exact file bytes when read; native initializers or runtime writes are not proven absent'],target_executed=False,native_emulation_run=False,static_constant_and_stack_accounting_only=True,concrete_runtime_return_verified=False,native_implementations_resolved=False,java_native_bindings_resolved=False,independent_semantic_review='NOT_RUN')
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--jar',required=True);p.add_argument('--out',required=True);p.add_argument('--check',action='store_true');a=p.parse_args();r=capture(Path(a.jar));out=Path(a.out)
 if a.check:
  if json.loads(out.read_text())!=r:raise SystemExit('File candidate mismatch')
 else:out.write_text(json.dumps(r,indent=2)+'\n')
 print(json.dumps({'status':'MATCH' if a.check else 'WRITTEN','file_state_candidate':hex(r['candidate']['relative_address']),'runtime_verified':False}))
if __name__=='__main__':main()
