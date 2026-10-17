#!/usr/bin/env python3
"""Fixed-artifact model readiness/scope evidence audit. Never runs target classes."""
import argparse,copy,hashlib,json,subprocess,zipfile
from pathlib import Path
from audit_seed_recovery_ysm_265 import parse_bounded,BOUNDDETAILS
from scan_ysm_265 import parse_class
SHA='25b5e902b96f4c298690208f8b433cbc31737c23f87590354dbd86f00207bc8f'
SIZE=63269843
OWNERS=['com/elfmcys/yesstevemodel/oOo00OoOO00O000ooO0Oo00o', 'com/elfmcys/yesstevemodel/oOo00OoOO00O000ooO0Oo00o$Oo0Oo0o00O00Oo0OOoOOoooo', 'com/elfmcys/yesstevemodel/o0O0oOooOo0OoOo0oOo00O00$Oo0Oo0o00O00Oo0OOoOOoooo', 'com/elfmcys/yesstevemodel/oO0O0OoO0Oo0O0O00O0o0OoO$Oo0Oo0o00O00Oo0OOoOOoooo', 'com/elfmcys/yesstevemodel/oOOOOOO0oo0O0O0o0OoOoOOO$Oo0Oo0o00O00Oo0OOoOOoooo', 'com/elfmcys/yesstevemodel/mixin/plugin/MixinTweaker', 'com/elfmcys/yesstevemodel/OoO00Oo00Ooo0OoOoo00o000']
SOURCES=[('src/main/java/com/elfmcys/yesstevemodel/client/entity/CustomEntity.java', 'f1d6924017b087a89ed03868be2d7e55be237edf0d8522adccb013a41f7e809c', 'f184edabd1b5115ce5a24cb6d155ba5a669f5ba6'), ('src/main/java/com/elfmcys/yesstevemodel/client/entity/CustomEntity.java', 'f1d6924017b087a89ed03868be2d7e55be237edf0d8522adccb013a41f7e809c', 'f184edabd1b5115ce5a24cb6d155ba5a669f5ba6'), ('src/main/java/com/elfmcys/yesstevemodel/client/entity/CustomHumanoidEntity.java', 'a5def776d16ae1164d7f559ddb0809a979b253f8c4b0367c471486d81c6246e0', 'f184edabd1b5115ce5a24cb6d155ba5a669f5ba6'), ('src/main/java/com/elfmcys/yesstevemodel/client/entity/CustomProjectileEntity.java', '7551945062ac6f5839b74d189c230d56863834db8687d56e82d90c449100dced', 'f184edabd1b5115ce5a24cb6d155ba5a669f5ba6'), ('src/main/java/com/elfmcys/yesstevemodel/client/entity/CustomVehicleEntity.java', '36e493c55ef8d7a13ebf37f3ef676bc30415f8f96e4438a012b9ee7f55f218e3', 'f184edabd1b5115ce5a24cb6d155ba5a669f5ba6'), ('src/main/java/com/elfmcys/yesstevemodel/mixin/plugin/MixinTweaker.java', 'e2f20806e7f6cb7ef0812be7251e757be4fd56ea30fab9e8a92c3a42bfbc0a26', 'f184edabd1b5115ce5a24cb6d155ba5a669f5ba6'), ('src/main/java/com/elfmcys/yesstevemodel/util/RenderUtil.java', 'b181c57910eeb0db57a69b7b956b5b74dd03275ad285470709e80c9aaaa2fae1', 'f184edabd1b5115ce5a24cb6d155ba5a669f5ba6')]

KEYS=('access','instructions','supplemental_full_operand_records','exception_handlers','code_sha256')
DECL=('access','super','interfaces','fields','methods')
def ident(m):return tuple(m.get(k) for k in ('owner','name','descriptor'))
def audit(e,actual,decl,details):
    checks=[]
    def ck(name,ok):checks.append({'check':name,'pass':bool(ok)})
    ck('fixed-artifact',e.get('artifact',{}).get('sha256')==SHA and e.get('artifact',{}).get('size')==SIZE)
    ck('detailed-operands',e.get('detailed_operands') is True)
    rows=e.get('members',[]);ids=[ident(m) for m in rows]
    ck('complete-73-methods',len(ids)==len(set(ids))==73 and set(ids)==set(actual))
    for m in rows:
        a=actual.get(ident(m),{})
        for k in KEYS:ck(str(ident(m))+':'+k,(k in m)==(k in a) and m.get(k)==a.get(k))
    ds=e.get('owner_declarations',[]);ck('seven-declarations',len(ds)==7 and {r['owner'] for r in ds}==set(OWNERS))
    for r in ds:ck(r['owner']+':declaration',r['declaration']==decl.get(r['owner']))
    bs=e.get('bootstrap_and_constant_evidence',[]);ck('seven-bootstrap-records',len(bs)==7 and {r['owner'] for r in bs}==set(OWNERS))
    for r in bs:
        for k in ('constant_values','bootstrap_methods'):ck(r['owner']+':'+k,k in r and r[k]==details.get(r['owner'],{}).get(k))
    ss=e.get('source_tracks',[]);ck('seven-fixed-source-records',sorted((r.get('path'),r.get('sha256'),r.get('revision')) for r in ss)==sorted(SOURCES))
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
    neg('registration-boolean-inverted',lambda x:op(x,0,'(Lnet/minecraft/world/entity/Entity;Z)V',12).update(opcode='0x9a'))
    neg('tick-equality-refresh',lambda x:op(x,0,'()V',11,'oOo0o0000OOOO0OooooO00oo').update(opcode='0xa3'))
    neg('holder-identity-gate',lambda x:op(x,0,'()V',40,'Oo00o0OooOOo0ooOoo0oO0o0').update(opcode='0xa5'))
    neg('holder-loaded-gate',lambda x:op(x,0,'()V',64,'Oo00o0OooOOo0ooOoo0oO0o0').update(opcode='0x9a'))
    neg('base-holder-not-ready',lambda x:op(x,1,'()Z',0).update(opcode='0x3'))
    neg('plugin-rejects',lambda x:op(x,5,'(Ljava/lang/String;Ljava/lang/String;)Z',0).update(opcode='0x3'))
    neg('level-predicate-or-reversed',lambda x:op(x,6,'()Z',3,'O00OOOooOoooOoo0o0o0oO0O').update(opcode='0x99'))
    neg('exclusive-includes-first-person',lambda x:op(x,6,'()Z',12,'oOOOo0OOO0ooooo0O00OO0o0').update(opcode='0x99'))
    neg('exclusive-render-thread-assertion',lambda x:op(x,6,'()Z',0,'oOOOo0OOO0ooooo0O00OO0o0')['reference'].update(name='wrong'))
    neg('invented-model-switch-finally',lambda x:member(x,0,'()V','Oo00o0OooOOo0ooOoo0oO0o0')['exception_handlers'].append({'start':0,'end':129,'handler':129,'catch':None}))
    result={'artifact_sha256':SHA,'checks':checks,'negative_controls':negatives,'failures':[c for c in checks if not c['pass']],'negative_failures':[n for n in negatives if not n['rejected']],'independent_semantic_review':'NOT_RUN','runtime_executed':False,'central_mapping_promoted':False}
    Path(a.out).write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({'checks':len(checks),'negative_controls':len(negatives),'failures':len(result['failures'])+len(result['negative_failures'])}))
    if result['failures'] or result['negative_failures']:raise SystemExit(1)
if __name__=='__main__':main()
