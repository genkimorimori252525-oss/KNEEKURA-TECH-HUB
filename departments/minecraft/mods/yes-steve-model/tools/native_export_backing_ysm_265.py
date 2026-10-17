#!/usr/bin/env python3
"""Resolve fixed image export file backing and only recognize one direct branch prefix; no execution/unpacking."""
import argparse,hashlib,json,struct,zipfile
from pathlib import Path
from native_image_metadata_ysm_265 import SHA,IMAGES,header

def regions(b):
 if b[:4]==b'\x7fELF':
  h=struct.unpack_from('<HHIQQQIHHHHHH',b,16);out=[]
  for i in range(h[9]):
   p=struct.unpack_from('<IIQQQQQQ',b,h[4]+i*h[8])
   if p[0]==1:out.append(dict(kind='PT_LOAD',index=i,address=p[3],memory_size=p[6],file_offset=p[2],file_size=p[5],flags=p[1]))
  return out
 e=struct.unpack_from('<I',b,60)[0];count=struct.unpack_from('<H',b,e+6)[0];start=e+24+struct.unpack_from('<H',b,e+20)[0];out=[]
 for i in range(count):
  off=start+i*40;vsize,va,size,ptr=struct.unpack_from('<IIII',b,off+8)
  out.append(dict(kind='PE_SECTION',index=i,name=b[off:off+8].rstrip(b'\0').decode('ascii'),address=va,memory_size=max(vsize,size),file_offset=ptr,file_size=size,flags=struct.unpack_from('<I',b,off+36)[0]))
 return out

def backing(rs,address,size):
 if size<=0 or address<0:raise ValueError('Invalid range')
 hits=[r for r in rs if r['address']<=address and address+size<=r['address']+r['memory_size']]
 if len(hits)!=1:raise ValueError('Unmapped or overlapping virtual range')
 r=hits[0];delta=address-r['address'];out={'region':r,'file_backed':delta+size<=r['file_size']}
 if out['file_backed']:out['file_offset']=r['file_offset']+delta
 return out

def data_at(b,rs,addr,size):
 v=backing(rs,addr,size)
 if not v['file_backed']:raise ValueError('Virtual-only range')
 off=v['file_offset']
 if off+size>len(b):raise ValueError('Truncated file')
 return b[off:off+size]

def pe_exports(b,rs):
 e=struct.unpack_from('<I',b,60)[0];rva=struct.unpack_from('<I',b,e+24+112)[0];d=struct.unpack('<IIHHIIIIIII',data_at(b,rs,rva,40));out=[]
 for i in range(d[7]):
  name_rva=struct.unpack('<I',data_at(b,rs,d[9]+4*i,4))[0];s=[]
  for j in range(256):
   c=data_at(b,rs,name_rva+j,1)[0]
   if c==0:break
   s.append(c)
  else:raise ValueError('Unterminated export name')
  ordinal=struct.unpack('<H',data_at(b,rs,d[10]+2*i,2))[0]
  if ordinal>=d[6]:raise ValueError('Invalid export ordinal')
  addr=struct.unpack('<I',data_at(b,rs,d[8]+4*ordinal,4))[0];out.append(dict(name=bytes(s).decode('ascii'),address=addr))
 return out

def direct_branch(machine,code,address):
 if machine==62 and len(code)>=5 and code[0]==0xe9:
  disp=struct.unpack_from('<i',code,1)[0];return dict(instruction='x86-64 JMP rel32',bytes=code[:5].hex(),signed_displacement=disp,target_address=address+5+disp)
 if machine==183 and len(code)>=4:
  word=struct.unpack_from('<I',code)[0]
  if word&0xfc000000==0x14000000:
   imm=word&0x3ffffff
   if imm&(1<<25):imm-=1<<26
   return dict(instruction='A64 B immediate',bytes=code[:4].hex(),signed_displacement=imm*4,target_address=address+imm*4)
 return None

def capture(jar,metadata):
 if hashlib.sha256(jar.read_bytes()).hexdigest()!=SHA:raise ValueError('Wrong JAR')
 if metadata.get('artifact_sha256')!=SHA:raise ValueError('Wrong metadata artifact')
 pins=dict(IMAGES);rows=[]
 if sorted(Path(r['jar_member']).name for r in metadata['images'])!=sorted(pins):raise ValueError('Wrong image set')
 with zipfile.ZipFile(jar) as z:
  for image in metadata['images']:
   member=image['jar_member'];b=z.read(member)
   if hashlib.sha256(b).hexdigest()!=pins[Path(member).name]:raise ValueError('Wrong image')
   if header(b)!=image['header']:raise ValueError('Header mismatch')
   rs=regions(b);syms=image.get('defined_dynamic_symbols') or pe_exports(b,rs);exports=[]
   for s in syms:
    addr=s['address'];size=4 if s['name'].startswith('YSM_') else 8;v=backing(rs,addr,size);row=dict(name=s['name'],address=addr,address_kind='ELF virtual address' if b[:4]==b'\x7fELF' else 'PE RVA',**v)
    if v['file_backed']:
     code=data_at(b,rs,addr,size);row['first_bytes']=code.hex()
     if s['name'].startswith('JNI_'):
      branch=direct_branch(image['header']['machine'],code,addr)
      if branch:branch['target_backing']=backing(rs,branch['target_address'],1)
      row['recognized_first_branch']=branch
    exports.append(row)
   rows.append(dict(jar_member=member,sha256=pins[Path(member).name],exports=exports))
 return dict(format='kneekura.ysm-native-export-backing.v1',artifact_sha256=SHA,metadata_canonical_sha256=hashlib.sha256(json.dumps(metadata,sort_keys=True,separators=(',',':')).encode()).hexdigest(),images=rows,scope='Named export file backing and first direct branch only; no subsequent body decoding, execution, emulation, native payload unpacking or Java/native binding claim',target_executed=False,native_implementations_resolved=False,java_native_bindings_resolved=False,independent_semantic_review='NOT_RUN')
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--jar',required=True);p.add_argument('--out',required=True);p.add_argument('--check',action='store_true');a=p.parse_args();root=Path(__file__).resolve().parent.parent;r=capture(Path(a.jar),json.loads((root/'NATIVE-IMAGE-METADATA-2026-10-17.json').read_text()));out=Path(a.out)
 if a.check:
  if json.loads(out.read_text())!=r:raise SystemExit('Backing mismatch')
 else:out.write_text(json.dumps(r,indent=2)+'\n')
 print(json.dumps({'images':len(r['images']),'status':'MATCH' if a.check else 'WRITTEN','target_executed':False}))
if __name__=='__main__':main()
