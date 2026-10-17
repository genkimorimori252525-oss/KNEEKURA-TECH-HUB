#!/usr/bin/env python3
"""TYPED-FUNCTION-GUARDS fixed-artifact integrity audit; does not execute target classes or independently prove prose semantics."""
import argparse,copy,hashlib,json,subprocess,zipfile
from pathlib import Path
from audit_seed_recovery_ysm_265 import parse_bounded,BOUNDDETAILS
from scan_ysm_265 import parse_class
SHA='25b5e902b96f4c298690208f8b433cbc31737c23f87590354dbd86f00207bc8f'
SIZE=63269843
OWNERS=['com/elfmcys/yesstevemodel/O00OoOOOo0o0ooooo0OO0OOO', 'com/elfmcys/yesstevemodel/O00o0Oo0O0oooOooOo0O0o00', 'com/elfmcys/yesstevemodel/O00oOoo00OOOO0Oo0oo00o0o', 'com/elfmcys/yesstevemodel/O0OO00o0OO000o00OOOoOO00', 'com/elfmcys/yesstevemodel/OO000oo0o000OooOoo00O0OO', 'com/elfmcys/yesstevemodel/OOOoo00ooO000oOOoO0OO000', 'com/elfmcys/yesstevemodel/o0000O00oo00oOOooO0oO0oO', 'com/elfmcys/yesstevemodel/o000OOOo000O00o000O0ooo0', 'com/elfmcys/yesstevemodel/o0ooOO00oOoO000oooO00o0o', 'com/elfmcys/yesstevemodel/oOOooOO0O0OoOOoOO00ooO0o', 'com/elfmcys/yesstevemodel/oo0000oOOoOo0OoOOOOoO0o0', 'com/elfmcys/yesstevemodel/ooO00OOOOOo0oOoooO00oOoO', 'com/elfmcys/yesstevemodel/ooO0oo0OOOoo0000O0OoooO0', 'com/elfmcys/yesstevemodel/o0oOo0o000oOo00OO000OOoO']
SELECTED=set([('com/elfmcys/yesstevemodel/O00OoOOOo0o0ooooo0OO0OOO', '<init>', '()V'), ('com/elfmcys/yesstevemodel/O00OoOOOo0o0ooooo0OO0OOO', 'Oo0Oo0o00O00Oo0OOoOOoooo', '(Lcom/elfmcys/yesstevemodel/oo0oOO0000o0Ooooo0OoOo0O;)Z'), ('com/elfmcys/yesstevemodel/O00o0Oo0O0oooOooOo0O0o00', '<init>', '()V'), ('com/elfmcys/yesstevemodel/O00o0Oo0O0oooOooOo0O0o00', 'Oo0Oo0o00O00Oo0OOoOOoooo', '(Lcom/elfmcys/yesstevemodel/oo0oOO0000o0Ooooo0OoOo0O;)Z'), ('com/elfmcys/yesstevemodel/O00oOoo00OOOO0Oo0oo00o0o', '<init>', '()V'), ('com/elfmcys/yesstevemodel/O00oOoo00OOOO0Oo0oo00o0o', 'Oo0Oo0o00O00Oo0OOoOOoooo', '(Lcom/elfmcys/yesstevemodel/oo0oOO0000o0Ooooo0OoOo0O;)Z'), ('com/elfmcys/yesstevemodel/O0OO00o0OO000o00OOOoOO00', '<init>', '()V'), ('com/elfmcys/yesstevemodel/O0OO00o0OO000o00OOOoOO00', 'Oo0Oo0o00O00Oo0OOoOOoooo', '(Lcom/elfmcys/yesstevemodel/oo0oOO0000o0Ooooo0OoOo0O;)Z'), ('com/elfmcys/yesstevemodel/OO000oo0o000OooOoo00O0OO', '<init>', '()V'), ('com/elfmcys/yesstevemodel/OO000oo0o000OooOoo00O0OO', 'Oo0Oo0o00O00Oo0OOoOOoooo', '(Lcom/elfmcys/yesstevemodel/oo0oOO0000o0Ooooo0OoOo0O;)Z'), ('com/elfmcys/yesstevemodel/OOOoo00ooO000oOOoO0OO000', '<init>', '()V'), ('com/elfmcys/yesstevemodel/OOOoo00ooO000oOOoO0OO000', 'Oo0Oo0o00O00Oo0OOoOOoooo', '(Lcom/elfmcys/yesstevemodel/oo0oOO0000o0Ooooo0OoOo0O;)Z'), ('com/elfmcys/yesstevemodel/o0000O00oo00oOOooO0oO0oO', '<init>', '()V'), ('com/elfmcys/yesstevemodel/o0000O00oo00oOOooO0oO0oO', 'Oo0Oo0o00O00Oo0OOoOOoooo', '(Lcom/elfmcys/yesstevemodel/oo0oOO0000o0Ooooo0OoOo0O;)Z'), ('com/elfmcys/yesstevemodel/o000OOOo000O00o000O0ooo0', '<init>', '()V'), ('com/elfmcys/yesstevemodel/o000OOOo000O00o000O0ooo0', 'Oo0Oo0o00O00Oo0OOoOOoooo', '(Lcom/elfmcys/yesstevemodel/oo0oOO0000o0Ooooo0OoOo0O;)Z'), ('com/elfmcys/yesstevemodel/o0ooOO00oOoO000oooO00o0o', '<init>', '()V'), ('com/elfmcys/yesstevemodel/o0ooOO00oOoO000oooO00o0o', 'Oo0Oo0o00O00Oo0OOoOOoooo', '(Lcom/elfmcys/yesstevemodel/oo0oOO0000o0Ooooo0OoOo0O;)Z'), ('com/elfmcys/yesstevemodel/oOOooOO0O0OoOOoOO00ooO0o', '<init>', '()V'), ('com/elfmcys/yesstevemodel/oOOooOO0O0OoOOoOO00ooO0o', 'Oo0Oo0o00O00Oo0OOoOOoooo', '(Lcom/elfmcys/yesstevemodel/oo0oOO0000o0Ooooo0OoOo0O;)Z'), ('com/elfmcys/yesstevemodel/oo0000oOOoOo0OoOOOOoO0o0', '<init>', '()V'), ('com/elfmcys/yesstevemodel/oo0000oOOoOo0OoOOOOoO0o0', 'Oo0Oo0o00O00Oo0OOoOOoooo', '(Lcom/elfmcys/yesstevemodel/oo0oOO0000o0Ooooo0OoOo0O;)Z'), ('com/elfmcys/yesstevemodel/ooO00OOOOOo0oOoooO00oOoO', '<init>', '()V'), ('com/elfmcys/yesstevemodel/ooO00OOOOOo0oOoooO00oOoO', 'Oo0Oo0o00O00Oo0OOoOOoooo', '(Lcom/elfmcys/yesstevemodel/oo0oOO0000o0Ooooo0OoOo0O;)Z'), ('com/elfmcys/yesstevemodel/ooO0oo0OOOoo0000O0OoooO0', '<init>', '()V'), ('com/elfmcys/yesstevemodel/ooO0oo0OOOoo0000O0OoooO0', 'Oo0Oo0o00O00Oo0OOoOOoooo', '(Lcom/elfmcys/yesstevemodel/oo0oOO0000o0Ooooo0OoOo0O;)Z'), ('com/elfmcys/yesstevemodel/o0oOo0o000oOo00OO000OOoO', '<init>', '()V'), ('com/elfmcys/yesstevemodel/o0oOo0o000oOo00OO000OOoO', 'Oo0Oo0o00O00Oo0OOoOOoooo', '(Lcom/elfmcys/yesstevemodel/oo0oOO0000o0Ooooo0OoOo0O;)Z'), ('com/elfmcys/yesstevemodel/o0oOo0o000oOo00OO000OOoO', 'evaluate', '(Lcom/elfmcys/yesstevemodel/oO0OoO0O0OoO0oo0oo0OOooo;Lcom/elfmcys/yesstevemodel/O00OOo00o0O00ooo000OOo0O$Oo0Oo0o00O00Oo0OOoOOoooo;)Ljava/lang/Object;'), ('com/elfmcys/yesstevemodel/o0oOo0o000oOo00OO000OOoO', 'Oo0Oo0o00O00Oo0OOoOOoooo', '(Lcom/elfmcys/yesstevemodel/oO0OoO0O0OoO0oo0oo0OOooo;Lcom/elfmcys/yesstevemodel/O00OOo00o0O00ooo000OOo0O$Oo0Oo0o00O00Oo0OOoOOoooo;)Ljava/lang/Object;')])
SOURCES=[('src/main/java/com/elfmcys/yesstevemodel/geckolib3/core/molang/function/entity/MobEntityFunction.java', 'cff3a0a2e2614ee9517ba25a9fc41f4df687884d901b4a46c1b1b6c631a4c833', 'f184edabd1b5115ce5a24cb6d155ba5a669f5ba6'), ('src/main/java/com/elfmcys/yesstevemodel/geckolib3/core/molang/function/entity/LivingEntityFunction.java', '3436f4de35df7226c9f5582b4ce457776e11ddebe04395a123234b91d2db3bf7', 'f184edabd1b5115ce5a24cb6d155ba5a669f5ba6'), ('src/main/java/com/elfmcys/yesstevemodel/geckolib3/core/molang/function/entity/ArrowEntityFunction.java', 'f0598a81f6d8c4699bbf701a5f2616764d38eadf037d12212556eb82e3b86c59', 'f184edabd1b5115ce5a24cb6d155ba5a669f5ba6'), ('src/main/java/com/elfmcys/yesstevemodel/geckolib3/core/molang/function/item/ItemFunction.java', '1a8697bca7d3c4790224aed01167ee7d44f711d13afb2a52c8c9d7d1d885dfa8', 'f184edabd1b5115ce5a24cb6d155ba5a669f5ba6'), ('src/main/java/com/elfmcys/yesstevemodel/geckolib3/core/molang/function/entity/ProjectileEntityFunction.java', '7904755c5af105d89552d2183de532c349e7f425a71b30d6f8a7a27cd25f6c45', 'f184edabd1b5115ce5a24cb6d155ba5a669f5ba6'), ('src/main/java/com/elfmcys/yesstevemodel/geckolib3/core/molang/function/entity/PlayerEntityFunction.java', '048ce905d0d60188c0358367dbfa0698b108f540d751060965683dfee5105b27', 'f184edabd1b5115ce5a24cb6d155ba5a669f5ba6'), ('src/main/java/com/elfmcys/yesstevemodel/geckolib3/core/molang/function/item/ItemStackFunction.java', '8d703c8bf55e6d8d24f0af2feff42fd042a701e51b6896111db848ad566c0d10', 'f184edabd1b5115ce5a24cb6d155ba5a669f5ba6'), ('src/main/java/com/elfmcys/yesstevemodel/geckolib3/core/molang/function/blocks/BlockFunction.java', '1a061fa186d60a4af58eb25a5310f854c6e02a329960f40f1e583033cda08a9f', 'f184edabd1b5115ce5a24cb6d155ba5a669f5ba6'), ('src/main/java/com/elfmcys/yesstevemodel/geckolib3/core/molang/function/blocks/AbstractBlockFunction.java', '3f20578bd56cdc35d5e378bdc583531d0b53e5e3d75eca5a5c370c9ad5791ac3', 'f184edabd1b5115ce5a24cb6d155ba5a669f5ba6'), ('src/main/java/com/elfmcys/yesstevemodel/geckolib3/core/molang/function/entity/AbstractArrowEntityFunction.java', 'd2c9dc35939fcfe5e9b6f73f7a111c5221fa1c89d57aedcf3d5f87f1b6d2e78f', 'f184edabd1b5115ce5a24cb6d155ba5a669f5ba6'), ('src/main/java/com/elfmcys/yesstevemodel/geckolib3/core/molang/function/entity/TamableEntityFunction.java', '269109258da65e6784334a3b3257c153198546888c5d4b4e668f5c868cad1716', 'f184edabd1b5115ce5a24cb6d155ba5a669f5ba6'), ('src/main/java/com/elfmcys/yesstevemodel/geckolib3/core/molang/function/entity/EntityFunction.java', 'd913a992a5645bd576ec186255d36085158c5998faca821210372bd4a02a1a63', 'f184edabd1b5115ce5a24cb6d155ba5a669f5ba6'), ('src/main/java/com/elfmcys/yesstevemodel/geckolib3/core/molang/function/entity/LocalPlayerEntityFunction.java', '21e4e068f8e7af573e49f8693a4093eecd8e6f5feb1dc73edf0e52f669eb1b5c', 'f184edabd1b5115ce5a24cb6d155ba5a669f5ba6'), ('src/main/java/com/elfmcys/yesstevemodel/geckolib3/core/molang/function/ContextFunction.java', 'fe91c465df4cfe0631bb7a165dc9b970172d5de0953273a599b74d862a96afdd', 'f184edabd1b5115ce5a24cb6d155ba5a669f5ba6')]

