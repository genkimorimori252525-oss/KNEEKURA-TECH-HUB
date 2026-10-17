#!/usr/bin/env python3
"""Closed fixed-JAR hierarchy/caller inventory, not runtime dispatch proof."""
import argparse,copy,hashlib,json,zipfile
from pathlib import Path
from scan_ysm_265 import parse_class
from audit_seed_recovery_ysm_265 import parse_bounded
SHA='25b5e902b96f4c298690208f8b433cbc31737c23f87590354dbd86f00207bc8f'
ROOT='com/elfmcys/yesstevemodel/o0000OoOooO0oo0o0oooo0Oo'
CUSTOM='com/elfmcys/yesstevemodel/oOo00OoOO00O000ooO0Oo00o'
TARGETS=[('OO0O00oO0OOO00oOO0OoO0OO','()Z'),('Oo0Oo0o00O00Oo0OOoOOoooo','(Lcom/elfmcys/yesstevemodel/OO00O0o0OooOOOo00OO00o00;)Z')]
def capture(jar):
    raw=Path(jar).read_bytes()
    if len(raw)!=63269843 or hashlib.sha256(raw).hexdigest()!=SHA:raise ValueError('Wrong artifact')
    with zipfile.ZipFile(jar) as z:
        classes={n[:-6]:parse_class(z.read(n)) for n in z.namelist() if n.endswith('.class')}
        def sub(o):
            seen=set()
            while o in classes and o not in seen:
                if o==ROOT:return True
                seen.add(o);o=classes[o]['super']
            return False
        descendants=sorted(o for o in classes if sub(o));decl=[];calls=[]
        for owner in sorted(classes):
            methods=parse_bounded(z.read(owner+'.class'),True)
            if owner in descendants:
                decl.append({'owner':owner,'super':classes[owner]['super'],'methods':[m for m in methods if (m['name'],m['descriptor']) in TARGETS]})
            for m in methods:
                for op in m.get('instructions',[]):
                    r=op.get('reference',{})
                    if r.get('owner') in descendants and ((r.get('name')=='Oo0Oo0o00O00Oo0OOoOOoooo' and r.get('descriptor')=='(F)V' and r.get('owner')==CUSTOM) or (r.get('name')=='oOOOooO00oo0oOooooOO0Oo0' and r.get('descriptor')=='()Lcom/elfmcys/yesstevemodel/OO00O0o0OooOOOo00OO00o00;')):
                        calls.append({'caller':{k:m[k] for k in ('owner','name','descriptor','code_sha256')},'instruction':op})
    return {'artifact_sha256':SHA,'class_count':len(classes),'descendants':decl,'direct_async_calls':calls,'runtime_dispatch_verified':False,'external_classes_scanned':False}
def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--jar',required=True);p.add_argument('--evidence',required=True);p.add_argument('--out');p.add_argument('--capture',action='store_true');a=p.parse_args();actual=capture(a.jar)
    if a.capture:Path(a.evidence).write_text(json.dumps(actual,indent=2)+'\n');return
    e=json.loads(Path(a.evidence).read_text());checks=[{'check':'complete-fixed-artifact-inventory','pass':e==actual},{'check':'955-classes','pass':actual['class_count']==955},{'check':'12-descendants-including-root','pass':len(actual['descendants'])==12}]
    negatives=[]
    for label,mutate in [('missing-descendant',lambda x:x['descendants'].pop()),('missing-caller',lambda x:x['direct_async_calls'].pop()),('wrong-artifact',lambda x:x.update(artifact_sha256='0'*64)),('invented-external-closure',lambda x:x.update(external_classes_scanned=True)),('lost-override-body',lambda x:next(d for d in x['descendants'] if d['methods'])['methods'].pop())]:
        y=copy.deepcopy(e);mutate(y);negatives.append({'control':label,'rejected':y!=actual})
    r={'checks':checks,'negative_controls':negatives,'failures':[c for c in checks if not c['pass']],'runtime_executed':False,'independent_review':'NOT_RUN'};Path(a.out).write_text(json.dumps(r,indent=2)+'\n');print(json.dumps({'descendants':len(actual['descendants']),'direct_async_calls':len(actual['direct_async_calls']),'checks':len(checks),'negative_controls':len(negatives),'failures':len(r['failures'])}))
    if r['failures'] or any(not n['rejected'] for n in negatives):raise SystemExit(1)
if __name__=='__main__':main()
