#!/usr/bin/env python3
"""HYBRID-PARCOOL-CONTROLLER fixed-artifact integrity audit; does not execute target classes or independently prove prose semantics."""
import argparse,copy,hashlib,json,subprocess,zipfile
from pathlib import Path
from audit_seed_recovery_ysm_265 import parse_bounded,BOUNDDETAILS
from scan_ysm_265 import parse_class
SHA='25b5e902b96f4c298690208f8b433cbc31737c23f87590354dbd86f00207bc8f'
SIZE=63269843
OWNERS=['com/elfmcys/yesstevemodel/oo0oO00OO0oo000oOOOOoO0o', 'com/elfmcys/yesstevemodel/ooO0000o0OO0O000OOooOOo0', 'com/elfmcys/yesstevemodel/o000oo00OO0Oo00ooOOoOO0O', 'com/elfmcys/yesstevemodel/o000oo00OO0Oo00ooOOoOO0O$1', 'com/elfmcys/yesstevemodel/oOoOOoOOoOooOoO0oO0OOoOO', 'com/elfmcys/yesstevemodel/oO00oooOoOo0O0oOo000o0Oo']
SELECTED=set([('com/elfmcys/yesstevemodel/oo0oO00OO0oo000oOOOOoO0o', '<init>', '()V'), ('com/elfmcys/yesstevemodel/oo0oO00OO0oo000oOOOOoO0o', 'Oo0Oo0o00O00Oo0OOoOOoooo', '()V'), ('com/elfmcys/yesstevemodel/oo0oO00OO0oo000oOOOOoO0o', 'o0OOooo0o0OO00OoOOOo0o0O', '()Ljava/util/Optional;'), ('com/elfmcys/yesstevemodel/oo0oO00OO0oo000oOOOOoO0o', 'O00OOOooOoooOoo0o0o0oO0O', '()Z'), ('com/elfmcys/yesstevemodel/oo0oO00OO0oo000oOOOOoO0o', 'oOOOo0OOO0ooooo0O00OO0o0', '()Ljava/util/Optional;'), ('com/elfmcys/yesstevemodel/oo0oO00OO0oo000oOOOOoO0o', 'Oo0Oo0o00O00Oo0OOoOOoooo', '(Lnet/minecraft/world/entity/player/Player;)Z'), ('com/elfmcys/yesstevemodel/oo0oO00OO0oo000oOOOOoO0o', 'o0OOooo0o0OO00OoOOOo0o0O', '(Lnet/minecraft/world/entity/player/Player;)Ljava/lang/String;'), ('com/elfmcys/yesstevemodel/oo0oO00OO0oo000oOOOOoO0o', 'Oo0Oo0o00O00Oo0OOoOOoooo', '(Lcom/elfmcys/yesstevemodel/OoOOOOOo0oo0000oooOOOoOO;)V'), ('com/elfmcys/yesstevemodel/oo0oO00OO0oo000oOOOOoO0o', 'o0OOooo0o0OO00OoOOOo0o0O', '(Lcom/elfmcys/yesstevemodel/OoOOOOOo0oo0000oooOOOoOO;)V'), ('com/elfmcys/yesstevemodel/oo0oO00OO0oo000oOOOOoO0o', 'Oo0Oo0o00O00Oo0OOoOOoooo', '(Lcom/elfmcys/yesstevemodel/oo0oOO0000o0Ooooo0OoOo0O;)Ljava/lang/Object;'), ('com/elfmcys/yesstevemodel/oo0oO00OO0oo000oOOOOoO0o', 'Oo0Oo0o00O00Oo0OOoOOoooo', '(Ljava/lang/String;Lcom/elfmcys/yesstevemodel/oo0OooOO0oOoOoOoo00oO000;)Lcom/elfmcys/yesstevemodel/OoOoOO0O00oOoO0o0ooOO0oO;'), ('com/elfmcys/yesstevemodel/oo0oO00OO0oo000oOOOOoO0o', '<clinit>', '()V'), ('com/elfmcys/yesstevemodel/ooO0000o0OO0O000OOooOOo0', '<init>', '()V'), ('com/elfmcys/yesstevemodel/ooO0000o0OO0O000OOooOOo0', 'Oo0Oo0o00O00Oo0OOoOOoooo', '(Lcom/elfmcys/yesstevemodel/OoOOOOOo0oo0000oooOOOoOO;)V'), ('com/elfmcys/yesstevemodel/ooO0000o0OO0O000OOooOOo0', 'Oo0Oo0o00O00Oo0OOoOOoooo', '(Lcom/elfmcys/yesstevemodel/oo0oOO0000o0Ooooo0OoOo0O;)Ljava/lang/String;'), ('com/elfmcys/yesstevemodel/o000oo00OO0Oo00ooOOoOO0O', '<init>', '()V'), ('com/elfmcys/yesstevemodel/o000oo00OO0Oo00ooOOoOO0O', 'Oo0Oo0o00O00Oo0OOoOOoooo', '(Lnet/minecraft/world/entity/player/Player;)Z'), ('com/elfmcys/yesstevemodel/o000oo00OO0Oo00ooOOoOO0O', 'o0OOooo0o0OO00OoOOOo0o0O', '(Lnet/minecraft/world/entity/player/Player;)Ljava/lang/String;'), ('com/elfmcys/yesstevemodel/o000oo00OO0Oo00ooOOoOO0O', 'Oo0Oo0o00O00Oo0OOoOOoooo', '(Lcom/alrex/parcool/client/animation/Animator;)Ljava/lang/String;'), ('com/elfmcys/yesstevemodel/o000oo00OO0Oo00ooOOoOO0O', 'Oo0Oo0o00O00Oo0OOoOOoooo', '(Ljava/lang/String;)Ljava/lang/String;'), ('com/elfmcys/yesstevemodel/o000oo00OO0Oo00ooOOoOO0O', 'Oo0Oo0o00O00Oo0OOoOOoooo', '(Ljava/lang/Class;)Ljava/lang/String;'), ('com/elfmcys/yesstevemodel/o000oo00OO0Oo00ooOOoOO0O', '<clinit>', '()V'), ('com/elfmcys/yesstevemodel/o000oo00OO0Oo00ooOOoOO0O$1', '<clinit>', '()V'), ('com/elfmcys/yesstevemodel/oOoOOoOOoOooOoO0oO0OOoOO', '<init>', '()V'), ('com/elfmcys/yesstevemodel/oOoOOoOOoOooOoO0oO0OOoOO', 'Oo0Oo0o00O00Oo0OOoOOoooo', '(Lcom/elfmcys/yesstevemodel/OO00O0o0OooOOOo00OO00o00;Lcom/elfmcys/yesstevemodel/O0Oooo00oOo00O00OoOOOooO;)Lcom/elfmcys/yesstevemodel/O0oOo0OoO0O0o0000o0O00o0;'), ('com/elfmcys/yesstevemodel/oO00oooOoOo0O0oOo000o0Oo', '<init>', '(Lcom/elfmcys/yesstevemodel/o0000OoOooO0oo0o0oooo0Oo;Ljava/lang/String;FLcom/elfmcys/yesstevemodel/oOOO0Oo0O00oo0O0oO0OooO0;)V'), ('com/elfmcys/yesstevemodel/oO00oooOoOo0O0oOo000o0Oo', '<init>', '(Lcom/elfmcys/yesstevemodel/o0000OoOooO0oo0o0oooo0Oo;Ljava/lang/String;FLcom/elfmcys/yesstevemodel/oOOO0Oo0O00oo0O0oO0OooO0;Z)V'), ('com/elfmcys/yesstevemodel/oO00oooOoOo0O0oOo000o0Oo', 'Oo0Oo0o00O00Oo0OOoOOoooo', '()Ljava/lang/String;'), ('com/elfmcys/yesstevemodel/oO00oooOoOo0O0oOo000o0Oo', 'o0OOooo0o0OO00OoOOOo0o0O', '()Ljava/lang/String;'), ('com/elfmcys/yesstevemodel/oO00oooOoOo0O0oOo000o0Oo', 'Oo0Oo0o00O00Oo0OOoOOoooo', '(Ljava/util/List;Lit/unimi/dsi/fastutil/objects/Object2ReferenceMap;)V'), ('com/elfmcys/yesstevemodel/oO00oooOoOo0O0oOo000o0Oo', 'Oo0Oo0o00O00Oo0OOoOOoooo', '(Lcom/elfmcys/yesstevemodel/OO00O0o0OooOOOo00OO00o00;Lcom/elfmcys/yesstevemodel/O0Oooo00oOo00O00OoOOOooO;Z)V'), ('com/elfmcys/yesstevemodel/oO00oooOoOo0O0oOo000o0Oo', 'Oo0Oo0o00O00Oo0OOoOOoooo', '(Ljava/util/function/Consumer;)V'), ('com/elfmcys/yesstevemodel/oO00oooOoOo0O0oOo000o0Oo', 'oooooooOOoOOoO00OooOo00O', '()Z'), ('com/elfmcys/yesstevemodel/oO00oooOoOo0O0oOo000o0Oo', 'oOOOo0OOO0ooooo0O00OO0o0', '()V')])
SOURCES=[('src/main/java/com/elfmcys/yesstevemodel/client/compat/parcool/ParCoolCompat.java', 'cee0a029202cb910aa6685568a56220643f5d2cc6ff19c5272b278af8094cd79', 'f184edabd1b5115ce5a24cb6d155ba5a669f5ba6'), ('src/main/java/com/elfmcys/yesstevemodel/client/compat/parcool/ParCoolCtrlBinding.java', 'f48d9af306cd2025bc6bac659acc780fb4b3c082b506a848459e3da05dce9a18', 'f184edabd1b5115ce5a24cb6d155ba5a669f5ba6'), ('src/main/java/com/elfmcys/yesstevemodel/client/compat/parcool/ParCoolAnimationManger.java', '7fc76c0f8684ea678eab4f37464a220dc53061ba92159d39facb3907d02bae70', 'f184edabd1b5115ce5a24cb6d155ba5a669f5ba6'), ('src/main/java/com/elfmcys/yesstevemodel/client/compat/parcool/ParCoolAnimationManger.java', '7fc76c0f8684ea678eab4f37464a220dc53061ba92159d39facb3907d02bae70', 'f184edabd1b5115ce5a24cb6d155ba5a669f5ba6'), ('src/main/java/com/elfmcys/yesstevemodel/client/compat/parcool/ParCoolPredicate.java', '354cb2c2e1e07ae67d73da9cff8928c10d00a055b80fefc6f9c700b396b131f3', 'f184edabd1b5115ce5a24cb6d155ba5a669f5ba6'), ('src/main/java/com/elfmcys/yesstevemodel/geckolib3/core/controller/HybridAnimationController.java', 'f0ac2decd9d0b14a754a9383a9e5f8baa16c66826ccd137313cd54721073a353', 'f184edabd1b5115ce5a24cb6d155ba5a669f5ba6')]

