#!/usr/bin/env python3
"""Fixed-artifact animatable frame evidence audit. Never runs target classes."""
import argparse,copy,hashlib,json,subprocess,zipfile
from pathlib import Path
from audit_seed_recovery_ysm_265 import parse_bounded,BOUNDDETAILS
from scan_ysm_265 import parse_class
SHA='25b5e902b96f4c298690208f8b433cbc31737c23f87590354dbd86f00207bc8f'
SIZE=63269843
OWNERS=['com/elfmcys/yesstevemodel/oOoOoO0O000OOoo000O0OO00', 'com/elfmcys/yesstevemodel/oOO0OOooo00oo0oOOOOoO00O', 'com/elfmcys/yesstevemodel/OOooOO0OoOOOOOOoO000oOOO', 'com/elfmcys/yesstevemodel/OOOO00o000o00OoOOo0o0oOO', 'com/elfmcys/yesstevemodel/OO0O00ooOo0OO0oooOoo0Oo0', 'com/elfmcys/yesstevemodel/O0o0OOO00000oO00O00oOOo0']
SOURCES=[('src/main/java/com/elfmcys/yesstevemodel/geckolib3/core/molang/binding/ContextBinding.java', '6e2940901a533435fdafcbdc2e2f6c8deb6b46fe034ac3f49f9c95d98fb1c134', 'f184edabd1b5115ce5a24cb6d155ba5a669f5ba6'), ('src/main/java/com/elfmcys/yesstevemodel/geckolib3/core/molang/variable/ContextVariable.java', '3974af193316d8cf3648a68860fa2012cdb05866aeb2e537474737c2df7f1e71', 'f184edabd1b5115ce5a24cb6d155ba5a669f5ba6'), ('src/main/java/com/elfmcys/yesstevemodel/geckolib3/core/molang/variable/LambdaVariable.java', '3a92785de4a5f3958b8ba19cdfecd97940db003fbe00e83a22ebcaaa34a67e41', 'f184edabd1b5115ce5a24cb6d155ba5a669f5ba6'), ('src/main/java/com/elfmcys/yesstevemodel/geckolib3/core/molang/variable/entity/EntityVariable.java', '51ffcd03cdb4926065ca91fa421593d567e5f41a3bf2b8e981e410b14848527e', 'f184edabd1b5115ce5a24cb6d155ba5a669f5ba6'), ('src/main/java/com/elfmcys/yesstevemodel/molang/runtime/binding/ValueConversions.java', '3eb91e8a0c75cb893fed4a2607e3e9e680e2c94e88ad0b655822b1200ac365ff', 'f184edabd1b5115ce5a24cb6d155ba5a669f5ba6'), ('src/main/java/com/elfmcys/yesstevemodel/geckolib3/core/molang/value/IValue.java', '43579daf47f89586b7ec63b9b75d5ddd3299cd5fcda8d98d1604a4be21364f79', 'f184edabd1b5115ce5a24cb6d155ba5a669f5ba6')]

KEYS=('access','instructions','supplemental_full_operand_records','exception_handlers','code_sha256')
DECL=('access','super','interfaces','fields','methods')
def ident(m):return tuple(m.get(k) for k in ('owner','name','descriptor'))
def audit(e,actual,decl,details):
    checks=[]
    def ck(name,ok):checks.append({'check':name,'pass':bool(ok)})
    ck('fixed-artifact',e.get('artifact',{}).get('sha256')==SHA and e.get('artifact',{}).get('size')==SIZE)
    ck('detailed-operands',e.get('detailed_operands') is True)
    rows=e.get('members',[]);ids=[ident(m) for m in rows]
    ck('complete-43-methods',len(ids)==len(set(ids))==43 and set(ids)==set(actual))
    for m in rows:
        a=actual.get(ident(m),{})
        for k in KEYS:ck(str(ident(m))+':'+k,(k in m)==(k in a) and m.get(k)==a.get(k))
    ds=e.get('owner_declarations',[]);ck('six-declarations',len(ds)==6 and {r['owner'] for r in ds}==set(OWNERS))
    for r in ds:ck(r['owner']+':declaration',r['declaration']==decl.get(r['owner']))
    bs=e.get('bootstrap_and_constant_evidence',[]);ck('six-bootstrap-records',len(bs)==6 and {r['owner'] for r in bs}==set(OWNERS))
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
    neg('missing-lambda-return-body',lambda x:member(x,2,'(Lcom/elfmcys/yesstevemodel/oo0oOO0000o0Ooooo0OoOo0O;)Ljava/lang/Object;')['instructions'].pop())
    neg('invented-variable-catch',lambda x:member(x,2,'(Lcom/elfmcys/yesstevemodel/oo0oOO0000o0Ooooo0OoOo0O;)Ljava/lang/Object;')['exception_handlers'].append({'start':0,'end':10,'handler':10,'catch':'java/lang/Throwable'}))
    neg('lost-value-catch',lambda x:member(x,5,'(Lcom/elfmcys/yesstevemodel/O0Oooo00oOo00O00OoOOOooO;)Ljava/lang/Object;','O00OOOooOoooOoo0o0o0oO0O')['exception_handlers'].clear())
    neg('nan-float-branch-inverted',lambda x:op(x,4,'(Ljava/lang/Object;)F',25).update(opcode='0x99'))
    neg('nan-boolean-branch-inverted',lambda x:op(x,4,'(Ljava/lang/Object;)Z',40).update(opcode='0x99'))
    neg('non-numeric-float-zero',lambda x:op(x,4,'(Ljava/lang/Object;)F',55).update(opcode='0xb'))
    neg('invalid-context-fallback',lambda x:op(x,1,'(Lcom/elfmcys/yesstevemodel/oO0OoO0O0OoO0oo0oo0OOooo;)Ljava/lang/Object;',34).update(opcode='0x4'))
    result={'artifact_sha256':SHA,'checks':checks,'negative_controls':negatives,'failures':[c for c in checks if not c['pass']],'negative_failures':[n for n in negatives if not n['rejected']],'independent_semantic_review':'NOT_RUN','runtime_executed':False,'central_mapping_promoted':False}
    Path(a.out).write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({'checks':len(checks),'negative_controls':len(negatives),'failures':len(result['failures'])+len(result['negative_failures'])}))
    if result['failures'] or result['negative_failures']:raise SystemExit(1)
if __name__=='__main__':main()
