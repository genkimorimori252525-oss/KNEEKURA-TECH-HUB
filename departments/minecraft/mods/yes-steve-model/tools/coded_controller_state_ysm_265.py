#!/usr/bin/env python3
"""Fixed-artifact coded-controller Java evidence audit. Never runs target classes."""
import argparse,copy,hashlib,json,subprocess,zipfile
from pathlib import Path
from audit_seed_recovery_ysm_265 import parse_bounded,BOUNDDETAILS
from scan_ysm_265 import parse_class
SHA='25b5e902b96f4c298690208f8b433cbc31737c23f87590354dbd86f00207bc8f'
SIZE=63269843
OWNERS=['com/elfmcys/yesstevemodel/oo000oooo0OOoo00O0o0OOOO', 'com/elfmcys/yesstevemodel/O0oOo0OoO0O0o0000o0O00o0', 'com/elfmcys/yesstevemodel/Oo0oOoO0OooOO0ooooOooo0O']
SOURCES=[('src/main/java/com/elfmcys/yesstevemodel/geckolib3/core/controller/CodedAnimationController.java', '9b24616ff4f0ecdcb5aaeb7b810ce6eca3cdac46e2b103d93b2253fe223c58ba', 'f184edabd1b5115ce5a24cb6d155ba5a669f5ba6'), ('src/main/java/com/elfmcys/yesstevemodel/geckolib3/core/PlayState.java', 'bc037e2897acaed22c785e3451f2c5c84fa82e2949bfad1bd41797305e7fea18', 'f184edabd1b5115ce5a24cb6d155ba5a669f5ba6'), ('src/main/java/com/elfmcys/yesstevemodel/geckolib3/core/AnimationState.java', 'd3ba65e6312ff8bdb4c7b77b994fcd82bb5f2cb73309d15d281424e80ca7b69a', 'f184edabd1b5115ce5a24cb6d155ba5a669f5ba6'), ('src/main/java/com/elfmcys/yesstevemodel/client/animation/molang/CtrlBinding.java', 'ad2ad6a48555907c2fc5311d18e0ac9f9d8b441f56aec671e0bdfc67d5db4520', 'f184edabd1b5115ce5a24cb6d155ba5a669f5ba6')]

KEYS=('access','instructions','supplemental_full_operand_records','exception_handlers','code_sha256')
DECL=('access','super','interfaces','fields','methods')
def ident(m):return tuple(m.get(k) for k in ('owner','name','descriptor'))
def audit(e,actual,decl,details):
    checks=[]
    def ck(name,ok):checks.append({'check':name,'pass':bool(ok)})
    ck('fixed-artifact',e.get('artifact',{}).get('sha256')==SHA and e.get('artifact',{}).get('size')==SIZE)
    ck('detailed-operands',e.get('detailed_operands') is True)
    rows=e.get('members',[]);ids=[ident(m) for m in rows]
    ck('complete-30-methods',len(ids)==len(set(ids))==30 and set(ids)==set(actual))
    for m in rows:
        a=actual.get(ident(m),{})
        for k in KEYS:ck(str(ident(m))+':'+k,(k in m)==(k in a) and m.get(k)==a.get(k))
    ds=e.get('owner_declarations',[]);ck('three-declarations',len(ds)==3 and {r['owner'] for r in ds}==set(OWNERS))
    for r in ds:ck(r['owner']+':declaration',r['declaration']==decl.get(r['owner']))
    bs=e.get('bootstrap_and_constant_evidence',[]);ck('three-bootstrap-records',len(bs)==3 and {r['owner'] for r in bs}==set(OWNERS))
    for r in bs:
        for k in ('constant_values','bootstrap_methods'):ck(r['owner']+':'+k,k in r and r[k]==details.get(r['owner'],{}).get(k))
    ss=e.get('source_tracks',[]);ck('four-fixed-sources',sorted((r.get('path'),r.get('sha256'),r.get('revision')) for r in ss)==sorted(SOURCES))
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
    proc='(Lcom/elfmcys/yesstevemodel/OO00O0o0OooOOOo00OO00o00;Lcom/elfmcys/yesstevemodel/O0Oooo00oOo00O00OoOOOooO;Z)V'
    pred='(Lcom/elfmcys/yesstevemodel/O0Oooo00oOo00O00OoOOOooO;)Lcom/elfmcys/yesstevemodel/O0oOo0OoO0O0o0000o0O00o0;'
    neg('fallback-polarity',lambda x:op(x,0,proc,14).update(opcode='0xc6'))
    neg('event-clear-before-predicate',lambda x:op(x,0,proc,32)['reference'].update(name='invalid'))
    neg('pause-emission-enabled',lambda x:op(x,0,proc,161).update(opcode='0x4'))
    neg('pause-flag-cleared',lambda x:op(x,0,proc,173).update(opcode='0x3'))
    neg('stop-stale-state-gate',lambda x:op(x,0,proc,120).update(opcode='0xa5'))
    neg('invented-process-cleanup',lambda x:member(x,0,proc)['exception_handlers'].append({'start':0,'end':195,'handler':195,'catch':None}))
    neg('predicate-emission-disabled',lambda x:op(x,0,pred,81).update(opcode='0x3'))
    neg('predicate-reset-inverted',lambda x:op(x,0,pred,105).update(opcode='0x4'))
    def switch(x):
        row=member(x,0,pred)
        next(o for o in row['supplemental_full_operand_records'] if o['offset']==136)['encoded_operands_hex']='00'
    neg('predicate-switch-table',switch)
    neg('pause-visitor-guard',lambda x:op(x,0,'(Ljava/util/function/Consumer;)V',4).update(opcode='0x99'))
    neg('play-state-label',lambda x:op(x,1,'()V',4,'<clinit>')['reference'].update(string='STOP'))
    result={'artifact_sha256':SHA,'checks':checks,'negative_controls':negatives,'failures':[c for c in checks if not c['pass']],'negative_failures':[n for n in negatives if not n['rejected']],'independent_semantic_review':'NOT_RUN','runtime_executed':False,'central_mapping_promoted':False}
    Path(a.out).write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({'checks':len(checks),'negative_controls':len(negatives),'failures':len(result['failures'])+len(result['negative_failures'])}))
    if result['failures'] or result['negative_failures']:raise SystemExit(1)
if __name__=='__main__':main()
