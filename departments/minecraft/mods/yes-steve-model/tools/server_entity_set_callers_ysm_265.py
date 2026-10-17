#!/usr/bin/env python3
"""Fixed-JAR server-model entity-set getter calls and raw-array field access; no runtime/global closure."""
import argparse,copy,hashlib,json,zipfile
from pathlib import Path
from audit_seed_recovery_ysm_265 import parse_bounded,BOUNDDETAILS
from validate_member_targets_ysm_265 import declaration_index,validate_targets
SHA='25b5e902b96f4c298690208f8b433cbc31737c23f87590354dbd86f00207bc8f'
P='com/elfmcys/yesstevemodel/'
TARGETS=set([('com/elfmcys/yesstevemodel/oOoOOo00o00O0ooooOOO0oO0', 'O00OOOooOoooOoo0o0o0oO0O', '()Ljava/util/Set;'), ('com/elfmcys/yesstevemodel/oOoOOo00o00O0ooooOOO0oO0', 'oOOOo0OOO0ooooo0O00OO0o0', '()Ljava/util/Set;'), ('com/elfmcys/yesstevemodel/oOoOOo00o00O0ooooOOO0oO0', 'oooooooOOoOOoO00OooOo00O', '[Ljava/lang/Object;'), ('com/elfmcys/yesstevemodel/oOoOOo00o00O0ooooOOO0oO0', 'Oo00o0OooOOo0ooOoo0oO0o0', '[Ljava/lang/Object;')])
def capture(jar):
 raw=Path(jar).read_bytes()
 if len(raw)!=63269843 or hashlib.sha256(raw).hexdigest()!=SHA:raise ValueError('Wrong artifact')
 calls=[];members=[];handles=[];count=0
 with zipfile.ZipFile(jar) as z:
  target_checks=validate_targets(TARGETS,declaration_index(z))
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
    matches=[op for op in m.get('instructions',[]) if tuple(op.get('reference',{}).get(k) for k in ('owner','name','descriptor')) in TARGETS and op['opcode'] in ['0xb2','0xb3','0xb4','0xb5','0xb6','0xb7','0xb8','0xb9']]
    if matches:
     members.append(m)
     for op in matches:
      index=next(i for i,v in enumerate(m['instructions']) if v['offset']==op['offset'])
      following=m['instructions'][index+1] if index+1<len(m['instructions']) else None
      calls.append({'caller':{k:m[k] for k in ['owner','name','descriptor']},'instruction':op,'immediate_following_instruction':following})
 return {'target_declaration_checks':target_checks,'target_declarations_verified':True,'artifact_sha256':SHA,'class_count':count,'targets':[list(x) for x in sorted(TARGETS)],'method_handle_targets':handles,'calls':calls,'caller_methods':members,'external_or_reflective_closure':False,'runtime_executed':False}
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--jar',required=True);p.add_argument('--evidence',required=True);p.add_argument('--out');p.add_argument('--capture',action='store_true');a=p.parse_args();d=capture(a.jar)
 if a.capture:Path(a.evidence).write_text(json.dumps(d,indent=2)+'\n');return
 e=json.loads(Path(a.evidence).read_text());checks=[{'check':'exact-complete-call-scan','pass':e==d},{'check':'955-classes','pass':d['class_count']==955}];neg=[]
 for name,mut in [('removed-target-declaration-proof',lambda x:x['target_declaration_checks'].pop()),('false-target-proof',lambda x:x.update(target_declarations_verified=False)),('invented-method-handle',lambda x:x['method_handle_targets'].append({'invented':True})),('invented-call',lambda x:x['calls'].append({'invented':True})),('invented-caller-body',lambda x:x['caller_methods'].append({'invented':True})),('missing-target',lambda x:x['targets'].pop()),('invented-global-closure',lambda x:x.update(external_or_reflective_closure=True)),('wrong-artifact',lambda x:x.update(artifact_sha256='0'*64))]:
  y=copy.deepcopy(e);mut(y);neg.append({'control':name,'rejected':y!=d})
 r={'checks':checks,'negative_controls':neg,'failures':[c for c in checks if not c['pass']],'independent_review':'NOT_RUN','runtime_executed':False};Path(a.out).write_text(json.dumps(r,indent=2)+'\n');print(json.dumps({'handles':len(d['method_handle_targets']),'calls':len(d['calls']),'caller_methods':len(d['caller_methods']),'checks':len(checks),'negative_controls':len(neg),'failures':len(r['failures'])}))
 if r['failures'] or any(not n['rejected'] for n in neg):raise SystemExit(1)
if __name__=='__main__':main()
