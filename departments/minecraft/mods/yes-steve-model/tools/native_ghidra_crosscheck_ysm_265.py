#!/usr/bin/env python3
"""Validate external static Ghidra lift against fixed artifact and GNU decoder; never execute target."""
import argparse,hashlib,json,re,subprocess,tempfile,zipfile
from pathlib import Path
from native_image_metadata_ysm_265 import SHA,IMAGES
from native_export_backing_ysm_265 import regions,data_at

def digest(b):return hashlib.sha256(b).hexdigest()
def parse_lift(text):
 groups=[];ops=[];pcode={};loads=[];data={};program=None;complete=False
 for line in text.splitlines():
  if complete:raise ValueError('Content after completion')
  f=line.split('\t');kind=f[0]
  if kind=='PROGRAM':
   if program is not None or len(f)!=4 or f[2]!='x86:LE:64:default' or int(f[3],16)!=0:raise ValueError('Wrong/duplicate program identity')
   program=f[1:]
  elif kind=='INS':
   if len(f)!=5:raise ValueError('Malformed instruction')
   a,n=int(f[1],16),int(f[2]);raw=bytes.fromhex(f[3])
   if n<=0 or len(raw)!=n or (ops and a!=ops[-1][0]+ops[-1][1]):raise ValueError('Instruction byte/length/address mismatch')
   ops.append((a,n,f[3],f[4]))
  elif kind=='PCODE':
   if len(f)!=3 or not ops or int(f[1],16)!=ops[-1][0]:raise ValueError('Unanchored pcode')
   pcode.setdefault(int(f[1],16),[]).append(f[2])
  elif kind=='RANGE':
   if len(f)!=6 or not ops:raise ValueError('Malformed range')
   a,n,count=int(f[1],16),int(f[2]),int(f[4]);raw=b''.join(bytes.fromhex(x[2]) for x in ops)
   if a!=ops[0][0] or n!=len(raw) or count!=len(ops) or digest(raw)!=f[3]:raise ValueError('Range coverage/hash mismatch')
   groups.append((f[1:],ops));ops=[]
  elif kind=='LOAD_MATCH':
   if len(f)!=5:raise ValueError('Malformed load record')
   loads.append(f[1:])
  elif kind=='DATA':
   if len(f)!=3 or f[1] in data:raise ValueError('Malformed/duplicate data record')
   data[f[1]]=f[2]
  elif kind in ('BLOCK','REG'):pass
  elif kind=='COMPLETE':
   if len(f)!=5 or f[3:]!=['target_executed=false','automatic_analysis=false'] or ops or int(f[1])!=len(groups) or int(f[2])!=sum(len(o) for _,o in groups):raise ValueError('Incomplete/count-mismatched lift')
   complete=True
  else:raise ValueError('Unknown lift record')
 if not complete or program is None:raise ValueError('Incomplete lift')
 return dict(groups=groups,pcode=pcode,loads=loads,data=data,program=program)

