#!/usr/bin/env python3
"""PARTICLE-SOUND-DISPATCH fixed-artifact integrity audit; does not execute target classes or independently prove prose semantics."""
import argparse,copy,hashlib,json,subprocess,zipfile
from pathlib import Path
from audit_seed_recovery_ysm_265 import parse_bounded,BOUNDDETAILS
from scan_ysm_265 import parse_class
SHA='25b5e902b96f4c298690208f8b433cbc31737c23f87590354dbd86f00207bc8f'
SIZE=63269843
OWNERS=['com/elfmcys/yesstevemodel/oooOoo00Ooo0000OoO0OOo0O', 'com/elfmcys/yesstevemodel/OOoOOooOOOOOO0OO0O0o0OOo', 'com/elfmcys/yesstevemodel/o0o00O0O0ooo00ooO0o00000$Oo0Oo0o00O00Oo0OOoOOoooo', 'com/elfmcys/yesstevemodel/o0o00O0O0ooo00ooO0o00000$o0OOooo0o0OO00OoOOOo0o0O', 'com/elfmcys/yesstevemodel/o0o00O0O0ooo00ooO0o00000$O00OOOooOoooOoo0o0o0oO0O', 'com/elfmcys/yesstevemodel/OOOO0O0OO0oOOo00Ooo0oooO', 'com/elfmcys/yesstevemodel/O0O00Oo0o0oO0oo0oO00OOoO', 'com/elfmcys/yesstevemodel/O0oo0oOo0OOOO00Oo0oo0o00', 'com/elfmcys/yesstevemodel/o000o0o0Ooooo0ooo0oO0O0o']
SELECTED=set([('com/elfmcys/yesstevemodel/oooOoo00Ooo0000OoO0OOo0O', '<init>', '(Z)V'), ('com/elfmcys/yesstevemodel/oooOoo00Ooo0000OoO0OOo0O', 'Oo0Oo0o00O00Oo0OOoOOoooo', '(Lcom/elfmcys/yesstevemodel/oO0OoO0O0OoO0oo0oo0OOooo;Lcom/elfmcys/yesstevemodel/O00OOo00o0O00ooo000OOo0O$Oo0Oo0o00O00Oo0OOoOOoooo;)Ljava/lang/Object;'), ('com/elfmcys/yesstevemodel/oooOoo00Ooo0000OoO0OOo0O', 'Oo0Oo0o00O00Oo0OOoOOoooo', '(I)Z'), ('com/elfmcys/yesstevemodel/OOoOOooOOOOOO0OO0O0o0OOo', '<init>', '()V'), ('com/elfmcys/yesstevemodel/OOoOOooOOOOOO0OO0O0o0OOo', 'Oo0Oo0o00O00Oo0OOoOOoooo', '(Lcom/elfmcys/yesstevemodel/oO0OoO0O0OoO0oo0oo0OOooo;Lcom/elfmcys/yesstevemodel/O00OOo00o0O00ooo000OOo0O$Oo0Oo0o00O00Oo0OOoOOoooo;Z)Z'), ('com/elfmcys/yesstevemodel/OOoOOooOOOOOO0OO0O0o0OOo', 'Oo0Oo0o00O00Oo0OOoOOoooo', '(Lnet/minecraft/world/entity/Entity;Ljava/lang/String;Lorg/joml/Vector3d;Lorg/joml/Vector3d;DIIZLnet/minecraft/util/RandomSource;)V'), ('com/elfmcys/yesstevemodel/OOoOOooOOOOOO0OO0O0o0OOo', 'Oo0Oo0o00O00Oo0OOoOOoooo', '(Lnet/minecraft/world/entity/Entity;Lorg/joml/Vector3d;Lorg/joml/Vector3d;DILnet/minecraft/client/particle/ParticleEngine;Lnet/minecraft/core/particles/ParticleOptions;ZLnet/minecraft/util/RandomSource;)V'), ('com/elfmcys/yesstevemodel/OOoOOooOOOOOO0OO0O0o0OOo', 'Oo0Oo0o00O00Oo0OOoOOoooo', '(Lnet/minecraft/client/particle/ParticleEngine;Lnet/minecraft/core/particles/ParticleOptions;DDDDDDI)V'), ('com/elfmcys/yesstevemodel/OOoOOooOOOOOO0OO0O0o0OOo', 'o0OOooo0o0OO00OoOOOo0o0O', '(Lnet/minecraft/client/particle/ParticleEngine;Lnet/minecraft/core/particles/ParticleOptions;DDDDDDI)V'), ('com/elfmcys/yesstevemodel/OOoOOooOOOOOO0OO0O0o0OOo', 'Oo0Oo0o00O00Oo0OOoOOoooo', '(Ljava/lang/String;)Lnet/minecraft/core/particles/ParticleOptions;'), ('com/elfmcys/yesstevemodel/OOoOOooOOOOOO0OO0O0o0OOo', '<clinit>', '()V'), ('com/elfmcys/yesstevemodel/o0o00O0O0ooo00ooO0o00000$Oo0Oo0o00O00Oo0OOoOOoooo', '<init>', '()V'), ('com/elfmcys/yesstevemodel/o0o00O0O0ooo00ooO0o00000$Oo0Oo0o00O00Oo0OOoOOoooo', 'Oo0Oo0o00O00Oo0OOoOOoooo', '(Lcom/elfmcys/yesstevemodel/oO0OoO0O0OoO0oo0oo0OOooo;Lcom/elfmcys/yesstevemodel/O00OOo00o0O00ooo000OOo0O$Oo0Oo0o00O00Oo0OOoOOoooo;)Ljava/lang/Object;'), ('com/elfmcys/yesstevemodel/o0o00O0O0ooo00ooO0o00000$Oo0Oo0o00O00Oo0OOoOOoooo', 'Oo0Oo0o00O00Oo0OOoOOoooo', '(I)Z'), ('com/elfmcys/yesstevemodel/o0o00O0O0ooo00ooO0o00000$Oo0Oo0o00O00Oo0OOoOOoooo', 'Oo0Oo0o00O00Oo0OOoOOoooo', '(Lcom/elfmcys/yesstevemodel/oO0OoO0O0OoO0oo0oo0OOooo;Ljava/lang/String;ILcom/elfmcys/yesstevemodel/O00OOo00o0O00ooo000OOo0O$Oo0Oo0o00O00Oo0OOoOOoooo;Lcom/elfmcys/yesstevemodel/Oo0OoO0O00o00oOOooo00OOO;)V'), ('com/elfmcys/yesstevemodel/o0o00O0O0ooo00ooO0o00000$o0OOooo0o0OO00OoOOOo0o0O', '<init>', '()V'), ('com/elfmcys/yesstevemodel/o0o00O0O0ooo00ooO0o00000$o0OOooo0o0OO00OoOOOo0o0O', 'Oo0Oo0o00O00Oo0OOoOOoooo', '(Lcom/elfmcys/yesstevemodel/oO0OoO0O0OoO0oo0oo0OOooo;Lcom/elfmcys/yesstevemodel/O00OOo00o0O00ooo000OOo0O$Oo0Oo0o00O00Oo0OOoOOoooo;)Ljava/lang/Object;'), ('com/elfmcys/yesstevemodel/o0o00O0O0ooo00ooO0o00000$o0OOooo0o0OO00OoOOOo0o0O', 'Oo0Oo0o00O00Oo0OOoOOoooo', '(I)Z'), ('com/elfmcys/yesstevemodel/o0o00O0O0ooo00ooO0o00000$O00OOOooOoooOoo0o0o0oO0O', '<init>', '()V'), ('com/elfmcys/yesstevemodel/o0o00O0O0ooo00ooO0o00000$O00OOOooOoooOoo0o0o0oO0O', 'Oo0Oo0o00O00Oo0OOoOOoooo', '(Lcom/elfmcys/yesstevemodel/oO0OoO0O0OoO0oo0oo0OOooo;Lcom/elfmcys/yesstevemodel/O00OOo00o0O00ooo000OOo0O$Oo0Oo0o00O00Oo0OOoOOoooo;)Ljava/lang/Object;'), ('com/elfmcys/yesstevemodel/o0o00O0O0ooo00ooO0o00000$O00OOOooOoooOoo0o0o0oO0O', 'Oo0Oo0o00O00Oo0OOoOOoooo', '(I)Z'), ('com/elfmcys/yesstevemodel/OOOO0O0OO0oOOo00Ooo0oooO', '<init>', '()V'), ('com/elfmcys/yesstevemodel/OOOO0O0OO0oOOo00Ooo0oooO', 'Oo0Oo0o00O00Oo0OOoOOoooo', '(Lcom/elfmcys/yesstevemodel/o0000OoOooO0oo0o0oooo0Oo;ILjava/lang/String;ZLjava/util/function/Consumer;)Z'), ('com/elfmcys/yesstevemodel/OOOO0O0OO0oOOo00Ooo0oooO', 'Oo0Oo0o00O00Oo0OOoOOoooo', '(I)Z'), ('com/elfmcys/yesstevemodel/OOOO0O0OO0oOOo00Ooo0oooO', 'Oo0Oo0o00O00Oo0OOoOOoooo', '()V'), ('com/elfmcys/yesstevemodel/OOOO0O0OO0oOOo00Ooo0oooO', 'o0OOooo0o0OO00OoOOOo0o0O', '()V'), ('com/elfmcys/yesstevemodel/OOOO0O0OO0oOOo00Ooo0oooO', 'Oo0Oo0o00O00Oo0OOoOOoooo', '(Lcom/elfmcys/yesstevemodel/Oo0OoO0O00o00oOOooo00OOO;)V'), ('com/elfmcys/yesstevemodel/OOOO0O0OO0oOOo00Ooo0oooO', 'Oo0Oo0o00O00Oo0OOoOOoooo', '(Lcom/elfmcys/yesstevemodel/Oo0OoO0O00o00oOOooo00OOO;Ljava/lang/Integer;Lcom/elfmcys/yesstevemodel/o0OO0oo00ooOOOO0O0o0OoOo;)Lcom/elfmcys/yesstevemodel/o0OO0oo00ooOOOO0O0o0OoOo;'), ('com/elfmcys/yesstevemodel/OOOO0O0OO0oOOo00Ooo0oooO', 'Oo0Oo0o00O00Oo0OOoOOoooo', '(Lcom/elfmcys/yesstevemodel/o0000OoOooO0oo0o0oooo0Oo;Lcom/elfmcys/yesstevemodel/O0o0O0ooO0OO00o0OOoO0ooo;)Lcom/elfmcys/yesstevemodel/o0000oo0oOO00O00O0o0o0O0;'), ('com/elfmcys/yesstevemodel/O0O00Oo0o0oO0oo0oO00OOoO', 'Oo0Oo0o00O00Oo0OOoOOoooo', '(Z)Lcom/elfmcys/yesstevemodel/OOOO0O0OO0oOOo00Ooo0oooO;'), ('com/elfmcys/yesstevemodel/O0oo0oOo0OOOO00Oo0oo0o00', 'O00OOOooOoooOoo0o0o0oO0O', '()Lcom/elfmcys/yesstevemodel/OOOO0O0OO0oOOo00Ooo0oooO;'), ('com/elfmcys/yesstevemodel/o000o0o0Ooooo0ooo0oO0O0o', 'o0OOooo0o0OO00OoOOOo0o0O', '()Lcom/elfmcys/yesstevemodel/OOOO0O0OO0oOOo00Ooo0oooO;')])
SOURCES=[('src/main/java/com/elfmcys/yesstevemodel/client/animation/molang/functions/ParticleFunction.java', '4193dced86f10ae0f6664994cce37bbab7c13412cc4d1aa2b8d1d0bb1dba7c42', 'f184edabd1b5115ce5a24cb6d155ba5a669f5ba6'), ('src/main/java/com/elfmcys/yesstevemodel/client/particle/ParticleSpawner.java', 'f4d426db550bdeca9760cf2a7be529e5e74d3bc29856b9d38800f015a8a5b324', 'f184edabd1b5115ce5a24cb6d155ba5a669f5ba6'), ('src/main/java/com/elfmcys/yesstevemodel/client/animation/molang/functions/SoundFunction.java', 'fa809d15dd2d6f8b5f74576c00bcee3c0d41b61ec55218932d2491c20af18692', 'f184edabd1b5115ce5a24cb6d155ba5a669f5ba6'), ('src/main/java/com/elfmcys/yesstevemodel/client/animation/molang/functions/SoundFunction.java', 'fa809d15dd2d6f8b5f74576c00bcee3c0d41b61ec55218932d2491c20af18692', 'f184edabd1b5115ce5a24cb6d155ba5a669f5ba6'), ('src/main/java/com/elfmcys/yesstevemodel/client/animation/molang/functions/SoundFunction.java', 'fa809d15dd2d6f8b5f74576c00bcee3c0d41b61ec55218932d2491c20af18692', 'f184edabd1b5115ce5a24cb6d155ba5a669f5ba6'), ('src/main/java/com/elfmcys/yesstevemodel/client/sound/instance/SoundInstanceManager.java', 'be135ce35192d7a1b5dbfccbb19aa6dc47849be37fa91fc7a79817ecfad027b1', 'f184edabd1b5115ce5a24cb6d155ba5a669f5ba6'), ('src/main/java/com/elfmcys/yesstevemodel/geckolib3/core/molang/context/MolangContext.java', 'e47a7884eda1f3c1c6af8986c9487f39748c40d5f39b2bbfe3456a20185eaacd', 'f184edabd1b5115ce5a24cb6d155ba5a669f5ba6'), ('src/main/java/com/elfmcys/yesstevemodel/geckolib3/core/molang/context/ControllerContext.java', 'ff70626a71d3ed2314cd59ab740feb5379876173a375ace9eaaa5027eaa742c5', 'f184edabd1b5115ce5a24cb6d155ba5a669f5ba6'), ('src/main/java/com/elfmcys/yesstevemodel/geckolib3/core/molang/context/AnimationContext.java', '27bfa16fb3b44e8febd3b74158c2f4ad28c8a544c2b2225c8beaab76c23a9ef6', 'f184edabd1b5115ce5a24cb6d155ba5a669f5ba6')]

