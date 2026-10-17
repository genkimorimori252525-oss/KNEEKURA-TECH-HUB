#!/usr/bin/env python3
"""CHILD-CONTEXT-ARROW fixed-artifact integrity audit; does not execute target classes or independently prove prose semantics."""
import argparse,copy,hashlib,json,subprocess,zipfile
from pathlib import Path
from audit_seed_recovery_ysm_265 import parse_bounded,BOUNDDETAILS
from scan_ysm_265 import parse_class
SHA='25b5e902b96f4c298690208f8b433cbc31737c23f87590354dbd86f00207bc8f'
SIZE=63269843
OWNERS=['com/elfmcys/yesstevemodel/O0O00Oo0o0oO0oo0oO00OOoO', 'com/elfmcys/yesstevemodel/oo00Oo00o0ooooOooo0Oo0OO', 'com/elfmcys/yesstevemodel/oo00O000000OoOo0O0O00oOO']
SELECTED=set([('com/elfmcys/yesstevemodel/O0O00Oo0o0oO0oo0oO00OOoO', '<init>', '(Ljava/lang/Object;Lcom/elfmcys/yesstevemodel/o0000OoOooO0oo0o0oooo0Oo;Lcom/elfmcys/yesstevemodel/OO00O0o0OooOOOo00OO00o00;Lcom/elfmcys/yesstevemodel/O00OoOOOOoOOOO0OOOoO0ooO;)V'), ('com/elfmcys/yesstevemodel/O0O00Oo0o0oO0oo0oO00OOoO', '<init>', '(Ljava/lang/Object;Lcom/elfmcys/yesstevemodel/O0O00Oo0o0oO0oo0oO00OOoO;)V'), ('com/elfmcys/yesstevemodel/O0O00Oo0o0oO0oo0oO00OOoO', 'OOOOo0O0oO0OOo0O0O0Oo0O0', '()Lcom/elfmcys/yesstevemodel/OO00O0o0OooOOOo00OO00o00;'), ('com/elfmcys/yesstevemodel/O0O00Oo0o0oO0oo0oO00OOoO', 'o0OOooo0o0OO00OoOOOo0o0O', '()Lcom/elfmcys/yesstevemodel/o0000OoOooO0oo0o0oooo0Oo;'), ('com/elfmcys/yesstevemodel/O0O00Oo0o0oO0oo0oO00OOoO', 'Ooooo0oooO0oooOOOoO0000O', '()Lcom/elfmcys/yesstevemodel/O00OoOOOOoOOOO0OOOoO0ooO;'), ('com/elfmcys/yesstevemodel/O0O00Oo0o0oO0oo0oO00OOoO', 'oo0OoO00oOoo000O0000o0oo', '()Lcom/elfmcys/yesstevemodel/o000o0o0Ooooo0ooo0oO0O0o;'), ('com/elfmcys/yesstevemodel/O0O00Oo0o0oO0oo0oO00OOoO', 'oooooooOOoOOoO00OooOo00O', '()Lcom/elfmcys/yesstevemodel/O0oo0oOo0OOOO00Oo0oo0o00;'), ('com/elfmcys/yesstevemodel/O0O00Oo0o0oO0oo0oO00OOoO', 'Oo00o0OooOOo0ooOoo0oO0o0', '()Lnet/minecraft/util/RandomSource;'), ('com/elfmcys/yesstevemodel/O0O00Oo0o0oO0oo0oO00OOoO', 'Oo0Oo0o00O00Oo0OOoOOoooo', '()Ljava/lang/Object;'), ('com/elfmcys/yesstevemodel/O0O00Oo0o0oO0oo0oO00OOoO', 'O00OOOooOoooOoo0o0o0oO0O', '()Lnet/minecraft/client/Minecraft;'), ('com/elfmcys/yesstevemodel/O0O00Oo0o0oO0oo0oO00OOoO', 'oOOOo0OOO0ooooo0O00OO0o0', '()Lnet/minecraft/client/multiplayer/ClientLevel;'), ('com/elfmcys/yesstevemodel/O0O00Oo0o0oO0oo0oO00OOoO', 'Oo0Oo0o00O00Oo0OOoOOoooo', '(Ljava/lang/Object;)Lcom/elfmcys/yesstevemodel/oo0oOO0000o0Ooooo0OoOo0O;'), ('com/elfmcys/yesstevemodel/O0O00Oo0o0oO0oo0oO00OOoO', 'o0OOO0o0o0OOo000oO00o00O', '()Lcom/elfmcys/yesstevemodel/oOOoO000oOo0OOOOooOOOO0o;'), ('com/elfmcys/yesstevemodel/O0O00Oo0o0oO0oo0oO00OOoO', 'O0OooOo0oOOoOoOoOooO000o', '()Lcom/elfmcys/yesstevemodel/o0Oo0OooOoo0o0000o0oo0oo;'), ('com/elfmcys/yesstevemodel/O0O00Oo0o0oO0oo0oO00OOoO', 'OOOo0OOOoOO0O00Oo00ooOOO', '()Lcom/elfmcys/yesstevemodel/oOOoOoOOooo000oooO0ooOO0;'), ('com/elfmcys/yesstevemodel/O0O00Oo0o0oO0oo0oO00OOoO', 'ooOO000o0O0OOOoO0Oo0o0Oo', '()Lcom/elfmcys/yesstevemodel/o0O0oooOOoo0ooo0OOOOoo0O;'), ('com/elfmcys/yesstevemodel/O0O00Oo0o0oO0oo0oO00OOoO', 'Oo0Oo0o00O00Oo0OOoOOoooo', '(Ljava/lang/String;)Lcom/elfmcys/yesstevemodel/O0o0OOO00000oO00O00oOOo0;'), ('com/elfmcys/yesstevemodel/O0O00Oo0o0oO0oo0oO00OOoO', 'Oo0Oo0o00O00Oo0OOoOOoooo', '(Lcom/elfmcys/yesstevemodel/oO0OoO0O0OoO0oo0oo0OOooo;Lcom/elfmcys/yesstevemodel/O0o0OOO00000oO00O00oOOo0;Ljava/util/List;)Ljava/lang/Object;'), ('com/elfmcys/yesstevemodel/O0O00Oo0o0oO0oo0oO00OOoO', 'Oo0Oo0o00O00Oo0OOoOOoooo', '(Lcom/elfmcys/yesstevemodel/oO0OoO0O0OoO0oo0oo0OOooo;Lcom/elfmcys/yesstevemodel/O0o0OOO00000oO00O00oOOo0;Lcom/elfmcys/yesstevemodel/O00OOo00o0O00ooo000OOo0O$Oo0Oo0o00O00Oo0OOoOOoooo;)Ljava/lang/Object;'), ('com/elfmcys/yesstevemodel/O0O00Oo0o0oO0oo0oO00OOoO', 'oOo0o0000OOOO0OooooO00oo', '()Ljava/util/List;'), ('com/elfmcys/yesstevemodel/O0O00Oo0o0oO0oo0oO00OOoO', 'O0ooooOO0oOo000O0Oo00OOO', '()Z'), ('com/elfmcys/yesstevemodel/O0O00Oo0o0oO0oo0oO00OOoO', 'OO0ooO00OoO00o0OO0OOooO0', '()Z'), ('com/elfmcys/yesstevemodel/O0O00Oo0o0oO0oo0oO00OOoO', 'o0OOooo0o0OO00OoOOOo0o0O', '(Z)V'), ('com/elfmcys/yesstevemodel/O0O00Oo0o0oO0oo0oO00OOoO', 'Oo0Oo0o00O00Oo0OOoOOoooo', '(Ljava/lang/String;[Ljava/lang/Object;)V'), ('com/elfmcys/yesstevemodel/O0O00Oo0o0oO0oo0oO00OOoO', 'Oo0Oo0o00O00Oo0OOoOOoooo', '(Lnet/minecraft/network/chat/Component;)V'), ('com/elfmcys/yesstevemodel/O0O00Oo0o0oO0oo0oO00OOoO', 'Oo0Oo0o00O00Oo0OOoOOoooo', '(Z)Lcom/elfmcys/yesstevemodel/OOOO0O0OO0oOOo00Ooo0oooO;'), ('com/elfmcys/yesstevemodel/O0O00Oo0o0oO0oo0oO00OOoO', 'Oo0Oo0o00O00Oo0OOoOOoooo', '(Lcom/elfmcys/yesstevemodel/OOOO0O0OO0oOOo00Ooo0oooO;)V'), ('com/elfmcys/yesstevemodel/O0O00Oo0o0oO0oo0oO00OOoO', 'Oo0Oo0o00O00Oo0OOoOOoooo', '(Lcom/elfmcys/yesstevemodel/o000o0o0Ooooo0ooo0oO0O0o;)V'), ('com/elfmcys/yesstevemodel/O0O00Oo0o0oO0oo0oO00OOoO', 'Oo0Oo0o00O00Oo0OOoOOoooo', '(Lcom/elfmcys/yesstevemodel/O0oo0oOo0OOOO00Oo0oo0o00;)V'), ('com/elfmcys/yesstevemodel/O0O00Oo0o0oO0oo0oO00OOoO', 'Oo0Oo0o00O00Oo0OOoOOoooo', '(Lcom/elfmcys/yesstevemodel/O0oooOO0Oooo0o0000ooOooO;)V'), ('com/elfmcys/yesstevemodel/O0O00Oo0o0oO0oo0oO00OOoO', 'Oo0Oo0o00O00Oo0OOoOOoooo', '(Lnet/minecraft/util/RandomSource;)V'), ('com/elfmcys/yesstevemodel/O0O00Oo0o0oO0oo0oO00OOoO', 'Oo0Oo0o00O00Oo0OOoOOoooo', '(Lcom/elfmcys/yesstevemodel/oOO0oO0ooo000OoOO0OOooOo;)V'), ('com/elfmcys/yesstevemodel/O0O00Oo0o0oO0oo0oO00OOoO', 'Oo0Oo0o00O00Oo0OOoOOoooo', '(Lcom/elfmcys/yesstevemodel/oOOo0Ooo0oOoo0O0OOOOo0oo;)V'), ('com/elfmcys/yesstevemodel/O0O00Oo0o0oO0oo0oO00OOoO', 'Oo0Oo0o00O00Oo0OOoOOoooo', '(Lcom/elfmcys/yesstevemodel/OOOo0OOOoOO0O00Oo00ooOOO;)V'), ('com/elfmcys/yesstevemodel/O0O00Oo0o0oO0oo0oO00OOoO', 'Oo0Oo0o00O00Oo0OOoOOoooo', '(Lcom/elfmcys/yesstevemodel/o0OOO0o0o0OOo000oO00o00O;)V'), ('com/elfmcys/yesstevemodel/oo00Oo00o0ooooOooo0Oo0OO', '<init>', '(Ljava/lang/Object;)V'), ('com/elfmcys/yesstevemodel/oo00Oo00o0ooooOooo0Oo0OO', 'o0OOooo0o0OO00OoOOOo0o0O', '(Ljava/lang/Object;)Lcom/elfmcys/yesstevemodel/oo00Oo00o0ooooOooo0Oo0OO;'), ('com/elfmcys/yesstevemodel/oo00Oo00o0ooooOooo0Oo0OO', 'Ooooo0oooO0oooOOOoO0000O', '(Lcom/elfmcys/yesstevemodel/oo00Oo00o0ooooOooo0Oo0OO;Lcom/elfmcys/yesstevemodel/oOOOOoo0O0Oo0O00oo0oooO0;Lcom/elfmcys/yesstevemodel/oOOOOoo0O0Oo0O00oo0oooO0;)Ljava/lang/Object;'), ('com/elfmcys/yesstevemodel/oo00O000000OoOo0O0O00oOO', '<init>', '()V'), ('com/elfmcys/yesstevemodel/oo00O000000OoOo0O0O00oOO', 'O0o00oO0O0ooOOOo0oo0Oo00', '(Lcom/elfmcys/yesstevemodel/oo0oOO0000o0Ooooo0OoOo0O;)Ljava/lang/Object;')])
SOURCES=[('src/main/java/com/elfmcys/yesstevemodel/geckolib3/core/molang/context/MolangContext.java', 'e47a7884eda1f3c1c6af8986c9487f39748c40d5f39b2bbfe3456a20185eaacd', 'f184edabd1b5115ce5a24cb6d155ba5a669f5ba6'), ('src/main/java/com/elfmcys/yesstevemodel/molang/runtime/ExpressionEvaluatorImpl.java', 'b1f5667dd9fc2e6b61d46fba8f66bc9ab51854e555fc192561ea552654febc2e', 'f184edabd1b5115ce5a24cb6d155ba5a669f5ba6'), ('src/main/java/com/elfmcys/yesstevemodel/client/animation/molang/YSMBinding.java', '22bf1679ba5a8967b09109795fff207afdd2cb45ba34c4f70fb9ca4c9ca117a0', 'f184edabd1b5115ce5a24cb6d155ba5a669f5ba6')]

