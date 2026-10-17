#!/usr/bin/env python3
"""Inventory ACC_NATIVE declarations in the fixed artifact; no native implementation is inspected or executed."""
import argparse,hashlib,json,zipfile
from pathlib import Path
from scan_ysm_265 import parse_class
SHA='25b5e902b96f4c298690208f8b433cbc31737c23f87590354dbd86f00207bc8f'
ANCHORS=['NATIVE-TEXTURE-JAVA-BOUNDARY','LOCATOR-MATRIX-PREPARATION','CLIENT-COMPAT-INITIALIZATION','COMMON-NATIVE-LIFECYCLE','SERVER-MODEL-SYNC-JAVA','CLIENT-MODEL-SYNC-STATE','JAVA-RENDER-BOUNDARY','AUDIO-DECODER-JAVA-BOUNDARY']
def ident(m):return tuple(m[k] for k in ('owner','name','descriptor'))
def inventory(jar,root):
 raw=jar.read_bytes()
 if hashlib.sha256(raw).hexdigest()!=SHA:raise ValueError('Wrong fixed artifact')
 anchors={};files=[]
 for prefix in ANCHORS:
  p=root/(prefix+'-EVIDENCE-2026-10-17.json');b=p.read_bytes();e=json.loads(b)
  if e.get('artifact',{}).get('sha256')!=SHA:raise ValueError('Wrong anchor artifact')
  files.append({'path':p.name,'sha256':hashlib.sha256(b).hexdigest()})
  for m in e['members']:
   if m.get('access',0)&0x100:
    if 'instructions' in m:raise ValueError('Invented native Code snapshot')
    anchors.setdefault(ident(m),[]).append({'evidence':p.name,'access':m['access']})
 rows=[];classes=0
 with zipfile.ZipFile(jar) as z:
  for n in sorted(z.namelist()):
   if not n.endswith('.class'):continue
   classes+=1;b=z.read(n);c=parse_class(b)
   for m in c['methods']:
    if not m['access']&0x100:continue
    row={'owner':n[:-6],'name':m['name'],'descriptor':m['descriptor'],'access':m['access'],'class_sha256':hashlib.sha256(b).hexdigest()}
    hits=anchors.get(ident(row),[])
    if not hits or any(h['access']!=row['access'] for h in hits):raise ValueError('Missing or mismatched anchor')
    row['evidence']=[h['evidence'] for h in hits];rows.append(row)
 if len(rows)!=17 or classes!=955 or len({ident(r) for r in rows})!=17:raise ValueError('Fixed declaration/class inventory changed')
 if set(anchors)!={ident(r) for r in rows}:raise ValueError('Extraneous anchored native declaration')
 return {'format':'kneekura.ysm-native-declaration-inventory.v1','artifact_sha256':SHA,'class_files_scanned':classes,'native_declarations':rows,'native_declaration_count':len(rows),'owner_count':len({r['owner'] for r in rows}),'anchor_files':files,'scope':'ACC_NATIVE declarations in this JAR only; not native exports, callbacks, dynamic binding, external library symbols or implementation coverage','native_implementations_resolved':False,'target_runtime_executed':False,'independent_semantic_review':'NOT_RUN','central_mapping_promoted':False}
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--jar',required=True);p.add_argument('--out',required=True);p.add_argument('--check',action='store_true');a=p.parse_args();root=Path(__file__).resolve().parent.parent;r=inventory(Path(a.jar),root);out=Path(a.out)
 if a.check:
  if json.loads(out.read_text())!=r:raise SystemExit('Inventory mismatch')
 else:out.write_text(json.dumps(r,indent=2)+'\n')
 print(json.dumps({'classes':r['class_files_scanned'],'native_declarations':r['native_declaration_count'],'owners':r['owner_count'],'status':'MATCH' if a.check else 'WRITTEN','native_implementation_coverage':'NOT_ESTABLISHED'}))
if __name__=='__main__':main()
