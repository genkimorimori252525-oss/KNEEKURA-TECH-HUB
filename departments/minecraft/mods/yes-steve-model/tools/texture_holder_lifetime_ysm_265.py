#!/usr/bin/env python3
"""Fixed-artifact animatable frame evidence audit. Never runs target classes."""
import argparse,copy,hashlib,json,subprocess,zipfile
from pathlib import Path
from audit_seed_recovery_ysm_265 import parse_bounded,BOUNDDETAILS
from scan_ysm_265 import parse_class
SHA='25b5e902b96f4c298690208f8b433cbc31737c23f87590354dbd86f00207bc8f'
SIZE=63269843
OWNERS=['com/elfmcys/yesstevemodel/OOOOoO0o0Oo00O0o0oOoOo00', 'com/elfmcys/yesstevemodel/OOOOoO0o0Oo00O0o0oOoOo00$Oo0Oo0o00O00Oo0OOoOOoooo', 'com/elfmcys/yesstevemodel/Oo0o0oO0000oO00O00oo00OO', 'com/elfmcys/yesstevemodel/ooooo00oOO000OO0o0oOOoOO']
SOURCES=[('src/main/java/com/elfmcys/yesstevemodel/client/texture/CustomTextureManager.java', 'c7d30da58234a6cb0842b79de5d59980d64d4d5d80e31b7dc70edc3e599d1498', 'f184edabd1b5115ce5a24cb6d155ba5a669f5ba6'), ('src/main/java/com/elfmcys/yesstevemodel/client/texture/CustomTextureManager.java', 'c7d30da58234a6cb0842b79de5d59980d64d4d5d80e31b7dc70edc3e599d1498', 'f184edabd1b5115ce5a24cb6d155ba5a669f5ba6'), ('src/main/java/com/elfmcys/yesstevemodel/client/texture/TextureHolder.java', 'e158adf6d62014652700977063b5966faa3ec6ca2cfa6c6a64c590830cb6aed0', 'f184edabd1b5115ce5a24cb6d155ba5a669f5ba6'), ('src/main/java/com/elfmcys/yesstevemodel/util/CleanerUtil.java', '3dae2e518faa84745e29b653e5be78808ca6ea25af44efc83203ff95a53eb2e3', 'f184edabd1b5115ce5a24cb6d155ba5a669f5ba6')]

KEYS=('access','instructions','supplemental_full_operand_records','exception_handlers','code_sha256')
DECL=('access','super','interfaces','fields','methods')
def ident(m):return tuple(m.get(k) for k in ('owner','name','descriptor'))
def audit(e,actual,decl,details):
    checks=[]
    def ck(name,ok):checks.append({'check':name,'pass':bool(ok)})
    ck('fixed-artifact',e.get('artifact',{}).get('sha256')==SHA and e.get('artifact',{}).get('size')==SIZE)
    ck('detailed-operands',e.get('detailed_operands') is True)
    rows=e.get('members',[]);ids=[ident(m) for m in rows]
    ck('complete-19-methods',len(ids)==len(set(ids))==19 and set(ids)==set(actual))
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
    reg='(Lnet/minecraft/client/renderer/texture/AbstractTexture;ZI)Lcom/elfmcys/yesstevemodel/Oo0o0oO0000oO00O00oo00OO;'
    do='(Lnet/minecraft/client/renderer/texture/AbstractTexture;Lcom/elfmcys/yesstevemodel/OOOOoO0o0Oo00O0o0oOoOo00$Oo0Oo0o00O00Oo0OOoOOoooo;)V'
    neg('render-thread-assertion',lambda x:op(x,0,reg,0)['reference'].update(name='wrong'))
    neg('ready-holder-reregister',lambda x:op(x,0,reg,41).update(opcode='0x99'))
    neg('immediate-queue-polarity',lambda x:op(x,0,reg,223).update(opcode='0x9a'))
    neg('registration-ready-check',lambda x:op(x,0,do,4).update(opcode='0x99'))
    neg('cleaner-before-ready',lambda x:op(x,0,do,39)['reference'].update(name='wrong'))
    neg('zero-delay-decrement',lambda x:op(x,0,'()V',57,'Oo0Oo0o00O00Oo0OOoOOoooo').update(opcode='0x9c'))
    neg('budget-20',lambda x:op(x,0,'()V',160,'Oo0Oo0o00O00Oo0OOoOOoooo')['reference'].update(value=200))
    neg('budget-equality-continues',lambda x:op(x,0,'()V',164,'Oo0Oo0o00O00Oo0OOoOOoooo').update(opcode='0x9e'))
    neg('release-direct-close',lambda x:op(x,0,'(Lnet/minecraft/client/renderer/texture/AbstractTexture;)V',7)['reference'].update(name='close'))
    neg('invented-registration-finally',lambda x:member(x,0,do)['exception_handlers'].append({'start':0,'end':46,'handler':46,'catch':None}))
    result={'artifact_sha256':SHA,'checks':checks,'negative_controls':negatives,'failures':[c for c in checks if not c['pass']],'negative_failures':[n for n in negatives if not n['rejected']],'independent_semantic_review':'NOT_RUN','runtime_executed':False,'central_mapping_promoted':False}
    Path(a.out).write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({'checks':len(checks),'negative_controls':len(negatives),'failures':len(result['failures'])+len(result['negative_failures'])}))
    if result['failures'] or result['negative_failures']:raise SystemExit(1)
if __name__=='__main__':main()
