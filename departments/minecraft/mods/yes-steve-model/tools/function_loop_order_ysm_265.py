#!/usr/bin/env python3
"""Fixed-artifact selected motion query evidence audit. Never runs target classes."""
import argparse,copy,hashlib,json,subprocess,zipfile
from pathlib import Path
from audit_seed_recovery_ysm_265 import parse_bounded,BOUNDDETAILS
from scan_ysm_265 import parse_class
SHA='25b5e902b96f4c298690208f8b433cbc31737c23f87590354dbd86f00207bc8f'
SIZE=63269843
OWNERS=['com/elfmcys/yesstevemodel/OOooO0oOOOoO000oOo0O00Oo', 'com/elfmcys/yesstevemodel/oO0OoO0O0OoO0oo0oo0OOooo', 'com/elfmcys/yesstevemodel/O00OOo00o0O00ooo000OOo0O', 'com/elfmcys/yesstevemodel/O00OOo00o0O00ooo000OOo0O$Oo0Oo0o00O00Oo0OOoOOoooo', 'com/elfmcys/yesstevemodel/oo00Oo00o0ooooOooo0Oo0OO']
SOURCES=[('src/main/java/com/elfmcys/yesstevemodel/molang/runtime/binding/StandardBindings.java', '93c7cbc1116fb1b4ba91998190a313df28810b33394c01e10837c61b6101d214', 'f184edabd1b5115ce5a24cb6d155ba5a669f5ba6'), ('src/main/java/com/elfmcys/yesstevemodel/molang/runtime/ExecutionContext.java', '4567c411c88fa5328804167f0acb04f994ace8035a2931cb20725b0a7e3a99a0', 'f184edabd1b5115ce5a24cb6d155ba5a669f5ba6'), ('src/main/java/com/elfmcys/yesstevemodel/molang/runtime/Function.java', '66e683e3b7e342e5fb5706c67409e88bcc3cb243eb89486ae85bc0597f44fff4', 'f184edabd1b5115ce5a24cb6d155ba5a669f5ba6'), ('src/main/java/com/elfmcys/yesstevemodel/molang/runtime/Function.java', '66e683e3b7e342e5fb5706c67409e88bcc3cb243eb89486ae85bc0597f44fff4', 'f184edabd1b5115ce5a24cb6d155ba5a669f5ba6'), ('src/main/java/com/elfmcys/yesstevemodel/molang/runtime/ExpressionEvaluatorImpl.java', 'b1f5667dd9fc2e6b61d46fba8f66bc9ab51854e555fc192561ea552654febc2e', 'f184edabd1b5115ce5a24cb6d155ba5a669f5ba6')]
SELECTED=set([('com/elfmcys/yesstevemodel/OOooO0oOOOoO000oOo0O00Oo', '<init>', '()V'), ('com/elfmcys/yesstevemodel/OOooO0oOOOoO000oOo0O00Oo', 'Oo0Oo0o00O00Oo0OOoOOoooo', '(Lcom/elfmcys/yesstevemodel/oO0OoO0O0OoO0oo0oo0OOooo;Lcom/elfmcys/yesstevemodel/O00OOo00o0O00ooo000OOo0O$Oo0Oo0o00O00Oo0OOoOOoooo;)Ljava/lang/Object;'), ('com/elfmcys/yesstevemodel/OOooO0oOOOoO000oOo0O00Oo', 'o0OOooo0o0OO00OoOOOo0o0O', '(Lcom/elfmcys/yesstevemodel/oO0OoO0O0OoO0oo0oo0OOooo;Lcom/elfmcys/yesstevemodel/O00OOo00o0O00ooo000OOo0O$Oo0Oo0o00O00Oo0OOoOOoooo;)Ljava/lang/Object;'), ('com/elfmcys/yesstevemodel/OOooO0oOOOoO000oOo0O00Oo', '<clinit>', '()V'), ('com/elfmcys/yesstevemodel/oO0OoO0O0OoO0oo0oo0OOooo', 'Oo0Oo0o00O00Oo0OOoOOoooo', '()Ljava/lang/Object;'), ('com/elfmcys/yesstevemodel/oO0OoO0O0OoO0oo0oo0OOooo', 'o0OOooo0o0OO00OoOOOo0o0O', '(Lcom/elfmcys/yesstevemodel/oOOOOoo0O0Oo0O00oo0oooO0;)Ljava/lang/Object;'), ('com/elfmcys/yesstevemodel/oO0OoO0O0OoO0oo0oo0OOooo', 'Oo0Oo0o00O00Oo0OOoOOoooo', '(Ljava/lang/Iterable;Z)Ljava/lang/Object;'), ('com/elfmcys/yesstevemodel/oO0OoO0O0OoO0oo0oo0OOooo', 'O00OOOooOoooOoo0o0o0oO0O', '(Lcom/elfmcys/yesstevemodel/oOOOOoo0O0Oo0O00oo0oooO0;)Ljava/lang/Object;'), ('com/elfmcys/yesstevemodel/oO0OoO0O0OoO0oo0oo0OOooo', 'o0OOooo0o0OO00OoOOOo0o0O', '(Ljava/lang/Iterable;Z)Ljava/lang/Object;'), ('com/elfmcys/yesstevemodel/O00OOo00o0O00ooo000OOo0O', 'evaluate', '(Lcom/elfmcys/yesstevemodel/oO0OoO0O0OoO0oo0oo0OOooo;Lcom/elfmcys/yesstevemodel/O00OOo00o0O00ooo000OOo0O$Oo0Oo0o00O00Oo0OOoOOoooo;)Ljava/lang/Object;'), ('com/elfmcys/yesstevemodel/O00OOo00o0O00ooo000OOo0O', 'Oo0Oo0o00O00Oo0OOoOOoooo', '(I)Z'), ('com/elfmcys/yesstevemodel/O00OOo00o0O00ooo000OOo0O', 'Oo0Oo0o00O00Oo0OOoOOoooo', '(Lcom/elfmcys/yesstevemodel/oO0OoO0O0OoO0oo0oo0OOooo;Lcom/elfmcys/yesstevemodel/O00OOo00o0O00ooo000OOo0O$Oo0Oo0o00O00Oo0OOoOOoooo;)Ljava/lang/Object;'), ('com/elfmcys/yesstevemodel/O00OOo00o0O00ooo000OOo0O', '<clinit>', '()V'), ('com/elfmcys/yesstevemodel/O00OOo00o0O00ooo000OOo0O$Oo0Oo0o00O00Oo0OOoOOoooo', '<init>', '(Ljava/util/List;)V'), ('com/elfmcys/yesstevemodel/O00OOo00o0O00ooo000OOo0O$Oo0Oo0o00O00Oo0OOoOOoooo', 'Oo0Oo0o00O00Oo0OOoOOoooo', '()I'), ('com/elfmcys/yesstevemodel/O00OOo00o0O00ooo000OOo0O$Oo0Oo0o00O00Oo0OOoOOoooo', 'Oo0Oo0o00O00Oo0OOoOOoooo', '(Lcom/elfmcys/yesstevemodel/oO0OoO0O0OoO0oo0oo0OOooo;I)Ljava/lang/String;'), ('com/elfmcys/yesstevemodel/O00OOo00o0O00ooo000OOo0O$Oo0Oo0o00O00Oo0OOoOOoooo', 'o0OOooo0o0OO00OoOOOo0o0O', '(Lcom/elfmcys/yesstevemodel/oO0OoO0O0OoO0oo0oo0OOooo;I)I'), ('com/elfmcys/yesstevemodel/O00OOo00o0O00ooo000OOo0O$Oo0Oo0o00O00Oo0OOoOOoooo', 'O00OOOooOoooOoo0o0o0oO0O', '(Lcom/elfmcys/yesstevemodel/oO0OoO0O0OoO0oo0oo0OOooo;I)D'), ('com/elfmcys/yesstevemodel/O00OOo00o0O00ooo000OOo0O$Oo0Oo0o00O00Oo0OOoOOoooo', 'oOOOo0OOO0ooooo0O00OO0o0', '(Lcom/elfmcys/yesstevemodel/oO0OoO0O0OoO0oo0oo0OOooo;I)I'), ('com/elfmcys/yesstevemodel/O00OOo00o0O00ooo000OOo0O$Oo0Oo0o00O00Oo0OOoOOoooo', 'OOOOo0O0oO0OOo0O0O0Oo0O0', '(Lcom/elfmcys/yesstevemodel/oO0OoO0O0OoO0oo0oo0OOooo;I)F'), ('com/elfmcys/yesstevemodel/O00OOo00o0O00ooo000OOo0O$Oo0Oo0o00O00Oo0OOoOOoooo', 'Ooooo0oooO0oooOOOoO0000O', '(Lcom/elfmcys/yesstevemodel/oO0OoO0O0OoO0oo0oo0OOooo;I)Z'), ('com/elfmcys/yesstevemodel/O00OOo00o0O00ooo000OOo0O$Oo0Oo0o00O00Oo0OOoOOoooo', 'oo0OoO00oOoo000O0000o0oo', '(Lcom/elfmcys/yesstevemodel/oO0OoO0O0OoO0oo0oo0OOooo;I)Lnet/minecraft/resources/ResourceLocation;'), ('com/elfmcys/yesstevemodel/O00OOo00o0O00ooo000OOo0O$Oo0Oo0o00O00Oo0OOoOOoooo', 'oooooooOOoOOoO00OooOo00O', '(Lcom/elfmcys/yesstevemodel/oO0OoO0O0OoO0oo0oo0OOooo;I)Ljava/lang/Object;'), ('com/elfmcys/yesstevemodel/O00OOo00o0O00ooo000OOo0O$Oo0Oo0o00O00Oo0OOoOOoooo', 'Oo0Oo0o00O00Oo0OOoOOoooo', '(I)Lcom/elfmcys/yesstevemodel/oOOOOoo0O0Oo0O00oo0oooO0;'), ('com/elfmcys/yesstevemodel/oo00Oo00o0ooooOooo0Oo0OO', 'Oo0Oo0o00O00Oo0OOoOOoooo', '(Lcom/elfmcys/yesstevemodel/OOoo00oo0OoOOO0o0OO0oOoo;)Ljava/lang/Object;'), ('com/elfmcys/yesstevemodel/oo00Oo00o0ooooOooo0Oo0OO', 'Oo0Oo0o00O00Oo0OOoOOoooo', '(Lcom/elfmcys/yesstevemodel/oo0Ooo00oo0000oOOOo0oOoo;)Ljava/lang/Object;'), ('com/elfmcys/yesstevemodel/oo00Oo00o0ooooOooo0Oo0OO', 'o0OOooo0o0OO00OoOOOo0o0O', '(Lcom/elfmcys/yesstevemodel/oo0Ooo00oo0000oOOOo0oOoo;)Z'), ('com/elfmcys/yesstevemodel/oo00Oo00o0ooooOooo0Oo0OO', 'Oo0Oo0o00O00Oo0OOoOOoooo', '(Lcom/elfmcys/yesstevemodel/oo0Ooo00oo0000oOOOo0oOoo;I)V'), ('com/elfmcys/yesstevemodel/oo00Oo00o0ooooOooo0Oo0OO', 'Oo0Oo0o00O00Oo0OOoOOoooo', '(Lcom/elfmcys/yesstevemodel/oo0Ooo00oo0000oOOOo0oOoo;Lcom/elfmcys/yesstevemodel/OO00oo0o0o0oo0OoO00OOoOo;Ljava/lang/Iterable;)V')])

