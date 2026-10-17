#!/usr/bin/env python3
"""VIEW-TEXTURE-INPUT fixed-artifact integrity audit; does not execute target classes or independently prove prose semantics."""
import argparse,copy,hashlib,json,subprocess,zipfile
from pathlib import Path
from audit_seed_recovery_ysm_265 import parse_bounded,BOUNDDETAILS
from scan_ysm_265 import parse_class
SHA='25b5e902b96f4c298690208f8b433cbc31737c23f87590354dbd86f00207bc8f'
SIZE=63269843
OWNERS=['com/elfmcys/yesstevemodel/ooooO00oOo0Oo0Oo0OO0OOOo', 'com/elfmcys/yesstevemodel/O0O0o0Oo0OOoo0o0Oo0O00O0', 'com/elfmcys/yesstevemodel/O0O0o0OOOoOoO0OOooOoooO0', 'com/elfmcys/yesstevemodel/oOO0OOo0O000ooOo00O0O0OO', 'com/elfmcys/yesstevemodel/OoO00Oo00Ooo0OoOoo00o000', 'com/elfmcys/yesstevemodel/o0O0oOooOo0OoOo0oOo00O00', 'com/elfmcys/yesstevemodel/OO0oooO0OO0o00oOOoOoOoOo', 'com/elfmcys/yesstevemodel/o0000OOo0000oo000OOOo0o0', 'com/elfmcys/yesstevemodel/oo00O000000OoOo0O0O00oOO']
SELECTED=set([('com/elfmcys/yesstevemodel/ooooO00oOo0Oo0Oo0OO0OOOo', '<init>', '()V'), ('com/elfmcys/yesstevemodel/ooooO00oOo0Oo0Oo0OO0OOOo', 'Oo0Oo0o00O00Oo0OOoOOoooo', '(Lcom/elfmcys/yesstevemodel/oo0oOO0000o0Ooooo0OoOo0O;)I'), ('com/elfmcys/yesstevemodel/ooooO00oOo0Oo0Oo0OO0OOOo', 'Oo0Oo0o00O00Oo0OOoOOoooo', '(Lcom/elfmcys/yesstevemodel/o0000OoOooO0oo0o0oooo0Oo;)Z'), ('com/elfmcys/yesstevemodel/ooooO00oOo0Oo0Oo0OO0OOOo', 'o0OOooo0o0OO00OoOOOo0o0O', '(Lcom/elfmcys/yesstevemodel/oo0oOO0000o0Ooooo0OoOo0O;)Z'), ('com/elfmcys/yesstevemodel/ooooO00oOo0Oo0Oo0OO0OOOo', 'o0OOooo0o0OO00OoOOOo0o0O', '(Lcom/elfmcys/yesstevemodel/o0000OoOooO0oo0o0oooo0Oo;)Z'), ('com/elfmcys/yesstevemodel/O0O0o0Oo0OOoo0o0Oo0O00O0', '<init>', '()V'), ('com/elfmcys/yesstevemodel/O0O0o0Oo0OOoo0o0Oo0O00O0', 'Oo0Oo0o00O00Oo0OOoOOoooo', '(Lcom/elfmcys/yesstevemodel/oo0oOO0000o0Ooooo0OoOo0O;)Ljava/lang/String;'), ('com/elfmcys/yesstevemodel/O0O0o0Oo0OOoo0o0Oo0O00O0', 'eval', '(Ljava/lang/Object;)Ljava/lang/Object;'), ('com/elfmcys/yesstevemodel/O0O0o0OOOoOoO0OOooOoooO0', '<init>', '()V'), ('com/elfmcys/yesstevemodel/O0O0o0OOOoOoO0OOooOoooO0', 'Oo0Oo0o00O00Oo0OOoOOoooo', '(Lcom/elfmcys/yesstevemodel/oo0oOO0000o0Ooooo0OoOo0O;)Ljava/lang/Boolean;'), ('com/elfmcys/yesstevemodel/O0O0o0OOOoOoO0OOooOoooO0', 'eval', '(Ljava/lang/Object;)Ljava/lang/Object;'), ('com/elfmcys/yesstevemodel/oOO0OOo0O000ooOo00O0O0OO', '<init>', '()V'), ('com/elfmcys/yesstevemodel/oOO0OOo0O000ooOo00O0O0OO', 'Oo0Oo0o00O00Oo0OOoOOoooo', '()V'), ('com/elfmcys/yesstevemodel/oOO0OOo0O000ooOo00O0O0OO', 'o0OOooo0o0OO00OoOOOo0o0O', '()Z'), ('com/elfmcys/yesstevemodel/oOO0OOo0O000ooOo00O0O0OO', 'Ooooo0oooO0oooOOOoO0000O', '()V'), ('com/elfmcys/yesstevemodel/oOO0OOo0O000ooOo00O0O0OO', 'O00OOOooOoooOoo0o0o0oO0O', '()Z'), ('com/elfmcys/yesstevemodel/oOO0OOo0O000ooOo00O0O0OO', 'oOOOo0OOO0ooooo0O00OO0o0', '()Z'), ('com/elfmcys/yesstevemodel/oOO0OOo0O000ooOo00O0O0OO', 'Oo0Oo0o00O00Oo0OOoOOoooo', '(F)V'), ('com/elfmcys/yesstevemodel/oOO0OOo0O000ooOo00O0O0OO', 'OOOOo0O0oO0OOo0O0O0Oo0O0', '()Z'), ('com/elfmcys/yesstevemodel/oOO0OOo0O000ooOo00O0O0OO', 'Oo0Oo0o00O00Oo0OOoOOoooo', '(Lnet/minecraft/client/player/AbstractClientPlayer;FLnet/minecraft/world/phys/Vec3;Lnet/minecraft/world/phys/Vec3;)Lnet/minecraft/world/phys/Vec3;'), ('com/elfmcys/yesstevemodel/OoO00Oo00Ooo0OoOoo00o000', 'Oo0Oo0o00O00Oo0OOoOOoooo', '(Z)V'), ('com/elfmcys/yesstevemodel/OoO00Oo00Ooo0OoOoo00o000', 'Oo0Oo0o00O00Oo0OOoOOoooo', '()Z'), ('com/elfmcys/yesstevemodel/OoO00Oo00Ooo0OoOoo00o000', 'o0OOooo0o0OO00OoOOOo0o0O', '(Z)V'), ('com/elfmcys/yesstevemodel/OoO00Oo00Ooo0OoOoo00o000', 'o0OOooo0o0OO00OoOOOo0o0O', '()Z'), ('com/elfmcys/yesstevemodel/OoO00Oo00Ooo0OoOoo00o000', 'O00OOOooOoooOoo0o0o0oO0O', '(Z)V'), ('com/elfmcys/yesstevemodel/OoO00Oo00Ooo0OoOoo00o000', 'O00OOOooOoooOoo0o0o0oO0O', '()Z'), ('com/elfmcys/yesstevemodel/OoO00Oo00Ooo0OoOoo00o000', 'oOOOo0OOO0ooooo0O00OO0o0', '()Z'), ('com/elfmcys/yesstevemodel/o0O0oOooOo0OoOo0oOo00O00', 'Oo00o0OooOOo0ooOoo0oO0o0', '()V'), ('com/elfmcys/yesstevemodel/o0O0oOooOo0OoOo0oOo00O00', 'oOoO0Oo0oO0o00O0oO0ooooo', '()Ljava/lang/String;'), ('com/elfmcys/yesstevemodel/OO0oooO0OO0o00oOOoOoOoOo', 'o0OOooo0o0OO00OoOOOo0o0O', '()Z'), ('com/elfmcys/yesstevemodel/OO0oooO0OO0o00oOOoOoOoOo', 'O00OOOooOoooOoo0o0o0oO0O', '()Z'), ('com/elfmcys/yesstevemodel/o0000OOo0000oo000OOOo0o0', 'OOOoOOo0oO00O0OoOO0oO00O', '(Lcom/elfmcys/yesstevemodel/oo0oOO0000o0Ooooo0OoOo0O;)Ljava/lang/Object;'), ('com/elfmcys/yesstevemodel/oo00O000000OoOo0O0O00oOO', 'o0Oo0oO0OO00O0ooOo0o0Ooo', '(Lcom/elfmcys/yesstevemodel/oo0oOO0000o0Ooooo0OoOo0O;)Ljava/lang/Object;')])
SOURCES=[('src/main/java/com/elfmcys/yesstevemodel/util/PersonView.java', 'b991ab0ed590fed9bb80320ea08a61d1b97ba353537f35041128f72fe8dbb4bd', 'f184edabd1b5115ce5a24cb6d155ba5a669f5ba6'), ('src/main/java/com/elfmcys/yesstevemodel/client/animation/molang/variable/TextureNameVariable.java', '7bdcc1d75e49771144edc8f9009538025a5f658b7c2a67fdc78c57a3e1c3b59d', 'f184edabd1b5115ce5a24cb6d155ba5a669f5ba6'), ('src/main/java/com/elfmcys/yesstevemodel/client/animation/molang/variable/FirstPersonModHideVariable.java', 'd70c72b6b3351185e90a8ef833b640697e63b5608f64b9e77df3e2faf81b5dc5', 'f184edabd1b5115ce5a24cb6d155ba5a669f5ba6'), ('src/main/java/com/elfmcys/yesstevemodel/client/compat/FirstPersonCompat.java', '32fd95b2aa2d57bb7d83256c1ad636863cc5d01c0df77e06d0536a052b37088c', 'f184edabd1b5115ce5a24cb6d155ba5a669f5ba6'), ('src/main/java/com/elfmcys/yesstevemodel/util/RenderUtil.java', 'b181c57910eeb0db57a69b7b956b5b74dd03275ad285470709e80c9aaaa2fae1', 'f184edabd1b5115ce5a24cb6d155ba5a669f5ba6'), ('src/main/java/com/elfmcys/yesstevemodel/client/entity/CustomHumanoidEntity.java', 'a5def776d16ae1164d7f559ddb0809a979b253f8c4b0367c471486d81c6246e0', 'f184edabd1b5115ce5a24cb6d155ba5a669f5ba6'), ('src/main/java/com/elfmcys/yesstevemodel/client/compat/IrisCompat.java', '7e3dd22456e2e1ba9ee7661039170d981a9e4fa6118681ad96232b44afe141e6', 'f184edabd1b5115ce5a24cb6d155ba5a669f5ba6'), ('src/main/java/com/elfmcys/yesstevemodel/geckolib3/core/molang/builtin/QueryBinding.java', 'f5fdc573ed9187fcf72465abe5ac19a0f16cd39c7e2d0edc66d1c2de1473bfc8', 'f184edabd1b5115ce5a24cb6d155ba5a669f5ba6'), ('src/main/java/com/elfmcys/yesstevemodel/client/animation/molang/YSMBinding.java', '22bf1679ba5a8967b09109795fff207afdd2cb45ba34c4f70fb9ca4c9ca117a0', 'f184edabd1b5115ce5a24cb6d155ba5a669f5ba6')]