KEYS=('access','instructions','supplemental_full_operand_records','exception_handlers','code_sha256')
DECL=('access','super','interfaces','fields','methods')
def ident(m):return tuple(m.get(k) for k in ('owner','name','descriptor'))
def audit(e,actual,decl,details):
    checks=[]
    def ck(name,ok):checks.append({'check':name,'pass':bool(ok)})
    ck('fixed-artifact',e.get('artifact',{}).get('sha256')==SHA and e.get('artifact',{}).get('size')==SIZE)
    ck('detailed-operands',e.get('detailed_operands') is True)
    rows=e.get('members',[]);ids=[ident(m) for m in rows]
    ck('selected-30-methods',len(ids)==len(set(ids))==30 and set(ids)==set(actual)==SELECTED)
    for m in rows:
        a=actual.get(ident(m),{})
        for k in KEYS:ck(str(ident(m))+':'+k,(k in m)==(k in a) and m.get(k)==a.get(k))
    ds=e.get('owner_declarations',[]);ck('fourteen-declarations',len(ds)==14 and {r['owner'] for r in ds}==set(OWNERS))
    for r in ds:ck(r['owner']+':declaration',r['declaration']==decl.get(r['owner']))
    bs=e.get('bootstrap_and_constant_evidence',[]);ck('fourteen-bootstrap-records',len(bs)==14 and {r['owner'] for r in bs}==set(OWNERS))
    for r in bs:
        for k in ('constant_values','bootstrap_methods'):ck(r['owner']+':'+k,k in r and r[k]==details.get(r['owner'],{}).get(k))
    ss=e.get('source_tracks',[]);ck('fourteen-fixed-source-records',sorted((r.get('path'),r.get('sha256'),r.get('revision')) for r in ss)==sorted(SOURCES))
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
    with zipfile.ZipFile(a.jar) as z:
        all_classes=[(n[:-6],parse_class(z.read(n))) for n in z.namelist() if n.endswith('.class')]
    direct_abstract={n for n,c in all_classes if c['super']==OWNERS[-1] and c['access']&0x400}
    details=copy.deepcopy(BOUNDDETAILS);checks=audit(e,actual,decl,details);root=Path(a.source_root)
    checks.append({'check':'fixed-955-class-13-direct-abstract-guard-family','pass':len(all_classes)==955 and direct_abstract==set(OWNERS[:-1])})
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
    neg('missing-model-asset-helper-0',lambda x:member(x,0,'(Lcom/elfmcys/yesstevemodel/oo0oOO0000o0Ooooo0OoOo0O;)Z','Oo0Oo0o00O00Oo0OOoOOoooo')['instructions'].pop())
    neg('missing-model-asset-helper-1',lambda x:member(x,1,'(Lcom/elfmcys/yesstevemodel/oo0oOO0000o0Ooooo0OoOo0O;)Z','Oo0Oo0o00O00Oo0OOoOOoooo')['instructions'].pop())
    neg('missing-model-asset-helper-2',lambda x:member(x,2,'(Lcom/elfmcys/yesstevemodel/oo0oOO0000o0Ooooo0OoOo0O;)Z','Oo0Oo0o00O00Oo0OOoOOoooo')['instructions'].pop())
    neg('missing-model-asset-helper-3',lambda x:member(x,3,'(Lcom/elfmcys/yesstevemodel/oo0oOO0000o0Ooooo0OoOo0O;)Z','Oo0Oo0o00O00Oo0OOoOOoooo')['instructions'].pop())
    neg('missing-model-asset-helper-4',lambda x:member(x,4,'(Lcom/elfmcys/yesstevemodel/oo0oOO0000o0Ooooo0OoOo0O;)Z','Oo0Oo0o00O00Oo0OOoOOoooo')['instructions'].pop())
    neg('missing-model-asset-helper-5',lambda x:member(x,5,'(Lcom/elfmcys/yesstevemodel/oo0oOO0000o0Ooooo0OoOo0O;)Z','Oo0Oo0o00O00Oo0OOoOOoooo')['instructions'].pop())
    neg('missing-model-asset-helper-6',lambda x:member(x,6,'(Lcom/elfmcys/yesstevemodel/oo0oOO0000o0Ooooo0OoOo0O;)Z','Oo0Oo0o00O00Oo0OOoOOoooo')['instructions'].pop())
    neg('missing-model-asset-helper-7',lambda x:member(x,7,'(Lcom/elfmcys/yesstevemodel/oo0oOO0000o0Ooooo0OoOo0O;)Z','Oo0Oo0o00O00Oo0OOoOOoooo')['instructions'].pop())
    neg('missing-model-asset-helper-8',lambda x:member(x,8,'(Lcom/elfmcys/yesstevemodel/oo0oOO0000o0Ooooo0OoOo0O;)Z','Oo0Oo0o00O00Oo0OOoOOoooo')['instructions'].pop())
    neg('missing-model-asset-helper-9',lambda x:member(x,9,'(Lcom/elfmcys/yesstevemodel/oo0oOO0000o0Ooooo0OoOo0O;)Z','Oo0Oo0o00O00Oo0OOoOOoooo')['instructions'].pop())
    neg('missing-model-asset-helper-10',lambda x:member(x,10,'(Lcom/elfmcys/yesstevemodel/oo0oOO0000o0Ooooo0OoOo0O;)Z','Oo0Oo0o00O00Oo0OOoOOoooo')['instructions'].pop())
    neg('missing-model-asset-helper-11',lambda x:member(x,11,'(Lcom/elfmcys/yesstevemodel/oo0oOO0000o0Ooooo0OoOo0O;)Z','Oo0Oo0o00O00Oo0OOoOOoooo')['instructions'].pop())
    neg('missing-model-asset-helper-12',lambda x:member(x,12,'(Lcom/elfmcys/yesstevemodel/oo0oOO0000o0Ooooo0OoOo0O;)Z','Oo0Oo0o00O00Oo0OOoOOoooo')['instructions'].pop())
    neg('missing-model-asset-helper-13',lambda x:member(x,13,'(Lcom/elfmcys/yesstevemodel/oo0oOO0000o0Ooooo0OoOo0O;)Z','Oo0Oo0o00O00Oo0OOoOOoooo')['instructions'].pop())
    result={'artifact_sha256':SHA,'checks':checks,'negative_controls':negatives,'failures':[c for c in checks if not c['pass']],'negative_failures':[n for n in negatives if not n['rejected']],'independent_semantic_review':'NOT_RUN','runtime_executed':False,'central_mapping_promoted':False}
    Path(a.out).write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({'checks':len(checks),'negative_controls':len(negatives),'failures':len(result['failures'])+len(result['negative_failures'])}))
    if result['failures'] or result['negative_failures']:raise SystemExit(1)
if __name__=='__main__':main()
