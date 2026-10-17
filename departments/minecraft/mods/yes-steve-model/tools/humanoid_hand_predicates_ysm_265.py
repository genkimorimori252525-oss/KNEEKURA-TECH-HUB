#!/usr/bin/env python3
"""HUMANOID-HAND-PREDICATES fixed-artifact integrity audit; does not execute target classes or independently prove prose semantics."""
import argparse,copy,hashlib,json,subprocess,zipfile
from pathlib import Path
from audit_seed_recovery_ysm_265 import parse_bounded,BOUNDDETAILS
from scan_ysm_265 import parse_class
SHA='25b5e902b96f4c298690208f8b433cbc31737c23f87590354dbd86f00207bc8f'
SIZE=63269843
OWNERS=['com/elfmcys/yesstevemodel/oOO0000O0oO0o0OooOOO0oO0', 'com/elfmcys/yesstevemodel/OoOO00O00O0o0OooOoO0O0oo', 'com/elfmcys/yesstevemodel/OOooo0o00o0Oo0O0ooO0OoO0', 'com/elfmcys/yesstevemodel/oOooO00OOoOoOOoo0OoOOOOO', 'com/elfmcys/yesstevemodel/oOO0o0o00o00Oo00oO00OooO', 'com/elfmcys/yesstevemodel/oo00oOO00o0OOo0oO0OOOO00', 'com/elfmcys/yesstevemodel/oo00OoO0Oo0OO0oOoOoOoOo0']
SELECTED=set([('com/elfmcys/yesstevemodel/oOO0000O0oO0o0OooOOO0oO0', '<init>', '()V'), ('com/elfmcys/yesstevemodel/oOO0000O0oO0o0OooOOO0oO0', 'Oo0Oo0o00O00Oo0OOoOOoooo', '(Lcom/elfmcys/yesstevemodel/OO00O0o0OooOOOo00OO00o00;Lcom/elfmcys/yesstevemodel/O0Oooo00oOo00O00OoOOOooO;)Lcom/elfmcys/yesstevemodel/O0oOo0OoO0O0o0000o0O00o0;'), ('com/elfmcys/yesstevemodel/oOO0000O0oO0o0OooOOO0oO0', 'Oo0Oo0o00O00Oo0OOoOOoooo', '(Lnet/minecraft/world/item/ItemStack;Lcom/elfmcys/yesstevemodel/oo00oOO00o0OOo0oO0OOOO00;Lnet/minecraft/world/InteractionHand;)Z'), ('com/elfmcys/yesstevemodel/oOO0000O0oO0o0OooOOO0oO0', 'Oo0Oo0o00O00Oo0OOoOOoooo', '(Lnet/minecraft/world/entity/LivingEntity;Lnet/minecraft/world/InteractionHand;)Z'), ('com/elfmcys/yesstevemodel/OoOO00O00O0o0OooOoO0O0oo', '<init>', '()V'), ('com/elfmcys/yesstevemodel/OoOO00O00O0o0OooOoO0O0oo', 'Oo0Oo0o00O00Oo0OOoOOoooo', '(Lcom/elfmcys/yesstevemodel/OO00O0o0OooOOOo00OO00o00;Lcom/elfmcys/yesstevemodel/O0Oooo00oOo00O00OoOOOooO;)Lcom/elfmcys/yesstevemodel/O0oOo0OoO0O0o0000o0O00o0;'), ('com/elfmcys/yesstevemodel/OoOO00O00O0o0OooOoO0O0oo', 'Oo0Oo0o00O00Oo0OOoOOoooo', '(Lnet/minecraft/world/item/ItemStack;Lcom/elfmcys/yesstevemodel/oo00oOO00o0OOo0oO0OOOO00;Lnet/minecraft/world/InteractionHand;)Z'), ('com/elfmcys/yesstevemodel/OoOO00O00O0o0OooOoO0O0oo', 'Oo0Oo0o00O00Oo0OOoOOoooo', '(Lnet/minecraft/world/entity/LivingEntity;Lnet/minecraft/world/InteractionHand;)Z'), ('com/elfmcys/yesstevemodel/OOooo0o00o0Oo0O0ooO0OoO0', '<init>', '()V'), ('com/elfmcys/yesstevemodel/OOooo0o00o0Oo0O0ooO0OoO0', 'Oo0Oo0o00O00Oo0OOoOOoooo', '(Lcom/elfmcys/yesstevemodel/OO00O0o0OooOOOo00OO00o00;Lcom/elfmcys/yesstevemodel/O0Oooo00oOo00O00OoOOOooO;)Lcom/elfmcys/yesstevemodel/O0oOo0OoO0O0o0000o0O00o0;'), ('com/elfmcys/yesstevemodel/oOooO00OOoOoOOoo0OoOOOOO', '<init>', '()V'), ('com/elfmcys/yesstevemodel/oOooO00OOoOoOOoo0OoOOOOO', 'Oo0Oo0o00O00Oo0OOoOOoooo', '(Lcom/elfmcys/yesstevemodel/OO00O0o0OooOOOo00OO00o00;Lcom/elfmcys/yesstevemodel/O0Oooo00oOo00O00OoOOOooO;)Lcom/elfmcys/yesstevemodel/O0oOo0OoO0O0o0000o0O00o0;'), ('com/elfmcys/yesstevemodel/oOO0o0o00o00Oo00oO00OooO', '<init>', '()V'), ('com/elfmcys/yesstevemodel/oOO0o0o00o00Oo00oO00OooO', 'Oo0Oo0o00O00Oo0OOoOOoooo', '(Lcom/elfmcys/yesstevemodel/OO00O0o0OooOOOo00OO00o00;Ljava/lang/String;I)Z'), ('com/elfmcys/yesstevemodel/oo00oOO00o0OOo0oO0OOOO00', '<init>', '(Lnet/minecraft/world/entity/LivingEntity;)V'), ('com/elfmcys/yesstevemodel/oo00oOO00o0OOo0oO0OOOO00', 'Oo0Oo0o00O00Oo0OOoOOoooo', '()V'), ('com/elfmcys/yesstevemodel/oo00oOO00o0OOo0oO0OOOO00', 'Oo0Oo0o00O00Oo0OOoOOoooo', '(FFF)V'), ('com/elfmcys/yesstevemodel/oo00oOO00o0OOo0oO0OOOO00', 'Oo0Oo0o00O00Oo0OOoOOoooo', '(Lnet/minecraft/world/InteractionHand;)Lnet/minecraft/world/item/ItemStack;'), ('com/elfmcys/yesstevemodel/oo00oOO00o0OOo0oO0OOOO00', 'Oo0Oo0o00O00Oo0OOoOOoooo', '(Lnet/minecraft/world/item/ItemStack;Lnet/minecraft/world/InteractionHand;)V'), ('com/elfmcys/yesstevemodel/oo00oOO00o0OOo0oO0OOOO00', 'ooOO000o0O0OOOoO0Oo0o0Oo', '()Lcom/elfmcys/yesstevemodel/oO000OOooo0Oo0OOO0Ooo00o$Oo0Oo0o00O00Oo0OOoOOoooo;'), ('com/elfmcys/yesstevemodel/oo00OoO0Oo0OO0oOoOoOoOo0', '<init>', '(Lnet/minecraft/world/InteractionHand;)V'), ('com/elfmcys/yesstevemodel/oo00OoO0Oo0OO0oOoOoOoOo0', 'Oo0Oo0o00O00Oo0OOoOOoooo', '(Ljava/lang/String;)V'), ('com/elfmcys/yesstevemodel/oo00OoO0Oo0OO0oOoOoOoOo0', 'Oo0Oo0o00O00Oo0OOoOOoooo', '(Lnet/minecraft/world/entity/LivingEntity;Lnet/minecraft/world/InteractionHand;)Ljava/lang/String;'), ('com/elfmcys/yesstevemodel/oo00OoO0Oo0OO0oOoOoOoOo0', 'o0OOooo0o0OO00OoOOOo0o0O', '(Lnet/minecraft/world/entity/LivingEntity;Lnet/minecraft/world/InteractionHand;)Ljava/lang/String;'), ('com/elfmcys/yesstevemodel/oo00OoO0Oo0OO0oOoOoOoOo0', 'O00OOOooOoooOoo0o0o0oO0O', '(Lnet/minecraft/world/entity/LivingEntity;Lnet/minecraft/world/InteractionHand;)Ljava/lang/String;'), ('com/elfmcys/yesstevemodel/oo00OoO0Oo0OO0oOoOoOoOo0', 'oOOOo0OOO0ooooo0O00OO0o0', '(Lnet/minecraft/world/entity/LivingEntity;Lnet/minecraft/world/InteractionHand;)Ljava/lang/String;'), ('com/elfmcys/yesstevemodel/oo00OoO0Oo0OO0oOoOoOoOo0', 'Oo0Oo0o00O00Oo0OOoOOoooo', '(Lnet/minecraft/tags/TagKey;)Ljava/lang/String;')])
SOURCES=[('src/main/java/com/elfmcys/yesstevemodel/client/animation/predicate/MainhandPredicate.java', 'd49f11f4100e38a7c959922936a798ab0db6eb5c9fb3cbaa36699d28b847e896', 'f184edabd1b5115ce5a24cb6d155ba5a669f5ba6'), ('src/main/java/com/elfmcys/yesstevemodel/client/animation/predicate/OffhandPredicate.java', 'ac2312caadf76e46ab011d10d81ba2fc5f4b6f54c766e7ff3f0cde599fb53a5b', 'f184edabd1b5115ce5a24cb6d155ba5a669f5ba6'), ('src/main/java/com/elfmcys/yesstevemodel/client/animation/predicate/SwingPredicate.java', 'b8b0b8cc5849f099a675ffa952922e1e2d5cadc0727b6909e41efb233231267a', 'f184edabd1b5115ce5a24cb6d155ba5a669f5ba6'), ('src/main/java/com/elfmcys/yesstevemodel/client/animation/predicate/UsePredicate.java', '226324ebeafeffc3d301800cd2651151c2d2be873ce7db1b1fa55d01e44b9241', 'f184edabd1b5115ce5a24cb6d155ba5a669f5ba6'), ('src/main/java/com/elfmcys/yesstevemodel/info/ModelFormatVersion.java', '90adc4bcd0ea97d9fe1961e4d3ec92c76b9831684d3e1f32ea958ce61b924479', 'f184edabd1b5115ce5a24cb6d155ba5a669f5ba6'), ('src/main/java/com/elfmcys/yesstevemodel/client/entity/HumanoidStateTracker.java', '4494778d9883d5bec560639b2f5f11d2e6e1d0faf5b9d29f88a2113196016762', 'f184edabd1b5115ce5a24cb6d155ba5a669f5ba6'), ('src/main/java/com/elfmcys/yesstevemodel/client/animation/condition/ConditionalHold.java', 'f9a4002dff5451550b7bd188f4b55994bc4e98d0766a9e1bb3537b526176fde5', 'f184edabd1b5115ce5a24cb6d155ba5a669f5ba6')]

