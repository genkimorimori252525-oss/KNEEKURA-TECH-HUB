#!/usr/bin/env python3
"""TLM-LOCATION-ADAPTER fixed-artifact integrity audit; does not execute target classes or independently prove prose semantics."""
import argparse,copy,hashlib,json,subprocess,zipfile
from pathlib import Path
from audit_seed_recovery_ysm_265 import parse_bounded,BOUNDDETAILS
from scan_ysm_265 import parse_class
SHA='25b5e902b96f4c298690208f8b433cbc31737c23f87590354dbd86f00207bc8f'
SIZE=63269843
OWNERS=['com/elfmcys/yesstevemodel/oOoOOOo0o0oO0OOOo0ooOOo0', 'com/elfmcys/yesstevemodel/oOoOOOo0o0oO0OOOo0ooOOo0$1', 'com/elfmcys/yesstevemodel/oOoOOOo0o0oO0OOOo0ooOOo0$2']
SELECTED=set([('com/elfmcys/yesstevemodel/oOoOOOo0o0oO0OOOo0ooOOo0', '<init>', '()V'), ('com/elfmcys/yesstevemodel/oOoOOOo0o0oO0OOOo0ooOOo0', 'Oo0Oo0o00O00Oo0OOoOOoooo', '(Lcom/elfmcys/yesstevemodel/OO0oo000o00O0O0oo00oO000;)Lcom/github/tartaricacid/touhoulittlemaid/geckolib3/core/processor/ILocationBone;'), ('com/elfmcys/yesstevemodel/oOoOOOo0o0oO0OOOo0ooOOo0', 'Oo0Oo0o00O00Oo0OOoOOoooo', '(Lcom/elfmcys/yesstevemodel/OOOO0O0O000O000000oOOO0o;)Lcom/github/tartaricacid/touhoulittlemaid/geckolib3/geo/animated/ILocationModel;'), ('com/elfmcys/yesstevemodel/oOoOOOo0o0oO0OOOo0ooOOo0', 'Oo0Oo0o00O00Oo0OOoOOoooo', '(Ljava/util/List;)Ljava/util/List;'), ('com/elfmcys/yesstevemodel/oOoOOOo0o0oO0OOOo0ooOOo0', 'Oo0Oo0o00O00Oo0OOoOOoooo', '(Lcom/elfmcys/yesstevemodel/Oo0o00oOOo0OO000000O0oO0;)Lcom/github/tartaricacid/touhoulittlemaid/geckolib3/core/processor/ILocationBone;'), ('com/elfmcys/yesstevemodel/oOoOOOo0o0oO0OOOo0ooOOo0$1', '<init>', '(Lcom/elfmcys/yesstevemodel/OO0oo000o00O0O0oo00oO000;)V'), ('com/elfmcys/yesstevemodel/oOoOOOo0o0oO0OOOo0ooOOo0$1', 'getRotationX', '()F'), ('com/elfmcys/yesstevemodel/oOoOOOo0o0oO0OOOo0ooOOo0$1', 'getRotationY', '()F'), ('com/elfmcys/yesstevemodel/oOoOOOo0o0oO0OOOo0ooOOo0$1', 'getRotationZ', '()F'), ('com/elfmcys/yesstevemodel/oOoOOOo0o0oO0OOOo0ooOOo0$1', 'getPositionX', '()F'), ('com/elfmcys/yesstevemodel/oOoOOOo0o0oO0OOOo0ooOOo0$1', 'getPositionY', '()F'), ('com/elfmcys/yesstevemodel/oOoOOOo0o0oO0OOOo0ooOOo0$1', 'getPositionZ', '()F'), ('com/elfmcys/yesstevemodel/oOoOOOo0o0oO0OOOo0ooOOo0$1', 'getScaleX', '()F'), ('com/elfmcys/yesstevemodel/oOoOOOo0o0oO0OOOo0ooOOo0$1', 'getScaleY', '()F'), ('com/elfmcys/yesstevemodel/oOoOOOo0o0oO0OOOo0ooOOo0$1', 'getScaleZ', '()F'), ('com/elfmcys/yesstevemodel/oOoOOOo0o0oO0OOOo0ooOOo0$1', 'getPivotX', '()F'), ('com/elfmcys/yesstevemodel/oOoOOOo0o0oO0OOOo0ooOOo0$1', 'getPivotY', '()F'), ('com/elfmcys/yesstevemodel/oOoOOOo0o0oO0OOOo0ooOOo0$1', 'getPivotZ', '()F'), ('com/elfmcys/yesstevemodel/oOoOOOo0o0oO0OOOo0ooOOo0$2', '<init>', '(Lcom/elfmcys/yesstevemodel/OOOO0O0O000O000000oOOO0o;)V'), ('com/elfmcys/yesstevemodel/oOoOOOo0o0oO0OOOo0ooOOo0$2', 'leftHandBones', '()Ljava/util/List;'), ('com/elfmcys/yesstevemodel/oOoOOOo0o0oO0OOOo0ooOOo0$2', 'extraLeftHandBones', '()Ljava/util/List;'), ('com/elfmcys/yesstevemodel/oOoOOOo0o0oO0OOOo0ooOOo0$2', 'rightHandBones', '()Ljava/util/List;'), ('com/elfmcys/yesstevemodel/oOoOOOo0o0oO0OOOo0ooOOo0$2', 'extraRightHandBones', '()Ljava/util/List;'), ('com/elfmcys/yesstevemodel/oOoOOOo0o0oO0OOOo0ooOOo0$2', 'leftWaistBones', '()Ljava/util/List;'), ('com/elfmcys/yesstevemodel/oOoOOOo0o0oO0OOOo0ooOOo0$2', 'rightWaistBones', '()Ljava/util/List;'), ('com/elfmcys/yesstevemodel/oOoOOOo0o0oO0OOOo0ooOOo0$2', 'backpackBones', '()Ljava/util/List;'), ('com/elfmcys/yesstevemodel/oOoOOOo0o0oO0OOOo0ooOOo0$2', 'tacPistolBones', '()Ljava/util/List;'), ('com/elfmcys/yesstevemodel/oOoOOOo0o0oO0OOOo0ooOOo0$2', 'tacRifleBones', '()Ljava/util/List;'), ('com/elfmcys/yesstevemodel/oOoOOOo0o0oO0OOOo0ooOOo0$2', 'headBones', '()Ljava/util/List;'), ('com/elfmcys/yesstevemodel/oOoOOOo0o0oO0OOOo0ooOOo0$2', 'Oo0Oo0o00O00Oo0OOoOOoooo', '(Ljava/util/List;Ljava/util/List;)V'), ('com/elfmcys/yesstevemodel/oOoOOOo0o0oO0OOOo0ooOOo0$2', 'o0OOooo0o0OO00OoOOOo0o0O', '(Ljava/util/List;Ljava/util/List;)V')])
SOURCES=[('src/main/java/com/elfmcys/yesstevemodel/client/compat/touhoulittlemaid/util/TlmConverterHelper.java', '2daf3d3d717ddf5106fdc2f664ab16b8b86d2e0f96be913a5f8ffe0af2fe59f8', 'f184edabd1b5115ce5a24cb6d155ba5a669f5ba6'), ('src/main/java/com/elfmcys/yesstevemodel/client/compat/touhoulittlemaid/util/TlmConverterHelper.java', '2daf3d3d717ddf5106fdc2f664ab16b8b86d2e0f96be913a5f8ffe0af2fe59f8', 'f184edabd1b5115ce5a24cb6d155ba5a669f5ba6'), ('src/main/java/com/elfmcys/yesstevemodel/client/compat/touhoulittlemaid/util/TlmConverterHelper.java', '2daf3d3d717ddf5106fdc2f664ab16b8b86d2e0f96be913a5f8ffe0af2fe59f8', 'f184edabd1b5115ce5a24cb6d155ba5a669f5ba6')]

