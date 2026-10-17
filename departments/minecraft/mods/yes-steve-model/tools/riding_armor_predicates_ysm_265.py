#!/usr/bin/env python3
"""RIDING-ARMOR-PREDICATES fixed-artifact integrity audit; does not execute target classes or independently prove prose semantics."""
import argparse,copy,hashlib,json,subprocess,zipfile
from pathlib import Path
from audit_seed_recovery_ysm_265 import parse_bounded,BOUNDDETAILS
from scan_ysm_265 import parse_class
SHA='25b5e902b96f4c298690208f8b433cbc31737c23f87590354dbd86f00207bc8f'
SIZE=63269843
OWNERS=['com/elfmcys/yesstevemodel/OOOo0oO00oOooooooOO00OOo', 'com/elfmcys/yesstevemodel/oOooO00oOO00OOO000oo00OO', 'com/elfmcys/yesstevemodel/OOo0ooo0oOOO0O0OoOOoO0OO', 'com/elfmcys/yesstevemodel/OOoo0OOooooOoo0OoO0oo00o', 'com/elfmcys/yesstevemodel/o0oOoOOo0ooo00Oo0oo0o00O', 'com/elfmcys/yesstevemodel/oo00O0OoO0o00000O0o000oo']
SELECTED=set([('com/elfmcys/yesstevemodel/OOOo0oO00oOooooooOO00OOo', '<init>', '()V'), ('com/elfmcys/yesstevemodel/OOOo0oO00oOooooooOO00OOo', 'Oo0Oo0o00O00Oo0OOoOOoooo', '(Lcom/elfmcys/yesstevemodel/OO00O0o0OooOOOo00OO00o00;Lcom/elfmcys/yesstevemodel/O0Oooo00oOo00O00OoOOOooO;)Lcom/elfmcys/yesstevemodel/O0oOo0OoO0O0o0000o0O00o0;'), ('com/elfmcys/yesstevemodel/OOOo0oO00oOooooooOO00OOo', 'Oo0Oo0o00O00Oo0OOoOOoooo', '(Lcom/elfmcys/yesstevemodel/OO00O0o0OooOOOo00OO00o00;)Lcom/elfmcys/yesstevemodel/O0oOo0OoO0O0o0000o0O00o0;'), ('com/elfmcys/yesstevemodel/oOooO00oOO00OOO000oo00OO', '<init>', '()V'), ('com/elfmcys/yesstevemodel/oOooO00oOO00OOO000oo00OO', 'Oo0Oo0o00O00Oo0OOoOOoooo', '(Lcom/elfmcys/yesstevemodel/OO00O0o0OooOOOo00OO00o00;Lcom/elfmcys/yesstevemodel/O0Oooo00oOo00O00OoOOOooO;)Lcom/elfmcys/yesstevemodel/O0oOo0OoO0O0o0000o0O00o0;'), ('com/elfmcys/yesstevemodel/OOo0ooo0oOOO0O0OoOOoO0OO', '<init>', '(Lnet/minecraft/world/entity/EquipmentSlot;)V'), ('com/elfmcys/yesstevemodel/OOo0ooo0oOOO0O0OoOOoO0OO', 'Oo0Oo0o00O00Oo0OOoOOoooo', '(Lcom/elfmcys/yesstevemodel/OO00O0o0OooOOOo00OO00o00;Lcom/elfmcys/yesstevemodel/O0Oooo00oOo00O00OoOOOooO;)Lcom/elfmcys/yesstevemodel/O0oOo0OoO0O0o0000o0O00o0;'), ('com/elfmcys/yesstevemodel/OOoo0OOooooOoo0OoO0oo00o', '<init>', '()V'), ('com/elfmcys/yesstevemodel/OOoo0OOooooOoo0OoO0oo00o', 'Oo0Oo0o00O00Oo0OOoOOoooo', '(Ljava/lang/String;)V'), ('com/elfmcys/yesstevemodel/OOoo0OOooooOoo0OoO0oo00o', 'Oo0Oo0o00O00Oo0OOoOOoooo', '(Lnet/minecraft/world/entity/LivingEntity;)Ljava/lang/String;'), ('com/elfmcys/yesstevemodel/OOoo0OOooooOoo0OoO0oo00o', 'Oo0Oo0o00O00Oo0OOoOOoooo', '(Lnet/minecraft/world/entity/Entity;)Ljava/lang/String;'), ('com/elfmcys/yesstevemodel/OOoo0OOooooOoo0OoO0oo00o', 'o0OOooo0o0OO00OoOOOo0o0O', '(Lnet/minecraft/world/entity/Entity;)Ljava/lang/String;'), ('com/elfmcys/yesstevemodel/OOoo0OOooooOoo0OoO0oo00o', 'Oo0Oo0o00O00Oo0OOoOOoooo', '(Lnet/minecraft/tags/TagKey;)Ljava/lang/String;'), ('com/elfmcys/yesstevemodel/OOoo0OOooooOoo0OoO0oo00o', 'Oo0Oo0o00O00Oo0OOoOOoooo', '(Lnet/minecraft/world/entity/Entity;Lnet/minecraft/tags/TagKey;)Z'), ('com/elfmcys/yesstevemodel/o0oOoOOo0ooo00Oo0oo0o00O', '<init>', '()V'), ('com/elfmcys/yesstevemodel/o0oOoOOo0ooo00Oo0oo0o00O', 'Oo0Oo0o00O00Oo0OOoOOoooo', '(Ljava/lang/String;)V'), ('com/elfmcys/yesstevemodel/o0oOoOOo0ooo00Oo0oo0o00O', 'Oo0Oo0o00O00Oo0OOoOOoooo', '(Lnet/minecraft/world/entity/LivingEntity;)Ljava/lang/String;'), ('com/elfmcys/yesstevemodel/o0oOoOOo0ooo00Oo0oo0o00O', 'Oo0Oo0o00O00Oo0OOoOOoooo', '(Lnet/minecraft/world/entity/Entity;)Ljava/lang/String;'), ('com/elfmcys/yesstevemodel/o0oOoOOo0ooo00Oo0oo0o00O', 'o0OOooo0o0OO00OoOOOo0o0O', '(Lnet/minecraft/world/entity/Entity;)Ljava/lang/String;'), ('com/elfmcys/yesstevemodel/o0oOoOOo0ooo00Oo0oo0o00O', 'Oo0Oo0o00O00Oo0OOoOOoooo', '(Lnet/minecraft/tags/TagKey;)Ljava/lang/String;'), ('com/elfmcys/yesstevemodel/o0oOoOOo0ooo00Oo0oo0o00O', 'Oo0Oo0o00O00Oo0OOoOOoooo', '(Lnet/minecraft/world/entity/Entity;Lnet/minecraft/tags/TagKey;)Z'), ('com/elfmcys/yesstevemodel/oo00O0OoO0o00000O0o000oo', '<init>', '()V'), ('com/elfmcys/yesstevemodel/oo00O0OoO0o00000O0o000oo', 'Oo0Oo0o00O00Oo0OOoOOoooo', '(Ljava/lang/String;)V'), ('com/elfmcys/yesstevemodel/oo00O0OoO0o00000O0o000oo', 'Oo0Oo0o00O00Oo0OOoOOoooo', '(Lnet/minecraft/world/entity/Entity;)Ljava/lang/String;'), ('com/elfmcys/yesstevemodel/oo00O0OoO0o00000O0o000oo', 'o0OOooo0o0OO00OoOOOo0o0O', '(Lnet/minecraft/world/entity/Entity;)Ljava/lang/String;')])
SOURCES=[('src/main/java/com/elfmcys/yesstevemodel/client/animation/predicate/VehiclePredicate.java', 'd5d2e72b703c450fa69bbee179537c067403e4f34bc973da9c7f0140ea9be331', 'f184edabd1b5115ce5a24cb6d155ba5a669f5ba6'), ('src/main/java/com/elfmcys/yesstevemodel/client/animation/predicate/PassengerPredicate.java', '50783490e834025b011090d505b2f137dcb998c1841d403aad83437a8212cba0', 'f184edabd1b5115ce5a24cb6d155ba5a669f5ba6'), ('src/main/java/com/elfmcys/yesstevemodel/client/animation/predicate/ArmorPredicate.java', '1cab8cdf5637239a0cd133ac093e7e4d08d6e2ffba2fdeb40888ea7b823304c0', 'f184edabd1b5115ce5a24cb6d155ba5a669f5ba6'), ('src/main/java/com/elfmcys/yesstevemodel/client/animation/condition/ConditionalVehicle.java', '80555e2439ba4a93fa6a83248fc276681353dcd64833301f2142211fb249ecf0', 'f184edabd1b5115ce5a24cb6d155ba5a669f5ba6'), ('src/main/java/com/elfmcys/yesstevemodel/client/animation/condition/ConditionalPassenger.java', 'aa60a2002df1159dc00139767c6fe0ed31212215a207628dad3db0c866502211', 'f184edabd1b5115ce5a24cb6d155ba5a669f5ba6'), ('src/main/java/com/elfmcys/yesstevemodel/client/animation/condition/ConditionalChair.java', 'f13322b1bb32a454203daa26b0b2c062083d70c951406adacead61839650cf48', 'f184edabd1b5115ce5a24cb6d155ba5a669f5ba6')]

