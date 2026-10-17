#!/usr/bin/env python3
"""Fixed-artifact easing/raw-keyframe Java evidence audit. Never runs target classes."""
import argparse,copy,hashlib,json,subprocess,zipfile
from pathlib import Path
from audit_seed_recovery_ysm_265 import parse_bounded,BOUNDDETAILS
from scan_ysm_265 import parse_class
SHA='25b5e902b96f4c298690208f8b433cbc31737c23f87590354dbd86f00207bc8f'
SIZE=63269843
OWNERS=['com/elfmcys/yesstevemodel/o00o00ooO000OoOoooO0000O', 'com/elfmcys/yesstevemodel/ooOooo0oOooOO0O0O00000oO', 'com/elfmcys/yesstevemodel/oOoOoOOooOOO0OO0oooO00oO', 'com/elfmcys/yesstevemodel/o0Oooo0OO0o00oOoOoo0oOOo', 'com/elfmcys/yesstevemodel/oO0O00O0oOOO0OoO0oOo0OoO']
SOURCES=[('src/main/java/com/elfmcys/yesstevemodel/geckolib3/core/keyframe/bone/EasingType.java', '57c047216e0f9d3afb63c3e5d5ac60142a230981a918a8c5f19ecb2506de0192', 'f184edabd1b5115ce5a24cb6d155ba5a669f5ba6'), ('src/main/java/com/elfmcys/yesstevemodel/geckolib3/core/keyframe/bone/RawBoneKeyFrame.java', 'bfe43d97ee48e6d55975b9576b289e1be7d837e35f3441f13c311cf82f496bb1', 'f184edabd1b5115ce5a24cb6d155ba5a669f5ba6'), ('src/main/java/com/elfmcys/yesstevemodel/geckolib3/core/molang/value/FloatValue.java', '6fb12624643d8b1d150699e08ea4bb7ea4c70488d17d3c03987fac6bc0a2f9aa', 'f184edabd1b5115ce5a24cb6d155ba5a669f5ba6'), ('src/main/java/com/elfmcys/yesstevemodel/geckolib3/core/molang/value/RotationValue.java', 'b4c040b76a974bf67b5b9ae21faeb6493165b070c56331f18a7c2f0cdf3d98d7', 'f184edabd1b5115ce5a24cb6d155ba5a669f5ba6'), ('src/main/java/com/elfmcys/yesstevemodel/geckolib3/core/keyframe/bone/BoneKeyFrameProcessor.java', '72f045e513d85d072e59a35b4ebd2bf7c3b56d0460def846542c0591ad65c65b', 'f184edabd1b5115ce5a24cb6d155ba5a669f5ba6')]

KEYS=('access','instructions','supplemental_full_operand_records','exception_handlers','code_sha256')
DECL=('access','super','interfaces','fields','methods')
def ident(m):return tuple(m.get(k) for k in ('owner','name','descriptor'))
def audit(e,actual,decl,details):
    checks=[]
    def ck(name,ok):checks.append({'check':name,'pass':bool(ok)})
    ck('fixed-artifact',e.get('artifact',{}).get('sha256')==SHA and e.get('artifact',{}).get('size')==SIZE)
    ck('detailed-operands',e.get('detailed_operands') is True)
    rows=e.get('members',[]);ids=[ident(m) for m in rows]
    ck('complete-27-methods',len(ids)==len(set(ids))==27 and set(ids)==set(actual))
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
    neg('raw-init-guard',lambda x:op(x,1,'(Z)V',4).update(opcode='0xc7'))
    neg('raw-contiguous-alias',lambda x:op(x,1,'(Z)V',65).update(opcode='0x9a'))
    neg('raw-x-flip',lambda x:op(x,1,'(Z)V',23).update(opcode='0x3'))
    neg('raw-z-flip',lambda x:op(x,1,'(Z)V',51).update(opcode='0x4'))
    neg('raw-tick-narrowing',lambda x:op(x,1,'()F',4).update(opcode='0x8d'))
    neg('float-nan-guard',lambda x:op(x,2,'(F)V',8).update(opcode='0x99'))
    neg('rotation-radians-promotion',lambda x:op(x,3,'(FZ)F',1).update(opcode='0x90'))
    neg('rotation-sign',lambda x:op(x,3,'(FZ)F',12).update(opcode='0x0'))
    desc='(Ljava/util/List;Z)Ljava/util/List;'
    neg('processor-easing-identity',lambda x:op(x,4,desc,76).update(opcode='0xa6'))
    neg('processor-first-index',lambda x:op(x,4,desc,80).update(opcode='0x99'))
    neg('processor-build-before-init',lambda x:op(x,4,desc,13).update(branch_target=110))
    result={'artifact_sha256':SHA,'checks':checks,'negative_controls':negatives,'failures':[c for c in checks if not c['pass']],'negative_failures':[n for n in negatives if not n['rejected']],'independent_semantic_review':'NOT_RUN','runtime_executed':False,'central_mapping_promoted':False}
    Path(a.out).write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({'checks':len(checks),'negative_controls':len(negatives),'failures':len(result['failures'])+len(result['negative_failures'])}))
    if result['failures'] or result['negative_failures']:raise SystemExit(1)
if __name__=='__main__':main()
