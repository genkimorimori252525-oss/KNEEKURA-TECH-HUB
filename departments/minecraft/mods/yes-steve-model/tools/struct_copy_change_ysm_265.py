#!/usr/bin/env python3
"""Fixed-artifact animatable frame evidence audit. Never runs target classes."""
import argparse,copy,hashlib,json,subprocess,zipfile
from pathlib import Path
from audit_seed_recovery_ysm_265 import parse_bounded,BOUNDDETAILS
from scan_ysm_265 import parse_class
SHA='25b5e902b96f4c298690208f8b433cbc31737c23f87590354dbd86f00207bc8f'
SIZE=63269843
OWNERS=['com/elfmcys/yesstevemodel/oOOoOOOoooOO000o00o0oooo', 'com/elfmcys/yesstevemodel/O0OOO0OoOO0OO0o00oooo000', 'com/elfmcys/yesstevemodel/o0O00OoOOooo0OoooOOoo00O', 'com/elfmcys/yesstevemodel/OOoO0OO0oOo0OOOoOOo0O0Oo', 'com/elfmcys/yesstevemodel/o0O00o0OOo00oOoooo0oOOOO']
SOURCES=[('src/main/java/com/elfmcys/yesstevemodel/molang/runtime/Struct.java', 'c93faa04f4631469048c6fbc72caed03445a6d4fe7e986a0043052a929968507', 'f184edabd1b5115ce5a24cb6d155ba5a669f5ba6'), ('src/main/java/com/elfmcys/yesstevemodel/molang/runtime/HashMapStruct.java', 'a41967309d6ab934ee0a169e5c95fe7d555843eddc364388101dd1da8564cc01', 'f184edabd1b5115ce5a24cb6d155ba5a669f5ba6'), ('src/main/java/com/elfmcys/yesstevemodel/client/animation/molang/struct/Vec3fStruct.java', 'c749164961306c5b01d4e2598e46e5063b10e28fa38019cb3dac991c6ced7736', 'f184edabd1b5115ce5a24cb6d155ba5a669f5ba6'), ('src/main/java/com/elfmcys/yesstevemodel/client/animation/molang/roaming/LocalRoamingStruct.java', '3bb374ca8c663c9b0fc7af1150951c311d00b2d4ce43e7c2b33003f79efbb788', 'f184edabd1b5115ce5a24cb6d155ba5a669f5ba6'), ('src/main/java/com/elfmcys/yesstevemodel/client/animation/molang/roaming/RemoteRoamingStruct.java', '43fa6d8e2c3279802d8bb926ccdc00ef0968d500bb22a2fdc547fb7f679ff279', 'f184edabd1b5115ce5a24cb6d155ba5a669f5ba6')]

KEYS=('access','instructions','supplemental_full_operand_records','exception_handlers','code_sha256')
DECL=('access','super','interfaces','fields','methods')
def ident(m):return tuple(m.get(k) for k in ('owner','name','descriptor'))
def audit(e,actual,decl,details):
    checks=[]
    def ck(name,ok):checks.append({'check':name,'pass':bool(ok)})
    ck('fixed-artifact',e.get('artifact',{}).get('sha256')==SHA and e.get('artifact',{}).get('size')==SIZE)
    ck('detailed-operands',e.get('detailed_operands') is True)
    rows=e.get('members',[]);ids=[ident(m) for m in rows]
    ck('complete-33-methods',len(ids)==len(set(ids))==33 and set(ids)==set(actual))
    for m in rows:
        a=actual.get(ident(m),{})
        for k in KEYS:ck(str(ident(m))+':'+k,(k in m)==(k in a) and m.get(k)==a.get(k))
    ds=e.get('owner_declarations',[]);ck('five-declarations',len(ds)==5 and {r['owner'] for r in ds}==set(OWNERS))
    for r in ds:ck(r['owner']+':declaration',r['declaration']==decl.get(r['owner']))
    bs=e.get('bootstrap_and_constant_evidence',[]);ck('five-bootstrap-records',len(bs)==5 and {r['owner'] for r in bs}==set(OWNERS))
    for r in bs:
        for k in ('constant_values','bootstrap_methods'):ck(r['owner']+':'+k,k in r and r[k]==details.get(r['owner'],{}).get(k))
    ss=e.get('source_tracks',[]);ck('five-fixed-sources',sorted((r.get('path'),r.get('sha256'),r.get('revision')) for r in ss)==sorted(SOURCES))
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
    neg('lost-local-change-body',lambda x:member(x,3,'(ILjava/lang/Object;)V')['instructions'].pop())
    neg('invented-remote-update-finally',lambda x:member(x,4,'(Lit/unimi/dsi/fastutil/ints/Int2FloatMap;)V')['exception_handlers'].append({'start':0,'end':10,'handler':10,'catch':None}))
    neg('mutable-vector-setter',lambda x:member(x,2,'(ILjava/lang/Object;)V')['instructions'].append({'offset':1,'opcode':'0x0'}))
    neg('right-value-copy-branch',lambda x:op(x,1,'()Lcom/elfmcys/yesstevemodel/oOOoOOOoooOO000o00o0oooo;',4).update(opcode='0x9a'))
    neg('local-equality-dirty-gate',lambda x:op(x,3,'(ILjava/lang/Object;)V',20).update(opcode='0x99'))
    neg('local-64-limit',lambda x:op(x,3,'(ILjava/lang/Object;)V',40).update(immediate=32))
    neg('local-limit-equality',lambda x:op(x,3,'(ILjava/lang/Object;)V',42).update(opcode='0xa1'))
    result={'artifact_sha256':SHA,'checks':checks,'negative_controls':negatives,'failures':[c for c in checks if not c['pass']],'negative_failures':[n for n in negatives if not n['rejected']],'independent_semantic_review':'NOT_RUN','runtime_executed':False,'central_mapping_promoted':False}
    Path(a.out).write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({'checks':len(checks),'negative_controls':len(negatives),'failures':len(result['failures'])+len(result['negative_failures'])}))
    if result['failures'] or result['negative_failures']:raise SystemExit(1)
if __name__=='__main__':main()
