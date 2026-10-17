#!/usr/bin/env python3
"""Literal Query/YSM constructor registration catalog, not global runtime registration closure."""
import argparse,copy,hashlib,json,zipfile
from pathlib import Path
from audit_seed_recovery_ysm_265 import parse_bounded,BOUNDDETAILS
SHA='25b5e902b96f4c298690208f8b433cbc31737c23f87590354dbd86f00207bc8f'
P='com/elfmcys/yesstevemodel/'
BINDING=P+'oOoOoO0O000OOoo000O0OO00'
ROOTS={'query':P+'o0000OOo0000oo000OOOo0o0','ysm':P+'oo00O000000OoOo0O0O00oOO'}
def capture(jar):
 raw=Path(jar).read_bytes()
 if len(raw)!=63269843 or hashlib.sha256(raw).hexdigest()!=SHA:raise ValueError('Wrong artifact')
 cache={};rows=[];other=[];constructors=[]
 with zipfile.ZipFile(jar) as z:
  def methods(owner):
   if owner not in cache:cache[owner]=parse_bounded(z.read(owner+'.class'),True)
   return cache[owner]
  registrations={(m['name'],m['descriptor']):m for m in methods(BINDING) if m['descriptor'].startswith('(Ljava/lang/String;') and m['descriptor'].endswith(')V')}
  for namespace,owner in ROOTS.items():
   ctor=next(m for m in methods(owner) if m['name']=='<init>');constructors.append(ctor);ops=ctor['instructions'];start=0;bs=copy.deepcopy(BOUNDDETAILS[owner]['bootstrap_methods'])
   for idx,op in enumerate(ops):
    ref=op.get('reference',{});key=ref.get('name'),ref.get('descriptor')
    if op['opcode']=='0xb6' and ref.get('owner') in [owner,BINDING] and key in registrations:
     segment=ops[start:idx];names=[i for i in segment if 'string' in i.get('reference',{})];assert len(names)==1,('ambiguous-name',namespace,op)
     dyn=[i for i in segment if i['opcode']=='0xba'];new=[i for i in segment if i['opcode']=='0xbb'];assert len(dyn)+len(new)==1,('ambiguous-value',namespace,op)
     target={'kind':'allocated-object','owner':new[0]['reference']['class_name']} if new else {'kind':'method-handle',**bs[dyn[0]['reference']['bootstrap_index']]['arguments'][1]['reference']}
     wrapper=[i['reference']['class_name'] for i in registrations[key].get('instructions',[]) if i['opcode']=='0xbb'];r={'namespace':namespace,'name':names[0]['reference']['string'],'name_offset':names[0]['offset'],'registration_offset':op['offset'],'registration_method':ref,'wrapper_allocations':wrapper,'value_target':target,'semantic_review':'NOT_INFERRED_FROM_CATALOG'}
     if dyn:
      r['bootstrap_index']=dyn[0]['reference']['bootstrap_index'];r['bootstrap']=bs[r['bootstrap_index']]
      target_owner=target.get('owner');target_name=target.get('name');target_desc=target.get('descriptor')
      if target_owner and target_owner+'.class' in z.namelist():
       matches=[m for m in methods(target_owner) if m['name']==target_name and m['descriptor']==target_desc];assert len(matches)==1,(target_owner,target_name,target_desc);r['target_code_sha256']=matches[0].get('code_sha256')
     rows.append(r);start=idx+1
   other.extend({'namespace':namespace,'instruction':i} for i in ops[start:] if i['opcode'] in ['0xb6','0xb7','0xb8','0xb9','0xba'])
  defs=[{'name':m['name'],'descriptor':m['descriptor'],'code_sha256':m.get('code_sha256')} for m in registrations.values()]
 return {'artifact_sha256':SHA,'constructor_roots':ROOTS,'entries':rows,'registration_definitions':defs,'constructor_members':constructors,'trailing_nonregistration_calls':other,'global_runtime_registration_complete':False,'optional_extension_registration_included':False,'runtime_executed':False}
def main():
 p=argparse.ArgumentParser(description=__doc__)
 for k in ['jar','evidence']:p.add_argument('--'+k,required=True)
 p.add_argument('--capture',action='store_true');p.add_argument('--out');a=p.parse_args();d=capture(a.jar)
 if a.capture:Path(a.evidence).write_text(json.dumps(d,indent=2)+'\n');return
 e=json.loads(Path(a.evidence).read_text());checks=[{'check':'exact-literal-registration-catalog','pass':e==d},{'check':'unique-namespace-names','pass':len({(r['namespace'],r['name']) for r in d['entries']})==len(d['entries'])}];neg=[]
 for name,mut in [('missing-entry',lambda x:x['entries'].pop()),('wrong-name',lambda x:x['entries'][0].update(name='invented')),('wrong-target',lambda x:x['entries'][0]['value_target'].update(owner='wrong')),('missing-extension-call',lambda x:x['trailing_nonregistration_calls'].pop()),('invented-global-coverage',lambda x:x.update(global_runtime_registration_complete=True))]:
  c=copy.deepcopy(e);mut(c);neg.append({'control':name,'rejected':c!=d})
 r={'checks':checks,'negative_controls':neg,'failures':[c for c in checks if not c['pass']],'independent_semantic_review':'NOT_RUN','runtime_executed':False,'central_mapping_promoted':False};Path(a.out).write_text(json.dumps(r,indent=2)+'\n');print(json.dumps({'entries':len(d['entries']),'checks':len(checks),'negative_controls':len(neg),'failures':len(r['failures'])}))
 if r['failures'] or any(not c['rejected'] for c in neg):raise SystemExit(1)
if __name__=='__main__':main()
