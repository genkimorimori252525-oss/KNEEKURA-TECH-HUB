#!/usr/bin/env python3
"""Audit direct writes in fixed initializer prefixes and two-hop import metadata; no execution."""
import argparse,hashlib,json,re,struct,zipfile
from pathlib import Path
from native_export_backing_ysm_265 import regions,data_at
from native_initializer_inventory_ysm_265 import capture as init_capture,rela_records
from native_ghidra_crosscheck_ysm_265 import capture as lift_capture,parse_lift

def rip_slot(code,address):
 if len(code)<6 or code[:2]!=b'\xff\x25':return None
 return address+6+struct.unpack_from('<i',code,2)[0]
def overlap(a,n,b,m):return a<b+m and a+n>b

def classify_write(pcode):
 m=re.match(r'\(ram, 0x([0-9a-f]+), (\d+)\) ',pcode)
 if m:return dict(kind='direct',address=int(m[1],16),size=int(m[2]))
 if ' STORE ' not in pcode:return None
 v=re.findall(r'\(([^,]+), 0x([0-9a-f]+), (\d+)\)',pcode)
 if len(v)!=3:raise ValueError('Malformed STORE pcode')
 if v[1][0]=='const':return dict(kind='direct',address=int(v[1][1],16),size=int(v[2][2]))
 return dict(kind='unresolved',size=int(v[2][2]))

def capture(jar,lift):
 D=Path(__file__).resolve().parent.parent
 cross=lift_capture(jar,lift,D/'NATIVE-GHIDRA-MANIFEST-2026-10-18.tsv',D/'NATIVE-GHIDRA-MEMORY-2026-10-18.tsv')
 original=json.loads((D/'NATIVE-GHIDRA-CROSSCHECK-2026-10-18.json').read_text())
 if cross!=original:raise ValueError('Require the retained fixed 73-range lift')
 parsed=parse_lift(lift.read_text());init=init_capture(jar);writes=[];unresolved=[];prefixes=[]
 for f,ops in parsed['groups']:
  if f[-1]!='NATIVE-INITIALIZER-INVENTORY-2026-10-17':continue
  entry=int(f[0],16);prefixes.append(entry)
  for op in ops:
   for p in parsed['pcode'].get(op[0],[]):
    w=classify_write(p)
    if w is None:continue
    row=dict(entry=entry,instruction=op[0],pcode_sha256=hashlib.sha256(p.encode()).hexdigest(),**w)
    (writes if w['kind']=='direct' else unresolved).append(row)
 with zipfile.ZipFile(jar) as z:b=z.read('META-INF/native/libysm-core.so')
 rs=regions(b);dyn=dict(init['dynamic_entries']);rel=rela_records(data_at(b,rs,dyn[7],dyn[8]))+rela_records(data_at(b,rs,dyn[23],dyn[2]));resolved=[];local=[]
 targets=sorted(set(x['direct_target'] for x in init['first_transfer_prefixes'] if x['direct_target']))
 for target in targets:
  slot=rip_slot(data_at(b,rs,target,6),target)
  if slot is None:local.append(target);continue
  hit=[x for x in rel if x[0]==slot]
  if len(hit)!=1 or hit[0][1]!=8:raise ValueError('Unexpected first-hop relocation')
  trampoline=hit[0][2];second=rip_slot(data_at(b,rs,trampoline,6),trampoline)
  if second is None:raise ValueError('Unexpected second-hop stub')
  h=[x for x in rel if x[0]==second]
  if len(h)!=1 or h[0][1]&0xffffffff!=7:raise ValueError('Unexpected JUMP_SLOT relocation')
  symbol=h[0][1]>>32
  if not 0<symbol<298:raise ValueError('Unexpected dynamic-symbol index')
  name_offset,info,other,section,value,size=struct.unpack('<IBBHQQ',data_at(b,rs,dyn[6]+symbol*24,24))
  if section!=0 or name_offset>=dyn[10]:raise ValueError('Not a named undefined import')
  raw=data_at(b,rs,dyn[5]+name_offset,dyn[10]-name_offset)
  if b'\0' not in raw:raise ValueError('Unterminated symbol name')
  name=raw.split(b'\0',1)[0].decode('ascii')
  resolved.append(dict(original_stub=target,first_slot=slot,relative_addend=trampoline,second_slot=second,symbol_index=symbol,symbol_name=name,prefix_sites=sum(x['direct_target']==target for x in init['first_transfer_prefixes'])))
 string=data_at(b,rs,0x46267,64).split(b'\0')[0].decode('ascii')
 return dict(format='kneekura.ysm-native-initializer-write-audit.v1',artifact_sha256=init['artifact_sha256'],image_sha256=init['image_sha256'],dependency_lift_sha256=cross['lift_sha256'],prefix_count=len(prefixes),direct_write_operations=writes,unresolved_store_operations=unresolved,watched_interval=dict(address=0xd2cd48,size=19),direct_overlaps=[w for w in writes if overlap(w['address'],w['size'],0xd2cd48,19)],resolved_import_chains=resolved,other_direct_targets=local,environment_string=dict(address=0x46267,text=string,caller_prefix=0x2aaae0),scope='Only 46 captured first-transfer prefixes; subsequent blocks, indirect stores and callees remain unresolved',all_initializer_effects_resolved=False,file_state_immutability_proven=False,actual_import_binding_verified=False,target_executed=False,native_emulator_run=False,independent_semantic_review='NOT_RUN')
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--jar',type=Path,required=True);p.add_argument('--lift',type=Path,required=True);p.add_argument('--out',type=Path,required=True);p.add_argument('--check',action='store_true');a=p.parse_args();r=capture(a.jar,a.lift)
 if a.check:
  if json.loads(a.out.read_text())!=r:raise SystemExit('Initializer write audit mismatch')
 else:a.out.write_text(json.dumps(r,indent=2)+'\n')
 print(json.dumps(dict(status='MATCH' if a.check else 'WRITTEN',direct_writes=len(r['direct_write_operations']),unresolved_stores=len(r['unresolved_store_operations']),direct_overlaps=len(r['direct_overlaps']),imports=[x['symbol_name'] for x in r['resolved_import_chains']])))
if __name__=='__main__':main()
