#!/usr/bin/env python3
"""Fixed-artifact animatable frame evidence audit. Never runs target classes."""
import argparse,copy,hashlib,json,subprocess,zipfile
from pathlib import Path
from audit_seed_recovery_ysm_265 import parse_bounded,BOUNDDETAILS
from scan_ysm_265 import parse_class
SHA='25b5e902b96f4c298690208f8b433cbc31737c23f87590354dbd86f00207bc8f'
SIZE=63269843
OWNERS=['com/elfmcys/yesstevemodel/oOo00OoOO00O000ooO0Oo00o', 'com/elfmcys/yesstevemodel/o0ooooOo0o000OOo0oO00OoO', 'com/elfmcys/yesstevemodel/oO0OoOo0OOoOo0OO000OO0oO', 'com/elfmcys/yesstevemodel/mixin/client/WorldRendererMixin']
SOURCES=[('src/main/java/com/elfmcys/yesstevemodel/client/entity/CustomEntity.java', 'f1d6924017b087a89ed03868be2d7e55be237edf0d8522adccb013a41f7e809c', 'f184edabd1b5115ce5a24cb6d155ba5a669f5ba6'), ('src/main/java/com/elfmcys/yesstevemodel/client/animation/AnimationParallelTicker.java', 'fbd26cfa0e8faf22de506b3d6c0d9831d18162ddb6de1de8972875e1746df93f', 'f184edabd1b5115ce5a24cb6d155ba5a669f5ba6'), ('src/main/java/com/elfmcys/yesstevemodel/util/ThreadTools.java', 'bd80e4eaaa8f797d9222d1cac774d70bccd8c072ae43afa450407eef612cb3cf', 'f184edabd1b5115ce5a24cb6d155ba5a669f5ba6'), ('src/main/java/com/elfmcys/yesstevemodel/mixin/client/WorldRendererMixin.java', '78d2ef4a703fde89e6aca2f228dc7554f5977c1df80b88a680ec66d70ebff7a7', 'f184edabd1b5115ce5a24cb6d155ba5a669f5ba6')]

KEYS=('access','instructions','supplemental_full_operand_records','exception_handlers','code_sha256')
DECL=('access','super','interfaces','fields','methods')
def ident(m):return tuple(m.get(k) for k in ('owner','name','descriptor'))
def audit(e,actual,decl,details):
    checks=[]
    def ck(name,ok):checks.append({'check':name,'pass':bool(ok)})
    ck('fixed-artifact',e.get('artifact',{}).get('sha256')==SHA and e.get('artifact',{}).get('size')==SIZE)
    ck('detailed-operands',e.get('detailed_operands') is True)
    rows=e.get('members',[]);ids=[ident(m) for m in rows]
    ck('complete-46-methods',len(ids)==len(set(ids))==46 and set(ids)==set(actual))
    for m in rows:
        a=actual.get(ident(m),{})
        for k in KEYS:ck(str(ident(m))+':'+k,(k in m)==(k in a) and m.get(k)==a.get(k))
    ds=e.get('owner_declarations',[]);ck('four-declarations',len(ds)==4 and {r['owner'] for r in ds}==set(OWNERS))
    for r in ds:ck(r['owner']+':declaration',r['declaration']==decl.get(r['owner']))
    bs=e.get('bootstrap_and_constant_evidence',[]);ck('four-bootstrap-records',len(bs)==4 and {r['owner'] for r in bs}==set(OWNERS))
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
    event='Lcom/elfmcys/yesstevemodel/OO00O0o0OooOOOo00OO00o00;'
    wait='()'+event
    worker='(F)'+event
    neg('pre-submit-fence',lambda x:op(x,0,'(F)V',3)['reference'].update(name='loadFence'))
    neg('future-get-replaced',lambda x:op(x,0,wait,13)['reference'].update(name='cancel'))
    neg('load-fence-removed',lambda x:op(x,0,wait,25)['reference'].update(name='storeFence'))
    neg('interrupt-catch-omitted',lambda x:member(x,0,wait)['exception_handlers'].pop(0))
    neg('worker-finally-omitted',lambda x:member(x,0,worker)['exception_handlers'].clear())
    neg('worker-render-scope-false',lambda x:op(x,0,worker,2).update(opcode='0x3'))
    neg('worker-super-call-virtual',lambda x:op(x,0,worker,3).update(opcode='0xb6'))
    neg('exclusive-scope-branch',lambda x:op(x,0,'(FZ)'+event,4).update(opcode='0x9a'))
    neg('render-thread-assertion-removed',lambda x:op(x,0,'(FZ)'+event,0)['reference'].update(name='wrong'))
    neg('wait-list-catch-omitted',lambda x:member(x,1,'()V','Oo0Oo0o00O00Oo0OOoOOoooo')['exception_handlers'].clear())
    neg('task-list-not-cleared',lambda x:op(x,1,'()V',45,'Oo0Oo0o00O00Oo0OOoOOoooo')['reference'].update(name='size'))
    neg('callable-overload-changed',lambda x:op(x,2,'(Ljava/util/concurrent/Callable;)Ljava/util/concurrent/Future;',4)['reference'].update(name='execute'))
    result={'artifact_sha256':SHA,'checks':checks,'negative_controls':negatives,'failures':[c for c in checks if not c['pass']],'negative_failures':[n for n in negatives if not n['rejected']],'independent_semantic_review':'NOT_RUN','runtime_executed':False,'central_mapping_promoted':False}
    Path(a.out).write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({'checks':len(checks),'negative_controls':len(negatives),'failures':len(result['failures'])+len(result['negative_failures'])}))
    if result['failures'] or result['negative_failures']:raise SystemExit(1)
if __name__=='__main__':main()
