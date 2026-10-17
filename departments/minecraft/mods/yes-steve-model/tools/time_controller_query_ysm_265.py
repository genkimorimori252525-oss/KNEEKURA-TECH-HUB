#!/usr/bin/env python3
"""TIME-CONTROLLER-QUERY fixed-artifact integrity audit; does not execute target classes or independently prove prose semantics."""
import argparse,copy,hashlib,json,subprocess,zipfile
from pathlib import Path
from audit_seed_recovery_ysm_265 import parse_bounded,BOUNDDETAILS
from scan_ysm_265 import parse_class
SHA='25b5e902b96f4c298690208f8b433cbc31737c23f87590354dbd86f00207bc8f'
SIZE=63269843
OWNERS=['com/elfmcys/yesstevemodel/o0000OOo0000oo000OOOo0o0', 'com/elfmcys/yesstevemodel/oOO0OO0OOO0ooOo000o0O0OO', 'com/elfmcys/yesstevemodel/O0oo0oOo0OOOO00Oo0oo0o00', 'com/elfmcys/yesstevemodel/o000o0o0Ooooo0ooo0oO0O0o', 'com/elfmcys/yesstevemodel/O00Oo0oo0Ooo0oOOOo0OO0oO', 'com/elfmcys/yesstevemodel/oo000oooo0OOoo00O0o0OOOO', 'com/elfmcys/yesstevemodel/OOOO0o0oo0o000oOOooOoOo0']
SELECTED=set([('com/elfmcys/yesstevemodel/o0000OOo0000oo000OOOo0o0', '<init>', '()V'), ('com/elfmcys/yesstevemodel/o0000OOo0000oo000OOOo0o0', 'Oo0Oo0o00O00Oo0OOoOOoooo', '(Lcom/elfmcys/yesstevemodel/oo0oOO0000o0Ooooo0OoOo0O;)Ljava/util/Optional;'), ('com/elfmcys/yesstevemodel/o0000OOo0000oo000OOOo0o0', 'o0OOooo0o0OO00OoOOOo0o0O', '(Lcom/elfmcys/yesstevemodel/oo0oOO0000o0Ooooo0OoOo0O;)Ljava/util/Optional;'), ('com/elfmcys/yesstevemodel/o0000OOo0000oo000OOOo0o0', 'OO00OOOOo0Ooo0oo0o0Oo0OO', '(Lcom/elfmcys/yesstevemodel/oo0oOO0000o0Ooooo0OoOo0O;)Ljava/lang/Object;'), ('com/elfmcys/yesstevemodel/o0000OOo0000oo000OOOo0o0', 'OoOOOOOo0oo0000oooOOOoOO', '(Lcom/elfmcys/yesstevemodel/oo0oOO0000o0Ooooo0OoOo0O;)Ljava/lang/Object;'), ('com/elfmcys/yesstevemodel/o0000OOo0000oo000OOOo0o0', 'O00o0ooOoo00o00o0OOOO0o0', '(Lcom/elfmcys/yesstevemodel/oo0oOO0000o0Ooooo0OoOo0O;)Ljava/lang/Object;'), ('com/elfmcys/yesstevemodel/o0000OOo0000oo000OOOo0o0', 'OO0OO0000O0ooO0oO000Oo0O', '(Lcom/elfmcys/yesstevemodel/oo0oOO0000o0Ooooo0OoOo0O;)Ljava/lang/Object;'), ('com/elfmcys/yesstevemodel/o0000OOo0000oo000OOOo0o0', 'ooo0o0OoOooOOOo0OOOo00oO', '(Lcom/elfmcys/yesstevemodel/oo0oOO0000o0Ooooo0OoOo0O;)Ljava/lang/Object;'), ('com/elfmcys/yesstevemodel/o0000OOo0000oo000OOOo0o0', 'oo00O000000OoOo0O0O00oOO', '(Lcom/elfmcys/yesstevemodel/oo0oOO0000o0Ooooo0OoOo0O;)Ljava/lang/Object;'), ('com/elfmcys/yesstevemodel/o0000OOo0000oo000OOOo0o0', 'o0oOOoO0oooo0O0OoOoOoOo0', '(Lcom/elfmcys/yesstevemodel/oo0oOO0000o0Ooooo0OoOo0O;)Ljava/lang/Object;'), ('com/elfmcys/yesstevemodel/oOO0OO0OOO0ooOo000o0O0OO', 'Oo0Oo0o00O00Oo0OOoOOoooo', '(J)F'), ('com/elfmcys/yesstevemodel/O0oo0oOo0OOOO00Oo0oo0o00', '<init>', '(Z)V'), ('com/elfmcys/yesstevemodel/O0oo0oOo0OOOO00Oo0oo0o00', 'Oo0Oo0o00O00Oo0OOoOOoooo', '(Z)V'), ('com/elfmcys/yesstevemodel/O0oo0oOo0OOOO00Oo0oo0o00', 'o0OOooo0o0OO00OoOOOo0o0O', '(Z)V'), ('com/elfmcys/yesstevemodel/O0oo0oOo0OOOO00Oo0oo0o00', 'Oo0Oo0o00O00Oo0OOoOOoooo', '()Z'), ('com/elfmcys/yesstevemodel/O0oo0oOo0OOOO00Oo0oo0o00', 'o0OOooo0o0OO00OoOOOo0o0O', '()Z'), ('com/elfmcys/yesstevemodel/O0oo0oOo0OOOO00Oo0oo0o00', 'O00OOOooOoooOoo0o0o0oO0O', '()Lcom/elfmcys/yesstevemodel/OOOO0O0OO0oOOo00Ooo0oooO;'), ('com/elfmcys/yesstevemodel/o000o0o0Ooooo0ooo0oO0O0o', 'Oo0Oo0o00O00Oo0OOoOOoooo', '(F)V'), ('com/elfmcys/yesstevemodel/o000o0o0Ooooo0ooo0oO0O0o', 'Oo0Oo0o00O00Oo0OOoOOoooo', '()F'), ('com/elfmcys/yesstevemodel/O00Oo0oo0Ooo0oOOOo0OO0oO', '<init>', '(Lcom/elfmcys/yesstevemodel/o0000OoOooO0oo0o0oooo0Oo;Ljava/lang/String;F)V'), ('com/elfmcys/yesstevemodel/O00Oo0oo0Ooo0oOOOo0OO0oO', 'Oo0Oo0o00O00Oo0OOoOOoooo', '(Lcom/elfmcys/yesstevemodel/O0Oooo00oOo00O00OoOOOooO;)Z'), ('com/elfmcys/yesstevemodel/oo000oooo0OOoo00O0o0OOOO', '<init>', '(Lcom/elfmcys/yesstevemodel/o0000OoOooO0oo0o0oooo0Oo;Ljava/lang/String;FLcom/elfmcys/yesstevemodel/oOOO0Oo0O00oo0O0oO0OooO0;Z)V'), ('com/elfmcys/yesstevemodel/oo000oooo0OOoo00O0o0OOOO', 'o0OOooo0o0OO00OoOOOo0o0O', '(Lcom/elfmcys/yesstevemodel/O0Oooo00oOo00O00OoOOOooO;)Lcom/elfmcys/yesstevemodel/O0oOo0OoO0O0o0000o0O00o0;'), ('com/elfmcys/yesstevemodel/OOOO0o0oo0o000oOOooOoOo0', 'Oo0Oo0o00O00Oo0OOoOOoooo', '(FLcom/elfmcys/yesstevemodel/O0Oooo00oOo00O00OoOOOooO;Z)V'), ('com/elfmcys/yesstevemodel/OOOO0o0oo0o000oOOooOoOo0', 'Oo0Oo0o00O00Oo0OOoOOoooo', '(Lcom/elfmcys/yesstevemodel/O0Oooo00oOo00O00OoOOOooO;Z)V')])
SOURCES=[('src/main/java/com/elfmcys/yesstevemodel/geckolib3/core/molang/builtin/QueryBinding.java', 'f5fdc573ed9187fcf72465abe5ac19a0f16cd39c7e2d0edc66d1c2de1473bfc8', 'f184edabd1b5115ce5a24cb6d155ba5a669f5ba6'), ('src/main/java/com/elfmcys/yesstevemodel/geckolib3/util/MolangUtils.java', '3316e1205fb016ff3a9985b279a546d0c4a8bd6653d24448107659e2dc39fcaf', 'f184edabd1b5115ce5a24cb6d155ba5a669f5ba6'), ('src/main/java/com/elfmcys/yesstevemodel/geckolib3/core/molang/context/ControllerContext.java', 'ff70626a71d3ed2314cd59ab740feb5379876173a375ace9eaaa5027eaa742c5', 'f184edabd1b5115ce5a24cb6d155ba5a669f5ba6'), ('src/main/java/com/elfmcys/yesstevemodel/geckolib3/core/molang/context/AnimationContext.java', '27bfa16fb3b44e8febd3b74158c2f4ad28c8a544c2b2225c8beaab76c23a9ef6', 'f184edabd1b5115ce5a24cb6d155ba5a669f5ba6'), ('src/main/java/com/elfmcys/yesstevemodel/geckolib3/core/controller/BedrockAnimationController.java', '9e19c878f2df8fe2f9f8deae14506ad04a5d19f425984f2e912bf3b1c5e5214a', 'f184edabd1b5115ce5a24cb6d155ba5a669f5ba6'), ('src/main/java/com/elfmcys/yesstevemodel/geckolib3/core/controller/CodedAnimationController.java', '9b24616ff4f0ecdcb5aaeb7b810ce6eca3cdac46e2b103d93b2253fe223c58ba', 'f184edabd1b5115ce5a24cb6d155ba5a669f5ba6'), ('src/main/java/com/elfmcys/yesstevemodel/geckolib3/core/controller/AnimationPlayer.java', 'd1716903063b44feda14c4d60c96c319744c60dcd19d75583bd3a7b6db50edea', 'f184edabd1b5115ce5a24cb6d155ba5a669f5ba6')]

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
    neg('missing-query-support-o0000OOo0000oo000OOOo0o0',lambda x:member(x,0,'(Lcom/elfmcys/yesstevemodel/oo0oOO0000o0Ooooo0OoOo0O;)Ljava/util/Optional;','Oo0Oo0o00O00Oo0OOoOOoooo')['instructions'].pop())
    neg('missing-query-support-oOO0OO0OOO0ooOo000o0O0OO',lambda x:member(x,1,'(J)F','Oo0Oo0o00O00Oo0OOoOOoooo')['instructions'].pop())
    neg('missing-query-support-O0oo0oOo0OOOO00Oo0oo0o00',lambda x:member(x,2,'(Z)V','Oo0Oo0o00O00Oo0OOoOOoooo')['instructions'].pop())
    neg('missing-query-support-o000o0o0Ooooo0ooo0oO0O0o',lambda x:member(x,3,'(F)V','Oo0Oo0o00O00Oo0OOoOOoooo')['instructions'].pop())
    neg('missing-query-support-O00Oo0oo0Ooo0oOOOo0OO0oO',lambda x:member(x,4,'(Lcom/elfmcys/yesstevemodel/O0Oooo00oOo00O00OoOOOooO;)Z','Oo0Oo0o00O00Oo0OOoOOoooo')['instructions'].pop())
    neg('missing-query-support-oo000oooo0OOoo00O0o0OOOO',lambda x:member(x,5,'(Lcom/elfmcys/yesstevemodel/O0Oooo00oOo00O00OoOOOooO;)Lcom/elfmcys/yesstevemodel/O0oOo0OoO0O0o0000o0O00o0;','o0OOooo0o0OO00OoOOOo0o0O')['instructions'].pop())
    neg('missing-query-support-OOOO0o0oo0o000oOOooOoOo0',lambda x:member(x,6,'(FLcom/elfmcys/yesstevemodel/O0Oooo00oOo00O00OoOOOooO;Z)V','Oo0Oo0o00O00Oo0OOoOOoooo')['instructions'].pop())
    neg('day-time-offset-changed',lambda x:op(x,1,'(J)F',1)['reference'].update(value=0))
    result={'artifact_sha256':SHA,'checks':checks,'negative_controls':negatives,'failures':[c for c in checks if not c['pass']],'negative_failures':[n for n in negatives if not n['rejected']],'independent_semantic_review':'NOT_RUN','runtime_executed':False,'central_mapping_promoted':False}
    Path(a.out).write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({'checks':len(checks),'negative_controls':len(negatives),'failures':len(result['failures'])+len(result['negative_failures'])}))
    if result['failures'] or result['negative_failures']:raise SystemExit(1)
if __name__=='__main__':main()
