#!/usr/bin/env python3
"""Fixed-artifact animation-player clock evidence audit. Never runs target classes."""
import argparse,copy,hashlib,json,subprocess,zipfile
from pathlib import Path
from audit_seed_recovery_ysm_265 import parse_bounded,BOUNDDETAILS
from scan_ysm_265 import parse_class
SHA='25b5e902b96f4c298690208f8b433cbc31737c23f87590354dbd86f00207bc8f'
SIZE=63269843
OWNERS=['com/elfmcys/yesstevemodel/OOOO0o0oo0o000oOOooOoOo0', 'com/elfmcys/yesstevemodel/OoooOo0OOOoOOoOOooOOoO00', 'com/elfmcys/yesstevemodel/o0OoOoOO0oooO0O000oO0o0o', 'com/elfmcys/yesstevemodel/OooOO0OOOoO0oOO0OOOO0Ooo', 'com/elfmcys/yesstevemodel/Oo0oOoO0OooOO0ooooOooo0O']
SOURCES=[('src/main/java/com/elfmcys/yesstevemodel/geckolib3/core/controller/AnimationPlayer.java', 'd1716903063b44feda14c4d60c96c319744c60dcd19d75583bd3a7b6db50edea', 'f184edabd1b5115ce5a24cb6d155ba5a669f5ba6'), ('src/main/java/com/elfmcys/yesstevemodel/geckolib3/core/controller/transition/LinearBlendTransition.java', 'f1df04570f58a0d33c888d7181cd15bf6d4b605377d83d32f577dce6ca4d170f', 'f184edabd1b5115ce5a24cb6d155ba5a669f5ba6'), ('src/main/java/com/elfmcys/yesstevemodel/geckolib3/core/controller/transition/IBlendTransition.java', 'dfa25ba1ef652f9c29b777108dfeb6d50e850fd4adbb8121a44a726c86b989c4', 'f184edabd1b5115ce5a24cb6d155ba5a669f5ba6'), ('src/main/java/com/elfmcys/yesstevemodel/geckolib3/core/builder/LoopType.java', '1d9729f840da22b345b813b90ef7770a70e8287f1193ef5666e9690734021d25', 'f184edabd1b5115ce5a24cb6d155ba5a669f5ba6'), ('src/main/java/com/elfmcys/yesstevemodel/geckolib3/core/AnimationState.java', 'd3ba65e6312ff8bdb4c7b77b994fcd82bb5f2cb73309d15d281424e80ca7b69a', 'f184edabd1b5115ce5a24cb6d155ba5a669f5ba6'), ('src/main/java/com/elfmcys/yesstevemodel/geckolib3/core/manager/AnimationData.java', '8337dd0ea030310ae7e3d73634c69da7cbc4408d1e925e1573ee87e6fd639bc4', 'f184edabd1b5115ce5a24cb6d155ba5a669f5ba6')]

KEYS=('access','instructions','supplemental_full_operand_records','exception_handlers','code_sha256')
DECL=('access','super','interfaces','fields','methods')
def ident(m):return tuple(m.get(k) for k in ('owner','name','descriptor'))
def audit(e,actual,decl,details):
    checks=[]
    def ck(name,ok):checks.append({'check':name,'pass':bool(ok)})
    ck('fixed-artifact',e.get('artifact',{}).get('sha256')==SHA and e.get('artifact',{}).get('size')==SIZE)
    ck('detailed-operands',e.get('detailed_operands') is True)
    rows=e.get('members',[]);ids=[ident(m) for m in rows]
    ck('complete-50-methods',len(ids)==len(set(ids))==50 and set(ids)==set(actual))
    for m in rows:
        a=actual.get(ident(m),{})
        for k in KEYS:ck(str(ident(m))+':'+k,(k in m)==(k in a) and m.get(k)==a.get(k))
    ds=e.get('owner_declarations',[]);ck('five-declarations',len(ds)==5 and {r['owner'] for r in ds}==set(OWNERS))
    for r in ds:ck(r['owner']+':declaration',r['declaration']==decl.get(r['owner']))
    bs=e.get('bootstrap_and_constant_evidence',[]);ck('five-bootstrap-records',len(bs)==5 and {r['owner'] for r in bs}==set(OWNERS))
    for r in bs:
        for k in ('constant_values','bootstrap_methods'):ck(r['owner']+':'+k,k in r and r[k]==details.get(r['owner'],{}).get(k))
    ss=e.get('source_tracks',[]);ck('six-fixed-sources',sorted((r.get('path'),r.get('sha256'),r.get('revision')) for r in ss)==sorted(SOURCES))
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
            actual.update({ident(m):m for m in parse_bounded(b,True)})
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
    proc='(FLcom/elfmcys/yesstevemodel/O0Oooo00oOo00O00OoOOOooO;Z)V'
    neg('ending-boundary-strictness',lambda x:op(x,0,proc,38).update(opcode='0x9e'))
    neg('playonce-boundary-strictness',lambda x:op(x,0,proc,75).update(opcode='0x9e'))
    neg('loop-boundary-strictness',lambda x:op(x,0,proc,263).update(opcode='0x9b'))
    neg('beginning-equality-gate',lambda x:op(x,0,proc,195).update(opcode='0x9d'))
    neg('loop-remainder',lambda x:op(x,0,proc,310).update(opcode='0x6e'))
    neg('timeline-max',lambda x:op(x,0,'(F)F',7)['reference'].update(name='min'))
    neg('timeline-subtraction',lambda x:op(x,0,'(F)F',5).update(opcode='0x62'))
    neg('duration-getter-divide',lambda x:op(x,0,'()F',11,'oooooooOOoOOoO00OooOo00O').update(opcode='0x6e'))
    neg('linear-duration-factor',lambda x:op(x,1,'(F)V',6,'<init>')['reference'].update(value=1.0))
    neg('linear-zero-result',lambda x:op(x,1,'(F)F',18).update(opcode='0xb'))
    neg('invented-player-finally',lambda x:member(x,0,proc)['exception_handlers'].append({'start':0,'end':426,'handler':426,'catch':None}))
    neg('ending-fixed-duration',lambda x:op(x,0,proc,35)['reference'].update(value=5.0))
    neg('loop-enum-label',lambda x:op(x,3,'()V',4,'<clinit>')['reference'].update(string='PLAY_ONCE'))
    result={'artifact_sha256':SHA,'checks':checks,'negative_controls':negatives,'failures':[c for c in checks if not c['pass']],'negative_failures':[n for n in negatives if not n['rejected']],'independent_semantic_review':'NOT_RUN','runtime_executed':False,'central_mapping_promoted':False}
    Path(a.out).write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({'checks':len(checks),'negative_controls':len(negatives),'failures':len(result['failures'])+len(result['negative_failures'])}))
    if result['failures'] or result['negative_failures']:raise SystemExit(1)
if __name__=='__main__':main()
