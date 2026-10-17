#!/usr/bin/env python3
"""Fixed ELF64 initializer and relocation inventory; never loads the target image."""
import struct,hashlib,json
from pathlib import Path

def dynamic_records(raw):
 if len(raw)%16:raise ValueError('Truncated dynamic records')
 out=[]
 for off in range(0,len(raw),16):
  tag,value=struct.unpack_from('<qQ',raw,off)
  if tag==0:return out
  out.append((tag,value))
 raise ValueError('Unterminated dynamic records')
def rela_records(raw):
 if len(raw)%24:raise ValueError('Truncated RELA records')
 return [struct.unpack_from('<QQq',raw,off) for off in range(0,len(raw),24)]
def array_targets(address,raw,records):
 if len(raw)%8:raise ValueError('Truncated initializer array')
 out=[]
 for i in range(0,len(raw),8):
  slot=address+i;hits=[r for r in records if r[0]==slot]
  if len(hits)!=1 or hits[0][1]!=8:raise ValueError('Expected one symbol-zero R_X86_64_RELATIVE per initializer slot')
  out.append(dict(slot=slot,raw_value=struct.unpack_from('<Q',raw,i)[0],relative_target=hits[0][2]))
 return out

def overlaps(records,address,size):
 if size<=0:raise ValueError('Invalid target interval')
 out=[]
 for off,info,addend in records:
  typ=info&0xffffffff
  if typ not in (1,6,7,8,16):raise ValueError('Unsupported relocation width')
  if off<address+size and off+8>address:out.append((off,info,addend))
 return out

def prefix_summary(output,address,code):
 from native_linux_prefix_frontier_ysm_265 import parse_prefix,direct_target
 ops=parse_prefix(output,address,code);last=ops[-1];size=last['address']+len(bytes.fromhex(last['bytes']))-address
 return dict(address=address,instruction_count=len(ops),prefix_byte_count=size,prefix_sha256=hashlib.sha256(code[:size]).hexdigest(),first_transfer=last,direct_target=direct_target(last),full_function_recovered=False)

def capture(jar):
 import zipfile,collections,tempfile,subprocess
 from native_image_metadata_ysm_265 import SHA,IMAGES,header
 from native_export_backing_ysm_265 import regions,data_at,backing
 if hashlib.sha256(jar.read_bytes()).hexdigest()!=SHA:raise ValueError('Wrong JAR')
 with zipfile.ZipFile(jar) as z:b=z.read('META-INF/native/libysm-core.so')
 if hashlib.sha256(b).hexdigest()!=dict(IMAGES)['libysm-core.so']:raise ValueError('Wrong native image')
 h=header(b);rs=regions(b);ph=[]
 for i in range(h['program_header_count']):
  p=struct.unpack_from('<IIQQQQQQ',b,h['program_header_offset']+i*56)
  if p[0]==2:ph.append(p)
 if len(ph)!=1:raise ValueError('Expected one PT_DYNAMIC')
 p=ph[0];records=dynamic_records(b[p[2]:p[2]+p[5]])
 def one(tag):
  vals=[v for t,v in records if t==tag]
  if len(vals)!=1:raise ValueError(f'Missing/duplicate dynamic tag {tag}')
  return vals[0]
 if any(t in (17,18,19,35,36,37) for t,_ in records):raise ValueError('Unsupported additional relocation table')
 if one(9)!=24 or one(20)!=7:raise ValueError('Not fixed RELA layout')
 rela=rela_records(data_at(b,rs,one(7),one(8)));plt=rela_records(data_at(b,rs,one(23),one(2)));allrows=rela+plt
 arrays=[]
 for name,tag,sizetag in [('INIT_ARRAY',25,27),('FINI_ARRAY',26,28)]:
  address,size=one(tag),one(sizetag);raw=data_at(b,rs,address,size);entries=array_targets(address,raw,allrows)
  for e in entries:e['target_backing']=backing(rs,e['relative_target'],1)
  arrays.append(dict(name=name,address=address,byte_size=size,raw_sha256=hashlib.sha256(raw).hexdigest(),entries=entries))
 prefixes=[]
 with tempfile.TemporaryDirectory() as td:
  tmp=Path(td)/'prefix.bin'
  for address in [one(12)]+[e['relative_target'] for e in arrays[0]['entries']]:
   code=data_at(b,rs,address,256);tmp.write_bytes(code)
   output=subprocess.check_output(['objdump','-D','-b','binary','-m','i386:x86-64','-M','intel','--insn-width=16','--adjust-vma='+str(address),str(tmp)],text=True)
   prefixes.append(prefix_summary(output,address,code))
 data_checks=[dict(address=a,size=4,file_hex=data_at(b,rs,a,4).hex(),overlapping_relocations=overlaps(allrows,a,4)) for a in (0xd2cd48,0xd2cd4c)]
 return dict(format='kneekura.ysm-native-initializer-inventory.v1',artifact_sha256=SHA,image_sha256=dict(IMAGES)['libysm-core.so'],dynamic_entries=records,dt_init=one(12),dt_fini=one(13),arrays=arrays,first_transfer_prefixes=prefixes,objdump_version=subprocess.check_output(['objdump','--version'],text=True).splitlines()[0],rela_count=len(rela),plt_rela_count=len(plt),relocation_type_counts=dict(sorted(collections.Counter(str(i&0xffffffff) for _,i,_ in allrows).items())),data_word_checks=data_checks,scope='ELF metadata, known-width relocation intervals and one first-transfer prefix per init entry; full initializer bodies and their memory effects remain unresolved',constructor_effects_resolved=False,file_state_immutability_proven=False,target_executed=False,native_machine_emulator_run=False,independent_semantic_review='NOT_RUN')
def main():
 import argparse
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--jar',required=True);p.add_argument('--out',required=True);p.add_argument('--check',action='store_true');a=p.parse_args();r=capture(Path(a.jar));out=Path(a.out)
 if a.check:
  # JSON serializes tuples as lists.
  if json.loads(out.read_text())!=json.loads(json.dumps(r)):raise SystemExit('Initializer inventory mismatch')
 else:out.write_text(json.dumps(r,indent=2)+'\n')
 print(json.dumps(dict(status='MATCH' if a.check else 'WRITTEN',init_array_entries=len(r['arrays'][0]['entries']),data_word_relocation_overlaps=sum(len(x['overlapping_relocations']) for x in r['data_word_checks']),constructor_effects_resolved=False)))
if __name__=='__main__':main()