KEYS=('access','instructions','supplemental_full_operand_records','exception_handlers','code_sha256')
DECL=('access','super','interfaces','fields','methods')
def ident(m):return tuple(m.get(k) for k in ('owner','name','descriptor'))
def audit(e,actual,decl,details):
    checks=[]
    def ck(name,ok):checks.append({'check':name,'pass':bool(ok)})
    ck('fixed-artifact',e.get('artifact',{}).get('sha256')==SHA and e.get('artifact',{}).get('size')==SIZE)
    ck('detailed-operands',e.get('detailed_operands') is True)
    rows=e.get('members',[]);ids=[ident(m) for m in rows]
    ck('selected-25-methods',len(ids)==len(set(ids))==25 and set(ids)==set(actual)==SELECTED)
    for m in rows:
        a=actual.get(ident(m),{})
        for k in KEYS:ck(str(ident(m))+':'+k,(k in m)==(k in a) and m.get(k)==a.get(k))
    ds=e.get('owner_declarations',[]);ck('six-declarations',len(ds)==6 and {r['owner'] for r in ds}==set(OWNERS))
    for r in ds:ck(r['owner']+':declaration',r['declaration']==decl.get(r['owner']))
    bs=e.get('bootstrap_and_constant_evidence',[]);ck('six-bootstrap-records',len(bs)==6 and {r['owner'] for r in bs}==set(OWNERS))
    for r in bs:
        for k in ('constant_values','bootstrap_methods'):ck(r['owner']+':'+k,k in r and r[k]==details.get(r['owner'],{}).get(k))
    ss=e.get('source_tracks',[]);ck('six-fixed-source-records',sorted((r.get('path'),r.get('sha256'),r.get('revision')) for r in ss)==sorted(SOURCES))
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
    neg('missing-riding-armor-link-0',lambda x:member(x,0,'(Lcom/elfmcys/yesstevemodel/OO00O0o0OooOOOo00OO00o00;Lcom/elfmcys/yesstevemodel/O0Oooo00oOo00O00OoOOOooO;)Lcom/elfmcys/yesstevemodel/O0oOo0OoO0O0o0000o0O00o0;','Oo0Oo0o00O00Oo0OOoOOoooo')['instructions'].pop())
    neg('missing-riding-armor-link-1',lambda x:member(x,1,'(Lcom/elfmcys/yesstevemodel/OO00O0o0OooOOOo00OO00o00;Lcom/elfmcys/yesstevemodel/O0Oooo00oOo00O00OoOOOooO;)Lcom/elfmcys/yesstevemodel/O0oOo0OoO0O0o0000o0O00o0;','Oo0Oo0o00O00Oo0OOoOOoooo')['instructions'].pop())
    neg('missing-riding-armor-link-2',lambda x:member(x,2,'(Lcom/elfmcys/yesstevemodel/OO00O0o0OooOOOo00OO00o00;Lcom/elfmcys/yesstevemodel/O0Oooo00oOo00O00OoOOOooO;)Lcom/elfmcys/yesstevemodel/O0oOo0OoO0O0o0000o0O00o0;','Oo0Oo0o00O00Oo0OOoOOoooo')['instructions'].pop())
    neg('missing-riding-armor-link-3',lambda x:member(x,3,'(Ljava/lang/String;)V','Oo0Oo0o00O00Oo0OOoOOoooo')['instructions'].pop())
    neg('missing-riding-armor-link-4',lambda x:member(x,4,'(Ljava/lang/String;)V','Oo0Oo0o00O00Oo0OOoOOoooo')['instructions'].pop())
    neg('missing-riding-armor-link-5',lambda x:member(x,5,'(Ljava/lang/String;)V','Oo0Oo0o00O00Oo0OOoOOoooo')['instructions'].pop())
    result={'artifact_sha256':SHA,'checks':checks,'negative_controls':negatives,'failures':[c for c in checks if not c['pass']],'negative_failures':[n for n in negatives if not n['rejected']],'independent_semantic_review':'NOT_RUN','runtime_executed':False,'central_mapping_promoted':False}
    Path(a.out).write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({'checks':len(checks),'negative_controls':len(negatives),'failures':len(result['failures'])+len(result['negative_failures'])}))
    if result['failures'] or result['negative_failures']:raise SystemExit(1)
if __name__=='__main__':main()
