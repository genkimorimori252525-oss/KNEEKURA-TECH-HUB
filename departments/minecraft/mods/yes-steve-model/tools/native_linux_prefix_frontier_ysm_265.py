#!/usr/bin/env python3
"""Fixed-image first-transfer prefixes, following only immediate CALL/JMP edges until a frontier; no execution."""
import argparse,hashlib,json,re,struct,subprocess,tempfile,zipfile
from pathlib import Path
from native_export_backing_ysm_265 import regions,data_at,backing
from native_image_metadata_ysm_265 import SHA,IMAGES
SEEDS={'JNI_OnLoad':0x121fe24,'JNI_OnUnload':0x10e09d2}
def parse_prefix(output,start,code):
 ops=[];expected=start
 for line in output.splitlines():
  m=re.match(r'\s*([0-9a-f]+):\s*((?:[0-9a-f]{2} )+)\s*\t(.*)',line)
  if not m:continue
  addr=int(m.group(1),16);raw=bytes.fromhex(m.group(2));asm=m.group(3).strip();mn=asm.split()[0]
  if addr!=expected or code[addr-start:addr-start+len(raw)]!=raw:raise ValueError('Disassembly byte/address mismatch')
  expected+=len(raw);ops.append(dict(address=addr,bytes=raw.hex(),assembly=asm))
  if mn.startswith(('j','ret','loop')) or mn in ['call','ud2','int','int3','syscall','sysenter','sysret','hlt','(bad)','.byte']:
   return ops
 raise ValueError('No first-transfer frontier inside fixed window')
def direct_target(op):
 match=re.fullmatch(r'(call|jmp)\s+(0x[0-9a-f]+)',op['assembly'])
 if not match:return None
 raw=bytes.fromhex(op['bytes'])
 if len(raw)!=5 or raw[0]!={'call':0xe8,'jmp':0xe9}[match.group(1)]:raise ValueError('Unsupported direct transfer encoding')
 target=op['address']+5+struct.unpack_from('<i',raw,1)[0]
 if target!=int(match.group(2),16):raise ValueError('Disassembler target disagreement')
 return target

def capture(jar):
 if hashlib.sha256(jar.read_bytes()).hexdigest()!=SHA:raise ValueError('Wrong JAR')
 with zipfile.ZipFile(jar) as z:b=z.read('META-INF/native/libysm-core.so')
 if hashlib.sha256(b).hexdigest()!=dict(IMAGES)['libysm-core.so']:raise ValueError('Wrong image')
 rs=regions(b);chains=[]
 with tempfile.TemporaryDirectory() as td:
  p=Path(td)/'prefix.bin'
  for name,seed in SEEDS.items():
   address=seed;seen=set();blocks=[]
   for depth in range(16):
    if address in seen:raise ValueError('Cycle before frontier')
    seen.add(address);code=data_at(b,rs,address,256);p.write_bytes(code)
    out=subprocess.check_output(['objdump','-D','-b','binary','-m','i386:x86-64','-M','intel','--insn-width=16','--adjust-vma='+str(address),str(p)],text=True)
    ops=parse_prefix(out,address,code);last=ops[-1];target=direct_target(last);size=last['address']+len(bytes.fromhex(last['bytes']))-address
    block=dict(start_address=address,file_offset=backing(rs,address,size)['file_offset'],instruction_count=len(ops),prefix_byte_count=size,prefix_sha256=hashlib.sha256(code[:size]).hexdigest(),first_transfer=last,followed_direct_target=target)
    blocks.append(block)
    if target is None:break
    address=target
   else:raise ValueError('Prefix-depth bound exhausted, not completed')
   chains.append(dict(entry=name,seed_address=seed,blocks=blocks,stop_reason='FIRST_NON_DIRECT_CALL_JUMP_TRANSFER',conditional_choice_resolved=False,call_return_continuations_followed=False))
 return dict(format='kneekura.ysm-native-linux-prefix-frontier.v1',artifact_sha256=SHA,image_sha256=dict(IMAGES)['libysm-core.so'],objdump_version=subprocess.check_output(['objdump','--version'],text=True).splitlines()[0],chains=chains,scope='First-transfer prefixes only; not a whole call graph, function boundary recovery or runtime reachability proof',target_executed=False,emulation_run=False,java_native_bindings_resolved=False,native_implementations_resolved=False,independent_semantic_review='NOT_RUN')
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--jar',required=True);p.add_argument('--out',required=True);p.add_argument('--check',action='store_true');a=p.parse_args();r=capture(Path(a.jar));out=Path(a.out)
 if a.check:
  if json.loads(out.read_text())!=r:raise SystemExit('Frontier mismatch')
 else:out.write_text(json.dumps(r,indent=2)+'\n')
 print(json.dumps({'chains':len(r['chains']),'blocks':[len(c['blocks']) for c in r['chains']],'status':'MATCH' if a.check else 'WRITTEN','target_executed':False}))
if __name__=='__main__':main()