KEYS=('access','instructions','supplemental_full_operand_records','exception_handlers','code_sha256')
DECL=('access','super','interfaces','fields','methods')
def ident(m):return tuple(m.get(k) for k in ('owner','name','descriptor'))
def audit(e,actual,decl,details):
    checks=[]
    def ck(name,ok):checks.append({'check':name,'pass':bool(ok)})
    ck('fixed-artifact',e.get('artifact',{}).get('sha256')==SHA and e.get('artifact',{}).get('size')==SIZE)
    ck('detailed-operands',e.get('detailed_operands') is True)
    rows=e.get('members',[]);ids=[ident(m) for m in rows]
    ck('selected-34-methods',len(ids)==len(set(ids))==34 and set(ids)==set(actual)==SELECTED)
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
    neg('missing-hybrid-parcool-link-0',lambda x:member(x,0,'()V','Oo0Oo0o00O00Oo0OOoOOoooo')['instructions'].pop())
    neg('missing-hybrid-parcool-link-1',lambda x:member(x,1,'(Lcom/elfmcys/yesstevemodel/OoOOOOOo0oo0000oooOOOoOO;)V','Oo0Oo0o00O00Oo0OOoOOoooo')['instructions'].pop())
    neg('missing-hybrid-parcool-link-2',lambda x:member(x,2,'(Lnet/minecraft/world/entity/player/Player;)Z','Oo0Oo0o00O00Oo0OOoOOoooo')['instructions'].pop())
    neg('missing-hybrid-parcool-link-3',lambda x:member(x,3,'()V','<clinit>')['instructions'].pop())
    neg('missing-hybrid-parcool-link-4',lambda x:member(x,4,'(Lcom/elfmcys/yesstevemodel/OO00O0o0OooOOOo00OO00o00;Lcom/elfmcys/yesstevemodel/O0Oooo00oOo00O00OoOOOooO;)Lcom/elfmcys/yesstevemodel/O0oOo0OoO0O0o0000o0O00o0;','Oo0Oo0o00O00Oo0OOoOOoooo')['instructions'].pop())
    neg('missing-hybrid-parcool-link-5',lambda x:member(x,5,'()Ljava/lang/String;','Oo0Oo0o00O00Oo0OOoOOoooo')['instructions'].pop())
    result={'artifact_sha256':SHA,'checks':checks,'negative_controls':negatives,'failures':[c for c in checks if not c['pass']],'negative_failures':[n for n in negatives if not n['rejected']],'independent_semantic_review':'NOT_RUN','runtime_executed':False,'central_mapping_promoted':False}
    Path(a.out).write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({'checks':len(checks),'negative_controls':len(negatives),'failures':len(result['failures'])+len(result['negative_failures'])}))
    if result['failures'] or result['negative_failures']:raise SystemExit(1)
if __name__=='__main__':main()
