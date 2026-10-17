#!/usr/bin/env python3
"""PROPERTY-RESET-LIFECYCLE fixed-artifact integrity audit; does not execute target classes or independently prove prose semantics."""
import argparse,copy,hashlib,json,subprocess,zipfile
from pathlib import Path
from audit_seed_recovery_ysm_265 import parse_bounded,BOUNDDETAILS
from scan_ysm_265 import parse_class
SHA='25b5e902b96f4c298690208f8b433cbc31737c23f87590354dbd86f00207bc8f'
SIZE=63269843
OWNERS=['com/elfmcys/yesstevemodel/o0O0oOooOo0OoOo0oOo00O00', 'com/elfmcys/yesstevemodel/oo0OooOO0oOoOoOoo00oO000', 'com/elfmcys/yesstevemodel/o0000OoOooO0oo0o0oooo0Oo', 'com/elfmcys/yesstevemodel/oOo00OoOO00O000ooO0Oo00o', 'com/elfmcys/yesstevemodel/o0OOO0o0o0OOo000oO00o00O', 'com/elfmcys/yesstevemodel/ooOO000o0O0OOOoO0Oo0o0Oo', 'com/elfmcys/yesstevemodel/O00OO0Oo0O0Oo0O0Ooo0o00O', 'com/elfmcys/yesstevemodel/O0oOOo0OO0000oooOO0ooo0O']
SELECTED=set([('com/elfmcys/yesstevemodel/o0O0oOooOo0OoOo0oOo00O00', 'Oo0Oo0o00O00Oo0OOoOOoooo', '(Ljava/lang/String;Ljava/lang/String;)V'), ('com/elfmcys/yesstevemodel/o0O0oOooOo0OoOo0oOo00O00', 'oOOOo0OOO0ooooo0O00OO0o0', '()V'), ('com/elfmcys/yesstevemodel/oo0OooOO0oOoOoOoo00oO000', 'oOOOo0OOO0ooooo0O00OO0o0', '()V'), ('com/elfmcys/yesstevemodel/o0000OoOooO0oo0o0oooo0Oo', 'oOOOo0OOO0ooooo0O00OO0o0', '()V'), ('com/elfmcys/yesstevemodel/o0000OoOooO0oo0o0oooo0Oo', 'Oo0Oo0o00O00Oo0OOoOOoooo', '(Lcom/elfmcys/yesstevemodel/OOoOoooOOooO0o0000o0O0o0;Lit/unimi/dsi/fastutil/objects/Object2ReferenceMap;)V'), ('com/elfmcys/yesstevemodel/o0000OoOooO0oo0o0oooo0Oo', 'O00o0ooOoo00o00o0OOOO0o0', '()V'), ('com/elfmcys/yesstevemodel/oOo00OoOO00O000ooO0Oo00o', 'Oo00o0OooOOo0ooOoo0oO0o0', '()V'), ('com/elfmcys/yesstevemodel/oOo00OoOO00O000ooO0Oo00o', 'o0OOooo0o0OO00OoOOOo0o0O', '(Ljava/lang/String;)V'), ('com/elfmcys/yesstevemodel/oOo00OoOO00O000ooO0Oo00o', 'oOOOo0OOO0ooooo0O00OO0o0', '()V'), ('com/elfmcys/yesstevemodel/o0OOO0o0o0OOo000oO00o00O', 'oOOOo0OOO0ooooo0O00OO0o0', '()V'), ('com/elfmcys/yesstevemodel/o0OOO0o0o0OOo000oO00o00O', 'Oo0Oo0o00O00Oo0OOoOOoooo', '(Lcom/elfmcys/yesstevemodel/OOOO0O0O000O000000oOOO0o;)V'), ('com/elfmcys/yesstevemodel/o0OOO0o0o0OOo000oO00o00O', 'Oo0Oo0o00O00Oo0OOoOOoooo', '(ILit/unimi/dsi/fastutil/ints/Int2FloatOpenHashMap;)V'), ('com/elfmcys/yesstevemodel/ooOO000o0O0OOOoO0Oo0o0Oo', 'Oo0Oo0o00O00Oo0OOoOOoooo', '()V'), ('com/elfmcys/yesstevemodel/ooOO000o0O0OOOoO0Oo0o0Oo', 'Oo0Oo0o00O00Oo0OOoOOoooo', '(Lcom/elfmcys/yesstevemodel/O00OO0Oo0O0Oo0O0Ooo0o00O;)V'), ('com/elfmcys/yesstevemodel/O00OO0Oo0O0Oo0O0Ooo0o00O', 'Oo0Oo0o00O00Oo0OOoOOoooo', '(Lcom/elfmcys/yesstevemodel/O00OO0Oo0O0Oo0O0Ooo0o00O;Lcom/elfmcys/yesstevemodel/o0OOO0o0o0OOo000oO00o00O;)V'), ('com/elfmcys/yesstevemodel/O0oOOo0OO0000oooOO0ooo0O', 'Oo0Oo0o00O00Oo0OOoOOoooo', '(Lcom/elfmcys/yesstevemodel/O0oOOo0OO0000oooOO0ooo0O;Lnet/minecraft/world/entity/Entity;Lcom/elfmcys/yesstevemodel/o0OOO0o0o0OOo000oO00o00O;)V')])
SOURCES=[('src/main/java/com/elfmcys/yesstevemodel/client/entity/CustomHumanoidEntity.java', 'a5def776d16ae1164d7f559ddb0809a979b253f8c4b0367c471486d81c6246e0', 'f184edabd1b5115ce5a24cb6d155ba5a669f5ba6'), ('src/main/java/com/elfmcys/yesstevemodel/client/entity/CustomPlayerEntity.java', '3ef5fbcc6c971465a7c43bc1c7927551c582299155a14792868f40be05968fa2', 'f184edabd1b5115ce5a24cb6d155ba5a669f5ba6'), ('src/main/java/com/elfmcys/yesstevemodel/geckolib3/model/AnimatableEntity.java', '8057707eb54d8446567c3656e1e4edf5ef8bb41febb243325623ade07d783ad7', 'f184edabd1b5115ce5a24cb6d155ba5a669f5ba6'), ('src/main/java/com/elfmcys/yesstevemodel/client/entity/CustomEntity.java', 'f1d6924017b087a89ed03868be2d7e55be237edf0d8522adccb013a41f7e809c', 'f184edabd1b5115ce5a24cb6d155ba5a669f5ba6'), ('src/main/java/com/elfmcys/yesstevemodel/capability/PlayerAnimatableCapability.java', '3296261fbf5d1f060ec5904da0a7c5d932e1f316694db78d8db370cfffcef78b', 'f184edabd1b5115ce5a24cb6d155ba5a669f5ba6'), ('src/main/java/com/elfmcys/yesstevemodel/capability/PlayerStateTracker.java', 'cc86509176ddefed3cecbc26eeaa3cc7cc6652f33007264531b19aa191652528', 'f184edabd1b5115ce5a24cb6d155ba5a669f5ba6'), ('src/main/java/com/elfmcys/yesstevemodel/network/message/DispatchServerDrivenProperty.java', '5d30671bf5303fc7fc01cb6a044f95c169630147e33d77c4991ef3f07949bc50', 'f184edabd1b5115ce5a24cb6d155ba5a669f5ba6'), ('src/main/java/com/elfmcys/yesstevemodel/network/message/SyncModelInfo.java', 'b24e1b7aba4980df67172b606ff05093edc2893e6a3a04d6838d9ce871569de2', 'f184edabd1b5115ce5a24cb6d155ba5a669f5ba6')]

