#!/usr/bin/env python3
"""PROJECTILE-HIT-INPUT fixed-artifact integrity audit; does not execute target classes or independently prove prose semantics."""
import argparse,copy,hashlib,json,subprocess,zipfile
from pathlib import Path
from audit_seed_recovery_ysm_265 import parse_bounded,BOUNDDETAILS
from scan_ysm_265 import parse_class
SHA='25b5e902b96f4c298690208f8b433cbc31737c23f87590354dbd86f00207bc8f'
SIZE=63269843
OWNERS=['com/elfmcys/yesstevemodel/oo00O000000OoOo0O0O00oOO', 'com/elfmcys/yesstevemodel/oo00O000000OoOo0O0O00oOO$1', 'com/elfmcys/yesstevemodel/mixin/AbstractArrowEntityMixin', 'com/elfmcys/yesstevemodel/Oo0Oo0o00O00Oo0OOoOOoooo', 'com/elfmcys/yesstevemodel/mixin/client/FishingHookAccessor', 'com/elfmcys/yesstevemodel/mixin/client/ThrowableItemProjectileAccessor', 'com/elfmcys/yesstevemodel/mixin/client/ArrowEntityAccessor']
SELECTED=set([('com/elfmcys/yesstevemodel/oo00O000000OoOo0O0O00oOO', 'Oo0Oo0o00O00Oo0OOoOOoooo', '(Lcom/elfmcys/yesstevemodel/oo0oOO0000o0Ooooo0OoOo0O;)Ljava/lang/String;'), ('com/elfmcys/yesstevemodel/oo00O000000OoOo0O0O00oOO', 'o0OOooo0o0OO00OoOOOo0o0O', '(Lcom/elfmcys/yesstevemodel/oo0oOO0000o0Ooooo0OoOo0O;)Ljava/lang/String;'), ('com/elfmcys/yesstevemodel/oo00O000000OoOo0O0O00oOO', 'O00OOOooOoooOoo0o0o0oO0O', '(Lcom/elfmcys/yesstevemodel/oo0oOO0000o0Ooooo0OoOo0O;)Ljava/lang/String;'), ('com/elfmcys/yesstevemodel/oo00O000000OoOo0O0O00oOO', 'oOOOo0OOO0ooooo0O00OO0o0', '(Lcom/elfmcys/yesstevemodel/oo0oOO0000o0Ooooo0OoOo0O;)Ljava/lang/String;'), ('com/elfmcys/yesstevemodel/oo00O000000OoOo0O0O00oOO', 'OO0ooO00OoO00o0OO0OOooO0', '(Lcom/elfmcys/yesstevemodel/oo0oOO0000o0Ooooo0OoOo0O;)Ljava/lang/Object;'), ('com/elfmcys/yesstevemodel/oo00O000000OoOo0O0O00oOO', 'Ooo0O0000OO0OOO0o0Oo0oOO', '(Lcom/elfmcys/yesstevemodel/oo0oOO0000o0Ooooo0OoOo0O;)Ljava/lang/Object;'), ('com/elfmcys/yesstevemodel/oo00O000000OoOo0O0O00oOO', 'o0o0Oooo00OoOoOOOooo0000', '(Lcom/elfmcys/yesstevemodel/oo0oOO0000o0Ooooo0OoOo0O;)Ljava/lang/Object;'), ('com/elfmcys/yesstevemodel/oo00O000000OoOo0O0O00oOO', 'ooooO0o00oO0Oo0OOo0O0O0o', '(Lcom/elfmcys/yesstevemodel/oo0oOO0000o0Ooooo0OoOo0O;)Ljava/lang/Object;'), ('com/elfmcys/yesstevemodel/oo00O000000OoOo0O0O00oOO', 'oOOo0Ooo0oOoo0O0OOOOo0oo', '(Lcom/elfmcys/yesstevemodel/oo0oOO0000o0Ooooo0OoOo0O;)Ljava/lang/Object;'), ('com/elfmcys/yesstevemodel/oo00O000000OoOo0O0O00oOO$1', '<clinit>', '()V'), ('com/elfmcys/yesstevemodel/mixin/AbstractArrowEntityMixin', '<init>', '()V'), ('com/elfmcys/yesstevemodel/mixin/AbstractArrowEntityMixin', 'Oo0Oo0o00O00Oo0OOoOOoooo', '()Z'), ('com/elfmcys/yesstevemodel/mixin/AbstractArrowEntityMixin', 'o0OOooo0o0OO00OoOOOo0o0O', '()I'), ('com/elfmcys/yesstevemodel/mixin/AbstractArrowEntityMixin', 'O00OOOooOoooOoo0o0o0oO0O', '()Ljava/lang/String;'), ('com/elfmcys/yesstevemodel/mixin/AbstractArrowEntityMixin', 'Oo0Oo0o00O00Oo0OOoOOoooo', '(Lnet/minecraft/world/entity/Entity;Lorg/spongepowered/asm/mixin/injection/callback/CallbackInfo;)V'), ('com/elfmcys/yesstevemodel/Oo0Oo0o00O00Oo0OOoOOoooo', 'Oo0Oo0o00O00Oo0OOoOOoooo', '()Z'), ('com/elfmcys/yesstevemodel/Oo0Oo0o00O00Oo0OOoOOoooo', 'o0OOooo0o0OO00OoOOOo0o0O', '()I'), ('com/elfmcys/yesstevemodel/Oo0Oo0o00O00Oo0OOoOOoooo', 'O00OOOooOoooOoo0o0o0oO0O', '()Ljava/lang/String;'), ('com/elfmcys/yesstevemodel/mixin/client/FishingHookAccessor', 'Oo0Oo0o00O00Oo0OOoOOoooo', '()Z'), ('com/elfmcys/yesstevemodel/mixin/client/FishingHookAccessor', 'o0OOooo0o0OO00OoOOOo0o0O', '()Lnet/minecraft/world/entity/Entity;'), ('com/elfmcys/yesstevemodel/mixin/client/ThrowableItemProjectileAccessor', 'Oo0Oo0o00O00Oo0OOoOOoooo', '()Lnet/minecraft/world/item/Item;'), ('com/elfmcys/yesstevemodel/mixin/client/ArrowEntityAccessor', 'Oo0Oo0o00O00Oo0OOoOOoooo', '()Ljava/util/Set;')])
SOURCES=[('src/main/java/com/elfmcys/yesstevemodel/client/animation/molang/YSMBinding.java', '22bf1679ba5a8967b09109795fff207afdd2cb45ba34c4f70fb9ca4c9ca117a0', 'f184edabd1b5115ce5a24cb6d155ba5a669f5ba6'), ('src/main/java/com/elfmcys/yesstevemodel/client/animation/molang/YSMBinding.java', '22bf1679ba5a8967b09109795fff207afdd2cb45ba34c4f70fb9ca4c9ca117a0', 'f184edabd1b5115ce5a24cb6d155ba5a669f5ba6'), ('src/main/java/com/elfmcys/yesstevemodel/mixin/AbstractArrowEntityMixin.java', 'ec56c07b331c6fb68a64835a3832199782139529bd86daaa472f65bbacd247c3', 'f184edabd1b5115ce5a24cb6d155ba5a669f5ba6'), ('src/main/java/com/elfmcys/yesstevemodel/api/IArrowExtraInfo.java', 'c798e3917c373a80efd63bc68b07eb9ad513e405f9cf4ba006dfaa9e2a049066', 'f184edabd1b5115ce5a24cb6d155ba5a669f5ba6'), ('src/main/java/com/elfmcys/yesstevemodel/mixin/client/FishingHookAccessor.java', 'd8a991727e08b88a3f98ed1262ed81a3f6beefa347f8d199d317d793aa96a212', 'f184edabd1b5115ce5a24cb6d155ba5a669f5ba6'), ('src/main/java/com/elfmcys/yesstevemodel/mixin/client/ThrowableItemProjectileAccessor.java', '82d513e050c0367ed3f237cf2d7be698bef6ff35196c6df51a87f4fcaf29a370', 'f184edabd1b5115ce5a24cb6d155ba5a669f5ba6'), ('src/main/java/com/elfmcys/yesstevemodel/mixin/client/ArrowEntityAccessor.java', '85bda1c06fedab33dc3ed79a9df92c53999d6e12cb68dd6c49e34d4da8d225c3', 'f184edabd1b5115ce5a24cb6d155ba5a669f5ba6')]

