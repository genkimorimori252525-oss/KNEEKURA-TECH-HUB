#!/usr/bin/env python3
"""RESOURCE-ARGUMENT-ADAPTER fixed-artifact integrity audit; does not execute target classes or independently prove prose semantics."""
import argparse,copy,hashlib,json,subprocess,zipfile
from pathlib import Path
from audit_seed_recovery_ysm_265 import parse_bounded,BOUNDDETAILS
from scan_ysm_265 import parse_class
SHA='25b5e902b96f4c298690208f8b433cbc31737c23f87590354dbd86f00207bc8f'
SIZE=63269843
OWNERS=['com/elfmcys/yesstevemodel/O00OOo00o0O00ooo000OOo0O$Oo0Oo0o00O00Oo0OOoOOoooo', 'com/elfmcys/yesstevemodel/oo0OoOoOoOo0oOoooo0oOOo0', 'com/elfmcys/yesstevemodel/oO0OoOOO0o000o0Oo000000O', 'com/elfmcys/yesstevemodel/OOo0OO0o00o00O0OOO0o00OO', 'com/elfmcys/yesstevemodel/oo00Oo00o0ooooOooo0Oo0OO', 'com/elfmcys/yesstevemodel/OO0O00ooOo0OO0oooOoo0Oo0']
SELECTED=set([('com/elfmcys/yesstevemodel/O00OOo00o0O00ooo000OOo0O$Oo0Oo0o00O00Oo0OOoOOoooo', '<init>', '(Ljava/util/List;)V'), ('com/elfmcys/yesstevemodel/O00OOo00o0O00ooo000OOo0O$Oo0Oo0o00O00Oo0OOoOOoooo', 'Oo0Oo0o00O00Oo0OOoOOoooo', '()I'), ('com/elfmcys/yesstevemodel/O00OOo00o0O00ooo000OOo0O$Oo0Oo0o00O00Oo0OOoOOoooo', 'Oo0Oo0o00O00Oo0OOoOOoooo', '(Lcom/elfmcys/yesstevemodel/oO0OoO0O0OoO0oo0oo0OOooo;I)Ljava/lang/String;'), ('com/elfmcys/yesstevemodel/O00OOo00o0O00ooo000OOo0O$Oo0Oo0o00O00Oo0OOoOOoooo', 'o0OOooo0o0OO00OoOOOo0o0O', '(Lcom/elfmcys/yesstevemodel/oO0OoO0O0OoO0oo0oo0OOooo;I)I'), ('com/elfmcys/yesstevemodel/O00OOo00o0O00ooo000OOo0O$Oo0Oo0o00O00Oo0OOoOOoooo', 'O00OOOooOoooOoo0o0o0oO0O', '(Lcom/elfmcys/yesstevemodel/oO0OoO0O0OoO0oo0oo0OOooo;I)D'), ('com/elfmcys/yesstevemodel/O00OOo00o0O00ooo000OOo0O$Oo0Oo0o00O00Oo0OOoOOoooo', 'oOOOo0OOO0ooooo0O00OO0o0', '(Lcom/elfmcys/yesstevemodel/oO0OoO0O0OoO0oo0oo0OOooo;I)I'), ('com/elfmcys/yesstevemodel/O00OOo00o0O00ooo000OOo0O$Oo0Oo0o00O00Oo0OOoOOoooo', 'OOOOo0O0oO0OOo0O0O0Oo0O0', '(Lcom/elfmcys/yesstevemodel/oO0OoO0O0OoO0oo0oo0OOooo;I)F'), ('com/elfmcys/yesstevemodel/O00OOo00o0O00ooo000OOo0O$Oo0Oo0o00O00Oo0OOoOOoooo', 'Ooooo0oooO0oooOOOoO0000O', '(Lcom/elfmcys/yesstevemodel/oO0OoO0O0OoO0oo0oo0OOooo;I)Z'), ('com/elfmcys/yesstevemodel/O00OOo00o0O00ooo000OOo0O$Oo0Oo0o00O00Oo0OOoOOoooo', 'oo0OoO00oOoo000O0000o0oo', '(Lcom/elfmcys/yesstevemodel/oO0OoO0O0OoO0oo0oo0OOooo;I)Lnet/minecraft/resources/ResourceLocation;'), ('com/elfmcys/yesstevemodel/O00OOo00o0O00ooo000OOo0O$Oo0Oo0o00O00Oo0OOoOOoooo', 'oooooooOOoOOoO00OooOo00O', '(Lcom/elfmcys/yesstevemodel/oO0OoO0O0OoO0oo0oo0OOooo;I)Ljava/lang/Object;'), ('com/elfmcys/yesstevemodel/O00OOo00o0O00ooo000OOo0O$Oo0Oo0o00O00Oo0OOoOOoooo', 'Oo0Oo0o00O00Oo0OOoOOoooo', '(I)Lcom/elfmcys/yesstevemodel/oOOOOoo0O0Oo0O00oo0oooO0;'), ('com/elfmcys/yesstevemodel/oo0OoOoOoOo0oOoooo0oOOo0', '<init>', '(Ljava/lang/String;)V'), ('com/elfmcys/yesstevemodel/oo0OoOoOoOo0oOoooo0oOOo0', 'Oo0Oo0o00O00Oo0OOoOOoooo', '()Ljava/lang/String;'), ('com/elfmcys/yesstevemodel/oo0OoOoOoOo0oOoooo0oOOo0', 'o0OOooo0o0OO00OoOOOo0o0O', '()I'), ('com/elfmcys/yesstevemodel/oo0OoOoOoOo0oOoooo0oOOo0', 'Oo0Oo0o00O00Oo0OOoOOoooo', '(Lcom/elfmcys/yesstevemodel/Oo0000oo0oo0OoO00000O0O0;)Ljava/lang/Object;'), ('com/elfmcys/yesstevemodel/oo0OoOoOoOo0oOoooo0oOOo0', 'toString', '()Ljava/lang/String;'), ('com/elfmcys/yesstevemodel/oo0OoOoOoOo0oOoooo0oOOo0', 'O00OOOooOoooOoo0o0o0oO0O', '()Lnet/minecraft/resources/ResourceLocation;'), ('com/elfmcys/yesstevemodel/oo0OoOoOoOo0oOoooo0oOOo0', 'Oo0Oo0o00O00Oo0OOoOOoooo', '(Lnet/minecraft/resources/ResourceLocation;)V'), ('com/elfmcys/yesstevemodel/oo0OoOoOoOo0oOoooo0oOOo0', 'equals', '(Ljava/lang/Object;)Z'), ('com/elfmcys/yesstevemodel/oo0OoOoOoOo0oOoooo0oOOo0', 'hashCode', '()I'), ('com/elfmcys/yesstevemodel/oO0OoOOO0o000o0Oo000000O', '<init>', '()V'), ('com/elfmcys/yesstevemodel/oO0OoOOO0o000o0Oo000000O', 'Oo0Oo0o00O00Oo0OOoOOoooo', '()V'), ('com/elfmcys/yesstevemodel/oO0OoOOO0o000o0Oo000000O', 'o0OOooo0o0OO00OoOOOo0o0O', '()Z'), ('com/elfmcys/yesstevemodel/oO0OoOOO0o000o0Oo000000O', 'Oo0Oo0o00O00Oo0OOoOOoooo', '(Lnet/minecraft/world/entity/player/Player;Lnet/minecraft/world/entity/EquipmentSlot;)Ljava/util/Optional;'), ('com/elfmcys/yesstevemodel/OOo0OO0o00o00O0OOO0o00OO', '<init>', '()V'), ('com/elfmcys/yesstevemodel/OOo0OO0o00o00O0OOO0o00OO', 'Oo0Oo0o00O00Oo0OOoOOoooo', '()V'), ('com/elfmcys/yesstevemodel/OOo0OO0o00o00O0OOO0o00OO', 'o0OOooo0o0OO00OoOOOo0o0O', '()Z'), ('com/elfmcys/yesstevemodel/OOo0OO0o00o00O0OOO0o00OO', 'Oo0Oo0o00O00Oo0OOoOOoooo', '(Lnet/minecraft/world/entity/LivingEntity;)Lnet/minecraft/world/item/ItemStack;'), ('com/elfmcys/yesstevemodel/oo00Oo00o0ooooOooo0Oo0OO', 'Oo0Oo0o00O00Oo0OOoOOoooo', '(Lcom/elfmcys/yesstevemodel/oo0OoOoOoOo0oOoooo0oOOo0;)Ljava/lang/Object;'), ('com/elfmcys/yesstevemodel/OO0O00ooOo0OO0oooOoo0Oo0', 'OOOOo0O0oO0OOo0O0O0Oo0O0', '(Ljava/lang/Object;)Ljava/lang/String;'), ('com/elfmcys/yesstevemodel/OO0O00ooOo0OO0oooOoo0Oo0', 'Ooooo0oooO0oooOOOoO0000O', '(Ljava/lang/Object;)I')])
SOURCES=[('src/main/java/com/elfmcys/yesstevemodel/molang/runtime/Function.java', '66e683e3b7e342e5fb5706c67409e88bcc3cb243eb89486ae85bc0597f44fff4', 'f184edabd1b5115ce5a24cb6d155ba5a669f5ba6'), ('src/main/java/com/elfmcys/yesstevemodel/molang/parser/ast/StringExpression.java', 'cc1d016a328939bd9a41e76f3da37f7a898bb71eae123167d71b1b86bc5a3386', 'f184edabd1b5115ce5a24cb6d155ba5a669f5ba6'), ('src/main/java/com/elfmcys/yesstevemodel/client/compat/CosmeticArmorCompat.java', '0840e9bf0a9cc2b1e31cc695f075d74e1066ba81d141fa9f6034ec23c125f0c5', 'f184edabd1b5115ce5a24cb6d155ba5a669f5ba6'), ('src/main/java/com/elfmcys/yesstevemodel/client/compat/ElytraSlotCompat.java', 'c3c54fb4b2c92b053c28b7a2879e37bc4453412314ebb96d18d29f6b8e40facf', 'f184edabd1b5115ce5a24cb6d155ba5a669f5ba6'), ('src/main/java/com/elfmcys/yesstevemodel/molang/runtime/ExpressionEvaluatorImpl.java', 'b1f5667dd9fc2e6b61d46fba8f66bc9ab51854e555fc192561ea552654febc2e', 'f184edabd1b5115ce5a24cb6d155ba5a669f5ba6'), ('src/main/java/com/elfmcys/yesstevemodel/molang/runtime/binding/ValueConversions.java', '3eb91e8a0c75cb893fed4a2607e3e9e680e2c94e88ad0b655822b1200ac365ff', 'f184edabd1b5115ce5a24cb6d155ba5a669f5ba6')]