KEYS=('access','instructions','supplemental_full_operand_records','exception_handlers','code_sha256')
DECL=('access','super','interfaces','fields','methods')
def ident(m):return tuple(m.get(k) for k in ('owner','name','descriptor'))
def audit(e,actual,decl,details):
    checks=[]
    def ck(name,ok):checks.append({'check':name,'pass':bool(ok)})
    ck('fixed-artifact',e.get('artifact',{}).get('sha256')==SHA and e.get('artifact',{}).get('size')==SIZE)
    ck('detailed-operands',e.get('detailed_operands') is True)
    rows=e.get('members',[]);ids=[ident(m) for m in rows]
    ck('selected-16-methods',len(ids)==len(set(ids))==16 and set(ids)==set(actual)==SELECTED)
    for m in rows:
        a=actual.get(ident(m),{})
        for k in KEYS:ck(str(ident(m))+':'+k,(k in m)==(k in a) and m.get(k)==a.get(k))
    ds=e.get('owner_declarations',[]);ck('eight-declarations',len(ds)==8 and {r['owner'] for r in ds}==set(OWNERS))
    for r in ds:ck(r['owner']+':declaration',r['declaration']==decl.get(r['owner']))
    bs=e.get('bootstrap_and_constant_evidence',[]);ck('eight-bootstrap-records',len(bs)==8 and {r['owner'] for r in bs}==set(OWNERS))
    for r in bs:
        for k in ('constant_values','bootstrap_methods'):ck(r['owner']+':'+k,k in r and r[k]==details.get(r['owner'],{}).get(k))
    ss=e.get('source_tracks',[]);ck('eight-fixed-source-records',sorted((r.get('path'),r.get('sha256'),r.get('revision')) for r in ss)==sorted(SOURCES))
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
    neg('missing-link-body-o0O0oOooOo0OoOo0oOo00O00',lambda x:member(x,0,'(Ljava/lang/String;Ljava/lang/String;)V','Oo0Oo0o00O00Oo0OOoOOoooo')['instructions'].pop())
    neg('missing-link-body-oo0OooOO0oOoOoOoo00oO000',lambda x:member(x,1,'()V','oOOOo0OOO0ooooo0O00OO0o0')['instructions'].pop())
    neg('missing-link-body-o0000OoOooO0oo0o0oooo0Oo',lambda x:member(x,2,'()V','oOOOo0OOO0ooooo0O00OO0o0')['instructions'].pop())
    neg('missing-link-body-oOo00OoOO00O000ooO0Oo00o',lambda x:member(x,3,'()V','Oo00o0OooOOo0ooOoo0oO0o0')['instructions'].pop())
    neg('missing-link-body-o0OOO0o0o0OOo000oO00o00O',lambda x:member(x,4,'()V','oOOOo0OOO0ooooo0O00OO0o0')['instructions'].pop())
    neg('missing-link-body-ooOO000o0O0OOOoO0Oo0o0Oo',lambda x:member(x,5,'()V','Oo0Oo0o00O00Oo0OOoOOoooo')['instructions'].pop())
    neg('missing-link-body-O00OO0Oo0O0Oo0O0Ooo0o00O',lambda x:member(x,6,'(Lcom/elfmcys/yesstevemodel/O00OO0Oo0O0Oo0O0Ooo0o00O;Lcom/elfmcys/yesstevemodel/o0OOO0o0o0OOo000oO00o00O;)V','Oo0Oo0o00O00Oo0OOoOOoooo')['instructions'].pop())
    neg('missing-link-body-O0oOOo0OO0000oooOO0ooo0O',lambda x:member(x,7,'(Lcom/elfmcys/yesstevemodel/O0oOOo0OO0000oooOO0ooo0O;Lnet/minecraft/world/entity/Entity;Lcom/elfmcys/yesstevemodel/o0OOO0o0o0OOo000oO00o00O;)V','Oo0Oo0o00O00Oo0OOoOOoooo')['instructions'].pop())
    neg('invented-tracker-reset-finally',lambda x:member(x,5,'()V')['exception_handlers'].append({'handler':0}))
    result={'artifact_sha256':SHA,'checks':checks,'negative_controls':negatives,'failures':[c for c in checks if not c['pass']],'negative_failures':[n for n in negatives if not n['rejected']],'independent_semantic_review':'NOT_RUN','runtime_executed':False,'central_mapping_promoted':False}
    Path(a.out).write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({'checks':len(checks),'negative_controls':len(negatives),'failures':len(result['failures'])+len(result['negative_failures'])}))
    if result['failures'] or result['negative_failures']:raise SystemExit(1)
if __name__=='__main__':main()