KEYS=('access','instructions','supplemental_full_operand_records','exception_handlers','code_sha256')
DECL=('access','super','interfaces','fields','methods')
def ident(m):return tuple(m.get(k) for k in ('owner','name','descriptor'))
def audit(e,actual,decl,details):
    checks=[]
    def ck(name,ok):checks.append({'check':name,'pass':bool(ok)})
    ck('fixed-artifact',e.get('artifact',{}).get('sha256')==SHA and e.get('artifact',{}).get('size')==SIZE)
    ck('detailed-operands',e.get('detailed_operands') is True)
    rows=e.get('members',[]);ids=[ident(m) for m in rows]
    ck('selected-22-methods',len(ids)==len(set(ids))==22 and set(ids)==set(actual)==SELECTED)
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
    neg('missing-input-body-oo00O000000OoOo0O0O00oOO',lambda x:member(x,0,'(Lcom/elfmcys/yesstevemodel/oo0oOO0000o0Ooooo0OoOo0O;)Ljava/lang/Object;','oOOo0Ooo0oOoo0O0OOOOo0oo')['instructions'].pop())
    neg('missing-input-body-oo00O000000OoOo0O0O00oOO$1',lambda x:member(x,1,'()V','<clinit>')['instructions'].pop())
    neg('missing-input-body-mixin/AbstractArrowEntityMixin',lambda x:member(x,2,'(Lnet/minecraft/world/entity/Entity;Lorg/spongepowered/asm/mixin/injection/callback/CallbackInfo;)V','Oo0Oo0o00O00Oo0OOoOOoooo')['instructions'].pop())
    neg('missing-abstract-contract-Oo0Oo0o00O00Oo0OOoOOoooo',lambda x:x['owner_declarations'][3]['declaration']['methods'].pop())
    neg('missing-abstract-contract-mixin/client/FishingHookAccessor',lambda x:x['owner_declarations'][4]['declaration']['methods'].pop())
    neg('missing-abstract-contract-mixin/client/ThrowableItemProjectileAccessor',lambda x:x['owner_declarations'][5]['declaration']['methods'].pop())
    neg('missing-abstract-contract-mixin/client/ArrowEntityAccessor',lambda x:x['owner_declarations'][6]['declaration']['methods'].pop())
    result={'artifact_sha256':SHA,'checks':checks,'negative_controls':negatives,'failures':[c for c in checks if not c['pass']],'negative_failures':[n for n in negatives if not n['rejected']],'independent_semantic_review':'NOT_RUN','runtime_executed':False,'central_mapping_promoted':False}
    Path(a.out).write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({'checks':len(checks),'negative_controls':len(negatives),'failures':len(result['failures'])+len(result['negative_failures'])}))
    if result['failures'] or result['negative_failures']:raise SystemExit(1)
if __name__=='__main__':main()