KEYS=('access','instructions','supplemental_full_operand_records','exception_handlers','code_sha256')
DECL=('access','super','interfaces','fields','methods')
def ident(m):return tuple(m.get(k) for k in ('owner','name','descriptor'))
def audit(e,actual,decl,details):
    checks=[]
    def ck(name,ok):checks.append({'check':name,'pass':bool(ok)})
    ck('fixed-artifact',e.get('artifact',{}).get('sha256')==SHA and e.get('artifact',{}).get('size')==SIZE)
    ck('detailed-operands',e.get('detailed_operands') is True)
    rows=e.get('members',[]);ids=[ident(m) for m in rows]
    ck('selected-31-methods',len(ids)==len(set(ids))==31 and set(ids)==set(actual)==SELECTED)
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
    neg('missing-query-support-O00OOo00o0O00ooo000OOo0O$Oo0Oo0o00O00Oo0OOoOOoooo',lambda x:member(x,0,'()I','Oo0Oo0o00O00Oo0OOoOOoooo')['instructions'].pop())
    neg('missing-query-support-oo0OoOoOoOo0oOoooo0oOOo0',lambda x:member(x,1,'()Ljava/lang/String;','Oo0Oo0o00O00Oo0OOoOOoooo')['instructions'].pop())
    neg('missing-query-support-oO0OoOOO0o000o0Oo000000O',lambda x:member(x,2,'()V','Oo0Oo0o00O00Oo0OOoOOoooo')['instructions'].pop())
    neg('missing-query-support-OOo0OO0o00o00O0OOO0o00OO',lambda x:member(x,3,'()V','Oo0Oo0o00O00Oo0OOoOOoooo')['instructions'].pop())
    neg('missing-query-support-oo00Oo00o0ooooOooo0Oo0OO',lambda x:member(x,4,'(Lcom/elfmcys/yesstevemodel/oo0OoOoOoOo0oOoooo0oOOo0;)Ljava/lang/Object;','Oo0Oo0o00O00Oo0OOoOOoooo')['instructions'].pop())
    neg('missing-query-support-OO0O00ooOo0OO0oooOoo0Oo0',lambda x:member(x,5,'(Ljava/lang/Object;)Ljava/lang/String;','OOOOo0O0oO0OOo0O0O0Oo0O0')['instructions'].pop())
    neg('resource-cache-hit-gate-inverted',lambda x:op(x,0,'(Lcom/elfmcys/yesstevemodel/oO0OoO0O0OoO0oo0oo0OOooo;I)Lnet/minecraft/resources/ResourceLocation;',25).update(opcode='0xc7'))
    result={'artifact_sha256':SHA,'checks':checks,'negative_controls':negatives,'failures':[c for c in checks if not c['pass']],'negative_failures':[n for n in negatives if not n['rejected']],'independent_semantic_review':'NOT_RUN','runtime_executed':False,'central_mapping_promoted':False}
    Path(a.out).write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({'checks':len(checks),'negative_controls':len(negatives),'failures':len(result['failures'])+len(result['negative_failures'])}))
    if result['failures'] or result['negative_failures']:raise SystemExit(1)
if __name__=='__main__':main()
