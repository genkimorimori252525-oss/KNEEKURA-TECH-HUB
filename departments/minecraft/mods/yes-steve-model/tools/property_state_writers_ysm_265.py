#!/usr/bin/env python3
"""Inventory exact-JAR direct writes to PlayerStateTracker scalar fields; static only."""
import argparse,copy,hashlib,json,zipfile
from pathlib import Path
from audit_seed_recovery_ysm_265 import parse_bounded
SHA='25b5e902b96f4c298690208f8b433cbc31737c23f87590354dbd86f00207bc8f'
OWNER='com/elfmcys/yesstevemodel/ooOO000o0O0OOOoO0Oo0o0Oo'
def capture(jar):
 raw=Path(jar).read_bytes()
 if len(raw)!=63269843 or hashlib.sha256(raw).hexdigest()!=SHA:raise ValueError('Wrong artifact')
 writes=[];members=[];calls=[];count=0
 with zipfile.ZipFile(jar) as z:
  for n in sorted(z.namelist()):
   if not n.endswith('.class'):continue
   count+=1
   for m in parse_bounded(z.read(n),True):
    matches=[op for op in m.get('instructions',[]) if op['opcode']=='0xb5' and op.get('reference',{}).get('owner')==OWNER and op['reference']['descriptor'] in ['Z','I','F']]
    for op in m.get('instructions',[]):
     ref=op.get('reference',{})
     if op['opcode'] in ['0xb6','0xb7','0xb8','0xb9'] and ref.get('owner')==OWNER and ref.get('descriptor')=='(Lcom/elfmcys/yesstevemodel/O00OO0Oo0O0Oo0O0Ooo0o00O;)V':calls.append({'caller':{k:m[k] for k in ['owner','name','descriptor']},'instruction':op})
    if matches:
     members.append(m)
     for op in matches:writes.append({'writer':{k:m[k] for k in ['owner','name','descriptor']},'instruction':op})
 return {'artifact_sha256':SHA,'class_count':count,'target_owner':OWNER,'target_field_descriptors':['Z','I','F'],'property_apply_calls':calls,'writes':writes,'writer_methods':members,'external_reflection_native_closure':False,'runtime_executed':False}
def main():
 p=argparse.ArgumentParser(description=__doc__)
 for k in ['jar','evidence']:p.add_argument('--'+k,required=True)
 p.add_argument('--out');p.add_argument('--capture',action='store_true');a=p.parse_args();d=capture(a.jar)
 if a.capture:Path(a.evidence).write_text(json.dumps(d,indent=2)+'\n');return
 e=json.loads(Path(a.evidence).read_text());checks=[{'check':'complete-exact-direct-writes','pass':d==e},{'check':'955-classes','pass':d['class_count']==955}];neg=[]
 for name,mut in [('missing-apply-call',lambda x:x['property_apply_calls'].pop()),('missing-write',lambda x:x['writes'].pop()),('missing-writer-body',lambda x:x['writer_methods'].pop()),('wrong-target',lambda x:x.update(target_owner='wrong')),('invented-native-closure',lambda x:x.update(external_reflection_native_closure=True)),('wrong-artifact',lambda x:x.update(artifact_sha256='0'*64))]:
  y=copy.deepcopy(e);mut(y);neg.append({'control':name,'rejected':y!=d})
 r={'checks':checks,'negative_controls':neg,'failures':[c for c in checks if not c['pass']],'independent_semantic_review':'NOT_RUN','runtime_executed':False,'central_mapping_promoted':False}
 Path(a.out).write_text(json.dumps(r,indent=2)+'\n');print(json.dumps({'apply_calls':len(d['property_apply_calls']),'writes':len(d['writes']),'writer_methods':len(d['writer_methods']),'checks':len(checks),'negative_controls':len(neg),'failures':len(r['failures'])}))
 if r['failures'] or any(not n['rejected'] for n in neg):raise SystemExit(1)
if __name__=='__main__':main()