KEYS=('access','instructions','supplemental_full_operand_records','exception_handlers','code_sha256')
DECL=('access','super','interfaces','fields','methods')
def ident(m):return tuple(m.get(k) for k in ('owner','name','descriptor'))
def audit(e,actual,decl,details):
    checks=[]
    def ck(name,ok):checks.append({'check':name,'pass':bool(ok)})
    ck('fixed-artifact',e.get('artifact',{}).get('sha256')==SHA and e.get('artifact',{}).get('size')==SIZE)
    ck('detailed-operands',e.get('detailed_operands') is True)
    rows=e.get('members',[]);ids=[ident(m) for m in rows]
    ck('selected-27-methods',len(ids)==len(set(ids))==27 and set(ids)==set(actual)==SELECTED)
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
    neg('missing-hand-predicate-link-0',lambda x:member(x,0,'(Lcom/elfmcys/yesstevemodel/OO00O0o0OooOOOo00OO00o00;Lcom/elfmcys/yesstevemodel/O0Oooo00oOo00O00OoOOOooO;)Lcom/elfmcys/yesstevemodel/O0oOo0OoO0O0o0000o0O00o0;','Oo0Oo0o00O00Oo0OOoOOoooo')['instructions'].pop())
    neg('missing-hand-predicate-link-1',lambda x:member(x,1,'(Lcom/elfmcys/yesstevemodel/OO00O0o0OooOOOo00OO00o00;Lcom/elfmcys/yesstevemodel/O0Oooo00oOo00O00OoOOOooO;)Lcom/elfmcys/yesstevemodel/O0oOo0OoO0O0o0000o0O00o0;','Oo0Oo0o00O00Oo0OOoOOoooo')['instructions'].pop())
    neg('missing-hand-predicate-link-2',lambda x:member(x,2,'(Lcom/elfmcys/yesstevemodel/OO00O0o0OooOOOo00OO00o00;Lcom/elfmcys/yesstevemodel/O0Oooo00oOo00O00OoOOOooO;)Lcom/elfmcys/yesstevemodel/O0oOo0OoO0O0o0000o0O00o0;','Oo0Oo0o00O00Oo0OOoOOoooo')['instructions'].pop())
    neg('missing-hand-predicate-link-3',lambda x:member(x,3,'(Lcom/elfmcys/yesstevemodel/OO00O0o0OooOOOo00OO00o00;Lcom/elfmcys/yesstevemodel/O0Oooo00oOo00O00OoOOOooO;)Lcom/elfmcys/yesstevemodel/O0oOo0OoO0O0o0000o0O00o0;','Oo0Oo0o00O00Oo0OOoOOoooo')['instructions'].pop())
    neg('missing-hand-predicate-link-4',lambda x:member(x,4,'(Lcom/elfmcys/yesstevemodel/OO00O0o0OooOOOo00OO00o00;Ljava/lang/String;I)Z','Oo0Oo0o00O00Oo0OOoOOoooo')['instructions'].pop())
    neg('missing-hand-predicate-link-5',lambda x:member(x,5,'()V','Oo0Oo0o00O00Oo0OOoOOoooo')['instructions'].pop())
    neg('missing-hand-predicate-link-6',lambda x:member(x,6,'(Ljava/lang/String;)V','Oo0Oo0o00O00Oo0OOoOOoooo')['instructions'].pop())
    result={'artifact_sha256':SHA,'checks':checks,'negative_controls':negatives,'failures':[c for c in checks if not c['pass']],'negative_failures':[n for n in negatives if not n['rejected']],'independent_semantic_review':'NOT_RUN','runtime_executed':False,'central_mapping_promoted':False}
    Path(a.out).write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({'checks':len(checks),'negative_controls':len(negatives),'failures':len(result['failures'])+len(result['negative_failures'])}))
    if result['failures'] or result['negative_failures']:raise SystemExit(1)
if __name__=='__main__':main()
