#!/usr/bin/env python3
"""Fixed-artifact static MathUtil evidence checks, not execution of YSM/JOML."""
import argparse
import copy
import hashlib
import json
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path
from audit_seed_recovery_ysm_265 import parse_bounded, BOUNDDETAILS

SHA = '25b5e902b96f4c298690208f8b433cbc31737c23f87590354dbd86f00207bc8f'
SIZE = 63269843
OWNER = 'com/elfmcys/yesstevemodel/oooOO00ooooooOO0ooO00O0O'
SOURCE_PATH = 'src/main/java/com/elfmcys/yesstevemodel/geckolib3/core/util/MathUtil.java'
SOURCE_SHA = 'b4d8fc5d4016a9fe2a5573233df936a1520dce0f73b30b3f859ec1471280b7f8'
REVISION = 'f184edabd1b5115ce5a24cb6d155ba5a669f5ba6'
FIELDS = ('access', 'instructions', 'supplemental_full_operand_records', 'exception_handlers', 'code_sha256')
def key(m):
    return tuple(m.get(k) for k in ('owner', 'name', 'descriptor'))
def audit(evidence, actual, details):
    checks=[]
    def check(name, passed): checks.append({'check':name,'pass':bool(passed)})
    check('fixed-artifact',evidence.get('artifact',{}).get('sha256')==SHA and evidence.get('artifact',{}).get('size')==SIZE)
    check('detailed-operands',evidence.get('detailed_operands') is True)
    cs=evidence.get('classes',[])
    check('one-required-class',len(cs)==1 and cs[0].get('owner')==OWNER and all(k in cs[0].get('declaration',{}) for k in ('access','super','interfaces','fields','methods')))
    ss=evidence.get('source_tracks',[])
    check('fixed-source-record',len(ss)==1 and ss[0].get('path')==SOURCE_PATH and ss[0].get('sha256')==SOURCE_SHA and ss[0].get('revision')==REVISION)
    rows=evidence.get('members',[])+evidence.get('bounded_dependency_support',[])
    ids=[key(m) for m in rows]
    check('complete-18-method-set',len(ids)==len(set(ids))==18 and set(ids)==set(actual))
    for m in rows:
        observed=actual.get(key(m),{})
        for f in FIELDS:check(str(key(m))+':'+f,f in m and m[f]==observed.get(f))
    ds=evidence.get('bootstrap_and_constant_evidence',[])
    check('single-owner-detail',len(ds)==1 and ds[0].get('owner')==OWNER)
    for f in ('bootstrap_methods','constant_values'):
        check(f,len(ds)==1 and f in ds[0] and ds[0][f]==details[f])
    return checks

def main():
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('jar','evidence','source-root','out'):p.add_argument('--'+name,required=True)
    a=p.parse_args();raw=Path(a.jar).read_bytes()
    if len(raw)!=SIZE or hashlib.sha256(raw).hexdigest()!=SHA:raise SystemExit('Wrong fixed artifact')
    e=json.loads(Path(a.evidence).read_text())
    with zipfile.ZipFile(a.jar) as z:actual={key(m):m for m in parse_bounded(z.read(OWNER+'.class'),True)}
    details=copy.deepcopy(BOUNDDETAILS[OWNER]);checks=audit(e,actual,details)
    root=Path(a.source_root);src=root/SOURCE_PATH
    rev=subprocess.check_output(['git','-C',str(root),'rev-parse','HEAD'],text=True).strip()
    checks.append({'check':'source-checkout-revision','pass':rev==REVISION})
    checks.append({'check':'source-file-sha','pass':src.is_file() and hashlib.sha256(src.read_bytes()).hexdigest()==SOURCE_SHA})
    with tempfile.TemporaryDirectory() as t:
        out=Path(t)/'base.json'
        run=subprocess.run([sys.executable,str(Path(__file__).with_name('audit_seed_recovery_ysm_265.py')),'--jar',a.jar,'--evidence',a.evidence,'--out',str(out)],capture_output=True,text=True)
        if not out.exists():raise SystemExit(run.stderr or run.stdout)
        base=json.loads(out.read_text())
    negatives=[]
    def member(x,role):return next(m for m in x['members'] if m['semantic_member']==role)
    def op(x,role,offset):return next(o for o in member(x,role)['instructions'] if o['offset']==offset)
    def control(name,mutate):
        x=copy.deepcopy(e);mutate(x);fail=[c for c in audit(x,actual,details) if not c['pass']];negatives.append({'control':name,'rejected':bool(fail)})
    control('missing-class-record',lambda x:x['classes'].clear())
    control('missing-source-record',lambda x:x['source_tracks'].clear())
    control('wrong-source-sha',lambda x:x['source_tracks'][0].update(sha256='0'*64))
    control('missing-method',lambda x:x['members'].pop())
    control('missing-static-initializer',lambda x:x['bounded_dependency_support'].pop())
    control('missing-operands',lambda x:member(x,'lerpRotationValues').pop('supplemental_full_operand_records'))
    control('rotation-xyz-vs-zyx',lambda x:op(x,'getQuatFromEulerZYX',8)['reference'].update(name='x'))
    control('nlerp-replaced-slerp',lambda x:op(x,'lerpRotationValues',43)['reference'].update(name='slerp'))
    control('scalar-lerp-subtraction',lambda x:op(x,'lerpScalar',4).update(opcode='0x62'))
    control('scalar-scale-weight-multiply',lambda x:op(x,'computeWeightedScaleScalar',5).update(opcode='0x62'))
    control('wrap-boundary-polarity',lambda x:op(x,'wrapRotationScalar',11).update(opcode='0x9e'))
    control('catmull-tangent-half',lambda x:op(x,'catmullRomScalar',3)['reference'].update(value=1.0))
    control('euler-safeasin',lambda x:op(x,'getEulerAnglesZYX',71)['reference'].update(name='asin'))
    control('missing-constants',lambda x:x['bootstrap_and_constant_evidence'][0].pop('constant_values'))
    control('wrong-artifact-claim',lambda x:x['artifact'].update(sha256='0'*64))
    result={'artifact_sha256':SHA,'base_checks':len(base['checks']),'base_failures':base['failures'],'scoped_checks':checks,'failures':[c for c in checks if not c['pass']],'negative_controls':negatives,'negative_failures':[n for n in negatives if not n['rejected']],'runtime_executed':False,'limit':'Checks preserve exact instructions and source-reviewed local roles, not external JOML numerical equivalence.'}
    Path(a.out).write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({'base_checks':result['base_checks'],'scoped_checks':len(checks),'negative_controls':len(negatives),'failures':len(result['base_failures'])+len(result['failures'])+len(result['negative_failures'])}))
    if run.returncode or result['failures'] or result['negative_failures']:raise SystemExit(1)
if __name__=='__main__':main()
