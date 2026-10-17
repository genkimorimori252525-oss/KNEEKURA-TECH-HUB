#!/usr/bin/env python3
"""Closed fixed-JAR direct-reference scan for full-state build and dirty-mark calls, including lambda handles."""
import argparse,copy,hashlib,json,zipfile
from pathlib import Path
from audit_seed_recovery_ysm_265 import parse_bounded,BOUNDDETAILS
SHA='25b5e902b96f4c298690208f8b433cbc31737c23f87590354dbd86f00207bc8f'
P='com/elfmcys/yesstevemodel/'
TARGETS={(P+'oooooooOOoOOoO00OooOo00O','oo0OoO00oOoo000O0000o0oo','()V'),(P+'oooooooOOoOOoO00OooOo00O','Oo0Oo0o00O00Oo0OOoOOoooo','(Lnet/minecraft/server/level/ServerPlayer;Z)Ljava/util/Optional;'),(P+'Ooo0O0000OO0OOO0o0Oo0oOO','Oo0Oo0o00O00Oo0OOoOOoooo','(Lnet/minecraft/server/level/ServerPlayer;Z)L'+P+'O00OO0Oo0O0Oo0O0Ooo0o00O;')}
def capture(jar):
 raw=Path(jar).read_bytes()
 if len(raw)!=63269843 or hashlib.sha256(raw).hexdigest()!=SHA:raise ValueError('Wrong artifact')
 calls=[];members=[];handles=[];count=0
 with zipfile.ZipFile(jar) as z:
  for n in sorted(z.namelist()):
   if not n.endswith('.class'):continue
   count+=1
   methods=parse_bounded(z.read(n),True)
   for i,b in enumerate(BOUNDDETAILS.get(n[:-6],{}).get('bootstrap_methods',[])):
    for arg in b.get('arguments',[]):
     r=arg.get('reference',{})
     if tuple(r.get(k) for k in ('owner','name','descriptor')) in TARGETS:
      users=[{'caller':{k:m[k] for k in ['owner','name','descriptor']},'instruction':op} for m in methods for op in m.get('instructions',[]) if op['opcode']=='0xba' and op.get('reference',{}).get('bootstrap_index')==i]
      handles.append({'owner':n[:-6],'bootstrap_index':i,'bootstrap':b,'users':users})
   for m in methods:
    matches=[op for op in m.get('instructions',[]) if tuple(op.get('reference',{}).get(k) for k in ('owner','name','descriptor')) in TARGETS and op['opcode'] in ['0xb6','0xb7','0xb8','0xb9']]
    if matches:
     members.append(m)
     for op in matches:calls.append({'caller':{k:m[k] for k in ['owner','name','descriptor']},'instruction':op})
 return {'artifact_sha256':SHA,'class_count':count,'targets':[list(x) for x in sorted(TARGETS)],'method_handle_targets':handles,'calls':calls,'caller_methods':members,'external_or_reflective_closure':False,'runtime_executed':False}
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--jar',required=True);p.add_argument('--evidence',required=True);p.add_argument('--out');p.add_argument('--capture',action='store_true');a=p.parse_args();d=capture(a.jar)
 if a.capture:Path(a.evidence).write_text(json.dumps(d,indent=2)+'\n');return
 e=json.loads(Path(a.evidence).read_text());checks=[{'check':'exact-complete-call-scan','pass':e==d},{'check':'955-classes','pass':d['class_count']==955}];neg=[]
 for name,mut in [('missing-method-handle',lambda x:x['method_handle_targets'].pop()),('missing-call',lambda x:x['calls'].pop()),('missing-caller-body',lambda x:x['caller_methods'].pop()),('missing-target',lambda x:x['targets'].pop()),('invented-global-closure',lambda x:x.update(external_or_reflective_closure=True)),('wrong-artifact',lambda x:x.update(artifact_sha256='0'*64))]:
  y=copy.deepcopy(e);mut(y);neg.append({'control':name,'rejected':y!=d})
 r={'checks':checks,'negative_controls':neg,'failures':[c for c in checks if not c['pass']],'independent_review':'NOT_RUN','runtime_executed':False};Path(a.out).write_text(json.dumps(r,indent=2)+'\n');print(json.dumps({'handles':len(d['method_handle_targets']),'calls':len(d['calls']),'caller_methods':len(d['caller_methods']),'checks':len(checks),'negative_controls':len(neg),'failures':len(r['failures'])}))
 if r['failures'] or any(not n['rejected'] for n in neg):raise SystemExit(1)
if __name__=='__main__':main()
