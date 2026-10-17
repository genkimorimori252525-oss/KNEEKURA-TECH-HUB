#!/usr/bin/env python3
"""Read fixed native-image headers/symbol metadata with installed binutils; never load or execute target images."""
import argparse,hashlib,json,re,struct,subprocess,tempfile,zipfile
from pathlib import Path
SHA='25b5e902b96f4c298690208f8b433cbc31737c23f87590354dbd86f00207bc8f'
IMAGES=[('libysm-core.so','15d0379718c5a293fc2f36fe17f2f95d5a031b8d5564f06355e08640f22b4c22'),('libysm-core-android.so','41251b0367926efe11c5397845b06c412141e5772869dd32cdd4ea41b6c931c8'),('ysm-core.dll','f895618d58efc89996374548d0b808a42199e967a03f16c2768e3112c3afce4d')]
def header(b):
 if b[:6]==b'\x7fELF\x02\x01':
  h=struct.unpack_from('<HHIQQQIHHHHHH',b,16)
  return dict(format='ELF64 little-endian',type=h[0],machine=h[1],entry_address=h[3],program_header_offset=h[4],section_header_offset=h[5],program_header_count=h[9],section_header_count=h[11],section_name_index=h[12])
 if b[:2]==b'MZ':
  off=struct.unpack_from('<I',b,60)[0]
  if b[off:off+4]!=b'PE\0\0':raise ValueError('Bad PE signature')
  machine,count,timestamp,_,_,optlen,flags=struct.unpack_from('<HHIIIHH',b,off+4);o=off+24;magic=struct.unpack_from('<H',b,o)[0]
  if magic!=0x20b:raise ValueError('Not PE32+')
  return dict(format='PE32+',machine=machine,section_count=count,coff_timestamp=timestamp,characteristics=flags,optional_header_size=optlen,entry_rva=struct.unpack_from('<I',b,o+16)[0],image_base=struct.unpack_from('<Q',b,o+24)[0])
 raise ValueError('Unsupported fixed image header')
def run(*args):
 p=subprocess.run(args,check=True,capture_output=True,text=True);return p.stdout,p.stderr

def capture(jar):
 if hashlib.sha256(jar.read_bytes()).hexdigest()!=SHA:raise ValueError('Wrong JAR')
 rows=[]
 with zipfile.ZipFile(jar) as z,tempfile.TemporaryDirectory() as td:
  for name,sha in IMAGES:
   member='META-INF/native/'+name;b=z.read(member)
   if hashlib.sha256(b).hexdigest()!=sha:raise ValueError('Wrong image hash')
   p=Path(td)/name;p.write_bytes(b);row=dict(jar_member=member,size=len(b),sha256=sha,header=header(b))
   if name.endswith('.so'):
    symbols,err=run('readelf','-DsW',str(p));dynamic,derr=run('readelf','-dW',str(p));exports=[];count=0
    for line in symbols.splitlines():
     m=re.match(r'\s*(\d+):\s+(\S+)\s+(\d+)\s+(\S+)\s+(\S+)\s+(\S+)\s+(\S+)\s+(.*)',line)
     if not m:continue
     count+=1
     if m.group(7)!='UND' and m.group(8):exports.append(dict(index=int(m.group(1)),address=int(m.group(2),16),size=int(m.group(3)),type=m.group(4),binding=m.group(5),visibility=m.group(6),reported_section_index=m.group(7),name=m.group(8)))
    row.update(dynamic_symbol_rows=count,defined_dynamic_symbols=exports,needed_libraries=re.findall(r'\(NEEDED\).*?\[(.*?)\]',dynamic),soname=re.findall(r'\(SONAME\).*?\[(.*?)\]',dynamic),tool_diagnostics=(err+derr).replace(str(p),name))
   else:
    output,err=run('objdump','-p',str(p));named=output.split('[Ordinal/Name Pointer] Table',1)[1].split('PE File Base Relocations',1)[0];exports=[]
    for line in named.splitlines():
     m=re.match(r'\s*\[\s*(\d+)\]\s+\+base\[\s*(\d+)\]\s+([0-9a-fA-F]+)\s+(\S+)',line)
     if m:exports.append(dict(index=int(m.group(1)),ordinal=int(m.group(2)),hint=int(m.group(3),16),name=m.group(4)))
    row.update(named_exports=exports,imported_dlls=re.findall(r'DLL Name:\s*(\S+)',output),tool_diagnostics=err.replace(str(p),name))
   if sorted(x['name'] for x in row.get('defined_dynamic_symbols',row.get('named_exports',[])))!=['JNI_OnLoad','JNI_OnUnload','YSM_FORGE_1200_PRODUCTION']:raise ValueError('Unexpected export inventory')
   rows.append(row)
 return dict(format='kneekura.ysm-native-image-metadata.v1',artifact_sha256=SHA,images=rows,tools={x:run(x,'--version')[0].splitlines()[0] for x in ['readelf','objdump']},scope='File headers and dynamic/named exports only; no loader, disassembly, native payload unpacking, emulation, decryption or native execution',native_implementations_resolved=False,java_native_bindings_resolved=False,independent_semantic_review='NOT_RUN',central_mapping_promoted=False)
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--jar',required=True);p.add_argument('--out',required=True);p.add_argument('--check',action='store_true');a=p.parse_args();r=capture(Path(a.jar));out=Path(a.out)
 if a.check:
  if json.loads(out.read_text())!=r:raise SystemExit('Metadata/tool version mismatch')
 else:out.write_text(json.dumps(r,indent=2)+'\n')
 print(json.dumps({'images':len(r['images']),'status':'MATCH' if a.check else 'WRITTEN','target_executed':False}))
if __name__=='__main__':main()
