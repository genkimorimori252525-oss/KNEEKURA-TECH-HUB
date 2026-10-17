#!/usr/bin/env python3
"""WORLD-QUERY-INPUT fixed-artifact integrity audit; does not execute target classes or independently prove prose semantics."""
import argparse,copy,hashlib,json,subprocess,zipfile
from pathlib import Path
from audit_seed_recovery_ysm_265 import parse_bounded,BOUNDDETAILS
from scan_ysm_265 import parse_class
SHA='25b5e902b96f4c298690208f8b433cbc31737c23f87590354dbd86f00207bc8f'
SIZE=63269843
OWNERS=['com/elfmcys/yesstevemodel/OOO0o0o0o0oOOoOOo00OOOOO', 'com/elfmcys/yesstevemodel/o0OO000O0OoOOoOO00ooo00O', 'com/elfmcys/yesstevemodel/OOoOOO0o0OoooOO00oO0ooOO', 'com/elfmcys/yesstevemodel/O000O00o0OO0o0O0OoOo000O', 'com/elfmcys/yesstevemodel/o0o000OOo0000OOOOOOoOOO0', 'com/elfmcys/yesstevemodel/O0oo000oo0oOOOooOOo0ooOO', 'com/elfmcys/yesstevemodel/ooO00OOOOOo0oOoooO00oOoO', 'com/elfmcys/yesstevemodel/oOO0OO0OOO0ooOo000o0O0OO', 'com/elfmcys/yesstevemodel/o0000OOo0000oo000OOOo0o0']
SELECTED=set([('com/elfmcys/yesstevemodel/OOO0o0o0o0oOOoOOo00OOOOO', '<init>', '()V'), ('com/elfmcys/yesstevemodel/OOO0o0o0o0oOOoOOo00OOOOO', 'Oo0Oo0o00O00Oo0OOoOOoooo', '(Lcom/elfmcys/yesstevemodel/oO0OoO0O0OoO0oo0oo0OOooo;Lcom/elfmcys/yesstevemodel/O00OOo00o0O00ooo000OOo0O$Oo0Oo0o00O00Oo0OOoOOoooo;)Ljava/lang/Object;'), ('com/elfmcys/yesstevemodel/OOO0o0o0o0oOOoOOo00OOOOO', 'Oo0Oo0o00O00Oo0OOoOOoooo', '(I)Z'), ('com/elfmcys/yesstevemodel/o0OO000O0OoOOoOO00ooo00O', '<init>', '()V'), ('com/elfmcys/yesstevemodel/o0OO000O0OoOOoOO00ooo00O', 'Oo0Oo0o00O00Oo0OOoOOoooo', '(Lcom/elfmcys/yesstevemodel/oO0OoO0O0OoO0oo0oo0OOooo;Lcom/elfmcys/yesstevemodel/O00OOo00o0O00ooo000OOo0O$Oo0Oo0o00O00Oo0OOoOOoooo;)Ljava/lang/Object;'), ('com/elfmcys/yesstevemodel/o0OO000O0OoOOoOO00ooo00O', 'Oo0Oo0o00O00Oo0OOoOOoooo', '(I)Z'), ('com/elfmcys/yesstevemodel/OOoOOO0o0OoooOO00oO0ooOO', '<init>', '()V'), ('com/elfmcys/yesstevemodel/OOoOOO0o0OoooOO00oO0ooOO', 'Oo0Oo0o00O00Oo0OOoOOoooo', '(Lcom/elfmcys/yesstevemodel/oO0OoO0O0OoO0oo0oo0OOooo;Lcom/elfmcys/yesstevemodel/O00OOo00o0O00ooo000OOo0O$Oo0Oo0o00O00Oo0OOoOOoooo;)Ljava/lang/Object;'), ('com/elfmcys/yesstevemodel/OOoOOO0o0OoooOO00oO0ooOO', 'Oo0Oo0o00O00Oo0OOoOOoooo', '(I)Z'), ('com/elfmcys/yesstevemodel/O000O00o0OO0o0O0OoOo000O', '<init>', '()V'), ('com/elfmcys/yesstevemodel/O000O00o0OO0o0O0OoOo000O', 'Oo0Oo0o00O00Oo0OOoOOoooo', '(Lcom/elfmcys/yesstevemodel/oO0OoO0O0OoO0oo0oo0OOooo;Lcom/elfmcys/yesstevemodel/O00OOo00o0O00ooo000OOo0O$Oo0Oo0o00O00Oo0OOoOOoooo;)Ljava/lang/Object;'), ('com/elfmcys/yesstevemodel/O000O00o0OO0o0O0OoOo000O', 'Oo0Oo0o00O00Oo0OOoOOoooo', '(I)Z'), ('com/elfmcys/yesstevemodel/o0o000OOo0000OOOOOOoOOO0', '<init>', '()V'), ('com/elfmcys/yesstevemodel/o0o000OOo0000OOOOOOoOOO0', 'Oo0Oo0o00O00Oo0OOoOOoooo', '(Lcom/elfmcys/yesstevemodel/oO0OoO0O0OoO0oo0oo0OOooo;Lcom/elfmcys/yesstevemodel/O00OOo00o0O00ooo000OOo0O$Oo0Oo0o00O00Oo0OOoOOoooo;)Ljava/lang/Object;'), ('com/elfmcys/yesstevemodel/o0o000OOo0000OOOOOOoOOO0', 'Oo0Oo0o00O00Oo0OOoOOoooo', '(I)Z'), ('com/elfmcys/yesstevemodel/O0oo000oo0oOOOooOOo0ooOO', '<init>', '()V'), ('com/elfmcys/yesstevemodel/O0oo000oo0oOOOooOOo0ooOO', 'Oo0Oo0o00O00Oo0OOoOOoooo', '(Lcom/elfmcys/yesstevemodel/oO0OoO0O0OoO0oo0oo0OOooo;Lcom/elfmcys/yesstevemodel/O00OOo00o0O00ooo000OOo0O$Oo0Oo0o00O00Oo0OOoOOoooo;)Ljava/lang/Object;'), ('com/elfmcys/yesstevemodel/O0oo000oo0oOOOooOOo0ooOO', 'Oo0Oo0o00O00Oo0OOoOOoooo', '(I)Z'), ('com/elfmcys/yesstevemodel/ooO00OOOOOo0oOoooO00oOoO', '<init>', '()V'), ('com/elfmcys/yesstevemodel/ooO00OOOOOo0oOoooO00oOoO', 'Oo0Oo0o00O00Oo0OOoOOoooo', '(Lcom/elfmcys/yesstevemodel/oo0oOO0000o0Ooooo0OoOo0O;)Z'), ('com/elfmcys/yesstevemodel/oOO0OO0OOO0ooOo000o0O0OO', 'Oo0Oo0o00O00Oo0OOoOOoooo', '(Lcom/elfmcys/yesstevemodel/oO0OoO0O0OoO0oo0oo0OOooo;Lcom/elfmcys/yesstevemodel/O00OOo00o0O00ooo000OOo0O$Oo0Oo0o00O00Oo0OOoOOoooo;)Lnet/minecraft/world/level/block/state/BlockState;'), ('com/elfmcys/yesstevemodel/oOO0OO0OOO0ooOo000o0O0OO', 'Oo0Oo0o00O00Oo0OOoOOoooo', '(Lcom/elfmcys/yesstevemodel/oO0OoO0O0OoO0oo0oo0OOooo;Lcom/elfmcys/yesstevemodel/O00OOo00o0O00ooo000OOo0O$Oo0Oo0o00O00Oo0OOoOOoooo;I)Lnet/minecraft/world/level/block/state/BlockState;'), ('com/elfmcys/yesstevemodel/o0000OOo0000oo000OOOo0o0', '<init>', '()V')])
SOURCES=[('src/main/java/com/elfmcys/yesstevemodel/geckolib3/core/molang/builtin/query/BiomeHasAllTags.java', '1e8e8d9094b03c77dea75d8c43a2fe9d920784f6d89c41d36a51785bdaa94131', 'f184edabd1b5115ce5a24cb6d155ba5a669f5ba6'), ('src/main/java/com/elfmcys/yesstevemodel/geckolib3/core/molang/builtin/query/BiomeHasAnyTag.java', '39791a948c8c4b4da4c7f8a9453f75ddceb75784e409d15ea1a9c1f067818228', 'f184edabd1b5115ce5a24cb6d155ba5a669f5ba6'), ('src/main/java/com/elfmcys/yesstevemodel/geckolib3/core/molang/builtin/query/RelativeBlockHasAllTags.java', 'cbbdf5f514b9db4a7e96bda2243747541a0a356c2312e33dcd630c1884e2a781', 'f184edabd1b5115ce5a24cb6d155ba5a669f5ba6'), ('src/main/java/com/elfmcys/yesstevemodel/geckolib3/core/molang/builtin/query/RelativeBlockHasAnyTag.java', '05a87d25157f87f2790f6b4c26bd73c228862ae2807bfea7fde06f6ea0134b6a', 'f184edabd1b5115ce5a24cb6d155ba5a669f5ba6'), ('src/main/java/com/elfmcys/yesstevemodel/geckolib3/core/molang/builtin/query/Position.java', 'e5efd3870638e8ec2821ef9b1658d0b44792c23849e4d5d027ab5a478948e82f', 'f184edabd1b5115ce5a24cb6d155ba5a669f5ba6'), ('src/main/java/com/elfmcys/yesstevemodel/client/animation/molang/functions/Rot2Camera.java', 'aa2678b898194ccf63b003f29c705647de06ca774cc2305ba19ce27ff651353d', 'f184edabd1b5115ce5a24cb6d155ba5a669f5ba6'), ('src/main/java/com/elfmcys/yesstevemodel/geckolib3/core/molang/function/entity/EntityFunction.java', 'd913a992a5645bd576ec186255d36085158c5998faca821210372bd4a02a1a63', 'f184edabd1b5115ce5a24cb6d155ba5a669f5ba6'), ('src/main/java/com/elfmcys/yesstevemodel/geckolib3/util/MolangUtils.java', '3316e1205fb016ff3a9985b279a546d0c4a8bd6653d24448107659e2dc39fcaf', 'f184edabd1b5115ce5a24cb6d155ba5a669f5ba6'), ('src/main/java/com/elfmcys/yesstevemodel/geckolib3/core/molang/builtin/QueryBinding.java', 'f5fdc573ed9187fcf72465abe5ac19a0f16cd39c7e2d0edc66d1c2de1473bfc8', 'f184edabd1b5115ce5a24cb6d155ba5a669f5ba6')]