KEYS=('access','instructions','supplemental_full_operand_records','exception_handlers','code_sha256')
DECL=('access','super','interfaces','fields','methods')
def ident(m):return tuple(m.get(k) for k in ('owner','name','descriptor'))
def audit(e,actual,decl,details):
    checks=[]
    def ck(name,ok):checks.append({'check':name,'pass':bool(ok)})
    ck('fixed-artifact',e.get('artifact',{}).get('sha256')==SHA and e.get('artifact',{}).get('size')==SIZE)
    ck('detailed-operands',e.get('detailed_operands') is True)
    rows=e.get('members',[]);ids=[ident(m) for m in rows]
    ck('selected-40-methods',len(ids)==len(set(ids))==40 and set(ids)==set(actual)==SELECTED)
    for m in rows:
        a=actual.get(ident(m),{})
        for k in KEYS:ck(str(ident(m))+':'+k,(k in m)==(k in a) and m.get(k)==a.get(k))
    ds=e.get('owner_declarations',[]);ck('three-declarations',len(ds)==3 and {r['owner'] for r in ds}==set(OWNERS))
    for r in ds:ck(r['owner']+':declaration',r['declaration']==decl.get(r['owner']))
    bs=e.get('bootstrap_and_constant_evidence',[]);ck('three-bootstrap-records',len(bs)==3 and {r['owner'] for r in bs}==set(OWNERS))
    for r in bs:
        for k in ('constant_values','bootstrap_methods'):ck(r['owner']+':'+k,k in r and r[k]==details.get(r['owner'],{}).get(k))
    ss=e.get('source_tracks',[]);ck('three-fixed-source-records',sorted((r.get('path'),r.get('sha256'),r.get('revision')) for r in ss)==sorted(SOURCES))
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
    neg('missing-query-support-O0O00Oo0o0oO0oo0oO00OOoO',lambda x:member(x,0,'()Lcom/elfmcys/yesstevemodel/OO00O0o0OooOOOo00OO00o00;','OOOOo0O0oO0OOo0O0O0Oo0O0')['instructions'].pop())
    neg('missing-query-support-oo00Oo00o0ooooOooo0Oo0OO',lambda x:member(x,1,'(Ljava/lang/Object;)Lcom/elfmcys/yesstevemodel/oo00Oo00o0ooooOooo0Oo0OO;','o0OOooo0o0OO00OoOOOo0o0O')['instructions'].pop())
    neg('missing-query-support-oo00O000000OoOo0O0O00oOO',lambda x:member(x,2,'(Lcom/elfmcys/yesstevemodel/oo0oOO0000o0Ooooo0OoOo0O;)Ljava/lang/Object;','O0o00oO0O0ooOOOo0oo0Oo00')['instructions'].pop())
    neg('invented-child-copy-finally',lambda x:member(x,0,'(Ljava/lang/Object;Lcom/elfmcys/yesstevemodel/O0O00Oo0o0oO0oo0oO00OOoO;)V','<init>')['exception_handlers'].append({'handler':0}))
    result={'artifact_sha256':SHA,'checks':checks,'negative_controls':negatives,'failures':[c for c in checks if not c['pass']],'negative_failures':[n for n in negatives if not n['rejected']],'independent_semantic_review':'NOT_RUN','runtime_executed':False,'central_mapping_promoted':False}
    Path(a.out).write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({'checks':len(checks),'negative_controls':len(negatives),'failures':len(result['failures'])+len(result['negative_failures'])}))
    if result['failures'] or result['negative_failures']:raise SystemExit(1)
if __name__=='__main__':main()