KEYS=('access','instructions','supplemental_full_operand_records','exception_handlers','code_sha256')
DECL=('access','super','interfaces','fields','methods')
def ident(m):return tuple(m.get(k) for k in ('owner','name','descriptor'))
def audit(e,actual,decl,details):
    checks=[]
    def ck(name,ok):checks.append({'check':name,'pass':bool(ok)})
    ck('fixed-artifact',e.get('artifact',{}).get('sha256')==SHA and e.get('artifact',{}).get('size')==SIZE)
    ck('detailed-operands',e.get('detailed_operands') is True)
    rows=e.get('members',[]);ids=[ident(m) for m in rows]
    ck('selected-31-methods',len(ids)==len(set(ids))==31 and set(ids)==set(actual)==SELECTED)
    for m in rows:
        a=actual.get(ident(m),{})
        for k in KEYS:ck(str(ident(m))+':'+k,(k in m)==(k in a) and m.get(k)==a.get(k))
    ds=e.get('owner_declarations',[]);ck('three-declarations',len(ds)==3 and {r['owner'] for r in ds}==set(OWNERS))
    for r in ds:ck(r['owner']+':declaration',r['declaration']==decl.get(r['owner']))
    bs=e.get('bootstrap_and_constant_evidence',[]);ck('three-bootstrap-records',len(bs)==3 and {r['owner'] for r in bs}==set(OWNERS))
    for r in bs:
        for k in ('constant_values','bootstrap_methods'):ck(r['owner']+':'+k,k in r and r[k]==details.get(r['owner'],{}).get(k))
    ss=e.get('source_tracks',[]);ck('three-fixed-source-records',sorted((r.get('path'),r.get('sha256'),r.get('revision')) for r in ss)==sorted(SOURCES))
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
    neg('missing-model-asset-helper-0',lambda x:member(x,0,'(Lcom/elfmcys/yesstevemodel/OO0oo000o00O0O0oo00oO000;)Lcom/github/tartaricacid/touhoulittlemaid/geckolib3/core/processor/ILocationBone;','Oo0Oo0o00O00Oo0OOoOOoooo')['instructions'].pop())
    neg('missing-model-asset-helper-1',lambda x:member(x,1,'()F','getRotationX')['instructions'].pop())
    neg('missing-model-asset-helper-2',lambda x:member(x,2,'()Ljava/util/List;','leftHandBones')['instructions'].pop())
    result={'artifact_sha256':SHA,'checks':checks,'negative_controls':negatives,'failures':[c for c in checks if not c['pass']],'negative_failures':[n for n in negatives if not n['rejected']],'independent_semantic_review':'NOT_RUN','runtime_executed':False,'central_mapping_promoted':False}
    Path(a.out).write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({'checks':len(checks),'negative_controls':len(negatives),'failures':len(result['failures'])+len(result['negative_failures'])}))
    if result['failures'] or result['negative_failures']:raise SystemExit(1)
if __name__=='__main__':main()