KEYS=('access','instructions','supplemental_full_operand_records','exception_handlers','code_sha256')
DECL=('access','super','interfaces','fields','methods')
def ident(m):return tuple(m.get(k) for k in ('owner','name','descriptor'))
def audit(e,actual,decl,details):
    checks=[]
    def ck(name,ok):checks.append({'check':name,'pass':bool(ok)})
    ck('fixed-artifact',e.get('artifact',{}).get('sha256')==SHA and e.get('artifact',{}).get('size')==SIZE)
    ck('detailed-operands',e.get('detailed_operands') is True)
    rows=e.get('members',[]);ids=[ident(m) for m in rows]
    ck('selected-23-methods',len(ids)==len(set(ids))==23 and set(ids)==set(actual)==SELECTED)
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
    neg('missing-query-support-OOO0o0o0o0oOOoOOo00OOOOO',lambda x:member(x,0,'(Lcom/elfmcys/yesstevemodel/oO0OoO0O0OoO0oo0oo0OOooo;Lcom/elfmcys/yesstevemodel/O00OOo00o0O00ooo000OOo0O$Oo0Oo0o00O00Oo0OOoOOoooo;)Ljava/lang/Object;','Oo0Oo0o00O00Oo0OOoOOoooo')['instructions'].pop())
    neg('missing-query-support-o0OO000O0OoOOoOO00ooo00O',lambda x:member(x,1,'(Lcom/elfmcys/yesstevemodel/oO0OoO0O0OoO0oo0oo0OOooo;Lcom/elfmcys/yesstevemodel/O00OOo00o0O00ooo000OOo0O$Oo0Oo0o00O00Oo0OOoOOoooo;)Ljava/lang/Object;','Oo0Oo0o00O00Oo0OOoOOoooo')['instructions'].pop())
    neg('missing-query-support-OOoOOO0o0OoooOO00oO0ooOO',lambda x:member(x,2,'(Lcom/elfmcys/yesstevemodel/oO0OoO0O0OoO0oo0oo0OOooo;Lcom/elfmcys/yesstevemodel/O00OOo00o0O00ooo000OOo0O$Oo0Oo0o00O00Oo0OOoOOoooo;)Ljava/lang/Object;','Oo0Oo0o00O00Oo0OOoOOoooo')['instructions'].pop())
    neg('missing-query-support-O000O00o0OO0o0O0OoOo000O',lambda x:member(x,3,'(Lcom/elfmcys/yesstevemodel/oO0OoO0O0OoO0oo0oo0OOooo;Lcom/elfmcys/yesstevemodel/O00OOo00o0O00ooo000OOo0O$Oo0Oo0o00O00Oo0OOoOOoooo;)Ljava/lang/Object;','Oo0Oo0o00O00Oo0OOoOOoooo')['instructions'].pop())
    neg('missing-query-support-o0o000OOo0000OOOOOOoOOO0',lambda x:member(x,4,'(Lcom/elfmcys/yesstevemodel/oO0OoO0O0OoO0oo0oo0OOooo;Lcom/elfmcys/yesstevemodel/O00OOo00o0O00ooo000OOo0O$Oo0Oo0o00O00Oo0OOoOOoooo;)Ljava/lang/Object;','Oo0Oo0o00O00Oo0OOoOOoooo')['instructions'].pop())
    neg('missing-query-support-O0oo000oo0oOOOooOOo0ooOO',lambda x:member(x,5,'(Lcom/elfmcys/yesstevemodel/oO0OoO0O0OoO0oo0oo0OOooo;Lcom/elfmcys/yesstevemodel/O00OOo00o0O00ooo000OOo0O$Oo0Oo0o00O00Oo0OOoOOoooo;)Ljava/lang/Object;','Oo0Oo0o00O00Oo0OOoOOoooo')['instructions'].pop())
    neg('missing-query-support-ooO00OOOOOo0oOoooO00oOoO',lambda x:member(x,6,'(Lcom/elfmcys/yesstevemodel/oo0oOO0000o0Ooooo0OoOo0O;)Z','Oo0Oo0o00O00Oo0OOoOOoooo')['instructions'].pop())
    neg('missing-query-support-oOO0OO0OOO0ooOo000o0O0OO',lambda x:member(x,7,'(Lcom/elfmcys/yesstevemodel/oO0OoO0O0OoO0oo0oo0OOooo;Lcom/elfmcys/yesstevemodel/O00OOo00o0O00ooo000OOo0O$Oo0Oo0o00O00Oo0OOoOOoooo;)Lnet/minecraft/world/level/block/state/BlockState;','Oo0Oo0o00O00Oo0OOoOOoooo')['instructions'].pop())
    neg('missing-query-support-o0000OOo0000oo000OOOo0o0',lambda x:member(x,8,'()V','<init>')['instructions'].pop())
    neg('relative-range-constant-altered',lambda x:op(x,7,'(Lcom/elfmcys/yesstevemodel/oO0OoO0O0OoO0oo0oo0OOooo;Lcom/elfmcys/yesstevemodel/O00OOo00o0O00ooo000OOo0O$Oo0Oo0o00O00Oo0OOoOOoooo;I)Lnet/minecraft/world/level/block/state/BlockState;',31)['reference'].update(value=6.0))
    result={'artifact_sha256':SHA,'checks':checks,'negative_controls':negatives,'failures':[c for c in checks if not c['pass']],'negative_failures':[n for n in negatives if not n['rejected']],'independent_semantic_review':'NOT_RUN','runtime_executed':False,'central_mapping_promoted':False}
    Path(a.out).write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({'checks':len(checks),'negative_controls':len(negatives),'failures':len(result['failures'])+len(result['negative_failures'])}))
    if result['failures'] or result['negative_failures']:raise SystemExit(1)
if __name__=='__main__':main()
