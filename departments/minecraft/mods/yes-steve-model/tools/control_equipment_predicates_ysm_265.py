#!/usr/bin/env python3
"""CONTROL-EQUIPMENT-PREDICATES fixed-artifact integrity audit; does not execute target classes or independently prove prose semantics."""
import argparse,copy,hashlib,json,subprocess,zipfile
from pathlib import Path
from audit_seed_recovery_ysm_265 import parse_bounded,BOUNDDETAILS
from scan_ysm_265 import parse_class
SHA='25b5e902b96f4c298690208f8b433cbc31737c23f87590354dbd86f00207bc8f'
SIZE=63269843
OWNERS=['com/elfmcys/yesstevemodel/O0O0ooOOooOOO00OO0OOOooO', 'com/elfmcys/yesstevemodel/O0O0ooOOooOOO00OO0OOOooO$Oo0Oo0o00O00Oo0OOoOOoooo', 'com/elfmcys/yesstevemodel/o0oOOoO0oooo0O0OoOoOoOo0', 'com/elfmcys/yesstevemodel/O000000ooOoOOo000ooO000o', 'com/elfmcys/yesstevemodel/OoOo0oO0O0OO00O00OOoOo0o']
SELECTED=set([('com/elfmcys/yesstevemodel/O0O0ooOOooOOO00OO0OOOooO', '<init>', '(Lcom/elfmcys/yesstevemodel/O0O0ooOOooOOO00OO0OOOooO$Oo0Oo0o00O00Oo0OOoOOoooo;)V'), ('com/elfmcys/yesstevemodel/O0O0ooOOooOOO00OO0OOOooO', 'Oo0Oo0o00O00Oo0OOoOOoooo', '()Lcom/elfmcys/yesstevemodel/O0O0ooOOooOOO00OO0OOOooO;'), ('com/elfmcys/yesstevemodel/O0O0ooOOooOOO00OO0OOOooO', 'o0OOooo0o0OO00OoOOOo0o0O', '()Lcom/elfmcys/yesstevemodel/O0O0ooOOooOOO00OO0OOOooO;'), ('com/elfmcys/yesstevemodel/O0O0ooOOooOOO00OO0OOOooO', 'O00OOOooOoooOoo0o0o0oO0O', '()Lcom/elfmcys/yesstevemodel/O0O0ooOOooOOO00OO0OOOooO;'), ('com/elfmcys/yesstevemodel/O0O0ooOOooOOO00OO0OOOooO', 'Oo0Oo0o00O00Oo0OOoOOoooo', '(Lcom/elfmcys/yesstevemodel/oO0OoO0O0OoO0oo0oo0OOooo;Lcom/elfmcys/yesstevemodel/O00OOo00o0O00ooo000OOo0O$Oo0Oo0o00O00Oo0OOoOOoooo;)Ljava/lang/Object;'), ('com/elfmcys/yesstevemodel/O0O0ooOOooOOO00OO0OOOooO', 'Oo0Oo0o00O00Oo0OOoOOoooo', '(I)Z'), ('com/elfmcys/yesstevemodel/O0O0ooOOooOOO00OO0OOOooO', 'Oo0Oo0o00O00Oo0OOoOOoooo', '(Lnet/minecraft/world/entity/LivingEntity;Lnet/minecraft/world/InteractionHand;)Z'), ('com/elfmcys/yesstevemodel/O0O0ooOOooOOO00OO0OOOooO', 'o0OOooo0o0OO00OoOOOo0o0O', '(Lnet/minecraft/world/entity/LivingEntity;Lnet/minecraft/world/InteractionHand;)Z'), ('com/elfmcys/yesstevemodel/O0O0ooOOooOOO00OO0OOOooO', 'O00OOOooOoooOoo0o0o0oO0O', '(Lnet/minecraft/world/entity/LivingEntity;Lnet/minecraft/world/InteractionHand;)Z'), ('com/elfmcys/yesstevemodel/O0O0ooOOooOOO00OO0OOOooO$Oo0Oo0o00O00Oo0OOoOOoooo', 'test', '(Lnet/minecraft/world/entity/LivingEntity;Lnet/minecraft/world/InteractionHand;)Z'), ('com/elfmcys/yesstevemodel/o0oOOoO0oooo0O0OoOoOoOo0', '<init>', '()V'), ('com/elfmcys/yesstevemodel/o0oOOoO0oooo0O0OoOoOoOo0', 'Oo0Oo0o00O00Oo0OOoOOoooo', '()Lcom/elfmcys/yesstevemodel/o0oOOoO0oooo0O0OoOoOoOo0;'), ('com/elfmcys/yesstevemodel/o0oOOoO0oooo0O0OoOoOoOo0', 'Oo0Oo0o00O00Oo0OOoOOoooo', '(Lcom/elfmcys/yesstevemodel/oO0OoO0O0OoO0oo0oo0OOooo;Lcom/elfmcys/yesstevemodel/O00OOo00o0O00ooo000OOo0O$Oo0Oo0o00O00Oo0OOoOOoooo;)Ljava/lang/Object;'), ('com/elfmcys/yesstevemodel/o0oOOoO0oooo0O0OoOoOoOo0', 'Oo0Oo0o00O00Oo0OOoOOoooo', '(I)Z'), ('com/elfmcys/yesstevemodel/O000000ooOoOOo000ooO000o', '<init>', '()V'), ('com/elfmcys/yesstevemodel/O000000ooOoOOo000ooO000o', 'Oo0Oo0o00O00Oo0OOoOOoooo', '()Lcom/elfmcys/yesstevemodel/O000000ooOoOOo000ooO000o;'), ('com/elfmcys/yesstevemodel/O000000ooOoOOo000ooO000o', 'Oo0Oo0o00O00Oo0OOoOOoooo', '(Lcom/elfmcys/yesstevemodel/oO0OoO0O0OoO0oo0oo0OOooo;Lcom/elfmcys/yesstevemodel/O00OOo00o0O00ooo000OOo0O$Oo0Oo0o00O00Oo0OOoOOoooo;)Ljava/lang/Object;'), ('com/elfmcys/yesstevemodel/O000000ooOoOOo000ooO000o', 'Oo0Oo0o00O00Oo0OOoOOoooo', '(I)Z'), ('com/elfmcys/yesstevemodel/OoOo0oO0O0OO00O00OOoOo0o', '<init>', '()V'), ('com/elfmcys/yesstevemodel/OoOo0oO0O0OO00O00OOoOo0o', 'Oo0Oo0o00O00Oo0OOoOOoooo', '(Ljava/lang/String;Lnet/minecraft/world/entity/LivingEntity;Lnet/minecraft/world/InteractionHand;)Ljava/lang/String;'), ('com/elfmcys/yesstevemodel/OoOo0oO0O0OO00O00OOoOo0o', 'Oo0Oo0o00O00Oo0OOoOOoooo', '(Lnet/minecraft/world/item/ItemStack;)Ljava/lang/String;')])
SOURCES=[('src/main/java/com/elfmcys/yesstevemodel/client/animation/molang/functions/HandItemCheck.java', '152a07bc585e83527020ad6d7e58fdcfa7ced60c192b10609c38e4ffbd284bc9', 'f184edabd1b5115ce5a24cb6d155ba5a669f5ba6'), ('src/main/java/com/elfmcys/yesstevemodel/client/animation/molang/functions/HandItemCheck.java', '152a07bc585e83527020ad6d7e58fdcfa7ced60c192b10609c38e4ffbd284bc9', 'f184edabd1b5115ce5a24cb6d155ba5a669f5ba6'), ('src/main/java/com/elfmcys/yesstevemodel/client/animation/molang/functions/ArmorCheck.java', 'c3825c8fedd5c7719ea96a1755d38a33bbe96523d7768df08a0cd08df66e94c4', 'f184edabd1b5115ce5a24cb6d155ba5a669f5ba6'), ('src/main/java/com/elfmcys/yesstevemodel/client/animation/molang/functions/RideCheck.java', 'f9e00fda293f99fafa4182c8210a1fd19b4e15cf6197fdf847ba3f1511e67b32', 'f184edabd1b5115ce5a24cb6d155ba5a669f5ba6'), ('src/main/java/com/elfmcys/yesstevemodel/client/animation/condition/InnerClassify.java', '2d4a09ac8c4f9b3ada4cbbe703162d503886533d86819ed8d37d89e2b2b9f1e2', 'f184edabd1b5115ce5a24cb6d155ba5a669f5ba6')]

