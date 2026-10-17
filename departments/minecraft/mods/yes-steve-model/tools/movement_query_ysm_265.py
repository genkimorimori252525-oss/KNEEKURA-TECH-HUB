#!/usr/bin/env python3
"""Fixed-artifact selected motion query evidence audit. Never runs target classes."""
import argparse,copy,hashlib,json,subprocess,zipfile
from pathlib import Path
from audit_seed_recovery_ysm_265 import parse_bounded,BOUNDDETAILS
from scan_ysm_265 import parse_class
SHA='25b5e902b96f4c298690208f8b433cbc31737c23f87590354dbd86f00207bc8f'
SIZE=63269843
OWNERS=['com/elfmcys/yesstevemodel/o0000OOo0000oo000OOOo0o0', 'com/elfmcys/yesstevemodel/oo00O000000OoOo0O0O00oOO', 'com/elfmcys/yesstevemodel/o0O0o0OOOoooO0O0OO000oO0']
SOURCES=[('src/main/java/com/elfmcys/yesstevemodel/geckolib3/core/molang/builtin/QueryBinding.java', 'f5fdc573ed9187fcf72465abe5ac19a0f16cd39c7e2d0edc66d1c2de1473bfc8', 'f184edabd1b5115ce5a24cb6d155ba5a669f5ba6'), ('src/main/java/com/elfmcys/yesstevemodel/client/animation/molang/YSMBinding.java', '22bf1679ba5a8967b09109795fff207afdd2cb45ba34c4f70fb9ca4c9ca117a0', 'f184edabd1b5115ce5a24cb6d155ba5a669f5ba6'), ('src/main/java/com/elfmcys/yesstevemodel/client/animation/molang/variable/MoveInputVariable.java', '75326769d658d5aa35adb3630fade323bcfccbe8e9880beeaab9064244ba260b', 'f184edabd1b5115ce5a24cb6d155ba5a669f5ba6')]
SELECTED=set([('com/elfmcys/yesstevemodel/o0000OOo0000oo000OOOo0o0', '<init>', '()V'), ('com/elfmcys/yesstevemodel/o0000OOo0000oo000OOOo0o0', 'Oo0Oo0o00O00Oo0OOoOOoooo', '(Lnet/minecraft/world/entity/Entity;)F'), ('com/elfmcys/yesstevemodel/o0000OOo0000oo000OOOo0o0', 'oooooooOOoOOoO00OooOo00O', '(Lcom/elfmcys/yesstevemodel/oo0oOO0000o0Ooooo0OoOo0O;)F'), ('com/elfmcys/yesstevemodel/o0000OOo0000oo000OOOo0o0', 'oOo0oOOOO0ooOOO0oOoOO0oo', '(Lcom/elfmcys/yesstevemodel/oo0oOO0000o0Ooooo0OoOo0O;)Ljava/lang/Object;'), ('com/elfmcys/yesstevemodel/o0000OOo0000oo000OOOo0o0', 'OO00OOOOo0Ooo0oo0o0Oo0OO', '(Lcom/elfmcys/yesstevemodel/oo0oOO0000o0Ooooo0OoOo0O;)Ljava/lang/Object;'), ('com/elfmcys/yesstevemodel/oo00O000000OoOo0O0O00oOO', '<init>', '()V'), ('com/elfmcys/yesstevemodel/oo00O000000OoOo0O0O00oOO', 'OOOOo0O0oO0OOo0O0O0Oo0O0', '(Lcom/elfmcys/yesstevemodel/oo0oOO0000o0Ooooo0OoOo0O;)F'), ('com/elfmcys/yesstevemodel/oo00O000000OoOo0O0O00oOO', 'OOo00o0o0oo0oOOOoOOOoooO', '(Lcom/elfmcys/yesstevemodel/oo0oOO0000o0Ooooo0OoOo0O;)Ljava/lang/Object;'), ('com/elfmcys/yesstevemodel/o0O0o0OOOoooO0O0OO000oO0', '<init>', '()V'), ('com/elfmcys/yesstevemodel/o0O0o0OOOoooO0O0OO000oO0', 'Oo0Oo0o00O00Oo0OOoOOoooo', '(Lcom/elfmcys/yesstevemodel/oo0oOO0000o0Ooooo0OoOo0O;)D'), ('com/elfmcys/yesstevemodel/o0O0o0OOOoooO0O0OO000oO0', 'o0OOooo0o0OO00OoOOOo0o0O', '(Lcom/elfmcys/yesstevemodel/oo0oOO0000o0Ooooo0OoOo0O;)D')])

