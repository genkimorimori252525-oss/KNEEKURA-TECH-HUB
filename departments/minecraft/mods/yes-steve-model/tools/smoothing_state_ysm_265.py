#!/usr/bin/env python3
"""SMOOTHING-STATE fixed-artifact integrity audit; does not execute target classes or independently prove prose semantics."""
import argparse,copy,hashlib,json,subprocess,zipfile
from pathlib import Path
from audit_seed_recovery_ysm_265 import parse_bounded,BOUNDDETAILS
from scan_ysm_265 import parse_class
SHA='25b5e902b96f4c298690208f8b433cbc31737c23f87590354dbd86f00207bc8f'
SIZE=63269843
OWNERS=['com/elfmcys/yesstevemodel/oOO00ooOo00Ooo0OOOOoO0oO', 'com/elfmcys/yesstevemodel/O0OO0ooOoooOO0oo0o0oOOOo', 'com/elfmcys/yesstevemodel/OOoO0oOOoooo0O0O0oOO0O0o', 'com/elfmcys/yesstevemodel/oOooOOoooOo0O0OOOoo0000o', 'com/elfmcys/yesstevemodel/ooO000OOoooo0OoOOo00o0Oo', 'com/elfmcys/yesstevemodel/ooOOOoOOOOo0ooooo0O0O0OO', 'com/elfmcys/yesstevemodel/o0000OoOooO0oo0o0oooo0Oo']
SELECTED=set([('com/elfmcys/yesstevemodel/oOO00ooOo00Ooo0OOOOoO0oO', '<init>', '()V'), ('com/elfmcys/yesstevemodel/oOO00ooOo00Ooo0OOOOoO0oO', 'Oo0Oo0o00O00Oo0OOoOOoooo', '(Lcom/elfmcys/yesstevemodel/oO0OoO0O0OoO0oo0oo0OOooo;Lcom/elfmcys/yesstevemodel/O00OOo00o0O00ooo000OOo0O$Oo0Oo0o00O00Oo0OOoOOoooo;)Ljava/lang/Object;'), ('com/elfmcys/yesstevemodel/oOO00ooOo00Ooo0OOOOoO0oO', 'Oo0Oo0o00O00Oo0OOoOOoooo', '(I)Z'), ('com/elfmcys/yesstevemodel/O0OO0ooOoooOO0oo0o0oOOOo', '<init>', '()V'), ('com/elfmcys/yesstevemodel/O0OO0ooOoooOO0oo0o0oOOOo', 'Oo0Oo0o00O00Oo0OOoOOoooo', '(Lcom/elfmcys/yesstevemodel/oO0OoO0O0OoO0oo0oo0OOooo;Lcom/elfmcys/yesstevemodel/O00OOo00o0O00ooo000OOo0O$Oo0Oo0o00O00Oo0OOoOOoooo;)Ljava/lang/Object;'), ('com/elfmcys/yesstevemodel/O0OO0ooOoooOO0oo0o0oOOOo', 'Oo0Oo0o00O00Oo0OOoOOoooo', '(I)Z'), ('com/elfmcys/yesstevemodel/OOoO0oOOoooo0O0O0oOO0O0o', '<init>', '(FF)V'), ('com/elfmcys/yesstevemodel/OOoO0oOOoooo0O0O0oOO0O0o', 'Oo0Oo0o00O00Oo0OOoOOoooo', '(F)V'), ('com/elfmcys/yesstevemodel/OOoO0oOOoooo0O0O0oOO0O0o', 'Oo0Oo0o00O00Oo0OOoOOoooo', '(FFFF)V'), ('com/elfmcys/yesstevemodel/OOoO0oOOoooo0O0O0oOO0O0o', 'Oo0Oo0o00O00Oo0OOoOOoooo', '()F'), ('com/elfmcys/yesstevemodel/oOooOOoooOo0O0OOOoo0000o', '<init>', '(FFFF)V'), ('com/elfmcys/yesstevemodel/oOooOOoooOo0O0OOOoo0000o', 'Oo0Oo0o00O00Oo0OOoOOoooo', '(F)V'), ('com/elfmcys/yesstevemodel/oOooOOoooOo0O0OOOoo0000o', 'Oo0Oo0o00O00Oo0OOoOOoooo', '(FFFF)V'), ('com/elfmcys/yesstevemodel/oOooOOoooOo0O0OOOoo0000o', 'Oo0Oo0o00O00Oo0OOoOOoooo', '()F'), ('com/elfmcys/yesstevemodel/ooO000OOoooo0OoOOo00o0Oo', 'Oo0Oo0o00O00Oo0OOoOOoooo', '(F)V'), ('com/elfmcys/yesstevemodel/ooO000OOoooo0OoOOo00o0Oo', 'Oo0Oo0o00O00Oo0OOoOOoooo', '(FFFF)V'), ('com/elfmcys/yesstevemodel/ooO000OOoooo0OoOOo00o0Oo', 'Oo0Oo0o00O00Oo0OOoOOoooo', '()F'), ('com/elfmcys/yesstevemodel/ooOOOoOOOOo0ooooo0O0O0OO', '<init>', '()V'), ('com/elfmcys/yesstevemodel/ooOOOoOOOOo0ooooo0O0O0OO', 'Oo0Oo0o00O00Oo0OOoOOoooo', '(F)V'), ('com/elfmcys/yesstevemodel/ooOOOoOOOOo0ooooo0O0O0OO', 'Oo0Oo0o00O00Oo0OOoOOoooo', '(ILcom/elfmcys/yesstevemodel/ooO000OOoooo0OoOOo00o0Oo;)V'), ('com/elfmcys/yesstevemodel/ooOOOoOOOOo0ooooo0O0O0OO', 'Oo0Oo0o00O00Oo0OOoOOoooo', '(I)Lcom/elfmcys/yesstevemodel/ooO000OOoooo0OoOOo00o0Oo;'), ('com/elfmcys/yesstevemodel/ooOOOoOOOOo0ooooo0O0O0OO', 'Oo0Oo0o00O00Oo0OOoOOoooo', '()V'), ('com/elfmcys/yesstevemodel/ooOOOoOOOOo0ooooo0O0O0OO', 'Oo0Oo0o00O00Oo0OOoOOoooo', '(FLit/unimi/dsi/fastutil/ints/Int2ReferenceMap$Entry;)V'), ('com/elfmcys/yesstevemodel/o0000OoOooO0oo0o0oooo0Oo', '<init>', '(Lnet/minecraft/world/entity/Entity;)V'), ('com/elfmcys/yesstevemodel/o0000OoOooO0oo0o0oooo0Oo', 'oOOOo0OOO0ooooo0O00OO0o0', '()V'), ('com/elfmcys/yesstevemodel/o0000OoOooO0oo0o0oooo0Oo', 'ooOO000o0O0OOOoO0Oo0o0Oo', '()Lcom/elfmcys/yesstevemodel/ooOOOoOOOOo0ooooo0O0O0OO;'), ('com/elfmcys/yesstevemodel/o0000OoOooO0oo0o0oooo0Oo', 'Oo0Oo0o00O00Oo0OOoOOoooo', '(Lcom/elfmcys/yesstevemodel/O0O00Oo0o0oO0oo0oO00OOoO;Lcom/elfmcys/yesstevemodel/OO00O0o0OooOOOo00OO00o00;)V')])
SOURCES=[('src/main/java/com/elfmcys/yesstevemodel/client/animation/molang/functions/FirstOrderFunction.java', '2c070b2629503d28eacc5242a54f0b57fe22b38979afd7a5dfaabb31d27f8b65', 'f184edabd1b5115ce5a24cb6d155ba5a669f5ba6'), ('src/main/java/com/elfmcys/yesstevemodel/client/animation/molang/functions/SecondOrderFunction.java', '54fea6339a45f95210a11fca1ba3ae1fb0843590aff03c3f52766a866d1325ac', 'f184edabd1b5115ce5a24cb6d155ba5a669f5ba6'), ('src/main/java/com/elfmcys/yesstevemodel/client/animation/molang/functions/physics/FirstOrder.java', '9dd07f96788aff4329879890af1acdae7502b29530592441b98d7b692235c391', 'f184edabd1b5115ce5a24cb6d155ba5a669f5ba6'), ('src/main/java/com/elfmcys/yesstevemodel/client/animation/molang/functions/physics/SecondOrder.java', 'b6461d3e9deda7b0bf8672ceaa0c949bf2bac63c33d418b928c32845014742e0', 'f184edabd1b5115ce5a24cb6d155ba5a669f5ba6'), ('src/main/java/com/elfmcys/yesstevemodel/client/animation/molang/functions/physics/IPhysics.java', '3f19029cb1db27f8266c614540c2422bee0675f98e3aac4cd0479468a4ce7128', 'f184edabd1b5115ce5a24cb6d155ba5a669f5ba6'), ('src/main/java/com/elfmcys/yesstevemodel/client/animation/molang/PhysicsManager.java', '863d07f4fe21cfdc762eaac9e5ecd9a1e385d0d1f1242a601d25eb40b96f4008', 'f184edabd1b5115ce5a24cb6d155ba5a669f5ba6'), ('src/main/java/com/elfmcys/yesstevemodel/geckolib3/model/AnimatableEntity.java', '8057707eb54d8446567c3656e1e4edf5ef8bb41febb243325623ade07d783ad7', 'f184edabd1b5115ce5a24cb6d155ba5a669f5ba6')]

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
    neg('missing-smoothing-link-0',lambda x:member(x,0,'(Lcom/elfmcys/yesstevemodel/oO0OoO0O0OoO0oo0oo0OOooo;Lcom/elfmcys/yesstevemodel/O00OOo00o0O00ooo000OOo0O$Oo0Oo0o00O00Oo0OOoOOoooo;)Ljava/lang/Object;','Oo0Oo0o00O00Oo0OOoOOoooo')['instructions'].pop())
    neg('missing-smoothing-link-1',lambda x:member(x,1,'(Lcom/elfmcys/yesstevemodel/oO0OoO0O0OoO0oo0oo0OOooo;Lcom/elfmcys/yesstevemodel/O00OOo00o0O00ooo000OOo0O$Oo0Oo0o00O00Oo0OOoOOoooo;)Ljava/lang/Object;','Oo0Oo0o00O00Oo0OOoOOoooo')['instructions'].pop())
    neg('missing-smoothing-link-2',lambda x:member(x,2,'(F)V','Oo0Oo0o00O00Oo0OOoOOoooo')['instructions'].pop())
    neg('missing-smoothing-link-3',lambda x:member(x,3,'(F)V','Oo0Oo0o00O00Oo0OOoOOoooo')['instructions'].pop())
    neg('missing-smoothing-link-5',lambda x:member(x,5,'(F)V','Oo0Oo0o00O00Oo0OOoOOoooo')['instructions'].pop())
    neg('missing-smoothing-link-6',lambda x:member(x,6,'()V','oOOOo0OOO0ooooo0O00OO0o0')['instructions'].pop())
    neg('invented-physics-interface-code',lambda x:member(x,4,'(F)V').update(instructions=[]))
    result={'artifact_sha256':SHA,'checks':checks,'negative_controls':negatives,'failures':[c for c in checks if not c['pass']],'negative_failures':[n for n in negatives if not n['rejected']],'independent_semantic_review':'NOT_RUN','runtime_executed':False,'central_mapping_promoted':False}
    Path(a.out).write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({'checks':len(checks),'negative_controls':len(negatives),'failures':len(result['failures'])+len(result['negative_failures'])}))
    if result['failures'] or result['negative_failures']:raise SystemExit(1)
if __name__=='__main__':main()