KEYS=('access','instructions','supplemental_full_operand_records','exception_handlers','code_sha256')
DECL=('access','super','interfaces','fields','methods')
def ident(m):return tuple(m.get(k) for k in ('owner','name','descriptor'))
def audit(e,actual,decl,details):
    checks=[]
    def ck(name,ok):checks.append({'check':name,'pass':bool(ok)})
    ck('fixed-artifact',e.get('artifact',{}).get('sha256')==SHA and e.get('artifact',{}).get('size')==SIZE)
    ck('detailed-operands',e.get('detailed_operands') is True)
    rows=e.get('members',[]);ids=[ident(m) for m in rows]
    ck('selected-32-methods',len(ids)==len(set(ids))==32 and set(ids)==set(actual)==SELECTED)
    for m in rows:
        a=actual.get(ident(m),{})
        for k in KEYS:ck(str(ident(m))+':'+k,(k in m)==(k in a) and m.get(k)==a.get(k))
    ds=e.get('owner_declarations',[]);ck('nine-declarations',len(ds)==9 and {r['owner'] for r in ds}==set(OWNERS))
    for r in ds:ck(r['owner']+':declaration',r['declaration']==decl.get(r['owner']))
    bs=e.get('bootstrap_and_constant_evidence',[]);ck('nine-bootstrap-records',len(bs)==9 and {r['owner'] for r in bs}==set(OWNERS))
    for r in bs:
        for k in ('constant_values','bootstrap_methods'):ck(r['owner']+':'+k,k in r and r[k]==details.get(r['owner'],{}).get(k))
    ss=e.get('source_tracks',[]);ck('nine-fixed-source-records',sorted((r.get('path'),r.get('sha256'),r.get('revision')) for r in ss)==sorted(SOURCES))
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
    neg('missing-effect-link-0',lambda x:member(x,0,'(Lcom/elfmcys/yesstevemodel/oO0OoO0O0OoO0oo0oo0OOooo;Lcom/elfmcys/yesstevemodel/O00OOo00o0O00ooo000OOo0O$Oo0Oo0o00O00Oo0OOoOOoooo;)Ljava/lang/Object;','Oo0Oo0o00O00Oo0OOoOOoooo')['instructions'].pop())
    neg('missing-effect-link-1',lambda x:member(x,1,'(Lcom/elfmcys/yesstevemodel/oO0OoO0O0OoO0oo0oo0OOooo;Lcom/elfmcys/yesstevemodel/O00OOo00o0O00ooo000OOo0O$Oo0Oo0o00O00Oo0OOoOOoooo;Z)Z','Oo0Oo0o00O00Oo0OOoOOoooo')['instructions'].pop())
    neg('missing-effect-link-2',lambda x:member(x,2,'(Lcom/elfmcys/yesstevemodel/oO0OoO0O0OoO0oo0oo0OOooo;Lcom/elfmcys/yesstevemodel/O00OOo00o0O00ooo000OOo0O$Oo0Oo0o00O00Oo0OOoOOoooo;)Ljava/lang/Object;','Oo0Oo0o00O00Oo0OOoOOoooo')['instructions'].pop())
    neg('missing-effect-link-3',lambda x:member(x,3,'(Lcom/elfmcys/yesstevemodel/oO0OoO0O0OoO0oo0oo0OOooo;Lcom/elfmcys/yesstevemodel/O00OOo00o0O00ooo000OOo0O$Oo0Oo0o00O00Oo0OOoOOoooo;)Ljava/lang/Object;','Oo0Oo0o00O00Oo0OOoOOoooo')['instructions'].pop())
    neg('missing-effect-link-4',lambda x:member(x,4,'(Lcom/elfmcys/yesstevemodel/oO0OoO0O0OoO0oo0oo0OOooo;Lcom/elfmcys/yesstevemodel/O00OOo00o0O00ooo000OOo0O$Oo0Oo0o00O00Oo0OOoOOoooo;)Ljava/lang/Object;','Oo0Oo0o00O00Oo0OOoOOoooo')['instructions'].pop())
    neg('missing-effect-link-5',lambda x:member(x,5,'(Lcom/elfmcys/yesstevemodel/o0000OoOooO0oo0o0oooo0Oo;ILjava/lang/String;ZLjava/util/function/Consumer;)Z','Oo0Oo0o00O00Oo0OOoOOoooo')['instructions'].pop())
    neg('missing-effect-link-6',lambda x:member(x,6,'(Z)Lcom/elfmcys/yesstevemodel/OOOO0O0OO0oOOo00Ooo0oooO;','Oo0Oo0o00O00Oo0OOoOOoooo')['instructions'].pop())
    neg('missing-effect-link-7',lambda x:member(x,7,'()Lcom/elfmcys/yesstevemodel/OOOO0O0OO0oOOo00Ooo0oooO;','O00OOOooOoooOoo0o0o0oO0O')['instructions'].pop())
    neg('missing-effect-link-8',lambda x:member(x,8,'()Lcom/elfmcys/yesstevemodel/OOOO0O0OO0oOOo00Ooo0oooO;','o0OOooo0o0OO00OoOOOo0o0O')['instructions'].pop())
    neg('lost-particle-exception-handler',lambda x:member(x,0,'(Lcom/elfmcys/yesstevemodel/oO0OoO0O0OoO0oo0oo0OOooo;Lcom/elfmcys/yesstevemodel/O00OOo00o0O00ooo000OOo0O$Oo0Oo0o00O00Oo0OOoOOoooo;)Ljava/lang/Object;')['exception_handlers'].pop())
    result={'artifact_sha256':SHA,'checks':checks,'negative_controls':negatives,'failures':[c for c in checks if not c['pass']],'negative_failures':[n for n in negatives if not n['rejected']],'independent_semantic_review':'NOT_RUN','runtime_executed':False,'central_mapping_promoted':False}
    Path(a.out).write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({'checks':len(checks),'negative_controls':len(negatives),'failures':len(result['failures'])+len(result['negative_failures'])}))
    if result['failures'] or result['negative_failures']:raise SystemExit(1)
if __name__=='__main__':main()
