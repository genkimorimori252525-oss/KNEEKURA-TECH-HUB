#!/usr/bin/env python3
"""Fixed-artifact static bone-state evidence checks, not execution of YSM/JOML."""
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
OWNER = 'com/elfmcys/yesstevemodel/OO0oo000o00O0O0oo00oO000'
SOURCE_PATH = 'src/main/java/com/elfmcys/yesstevemodel/geckolib3/model/GeoBoneState.java'
SOURCE_SHA = '54287db4a6e3ed32b1086731425f4c98d9521b0042ad5223733c0a644f25ac9b'
REVISION = 'f184edabd1b5115ce5a24cb6d155ba5a669f5ba6'
BUFFER_CONTRACT = {'input_array_field': 'O0o00oO0O0ooOOOo0oo0Oo00', 'input_offset_field': 'oOOOooO00oo0oOooooOO0Oo0', 'output_array_field': 'OO0O00oO0OOO00oOO0OoO0OO', 'output_offset_field': 'o0OooO00ooo0OO000O0OoOoO', 'input_slots': {'rotation_x': 0, 'rotation_y': 1, 'rotation_z': 2, 'position_x': 3, 'position_y': 4, 'position_z': 5, 'scale_x': 6, 'scale_y': 7, 'scale_z': 8, 'hidden': 9, 'children_hidden': 10, 'tracking': 11}, 'output_slots': {'absolute_pivot_x': 0, 'absolute_pivot_y': 1, 'absolute_pivot_z': 2}, 'source_artifact_divergence_flag_preserved': True}
ALLOC_OWNER = 'com/elfmcys/yesstevemodel/OOOO0O0O000O000000oOOO0o'
ALLOC_IDS = [('com/elfmcys/yesstevemodel/OOOO0O0O000O000000oOOO0o', '<init>', '(Lcom/elfmcys/yesstevemodel/OOoOoooOOooO0o0000o0O0o0;)V'), ('com/elfmcys/yesstevemodel/OOOO0O0O000O000000oOOO0o', 'Oo0Oo0o00O00Oo0OOoOOoooo', '()[F'), ('com/elfmcys/yesstevemodel/OOOO0O0O000O000000oOOO0o', 'o0OOooo0o0OO00OoOOOo0o0O', '()[F')]
ALLOC_SOURCE = {'path': 'src/main/java/com/elfmcys/yesstevemodel/geckolib3/model/GeoModelState.java', 'sha256': '9076ef19fa5757ceb38ef4898985fe53d5be06d5e7f88d56ce163f86a8752424', 'revision': 'f184edabd1b5115ce5a24cb6d155ba5a669f5ba6'}
FIELDS = ('access', 'instructions', 'supplemental_full_operand_records', 'exception_handlers', 'code_sha256')
def key(m):
    return tuple(m.get(k) for k in ('owner', 'name', 'descriptor'))
def audit(evidence, actual, details, alloc_actual=None):
    checks=[]
    def check(name, passed): checks.append({'check':name,'pass':bool(passed)})
    check('fixed-artifact',evidence.get('artifact',{}).get('sha256')==SHA and evidence.get('artifact',{}).get('size')==SIZE)
    check('detailed-operands',evidence.get('detailed_operands') is True)
    cs=evidence.get('classes',[])
    check('one-required-class',len(cs)==1 and cs[0].get('owner')==OWNER and all(k in cs[0].get('declaration',{}) for k in ('access','super','interfaces','fields','methods')))
    ss=evidence.get('source_tracks',[])
    check('fixed-source-record',len(ss)==1 and ss[0].get('path')==SOURCE_PATH and ss[0].get('sha256')==SOURCE_SHA and ss[0].get('revision')==REVISION)
    check('fixed-buffer-contract',evidence.get('buffer_contract')==BUFFER_CONTRACT)
    rows=evidence.get('members',[])+evidence.get('bounded_dependency_support',[])
    ids=[key(m) for m in rows]
    check('complete-35-method-set',len(ids)==len(set(ids))==35 and set(ids)==set(actual))
    for m in rows:
        observed=actual.get(key(m),{})
        for f in FIELDS:check(str(key(m))+':'+f,f in m and m[f]==observed.get(f))
    ds=evidence.get('bootstrap_and_constant_evidence',[])
    check('single-owner-detail',len(ds)==1 and ds[0].get('owner')==OWNER)
    for f in ('bootstrap_methods','constant_values'):
        check(f,len(ds)==1 and f in ds[0] and ds[0][f]==details[f])
    ar=evidence.get('allocation_support',[])
    check('three-allocation-methods',len(ar)==3 and {key(m) for m in ar}==set(ALLOC_IDS))
    for m in ar:
        observed=(alloc_actual or {}).get(key(m),{})
        for f in FIELDS:check('allocation:'+str(key(m))+':'+f,f in m and m[f]==observed.get(f))
    check('fixed-allocation-source',evidence.get('allocation_source')==ALLOC_SOURCE)
    return checks

