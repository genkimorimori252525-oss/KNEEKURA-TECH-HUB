#!/usr/bin/env python3
"""Fixed-artifact animatable frame evidence audit. Never runs target classes."""
import argparse,copy,hashlib,json,subprocess,zipfile
from pathlib import Path
from audit_seed_recovery_ysm_265 import parse_bounded,BOUNDDETAILS
from scan_ysm_265 import parse_class
SHA='25b5e902b96f4c298690208f8b433cbc31737c23f87590354dbd86f00207bc8f'
SIZE=63269843
OWNERS=['com/elfmcys/yesstevemodel/O0oooOO0Oooo0o0000ooOooO', 'com/elfmcys/yesstevemodel/O0oooOO0Oooo0o0000ooOooO$Oo0Oo0o00O00Oo0OOoOOoooo', 'com/elfmcys/yesstevemodel/O00o0OooOOOooo000ooOo00o', 'com/elfmcys/yesstevemodel/O00o0OooOOOooo000ooOo00o$Oo0Oo0o00O00Oo0OOoOOoooo', 'com/elfmcys/yesstevemodel/O00o0OooOOOooo000ooOo00o$o0OOooo0o0OO00OoOOOo0o0O', 'com/elfmcys/yesstevemodel/O0O00Oo0o0oO0oo0oO00OOoO', 'com/elfmcys/yesstevemodel/o000o0o0Ooooo0ooo0oO0O0o']
SOURCES=[('src/main/java/com/elfmcys/yesstevemodel/geckolib3/core/molang/storage/MolangMemory.java', 'b22b661a2c4c8663e095214a12e95b92791bfc79ed92cd67c60bd71ca498c76e', 'f184edabd1b5115ce5a24cb6d155ba5a669f5ba6'), ('src/main/java/com/elfmcys/yesstevemodel/geckolib3/core/molang/storage/MolangMemory.java', 'b22b661a2c4c8663e095214a12e95b92791bfc79ed92cd67c60bd71ca498c76e', 'f184edabd1b5115ce5a24cb6d155ba5a669f5ba6'), ('src/main/java/com/elfmcys/yesstevemodel/geckolib3/core/molang/storage/StackMemory.java', 'b82c05a67e7e5d29cd00eff10ba69133633e6e4d6553cd9919299c0a59a76e0a', 'f184edabd1b5115ce5a24cb6d155ba5a669f5ba6'), ('src/main/java/com/elfmcys/yesstevemodel/geckolib3/core/molang/storage/StackMemory.java', 'b82c05a67e7e5d29cd00eff10ba69133633e6e4d6553cd9919299c0a59a76e0a', 'f184edabd1b5115ce5a24cb6d155ba5a669f5ba6'), ('src/main/java/com/elfmcys/yesstevemodel/geckolib3/core/molang/storage/StackMemory.java', 'b82c05a67e7e5d29cd00eff10ba69133633e6e4d6553cd9919299c0a59a76e0a', 'f184edabd1b5115ce5a24cb6d155ba5a669f5ba6'), ('src/main/java/com/elfmcys/yesstevemodel/geckolib3/core/molang/context/MolangContext.java', 'e47a7884eda1f3c1c6af8986c9487f39748c40d5f39b2bbfe3456a20185eaacd', 'f184edabd1b5115ce5a24cb6d155ba5a669f5ba6'), ('src/main/java/com/elfmcys/yesstevemodel/geckolib3/core/molang/context/AnimationContext.java', '27bfa16fb3b44e8febd3b74158c2f4ad28c8a544c2b2225c8beaab76c23a9ef6', 'f184edabd1b5115ce5a24cb6d155ba5a669f5ba6')]