KEYS=('access','instructions','supplemental_full_operand_records','exception_handlers','code_sha256')
DECL=('access','super','interfaces','fields','methods')
def ident(m):return tuple(m.get(k) for k in ('owner','name','descriptor'))
def audit(e,actual,decl,details):
    checks=[]
    def ck(name,ok):checks.append({'check':name,'pass':bool(ok)})
    ck('fixed-artifact',e.get('artifact',{}).get('sha256')==SHA and e.get('artifact',{}).get('size')==SIZE)
    ck('detailed-operands',e.get('detailed_operands') is True)
    rows=e.get('members',[]);ids=[ident(m) for m in rows]
    ck('complete-11-selected-methods',len(ids)==len(set(ids))==11 and set(ids)==set(actual)==SELECTED)
    for m in rows:
        a=actual.get(ident(m),{})
        for k in KEYS:ck(str(ident(m))+':'+k,(k in m)==(k in a) and m.get(k)==a.get(k))
    ds=e.get('owner_declarations',[]);ck('three-declarations',len(ds)==3 and {r['owner'] for r in ds}==set(OWNERS))
    for r in ds:ck(r['owner']+':declaration',r['declaration']==decl.get(r['owner']))
    bs=e.get('bootstrap_and_constant_evidence',[]);ck('three-bootstrap-records',len(bs)==3 and {r['owner'] for r in bs}==set(OWNERS))
    for r in bs:
        for k in ('constant_values','bootstrap_methods'):ck(r['owner']+':'+k,k in r and r[k]==details.get(r['owner'],{}).get(k))
    ss=e.get('source_tracks',[]);ck('three-fixed-sources',sorted((r.get('path'),r.get('sha256'),r.get('revision')) for r in ss)==sorted(SOURCES))
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
    ctx='(Lcom/elfmcys/yesstevemodel/oo0oOO0000o0Ooooo0OoOo0O;)'
    neg('input-threshold',lambda x:op(x,2,ctx+'D',59,'Oo0Oo0o00O00Oo0OOoOOoooo')['reference'].update(value=0.001))
    neg('input-threshold-equality',lambda x:op(x,2,ctx+'D',63,'Oo0Oo0o00O00Oo0OOoOOoooo').update(opcode='0x9d'))
    neg('ground-speed2-denominator',lambda x:op(x,1,ctx+'F',46,'OOOOo0O0oO0OOo0O0O0Oo0O0').update(opcode='0x6a'))
    neg('time-delta-unit',lambda x:op(x,1,ctx+'Ljava/lang/Object;',12,'OOo00o0o0oo0oOOOoOOOoooO')['reference'].update(value=1.0))
    neg('input-registration-label',lambda x:op(x,1,'()V',258,'<init>')['reference'].update(string='vertical_speed'))
    neg('lost-bootstrap-target',lambda x:x['bootstrap_and_constant_evidence'][1]['bootstrap_methods'][10]['arguments'][1]['reference'].update(name='wrong'))
    result={'artifact_sha256':SHA,'checks':checks,'negative_controls':negatives,'failures':[c for c in checks if not c['pass']],'negative_failures':[n for n in negatives if not n['rejected']],'independent_semantic_review':'NOT_RUN','runtime_executed':False,'central_mapping_promoted':False}
    Path(a.out).write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({'checks':len(checks),'negative_controls':len(negatives),'failures':len(result['failures'])+len(result['negative_failures'])}))
    if result['failures'] or result['negative_failures']:raise SystemExit(1)
if __name__=='__main__':main()