def capture(jar,lift,manifest,memory):
 if digest(jar.read_bytes())!=SHA:raise ValueError('Wrong JAR')
 with zipfile.ZipFile(jar) as z:b=z.read('META-INF/native/libysm-core.so')
 if digest(b)!=dict(IMAGES)['libysm-core.so']:raise ValueError('Wrong image')
 rs=regions(b);r=parse_lift(lift.read_text());expected=[l.split('\t') for l in manifest.read_text().splitlines() if l and not l.startswith('#')]
 if [(f[0],f[1],f[2],f[4]) for f,o in r['groups']]!=[tuple(x) for x in expected]:raise ValueError('Manifest coverage mismatch')
 memory_rows=[l.split('\t') for l in memory.read_text().splitlines() if l]
 if r['loads']!=memory_rows:raise ValueError('Memory coverage mismatch')
 for a,n,h,label in memory_rows:
  if digest(data_at(b,rs,int(a,16),int(n)))!=h:raise ValueError('Wrong PT_LOAD hash')
 reports=[];unique={}
 with tempfile.TemporaryDirectory() as td:
  tmp=Path(td)/'range.bin'
  for f,ghops in r['groups']:
   a,n=int(f[0],16),int(f[1]);code=data_at(b,rs,a,n)
   if digest(code)!=f[2]:raise ValueError('Wrong range bytes')
   tmp.write_bytes(code);output=subprocess.check_output(['objdump','-D','-b','binary','-m','i386:x86-64','-M','intel','--insn-width=16',f'--adjust-vma={a}',str(tmp)],text=True);gnu=[]
   for line in output.splitlines():
    m=re.match(r'\s*([0-9a-f]+):\s*((?:[0-9a-f]{2} )+)\s*\t(.*)',line)
    if m:raw=bytes.fromhex(m[2]);gnu.append((int(m[1],16),len(raw),raw.hex(),m[3]))
   if [x[:3] for x in ghops]!=[x[:3] for x in gnu]:raise ValueError(f'Decoder disagreement at {a:x}')
   for op in ghops:
    if op[0] in unique and unique[op[0]][:3]!=op[:3]:raise ValueError('Overlapping instruction disagreement')
    unique[op[0]]=op
   reports.append(dict(address=a,size=n,sha256=f[2],instruction_occurrences=len(ghops),address_length_bytes_match=True))
 for a in (0xd2cd48,0xd2cd4c):
  if r['data'].get(f'{a:x}')!=data_at(b,rs,a,4).hex():raise ValueError('Wrong imported data word')
 selected={hex(a):digest('\n'.join(r['pcode'].get(a,[])).encode()) for a in (0xee9ad7,0xee9ada,0x1060c43,0x10d1780,0x10d179a)}
 if any(not r['pcode'].get(a) for a in (0xee9ad7,0xee9ada,0x1060c43,0x10d1780,0x10d179a)):raise ValueError('Missing selected pcode')
 return dict(format='kneekura.ysm-native-ghidra-crosscheck.v1',artifact_sha256=SHA,image_sha256=dict(IMAGES)['libysm-core.so'],ghidra_release='12.1.4',ghidra_archive_sha256='ddac49f903da9d5bac833e5cc79395098b9c33cfd3279be5f31bd00387d2d4db',gnu_version=subprocess.check_output(['objdump','--version'],text=True).splitlines()[0],manifest_sha256=digest(manifest.read_bytes()),memory_manifest_sha256=digest(memory.read_bytes()),lift_sha256=digest(lift.read_bytes()),script_sha256=digest((Path(__file__).parent/'ghidra/YsmScopedLift.java').read_bytes()),range_count=len(reports),instruction_occurrences=sum(x['instruction_occurrences'] for x in reports),unique_instruction_addresses=len(unique),ranges=reports,full_file_backed_load_segments_matched=len(memory_rows),imported_data_words=r['data'],selected_pcode_sha256=selected,automatic_analysis=False,relocations_applied=False,external_libraries_loaded=False,target_executed=False,native_emulator_run=False,scope='Exact imported file-backed memory and selected decoder boundaries/bytes; not whole-function recovery or semantic equivalence',independent_semantic_review='NOT_RUN',native_bindings_resolved=False,runtime_data_immutability_proven=False)

def main():
 p=argparse.ArgumentParser(description=__doc__)
 for name in ['jar','lift','manifest','memory','out']:p.add_argument('--'+name,required=True,type=Path)
 p.add_argument('--check',action='store_true');a=p.parse_args();r=capture(a.jar,a.lift,a.manifest,a.memory)
 if a.check:
  if json.loads(a.out.read_text())!=r:raise SystemExit('Crosscheck receipt mismatch')
 else:a.out.write_text(json.dumps(r,indent=2)+'\n')
 print(json.dumps(dict(status='MATCH' if a.check else 'WRITTEN',ranges=r['range_count'],instruction_occurrences=r['instruction_occurrences'],memory_segments=r['full_file_backed_load_segments_matched'])))
if __name__=='__main__':main()