KEYS=('access','instructions','supplemental_full_operand_records','exception_handlers','code_sha256')
DECL=('access','super','interfaces','fields','methods')
def ident(m):return tuple(m.get(k) for k in ('owner','name','descriptor'))
def audit(e,actual,decl,details):
    checks=[]
    def ck(name,ok):checks.append({'check':name,'pass':bool(ok)})
    ck('fixed-artifact',e.get('artifact',{}).get('sha256')==SHA and e.get('artifact',{}).get('size')==SIZE)
    ck('detailed-operands',e.get('detailed_operands') is True)
    rows=e.get('members',[]);ids=[ident(m) for m in rows]
    ck('complete-88-methods',len(ids)==len(set(ids))==88 and set(ids)==set(actual))
    for m in rows:
        a=actual.get(ident(m),{})
        for k in KEYS:ck(str(ident(m))+':'+k,(k in m)==(k in a) and m.get(k)==a.get(k))
    ds=e.get('owner_declarations',[]);ck('seven-declarations',len(ds)==7 and {r['owner'] for r in ds}==set(OWNERS))
    for r in ds:ck(r['owner']+':declaration',r['declaration']==decl.get(r['owner']))
    bs=e.get('bootstrap_and_constant_evidence',[]);ck('seven-bootstrap-records',len(bs)==7 and {r['owner'] for r in bs}==set(OWNERS))
    for r in bs:
        for k in ('constant_values','bootstrap_methods'):ck(r['owner']+':'+k,k in r and r[k]==details.get(r['owner'],{}).get(k))
    ss=e.get('source_tracks',[]);ck('seven-fixed-source-records',sorted((r.get('path'),r.get('sha256'),r.get('revision')) for r in ss)==sorted(SOURCES))
    return checks

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    for k in ('jar','evidence','source-root','out'):ap.add_argument('--'+k,required=True)
    a=ap.parse_args();raw=Path(a.jar).read_bytes()
    if len(raw)!=SIZE or hashlib.sha256(raw).hexdigest()!=SHA:raise SystemExit('Wrong fixed artifact')
    e=json.loads(Path(a.evidence).read_text());actual={};decl={}
    with zipfile.ZipFile(a.jar) as z:
        for owner in OWNERS:
            b=z.read(owner+'.class');c=parse_class(b);decl[owner]={k:c[k] for k in DECL}
            actual.update({ident(m):m for m in parse_bounded(b,True)})
    details=copy.deepcopy(BOUNDDETAILS);checks=audit(e,actual,decl,details);root=Path(a.source_root)
    revision=subprocess.check_output(['git','-C',str(root),'rev-parse','HEAD'],text=True).strip()
    checks.append({'check':'source-revision','pass':revision==SOURCES[0][2]})
    for path,sha,rev in SOURCES:checks.append({'check':'source:'+path,'pass':hashlib.sha256((root/path).read_bytes()).hexdigest()==sha})
    negatives=[]
    def member(x,owner,desc,name=None):return next(m for m in x['members'] if m['owner']==OWNERS[owner] and m['descriptor']==desc and (name is None or m['name']==name))
    def op(x,owner,desc,offset,name=None):return next(o for o in member(x,owner,desc,name)['instructions'] if o['offset']==offset)
    def neg(name,mutate):
        x=copy.deepcopy(e);mutate(x);fail=[c for c in audit(x,actual,decl,details) if not c['pass']];negatives.append({'control':name,'rejected':bool(fail)})
    neg('missing-method',lambda x:x['members'].pop())
    neg('missing-owner',lambda x:x['owner_declarations'].pop())
    neg('missing-source',lambda x:x['source_tracks'].pop())
    neg('missing-bootstrap',lambda x:x['bootstrap_and_constant_evidence'].pop())
    neg('wrong-artifact',lambda x:x['artifact'].update(sha256='0'*64))
    neg('missing-pop-body',lambda x:member(x,2,'()V','Oo0Oo0o00O00Oo0OOoOOoooo')['instructions'].pop())
    neg('invented-list-push-finally',lambda x:member(x,2,'(Ljava/util/List;)Z')['exception_handlers'].append({'start':0,'end':99,'handler':99,'catch':None}))
    neg('lost-args-accessor-body',lambda x:member(x,3,'(I)Ljava/lang/Object;','get')['instructions'].pop())
    neg('stack-depth-limit',lambda x:op(x,2,'(Ljava/util/List;)Z',7).update(immediate=64))
    neg('stack-depth-equality',lambda x:op(x,2,'(Ljava/util/List;)Z',9).update(opcode='0xa3'))
    neg('temp-size-equality',lambda x:op(x,2,'(I)Ljava/lang/Object;',5).update(opcode='0xa3'))
    call='(Lcom/elfmcys/yesstevemodel/oO0OoO0O0OoO0oo0oo0OOooo;Lcom/elfmcys/yesstevemodel/O0o0OOO00000oO00O00oOOo0;Ljava/util/List;)Ljava/lang/Object;'
    neg('lost-user-call-finally',lambda x:member(x,5,call)['exception_handlers'].clear())
    neg('failed-push-enters-body',lambda x:op(x,5,call,11).update(opcode='0x9a'))
    result={'artifact_sha256':SHA,'checks':checks,'negative_controls':negatives,'failures':[c for c in checks if not c['pass']],'negative_failures':[n for n in negatives if not n['rejected']],'independent_semantic_review':'NOT_RUN','runtime_executed':False,'central_mapping_promoted':False}
    Path(a.out).write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({'checks':len(checks),'negative_controls':len(negatives),'failures':len(result['failures'])+len(result['negative_failures'])}))
    if result['failures'] or result['negative_failures']:raise SystemExit(1)
if __name__=='__main__':main()