KEYS=('access','instructions','supplemental_full_operand_records','exception_handlers','code_sha256')
DECL=('access','super','interfaces','fields','methods')
def ident(m):return tuple(m.get(k) for k in ('owner','name','descriptor'))
def audit(e,actual,decl,details):
    checks=[]
    def ck(name,ok):checks.append({'check':name,'pass':bool(ok)})
    ck('fixed-artifact',e.get('artifact',{}).get('sha256')==SHA and e.get('artifact',{}).get('size')==SIZE)
    ck('detailed-operands',e.get('detailed_operands') is True)
    rows=e.get('members',[]);ids=[ident(m) for m in rows]
    ck('complete-29-selected-methods',len(ids)==len(set(ids))==29 and set(ids)==set(actual)==SELECTED)
    for m in rows:
        a=actual.get(ident(m),{})
        for k in KEYS:ck(str(ident(m))+':'+k,(k in m)==(k in a) and m.get(k)==a.get(k))
    ds=e.get('owner_declarations',[]);ck('five-declarations',len(ds)==5 and {r['owner'] for r in ds}==set(OWNERS))
    for r in ds:ck(r['owner']+':declaration',r['declaration']==decl.get(r['owner']))
    bs=e.get('bootstrap_and_constant_evidence',[]);ck('five-bootstrap-records',len(bs)==5 and {r['owner'] for r in bs}==set(OWNERS))
    for r in bs:
        for k in ('constant_values','bootstrap_methods'):ck(r['owner']+':'+k,k in r and r[k]==details.get(r['owner'],{}).get(k))
    ss=e.get('source_tracks',[]);ck('five-fixed-sources',sorted((r.get('path'),r.get('sha256'),r.get('revision')) for r in ss)==sorted(SOURCES))
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
            actual.update({ident(m):m for m in parse_bounded(b,True) if ident(m) in SELECTED})
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
    loop='(Lcom/elfmcys/yesstevemodel/oo0Ooo00oo0000oOOOo0oOoo;)Z'
    neg('lost-loop-depth-finally',lambda x:member(x,4,loop)['exception_handlers'].clear())
    safe='(Lcom/elfmcys/yesstevemodel/oOOOOoo0O0Oo0O00oo0oooO0;)Ljava/lang/Object;'
    neg('safe-evaluation-catches-Throwable',lambda x:member(x,1,safe,'O00OOOooOoooOoo0o0o0oO0O')['exception_handlers'][0].update(catch='java/lang/Throwable'))
    neg('missing-argument-read',lambda x:member(x,3,'(Lcom/elfmcys/yesstevemodel/oO0OoO0O0OoO0oo0oo0OOooo;I)Ljava/lang/Object;')['instructions'].pop())
    func='(Lcom/elfmcys/yesstevemodel/oO0OoO0O0OoO0oo0oo0OOooo;Lcom/elfmcys/yesstevemodel/O00OOo00o0O00ooo000OOo0O$Oo0Oo0o00O00Oo0OOoOOoooo;)Ljava/lang/Object;'
    neg('loop-cap-removed',lambda x:op(x,0,func,19,'o0OOooo0o0OO00OoOOOo0o0O').update(immediate=2048))
    neg('loop-round-to-floor',lambda x:op(x,0,func,16,'o0OOooo0o0OO00OoOOOo0o0O')['reference'].update(name='floor'))
    neg('foreach-target-type',lambda x:op(x,0,func,17,'Oo0Oo0o00O00Oo0OOoOOoooo')['reference'].update(class_name='java/lang/Object'))
    neg('foreach-arity',lambda x:op(x,0,func,4,'Oo0Oo0o00O00Oo0OOoOOoooo').update(opcode='0x5'))
    result={'artifact_sha256':SHA,'checks':checks,'negative_controls':negatives,'failures':[c for c in checks if not c['pass']],'negative_failures':[n for n in negatives if not n['rejected']],'independent_semantic_review':'NOT_RUN','runtime_executed':False,'central_mapping_promoted':False}
    Path(a.out).write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({'checks':len(checks),'negative_controls':len(negatives),'failures':len(result['failures'])+len(result['negative_failures'])}))
    if result['failures'] or result['negative_failures']:raise SystemExit(1)
if __name__=='__main__':main()