KEYS=('access','instructions','supplemental_full_operand_records','exception_handlers','code_sha256')
DECL=('access','super','interfaces','fields','methods')
def ident(m):return tuple(m.get(k) for k in ('owner','name','descriptor'))
def audit(e,actual,decl,details):
    checks=[]
    def ck(name,ok):checks.append({'check':name,'pass':bool(ok)})
    ck('fixed-artifact',e.get('artifact',{}).get('sha256')==SHA and e.get('artifact',{}).get('size')==SIZE)
    ck('detailed-operands',e.get('detailed_operands') is True)
    rows=e.get('members',[]);ids=[ident(m) for m in rows]
    ck('selected-33-methods',len(ids)==len(set(ids))==33 and set(ids)==set(actual)==SELECTED)
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
    neg('missing-view-source-0',lambda x:member(x,0,'(Lcom/elfmcys/yesstevemodel/oo0oOO0000o0Ooooo0OoOo0O;)I','Oo0Oo0o00O00Oo0OOoOOoooo')['instructions'].pop())
    neg('missing-view-source-1',lambda x:member(x,1,'(Lcom/elfmcys/yesstevemodel/oo0oOO0000o0Ooooo0OoOo0O;)Ljava/lang/String;','Oo0Oo0o00O00Oo0OOoOOoooo')['instructions'].pop())
    neg('missing-view-source-2',lambda x:member(x,2,'(Lcom/elfmcys/yesstevemodel/oo0oOO0000o0Ooooo0OoOo0O;)Ljava/lang/Boolean;','Oo0Oo0o00O00Oo0OOoOOoooo')['instructions'].pop())
    neg('missing-view-source-3',lambda x:member(x,3,'()V','Oo0Oo0o00O00Oo0OOoOOoooo')['instructions'].pop())
    neg('missing-view-source-4',lambda x:member(x,4,'(Z)V','Oo0Oo0o00O00Oo0OOoOOoooo')['instructions'].pop())
    neg('missing-view-source-5',lambda x:member(x,5,'()V','Oo00o0OooOOo0ooOoo0oO0o0')['instructions'].pop())
    neg('missing-view-source-6',lambda x:member(x,6,'()Z','o0OOooo0o0OO00OoOOOo0o0O')['instructions'].pop())
    neg('missing-view-source-7',lambda x:member(x,7,'(Lcom/elfmcys/yesstevemodel/oo0oOO0000o0Ooooo0OoOo0O;)Ljava/lang/Object;','OOOoOOo0oO00O0OoOO0oO00O')['instructions'].pop())
    neg('missing-view-source-8',lambda x:member(x,8,'(Lcom/elfmcys/yesstevemodel/oo0oOO0000o0Ooooo0OoOo0O;)Ljava/lang/Object;','o0Oo0oO0OO00O0ooOo0o0Ooo')['instructions'].pop())
    result={'artifact_sha256':SHA,'checks':checks,'negative_controls':negatives,'failures':[c for c in checks if not c['pass']],'negative_failures':[n for n in negatives if not n['rejected']],'independent_semantic_review':'NOT_RUN','runtime_executed':False,'central_mapping_promoted':False}
    Path(a.out).write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({'checks':len(checks),'negative_controls':len(negatives),'failures':len(result['failures'])+len(result['negative_failures'])}))
    if result['failures'] or result['negative_failures']:raise SystemExit(1)
if __name__=='__main__':main()