KEYS=('access','instructions','supplemental_full_operand_records','exception_handlers','code_sha256')
DECL=('access','super','interfaces','fields','methods')
def ident(m):return tuple(m.get(k) for k in ('owner','name','descriptor'))
def audit(e,actual,decl,details):
    checks=[]
    def ck(name,ok):checks.append({'check':name,'pass':bool(ok)})
    ck('fixed-artifact',e.get('artifact',{}).get('sha256')==SHA and e.get('artifact',{}).get('size')==SIZE)
    ck('detailed-operands',e.get('detailed_operands') is True)
    rows=e.get('members',[]);ids=[ident(m) for m in rows]
    ck('selected-21-methods',len(ids)==len(set(ids))==21 and set(ids)==set(actual)==SELECTED)
    for m in rows:
        a=actual.get(ident(m),{})
        for k in KEYS:ck(str(ident(m))+':'+k,(k in m)==(k in a) and m.get(k)==a.get(k))
    ds=e.get('owner_declarations',[]);ck('five-declarations',len(ds)==5 and {r['owner'] for r in ds}==set(OWNERS))
    for r in ds:ck(r['owner']+':declaration',r['declaration']==decl.get(r['owner']))
    bs=e.get('bootstrap_and_constant_evidence',[]);ck('five-bootstrap-records',len(bs)==5 and {r['owner'] for r in bs}==set(OWNERS))
    for r in bs:
        for k in ('constant_values','bootstrap_methods'):ck(r['owner']+':'+k,k in r and r[k]==details.get(r['owner'],{}).get(k))
    ss=e.get('source_tracks',[]);ck('five-fixed-source-records',sorted((r.get('path'),r.get('sha256'),r.get('revision')) for r in ss)==sorted(SOURCES))
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
    neg('missing-equipment-predicate-link-0',lambda x:member(x,0,'()Lcom/elfmcys/yesstevemodel/O0O0ooOOooOOO00OO0OOOooO;','Oo0Oo0o00O00Oo0OOoOOoooo')['instructions'].pop())
    neg('missing-equipment-predicate-link-2',lambda x:member(x,2,'()Lcom/elfmcys/yesstevemodel/o0oOOoO0oooo0O0OoOoOoOo0;','Oo0Oo0o00O00Oo0OOoOOoooo')['instructions'].pop())
    neg('missing-equipment-predicate-link-3',lambda x:member(x,3,'()Lcom/elfmcys/yesstevemodel/O000000ooOoOOo000ooO000o;','Oo0Oo0o00O00Oo0OOoOOoooo')['instructions'].pop())
    neg('missing-equipment-predicate-link-4',lambda x:member(x,4,'(Ljava/lang/String;Lnet/minecraft/world/entity/LivingEntity;Lnet/minecraft/world/InteractionHand;)Ljava/lang/String;','Oo0Oo0o00O00Oo0OOoOOoooo')['instructions'].pop())
    result={'artifact_sha256':SHA,'checks':checks,'negative_controls':negatives,'failures':[c for c in checks if not c['pass']],'negative_failures':[n for n in negatives if not n['rejected']],'independent_semantic_review':'NOT_RUN','runtime_executed':False,'central_mapping_promoted':False}
    Path(a.out).write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({'checks':len(checks),'negative_controls':len(negatives),'failures':len(result['failures'])+len(result['negative_failures'])}))
    if result['failures'] or result['negative_failures']:raise SystemExit(1)
if __name__=='__main__':main()