def main():
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('jar','evidence','source-root','out'):p.add_argument('--'+name,required=True)
    a=p.parse_args();raw=Path(a.jar).read_bytes()
    if len(raw)!=SIZE or hashlib.sha256(raw).hexdigest()!=SHA:raise SystemExit('Wrong fixed artifact')
    e=json.loads(Path(a.evidence).read_text())
    with zipfile.ZipFile(a.jar) as z:
        actual={key(m):m for m in parse_bounded(z.read(OWNER+'.class'),True)}
        alloc_actual={key(m):m for m in parse_bounded(z.read(ALLOC_OWNER+'.class'),True) if key(m) in ALLOC_IDS}
    details=copy.deepcopy(BOUNDDETAILS[OWNER]);checks=audit(e,actual,details,alloc_actual)
    root=Path(a.source_root);src=root/SOURCE_PATH
    rev=subprocess.check_output(['git','-C',str(root),'rev-parse','HEAD'],text=True).strip()
    alloc_src=root/ALLOC_SOURCE['path']
    checks.append({'check':'allocation-source-sha','pass':alloc_src.is_file() and hashlib.sha256(alloc_src.read_bytes()).hexdigest()==ALLOC_SOURCE['sha256']})
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
        x=copy.deepcopy(e);mutate(x);fail=[c for c in audit(x,actual,details,alloc_actual) if not c['pass']];negatives.append({'control':name,'rejected':bool(fail)})
    control('missing-allocation-record',lambda x:x['allocation_support'].pop())
    control('wrong-output-stride',lambda x:next(o for o in x['allocation_support'][0]['instructions'] if o['offset']==68).update(opcode='0x6'))
    control('missing-allocation-source',lambda x:x.pop('allocation_source'))
    control('missing-class-record',lambda x:x['classes'].clear())
    control('missing-source-record',lambda x:x['source_tracks'].clear())
    control('wrong-source-sha',lambda x:x['source_tracks'][0].update(sha256='0'*64))
    control('missing-setter',lambda x:x['members'].pop())
    control('missing-support-getter',lambda x:x['bounded_dependency_support'].pop())
    control('missing-operands',lambda x:member(x,'setRotationX').pop('supplemental_full_operand_records'))
    control('rotation-x-slot',lambda x:op(x,'setRotationX',8).update(opcode='0x4'))
    control('rotation-x-store',lambda x:op(x,'setRotationX',11).update(opcode='0x30'))
    control('input-output-array-confusion',lambda x:op(x,'setRotationX',1)['reference'].update(name='OO0O00oO0OOO00oOO0OoO0OO'))
    control('hidden-branch-polarity',lambda x:op(x,'setHiddenSeparately',12).update(opcode='0x9a'))
    control('hidden-child-slot',lambda x:op(x,'setHiddenSeparately',29).update(immediate=9))
    control('hidden-together-argument',lambda x:op(x,'setHiddenTogether',2).update(opcode='0x3'))
    control('tracking-true-value',lambda x:op(x,'setTracking',15).update(opcode='0xb'))
    control('wrong-published-slot-contract',lambda x:x['buffer_contract']['input_slots'].update(rotation_x=1))
    control('wrong-artifact-claim',lambda x:x['artifact'].update(sha256='0'*64))
    result={'artifact_sha256':SHA,'base_checks':len(base['checks']),'base_failures':base['failures'],'scoped_checks':checks,'failures':[c for c in checks if not c['pass']],'negative_controls':negatives,'negative_failures':[n for n in negatives if not n['rejected']],'runtime_executed':False,'limit':'Static array-write evidence only; no native consumer or concurrent safety proof.'}
    Path(a.out).write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({'base_checks':result['base_checks'],'scoped_checks':len(checks),'negative_controls':len(negatives),'failures':len(result['base_failures'])+len(result['failures'])+len(result['negative_failures'])}))
    if run.returncode or result['failures'] or result['negative_failures']:raise SystemExit(1)
if __name__=='__main__':main()
